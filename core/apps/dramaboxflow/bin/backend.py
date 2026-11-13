#!/usr/bin/env python3
"""
👑 FLOWORK OS — DRAMABOX SOVEREIGN BACKEND SERVICE
High-speed scraper & streaming bridge for DramaBox short drama content.
"""

import os
import sys
import json
import re
import ssl
import urllib.request
import urllib.parse
from pathlib import Path

DATA_DIR = Path(os.path.expanduser("~/.flowork/data/dramaboxflow"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def _read_cache(cache_key: str):
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _write_cache(cache_key: str, data: dict):
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _http_get(url: str, timeout: int = 12, retries: int = 2) -> str:
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    )
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            last_err = e
            time.sleep(0.3)
    raise last_err or RuntimeError("HTTP GET failed")


def _extract_next_data(html: str) -> dict:
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except Exception:
        return {}


CATEGORY_SLUG_MAP = {
    454: "Kawin-Kontrak",
    464: "CEO-Wanita",
    456: "Nikah-Dulu-Cinta-Belakangan",
    450: "Kelahiran-Kembali",
    449: "Cinta-Pahit",
    470: "Orang-Kuat",
    442: "Naga",
    467: "Realitas",
}


def get_browse(page: int = 1, cat_id: int = 0, slug: str = "", lang: str = "in") -> dict:
    cache_key = f"browse_{lang}_{cat_id}_{page}"

    # 1. Primary: Official DramaBox API backend (Thousands of dramas)
    last_api_err = None
    for attempt in range(2):
        try:
            url = "https://www.webfic.com/webfic/home/browse"
            payload = json.dumps({
                "typeTwoId": int(cat_id) if cat_id else 0,
                "pageNo": int(page),
                "pageSize": 30
            }).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "pline": "DRAMABOX",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            if lang:
                headers["language"] = lang
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8")).get("data", {})
                book_list = data.get("bookList", [])
                types = data.get("types", [])
                pages = data.get("pages", 1)
                total = data.get("total", len(book_list))
                if book_list:
                    res = {
                        "status": "success",
                        "types": types,
                        "bookList": book_list,
                        "pageNo": int(page),
                        "pages": pages,
                        "total": total,
                        "source": "api"
                    }
                    _write_cache(cache_key, res)
                    if not cat_id and page == 1:
                        _write_cache("master_catalog", res)
                    return res
        except Exception as e:
            last_api_err = e
            time.sleep(0.4)

    # 2. Fallback: Web scraper
    if not slug and cat_id in CATEGORY_SLUG_MAP:
        slug = CATEGORY_SLUG_MAP[cat_id]

    if slug:
        url = f"https://www.dramabox.com/in/browse/{slug}?pageNo={page}"
    else:
        url = f"https://www.dramabox.com/in/browse?pageNo={page}"

    try:
        html = _http_get(url, timeout=10)
        data = _extract_next_data(html)
        props = data.get("props", {}).get("pageProps", {})
        book_list = props.get("bookList", [])
        if book_list:
            res = {
                "status": "success",
                "types": props.get("types", []),
                "bookList": book_list,
                "pageNo": props.get("pageNo", page),
                "pages": props.get("pages", 1),
                "total": props.get("total", len(book_list)),
                "source": "scraper"
            }
            _write_cache(cache_key, res)
            return res
    except Exception:
        pass

    # 3. Fallback: Disk Cache
    cached = _read_cache(cache_key)
    if cached and cached.get("bookList"):
        cached["source"] = "disk_cache"
        return cached

    master = _read_cache("master_catalog")
    if master and master.get("bookList"):
        master_copy = dict(master)
        master_copy["source"] = "master_cache"
        return master_copy

    return {"status": "error", "message": str(last_api_err or "Catalog temporarily unavailable"), "types": [], "bookList": []}


def search(query: str) -> dict:
    if not query.strip():
        return get_browse(1, 0)
    encoded = urllib.parse.quote(query)
    url = f"https://www.dramabox.com/in/search?keyword={encoded}"
    try:
        html = _http_get(url, timeout=10)
        data = _extract_next_data(html)
        props = data.get("props", {}).get("pageProps", {})
        book_list = props.get("bookList", [])
        search_list = props.get("searchList", [])
        similar_list = props.get("similarList", [])
        
        # Merge unique dramas by bookId
        seen = set()
        merged = []
        for item in (search_list + book_list + similar_list):
            bid = str(item.get("bookId") or item.get("id"))
            if bid and bid not in seen:
                seen.add(bid)
                merged.append(item)
        if merged:
            return {
                "status": "success",
                "query": query,
                "bookList": merged,
                "total": len(merged)
            }
    except Exception:
        pass

    # Fallback to local search across cached catalogs
    q_lower = query.lower()
    local_matches = []
    seen = set()
    for cf in CACHE_DIR.glob("*.json"):
        try:
            with open(cf, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                for item in cdata.get("bookList", []):
                    title = item.get("bookName") or item.get("title") or ""
                    bid = str(item.get("bookId") or item.get("id") or "")
                    if q_lower in title.lower() and bid not in seen:
                        seen.add(bid)
                        local_matches.append(item)
        except Exception:
            continue

    return {
        "status": "success" if local_matches else "error",
        "query": query,
        "bookList": local_matches,
        "total": len(local_matches),
        "source": "local_cache_search"
    }


GOODBOS_BASE = "https://dramabox.goodbos.online"
GOODBOS_TOKEN = "6EB57533425BC1D78ADA1F80354161D4"


def fetch_unlocked_episodes(book_id: str) -> list:
    """Fetch all unlocked episodes with direct stream CDN links via Goodbos API."""
    url = f"{GOODBOS_BASE}/api/dramabox/allepisode?bookId={book_id}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "okhttp/4.10.0",
            "x-token": GOODBOS_TOKEN,
        },
    )
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                return data
    except Exception as e:
        sys.stderr.write(f"[Goodbos Stream Error] {e}\n")
    return []


