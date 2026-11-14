#!/usr/bin/env python3
"""
👑 FLOWORK OS — DRAMABOX & MELOLO SOVEREIGN BACKEND SERVICE
High-speed scraper, catalog engine & streaming bridge for:
1. DramaBox (1,845+ Indonesian & 2,000+ Global dramas via Goodbos CDN)
2. Melolo Short Dramas (3,400+ titles via Tencent EdgeOne CDN streaming proxy)
"""

import os
import sys
import json
import time
import random
import ssl
import re
import socket
import threading
import http.server
import urllib.request
import urllib.parse
from pathlib import Path

CACHE_DIR = Path.home() / ".flowork" / "data" / "dramaboxflow" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = CACHE_DIR / "history.json"
FAVORITES_FILE = CACHE_DIR / "favorites.json"
MELOLO_SYSTEM_CATALOG = Path("/opt/floworkos/apps/dramaboxflow/assets/melolo_catalog.json")

# Stream Proxy Port
STREAM_PROXY_PORT = 19842
_PROXY_SERVER = None
_MELOLO_SIGN_CACHE = {}  # key: (slug, ep) -> (url, expiry_ts)

# -------------------------------------------------------------
# MELOLO STREAMING PROXY (Range support, signed URL & Referer)
# -------------------------------------------------------------
def get_melolo_signed_url(slug: str, ep: int = 1) -> str:
    key = f"{slug}:{ep}"
    now = time.time()
    if key in _MELOLO_SIGN_CACHE:
        cached_url, exp = _MELOLO_SIGN_CACHE[key]
        if now < exp:
            return cached_url

    # 1. Primary: Direct Melolo Next.js API (/api/series/getSeriesBySlug)
    try:
        refresh_key = f"{int(now * 1000)}-{random.random()}"
        api_url = f"https://melolo.com/api/series/getSeriesBySlug?language=id&series_slug={slug}&pageType=play&episode_id={ep}&_refresh={refresh_key}"
        req = urllib.request.Request(api_url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"https://melolo.com/id/dramas/{slug}"
        })
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
            series = data.get("data", [{}])[0]
            ep_list = series.get("episode_list", [])
            for item in ep_list:
                if int(item.get("episode_id", 0)) == int(ep):
                    target = item.get("url", "")
                    if target and "?sign=" in target:
                        clean_url = target.replace("\\u0026", "&")
                        _MELOLO_SIGN_CACHE[key] = (clean_url, now + 7200)
                        return clean_url
    except Exception as e:
        sys.stderr.write(f"Melolo API getSeriesBySlug error for {slug} ep {ep}: {e}\n")

    # 2. Fallback: Direct episode web page scrape (/id/dramas/{slug}/ep{ep})
    page_urls = [
        f"https://melolo.com/id/dramas/{slug}/ep{ep}" if ep > 1 else f"https://melolo.com/id/dramas/{slug}",
        f"https://melolo.com/dramas/{slug}/ep{ep}" if ep > 1 else f"https://melolo.com/dramas/{slug}",
        f"https://melolo.com/id/dramas/{slug}",
    ]
    ctx = ssl._create_unverified_context()
    pattern = re.compile(r'https?://v\.melolo\.com/[^\s\"\'<>\\\\]+\.mp4\?sign=[^\s\"\'<>\\\\]+')
    for page_url in page_urls:
        try:
            req = urllib.request.Request(page_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://melolo.com/id"
            })
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                html = r.read().decode("utf-8", "ignore")
            signs = pattern.findall(html)
            if signs:
                clean_url = signs[-1].replace("\\u0026", "&")
                _MELOLO_SIGN_CACHE[key] = (clean_url, now + 7200)
                return clean_url
        except Exception:
            pass

    return ""


class StreamProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.handle_proxy(is_head=True)

    def do_GET(self):
        self.handle_proxy(is_head=False)

    def handle_proxy(self, is_head=False):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/stream":
            provider = qs.get("provider", [""])[0]
            slug = qs.get("slug", [""])[0]
            try:
                ep = int(qs.get("ep", ["1"])[0])
            except ValueError:
                ep = 1

            real_url = ""
            if provider == "melolo" and slug:
                real_url = get_melolo_signed_url(slug, ep)

            if not real_url:
                self.send_error(404, "Stream URL not resolved")
                return

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://melolo.com/"
            }
            if "Range" in self.headers:
                headers["Range"] = self.headers["Range"]

            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(real_url, headers=headers)
            upstream = None
            for attempt in range(2):
                try:
                    upstream = urllib.request.urlopen(req, context=ctx, timeout=12)
                    break
                except Exception as e:
                    if attempt == 0:
                        time.sleep(0.3)
                    else:
                        try:
                            self.send_error(502, f"Proxy upstream error: {e}")
                        except Exception:
                            pass
                        return

            try:
                self.send_response(upstream.status)
                for k, v in upstream.headers.items():
                    if k.lower() in ["content-type", "content-length", "content-range", "accept-ranges"]:
                        self.send_header(k, v)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                if not is_head:
                    while True:
                        chunk = upstream.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                pass
            finally:
                if upstream:
                    upstream.close()
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass  # Silent logging to prevent spamming terminal


def start_proxy_server(port=STREAM_PROXY_PORT):
    global _PROXY_SERVER
    if _PROXY_SERVER is not None:
        return

    # Check if port is already listening
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_open = sock.connect_ex(("127.0.0.1", port)) == 0
    sock.close()
    if is_open:
        return

    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), StreamProxyHandler)
        _PROXY_SERVER = server
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
    except Exception as e:
        sys.stderr.write(f"Could not bind streaming proxy to port {port}: {e}\n")


# Start proxy server automatically on import
start_proxy_server()

# -------------------------------------------------------------
# MELOLO CATALOG MANAGEMENT
# -------------------------------------------------------------
_MELOLO_CATALOG = []

MELOLO_TYPES = [
    {"typeTwoId": 0, "name": "🇮🇩 Semua Sub Indo (1.480+)"},
    {"typeTwoId": 1, "name": "❤️ Romansa"},
    {"typeTwoId": 2, "name": "💼 CEO & Miliarder"},
    {"typeTwoId": 3, "name": "⚔️ Balas Dendam"},
    {"typeTwoId": 4, "name": "🐺 Fantasi & Serigala"},
    {"typeTwoId": 5, "name": "🎭 Drama Kehidupan"},
]

_MELOLO_CATALOG = None
_MELOLO_CATALOG_MTIME = 0

def _load_melolo_catalog():
    global _MELOLO_CATALOG, _MELOLO_CATALOG_MTIME
    catalog_path = MELOLO_SYSTEM_CATALOG
    if not catalog_path.exists():
        catalog_path = CACHE_DIR / "melolo_catalog.json"

    if catalog_path.exists():
        try:
            mtime = catalog_path.stat().st_mtime
            if _MELOLO_CATALOG is not None and mtime == _MELOLO_CATALOG_MTIME:
                return _MELOLO_CATALOG
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                raw_dramas = data.get("dramas", [])
                # Strictly enforce verified working covers & Indonesian language
                _MELOLO_CATALOG = [
                    d for d in raw_dramas 
                    if (d.get("cover", "").startswith("https://v.melolo.com") or d.get("cover", "").startswith("https://"))
                    and not d.get("cover", "").endswith("/Logo.svg")
                    and (d.get("lang") == "id" or d.get("isSubIndo"))
                ]
                if not _MELOLO_CATALOG:
                    _MELOLO_CATALOG = raw_dramas
                _MELOLO_CATALOG_MTIME = mtime
        except Exception:
            if _MELOLO_CATALOG is None:
                _MELOLO_CATALOG = []
    return _MELOLO_CATALOG or []


def get_melolo_browse(page: int = 1, cat_id: int = 0) -> dict:
    catalog = _load_melolo_catalog()
    if not catalog:
        return {"status": "error", "message": "Melolo Indonesian catalog not loaded", "types": MELOLO_TYPES, "bookList": []}

    cat_map = {
        1: ["Romansa", "Romance"],
        2: ["CEO", "Miliarder", "Billionaire"],
        3: ["Balas Dendam", "Dendam", "Revenge"],
        4: ["Fantasi", "Serigala", "Werewolf"],
        5: ["Drama Kehidupan", "Drama", "Kehidupan"]
    }

    filtered = catalog
    if cat_id in cat_map:
        target_keys = [k.lower() for k in cat_map[cat_id]]
        filtered = [d for d in catalog if any(k in (d.get("category", "")).lower() for k in target_keys)]

    page_size = 30
    total = len(filtered)
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    page = max(1, min(page, pages))

    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    return {
        "status": "success",
        "types": MELOLO_TYPES,
        "bookList": page_items,
        "pageNo": page,
        "pages": pages,
        "total": total,
        "source": "melolo_catalog",
        "provider": "melolo"
    }

