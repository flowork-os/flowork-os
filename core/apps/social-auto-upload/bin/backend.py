#!/usr/bin/env python3
"""
👑 FLOWORK OS — SOCIAL AUTO UPLOAD STUDIO BACKEND IPC SERVICE
Provides multi-account orchestration, authentication lifecycle, media management,
and multi-platform broadcast execution for both Human User and Sovereign Agent (Mr. Flow).
"""

import sys
import os
import json
import glob
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path("/opt/floworkos/apps/social-auto-upload")
COOKIES_DIR = BASE_DIR / "cookies"
DB_DIR = BASE_DIR / "db"
DOCUMENTS_DIR = Path("/opt/floworkos/documents")
SAU_BIN = "/opt/floworkos/bin/sau"
PYTHON_BIN = str(BASE_DIR / ".venv" / "bin" / "python")
HISTORY_FILE = DB_DIR / "upload_history.json"

PLATFORMS_META = {
    "youtube": {
        "id": "youtube",
        "name": "YouTube",
        "subtitle": "Shorts & Videos",
        "icon": "▶️",
        "color": "#ff0033",
        "supports_thumbnail": True,
        "supports_visibility": True,
        "supports_schedule": True
    },
    "instagram": {
        "id": "instagram",
        "name": "Instagram",
        "subtitle": "Reels & Feed",
        "icon": "📸",
        "color": "#e1306c",
        "supports_thumbnail": True,
        "supports_visibility": False,
        "supports_schedule": False
    },
    "douyin": {
        "id": "douyin",
        "name": "Douyin / TikTok",
        "subtitle": "Short-Form Video",
        "icon": "🎵",
        "color": "#00f2fe",
        "supports_thumbnail": True,
        "supports_visibility": True,
        "supports_schedule": True
    },
    "bilibili": {
        "id": "bilibili",
        "name": "Bilibili",
        "subtitle": "Anime & Tech Portal",
        "icon": "📺",
        "color": "#00a1d6",
        "supports_thumbnail": True,
        "supports_visibility": False,
        "supports_schedule": True
    },
    "facebook-page": {
        "id": "facebook-page",
        "name": "Facebook Page",
        "subtitle": "Meta Business Suite",
        "icon": "🌐",
        "color": "#1877f2",
        "supports_thumbnail": False,
        "supports_visibility": False,
        "supports_schedule": True
    },
    "tencent": {
        "id": "tencent",
        "name": "WeChat Channels",
        "subtitle": "Tencent Video Spheres",
        "icon": "🟢",
        "color": "#07c160",
        "supports_thumbnail": True,
        "supports_visibility": False,
        "supports_schedule": True
    },
    "xiaohongshu": {
        "id": "xiaohongshu",
        "name": "Xiaohongshu",
        "subtitle": "RED Creator Studio",
        "icon": "📕",
        "color": "#ff2442",
        "supports_thumbnail": True,
        "supports_visibility": False,
        "supports_schedule": False
    },
    "kuaishou": {
        "id": "kuaishou",
        "name": "Kuaishou",
        "subtitle": "Kwai Short Videos",
        "icon": "⚡",
        "color": "#ff7700",
        "supports_thumbnail": True,
        "supports_visibility": False,
        "supports_schedule": False
    }
}


def _ensure_dirs():
    COOKIES_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)


def _load_history():
    _ensure_dirs()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_history_entry(entry):
    _ensure_dirs()
    history = _load_history()
    history.insert(0, entry)
    # Retain last 200 items
    history = history[:200]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def list_accounts():
    """Scan cookies directory and return multi-account mapping per platform."""
    _ensure_dirs()
    accounts_by_platform = {pid: [] for pid in PLATFORMS_META.keys()}

    for item in COOKIES_DIR.glob("*.json"):
        filename = item.name
        if "_" in filename:
            parts = filename[:-5].split("_", 1)
            platform, account_name = parts[0], parts[1]
            if platform in accounts_by_platform:
                size_bytes = item.stat().st_size
                mtime_iso = datetime.fromtimestamp(item.stat().st_mtime, timezone.utc).isoformat()
                accounts_by_platform[platform].append({
                    "account": account_name,
                    "cookie_file": str(item),
                    "file_size": size_bytes,
                    "updated_at": mtime_iso,
                    "status": "cached"
                })

    result = []
    for pid, meta in PLATFORMS_META.items():
        accts = accounts_by_platform.get(pid, [])
        result.append({
            "platform": pid,
            "name": meta["name"],
            "subtitle": meta["subtitle"],
            "icon": meta["icon"],
            "color": meta["color"],
            "accounts": accts,
            "account_count": len(accts)
        })

    return {"status": "success", "platforms": result}


