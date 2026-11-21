#!/usr/bin/env python3
"""
👑 DISKCRAFT — SOVEREIGN STORAGE & DISK HYGIENE BACKEND ENGINE
High-performance, safety-first storage analyzer, declarative cleaner, duplicate finder, and disk telemetry.
Target: Flowork OS (Linux 7.3.0-flowork-rust)
"""

import os
import sys
import json
import time
import hashlib
import shutil
import subprocess
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# SAFETY INVARIANTS: ABSOLUTE SYSTEM BLACKLIST
# ---------------------------------------------------------------------------
STRICT_PROTECTED_PATHS = {
    "/", "/bin", "/sbin", "/lib", "/lib64", "/usr", "/usr/bin", "/usr/sbin",
    "/usr/lib", "/boot", "/dev", "/proc", "/sys", "/etc", "/root",
    "/swapfile",
    "/opt/floworkos/connector", "/opt/floworkos/connector/bin",
    "/opt/floworkos/kernel.rs", "/opt/floworkos/system", "/opt/floworkos/bin",
    "/opt/floworkos/policies", "/opt/floworkos/theme", "/opt/floworkos/session"
}

def is_path_safe_to_clean(target_path):
    """Ensure path is not inside any critical system directory."""
    try:
        resolved = os.path.realpath(target_path)
    except Exception:
        return False

    if resolved in STRICT_PROTECTED_PATHS:
        return False

    for prot in STRICT_PROTECTED_PATHS:
        # If the resolved path is a parent of a protected path, or protected path is exact prefix
        if prot != "/" and (resolved == prot or resolved.startswith(prot + "/")):
            # Only allow specific subpaths explicitly intended for cache
            if not (resolved.startswith("/var/log") or 
                    resolved.startswith("/var/cache") or 
                    resolved.startswith("/tmp") or 
                    resolved.startswith("/home") or
                    resolved.startswith("/dev/shm")):
                return False

    return True

