#!/usr/bin/env python3
"""
👑 FLOWORK OS — SOVEREIGN STEALTH RUNNER (HYBRID ENGINE)
Spawns an interactive, persistent anti-detect browser session.
Engine 1: Native Camoufox C++ anti-detect (if fetched).
Engine 2: Sovereign Chrome Stealth + Hardware Masking Extension (instant launch < 0.3s).
"""

import sys
import os
import re
import fcntl
import json
import glob
import shutil
import subprocess
from pathlib import Path

# Add Camoufox virtualenv to sys.path
VENV_PATH = Path("/opt/floworkos/apps/camoufox/venv")
VENV_SITE = VENV_PATH / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
if VENV_SITE.exists() and str(VENV_SITE) not in sys.path:
    sys.path.insert(0, str(VENV_SITE))

BASE_DIR = Path("/opt/floworkos/apps/flowork-stealth")
PROFILES_DIR = BASE_DIR / "profiles"
DB_FILE = BASE_DIR / "profiles.json"


def _parse_gecko_lock_pid(target):
    m = re.search(r":\+(\d+)$", target or "")
    return int(m.group(1)) if m else None


def _is_pid_active_gecko(pid):
    if pid is None or pid <= 0:
        return False
    proc_dir = Path(f"/proc/{pid}")
    if not proc_dir.exists():
        return False
    try:
        cmdline = (proc_dir / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", errors="ignore").lower()
        comm = (proc_dir / "comm").read_text(encoding="utf-8", errors="ignore").strip().lower()
        text = f"{comm} {cmdline}"
        return any(tok in text for tok in ("camoufox", "firefox", "gecko"))
    except OSError:
        return False


def _is_parentlock_held(parentlock: Path) -> bool:
    if not parentlock.exists():
        return False
    try:
        fd = os.open(str(parentlock), os.O_RDWR)
    except OSError:
        try:
            fd = os.open(str(parentlock), os.O_RDONLY)
        except OSError:
            return False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.lockf(fd, fcntl.LOCK_UN)
        except OSError as e:
            if e.errno in (11, 13):  # EAGAIN / EACCES
                fcntl.flock(fd, fcntl.LOCK_UN)
                return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    except BlockingIOError:
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def cleanup_stale_gecko_locks(user_data: Path) -> bool:
    """Safely remove stale Firefox/Camoufox lock files if no owning Gecko process is active."""
    lock_file = user_data / "lock"
    parentlock = user_data / ".parentlock"
    has_lock = os.path.lexists(lock_file)
    has_parent = os.path.lexists(parentlock)
    if not has_lock and not has_parent:
        return False

    if has_lock and os.path.islink(lock_file):
        try:
            pid = _parse_gecko_lock_pid(os.readlink(lock_file))
            if _is_pid_active_gecko(pid):
                return False
        except OSError:
            pass

    if _is_parentlock_held(parentlock):
        return False

    removed = []
    for path in (lock_file, parentlock):
        if os.path.lexists(path):
            try:
                os.unlink(path)
                removed.append(path.name)
            except OSError as e:
                print(f"[!] Warning removing stale lock {path}: {e}", file=sys.stderr)
    if removed:
        print(f"[!] Cleaned stale Gecko lock files in {user_data.name}: {', '.join(removed)}")
    return bool(removed)


def is_camoufox_installed():
    candidates = glob.glob(os.path.expanduser("~/.cache/camoufox/browsers/official/*/camoufox"))
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return True
    return False


def launch_chrome_stealth(slug, target_url, p):
    prof_dir = PROFILES_DIR / slug
    ext_dir = prof_dir / "extension"
    user_data = prof_dir / "user_data_chrome"
    user_data.mkdir(parents=True, exist_ok=True)

    # Ensure extension files exist
    if not (ext_dir / "manifest.json").exists() or not (ext_dir / "stealth.js").exists():
        from importlib.machinery import SourceFileLoader
        cli_mod = SourceFileLoader("flowork_stealth", str(BASE_DIR / "bin" / "flowork-stealth")).load_module()
        cli_mod.create_profile(
            p.get("profileName", slug),
            p.get("preset", "win11-rtx4070"),
            p.get("proxy"),
            p.get("notes", "")
        )

    chrome_bin = "/usr/local/bin/google-chrome"
    if not os.path.exists(chrome_bin):
        chrome_bin = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")

    if not chrome_bin or not os.path.exists(chrome_bin):
        raise FileNotFoundError("Google Chrome / Chromium binary not found on system.")

    width = p.get("screenWidth", 1920)
    height = p.get("screenHeight", 1080)

    cmd = [
        chrome_bin,
        f"--user-data-dir={user_data}",
        f"--load-extension={ext_dir}",
        "--new-window",
        "--no-first-run",
        "--no-default-browser-check",
        f"--window-size={width},{height}",
        "--class=flowork-stealth-browser",
        target_url
    ]

    if p.get("proxy"):
        cmd.append(f"--proxy-server={p['proxy'].strip()}")

    print(f"[🚀] Launching Flowork Native Chrome Stealth Engine for '{slug}'...")
    print(f"     Target URL: {target_url}")
    print(f"     Persona   : {p.get('platform', 'Win32')} ({p.get('os', 'windows').upper()})")
    print(f"     GPU       : {p.get('webglRenderer')}")
    print(f"     Seeds     : Canvas={p.get('canvasSeed')} | Audio={p.get('audioSeed')}")

    env_vars = dict(os.environ)
    env_vars["DISPLAY"] = os.environ.get("DISPLAY", ":0")

    proc = subprocess.Popen(cmd, env=env_vars, preexec_fn=os.setpgrp)
    print(f"[*] Flowork Chrome Stealth active (PID: {proc.pid}).")

    # Bring window to front
    try:
        subprocess.run(["wmctrl", "-x", "-a", "flowork-stealth-browser"], timeout=1, check=False)
    except Exception:
        pass

    return proc.pid


def launch_camoufox(slug, target_url, p):
    from camoufox.sync_api import Camoufox

    prof_dir = PROFILES_DIR / slug
    user_data = prof_dir / "user_data"
    user_data.mkdir(parents=True, exist_ok=True)
    cleanup_stale_gecko_locks(user_data)

    target_os = p.get("os", "windows")
    if target_os not in ["windows", "macos", "linux"]:
        target_os = "windows"

    env_vars = dict(os.environ)
    env_vars["DISPLAY"] = os.environ.get("DISPLAY", ":0")
    env_vars.setdefault("TZ", "Asia/Jakarta")

    proxy_cfg = None
    if p.get("proxy"):
        raw_proxy = p["proxy"].strip()
        if raw_proxy:
            proxy_cfg = {"server": raw_proxy}

    print(f"[🚀] Launching Flowork Camoufox Stealth Session: '{slug}'...")
    with Camoufox(
        persistent_context=True,
        user_data_dir=str(user_data),
        headless=False,
        humanize=True,
        geoip=True,
        os=target_os,
        proxy=proxy_cfg,
        env=env_vars
    ) as context:
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_navigation_timeout(60000)
        try:
            page.goto(target_url, wait_until="domcontentloaded")
        except Exception as e:
            print(f"[!] Navigation note: {e}")

        print("[*] Camoufox session active. Close browser window to exit.")
        try:
            context.wait_for_event("close", timeout=0)
        except (KeyboardInterrupt, Exception):
            pass


def main():
    if len(sys.argv) < 2:
        print("Usage: stealth_runner.py <profile_slug> [target_url]")
        sys.exit(1)

    slug = sys.argv[1]
    target_url = sys.argv[2] if len(sys.argv) > 2 else "https://iphey.com"

    cfg_file = PROFILES_DIR / slug / "config.json"
    if not cfg_file.exists():
        if DB_FILE.exists():
            with open(DB_FILE, "r") as f:
                db = json.load(f)
                if slug in db:
                    p = db[slug]
                else:
                    print(f"[!] Profile '{slug}' not found.")
                    sys.exit(1)
        else:
            print(f"[!] Config for '{slug}' not found.")
            sys.exit(1)
    else:
        with open(cfg_file, "r") as f:
            p = json.load(f)

    # Hybrid Launch Strategy:
    # 1. If Camoufox binary is already fetched, use Camoufox.
    # 2. Otherwise (or on Camoufox error), seamlessly launch Native Chrome Stealth instantly (< 0.3s).
    if is_camoufox_installed():
        try:
            launch_camoufox(slug, target_url, p)
            return
        except Exception as err:
            print(f"[!] Camoufox failed ({err}). Falling back to Native Chrome Stealth...")

    launch_chrome_stealth(slug, target_url, p)


if __name__ == "__main__":
    main()