def check_account(platform, account):
    """Execute sau check command to verify login cookie validity."""
    if not platform or not account:
        return {"status": "error", "error": "Platform and account are required."}

    cmd = [SAU_BIN, platform, "check", "--account", account]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)

    try:
        proc = subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True, text=True, timeout=60)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        is_valid = ("valid" in stdout.lower() or proc.returncode == 0) and "invalid" not in stdout.lower()
        return {
            "status": "success",
            "platform": platform,
            "account": account,
            "valid": is_valid,
            "raw_output": stdout or stderr,
            "exit_code": proc.returncode
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Verification timed out after 60s."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def login_account(platform, account, headless=False):
    """Launch interactive browser on active DISPLAY for QR scan or credential login."""
    if not platform or not account:
        return {"status": "error", "error": "Platform and account are required."}

    env = os.environ.copy()
    if not env.get("DISPLAY"):
        env["DISPLAY"] = ":0"
    env["PYTHONPATH"] = str(BASE_DIR)

    cmd = [SAU_BIN, platform, "login", "--account", account]
    if headless:
        cmd.append("--headless")

    try:
        proc = subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True, text=True, timeout=600)
        cookie_path = COOKIES_DIR / f"{platform}_{account}.json"
        success = cookie_path.exists() and cookie_path.stat().st_size > 0
        return {
            "status": "success" if success else "error",
            "success": success,
            "platform": platform,
            "account": account,
            "cookie_exists": cookie_path.exists(),
            "raw_output": proc.stdout.strip() or proc.stderr.strip(),
            "exit_code": proc.returncode
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Interactive login timed out after 10 minutes."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def delete_account(platform, account):
    """Safely delete cookie file for specified profile."""
    cookie_path = COOKIES_DIR / f"{platform}_{account}.json"
    if cookie_path.exists():
        try:
            cookie_path.unlink()
            return {"status": "success", "message": f"Account '{account}' for {platform} deleted."}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    return {"status": "error", "error": "Account cookie not found."}


def list_media():
    """Scan documents and videos for media candidates and thumbnail graphics."""
    videos = []
    thumbnails = []
    scan_paths = [DOCUMENTS_DIR, BASE_DIR / "videos", BASE_DIR / "media"]

    video_exts = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
    image_exts = {".png", ".jpg", ".jpeg", ".webp"}

    for sp in scan_paths:
        if not sp.exists():
            continue
        for p in sp.glob("*"):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            try:
                stat = p.stat()
                size_mb = round(stat.st_size / (1024 * 1024), 2)
                item = {
                    "path": str(p),
                    "filename": p.name,
                    "stem": p.stem,
                    "size_mb": size_mb,
                    "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "source": sp.name
                }
                if ext in video_exts:
                    videos.append(item)
                elif ext in image_exts:
                    thumbnails.append(item)
            except Exception:
                continue

    # Sort descending by modification time
    videos.sort(key=lambda x: x["mtime"], reverse=True)
    thumbnails.sort(key=lambda x: x["mtime"], reverse=True)

    return {"status": "success", "videos": videos, "thumbnails": thumbnails}


def browse_file(target_type="video"):
    """Open native GTK file selection dialog via zenity."""
    env = os.environ.copy()
    if not env.get("DISPLAY"):
        env["DISPLAY"] = ":0"

    title = "Select Video File" if target_type == "video" else "Select Thumbnail Image"
    filter_arg = "Video Files | *.mp4 *.mov *.webm *.mkv *.avi" if target_type == "video" else "Image Files | *.png *.jpg *.jpeg *.webp"

    try:
        proc = subprocess.run(
            ["zenity", "--file-selection", f"--title={title}", f"--file-filter={filter_arg}"],
            capture_output=True, text=True, env=env
        )
        if proc.returncode == 0:
            selected_path = proc.stdout.strip()
            return {"status": "success", "file_path": selected_path}
        return {"status": "cancelled", "file_path": ""}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def upload_video(payload):
    """
    Execute multi-target upload across selected accounts.
    payload schema:
      - file: string (required)
      - title: string (required)
      - desc: string
      - tags: string
      - thumbnail: string
      - visibility: string ('public', 'unlisted', 'private')
      - schedule: string ('YYYY-MM-DD HH:MM')
      - targets: list of { platform: str, account: str }
      - headless: bool
    """
    video_path = payload.get("file")
    title = payload.get("title")
    desc = payload.get("desc", "")
    tags = payload.get("tags", "")
    thumbnail = payload.get("thumbnail")
    visibility = payload.get("visibility", "public")
    schedule = payload.get("schedule")
    targets = payload.get("targets", [])
    headless = payload.get("headless", True)

    if not video_path or not os.path.exists(video_path):
        return {"status": "error", "error": f"Video file not found: {video_path}"}
    if not title:
        return {"status": "error", "error": "Video title is required."}
    if not targets:
        return {"status": "error", "error": "At least one target account must be selected."}

    results = []
    overall_success = True

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    if not env.get("DISPLAY"):
        env["DISPLAY"] = ":0"

    for tgt in targets:
        platform = tgt.get("platform")
        account = tgt.get("account")
        if not platform or not account:
            continue

        cmd = [
            SAU_BIN, platform, "upload-video",
            "--account", account,
            "--file", os.path.abspath(video_path),
            "--title", title
        ]

        if desc:
            cmd.extend(["--desc", desc])
        if tags:
            cmd.extend(["--tags", tags])
        if thumbnail and os.path.exists(thumbnail):
            cmd.extend(["--thumbnail", os.path.abspath(thumbnail)])
        if visibility and platform in ("youtube", "douyin"):
            cmd.extend(["--visibility", visibility])
        if schedule and platform in ("youtube", "bilibili", "tencent", "douyin", "facebook-page"):
            cmd.extend(["--schedule", schedule])

        if headless:
            cmd.append("--headless")
        else:
            cmd.append("--headed")

        start_time = datetime.now(timezone.utc).isoformat()
        try:
            proc = subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True, text=True, timeout=600)
            success = (proc.returncode == 0)
            if not success:
                overall_success = False

            tgt_res = {
                "platform": platform,
                "account": account,
                "success": success,
                "exit_code": proc.returncode,
                "output": proc.stdout.strip() or proc.stderr.strip()
            }
            results.append(tgt_res)

            # Record in shared history ledger
            history_record = {
                "id": f"upl_{int(datetime.now().timestamp() * 1000)}_{platform}_{account}",
                "timestamp": start_time,
                "platform": platform,
                "account": account,
                "title": title,
                "file": video_path,
                "visibility": visibility,
                "success": success,
                "exit_code": proc.returncode,
                "output_snippet": tgt_res["output"][:400]
            }
            _save_history_entry(history_record)

        except subprocess.TimeoutExpired:
            overall_success = False
            results.append({
                "platform": platform,
                "account": account,
                "success": False,
                "exit_code": 124,
                "output": "Upload process timed out after 600s."
            })
        except Exception as e:
            overall_success = False
            results.append({
                "platform": platform,
                "account": account,
                "success": False,
                "exit_code": 1,
                "output": str(e)
            })

    return {
        "status": "success" if overall_success else "partial_error",
        "overall_success": overall_success,
        "results": results
    }


def execute(payload):
    """Main IPC entrypoint invoked by SovereignAppWindow runner."""
    if not isinstance(payload, dict):
        return {"status": "error", "error": "Payload must be a JSON dictionary."}

    action = payload.get("action")

    if action == "list_accounts":
        return list_accounts()
    elif action == "check_account":
        return check_account(payload.get("platform"), payload.get("account"))
    elif action == "login_account":
        return login_account(payload.get("platform"), payload.get("account"), payload.get("headless", False))
    elif action == "delete_account":
        return delete_account(payload.get("platform"), payload.get("account"))
    elif action == "list_media":
        return list_media()
    elif action == "browse_file":
        return browse_file(payload.get("type", "video"))
    elif action == "upload_video":
        return upload_video(payload)
    elif action == "get_history":
        return {"status": "success", "history": _load_history()}
    else:
        return {"status": "error", "error": f"Unknown action: {action}"}


if __name__ == "__main__":
    test_res = list_accounts()
    print(json.dumps(test_res, indent=2))