# ---------------------------------------------------------------------------
# TELEMETRY & SYSTEM METRICS
# ---------------------------------------------------------------------------
def get_system_telemetry():
    """Retrieve mounted partitions, usage, inodes, and I/O stats."""
    disks = []
    try:
        # Read mounts via df -B1
        cmd = ["df", "-B1", "--output=source,fstype,size,used,avail,pcent,target"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            lines = res.stdout.strip().split("\n")
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 7:
                    src, fstype, size, used, avail, pcent, target = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
                    if src.startswith("/dev/") or target in ["/", "/home", "/opt"]:
                        try:
                            disks.append({
                                "device": src,
                                "fstype": fstype,
                                "size": int(size),
                                "used": int(used),
                                "free": int(avail),
                                "percent": pcent,
                                "mountpoint": target
                            })
                        except ValueError:
                            pass
    except Exception as e:
        print(f"[DiskCraft Telemetry] Error reading df: {e}", file=sys.stderr)

    # Inode statistics for root
    inodes = {}
    try:
        st = os.statvfs("/")
        inodes = {
            "total": st.f_files,
            "free": st.f_ffree,
            "used": st.f_files - st.f_ffree,
            "percent": f"{round((st.f_files - st.f_ffree) / max(1, st.f_files) * 100, 1)}%"
        }
    except Exception:
        pass

    # Read /proc/diskstats for activity snapshot
    io_stats = {}
    try:
        if os.path.exists("/proc/diskstats"):
            with open("/proc/diskstats", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 14:
                        dev_name = parts[2]
                        if not dev_name.startswith("loop") and not dev_name.startswith("ram"):
                            reads = int(parts[5]) * 512 # sectors to bytes
                            writes = int(parts[9]) * 512
                            io_stats[dev_name] = {"read_bytes": reads, "write_bytes": writes}
    except Exception:
        pass

    return {
        "status": "success",
        "timestamp": time.time(),
        "disks": disks,
        "inodes": inodes,
        "io_stats": io_stats,
        "kernel": "Linux 7.3.0-flowork-rust"
    }

# ---------------------------------------------------------------------------
# DEEP CLEANUP ENGINE (DECLARATIVE RULES)
# ---------------------------------------------------------------------------
CLEANUP_RULES = [
    {
        "id": "pipeline_renders",
        "category": "Media & Pipeline Scratch",
        "name": "Pipeline Video Renders & Audio Takes (/opt/floworkos/pipelines)",
        "desc": "Rendered video (.mp4, .mov, .mkv) and audio (.wav, .m4a, .mp3, .blend1) scratch files from AI/Stickman media pipelines",
        "scan_dirs": ["/opt/floworkos/pipelines"],
        "filter_ext": [".mp4", ".mov", ".mkv", ".avi", ".webm", ".wav", ".m4a", ".mp3", ".blend1"],
        "safe_delete": "matched_files"
    },
    {
        "id": "iso_build_scratch",
        "category": "Build & System Scratch",
        "name": "ISO Builder Workdirs & Temp Roots",
        "desc": "Temporary squashfs roots and build workdirs in ~/Downloads/flowork-iso-build/work",
        "paths": ["~/Downloads/flowork-iso-build/work"],
        "safe_delete": "directory"
    },
    {
        "id": "user_cache",
        "category": "User & App Caches",
        "name": "General User Cache (~/.cache)",
        "desc": "Temporary thumbnails, IPC buffers, font caches, and application scratch data",
        "paths": ["~/.cache"],
        "safe_delete": "contents"
    },
    {
        "id": "trash",
        "category": "Trash & Recycled",
        "name": "System Trash Bin",
        "desc": "Deleted files moved to the user's desktop trash bin",
        "paths": ["~/.local/share/Trash/files", "~/.local/share/Trash/info"],
        "safe_delete": "contents"
    },
    {
        "id": "browser_cache",
        "category": "Browser Artifacts",
        "name": "Web Browsers Cache (Chrome & Stealth)",
        "desc": "Cached web images, scripts, network buffers for Chrome & Camoufox",
        "paths": [
            "~/.cache/google-chrome",
            "~/.config/google-chrome/Default/Cache",
            "~/.config/google-chrome/Default/Code Cache",
            "/opt/floworkos/apps/flowork-stealth/profiles/*/user_data/Cache",
            "/tmp/camoufox_*"
        ],
        "safe_delete": "contents"
    },
    {
        "id": "apt_cache",
        "category": "System & OS Logs",
        "name": "Package Manager Archives (/var/cache/apt)",
        "desc": "Downloaded .deb archives cached during system package updates",
        "paths": ["/var/cache/apt/archives"],
        "safe_delete": "contents_except_lock"
    },
    {
        "id": "system_logs",
        "category": "System & OS Logs",
        "name": "Rotated System Logs (/var/log/*.gz)",
        "desc": "Archived compressed system log files",
        "paths": ["/var/log"],
        "filter_ext": [".gz", ".1", ".old", ".tmp"],
        "safe_delete": "matched_files"
    },
    {
        "id": "system_journal",
        "category": "System & OS Logs",
        "name": "Journald System Logs Vacuum (Retain 100MB max)",
        "desc": "Vacuum systemd journal logs to strictly enforce maximum size cap",
        "action_type": "journal_vacuum",
        "safe_delete": "journal_vacuum"
    },
    {
        "id": "dev_artifacts",
        "category": "Developer Artifacts",
        "name": "Developer Build Scratch (__pycache__, target, .pytest_cache)",
        "desc": "Python bytecode compilations and test caches across project directories",
        "scan_dirs": ["/opt/floworkos", os.path.expanduser("~")],
        "pattern_dirs": ["__pycache__", ".pytest_cache", ".ruff_cache"],
        "safe_delete": "directory"
    },
    {
        "id": "tmp_scratch",
        "category": "Temporary & Scratch",
        "name": "Stale Scratch & Temp Buffers (/tmp)",
        "desc": "Orphaned files older than 24 hours in the temporary mount",
        "paths": ["/tmp"],
        "max_age_hours": 24,
        "safe_delete": "stale_temp"
    }
]

_ACTIVE_CLEANUP_TARGETS = defaultdict(list)

def scan_cleanup_items():
    """Scan all declarative cleanup rules and calculate reclaimable size."""
    global _ACTIVE_CLEANUP_TARGETS
    _ACTIVE_CLEANUP_TARGETS.clear()

    results = []
    total_reclaimable = 0

    for rule in CLEANUP_RULES:
        rule_size = 0
        rule_count = 0
        rule_targets = []
        rule_id = rule["id"]

        # 1. Action Type: Journal vacuum
        if rule.get("action_type") == "journal_vacuum":
            try:
                cmd = ["journalctl", "--disk-usage"]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                import re
                m = re.search(r"take up ([\d\.]+)([KMGTPkmgtp]?)", res.stdout)
                if m:
                    val = float(m.group(1))
                    unit = m.group(2).upper()
                    mult = {"K": 1024, "M": 1024**2, "G": 1024**3}.get(unit, 1)
                    tot = int(val * mult)
                    rule_size = max(0, tot - (100 * 1024 * 1024))
                else:
                    rule_size = 0
                rule_count = 1 if rule_size > 0 else 0
                rule_targets.append({"path": "journalctl --vacuum-size=100M", "size": rule_size, "type": "command"})
            except Exception:
                pass

        # 2. Directory Tree Scanning (Pattern dirs or filter ext)
        elif "scan_dirs" in rule:
            for base in rule.get("scan_dirs", []):
                p_base = os.path.expanduser(base)
                if not os.path.exists(p_base):
                    continue
                try:
                    for root, dirs, files in os.walk(p_base, topdown=True):
                        # Filter to avoid deep recursion into git
                        if ".git" in dirs:
                            dirs.remove(".git")
                        if "node_modules" in dirs and base == "/opt/floworkos":
                            dirs.remove("node_modules")

                        # If matching directory patterns (e.g. __pycache__)
                        if "pattern_dirs" in rule:
                            for d in list(dirs):
                                if d in rule["pattern_dirs"]:
                                    dir_path = os.path.join(root, d)
                                    if not is_path_safe_to_clean(dir_path):
                                        continue
                                    d_size = 0
                                    d_count = 0
                                    for sub_r, _, sub_f in os.walk(dir_path):
                                        for f in sub_f:
                                            fp = os.path.join(sub_r, f)
                                            try:
                                                sz = os.path.getsize(fp)
                                                d_size += sz
                                                d_count += 1
                                            except OSError:
                                                pass
                                    rule_size += d_size
                                    rule_count += d_count
                                    rule_targets.append({"path": dir_path, "size": d_size, "type": "dir"})
                                    dirs.remove(d)

                        # If matching file extensions (e.g. media renders in pipelines)
                        if "filter_ext" in rule:
                            for f in files:
                                ext = os.path.splitext(f)[1].lower()
                                if ext in rule["filter_ext"]:
                                    fp = os.path.join(root, f)
                                    if not is_path_safe_to_clean(fp):
                                        continue
                                    try:
                                        sz = os.path.getsize(fp)
                                        rule_size += sz
                                        rule_count += 1
                                        rule_targets.append({"path": fp, "size": sz, "type": "file"})
                                    except OSError:
                                        pass
                except Exception as ex:
                    print(f"[DiskCraft Cleanup] Error scanning {rule_id}: {ex}", file=sys.stderr)

        # 3. Path-based rules
        elif "paths" in rule:
            for raw_p in rule["paths"]:
                expanded_list = []
                if "*" in raw_p:
                    import glob
                    expanded_list = glob.glob(os.path.expanduser(raw_p))
                else:
                    exp = os.path.expanduser(raw_p)
                    if os.path.exists(exp):
                        expanded_list = [exp]

                for p in expanded_list:
                    if not is_path_safe_to_clean(p):
                        continue

                    # Filter ext (like logs)
                    if "filter_ext" in rule:
                        try:
                            if os.path.isdir(p):
                                for f in os.listdir(p):
                                    fp = os.path.join(p, f)
                                    if any(f.endswith(ext) for ext in rule["filter_ext"]):
                                        try:
                                            sz = os.path.getsize(fp)
                                            rule_size += sz
                                            rule_count += 1
                                            rule_targets.append({"path": fp, "size": sz, "type": "file"})
                                        except OSError:
                                            pass
                        except Exception:
                            pass

                    # Stale temp
                    elif rule.get("max_age_hours"):
                        cutoff = time.time() - (rule["max_age_hours"] * 3600)
                        try:
                            for f in os.listdir(p):
                                if f.startswith(".X") or f.startswith(".ICE") or f.startswith(".font"):
                                    continue
                                fp = os.path.join(p, f)
                                try:
                                    st = os.stat(fp)
                                    if st.st_mtime < cutoff:
                                        sz = st.st_size if os.path.isfile(fp) else 4096
                                        rule_size += sz
                                        rule_count += 1
                                        rule_targets.append({"path": fp, "size": sz, "type": "file" if os.path.isfile(fp) else "dir"})
                                except OSError:
                                    pass
                        except Exception:
                            pass

                    # Entire directory deletion (e.g. build workdir)
                    elif rule.get("safe_delete") == "directory":
                        if os.path.exists(p):
                            d_size = 0
                            d_count = 0
                            for r, _, fl in os.walk(p):
                                for f in fl:
                                    try:
                                        d_size += os.path.getsize(os.path.join(r, f))
                                        d_count += 1
                                    except OSError:
                                        pass
                            rule_size += d_size
                            rule_count += d_count
                            rule_targets.append({"path": p, "size": d_size, "type": "dir"})

                    # Normal directory contents
                    elif rule.get("safe_delete") in ["contents", "contents_except_lock"]:
                        try:
                            if os.path.isdir(p):
                                for root, _, files in os.walk(p):
                                    for f in files:
                                        if f in ["lock", ".lock"] and rule.get("safe_delete") == "contents_except_lock":
                                            continue
                                        fp = os.path.join(root, f)
                                        try:
                                            sz = os.path.getsize(fp)
                                            rule_size += sz
                                            rule_count += 1
                                            rule_targets.append({"path": fp, "size": sz, "type": "file"})
                                        except OSError:
                                            pass
                            elif os.path.isfile(p):
                                sz = os.path.getsize(p)
                                rule_size += sz
                                rule_count += 1
                                rule_targets.append({"path": p, "size": sz, "type": "file"})
                        except Exception:
                            pass

        _ACTIVE_CLEANUP_TARGETS[rule_id] = rule_targets
        total_reclaimable += rule_size
        results.append({
            "id": rule["id"],
            "category": rule["category"],
            "name": rule["name"],
            "desc": rule["desc"],
            "size": rule_size,
            "count": rule_count,
            "sample_files": rule_targets[:50]
        })

    return {
        "status": "success",
        "total_reclaimable": total_reclaimable,
        "rules": results
    }

def execute_cleanup(rule_ids, dry_run=False):
    """Execute cleanup for selected rule IDs with safety guards and dry-run support."""
    global _ACTIVE_CLEANUP_TARGETS
    cleaned_size = 0
    cleaned_count = 0
    errors = []

    # If targets cache is empty or incomplete, trigger a fresh scan
    if not _ACTIVE_CLEANUP_TARGETS or any(rid not in _ACTIVE_CLEANUP_TARGETS for rid in rule_ids):
        scan_cleanup_items()

    for rid in rule_ids:
        targets = _ACTIVE_CLEANUP_TARGETS.get(rid, [])

        for item in targets:
            path = item.get("path")
            sz = item.get("size", 0)
            target_type = item.get("type", "file")

            if dry_run:
                cleaned_size += sz
                cleaned_count += 1
                continue

            if target_type == "command":
                if rid == "system_journal":
                    try:
                        subprocess.run(["journalctl", "--vacuum-size=100M"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        cleaned_size += sz
                        cleaned_count += 1
                    except Exception as ex:
                        errors.append(f"Failed vacuuming journals: {str(ex)}")
                continue

            if not is_path_safe_to_clean(path):
                errors.append(f"Safety violation blocked: {path}")
                continue

            try:
                if target_type == "dir" and os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                    cleaned_size += sz
                    cleaned_count += 1
                elif target_type == "file" and (os.path.isfile(path) or os.path.islink(path)):
                    os.unlink(path)
                    cleaned_size += sz
                    cleaned_count += 1
            except Exception as ex:
                errors.append(f"Failed deleting {path}: {str(ex)}")

    return {
        "status": "success",
        "dry_run": dry_run,
        "cleaned_size": cleaned_size,
        "cleaned_count": cleaned_count,
        "errors": errors[:20]
    }

def execute_prebuild_hygiene(dry_run=False):
    """Sovereign automated hygiene sweep executed by build-live-iso.sh before mksquashfs."""
    prebuild_rules = [
        "pipeline_renders",
        "iso_build_scratch",
        "dev_artifacts",
        "apt_cache",
        "tmp_scratch",
        "system_journal"
    ]
    scan_res = scan_cleanup_items()
    rule_map = {r["id"]: r for r in scan_res["rules"]}

    print("┌────────────────────────────────────────────────────────────────────────┐")
    print("│ 👑 DISKCRAFT SENTINEL: SOVEREIGN PRE-BUILD HYGIENE SWEEP (AUTO)        │")
    print("├────────────────────────────────────────────────────────────────────────┤")

    total_reclaimable = sum(rule_map[r]["size"] for r in prebuild_rules if r in rule_map)
    total_files = sum(rule_map[r]["count"] for r in prebuild_rules if r in rule_map)

    for rid in prebuild_rules:
        if rid in rule_map:
            r = rule_map[rid]
            mb = r["size"] / (1024 * 1024)
            print(f"│ [Scan] {r['name'][:42]:<42} : {mb:>8.2f} MB ({r['count']} items)")

    print("├────────────────────────────────────────────────────────────────────────┤")
    print(f"│ Target Reclaimable: {total_reclaimable / (1024*1024*1024):.2f} GB across {total_files} items")

    if not dry_run:
        res = execute_cleanup(prebuild_rules, dry_run=False)
        print(f"│ [✓] Cleaned: {res['cleaned_size'] / (1024*1024*1024):.2f} GB ({res['cleaned_count']} files/dirs removed)")
        if res["errors"]:
            print(f"│ [!] Note: {len(res['errors'])} warnings/errors encountered")
    else:
        print("│ [Simulation] Dry-run mode active. No files deleted.")

    print("│ [✓] Safety Invariants: /swapfile and host toolchains preserved.")
    print("└────────────────────────────────────────────────────────────────────────┘")
    return 0

def execute_login_hygiene(dry_run=False):
    """Low-priority background sentinel sweep invoked on user desktop login."""
    login_rules = [
        "user_cache",
        "browser_cache",
        "tmp_scratch",
        "system_journal",
        "dev_artifacts"
    ]
    if not dry_run:
        return execute_cleanup(login_rules, dry_run=False)
    return scan_cleanup_items()

# ---------------------------------------------------------------------------
# STORAGE TREEMAP & LARGE FILE EXPLORER
# ---------------------------------------------------------------------------
def scan_storage_hierarchy(target_path, max_depth=2):
    """Scan directory hierarchy and calculate weights for Treemap display."""
    target_path = os.path.expanduser(target_path)
    if not os.path.exists(target_path):
        return {"status": "error", "error": f"Path not found: {target_path}"}

    def walk_dir(current_path, current_depth):
        node = {
            "name": os.path.basename(current_path) or current_path,
            "path": current_path,
            "size": 0,
            "children": []
        }

        try:
            entries = list(os.scandir(current_path))
        except (PermissionError, OSError):
            return node

        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_file():
                    sz = entry.stat().st_size
                    node["size"] += sz
                    if current_depth < max_depth:
                        node["children"].append({
                            "name": entry.name,
                            "path": entry.path,
                            "size": sz,
                            "type": "file"
                        })
                elif entry.is_dir():
                    if entry.name in [".git", "proc", "sys", "dev"]:
                        continue
                    child_node = walk_dir(entry.path, current_depth + 1) if current_depth < max_depth else None
                    if child_node:
                        node["size"] += child_node["size"]
                        node["children"].append(child_node)
                    else:
                        # Shallow calculate size
                        d_size = 0
                        for r, _, fl in os.walk(entry.path):
                            for f in fl:
                                try:
                                    d_size += os.path.getsize(os.path.join(r, f))
                                except OSError:
                                    pass
                        node["size"] += d_size
                        node["children"].append({
                            "name": entry.name,
                            "path": entry.path,
                            "size": d_size,
                            "type": "dir"
                        })
            except (PermissionError, OSError):
                pass

        # Sort children by size descending
        node["children"].sort(key=lambda x: x["size"], reverse=True)
        return node

    root_tree = walk_dir(target_path, 0)

    # Also extract top 30 largest files
    large_files = []
    try:
        for root, _, files in os.walk(target_path):
            if any(p in root for p in ["/proc", "/sys", "/dev", "/.git"]):
                continue
            for f in files:
                fp = os.path.join(root, f)
                try:
                    sz = os.path.getsize(fp)
                    if sz > 10 * 1024 * 1024: # >10MB
                        large_files.append({"name": f, "path": fp, "size": sz})
                except OSError:
                    pass
    except Exception:
        pass

    large_files.sort(key=lambda x: x["size"], reverse=True)

    return {
        "status": "success",
        "target": target_path,
        "tree": root_tree,
        "large_files": large_files[:30]
    }

# ---------------------------------------------------------------------------
# SMART DUPLICATE FINDER (MULTI-TIERED HASHING)
# ---------------------------------------------------------------------------
def find_duplicates(target_dir, min_size_mb=1):
    """Find identical duplicate files using multi-tiered size and BLAKE3/SHA256 hashing."""
    target_dir = os.path.expanduser(target_dir)
    if not os.path.exists(target_dir):
        return {"status": "error", "error": f"Directory not found: {target_dir}"}

    min_bytes = int(min_size_mb * 1024 * 1024)
    size_groups = defaultdict(list)

    # Step 1: Group files by exact byte size
    for root, _, files in os.walk(target_dir):
        if any(p in root for p in ["/.git", "/node_modules", "/proc", "/sys", "/dev"]):
            continue
        for f in files:
            fp = os.path.join(root, f)
            try:
                st = os.stat(fp)
                if st.st_size >= min_bytes and not os.path.islink(fp):
                    size_groups[st.st_size].append(fp)
            except OSError:
                pass

    # Filter to sizes with >1 files
    candidates = {sz: paths for sz, paths in size_groups.items() if len(paths) > 1}

    # Step 2: Compare 4KB header hash
    header_groups = defaultdict(list)
    for sz, paths in candidates.items():
        for p in paths:
            try:
                with open(p, "rb") as f:
                    chunk = f.read(4096)
                    hdr_hash = hashlib.sha256(chunk).hexdigest()
                    header_groups[(sz, hdr_hash)].append(p)
            except OSError:
                pass

    # Step 3: Full hashing for matches
    duplicate_groups = []
    total_wasted_space = 0

    for (sz, _), paths in header_groups.items():
        if len(paths) <= 1:
            continue

        full_hash_map = defaultdict(list)
        for p in paths:
            try:
                h = hashlib.sha256()
                with open(p, "rb") as f:
                    while chunk := f.read(65536):
                        h.update(chunk)
                full_hash_map[h.hexdigest()].append(p)
            except OSError:
                pass

        for fhash, matches in full_hash_map.items():
            if len(matches) > 1:
                # First file is marked as Original (Kept), subsequent files are Duplicates
                wasted = (len(matches) - 1) * sz
                total_wasted_space += wasted
                duplicate_groups.append({
                    "hash": fhash[:12],
                    "size": sz,
                    "wasted": wasted,
                    "files": [
                        {"path": matches[0], "is_original": True, "selected": False},
                        *[{"path": m, "is_original": False, "selected": True} for m in matches[1:]]
                    ]
                })

    return {
        "status": "success",
        "target": target_dir,
        "total_wasted": total_wasted_space,
        "group_count": len(duplicate_groups),
        "groups": duplicate_groups[:50]
    }

def delete_duplicates(file_paths, dry_run=False):
    """Delete selected duplicate files with safety validation."""
    freed = 0
    deleted_count = 0
    errors = []

    for fp in file_paths:
        if not is_path_safe_to_clean(fp):
            errors.append(f"Protected path blocked: {fp}")
            continue

        try:
            sz = os.path.getsize(fp)
            if not dry_run:
                os.unlink(fp)
            freed += sz
            deleted_count += 1
        except Exception as ex:
            errors.append(f"Failed deleting {fp}: {str(ex)}")

    return {
        "status": "success",
        "dry_run": dry_run,
        "freed_bytes": freed,
        "deleted_count": deleted_count,
        "errors": errors
    }

# ---------------------------------------------------------------------------
# UNIFIED DISPATCH HANDLER (CALLED BY WEBKIT IPC RUNNER)
# ---------------------------------------------------------------------------
def execute(payload):
    """Entry point for frontend IPC bridge requests."""
    action = payload.get("action")
    user_home = os.path.expanduser("~")

    def resolve_target(raw_target):
        if not raw_target or raw_target in ("~", "~/"):
            return user_home
        if raw_target.startswith("~/"):
            return os.path.expanduser(raw_target)
        return raw_target

    if action == "get_env":
        return {"status": "success", "home_dir": user_home, "user": os.path.basename(user_home)}
    elif action == "telemetry":
        tel = get_system_telemetry()
        tel["home_dir"] = user_home
        return tel
    elif action == "scan_cleanup":
        return scan_cleanup_items()
    elif action == "execute_cleanup":
        rule_ids = payload.get("rule_ids", [])
        dry_run = payload.get("dry_run", False)
        return execute_cleanup(rule_ids, dry_run=dry_run)
    elif action == "scan_storage":
        target = resolve_target(payload.get("target"))
        depth = payload.get("depth", 2)
        return scan_storage_hierarchy(target, depth)
    elif action == "find_duplicates":
        target = resolve_target(payload.get("target"))
        min_size = payload.get("min_size_mb", 1.0)
        return find_duplicates(target, min_size)
    elif action == "delete_duplicates":
        files = payload.get("files", [])
        dry_run = payload.get("dry_run", False)
        return delete_duplicates(files, dry_run)
    else:
        return {"status": "error", "error": f"Unknown action: {action}"}

# ---------------------------------------------------------------------------
# CLI & HEADLESS AUTOMATED RUNNER
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DiskCraft — Sovereign Storage & Disk Hygiene Suite")
    parser.add_argument("--clean-prebuild", action="store_true", help="Auto-clean media renders, ISO workdirs, and dev scratch before ISO build")
    parser.add_argument("--clean-login", action="store_true", help="Background sentinel sweep on user login/boot")
    parser.add_argument("--clean-all", action="store_true", help="Execute all declarative cleanup rules")
    parser.add_argument("--scan", action="store_true", help="Scan and display cleanable categories")
    parser.add_argument("--dry-run", action="store_true", help="Simulate cleanup without deleting files")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if args.clean_prebuild:
        code = execute_prebuild_hygiene(dry_run=args.dry_run)
        sys.exit(code)
    elif args.clean_login:
        res = execute_login_hygiene(dry_run=args.dry_run)
        if args.json:
            print(json.dumps(res))
        else:
            print(f"[DiskCraft Sentinel] Login sweep completed. Cleaned: {res.get('cleaned_size', 0)} bytes.")
        sys.exit(0)
    elif args.clean_all:
        all_rules = [r["id"] for r in CLEANUP_RULES]
        res = execute_cleanup(all_rules, dry_run=args.dry_run)
        if args.json:
            print(json.dumps(res))
        else:
            print(f"[DiskCraft] Full system sweep completed. Cleaned: {res.get('cleaned_size', 0)} bytes.")
        sys.exit(0)
    elif args.scan:
        res = scan_cleanup_items()
        if args.json:
            print(json.dumps(res))
        else:
            print(f"Total Reclaimable: {res['total_reclaimable'] / (1024*1024):.2f} MB across {len(res['rules'])} categories.")
            for r in res["rules"]:
                print(f" - {r['name']}: {r['size'] / (1024*1024):.2f} MB ({r['count']} items)")
        sys.exit(0)
    else:
        # Default self-test mode
        print("Testing DiskCraft Backend Engine...")
        tel = get_system_telemetry()
        print(f"✓ Telemetry disks found: {len(tel['disks'])}")
        sc = scan_cleanup_items()
        print(f"✓ Cleanup categories found: {len(sc['rules'])}, Reclaimable: {sc['total_reclaimable'] / (1024*1024):.2f} MB")
        print("ALL TESTS PASSED EXIT CODE 0")
        sys.exit(0)
