#!/usr/bin/env python3
"""
ingest.py - YouTube Video/Concept Ingestion & Anti-Duplicate Gatekeeper.
Ingests reference video concepts, extracts core engineering/cognitive hooks,
and checks against the Sovereign REA Ledger before starting production.
"""

import sys
import os
import json
import subprocess
import argparse
from typing import Dict, Any, Optional

# Add skill directory to import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger


def extract_youtube_metadata(url: str) -> Dict[str, Any]:
    """
    Extracts metadata from YouTube URL using yt-dlp.
    """
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--skip-download",
        "--no-playlist",
        url
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout.strip().split("\n")[0])
            return {
                "source_id": data.get("id", ""),
                "title": data.get("title", ""),
                "url": url,
                "duration": data.get("duration", 0),
                "description": data.get("description", "")[:500],
                "channel": data.get("uploader", ""),
                "view_count": data.get("view_count", 0),
                "tags": data.get("tags", [])
            }
    except Exception as e:
        print(f"[WARN] yt-dlp extraction failed: {e}", file=sys.stderr)

    # Fallback if yt-dlp fails or URL is generic
    slug = ledger.slugify(url)
    return {
        "source_id": f"yt_{slug[:16]}",
        "title": url,
        "url": url,
        "duration": 60,
        "description": "",
        "channel": "Unknown",
        "view_count": 0,
        "tags": []
    }


def ingest_concept(url_or_title: str, force: bool = False) -> Dict[str, Any]:
    is_url = url_or_title.startswith("http://") or url_or_title.startswith("https://") or "youtube.com" in url_or_title or "youtu.be" in url_or_title

    if is_url:
        meta = extract_youtube_metadata(url_or_title)
        query_title = meta["title"]
        source_id = meta["source_id"]
        source_url = meta["url"]
    else:
        query_title = url_or_title
        source_id = f"manual_{ledger.slugify(query_title)[:16]}"
        source_url = ""
        meta = {
            "source_id": source_id,
            "title": query_title,
            "url": source_url,
            "duration": 0,
            "description": "",
            "channel": "Manual",
            "view_count": 0,
            "tags": []
        }

    # 1. Anti-Duplicate Check
    check = ledger.check_duplicate(query_title)
    if check["exists"] and not force:
        rec = check["record"]
        print("=" * 80)
        print("🚨 [DUPLICATE DETECTED] REA ALREADY EXISTS IN SOVEREIGN LEDGER!")
        print(f"Match Type:    {check['match_type']}")
        print(f"Title:         {rec['source_title']}")
        print(f"Slug:          {rec['topic_slug']}")
        print(f"Status:        {rec['status']}")
        print(f"Finished File: {rec.get('output_video_path', 'N/A')}")
        print("=" * 80)
        return {"status": "duplicate", "record": rec}

    # 2. Register new concept as in_progress
    slug = ledger.slugify(query_title)
    reg = ledger.register_rea(
        source_title=query_title,
        topic_slug=slug,
        source_url=source_url,
        source_id=source_id,
        status="in_progress",
        notes="Ingested via stickman-rea-engine ingest.py"
    )

    blueprint = {
        "status": "ready_for_rea",
        "slug": slug,
        "source_title": query_title,
        "source_url": source_url,
        "target_specs": {
            "aspect": "9:16 (1080x1920)",
            "fps": 30.00,
            "target_duration_s": "50-55 seconds",
            "word_count_range": "130-150 words",
            "words_per_minute": 150,
            "hook_duration_s": "0-3 seconds",
            "character_style": "100% 2D Soulful Stickman (No CAD/3D realism)",
            "audio_specs": "-14 LUFS (±2), -1 dBTP, 48000 Hz AAC mono",
            "finish_destination": "/home/awenkaudico/Documents/videos/finish/"
        },
        "screenplay_beats": [
            {"beat": 1, "time": "0-3s", "role": "Cognitive Gap / Visual Hook (shock, instant failure)"},
            {"beat": 2, "time": "3-12s", "role": "Common Intuition Misconception (why people think it works)"},
            {"beat": 3, "time": "12-25s", "role": "The Hidden Physical Flaw / Catastrophe (slapstick physics, squish, panic)"},
            {"beat": 4, "time": "25-42s", "role": "The Ingenious Engineering Solution (math, geometry, conical/clothoid curve)"},
            {"beat": 5, "time": "42-50s", "role": "Mindblow Payoff & Triumph (character celebrate, smooth ride)"},
            {"beat": 6, "time": "50-54s", "role": "Seamless Infinite Loop Linker back to second 0"}
        ]
    }

    print(json.dumps(blueprint, indent=2))
    return blueprint


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest video/concept for Stickman REA")
    parser.add_argument("query", help="YouTube URL or Topic Title")
    parser.add_argument("--force", action="store_true", help="Force ingestion even if duplicate exists")
    args = parser.parse_args()

    res = ingest_concept(args.query, args.force)
    if res.get("status") == "duplicate":
        sys.exit(2)
    sys.exit(0)
