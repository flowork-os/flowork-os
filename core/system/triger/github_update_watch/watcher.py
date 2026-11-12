#!/usr/bin/env python3
"""
Flowork OS — Active Trigger: GitHub Upstream Update Watcher
Monitors upstream repository commits/manifests with ETag conditional polling,
writes /tmp/flowork_active_trigger.json, updates sidebar badge, emits Neural Bus
events, and wakes Mr. Flow via UNIX socket when upstream changes arrive.
"""

import argparse
import gzip
import json
import os
import pwd
import re
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

TRIGGER_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(TRIGGER_DIR, "trigger.json")
PID_FILE = os.path.join(TRIGGER_DIR, ".pid")
LAST_ALERT_FILE = os.path.join(TRIGGER_DIR, ".last_alert")
STATE_FILE = os.path.join(TRIGGER_DIR, ".state.json")

SIGNAL_FILE = "/tmp/flowork_active_trigger.json"
VERSION_FILE = "/opt/floworkos/system/version.json"
LOCAL_MANIFEST_FILE = "/opt/floworkos/system/manifest.json"
REPO_STAGE_DIR = os.environ.get("FLOWORK_REPO_DIR") or (
    "/opt/flowork-os-repo"
    if os.path.isdir("/opt/flowork-os-repo")
    else os.path.expanduser("~/flowork-os-repo")
)

PRIORITY_CRITICAL_SOURCES = {"kernel_telemetry", "system_telemetry", "disk_guard", "KERNEL_WATCHDOG"}
ACTIVE_SIGNAL_TTL_SECS = 300

DEV_LANDMARK_PATHS = [
    "/opt/floworkos/flowork.dev",
    "/etc/flowork.dev",
    os.path.expanduser("~/.flowork/flowork.dev"),
    os.path.expanduser("~/flowork.dev"),
]


def atomic_write_text(path: str, content: str, mode: int = 0o644) -> None:
    parent = os.path.dirname(path) or "/tmp"
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_ghwatch_", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def atomic_write_json(path: str, payload: dict, mode: int = 0o644) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2) + "\n", mode=mode)


def load_json_safe(path: str, default=None):
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
    except Exception:
        pass
    return default


def load_trigger_config() -> dict:
    cfg = load_json_safe(CONFIG_FILE, {}) or {}
    if not isinstance(cfg, dict):
        cfg = {}
    thresholds = cfg.get("thresholds") if isinstance(cfg.get("thresholds"), dict) else {}
    return {
        "name": str(cfg.get("name") or "github_update_watch"),
        "enabled": bool(cfg.get("enabled", True)),
        "interval_seconds": max(30, int(cfg.get("interval_seconds", 300))),
        "cooldown_seconds": max(60, int(cfg.get("cooldown_seconds", 1800))),
        "repo": str(thresholds.get("repo") or "flowork-os/flowork-os"),
        "branch": str(thresholds.get("branch") or "main"),
        "compare_files_limit": max(5, min(50, int(thresholds.get("compare_files_limit", 25)))),
        "busy_retry_seconds": max(10, min(120, int(thresholds.get("busy_retry_seconds", 30)))),
    }


def resolve_repo_and_branch(cfg: dict) -> tuple[str, str, dict]:
    version_data = load_json_safe(VERSION_FILE, {}) or {}
    repo = cfg["repo"]
    branch = str(version_data.get("branch") or cfg["branch"] or "main").strip()
    remote_url = str(version_data.get("remote_url") or "").strip()
    m = re.search(r"github\.com[:/]([^/]+/[^/.]+?)(?:\.git)?/?$", remote_url)
    if m:
        repo = m.group(1)
    return repo, branch, version_data


def get_ssl_context():
    for ca_path in (
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/ca-bundle.pem",
    ):
        if os.path.exists(ca_path):
            try:
                return ssl.create_default_context(cafile=ca_path)
            except Exception:
                pass
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()


def check_dev_mode() -> tuple[bool, str]:
    for var in ("FLOWORK_ENV", "FLOWORK_DEV", "ENV", "MODE"):
        val = (os.environ.get(var) or "").strip().lower()
        if val in ("dev", "development", "1", "true", "yes"):
            return True, f"environment variable {var}={val}"
    for path in DEV_LANDMARK_PATHS:
        try:
            if os.path.exists(path):
                return True, f"landmark file {path}"
        except Exception:
            pass
    return False, ""


