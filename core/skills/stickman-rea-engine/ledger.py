#!/usr/bin/env python3
"""
ledger.py - Persistent Deduplication Ledger for Viral Video REA (Remake) Pipeline.
Tracks reference YouTube source videos, topics, in-progress productions, and completed deliverables
to prevent duplicate remakes and ensure 100% unique catalog expansion.
"""

import sys
import os
import sqlite3
import json
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

DB_PATH = "/opt/floworkos/history/rea_registry.db"
JSON_EXPORT_PATH = "/opt/floworkos/history/rea_registry.json"


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rea_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT UNIQUE,
                source_url TEXT,
                source_title TEXT,
                topic_slug TEXT UNIQUE,
                status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'rejected')),
                output_video_path TEXT,
                duration_seconds REAL,
                created_at TEXT,
                completed_at TEXT,
                notes TEXT
            )
        """)
    sync_to_json()


def sync_to_json():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM rea_ledger ORDER BY id ASC").fetchall()
    data = [dict(r) for r in rows]
    with open(JSON_EXPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
    return text[:64]


def check_duplicate(query: str) -> Dict[str, Any]:
    """
    Checks if a query (URL, YouTube ID, title, or topic slug) already exists in the ledger.
    """
    init_db()
    conn = get_db_connection()
    clean_query = query.strip()
    slug = slugify(clean_query)

    # 1. Exact match on URL or ID
    row = conn.execute(
        "SELECT * FROM rea_ledger WHERE source_id = ? OR source_url = ? OR topic_slug = ?",
        (clean_query, clean_query, slug)
    ).fetchone()

    if row:
        return {"exists": True, "match_type": "exact", "record": dict(row)}

    # 2. Fuzzy substring match on title
    rows = conn.execute("SELECT * FROM rea_ledger WHERE source_title LIKE ?", (f"%{clean_query}%",)).fetchall()
    if rows:
        return {"exists": True, "match_type": "title_fuzzy", "record": dict(rows[0])}

    # 3. Word overlap similarity check
    query_words = set(re.findall(r'\w+', clean_query.lower()))
    all_rows = conn.execute("SELECT * FROM rea_ledger").fetchall()
    for r in all_rows:
        title_words = set(re.findall(r'\w+', (r['source_title'] or '').lower()))
        slug_words = set(r['topic_slug'].split('_'))
        combined = title_words | slug_words
        if len(query_words) >= 3 and len(query_words & combined) >= 3:
            return {"exists": True, "match_type": "concept_overlap", "record": dict(r)}

    return {"exists": False, "match_type": "none", "record": None}


def register_rea(
    source_title: str,
    topic_slug: Optional[str] = None,
    source_url: str = "",
    source_id: str = "",
    status: str = "in_progress",
    output_video_path: str = "",
    duration_seconds: float = 0.0,
    notes: str = ""
) -> Dict[str, Any]:
    init_db()
    conn = get_db_connection()
    slug = topic_slug or slugify(source_title)
    if not source_id:
        source_id = f"custom_{slug}"

    now = datetime.now(timezone.utc).isoformat()
    completed_at = now if status == "completed" else None

    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO rea_ledger 
            (source_id, source_url, source_title, topic_slug, status, output_video_path, duration_seconds, created_at, completed_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, source_url, source_title, slug, status, output_video_path, duration_seconds, now, completed_at, notes))

    sync_to_json()
    return check_duplicate(slug)


def complete_rea(topic_slug: str, output_video_path: str, duration_seconds: float = 0.0, notes: str = ""):
    init_db()
    conn = get_db_connection()
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute("""
            UPDATE rea_ledger
            SET status = 'completed', output_video_path = ?, duration_seconds = ?, completed_at = ?, notes = ?
            WHERE topic_slug = ? OR source_id = ?
        """, (output_video_path, duration_seconds, now, notes, topic_slug, topic_slug))
    sync_to_json()


def list_records() -> List[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM rea_ledger ORDER BY id ASC").fetchall()
    return [dict(r) for r in rows]


def seed_existing():
    init_db()
    # Deliverable 1: Railroads
    railroad_path = "/home/awenkaudico/Documents/videos/finish/STICKMAN_RAILROADS_VIRAL_9X16.mp4"
    if os.path.exists(railroad_path) or os.path.exists("/opt/floworkos/documents/videos/finish/STICKMAN_RAILROADS_VIRAL_9X16.mp4"):
        register_rea(
            source_title="Why Perfect Railroads Don't Work (Conical Wheels)",
            topic_slug="railroads_conical_wheels",
            source_url="https://youtube.com/shorts/reference_railroad",
            source_id="ref_railroads_01",
            status="completed",
            output_video_path="/home/awenkaudico/Documents/videos/finish/STICKMAN_RAILROADS_VIRAL_9X16.mp4",
            duration_seconds=54.6,
            notes="Deliverable #1: Railroad conical self-centering wheel animation."
        )

    # Deliverable 2: Coaster Loop
    coaster_path = "/home/awenkaudico/Documents/videos/finish/STICKMAN_COASTER_VIRAL_9X16.mp4"
    if os.path.exists(coaster_path) or os.path.exists("/opt/floworkos/documents/videos/finish/STICKMAN_COASTER_VIRAL_9X16.mp4"):
        register_rea(
            source_title="Why Roller Coasters NEVER Use Circle Loops (12G Clothoid Loop)",
            topic_slug="roller_coaster_circle_loop",
            source_url="https://youtube.com/shorts/reference_coaster",
            source_id="ref_coaster_02",
            status="completed",
            output_video_path="/home/awenkaudico/Documents/videos/finish/STICKMAN_COASTER_VIRAL_9X16.mp4",
            duration_seconds=54.8,
            notes="Deliverable #2: Roller coaster 1895 circular 12G lethal loop vs clothoid teardrop loop."
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ledger.py [init|check <query>|list|seed]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "init":
        init_db()
        print(f"Ledger initialized at {DB_PATH}")
    elif cmd == "seed":
        seed_existing()
        print("Seeded existing deliverables (Railroad & Coaster).")
    elif cmd == "check":
        if len(sys.argv) < 3:
            print("Error: query string required for check")
            sys.exit(1)
        res = check_duplicate(sys.argv[2])
        print(json.dumps(res, indent=2))
        if res["exists"]:
            sys.exit(2)  # Return non-zero if duplicate to allow shell piping
        sys.exit(0)
    elif cmd == "list":
        records = list_records()
        print(json.dumps(records, indent=2))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
