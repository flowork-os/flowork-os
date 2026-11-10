#!/usr/bin/env python3
import sys
import os
import json
import sqlite3
from datetime import datetime

DB_PATH = '/opt/floworkos/history/episodic_memory.db'

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
                exit_code INTEGER DEFAULT 0
            )
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
        # Ensure sync triggers
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
    return conn

def main():
    try:
        raw_in = sys.stdin.read().strip()
        params = json.loads(raw_in) if raw_in else {}
        action = params.get('action', 'stats')

        conn = get_db()

        if action == 'index':
            category = params.get('category', 'general')
            problem = params.get('problem', '')
            solution = params.get('solution', '')
            kw_list = params.get('keywords', [])
            keywords = ', '.join(kw_list) if isinstance(kw_list, list) else str(kw_list)
            session_id = params.get('session_id', 'active_turn')
            ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

            if not problem or not solution:
                print(json.dumps({'status': 'error', 'message': 'problem and solution fields are required.'}))
                sys.exit(1)

            cur = conn.cursor()
            cur.execute("""
                INSERT INTO episodes (session_id, timestamp, category, problem, solution, keywords, exit_code)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (session_id, ts, category, problem, solution, keywords))
            conn.commit()
            print(json.dumps({'status': 'indexed', 'id': cur.lastrowid, 'category': category, 'keywords': keywords}))

        elif action == 'search':
            query = params.get('query', '').strip()
            if not query:
                print(json.dumps({'status': 'error', 'message': 'query string is required.'}))
                sys.exit(1)

            # Clean query for FTS5 syntax
            safe_query = ''.join(c if c.isalnum() or c in ' *' else ' ' for c in query)
            cur = conn.cursor()
            rows = cur.execute("""
                SELECT e.id, e.timestamp, e.category, e.problem, e.solution, e.keywords, rank
                FROM episodes_fts f
                JOIN episodes e ON f.rowid = e.id
                WHERE episodes_fts MATCH ?
                ORDER BY rank
                LIMIT 5
            """, (safe_query,)).fetchall()

            results = []
            for r in rows:
                results.append({
                    'id': r['id'],
                    'timestamp': r['timestamp'],
                    'category': r['category'],
                    'problem': r['problem'],
                    'solution': r['solution'],
                    'keywords': r['keywords'],
                    'rank': round(r['rank'], 3)
                })
            print(json.dumps({'status': 'ok', 'count': len(results), 'matches': results}, indent=2))

        elif action == 'stats':
            cur = conn.cursor()
            count = cur.execute('SELECT COUNT(*) FROM episodes').fetchone()[0]
            categories = [r[0] for r in cur.execute('SELECT DISTINCT category FROM episodes').fetchall()]
            size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
            print(json.dumps({
                'status': 'ok',
                'database': DB_PATH,
                'total_episodes': count,
                'categories': categories,
                'size_bytes': size_bytes
            }))

        else:
            print(json.dumps({'status': 'error', 'message': f'Unknown action {action}'}))
            sys.exit(1)

    except Exception as e:
        sys.stderr.write(f'Memory engine error: {e}')
        print(json.dumps({'status': 'error', 'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
