#!/usr/bin/env python3
"""
👑 GITHUB TO YOUTUBE SOVEREIGN CLI HARNESS
Automates the lifecycle of converting trending GitHub repositories into
high-retention, 15+ minute stickman animated YouTube documentaries.
"""

import os
import sys
import json
import shutil
import sqlite3
import argparse
import subprocess
from datetime import datetime, timezone

FLOWREPO_DB = "/opt/floworkos/apps/flow-repo/data/flowrepo.db"
OUTPUT_DIR = "/opt/floworkos/documents/videos"

def search_social_buzz(topic):
    print(f"\n[*] Scouting social media buzz for topic: '{topic}' via last30days...")
    cmd = ["python3", "/opt/floworkos/skills/last30days/scripts/last30days.py", topic, "--emit=compact"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print(res.stdout[:1500])
        if len(res.stdout) > 1500:
            print("... (truncated)")
    except Exception as e:
        print(f"[!] Error executing last30days: {e}")

def harvest_flowrepo(query="", min_stars=1000, limit=10):
    print(f"\n[*] Querying FlowRepo vault for keyword: '{query}' (min stars: {min_stars})...")
    if not os.path.exists(FLOWREPO_DB):
        print(f"[!] FlowRepo DB not found at: {FLOWREPO_DB}")
        return []
    
    conn = sqlite3.connect(FLOWREPO_DB)
    c = conn.cursor()
    sql = """
        SELECT full_name, name, stars, stars_num, language, desc, url 
        FROM repositories 
        WHERE (full_name LIKE ? OR desc LIKE ? OR language LIKE ?)
          AND stars_num >= ?
        ORDER BY stars_num DESC 
        LIMIT ?
    """
    pattern = f"%{query}%"
    c.execute(sql, (pattern, pattern, pattern, min_stars, limit))
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("[-] No matching repositories found in FlowRepo database.")
        return []

    print(f"[+] Found {len(rows)} matching repositories:")
    for r in rows:
        print(f"  • [{r[2]} stars] {r[0]} ({r[4]}): {r[5][:75]}...")
        print(f"    URL: {r[6]}")
    return rows

def print_production_catalog():
    print(f"\n========================================================")
    print(f"🎬 GITHUB TO YOUTUBE PRODUCTION CATALOG ({OUTPUT_DIR})")
    print(f"========================================================")
    if not os.path.exists(OUTPUT_DIR):
        print("[-] No video output directory found.")
        return
    
    entries = sorted(os.listdir(OUTPUT_DIR))
    # 1. Check Theme Subfolders (Mandatory standard)
    theme_folders = [d for d in entries if os.path.isdir(os.path.join(OUTPUT_DIR, d))]
    for tf in theme_folders:
        tf_path = os.path.join(OUTPUT_DIR, tf)
        tf_files = os.listdir(tf_path)
        mp4s = [f for f in tf_files if f.endswith(".mp4")]
        print(f"📁 [THEME VAULT] {tf}/")
        for vid in sorted(mp4s):
            full_path = os.path.join(tf_path, vid)
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"   🎬 {vid} ({size_mb:.1f} MB)")
            srt = full_path.replace(".mp4", ".srt")
            seo = full_path.replace(".mp4", "_SEO.md")
            thumb = full_path.replace(".mp4", "_thumbnail.png")
            cs = full_path.replace(".mp4", "_contact_sheet.png")
            if os.path.exists(srt):
                print(f"      ✓ Subtitles: {os.path.basename(srt)}")
            if os.path.exists(seo):
                print(f"      ✓ SEO Package: {os.path.basename(seo)}")
            if os.path.exists(thumb):
                print(f"      ✓ High-CTR Thumbnail: {os.path.basename(thumb)}")
            if os.path.exists(cs):
                print(f"      ✓ Empirical Contact Sheet: {os.path.basename(cs)}")

    # 2. Check loose root files (if any exist)
    root_mp4s = [f for f in entries if f.endswith(".mp4") and os.path.isfile(os.path.join(OUTPUT_DIR, f))]
    if root_mp4s:
        print("\n⚠️ [LEGACY ROOT DELIVERABLES] (Move to theme subfolder):")
        for vid in root_mp4s:
            full_path = os.path.join(OUTPUT_DIR, vid)
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"  • {vid} ({size_mb:.1f} MB)")
    print(f"========================================================\n")

def main():
    parser = argparse.ArgumentParser(description="GitHub to YouTube Autonomous Video Foundry")
    parser.add_argument("--buzz", type=str, help="Research social buzz on topic via last30days")
    parser.add_argument("--harvest", type=str, default="", help="Query trending repositories in FlowRepo")
    parser.add_argument("--min-stars", type=int, default=1000, help="Minimum stars filter")
    parser.add_argument("--status", action="store_true", help="Print production catalog and deliverables")
    parser.add_argument("--render", type=str, help="Render longform documentary for topic/theme (e.g. 'billion-context')")
    parser.add_argument("--bg", type=str, help="Modular background image file for anti-duplicate multi-channel syndication")

    args = parser.parse_args()

    if args.status or len(sys.argv) == 1:
        print_production_catalog()
    if args.buzz:
        search_social_buzz(args.buzz)
    if args.harvest or "--harvest" in sys.argv:
        harvest_flowrepo(args.harvest, args.min_stars)
    if args.render:
        pipeline_map = {
            "billion-context": os.path.join(os.path.dirname(os.path.abspath(__file__)), "documentary_assembler.py"),
            "openclaw": os.path.join(os.path.dirname(os.path.abspath(__file__)), "openclaw_documentary_assembler.py"),
        }
        script = pipeline_map.get(args.render)
        if not script or not os.path.exists(script):
            print(f"[!] No pipeline found for theme '{args.render}'. Available: {list(pipeline_map.keys())}")
            sys.exit(1)
        render_cmd = ["python3", script]
        if args.bg:
            render_cmd.extend(["--bg", args.bg])
        print(f"[*] Launching production pipeline: {' '.join(render_cmd)}")
        subprocess.run(render_cmd, check=True)

if __name__ == "__main__":
    main()
