#!/usr/bin/env python3
"""
Flowork OS Episodic Memory Engine (SQLite FTS5 + WAL)
- Concurrent-safe WAL + busy_timeout
- Deterministic SHA-256 fingerprint deduplication + FTS5 update triggers
- Secret & username scrubbing prior to persistence
- Syncs verified .fl_brain/*.md solution notes and harvests verified JSONL recoveries
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

FLOWORK_ROOT = os.environ.get("FLOWORK_ROOT", "/opt/floworkos")
DB_PATH = os.environ.get(
    "FLOWORK_EPISODIC_DB",
    os.path.join(FLOWORK_ROOT, "history", "episodic_memory.db"),
)

STOP_WORDS = {
    "the", "and", "for", "with", "from", "check", "status", "test", "that", "this",
    "what", "when", "where", "which", "have", "been", "were", "will", "your", "into",
    "file", "path", "code", "make", "help", "task", "error", "fix", "issue", "yang",
    "untuk", "dari", "dengan", "pada", "ini", "itu", "bisa", "cara", "tolong", "coba",
}

SECRET_PATTERNS = [
    (re.compile(r"AIza[0-9A-Za-z_-]{20,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bgh[pous]_[A-Za-z0-9_]{16,}"), "[REDACTED_GH_TOKEN]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "[REDACTED_GH_TOKEN]"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]{16,}"), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"(?i)(token|password|secret|api_key|apikey)\s*([:=])\s*['\"]?([^\s'\";,]{8,})['\"]?"), r"\1\2[REDACTED]"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def scrub_sensitive(text: str) -> str:
    if not text:
        return ""
    cleaned = text
    home = os.path.expanduser("~")
    if home and home != "/" and home != "$HOME":
        cleaned = cleaned.replace(home, "$HOME")
    for pattern, repl in SECRET_PATTERNS:
        cleaned = pattern.sub(repl, cleaned)
    return cleaned.strip()


def compute_fingerprint(category: str, problem: str) -> str:
    norm_cat = " ".join(category.lower().split())
    norm_prob = " ".join(problem.lower().split())[:240]
    digest_input = f"{norm_cat}|{norm_prob}".encode("utf-8", errors="ignore")
    return hashlib.sha256(digest_input).hexdigest()


def resolve_writable_db_path(db_path: str) -> str:
    abs_p = os.path.abspath(db_path)
    parent = os.path.dirname(abs_p)
    need_fallback = False
    if os.path.exists(abs_p):
        if not os.access(abs_p, os.W_OK) or not os.access(parent, os.W_OK):
            need_fallback = True
    elif os.path.exists(parent) and not os.access(parent, os.W_OK):
        need_fallback = True

    if need_fallback and not os.environ.get("FLOWORK_EPISODIC_DB"):
        user_db = os.path.join(os.path.expanduser("~"), ".flowork", "history", "episodic_memory.db")
        os.makedirs(os.path.dirname(user_db), exist_ok=True)
        if not os.path.exists(user_db) and os.path.isfile(abs_p) and os.access(abs_p, os.R_OK):
            import shutil
            shutil.copy2(abs_p, user_db)
            try:
                os.chmod(user_db, 0o644)
            except OSError:
                pass
        return user_db
    return abs_p


def get_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    db_path = resolve_writable_db_path(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=3000;")

    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TEXT,
                category TEXT,
                problem TEXT,
                solution TEXT,
                keywords TEXT,
                exit_code INTEGER DEFAULT 0,
                fingerprint TEXT,
                source TEXT DEFAULT 'manual',
                hit_count INTEGER DEFAULT 0
            )
        """)

        existing_cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(episodes)").fetchall()
        }
        if "fingerprint" not in existing_cols:
            conn.execute("ALTER TABLE episodes ADD COLUMN fingerprint TEXT")
        if "source" not in existing_cols:
            conn.execute("ALTER TABLE episodes ADD COLUMN source TEXT DEFAULT 'manual'")
        if "hit_count" not in existing_cols:
            conn.execute("ALTER TABLE episodes ADD COLUMN hit_count INTEGER DEFAULT 0")

        # Backfill missing fingerprints safely before creating unique index
        missing_rows = conn.execute(
            "SELECT id, category, problem FROM episodes WHERE fingerprint IS NULL OR fingerprint = ''"
        ).fetchall()
        for r in missing_rows:
            fp = compute_fingerprint(r["category"] or "general", r["problem"] or f"row_{r['id']}")
            conn.execute("UPDATE episodes SET fingerprint = ? WHERE id = ?", (fp, r["id"]))

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_episodes_fingerprint
            ON episodes(fingerprint)
            WHERE fingerprint IS NOT NULL AND fingerprint != ''
        """)

        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
                category,
                problem,
                solution,
                keywords,
                content='episodes',
                content_rowid='id'
            )
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS episodes_ai AFTER INSERT ON episodes BEGIN
                INSERT INTO episodes_fts(rowid, category, problem, solution, keywords)
                VALUES (new.id, new.category, new.problem, new.solution, new.keywords);
            END;
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS episodes_ad AFTER DELETE ON episodes BEGIN
                INSERT INTO episodes_fts(episodes_fts, rowid, category, problem, solution, keywords)
                VALUES('delete', old.id, old.category, old.problem, old.solution, old.keywords);
            END;
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS episodes_au AFTER UPDATE OF category, problem, solution, keywords ON episodes BEGIN
                INSERT INTO episodes_fts(episodes_fts, rowid, category, problem, solution, keywords)
                VALUES('delete', old.id, old.category, old.problem, old.solution, old.keywords);
                INSERT INTO episodes_fts(rowid, category, problem, solution, keywords)
                VALUES (new.id, new.category, new.problem, new.solution, new.keywords);
            END;
        """)
    return conn