# -------------------------------------------------------------
# DRAMABOX & GOODBOS BACKEND
# -------------------------------------------------------------
def _read_cache(key: str) -> dict:
    fpath = CACHE_DIR / f"{key}.json"
    if fpath.exists():
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _write_cache(key: str, data: dict):
    fpath = CACHE_DIR / f"{key}.json"
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _http_get(url: str, headers: dict = None, timeout: int = 12) -> str:
    default_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "id,en-US,en;q=0.9",
    }
    if headers:
        default_headers.update(headers)

    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=default_headers)
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _extract_next_data(html: str) -> dict:
    pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
    match = re.search(pattern, html, re.DOTALL)
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


def get_browse(page: int = 1, cat_id: int = 0, slug: str = "", lang: str = "in", provider: str = "dramabox") -> dict:
    if provider == "melolo":
        return get_melolo_browse(page=page, cat_id=cat_id)

    cache_key = f"browse_{lang}_{cat_id}_{page}"

    # 1. Primary: Official DramaBox API backend
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
                    # Tag items with provider
                    for b in book_list:
                        b["provider"] = "dramabox"
                    res = {
                        "status": "success",
                        "types": types,
                        "bookList": book_list,
                        "pageNo": int(page),
                        "pages": pages,
                        "total": total,
                        "source": "api",
                        "provider": "dramabox"
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
            for b in book_list:
                b["provider"] = "dramabox"
            res = {
                "status": "success",
                "types": props.get("types", []),
                "bookList": book_list,
                "pageNo": props.get("pageNo", page),
                "pages": props.get("pages", 1),
                "total": props.get("total", len(book_list)),
                "source": "scraper",
                "provider": "dramabox"
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


def search(query: str, provider: str = "all") -> dict:
    if not query.strip():
        return {"status": "success", "results": []}

    q = query.strip().lower()
    results = []

    # 1. Search Melolo Catalog
    if provider in ["all", "melolo"]:
        catalog = _load_melolo_catalog()
        for d in catalog:
            name = (d.get("bookName") or "").lower()
            slug = (d.get("slug") or "").lower()
            if q in name or q in slug:
                results.append(d)
                if len(results) >= 60:
                    break

    # 2. Search DramaBox API
    if provider in ["all", "dramabox"]:
        goodbos_search_url = f"https://dramabox.goodbos.online/api/dramabox/search?query={urllib.parse.quote(query.strip())}"
        try:
            req = urllib.request.Request(goodbos_search_url, headers={
                "x-token": "6EB57533425BC1D78ADA1F80354161D4",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                g_data = json.loads(resp.read().decode("utf-8"))
                g_list = g_data if isinstance(g_data, list) else g_data.get("data", [])
                for b in g_list:
                    b["provider"] = "dramabox"
                    results.append(b)
        except Exception:
            pass

        url = "https://www.webfic.com/webfic/home/search"
        payload = json.dumps({"keyword": query.strip()}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "pline": "DRAMABOX",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        ctx = ssl._create_unverified_context()
        try:
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8")).get("data", {})
                dramabox_list = data.get("bookList", []) or data.get("list", [])
                for b in dramabox_list:
                    b["provider"] = "dramabox"
                    results.append(b)
        except Exception:
            pass

        # 3. Search local master catalog for instant DramaBox offline matches
        master = _read_cache("master_catalog")
        if master and master.get("bookList"):
            for b in master.get("bookList", []):
                name = (b.get("bookName") or "").lower()
                intro = (b.get("introduction") or "").lower()
                if q in name or q in intro:
                    if not any(str(r.get("bookId")) == str(b.get("bookId")) for r in results):
                        b_copy = dict(b)
                        b_copy["provider"] = "dramabox"
                        results.append(b_copy)

    return {"status": "success", "results": results}


def get_drama_detail(book_id, provider: str = "dramabox") -> dict:
    book_id_str = str(book_id)

    # ---------------------------------------------------------
    # MELOLO DETAIL & STREAM DISPATCH (100% Free & Unlocked)
    # ---------------------------------------------------------
    if provider == "melolo" or book_id_str.startswith("melolo_"):
        slug = book_id_str.replace("melolo_", "")
        cache_key = f"detail_melolo_{slug}"
        cached = _read_cache(cache_key)
        # Validate cache: ensure chapters exist, have mp4 proxy stream, and are all unlocked
        if cached.get("chapterList") and all(bool(c.get("unlock") and c.get("mp4")) for c in cached.get("chapterList", [])):
            return cached

        catalog = _load_melolo_catalog()
        target = None
        for d in catalog:
            if d.get("slug") == slug:
                target = dict(d)
                break

        title = target.get("bookName") if target else slug.replace("-", " ").title()
        cover = target.get("cover") if target else ""
        intro = target.get("introduction", "Drama pendek Melolo Sub Indo. 100% Free.") if target else "Drama pendek Melolo Sub Indo. 100% Free."
        chapter_count = max(1, target.get("chapterCount", 10)) if target else 10

        # Query official Melolo API for live series metadata & full episode list
        api_episodes = []
        try:
            refresh_key = f"{int(time.time() * 1000)}-{random.random()}"
            api_url = f"https://melolo.com/api/series/getSeriesBySlug?language=id&series_slug={slug}&pageType=play&episode_id=1&_refresh={refresh_key}"
            req = urllib.request.Request(api_url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": f"https://melolo.com/id/dramas/{slug}"
            })
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=ctx, timeout=7) as r:
                data = json.loads(r.read().decode("utf-8"))
                series = data.get("data", [{}])[0]
                if series:
                    title = series.get("name") or title
                    cover = series.get("cover_url") or cover
                    intro = series.get("intro") or intro
                    ep_list = series.get("episode_list", [])
                    if ep_list:
                        api_episodes = ep_list
        except Exception as e:
            sys.stderr.write(f"Error fetching Melolo live series detail for {slug}: {e}\n")

        chapters = []
        if api_episodes:
            for item in api_episodes:
                ep_num = int(item.get("episode_id", 1))
                stream_url = f"http://127.0.0.1:{STREAM_PROXY_PORT}/stream?provider=melolo&slug={slug}&ep={ep_num}"
                chapters.append({
                    "id": f"melolo_{slug}_{ep_num}",
                    "name": f"Part {ep_num} [Sub Indo]",
                    "chapterName": f"Part {ep_num} [Sub Indo]",
                    "index": ep_num - 1,
                    "indexStr": f"Part {ep_num}",
                    "mp4": stream_url,
                    "unlock": True,
                    "provider": "melolo"
                })
        else:
            # Fallback to catalog chapter count (all 100% unlocked)
            for i in range(chapter_count):
                ep_num = i + 1
                stream_url = f"http://127.0.0.1:{STREAM_PROXY_PORT}/stream?provider=melolo&slug={slug}&ep={ep_num}"
                chapters.append({
                    "id": f"melolo_{slug}_{ep_num}",
                    "name": f"Part {ep_num} [Sub Indo]",
                    "chapterName": f"Part {ep_num} [Sub Indo]",
                    "index": i,
                    "indexStr": f"Part {ep_num}",
                    "mp4": stream_url,
                    "unlock": True,
                    "provider": "melolo"
                })

        meta = {
            "bookId": f"melolo_{slug}",
            "bookName": title,
            "slug": slug,
            "category": "Melolo Short Drama",
            "chapterCount": len(chapters),
            "cover": cover,
            "provider": "melolo",
            "introduction": intro
        }
        res = {
            "status": "success",
            "bookInfo": meta,
            "chapterList": chapters,
            "provider": "melolo"
        }
        if chapters:
            _write_cache(cache_key, res)
        return res

    # ---------------------------------------------------------
    # DRAMABOX GOODBOS CDN STREAM DISPATCH
    # ---------------------------------------------------------
    cache_key = f"detail_{book_id_str}"
    cached = _read_cache(cache_key)

    # Fetch chapters from Goodbos API
    chapters = []
    goodbos_url = f"https://dramabox.goodbos.online/api/dramabox/allepisode?bookId={book_id_str}"
    goodbos_headers = {
        "x-token": "6EB57533425BC1D78ADA1F80354161D4",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    ctx = ssl._create_unverified_context()

    try:
        req = urllib.request.Request(goodbos_url, headers=goodbos_headers)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                for idx, ep in enumerate(data):
                    mp4_url = (
                        ep.get("videoUrl") or
                        ep.get("videoUrl720") or
                        ep.get("videoUrl1080") or
                        ep.get("videoUrl540") or
                        ep.get("video_url") or
                        ep.get("mp4") or
                        ep.get("url") or
                        ""
                    )
                    ch_name = ep.get("chapterName") or ep.get("name") or f"Part {idx + 1}"
                    ch_id = ep.get("chapterId") or ep.get("id") or (idx + 1)
                    ch_idx = ep.get("chapterIndex", idx)
                    chapters.append({
                        "id": ch_id,
                        "name": ch_name,
                        "chapterName": ch_name,
                        "index": ch_idx,
                        "indexStr": f"Part {idx + 1}",
                        "mp4": mp4_url,
                        "unlock": bool(mp4_url),
                        "provider": "dramabox"
                    })
    except Exception as e:
        sys.stderr.write(f"Goodbos API error for book {book_id_str}: {e}\n")

    # Fetch metadata from webfic
    meta = {}
    try:
        url = "https://www.webfic.com/webfic/home/drama/detail"
        payload = json.dumps({"bookId": int(book_id_str)}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "pline": "DRAMABOX",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8")).get("data", {})
            meta = data.get("bookInfo", {}) or data
            if not chapters:
                api_chaps = data.get("chapterList", [])
                for idx, c in enumerate(api_chaps):
                    mp4_url = _extract_stream_from_chapter(c)
                    chapters.append({
                        "id": c.get("chapterId", idx + 1),
                        "name": c.get("chapterName", f"Episode {idx + 1}"),
                        "chapterName": c.get("chapterName", f"Episode {idx + 1}"),
                        "index": idx,
                        "indexStr": f"Ep {idx + 1}",
                        "mp4": mp4_url,
                        "unlock": True,
                        "provider": "dramabox"
                    })
    except Exception:
        pass

    if not meta and cached.get("bookInfo"):
        meta = cached["bookInfo"]
    if not chapters and cached.get("chapterList"):
        chapters = cached["chapterList"]

    if not meta or not meta.get("cover") or str(meta.get("bookName", "")).startswith("Drama #"):
        found = _lookup_metadata(book_id_str)
        if found:
            if not meta:
                meta = found
            else:
                if not meta.get("cover") and found.get("cover"):
                    meta["cover"] = found["cover"]
                if (not meta.get("bookName") or str(meta.get("bookName", "")).startswith("Drama #")) and found.get("bookName"):
                    meta["bookName"] = found["bookName"]
                if not meta.get("introduction") and found.get("introduction"):
                    meta["introduction"] = found["introduction"]

    if not meta:
        meta = {
            "bookId": book_id_str,
            "bookName": f"Drama #{book_id_str}",
            "cover": "",
            "chapterCount": len(chapters),
            "introduction": "DramaBox Short Drama Series.",
            "provider": "dramabox"
        }
    meta["provider"] = "dramabox"

    res = {
        "status": "success",
        "bookInfo": meta,
        "chapterList": chapters,
        "provider": "dramabox"
    }
    if chapters:
        _write_cache(cache_key, res)
    return res


def _lookup_metadata(book_id: str) -> dict:
    bid_str = str(book_id or "").strip()
    if not bid_str:
        return {}

    # 1. Melolo catalog lookup
    if bid_str.startswith("melolo_") or not bid_str.isdigit():
        slug = bid_str.replace("melolo_", "")
        for d in _load_melolo_catalog():
            if d.get("slug") == slug:
                return {
                    "bookId": f"melolo_{slug}",
                    "bookName": d.get("title", ""),
                    "cover": d.get("cover", ""),
                    "introduction": d.get("intro", ""),
                    "provider": "melolo"
                }

    # 2. DramaBox cache files lookup
    try:
        for f in CACHE_DIR.glob("browse_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as bf:
                    bdata = json.load(bf)
                    books = bdata.get("bookList") or bdata.get("dramas") or bdata.get("data") or []
                    for d in books:
                        if str(d.get("bookId")) == bid_str or str(d.get("originalBookId")) == bid_str:
                            return {
                                "bookId": bid_str,
                                "bookName": d.get("bookName", ""),
                                "cover": d.get("cover", ""),
                                "introduction": d.get("introduction", ""),
                                "provider": "dramabox"
                            }
            except Exception:
                pass
    except Exception:
        pass

    return {}


def _extract_stream_from_chapter(c: dict) -> str:
    res = c.get("resourceList", [])
    if isinstance(res, list) and len(res) > 0:
        for r in res:
            if isinstance(r, dict) and r.get("url"):
                return r["url"]
    for field in ["videoUrl", "playUrl", "mp4", "downloadUrl", "previewUrl"]:
        if c.get(field):
            return c[field]
    return ""


def get_history() -> dict:
    if not HISTORY_FILE.exists():
        return {"status": "success", "history": []}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
            updated = False
            for h in items:
                bid = str(h.get("bookId", ""))
                if not h.get("cover") or str(h.get("bookName", "")).startswith("Drama #"):
                    meta = _lookup_metadata(bid)
                    if meta.get("cover") and not h.get("cover"):
                        h["cover"] = meta["cover"]
                        updated = True
                    if meta.get("bookName") and (not h.get("bookName") or str(h.get("bookName", "")).startswith("Drama #")):
                        h["bookName"] = meta["bookName"]
                        updated = True
            if updated:
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
            return {"status": "success", "history": items}
    except Exception:
        return {"status": "success", "history": []}


def save_history(entry: dict) -> dict:
    bid = str(entry.get("bookId", ""))
    if not entry.get("cover") or str(entry.get("bookName", "")).startswith("Drama #"):
        meta = _lookup_metadata(bid)
        if meta.get("cover") and not entry.get("cover"):
            entry["cover"] = meta["cover"]
        if meta.get("bookName") and (not entry.get("bookName") or str(entry.get("bookName", "")).startswith("Drama #")):
            entry["bookName"] = meta["bookName"]

    history = get_history().get("history", [])
    history = [h for h in history if str(h.get("bookId")) != bid]
    history.insert(0, entry)
    history = history[:30]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def clear_history() -> dict:
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        return {"status": "success", "history": []}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_history_item(book_id: str) -> dict:
    if not book_id:
        return {"status": "error", "message": "bookId is required"}
    try:
        history = get_history().get("history", [])
        history = [h for h in history if str(h.get("bookId")) != str(book_id)]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return {"status": "success", "history": history}
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
    provider = payload.get("provider", "dramabox")

    if action == "browse":
        page = payload.get("page", 1)
        cat_id = payload.get("cat_id", 0)
        lang = payload.get("lang", "in")
        return get_browse(page=page, cat_id=cat_id, lang=lang, provider=provider)
    elif action == "search":
        query = payload.get("query", "")
        return search(query, provider=provider)
    elif action == "detail":
        book_id = payload.get("bookId")
        return get_drama_detail(book_id, provider=provider)
    elif action == "get_history":
        return get_history()
    elif action == "save_history":
        return save_history(payload.get("entry", {}))
    elif action == "clear_history":
        return clear_history()
    elif action == "delete_history":
        return delete_history_item(payload.get("bookId"))
    elif action == "get_favorites":
        return get_favorites()
    elif action == "toggle_favorite":
        return toggle_favorite(payload.get("drama", {}))
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        prov = sys.argv[2] if len(sys.argv) > 2 else "dramabox"
        if cmd == "browse":
            print(json.dumps(get_browse(1, 0, provider=prov), indent=2))
        elif cmd == "detail" and len(sys.argv) > 2:
            print(json.dumps(get_drama_detail(sys.argv[2]), indent=2))
