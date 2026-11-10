#!/usr/bin/env python3
"""
👑 FLOWORK OS — FLOWFS CORE ENGINE & VECTOR RETRIEVAL MODULE
Sovereign local semantic search, document embedding, and fast vector indexing.

Universal root: /opt/floworkos
Author: Flowork Architecture Board & Dr. Flow
"""

import os
import re
import time
import math
import hashlib
import sqlite3
import subprocess
import numpy as np

FLOWORK_ROOT = "/opt/floworkos"
DB_DIR = os.path.expanduser("~/.local/share/flowork")
DB_PATH = os.path.join(DB_DIR, "flowfs.vec.db")

VECTOR_DIM = 128
INDEXABLE_EXTENSIONS = {
    ".md", ".txt", ".py", ".json", ".toml", ".yaml", ".yml",
    ".conf", ".rs", ".js", ".html", ".css", ".sh", ".c", ".h"
}

IGNORE_DIRS = {
    ".git", "node_modules", "target", "__pycache__", ".cache",
    ".rustup", ".npm", ".gemini", "proc", "sys", "dev",
    "venv", ".venv", "site-packages", "dist-packages", "user_data_chrome", "user_data"
}

SEARCH_ROOTS = [
    "/opt/floworkos",
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/flowork-os-repo")
]

# In-memory matrix cache for instant search
_CACHE = {
    "db_mtime": 0,
    "matrix": None,
    "rows": []
}


def init_db(db_path=None):
    """Initialize SQLite database for file metadata and vector embeddings."""
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS flow_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime REAL NOT NULL,
            title TEXT,
            snippet TEXT,
            embedding BLOB NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_path ON flow_documents(path)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_filename ON flow_documents(filename)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS flow_screen_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            window_title TEXT,
            app_class TEXT,
            screenshot_path TEXT,
            thumbnail_path TEXT,
            extracted_text TEXT,
            embedding BLOB NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_screen_ts ON flow_screen_memory(timestamp)")
    try:
        cur.execute("ALTER TABLE flow_screen_memory ADD COLUMN thumbnail_path TEXT")
    except Exception:
        pass
    conn.commit()
    return conn


def text_to_vector(text, dim=VECTOR_DIM):
    """Generate normalized semantic hash projection vector from text."""
    words = re.findall(r"\w+", text.lower())
    if not words:
        vec = np.zeros(dim, dtype=np.float32)
        vec[0] = 1.0
        return vec

    vec = np.zeros(dim, dtype=np.float32)
    for w in words:
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) else -1.0
        weight = math.log1p(len(w))
        vec[idx] += sign * weight

    norm = np.linalg.norm(vec)
    if norm > 1e-6:
        vec /= norm
    return vec.astype(np.float32)


