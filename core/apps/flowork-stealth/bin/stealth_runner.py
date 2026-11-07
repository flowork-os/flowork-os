#!/usr/bin/env python3
"""
Flowork Sovereign Stealth Runner
Spawns an interactive, persistent Camoufox C++ Anti-Detect browser session.
Maintains persistent user profiles, cookies, sessions, and hardware spoofing.
"""

import sys
import os
import json
import time
from pathlib import Path

# Add Camoufox virtualenv to sys.path
VENV_PATH = Path("/opt/floworkos/apps/camoufox/venv")
VENV_SITE = VENV_PATH / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
if VENV_SITE.exists() and str(VENV_SITE) not in sys.path:
    sys.path.insert(0, str(VENV_SITE))

from camoufox.sync_api import Camoufox

BASE_DIR = Path("/opt/floworkos/apps/flowork-stealth")
PROFILES_DIR = BASE_DIR / "profiles"
DB_FILE = BASE_DIR / "profiles.json"

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

    user_data = PROFILES_DIR / slug / "user_data"
    user_data.mkdir(parents=True, exist_ok=True)

    # Determine OS disguise
    target_os = p.get("os", "windows")
    if target_os not in ["windows", "macos", "linux"]:
        target_os = "windows"

    # Environment overrides
    env_vars = dict(os.environ)
    env_vars["DISPLAY"] = os.environ.get("DISPLAY", ":0")
    
    # Auto-resolve timezone from IP if possible, fallback to Asia/Jakarta
    env_vars.setdefault("TZ", "Asia/Jakarta")

    proxy_cfg = None
    if p.get("proxy"):
        raw_proxy = p["proxy"].strip()
        if raw_proxy:
            proxy_cfg = {"server": raw_proxy}

    print(f"[🚀] Launching Flowork Stealth Session for profile: '{slug}'")
    print(f"     Target OS Persona : {target_os}")
    print(f"     Persistent Profile: {user_data}")
    print(f"     Starting URL      : {target_url}")

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
            print(f"[!] Initial navigation note: {e}")

        print("[*] Flowork Stealth Browser running. Close browser window to exit session.")
        
        # Keep process alive until context is closed by user
        try:
            context.wait_for_event("close", timeout=0)
        except (KeyboardInterrupt, Exception):
            pass

    print(f"[✓] Session for profile '{slug}' closed cleanly.")

if __name__ == "__main__":
    main()
