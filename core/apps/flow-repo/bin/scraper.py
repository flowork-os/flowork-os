#!/usr/bin/env python3
"""
👑 FLOWREPO SOVEREIGN MULTI-SOURCE SCRAPER ENGINE
Scrapes and archives trending & top open-source repositories from the inception
of GitHub (2008) up to 2026.

Sources:
1. Curated Historical Rankings (Top 100 across 17 languages: 1,700+ repositories)
2. Live GitHub Trending Scraper (Daily, Weekly, Monthly across multiple languages)
3. Direct SQLite database & JSON vault upsert with zero duplication
"""

import os
import sys
import re
import json
import sqlite3
import datetime
import urllib.request
import urllib.parse
import ssl
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "flowrepo.db")
JSON_BACKUP_PATH = os.path.join(DATA_DIR, "flowrepo.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain,*/*;q=0.8"
}

def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def format_stars(num):
    try:
        num = int(num)
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"{num / 1000:.0f}k"
        return str(num)
    except Exception:
        return str(num)

def parse_stars_int(star_str):
    try:
        s = str(star_str).strip().replace(',', '')
        if s.endswith('k') or s.endswith('K'):
            return int(float(s[:-1]) * 1000)
        elif s.endswith('M') or s.endswith('m'):
            return int(float(s[:-1]) * 1000000)
        return int(float(s))
    except Exception:
        return 0

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS repositories (
        full_name TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        stars TEXT NOT NULL,
        stars_num INTEGER NOT NULL,
        forks TEXT NOT NULL,
        language TEXT NOT NULL,
        desc TEXT NOT NULL,
        url TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        era TEXT NOT NULL,
        topics TEXT NOT NULL
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_repos_stars ON repositories (stars_num DESC);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_repos_era ON repositories (era);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_repos_lang ON repositories (language);")
    conn.commit()
    conn.close()

def determine_era(created_or_updated_str):
    try:
        m = re.search(r'(\d{4})', str(created_or_updated_str))
        if m:
            year = int(m.group(1))
            if year >= 2023:
                return "2023_2026"
            elif year >= 2020:
                return "2020_2022"
            elif year >= 2015:
                return "2015_2019"
            else:
                return "2008_2014"
    except Exception:
        pass
    return "2023_2026"

def upsert_repo(conn, repo_data):
    c = conn.cursor()
    c.execute("""
    INSERT INTO repositories
    (full_name, name, stars, stars_num, forks, language, desc, url, created_at, updated_at, era, topics)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(full_name) DO UPDATE SET
        stars=excluded.stars,
        stars_num=MAX(repositories.stars_num, excluded.stars_num),
        forks=excluded.forks,
        desc=CASE WHEN LENGTH(excluded.desc) > LENGTH(repositories.desc) THEN excluded.desc ELSE repositories.desc END,
        updated_at=excluded.updated_at
    """, (
        repo_data["full_name"],
        repo_data["name"],
        repo_data["stars"],
        repo_data["stars_num"],
        repo_data["forks"],
        repo_data["language"],
        repo_data["desc"],
        repo_data["url"],
        repo_data["created_at"],
        repo_data["updated_at"],
        repo_data["era"],
        repo_data["topics"]
    ))

def dump_json_backup():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM repositories ORDER BY stars_num DESC")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        with open(JSON_BACKUP_PATH, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)
        print(f"[FlowRepo Scraper] JSON vault updated: {len(rows)} repositories stored in {JSON_BACKUP_PATH}")
    except Exception as e:
        print(f"[FlowRepo Scraper] JSON backup warning: {e}", file=sys.stderr)

# ==============================================================================
# HARVESTER 1: HISTORICAL RANKINGS (Top 100 Across 17 Languages)
# ==============================================================================

HISTORICAL_FILES = [
    "Top-100-stars", "Python", "Rust", "Go", "JavaScript", "TypeScript",
    "CPP", "C", "Java", "PHP", "Ruby", "Kotlin", "Swift", "Shell",
    "Lua", "Dart", "HTML"
]

def scrape_historical_rankings():
    print("=" * 70)
    print("⏳ [FLOWREPO] HARVESTING HISTORICAL RANKINGS (2008 - 2026)...")
    print("=" * 70)
    
    init_db()
    conn = get_db()
    total_parsed = 0
    ctx = get_ssl_context()

    for item in HISTORICAL_FILES:
        url = f"https://raw.githubusercontent.com/EvanLi/Github-Ranking/master/Top100/{item}.md"
        print(f"-> Fetching {item} archive table...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Flowork-Scraper/2.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                
                # Parse markdown table rows: | rank | [name](url) | stars | forks | lang | issues | desc | updated |
                lines = [l for l in content.splitlines() if "|" in l and "[" in l and "github.com" in l]
                count_item = 0
                for line in lines:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 8:
                        # parts[2] is [name](url)
                        name_url_match = re.search(r'\[([^\]]+)\]\((https://github\.com/([^\)]+))\)', parts[2])
                        if not name_url_match:
                            continue
                        name = name_url_match.group(1)
                        url_val = name_url_match.group(2)
                        full_name = name_url_match.group(3)

                        stars_raw = parts[3]
                        stars_num = parse_stars_int(stars_raw)
                        stars_formatted = format_stars(stars_num)

                        forks_raw = parts[4]
                        forks_formatted = format_stars(parse_stars_int(forks_raw))

                        lang = parts[5] if parts[5] and parts[5] != "None" else (item if item != "Top-100-stars" and item != "CPP" else "C++")
                        desc = parts[7] if len(parts) > 7 and parts[7] else "Open source repository."
                        updated = parts[8][:10] if len(parts) > 8 and len(parts[8]) >= 10 else "2024-01-01"

                        era = determine_era(updated)

                        repo_data = {
                            "full_name": full_name,
                            "name": name,
                            "stars": stars_formatted,
                            "stars_num": stars_num,
                            "forks": forks_formatted,
                            "language": lang,
                            "desc": desc,
                            "url": url_val,
                            "created_at": updated,
                            "updated_at": updated,
                            "era": era,
                            "topics": f"{lang.lower()}, open-source, trending"
                        }
                        upsert_repo(conn, repo_data)
                        count_item += 1

                conn.commit()
                total_parsed += count_item
                print(f"   ✓ Added {count_item} repositories from {item}")
        except Exception as e:
            print(f"   ⚠️ Could not fetch {item}: {e}")

    conn.close()
    dump_json_backup()
    print(f"\n✅ Historical harvesting complete: {total_parsed} repositories processed.")
    return total_parsed

# ==============================================================================
# HARVESTER 2: LIVE GITHUB TRENDING (Daily, Weekly, Monthly)
# ==============================================================================

TRENDING_TARGETS = [
    ("", "overall-daily"),
    ("?since=weekly", "overall-weekly"),
    ("?since=monthly", "overall-monthly"),
    ("/python?since=monthly", "python-monthly"),
    ("/rust?since=monthly", "rust-monthly"),
    ("/javascript?since=monthly", "js-monthly"),
    ("/typescript?since=monthly", "ts-monthly"),
    ("/go?since=monthly", "go-monthly"),
    ("/c++?since=monthly", "cpp-monthly"),
    ("/c?since=monthly", "c-monthly"),
    ("/zig?since=monthly", "zig-monthly")
]

def scrape_live_trending():
    print("=" * 70)
    print("🔥 [FLOWREPO] SCRAPING LIVE GITHUB TRENDING...")
    print("=" * 70)

    init_db()
    conn = get_db()
    total_scraped = 0
    ctx = get_ssl_context()

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    for path_slug, label in TRENDING_TARGETS:
        url = f"https://github.com/trending{path_slug}"
        print(f"-> Scraping {label} ({url})...")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                articles = re.findall(r'<article[^>]*class=\"Box-row\"[^>]*>(.*?)</article>', html, re.DOTALL)
                
                count_target = 0
                for art in articles:
                    # Repo link
                    name_m = re.search(r'href=\"/([^/\" \n]+/[^/\" \n]+)\"', art)
                    if not name_m:
                        continue
                    full_name = name_m.group(1).strip()
                    if "/" not in full_name or full_name.startswith(("trending", "features", "topics", "events")):
                        continue
                    name = full_name.split("/")[1]

                    # Description
                    desc_m = re.search(r'<p[^>]*class=\"[^\"]*col-9[^\"]*\"[^>]*>(.*?)</p>', art, re.DOTALL)
                    desc = desc_m.group(1).strip() if desc_m else "Trending open-source project."
                    desc = re.sub(r'<[^>]+>', '', desc).strip()

                    # Language
                    lang_m = re.search(r'itemprop=\"programmingLanguage\">([^<]+)</span>', art)
                    language = lang_m.group(1).strip() if lang_m else "Code"

                    # Stars
                    stars_m = re.search(r'href=\"/[^/]+/[^/]+/stargazers\"[^>]*>\s*([0-9,kM\.]+)\s*</a>', art)
                    stars_raw = stars_m.group(1) if stars_m else "1k"
                    stars_num = parse_stars_int(stars_raw)

                    # Forks
                    forks_m = re.search(r'href=\"/[^/]+/[^/]+/forks\"[^>]*>\s*([0-9,kM\.]+)\s*</a>', art)
                    forks_raw = forks_m.group(1) if forks_m else "100"

                    # Era is modern/current
                    era = "2023_2026"

                    repo_data = {
                        "full_name": full_name,
                        "name": name,
                        "stars": format_stars(stars_num),
                        "stars_num": stars_num,
                        "forks": format_stars(parse_stars_int(forks_raw)),
                        "language": language,
                        "desc": desc,
                        "url": f"https://github.com/{full_name}",
                        "created_at": today_str,
                        "updated_at": today_str,
                        "era": era,
                        "topics": "trending, github, active"
                    }
                    upsert_repo(conn, repo_data)
                    count_target += 1

                conn.commit()
                total_scraped += count_target
                print(f"   ✓ Scraped {count_target} repositories from {label}")
                time.sleep(0.3)
        except Exception as e:
            print(f"   ⚠️ Scrape failed for {label}: {e}")

    conn.close()
    dump_json_backup()
    print(f"\n✅ Live trending scrape complete: {total_scraped} repositories processed.")
    return total_scraped

def run_full_harvest():
    t0 = time.time()
    h_count = scrape_historical_rankings()
    t_count = scrape_live_trending()
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM repositories")
    total = c.fetchone()[0]
    conn.close()

    duration = time.time() - t0
    print("\n" + "=" * 70)
    print(f"🎉 [FLOWREPO] HARVEST COMPLETED IN {duration:.1f}s")
    print(f"   TOTAL REPOSITORIES IN VAULT: {total}")
    print(f"   SQLITE DB: {DB_PATH}")
    print(f"   JSON VAULT: {JSON_BACKUP_PATH}")
    print("=" * 70)
    return total

if __name__ == "__main__":
    mode = "--all"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    if mode in ("--trending", "-t"):
        scrape_live_trending()
    elif mode in ("--historical", "-h"):
        scrape_historical_rankings()
    else:
        run_full_harvest()