def extract_file_content(path, max_bytes=32768):
    """Safely extract title, snippet, and text from an indexable file."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_bytes)

        lines = [line.strip() for line in content.split("\n") if line.strip()]
        title = ""
        for line in lines[:5]:
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break
        if not title and lines:
            title = lines[0][:80]
        if not title:
            title = os.path.basename(path)

        snippet = " ".join(lines[:3])[:200]
        return title, snippet, content
    except Exception:
        return os.path.basename(path), "", ""


def index_files(db_path=None, verbose=True):
    """Scan and index all files in search roots with mtime incremental check."""
    path = db_path or DB_PATH
    conn = init_db(path)
    cur = conn.cursor()

    cur.execute("SELECT path, mtime FROM flow_documents")
    existing = {row[0]: row[1] for row in cur.fetchall()}

    indexed_count = 0
    updated_count = 0
    skipped_count = 0

    if verbose:
        print("🔍 FlowFS — Starting incremental semantic indexing...")

    batch_inserts = []
    seen_paths = set()

    for root_dir in SEARCH_ROOTS:
        if not os.path.isdir(root_dir):
            continue

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in INDEXABLE_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file)
                seen_paths.add(full_path)

                try:
                    stat = os.stat(full_path)
                    mtime = stat.st_mtime
                    size = stat.st_size
                except OSError:
                    continue

                if size > 5 * 1024 * 1024:
                    continue

                if full_path in existing:
                    if abs(existing[full_path] - mtime) < 1.0:
                        skipped_count += 1
                        continue
                    updated_count += 1
                else:
                    indexed_count += 1

                title, snippet, content = extract_file_content(full_path)
                combined_text = f"{file} {title} {content}"
                vec = text_to_vector(combined_text)

                batch_inserts.append((
                    full_path, file, ext, size, mtime, title, snippet, vec.tobytes()
                ))

                if len(batch_inserts) >= 200:
                    cur.executemany("""
                        INSERT OR REPLACE INTO flow_documents 
                        (path, filename, extension, size, mtime, title, snippet, embedding)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch_inserts)
                    conn.commit()
                    batch_inserts = []

    if batch_inserts:
        cur.executemany("""
            INSERT OR REPLACE INTO flow_documents 
            (path, filename, extension, size, mtime, title, snippet, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_inserts)
        conn.commit()

    stale_paths = set(existing.keys()) - seen_paths
    if stale_paths:
        cur.executemany("DELETE FROM flow_documents WHERE path = ?", [(p,) for p in stale_paths])
        conn.commit()

    conn.close()

    # Reset cache
    _CACHE["db_mtime"] = 0

    if verbose:
        print(f"✓ Indexing complete: {indexed_count} new, {updated_count} updated, {skipped_count} unchanged, {len(stale_paths)} purged.")
    return {"new": indexed_count, "updated": updated_count, "unchanged": skipped_count, "purged": len(stale_paths)}


def _load_cache(path):
    """Load or refresh matrix cache from database."""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0

    if _CACHE["matrix"] is not None and _CACHE["db_mtime"] == mtime and mtime > 0:
        return _CACHE["matrix"], _CACHE["rows"]

    conn = init_db(path)
    cur = conn.cursor()
    cur.execute("SELECT id, path, filename, extension, size, title, snippet, embedding FROM flow_documents")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        _CACHE["matrix"] = None
        _CACHE["rows"] = []
        _CACHE["db_mtime"] = mtime
        return None, []

    embeddings = []
    meta = []
    for r in rows:
        vec = np.frombuffer(r[7], dtype=np.float32)
        embeddings.append(vec)
        meta.append({
            "id": r[0],
            "path": r[1],
            "filename": r[2],
            "extension": r[3],
            "size": r[4],
            "title": r[5],
            "snippet": r[6]
        })

    matrix = np.vstack(embeddings)
    _CACHE["matrix"] = matrix
    _CACHE["rows"] = meta
    _CACHE["db_mtime"] = mtime
    return matrix, meta


def semantic_search(query, limit=10, db_path=None):
    """Perform vector cosine similarity search over indexed documents with in-process cache."""
    path = db_path or DB_PATH
    if not os.path.exists(path):
        index_files(path, verbose=False)

    matrix, meta_list = _load_cache(path)
    if matrix is None or len(meta_list) == 0:
        return []

    query_vec = text_to_vector(query)
    q_words = [w.lower() for w in re.findall(r"\w+", query)]

    # Compute dot products with all documents in single vectorized BLAS instruction
    scores = np.dot(matrix, query_vec)

    # Hybrid keyword & exact matching bonus
    for i, meta in enumerate(meta_list):
        fn_lower = meta["filename"].lower()
        title_lower = (meta["title"] or "").lower()
        snippet_lower = (meta["snippet"] or "").lower()

        for w in q_words:
            if len(w) < 3:
                continue
            if w in fn_lower:
                scores[i] += 0.25
            if w in title_lower:
                scores[i] += 0.15
            if w in snippet_lower:
                scores[i] += 0.05

    top_indices = np.argsort(scores)[::-1][:limit]

    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score <= 0.05:
            continue
        item = dict(meta_list[idx])
        item["score"] = round(score, 4)
        results.append(item)

    return results


def index_screen_capture(screenshot_path, window_title="", app_class="", text="", db_path=None):
    """Index an ambient desktop screen capture into FlowFS screen memory with semantic embedding."""
    path = db_path or DB_PATH
    conn = init_db(path)
    cur = conn.cursor()

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    combined = f"{window_title} {app_class} {text}".strip()
    if not combined:
        combined = os.path.basename(screenshot_path)

    vec = text_to_vector(combined)

    # Fast 320x180 WebP thumbnail generation via convert
    thumb_path = ""
    if os.path.exists(screenshot_path):
        thumb_dir = "/opt/floworkos/screenshots/thumbs"
        try:
            os.makedirs(thumb_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(screenshot_path))[0]
            thumb_candidate = os.path.join(thumb_dir, f"{base_name}_thumb.webp")
            if not os.path.exists(thumb_candidate):
                subprocess.run(
                    ["convert", screenshot_path, "-resize", "320x180^", "-gravity", "center", "-extent", "320x180", "-quality", "80", thumb_candidate],
                    capture_output=True, timeout=5
                )
            if os.path.exists(thumb_candidate):
                thumb_path = thumb_candidate
        except Exception:
            pass

    cur.execute("""
        INSERT INTO flow_screen_memory (timestamp, window_title, app_class, screenshot_path, thumbnail_path, extracted_text, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ts, window_title, app_class, screenshot_path, thumb_path, text, vec.tobytes()))
    conn.commit()
    conn.close()
    return {"timestamp": ts, "screenshot_path": screenshot_path, "thumbnail_path": thumb_path, "status": "indexed"}


def search_screen_memory(query, limit=5, db_path=None):
    """Search visual screen memory captures using semantic vector similarity."""
    path = db_path or DB_PATH
    conn = init_db(path)
    cur = conn.cursor()

    cur.execute("SELECT id, timestamp, window_title, app_class, screenshot_path, thumbnail_path, extracted_text, embedding FROM flow_screen_memory ORDER BY id DESC LIMIT 500")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return []

    q_vec = text_to_vector(query)
    q_norm = np.linalg.norm(q_vec)

    results = []
    for r in rows:
        emb = np.frombuffer(r[7], dtype=np.float32)
        dot = float(np.dot(q_vec, emb))
        emb_norm = float(np.linalg.norm(emb))
        sim = float(dot / (q_norm * emb_norm + 1e-9))

        results.append({
            "id": int(r[0]),
            "timestamp": str(r[1]),
            "window_title": str(r[2] or "Desktop"),
            "app_class": str(r[3] or ""),
            "screenshot_path": str(r[4]),
            "thumbnail_path": str(r[5] or ""),
            "text": str(r[6] or ""),
            "similarity": float(round(sim, 4))
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:limit]