def get_drama_detail(book_id: str) -> dict:
    url = f"https://www.dramabox.com/in/video/{book_id}"
    book_info = {}
    chapter_list = []
    recommends = []

    try:
        html = _http_get(url)
        data = _extract_next_data(html)
        props = data.get("props", {}).get("pageProps", {})
        book_info = props.get("bookInfo", {})
        chapter_list = props.get("chapterList", [])
        recommends = props.get("recommends", [])
    except Exception as e:
        sys.stderr.write(f"[Scrape Error] {e}\n")

    # Fetch all unlocked episodes from upstream stream provider
    unlocked_eps = fetch_unlocked_episodes(book_id)

    if unlocked_eps:
        # Merge/enrich stream URLs into chapterList
        for idx, ep in enumerate(unlocked_eps):
            mp4_url = (
                ep.get("videoUrl720")
                or ep.get("videoUrl")
                or ep.get("videoUrl1080")
                or ep.get("videoUrl540")
            )
            ch_name = ep.get("chapterName") or f"Ep {idx + 1}"
            ch_id = str(ep.get("chapterId", idx))

            if idx < len(chapter_list):
                chapter_list[idx]["mp4"] = mp4_url
                chapter_list[idx]["unlock"] = True
                chapter_list[idx]["videoUrl720"] = ep.get("videoUrl720")
                chapter_list[idx]["videoUrl1080"] = ep.get("videoUrl1080")
            else:
                chapter_list.append({
                    "id": ch_id,
                    "name": ch_name,
                    "index": idx,
                    "indexStr": str(idx + 1).zfill(3),
                    "mp4": mp4_url,
                    "unlock": True,
                    "chapterPrice": 0,
                    "videoUrl720": ep.get("videoUrl720"),
                    "videoUrl1080": ep.get("videoUrl1080")
                })

    if not book_info and unlocked_eps:
        book_info = {
            "bookId": str(book_id),
            "bookName": f"Drama {book_id}",
            "chapterCount": len(chapter_list)
        }

    return {
        "status": "success",
        "bookInfo": book_info,
        "chapterList": chapter_list,
        "recommends": recommends,
        "totalChapters": len(chapter_list),
        "freeChapters": len([c for c in chapter_list if c.get("mp4")])
    }


def get_history() -> dict:
    if not HISTORY_FILE.exists():
        return {"status": "success", "history": []}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return {"status": "success", "history": json.load(f)}
    except Exception:
        return {"status": "success", "history": []}


def save_history(entry: dict) -> dict:
    history = get_history().get("history", [])
    # Filter out duplicate bookId
    history = [h for h in history if str(h.get("bookId")) != str(entry.get("bookId"))]
    history.insert(0, entry)
    history = history[:30]  # keep top 30
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_favorites() -> dict:
    if not FAVORITES_FILE.exists():
        return {"status": "success", "favorites": []}
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return {"status": "success", "favorites": json.load(f)}
    except Exception:
        return {"status": "success", "favorites": []}


def toggle_favorite(drama: dict) -> dict:
    favs = get_favorites().get("favorites", [])
    bid = str(drama.get("bookId"))
    found = any(str(f.get("bookId")) == bid for f in favs)
    if found:
        favs = [f for f in favs if str(f.get("bookId")) != bid]
        is_fav = False
    else:
        favs.insert(0, drama)
        is_fav = True
    try:
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(favs, f, ensure_ascii=False, indent=2)
        return {"status": "success", "isFavorite": is_fav, "favorites": favs}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def execute(payload: dict) -> dict:
    action = payload.get("cmd") or payload.get("action")
    if action == "browse":
        page = payload.get("page", 1)
        cat_id = payload.get("cat_id", 0)
        lang = payload.get("lang", "in")
        return get_browse(page=page, cat_id=cat_id, lang=lang)
    elif action == "search":
        query = payload.get("query", "")
        return search(query)
    elif action == "detail":
        book_id = payload.get("bookId")
        return get_drama_detail(book_id)
    elif action == "get_history":
        return get_history()
    elif action == "save_history":
        return save_history(payload.get("entry", {}))
    elif action == "get_favorites":
        return get_favorites()
    elif action == "toggle_favorite":
        return toggle_favorite(payload.get("drama", {}))
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "browse":
            print(json.dumps(get_browse(1, 0), indent=2))
        elif cmd == "detail" and len(sys.argv) > 2:
            print(json.dumps(get_drama_detail(sys.argv[2]), indent=2))