def upsert_episode(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    category: str,
    problem: str,
    solution: str,
    keywords: str,
    source: str = "manual",
    exit_code: int = 0,
    timestamp: str | None = None,
) -> tuple[int, bool]:
    cat_clean = scrub_sensitive(category or "general")[:64] or "general"
    prob_clean = scrub_sensitive(problem)[:600]
    sol_clean = scrub_sensitive(solution)[:1600]
    kw_clean = scrub_sensitive(keywords)[:400]
    ts = timestamp or utc_now()
    fp = compute_fingerprint(cat_clean, prob_clean)

    with conn:
        existing = conn.execute(
            "SELECT id, solution, keywords FROM episodes WHERE fingerprint = ?",
            (fp,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE episodes
                SET session_id = ?, timestamp = ?, solution = ?, keywords = ?, source = ?, exit_code = ?
                WHERE id = ?
                """,
                (session_id, ts, sol_clean, kw_clean, source, exit_code, existing["id"]),
            )
            return int(existing["id"]), False

        cur = conn.execute(
            """
            INSERT INTO episodes (session_id, timestamp, category, problem, solution, keywords, exit_code, fingerprint, source, hit_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (session_id, ts, cat_clean, prob_clean, sol_clean, kw_clean, exit_code, fp, source),
        )
        return int(cur.lastrowid), True


def extract_query_tokens(query: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z0-9_]+", query.lower())
    seen = set()
    tokens = []
    for tok in raw_tokens:
        if len(tok) < 3 or tok in STOP_WORDS:
            continue
        if tok not in seen:
            seen.add(tok)
            tokens.append(tok)
    return tokens[:12]


def search_episodes(conn: sqlite3.Connection, query: str, limit: int = 5) -> list[dict]:
    limit = max(1, min(int(limit or 5), 10))
    tokens = extract_query_tokens(query)
    if not tokens:
        return []

    fts_expr = " OR ".join(f'"{t}"' for t in tokens)
    rows = conn.execute(
        """
        SELECT e.id, e.timestamp, e.category, e.problem, e.solution, e.keywords, e.source, e.hit_count,
               bm25(episodes_fts, 1.0, 4.0, 2.5, 3.0) AS score
        FROM episodes_fts f
        JOIN episodes e ON f.rowid = e.id
        WHERE episodes_fts MATCH ?
        ORDER BY score ASC
        LIMIT ?
        """,
        (fts_expr, limit),
    ).fetchall()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "timestamp": r["timestamp"],
            "category": r["category"],
            "source": r["source"],
            "problem": r["problem"],
            "solution": r["solution"],
            "keywords": r["keywords"],
            "hit_count": r["hit_count"],
            "rank": round(float(r["score"]), 3),
        })
    return results


