#!/usr/bin/env python3
"""
👑 SHERLOCKCRAFT — FAST STREAMING & HIGH PRIORITY TARGET RECONNAISSANCE ENGINE
Categorized detection tiers:
- Tier 1: Core Top 40 Platforms (instant results <2s)
- Tier 2: Extended Top 100 Platforms (<5s)
- Tier 3: Deep Comprehensive 480+ Scan
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.error
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = "/opt/floworkos/apps/sherlockcraft/data/sites.json"

TOP_TIER_PLATFORMS = [
    "GitHub", "Twitter", "Reddit", "Instagram", "TikTok", "Telegram", "YouTube",
    "GitLab", "Steam", "HackerNews", "Medium", "Twitch", "Spotify", "Pinterest",
    "Patreon", "SoundCloud", "Discord", "Flickr", "DeviantART", "Disqus",
    "Goodreads", "Docker Hub", "Dribbble", "Behance", "Bitbucket", "Codecademy",
    "Pastebin", "Roblox", "Vimeo", "Substack", "Keybase", "Mastodon",
    "Chess", "Bandcamp", "Snapchat", "Kaggle", "ProductHunt", "About.me"
]

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
]

def load_sites_db():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: v for k, v in data.items() if not k.startswith("$") and isinstance(v, dict)}
        except Exception:
            pass
    return {}

def check_single_site(site_name, site_data, username, timeout=2.0):
    """Probe single platform using Sherlock logic with aggressive 3.5s timeout."""
    regex_pattern = site_data.get("regexCheck")
    if regex_pattern:
        try:
            if not re.search(regex_pattern, username):
                return {
                    "site": site_name,
                    "status": "ILLEGAL_FORMAT",
                    "url": site_data.get("url", "").replace("{}", username),
                    "time_ms": 0,
                    "exists": False
                }
        except Exception:
            pass

    target_url = site_data.get("url", "").replace("{}", username)
    probe_url = site_data.get("urlProbe", "").replace("{}", username) if site_data.get("urlProbe") else target_url
    error_type = site_data.get("errorType", "status_code")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    if "headers" in site_data and isinstance(site_data["headers"], dict):
        headers.update(site_data["headers"])

    start_time = time.time()
    try:
        req = urllib.request.Request(probe_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            elapsed = int((time.time() - start_time) * 1000)
            final_url = resp.geturl()
            code = resp.getcode()
            body = ""

            if error_type == "message":
                try:
                    body = resp.read(65536).decode("utf-8", errors="ignore")
                except Exception:
                    body = ""

            if error_type == "status_code":
                expected_error_code = site_data.get("errorCode", 404)
                if code == expected_error_code:
                    return {"site": site_name, "status": "AVAILABLE", "url": target_url, "time_ms": elapsed, "exists": False}
                elif code == 200:
                    return {"site": site_name, "status": "CLAIMED", "url": target_url, "time_ms": elapsed, "exists": True}

            elif error_type == "message":
                error_msgs = site_data.get("errorMsg", [])
                if isinstance(error_msgs, str):
                    error_msgs = [error_msgs]
                for msg in error_msgs:
                    if msg in body:
                        return {"site": site_name, "status": "AVAILABLE", "url": target_url, "time_ms": elapsed, "exists": False}
                return {"site": site_name, "status": "CLAIMED", "url": target_url, "time_ms": elapsed, "exists": True}

            elif error_type == "response_url":
                error_url = site_data.get("errorUrl", "")
                if error_url and error_url in final_url:
                    return {"site": site_name, "status": "AVAILABLE", "url": target_url, "time_ms": elapsed, "exists": False}
                elif final_url == target_url or final_url.endswith(username) or final_url.endswith(username + "/"):
                    return {"site": site_name, "status": "CLAIMED", "url": target_url, "time_ms": elapsed, "exists": True}
                else:
                    return {"site": site_name, "status": "AVAILABLE", "url": target_url, "time_ms": elapsed, "exists": False}

            return {"site": site_name, "status": "CLAIMED", "url": target_url, "time_ms": elapsed, "exists": True}

    except urllib.error.HTTPError as e:
        elapsed = int((time.time() - start_time) * 1000)
        if error_type == "status_code" and e.code in [404, 410]:
            return {"site": site_name, "status": "AVAILABLE", "url": target_url, "time_ms": elapsed, "exists": False}
        elif error_type == "message":
            try:
                err_body = e.read(16384).decode("utf-8", errors="ignore")
                error_msgs = site_data.get("errorMsg", [])
                if isinstance(error_msgs, str):
                    error_msgs = [error_msgs]
                if any(msg in err_body for msg in error_msgs):
                    return {"site": site_name, "status": "AVAILABLE", "url": target_url, "time_ms": elapsed, "exists": False}
            except Exception:
                pass
            return {"site": site_name, "status": "AVAILABLE", "url": target_url, "time_ms": elapsed, "exists": False}
        return {"site": site_name, "status": "ERROR", "code": e.code, "url": target_url, "time_ms": elapsed, "exists": False}

    except urllib.error.URLError:
        elapsed = int((time.time() - start_time) * 1000)
        return {"site": site_name, "status": "TIMEOUT", "url": target_url, "time_ms": elapsed, "exists": False}
    except Exception:
        elapsed = int((time.time() - start_time) * 1000)
        return {"site": site_name, "status": "ERROR", "url": target_url, "time_ms": elapsed, "exists": False}

def run_osint_scan(username, mode="top", max_workers=50):
    """Scan targets based on mode: 'top' (top 40 high-value), 'extended' (top 100), or 'all' (480+)."""
    all_sites = load_sites_db()
    if not all_sites:
        return {"status": "error", "error": "Database missing"}

    scan_list = {}
    if mode == "top":
        for name in TOP_TIER_PLATFORMS:
            if name in all_sites:
                scan_list[name] = all_sites[name]
    elif mode == "extended":
        for name in list(all_sites.keys())[:100]:
            scan_list[name] = all_sites[name]
    else:
        scan_list = all_sites

    claimed = []
    available = []
    errors = []

    start_scan = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_single_site, name, data, username): name for name, data in scan_list.items()}
        for future in as_completed(futures):
            res = future.result()
            if res.get("exists") and res.get("status") == "CLAIMED":
                claimed.append(res)
            elif res.get("status") in ["AVAILABLE", "ILLEGAL_FORMAT"]:
                available.append(res)
            else:
                errors.append(res)

    total_time = round(time.time() - start_scan, 2)
    claimed.sort(key=lambda x: x["site"].lower())

    return {
        "status": "success",
        "username": username,
        "mode": mode,
        "total_checked": len(scan_list),
        "total_claimed": len(claimed),
        "total_available": len(available),
        "total_errors": len(errors),
        "duration_seconds": total_time,
        "claimed": claimed,
        "available": available[:30]
    }

def execute(payload):
    action = payload.get("action")
    if action == "scan":
        raw_username = payload.get("username", "")
        username = raw_username.lstrip("@").strip()
        if not username:
            return {"status": "error", "error": "Username is required"}
        mode = payload.get("mode", "top") # default top 40 for instant fast UI feedback
        return run_osint_scan(username, mode=mode, max_workers=50)
    elif action == "catalog":
        sites = load_sites_db()
        return {"status": "success", "count": len(sites), "top_count": len(TOP_TIER_PLATFORMS)}
    else:
        return {"status": "error", "error": f"Unknown action: {action}"}

if __name__ == "__main__":
    t0 = time.time()
    res = run_osint_scan("elonmusk", mode="top")
    print(f"Top 40 scan finished in {time.time()-t0:.2f}s! Found: {len(res['claimed'])}")