def get_local_repo_stage_status() -> dict:
    info = {"exists": os.path.isdir(REPO_STAGE_DIR), "head": None, "dirty_count": 0}
    if not info["exists"]:
        return info
    try:
        head_res = subprocess.run(
            ["git", "-C", REPO_STAGE_DIR, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if head_res.returncode == 0:
            info["head"] = head_res.stdout.strip()
        st_res = subprocess.run(
            ["git", "-C", REPO_STAGE_DIR, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if st_res.returncode == 0:
            info["dirty_count"] = len([ln for ln in st_res.stdout.splitlines() if ln.strip()])
    except Exception:
        pass
    return info


def http_get_with_etag(url: str, etag: str = "", accept: str = "application/vnd.github+json", timeout: int = 8):
    headers = {
        "User-Agent": "FloworkOS-GitHubWatch/1.0",
        "Accept": accept,
    }
    if etag:
        headers["If-None-Match"] = etag

    req = urllib.request.Request(url, headers=headers)
    ctx = get_ssl_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            body = resp.read()
            return resp.status, resp_headers, body
    except urllib.error.HTTPError as err:
        resp_headers = {k.lower(): v for k, v in err.headers.items()} if err.headers else {}
        return err.code, resp_headers, b""
    except Exception as exc:
        return None, {}, str(exc).encode("utf-8", errors="ignore")


def summarize_changed_files(files_list: list, limit: int = 25) -> list[dict]:
    summarized = []
    for fobj in (files_list or [])[:limit]:
        if not isinstance(fobj, dict):
            continue
        summarized.append(
            {
                "filename": fobj.get("filename", ""),
                "status": fobj.get("status", "modified"),
                "additions": int(fobj.get("additions", 0) or 0),
                "deletions": int(fobj.get("deletions", 0) or 0),
            }
        )
    return summarized


def parse_git_pkt_lines_for_ref(raw_bytes: bytes, target_ref_bytes: bytes) -> str | None:
    i = 0
    n = len(raw_bytes)
    while i + 4 <= n:
        hdr = raw_bytes[i : i + 4]
        if hdr == b"0000":
            i += 4
            continue
        try:
            plen = int(hdr.decode("ascii"), 16)
        except Exception:
            break
        if plen < 4 or i + plen > n:
            break
        payload = raw_bytes[i + 4 : i + plen]
        i += plen
        if payload.startswith(b"#"):
            continue
        main_part = payload.split(b"\x00", 1)[0].strip()
        parts = main_part.split(None, 1)
        if len(parts) == 2 and parts[1] == target_ref_bytes:
            sha = parts[0].decode("ascii", errors="ignore").lower()
            if re.fullmatch(r"[0-9a-f]{40}", sha):
                return sha
    return None


def fetch_git_smart_head(repo: str, branch: str, timeout: int = 8) -> str | None:
    url = f"https://github.com/{repo}.git/info/refs?service=git-upload-pack"
    headers = {"User-Agent": "FloworkOS-GitHubWatch/2.0", "Cache-Control": "no-cache"}
    req = urllib.request.Request(url, headers=headers)
    ctx = get_ssl_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            raw = resp.read()
        return parse_git_pkt_lines_for_ref(raw, f"refs/heads/{branch}".encode("utf-8"))
    except Exception:
        return None


def fetch_github_head(repo: str, branch: str, state: dict, force_no_etag: bool = False) -> dict:
    """
    Query GitHub commits/{branch} using ETag If-None-Match conditional requests
    (304 Not Modified consumes zero GitHub REST rate-limit quota).
    On REST API error or rate-limit, resolves exact live HEAD via Git Smart HTTP first
    and fetches commit-pinned manifest.json.gz (eliminating Fastly CDN /main/ lag).
    """
    api_url = f"https://api.github.com/repos/{repo}/commits/{branch}"
    prev_etag = "" if force_no_etag else str(state.get("etag") or "")

    status_code, headers, body = http_get_with_etag(api_url, etag=prev_etag)
    if status_code == 304 and state.get("last_remote_meta"):
        cached = dict(state["last_remote_meta"])
        cached["http_status"] = 304
        cached["source_channel"] = "github_api_cached_etag"
        return cached

    if status_code == 200 and body:
        try:
            data = json.loads(body.decode("utf-8"))
            commit_obj = data.get("commit") or {}
            author_obj = commit_obj.get("author") or {}
            files_list = data.get("files") or []
            meta = {
                "ok": True,
                "http_status": 200,
                "source_channel": "github_api",
                "etag": headers.get("etag", ""),
                "sha": str(data.get("sha") or "").strip(),
                "message": str(commit_obj.get("message") or "").strip().splitlines()[0][:240]
                if commit_obj.get("message")
                else "",
                "author": str(author_obj.get("name") or "").strip(),
                "date": str(author_obj.get("date") or "").strip(),
                "html_url": str(data.get("html_url") or f"https://github.com/{repo}/commit/{data.get('sha', '')}"),
                "head_files_count": len(files_list),
                "head_files_sample": summarize_changed_files(files_list, limit=25),
            }
            return meta
        except Exception as exc:
            return {"ok": False, "error": f"Failed parsing GitHub API commit payload: {exc}"}

    # Fallback A: Git Smart HTTP (exact real-time HEAD SHA without REST quota or CDN cache)
    smart_sha = fetch_git_smart_head(repo, branch)
    if smart_sha:
        cached_meta = state.get("last_remote_meta") or {}
        if not force_no_etag and cached_meta.get("sha") == smart_sha and cached_meta.get("ok"):
            cached = dict(cached_meta)
            cached["http_status"] = 304
            cached["source_channel"] = "git_smart_http_cached"
            return cached

        pinned_url = f"https://raw.githubusercontent.com/{repo}/{smart_sha}/manifest.json.gz"
        r_code, r_headers, r_body = http_get_with_etag(pinned_url, accept="application/gzip", timeout=15)
        if r_code == 200 and r_body:
            try:
                manifest = json.loads(gzip.decompress(r_body).decode("utf-8"))
                return {
                    "ok": True,
                    "http_status": 200,
                    "source_channel": "git_smart_http_manifest_gz",
                    "raw_etag": r_headers.get("etag", ""),
                    "sha": smart_sha,
                    "manifest_id": str(manifest.get("manifest_id") or "").strip(),
                    "date": str(manifest.get("generated_at") or "").strip(),
                    "message": f"Upstream commit {smart_sha[:10]} ({manifest.get('total_files', 0)} tracked files)",
                    "author": "Flowork OS Release",
                    "html_url": f"https://github.com/{repo}/commit/{smart_sha}",
                    "remote_manifest_files": manifest.get("files") or {},
                }
            except Exception:
                pass
        return {
            "ok": True,
            "http_status": 200,
            "source_channel": "git_smart_http",
            "sha": smart_sha,
            "date": "",
            "message": f"Upstream commit {smart_sha[:10]} detected via Git Smart HTTP",
            "author": "Flowork OS Release",
            "html_url": f"https://github.com/{repo}/commit/{smart_sha}",
        }

    # Fallback B: raw manifest.json.gz over branch (only if both REST API and Git Smart HTTP fail)
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/manifest.json.gz"
    raw_etag = "" if force_no_etag else str(state.get("raw_etag") or "")
    r_code, r_headers, r_body = http_get_with_etag(raw_url, etag=raw_etag, accept="application/gzip", timeout=12)
    if r_code == 304 and state.get("last_remote_meta"):
        cached = dict(state["last_remote_meta"])
        cached["http_status"] = 304
        cached["source_channel"] = "raw_manifest_cached_etag"
        return cached

    if r_code == 200 and r_body:
        try:
            manifest = json.loads(gzip.decompress(r_body).decode("utf-8"))
            return {
                "ok": True,
                "http_status": 200,
                "source_channel": "raw_manifest_gz",
                "raw_etag": r_headers.get("etag", ""),
                "sha": str(manifest.get("commit") or "").strip(),
                "manifest_id": str(manifest.get("manifest_id") or "").strip(),
                "date": str(manifest.get("generated_at") or "").strip(),
                "message": f"Remote manifest update ({manifest.get('total_files', 0)} tracked files)",
                "author": "Flowork OS Release",
                "html_url": f"https://github.com/{repo}/commits/{branch}",
                "remote_manifest_files": manifest.get("files") or {},
            }
        except Exception as exc:
            return {"ok": False, "error": f"Fallback manifest parse failed: {exc}"}

    err_msg = body.decode("utf-8", errors="ignore")[:180] if isinstance(body, (bytes, bytearray)) else str(body)
    return {
        "ok": False,
        "http_status": status_code,
        "error": f"GitHub check unavailable (api_status={status_code}, raw_status={r_code}): {err_msg}",
    }


def inspect_upstream_delta(
    repo: str,
    local_commit: str,
    remote_meta: dict,
    files_limit: int = 25,
) -> dict:
    """
    Determine whether remote is genuinely ahead/diverged compared to local commit
    and extract concrete changed files + commit log without cloning full repo.
    """
    remote_commit = str(remote_meta.get("sha") or "").strip()
    if not remote_commit:
        return {"update_available": False, "reason": "Empty remote commit SHA"}

    if local_commit and remote_commit == local_commit:
        return {
            "update_available": False,
            "comparison_status": "identical",
            "ahead_by": 0,
            "behind_by": 0,
            "changed_files_count": 0,
            "changed_files_sample": [],
            "commits": [],
        }

    # Check directionality via GitHub compare API when local_commit is a valid SHA
    valid_local_sha = bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", local_commit or ""))
    if valid_local_sha:
        cmp_url = f"https://api.github.com/repos/{repo}/compare/{local_commit}...{remote_commit}"
        c_code, _, c_body = http_get_with_etag(cmp_url, timeout=8)
        if c_code == 200 and c_body:
            try:
                cmp_data = json.loads(c_body.decode("utf-8"))
                c_status = str(cmp_data.get("status") or "")
                ahead_by = int(cmp_data.get("ahead_by", 0) or 0)
                behind_by = int(cmp_data.get("behind_by", 0) or 0)
                files_list = cmp_data.get("files") or []
                commits_raw = cmp_data.get("commits") or []
                commits_summary = []
                for c in commits_raw[-8:]:
                    c_info = c.get("commit") or {}
                    c_author = c_info.get("author") or {}
                    commits_summary.append(
                        {
                            "sha": str(c.get("sha") or "")[:10],
                            "date": str(c_author.get("date") or ""),
                            "author": str(c_author.get("name") or ""),
                            "message": str(c_info.get("message") or "").splitlines()[0][:180]
                            if c_info.get("message")
                            else "",
                        }
                    )

                # Prevent false positive when local has unpushed commits ahead of remote
                is_update = (c_status in ("ahead", "diverged") and ahead_by > 0) or ahead_by > 0
                return {
                    "update_available": is_update,
                    "comparison_status": c_status,
                    "ahead_by": ahead_by,
                    "behind_by": behind_by,
                    "changed_files_count": len(files_list),
                    "changed_files_sample": summarize_changed_files(files_list, limit=files_limit),
                    "commits": commits_summary,
                }
            except Exception:
                pass

    # Fallback delta comparison against local /opt/floworkos/system/manifest.json
    local_manifest = load_json_safe(LOCAL_MANIFEST_FILE, {}) or {}
    local_files = local_manifest.get("files") if isinstance(local_manifest, dict) else {}
    remote_files = remote_meta.get("remote_manifest_files") or {}

    if isinstance(remote_files, dict) and remote_files and isinstance(local_files, dict):
        changed = []
        for rel, r_info in remote_files.items():
            if rel not in local_files:
                changed.append({"filename": rel, "status": "added", "additions": 0, "deletions": 0})
            elif local_files[rel].get("sha256") != r_info.get("sha256"):
                changed.append({"filename": rel, "status": "modified", "additions": 0, "deletions": 0})
        for rel in local_files:
            if rel not in remote_files:
                changed.append({"filename": rel, "status": "removed", "additions": 0, "deletions": 0})

        return {
            "update_available": len(changed) > 0,
            "comparison_status": "manifest_diff",
            "ahead_by": 1 if changed else 0,
            "behind_by": 0,
            "changed_files_count": len(changed),
            "changed_files_sample": changed[:files_limit],
            "commits": [
                {
                    "sha": remote_commit[:10],
                    "date": remote_meta.get("date", ""),
                    "author": remote_meta.get("author", ""),
                    "message": remote_meta.get("message", ""),
                }
            ],
        }

    head_sample = remote_meta.get("head_files_sample") or []
    return {
        "update_available": True,
        "comparison_status": "head_mismatch",
        "ahead_by": 1,
        "behind_by": 0,
        "changed_files_count": remote_meta.get("head_files_count", len(head_sample)),
        "changed_files_sample": head_sample[:files_limit],
        "commits": [
            {
                "sha": remote_commit[:10],
                "date": remote_meta.get("date", ""),
                "author": remote_meta.get("author", ""),
                "message": remote_meta.get("message", ""),
            }
        ],
    }


def build_agent_directive(repo: str, branch: str, local_commit: str, remote_meta: dict, delta: dict, dev_mode: bool, dev_reason: str, repo_stage: dict) -> tuple[dict, str, str]:
    remote_commit = remote_meta.get("sha", "unknown")
    local_short = (local_commit or "unknown")[:10]
    remote_short = remote_commit[:10]
    raw_ahead = delta.get("ahead_by")
    ahead_by = int(raw_ahead) if raw_ahead is not None else 1
    changed_count = int(delta.get("changed_files_count", 0) or 0)
    sample_files = [f.get("filename", "") for f in (delta.get("changed_files_sample") or []) if f.get("filename")]
    recent_commits = delta.get("commits") or []

    # Classify touched areas so the agent immediately prioritizes recommendations cleanly
    area_tags = sorted(
        {
            p.split("/", 2)[0] + ("/" + p.split("/", 2)[1] if "/" in p else "")
            for p in sample_files
            if p
        }
    )[:10]

    telemetry = {
        "repo": repo,
        "branch": branch,
        "local_commit": local_commit,
        "remote_commit": remote_commit,
        "local_short": local_short,
        "remote_short": remote_short,
        "comparison_status": delta.get("comparison_status", "ahead"),
        "ahead_by": ahead_by,
        "behind_by": int(delta.get("behind_by", 0) or 0),
        "commit_message": remote_meta.get("message", ""),
        "commit_author": remote_meta.get("author", ""),
        "commit_date": remote_meta.get("date", ""),
        "commit_url": remote_meta.get("html_url", ""),
        "changed_files_count": changed_count,
        "changed_files_sample": delta.get("changed_files_sample", []),
        "recent_commits": recent_commits,
        "affected_subsystems": area_tags,
        "dev_mode": dev_mode,
        "dev_reason": dev_reason,
        "repo_stage_dirty_files": repo_stage.get("dirty_count", 0),
    }

    dev_guard_note = (
        f"DEVELOPER MODE IS ACTIVE ({dev_reason}): DO NOT auto-run flowork-update --force or overwrite local modifications."
        if dev_mode
        else "Standard OTA mode: verify health & compatibility before recommending flowork-update."
    )
    files_preview = ", ".join(sample_files[:8]) if sample_files else "inspect upstream compare payload"

    ipc_instruction = (
        f"Upstream GitHub update detected on {repo} ({branch}): local {local_short} -> remote {remote_short} "
        f"({ahead_by} commit(s) ahead, {changed_count} file(s) changed; sample: {files_preview}). "
        f"If commit {remote_short} has not already been reviewed in this conversation: "
        f"1) Read-only inspect the upstream commit diff and affected subsystems ({', '.join(area_tags) or 'system core'}), "
        f"2) {dev_guard_note}, and "
        f"3) Present prioritized, actionable update recommendations (what changed, risk/impact, and exact safe update command or selective merge steps)."
    )

    commit_lines = "\n".join(
        f"- {c.get('sha', '')}: {c.get('message', '')} ({c.get('author', '')}, {c.get('date', '')})"
        for c in recent_commits[-5:]
    ) or f"- {remote_short}: {remote_meta.get('message', 'Upstream commit detected')}"

    file_lines = "\n".join(
        f"- [{f.get('status', 'modified')}] {f.get('filename', '')} (+{f.get('additions', 0)}/-{f.get('deletions', 0)})"
        for f in (delta.get("changed_files_sample") or [])[:15]
    ) or "- Run read-only compare inspection via curl/API or manifest diff."

    sidebar_prompt = (
        f"[ACTIVE TRIGGER: github_update_watch]\n"
        f"A new upstream update was pushed to GitHub repository '{repo}' (branch '{branch}').\n"
        f"- Local Commit: {local_short}\n"
        f"- Upstream Commit: {remote_short} ({ahead_by} commit(s) ahead, {changed_count} file(s) changed)\n"
        f"- Latest Commit Summary: {remote_meta.get('message', 'N/A')}\n"
        f"- Dev Mode Guard: {dev_guard_note}\n\n"
        f"Upstream Commits:\n{commit_lines}\n\n"
        f"Changed Files Sample:\n{file_lines}\n\n"
        f"Required Action:\n"
        f"Perform a read-only audit of the upstream changes (compare commits/files, check if local files have conflicts or unpushed changes, "
        f"and inspect /opt/floworkos/system/version.json + /opt/floworkos/bin/flowork-update --dry-run status without modifying files). "
        f"Then present clear, structured update recommendations covering: (1) What is new/fixed upstream, (2) Risk & dev-mode safety assessment, "
        f"and (3) Recommended update path (full delta OTA, selective cherry-pick, or defer). Wait for user approval before applying updates."
    )

    return telemetry, ipc_instruction, sidebar_prompt


def should_preserve_existing_emergency_signal(signal_path: str = SIGNAL_FILE) -> bool:
    existing = load_json_safe(signal_path)
    if not isinstance(existing, dict) or not existing.get("active", False):
        return False
    source = str(existing.get("source") or "")
    if source not in PRIORITY_CRITICAL_SOURCES:
        return False
    try:
        ts = float(existing.get("timestamp", 0))
        if ts > 1_000_000_000_000:
            ts /= 1000.0
        return (time.time() - ts) < ACTIVE_SIGNAL_TTL_SECS
    except Exception:
        return False


def clear_stale_self_signal(local_commit: str, signal_path: str = SIGNAL_FILE) -> None:
    existing = load_json_safe(signal_path)
    if not isinstance(existing, dict):
        return
    if existing.get("source") != "github_update_watch":
        return
    if existing.get("active", False):
        tel = existing.get("telemetry") or {}
        if tel.get("remote_commit") == local_commit or not tel.get("remote_commit"):
            updated = dict(existing)
            updated["active"] = False
            updated["cleared_at"] = int(time.time())
            atomic_write_json(signal_path, updated)


def publish_neural_bus_event(event_type: str, payload: dict) -> bool:
    try:
        bus_port = os.environ.get("FLOWORK_BUS_PORT", "18095")
        url = f"http://127.0.0.1:{bus_port}/api/bus/publish"
        data = json.dumps({"type": event_type, "source": "github_update_watch", "payload": payload}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=1.5) as _:
            return True
    except Exception:
        return False


def notify_desktop(title: str, body: str) -> None:
    try:
        env = dict(os.environ)
        if not env.get("DISPLAY"):
            env["DISPLAY"] = ":0"
        subprocess.run(
            ["notify-send", "-u", "normal", "-a", "Flowork OS", "-i", "system-software-update", title, body],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except Exception:
        pass


def discover_sidebar_socket() -> str | None:
    candidates = []
    user = os.environ.get("USER") or os.environ.get("LOGNAME")
    if not user:
        try:
            user = pwd.getpwuid(os.getuid()).pw_name
        except Exception:
            user = ""
    if user:
        candidates.append(f"/tmp/mrflow-sidebar-{user}.sock")
    try:
        for fn in sorted(os.listdir("/tmp")):
            if fn.startswith("mrflow-sidebar-") and fn.endswith(".sock"):
                full = os.path.join("/tmp", fn)
                if full not in candidates:
                    candidates.append(full)
    except Exception:
        pass
    for sock_path in candidates:
        if os.path.exists(sock_path):
            return sock_path
    return None


def send_sidebar_rpc(sock_path: str, payload: dict, timeout: float = 2.0) -> str:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(timeout)
    try:
        client.connect(sock_path)
        client.sendall(json.dumps(payload).encode("utf-8"))
        return client.recv(4096).decode("utf-8", errors="ignore").strip()
    finally:
        try:
            client.close()
        except Exception:
            pass


def update_sidebar_badge(telemetry: dict, update_available: bool) -> bool:
    sock_path = discover_sidebar_socket()
    if not sock_path:
        return False
    badge_payload = {
        "update_available": bool(update_available),
        "current_commit": str(telemetry.get("local_commit") or ""),
        "latest_commit": str(telemetry.get("remote_commit") or ""),
        "ahead_by": int(telemetry.get("ahead_by", 0) or 0),
        "dev_mode": bool(telemetry.get("dev_mode", False)),
    }
    js = f"if (window.onSystemUpdateChecked) {{ window.onSystemUpdateChecked({json.dumps(badge_payload)}); }}"
    try:
        resp = send_sidebar_rpc(sock_path, {"action": "eval_js", "code": js})
        return resp == "OK"
    except Exception:
        return False


def wake_mrflow_sidebar(remote_short: str, sidebar_prompt: str, dry_run: bool = False) -> tuple[bool, str]:
    if dry_run:
        return False, "dry_run_suppressed"
    sock_path = discover_sidebar_socket()
    if not sock_path:
        return False, "sidebar_socket_offline"
    try:
        status_raw = send_sidebar_rpc(sock_path, {"action": "status"})
        status_data = json.loads(status_raw) if status_raw else {}
        if status_data.get("is_busy", False):
            return False, "sidebar_busy"

        if not status_data.get("is_open", False):
            send_sidebar_rpc(sock_path, {"action": "show"})
            time.sleep(0.28)

        resp = send_sidebar_rpc(
            sock_path,
            {
                "action": "send_prompt",
                "source": "github_update_watch",
                "title": f"GitHub Upstream Update ({remote_short})",
                "new_session": True,
                "prompt": sidebar_prompt,
            },
        )
        return (resp == "OK"), ("woken" if resp == "OK" else f"unexpected_resp:{resp}")
    except Exception as exc:
        return False, f"socket_error:{exc}"


def check_cooldown_elapsed(cooldown_seconds: int) -> tuple[bool, float]:
    now = time.time()
    try:
        if os.path.isfile(LAST_ALERT_FILE):
            with open(LAST_ALERT_FILE, "r", encoding="utf-8") as handle:
                last_ts = float(handle.read().strip() or "0")
            remaining = cooldown_seconds - (now - last_ts)
            if remaining > 0:
                return False, round(remaining, 1)
    except Exception:
        pass
    return True, 0.0


def run_cycle(
    emit_alert: bool = True,
    force: bool = False,
    dry_run: bool = False,
    simulate_payload: dict | None = None,
    state_override_path: str | None = None,
    signal_override_path: str | None = None,
) -> dict:
    signal_path = signal_override_path or SIGNAL_FILE
    state_path = state_override_path or STATE_FILE
    cfg = load_trigger_config()
    repo, branch, version_data = resolve_repo_and_branch(cfg)
    local_commit = str(version_data.get("commit") or "").strip()
    dev_mode, dev_reason = check_dev_mode()
    repo_stage = get_local_repo_stage_status()
    state = load_json_safe(state_path, {}) or {}
    if not isinstance(state, dict):
        state = {}

    if simulate_payload is not None:
        remote_meta = dict(simulate_payload.get("remote_meta") or {})
        delta = dict(simulate_payload.get("delta") or {})
    else:
        remote_meta = fetch_github_head(repo, branch, state, force_no_etag=force)
        if not remote_meta.get("ok"):
            result = {
                "ok": False,
                "repo": repo,
                "branch": branch,
                "local_commit": local_commit,
                "update_available": False,
                "error": remote_meta.get("error", "Unknown network error"),
            }
            return result

        if remote_meta.get("etag"):
            state["etag"] = remote_meta["etag"]
        if remote_meta.get("raw_etag"):
            state["raw_etag"] = remote_meta["raw_etag"]

        # Persist clean metadata snapshot (without huge raw file maps)
        snapshot = {k: v for k, v in remote_meta.items() if k != "remote_manifest_files"}
        state["last_remote_meta"] = snapshot
        state["last_checked_at"] = int(time.time())

        remote_sha = str(remote_meta.get("sha") or "")
        remote_manifest_id = str(remote_meta.get("manifest_id") or "").strip()
        same_raw_manifest = False
        if remote_meta.get("source_channel") == "raw_manifest_gz" and remote_manifest_id:
            local_manifest = load_json_safe(LOCAL_MANIFEST_FILE, {}) or {}
            local_manifest_id = (
                str(local_manifest.get("manifest_id") or "").strip()
                if isinstance(local_manifest, dict)
                else ""
            )
            same_raw_manifest = bool(local_manifest_id and remote_manifest_id == local_manifest_id)

        if remote_sha == local_commit or same_raw_manifest:
            delta = {
                "update_available": False,
                "comparison_status": "identical",
                "ahead_by": 0,
                "behind_by": 0,
                "changed_files_count": 0,
                "changed_files_sample": [],
                "commits": [],
            }
            if remote_sha:
                state["cached_no_update_for_local"] = remote_sha
                state["cached_local_commit"] = local_commit
                state["last_comparison_status"] = "identical"
        elif (
            remote_sha
            and remote_sha == state.get("cached_no_update_for_local")
            and local_commit == state.get("cached_local_commit")
            and remote_meta.get("http_status") == 304
        ):
            delta = {
                "update_available": False,
                "comparison_status": state.get("last_comparison_status", "identical"),
                "ahead_by": 0,
                "behind_by": 0,
                "changed_files_count": 0,
                "changed_files_sample": [],
                "commits": [],
            }
        else:
            delta = inspect_upstream_delta(repo, local_commit, remote_meta, files_limit=cfg["compare_files_limit"])
            if not delta.get("update_available"):
                state["cached_no_update_for_local"] = remote_sha
                state["cached_local_commit"] = local_commit
                state["last_comparison_status"] = delta.get("comparison_status", "behind")

    remote_sha = str(remote_meta.get("sha") or "")
    update_available = bool(delta.get("update_available", False))
    telemetry, ipc_instruction, sidebar_prompt = build_agent_directive(
        repo, branch, local_commit, remote_meta, delta, dev_mode, dev_reason, repo_stage
    )

    if not update_available:
        state["pending_wakeup_commit"] = None
        if emit_alert and not dry_run:
            atomic_write_json(state_path, state)
            clear_stale_self_signal(local_commit, signal_path)
            update_sidebar_badge(telemetry, False)
        return {
            "ok": True,
            "update_available": False,
            "telemetry": telemetry,
            "wakeup": "none_up_to_date",
        }

    # Update badge even if alert/wakeup is deferred or rate-limited
    if emit_alert and not dry_run:
        update_sidebar_badge(telemetry, True)

    already_notified = (state.get("last_notified_commit") == remote_sha)
    already_woken = (state.get("last_woken_commit") == remote_sha)
    pending_for_same_commit = (state.get("pending_wakeup_commit") == remote_sha)
    cooldown_ok, cooldown_rem = check_cooldown_elapsed(cfg["cooldown_seconds"])

    action_status = "detected_read_only"
    signal_written = False
    sidebar_result = "skipped"

    if emit_alert:
        # 1. IPC signal + desktop notify + neural bus once per new upstream commit (cooldown guarded)
        if force or (not already_notified and (cooldown_ok or simulate_payload is not None)):
            if (not dry_run or signal_override_path) and not should_preserve_existing_emergency_signal(signal_path):
                ipc_payload = {
                    "active": True,
                    "source": "github_update_watch",
                    "timestamp": int(time.time()),
                    "telemetry": telemetry,
                    "instruction": ipc_instruction,
                }
                atomic_write_json(signal_path, ipc_payload)
                signal_written = True

            if not dry_run:
                atomic_write_text(LAST_ALERT_FILE, f"{int(time.time())}\n")
                state["last_notified_commit"] = remote_sha
                state["pending_wakeup_commit"] = remote_sha
                publish_neural_bus_event("system.github.update_detected", telemetry)
                notify_desktop(
                    f"Flowork OS GitHub Update ({telemetry['remote_short']})",
                    f"{telemetry['ahead_by']} new commit(s), {telemetry['changed_files_count']} file(s) changed. Waking Mr. Flow to review & recommend update.",
                )
            print(
                f"[ACTIVE_TRIGGER:github_update_watch] Upstream commit {telemetry['remote_short']} detected "
                f"({telemetry['ahead_by']} ahead, {telemetry['changed_files_count']} files).",
                flush=True,
            )

        # 2. Wake sidebar if newly pending or previously deferred while sidebar was busy
        should_attempt_wake = force or (
            not already_woken
            and (
                (not already_notified and (cooldown_ok or simulate_payload is not None))
                or pending_for_same_commit
            )
        )

        if should_attempt_wake:
            woken, reason = wake_mrflow_sidebar(telemetry["remote_short"], sidebar_prompt, dry_run=dry_run)
            sidebar_result = reason
            if woken:
                state["last_woken_commit"] = remote_sha
                state["pending_wakeup_commit"] = None
                action_status = "signal_and_agent_woken"
            elif reason == "sidebar_busy":
                state["pending_wakeup_commit"] = remote_sha
                action_status = "signal_written_waiting_for_idle_sidebar"
            else:
                state["pending_wakeup_commit"] = remote_sha if reason == "sidebar_socket_offline" else None
                action_status = f"signal_written_{reason}"
        elif not cooldown_ok and not already_notified:
            action_status = f"cooldown_active_{cooldown_rem}s_remaining"
        else:
            action_status = "already_notified_for_commit"

        if not dry_run:
            atomic_write_json(state_path, state)

    return {
        "ok": True,
        "update_available": True,
        "signal_written": signal_written,
        "sidebar_wakeup": sidebar_result,
        "action_status": action_status,
        "telemetry": telemetry,
        "instruction": ipc_instruction,
    }


def build_synthetic_simulation() -> dict:
    _, _, version_data = resolve_repo_and_branch(load_trigger_config())
    local_sha = str(version_data.get("commit") or "0000000000000000000000000000000000000000")
    sim_sha = "f10w0rk7300deadbeefcafe1234567890abcdef1"
    return {
        "remote_meta": {
            "ok": True,
            "http_status": 200,
            "source_channel": "simulation",
            "sha": sim_sha,
            "message": "fix(core): upstream security hardening & performance update (simulated)",
            "author": "Flowork OS Upstream",
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "html_url": f"https://github.com/flowork-os/flowork-os/commit/{sim_sha}",
        },
        "delta": {
            "update_available": True,
            "comparison_status": "ahead",
            "ahead_by": 2,
            "behind_by": 0,
            "changed_files_count": 3,
            "changed_files_sample": [
                {"filename": "core/bin/flowork-update", "status": "modified", "additions": 18, "deletions": 2},
                {"filename": "core/system/triger/supervisor.py", "status": "modified", "additions": 10, "deletions": 4},
                {"filename": "core/apps/mrflow-sidebar/bin/mrflow-sidebar.py", "status": "modified", "additions": 12, "deletions": 0},
            ],
            "commits": [
                {
                    "sha": sim_sha[:10],
                    "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "author": "Flowork OS Upstream",
                    "message": f"fix(core): simulated upstream delta over {local_sha[:8]}",
                }
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Flowork OS Active Trigger: GitHub Upstream Update Watcher")
    parser.add_argument("--check", action="store_true", help="One-shot read-only check printing JSON status")
    parser.add_argument("--once", action="store_true", help="Execute one watchdog evaluation cycle and exit")
    parser.add_argument("--force", action="store_true", help="Bypass ETag cache and cooldown on one-shot execution")
    parser.add_argument("--dry-run", action="store_true", help="Do not mutate state files or wake interactive sidebar")
    parser.add_argument("--simulate", action="store_true", help="Simulate an upstream GitHub update payload")
    args = parser.parse_args()

    sim_data = build_synthetic_simulation() if args.simulate else None

    if args.check:
        res = run_cycle(emit_alert=False, force=True, dry_run=True, simulate_payload=sim_data)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("ok") else 1)

    if args.once or args.simulate:
        if args.dry_run:
            with tempfile.TemporaryDirectory(prefix="flowork_ghwatch_sim_") as tmp_dir:
                res = run_cycle(
                    emit_alert=True,
                    force=args.force or args.simulate,
                    dry_run=True,
                    simulate_payload=sim_data,
                    state_override_path=os.path.join(tmp_dir, "state.json"),
                    signal_override_path=os.path.join(tmp_dir, "signal.json"),
                )
        else:
            res = run_cycle(
                emit_alert=True,
                force=args.force or args.simulate,
                dry_run=False,
                simulate_payload=sim_data,
            )
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("ok") else 1)

    # Continuous daemon mode (supervised by flowork-triggers-supervisor)
    atomic_write_text(PID_FILE, f"{os.getpid()}\n")
    print("[ACTIVE_TRIGGER:github_update_watch] Daemon initialized.", flush=True)

    # Initial delay avoids competing with desktop login startup burst
    time.sleep(10)

    while True:
        cfg = load_trigger_config()
        if not cfg["enabled"]:
            time.sleep(cfg["interval_seconds"])
            continue

        sleep_secs = cfg["interval_seconds"]
        try:
            res = run_cycle(emit_alert=True, force=False, dry_run=False)
            if res.get("action_status") == "signal_written_waiting_for_idle_sidebar":
                sleep_secs = cfg["busy_retry_seconds"]
        except Exception as exc:
            print(f"[ACTIVE_TRIGGER:github_update_watch] Iteration error: {exc}", file=sys.stderr, flush=True)

        time.sleep(sleep_secs)


if __name__ == "__main__":
    main()