def parse_fl_brain_markdown(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read().strip()
    except OSError:
        return None
    if not raw:
        return None

    title = os.path.splitext(os.path.basename(path))[0].replace("_", " ").title()
    category = "architecture"
    keywords: list[str] = []
    date_str = utc_now()
    body = raw

    if raw.startswith("---"):
        end_idx = raw.find("\n---", 3)
        if end_idx != -1:
            fm = raw[3:end_idx]
            body = raw[end_idx + 4:].strip()
            in_kws = False
            for line in fm.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith("- ") and in_kws:
                    kw = stripped[2:].strip().strip("\"'")
                    if kw:
                        keywords.append(kw)
                    continue
                if ":" in stripped:
                    k, v = stripped.split(":", 1)
                    key = k.strip().lower()
                    val = v.strip().strip("\"'")
                    in_kws = False
                    if key == "title" and val:
                        title = val
                    elif key == "category" and val:
                        category = val
                    elif key == "date" and val:
                        if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
                            date_str = f"{val}T00:00:00Z"
                        else:
                            date_str = val
                    elif key == "keywords":
                        if val.startswith("[") and val.endswith("]"):
                            for part in val[1:-1].split(","):
                                kw = part.strip().strip("\"'")
                                if kw:
                                    keywords.append(kw)
                        elif not val:
                            in_kws = True

    # Condense markdown body into crisp non-bloated engineering solution notes
    summary_lines = []
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("```") or s.startswith("# "):
            continue
        if any(ch in s for ch in ("┌", "┐", "└", "┘", "├", "┤", "──", "══", "║")):
            continue
        summary_lines.append(s)
        if sum(len(x) + 1 for x in summary_lines) >= 1200:
            break

    solution = "\n".join(summary_lines)[:1400]
    if not solution:
        solution = title

    return {
        "session_id": f"fl_brain:{os.path.basename(path)}",
        "category": category,
        "problem": title,
        "solution": solution,
        "keywords": ", ".join(keywords),
        "timestamp": date_str,
    }


def action_sync_brain(conn: sqlite3.Connection, brain_dir: str | None = None) -> dict:
    target_dir = brain_dir or os.path.join(FLOWORK_ROOT, ".fl_brain")
    if not os.path.isdir(target_dir):
        return {"status": "error", "message": f"Brain directory not found: {target_dir}"}

    inserted = 0
    updated = 0
    skipped = 0
    files = sorted(glob.glob(os.path.join(target_dir, "*.md")))
    for fp in files:
        parsed = parse_fl_brain_markdown(fp)
        if not parsed:
            skipped += 1
            continue
        _, is_new = upsert_episode(
            conn,
            session_id=parsed["session_id"],
            category=parsed["category"],
            problem=parsed["problem"],
            solution=parsed["solution"],
            keywords=parsed["keywords"],
            source="fl_brain",
            exit_code=0,
            timestamp=parsed["timestamp"],
        )
        if is_new:
            inserted += 1
        else:
            updated += 1

    return {
        "status": "ok",
        "brain_dir": target_dir,
        "files_scanned": len(files),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
    }


def action_harvest_chat(conn: sqlite3.Connection, chat_file: str | None = None) -> dict:
    candidates: list[str] = []
    if chat_file:
        if os.path.isfile(chat_file):
            candidates.append(chat_file)
        else:
            return {"status": "error", "message": f"Chat file not found: {chat_file}"}
    else:
        search_roots = [
            os.path.expanduser("~/.flowork/history/chats"),
            os.path.join(FLOWORK_ROOT, "history", "chats"),
        ]
        found = []
        for root in search_roots:
            if not os.path.isdir(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                if "subagent" in dirpath:
                    continue
                for fn in filenames:
                    if fn.endswith(".jsonl"):
                        full = os.path.join(dirpath, fn)
                        try:
                            found.append((os.path.getmtime(full), full))
                        except OSError:
                            pass
        found.sort(reverse=True)
        candidates = [p for _, p in found[:8]]

    inserted = 0
    updated = 0
    scanned_files = 0

    for fp in candidates:
        scanned_files += 1
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except OSError:
            continue

        session_id = os.path.splitext(os.path.basename(fp))[0]
        last_user_prompt = ""
        had_error_in_turn = False
        error_snippet = ""
        successful_tools: list[str] = []
        final_model_text = ""

        def flush_turn():
            nonlocal inserted, updated, had_error_in_turn, error_snippet, successful_tools, final_model_text
            if not last_user_prompt or not final_model_text or not successful_tools:
                return
            if not had_error_in_turn and len(successful_tools) < 2:
                return
            category = "recovery" if had_error_in_turn else "verified_workflow"
            problem = last_user_prompt.splitlines()[0].strip()[:220]
            if error_snippet:
                problem = f"{problem} | Prior error: {error_snippet[:160]}"
            tools_summary = ", ".join(dict.fromkeys(successful_tools))
            solution = f"Tools: {tools_summary}. Outcome: {final_model_text[:600]}"
            kws = ", ".join(sorted(set(extract_query_tokens(problem + " " + tools_summary)))[:10])
            _, is_new = upsert_episode(
                conn,
                session_id=session_id,
                category=category,
                problem=problem,
                solution=solution,
                keywords=kws,
                source="chat_harvest",
                exit_code=0,
            )
            if is_new:
                inserted += 1
            else:
                updated += 1

        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if "sessionId" in rec and not rec.get("type"):
                session_id = str(rec["sessionId"])
                continue

            rtype = rec.get("type")
            if rtype == "user":
                content = rec.get("content")
                if isinstance(content, list) and content and isinstance(content[0], dict) and "text" in content[0]:
                    flush_turn()
                    last_user_prompt = str(content[0]["text"]).strip()
                    had_error_in_turn = False
                    error_snippet = ""
                    successful_tools = []
                    final_model_text = ""
            elif rtype == "gemini":
                txt = str(rec.get("content") or "").strip()
                if txt:
                    final_model_text = txt
                for tc in rec.get("toolCalls") or []:
                    name = str(tc.get("name") or "")
                    status = str(tc.get("status") or "")
                    if status == "error":
                        had_error_in_turn = True
                        disp = str(tc.get("resultDisplay") or "").strip()
                        if disp and not error_snippet:
                            error_snippet = disp.splitlines()[0]
                    elif status == "success" and name:
                        successful_tools.append(name)

        flush_turn()

    return {
        "status": "ok",
        "files_scanned": scanned_files,
        "inserted": inserted,
        "updated": updated,
    }


def action_stats(conn: sqlite3.Connection) -> dict:
    count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    categories = [r[0] for r in conn.execute("SELECT DISTINCT category FROM episodes ORDER BY category").fetchall()]
    sources = {
        r[0] or "manual": r[1]
        for r in conn.execute("SELECT source, COUNT(*) FROM episodes GROUP BY source").fetchall()
    }
    wal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        "status": "ok",
        "database": DB_PATH,
        "wal_mode": wal_mode,
        "total_episodes": count,
        "categories": categories,
        "sources": sources,
        "size_bytes": size_bytes,
    }


def parse_cli_fallback(argv: list[str]) -> dict | None:
    if not argv:
        return None
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--sync-brain", action="store_true")
    parser.add_argument("--brain-dir", default=None)
    parser.add_argument("--search", default=None)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--harvest", nargs="?", const="", default=None)
    args = parser.parse_args(argv)
    if args.sync_brain:
        return {"action": "sync_brain", "brain_dir": args.brain_dir}
    if args.stats:
        return {"action": "stats"}
    if args.search is not None:
        return {"action": "search", "query": args.search, "limit": args.limit}
    if args.harvest is not None:
        return {"action": "harvest_chat", "chat_file": args.harvest or None}
    return None


def main():
    try:
        cli_params = parse_cli_fallback(sys.argv[1:])
        if cli_params is not None:
            params = cli_params
        else:
            raw_in = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
            params = json.loads(raw_in) if raw_in else {"action": "stats"}

        action = params.get("action", "stats")
        conn = get_db()

        if action == "index":
            category = params.get("category", "general")
            problem = params.get("problem", "")
            solution = params.get("solution", "")
            kw_list = params.get("keywords", [])
            keywords = ", ".join(kw_list) if isinstance(kw_list, list) else str(kw_list)
            session_id = params.get("session_id", "active_turn")
            source = params.get("source", "manual")
            exit_code = int(params.get("exit_code", 0))

            if not problem or not solution:
                print(json.dumps({"status": "error", "message": "problem and solution fields are required."}))
                sys.exit(1)

            row_id, is_new = upsert_episode(
                conn,
                session_id=session_id,
                category=category,
                problem=problem,
                solution=solution,
                keywords=keywords,
                source=source,
                exit_code=exit_code,
            )
            print(json.dumps({
                "status": "indexed" if is_new else "dedup_updated",
                "id": row_id,
                "category": category,
                "keywords": keywords,
            }))

        elif action == "search":
            query = str(params.get("query", "")).strip()
            if not query:
                print(json.dumps({"status": "error", "message": "query string is required."}))
                sys.exit(1)
            limit = int(params.get("limit", 5))
            results = search_episodes(conn, query, limit=limit)
            print(json.dumps({"status": "ok", "count": len(results), "matches": results}, indent=2))

        elif action == "sync_brain":
            res = action_sync_brain(conn, params.get("brain_dir"))
            print(json.dumps(res, indent=2))
            if res.get("status") != "ok":
                sys.exit(1)

        elif action == "harvest_chat":
            res = action_harvest_chat(conn, params.get("chat_file"))
            print(json.dumps(res, indent=2))
            if res.get("status") != "ok":
                sys.exit(1)

        elif action == "stats":
            print(json.dumps(action_stats(conn), indent=2))

        else:
            print(json.dumps({"status": "error", "message": f"Unknown action {action}"}))
            sys.exit(1)

    except Exception as e:
        sys.stderr.write(f"Memory engine error: {e}\n")
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

