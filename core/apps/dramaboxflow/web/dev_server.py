#!/usr/bin/env python3
"""
DramaBoxFlow Web Local Development Server
Provides static web hosting + serverless API parity:
- /api/browse: Multi-provider browsing (Melolo: 1,480 titles, DramaBox: 1,320 titles)
- /api/detail: Live Melolo Next.js API + Goodbos DramaBox API
- /api/search: Unified high-speed search across 2,800+ drama titles
- /api/stream: Zero-copy reverse proxy with Range 206 Partial Content & CDN Referer bypass
"""

import os
import sys
import json
import time
import re
import random
import ssl
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = 8787
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
MELOLO_CATALOG_PATH = os.path.join(PUBLIC_DIR, "melolo_catalog.json")
DRAMABOX_CATALOG_PATH = os.path.join(PUBLIC_DIR, "dramabox_catalog.json")

_MELOLO_CATALOG_CACHE = None
_DRAMABOX_CATALOG_CACHE = None
_MELOLO_SIGN_CACHE = {}

def get_melolo_catalog():
    global _MELOLO_CATALOG_CACHE
    if _MELOLO_CATALOG_CACHE is not None:
        return _MELOLO_CATALOG_CACHE
    if os.path.isfile(MELOLO_CATALOG_PATH):
        try:
            with open(MELOLO_CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                _MELOLO_CATALOG_CACHE = data.get("dramas", data) if isinstance(data, dict) else data
                return _MELOLO_CATALOG_CACHE
        except Exception as e:
            sys.stderr.write(f"Melolo catalog load error: {e}\n")
    _MELOLO_CATALOG_CACHE = []
    return _MELOLO_CATALOG_CACHE

def get_dramabox_catalog():
    global _DRAMABOX_CATALOG_CACHE
    if _DRAMABOX_CATALOG_CACHE is not None:
        return _DRAMABOX_CATALOG_CACHE
    if os.path.isfile(DRAMABOX_CATALOG_PATH):
        try:
            with open(DRAMABOX_CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                _DRAMABOX_CATALOG_CACHE = data.get("dramas", data) if isinstance(data, dict) else data
                return _DRAMABOX_CATALOG_CACHE
        except Exception as e:
            sys.stderr.write(f"DramaBox catalog load error: {e}\n")
    _DRAMABOX_CATALOG_CACHE = []
    return _DRAMABOX_CATALOG_CACHE

def get_melolo_signed_url(slug: str, ep: int = 1) -> str:
    key = f"{slug}:{ep}"
    now = time.time()
    if key in _MELOLO_SIGN_CACHE:
        cached_url, exp = _MELOLO_SIGN_CACHE[key]
        if now < exp:
            return cached_url

    # 1. Melolo Next.js API
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
            for item in series.get("episode_list", []):
                if int(item.get("episode_id", 0)) == int(ep):
                    target = item.get("url", "")
                    if target:
                        clean = target.replace("\\u0026", "&")
                        _MELOLO_SIGN_CACHE[key] = (clean, now + 7200)
                        return clean
    except Exception as e:
        sys.stderr.write(f"Melolo API getSeriesBySlug error for {slug} ep {ep}: {e}\n")

    # 2. Fallback scrape
    page_urls = [
        f"https://melolo.com/id/dramas/{slug}/ep{ep}" if ep > 1 else f"https://melolo.com/id/dramas/{slug}",
        f"https://melolo.com/dramas/{slug}/ep{ep}" if ep > 1 else f"https://melolo.com/dramas/{slug}",
    ]
    ctx = ssl._create_unverified_context()
    pattern = re.compile(r'https?://v\.melolo\.com/[^\s\"\'<>\\\\]+\.mp4\?sign=[^\s\"\'<>\\\\]+')
    for page_url in page_urls:
        try:
            req = urllib.request.Request(page_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://melolo.com/id"
            })
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                html = r.read().decode("utf-8", "ignore")
            signs = pattern.findall(html)
            if signs:
                clean = signs[-1].replace("\\u0026", "&")
                _MELOLO_SIGN_CACHE[key] = (clean, now + 7200)
                return clean
        except Exception:
            pass
    return ""

class DevHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        self.end_headers()

    def do_HEAD(self):
        if self.path.startswith("/api/stream"):
            self.handle_stream_proxy(is_head=True)
        else:
            super().do_HEAD()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api(path, qs)
        else:
            # Fallback to index.html for SPA routing if file not found
            local_path = os.path.join(PUBLIC_DIR, path.lstrip("/"))
            if not os.path.exists(local_path) and not path.startswith("/api"):
                self.path = "/index.html"
            super().do_GET()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_api(self, path, qs):
        if path == "/api/browse":
            provider = qs.get("provider", ["all"])[0]
            cat_id = int(qs.get("cat_id", ["0"])[0])
            page = int(qs.get("page", ["1"])[0])
            page_size = int(qs.get("page_size", ["24"])[0])

            melolo_list = get_melolo_catalog()
            dramabox_list = get_dramabox_catalog()

            if provider == "melolo":
                catalog = melolo_list
            elif provider == "dramabox":
                catalog = dramabox_list
            else:
                # Merge and alternate
                catalog = []
                max_len = max(len(melolo_list), len(dramabox_list))
                for i in range(max_len):
                    if i < len(melolo_list):
                        catalog.append(melolo_list[i])
                    if i < len(dramabox_list):
                        catalog.append(dramabox_list[i])

            cat_map = {
                1: ["romansa", "romance"],
                2: ["ceo", "miliarder", "billionaire"],
                3: ["balas dendam", "dendam", "revenge", "melawan balik"],
                4: ["fantasi", "serigala", "werewolf", "magic"],
                5: ["drama kehidupan", "drama", "kehidupan", "urban", "modern"]
            }

            if cat_id in cat_map:
                keys = cat_map[cat_id]
                def matches(d):
                    tags = d.get("typeTwoNames", []) if isinstance(d.get("typeTwoNames"), list) else []
                    labels = d.get("tags", []) if isinstance(d.get("tags"), list) else []
                    text = (
                        (d.get("category") or "") + " " +
                        (d.get("bookName") or "") + " " +
                        (d.get("title") or "") + " " +
                        " ".join(tags) + " " +
                        " ".join(labels) + " " +
                        (d.get("introduction") or "")
                    ).lower()
                    return any(k in text for k in keys)
                filtered = [d for d in catalog if matches(d)]
            else:
                filtered = catalog

            total = len(filtered)
            pages = (total + page_size - 1) // page_size if total > 0 else 1
            page = max(1, min(page, pages))
            start = (page - 1) * page_size
            end = start + page_size

            res = {
                "status": "success",
                "bookList": filtered[start:end],
                "pageNo": page,
                "pages": pages,
                "total": total,
                "provider": provider
            }
            self.send_json(res)

        elif path == "/api/search":
            q = qs.get("q", [""])[0].strip().lower()
            if not q:
                self.send_json({"status": "success", "results": []})
                return

            melolo_list = get_melolo_catalog()
            dramabox_list = get_dramabox_catalog()
            results = []
            seen = set()

            def match_search(d):
                name = (d.get("bookName") or d.get("title") or "").lower()
                slug = (d.get("slug") or "").lower()
                intro = (d.get("introduction") or "").lower()
                return q in name or q in slug or q in intro

            for d in dramabox_list:
                bid = str(d.get("bookId"))
                if match_search(d) and bid not in seen:
                    seen.add(bid)
                    results.append(d)
                    if len(results) >= 40:
                        break

            for d in melolo_list:
                bid = str(d.get("bookId"))
                if match_search(d) and bid not in seen:
                    seen.add(bid)
                    results.append(d)
                    if len(results) >= 80:
                        break

            # Also search Goodbos for live DramaBox items
            try:
                g_url = f"https://dramabox.goodbos.online/api/dramabox/search?query={urllib.parse.quote(q)}"
                req = urllib.request.Request(g_url, headers={
                    "x-token": "6EB57533425BC1D78ADA1F80354161D4",
                    "User-Agent": "Mozilla/5.0"
                })
                ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                    g_data = json.loads(resp.read().decode("utf-8"))
                    g_list = g_data if isinstance(g_data, list) else g_data.get("data", [])
                    for b in g_list:
                        bid = str(b.get("bookId"))
                        if bid not in seen:
                            seen.add(bid)
                            b["provider"] = "dramabox"
                            results.append(b)
            except Exception:
                pass

            self.send_json({"status": "success", "results": results})

        elif path == "/api/detail":
            book_id = qs.get("bookId", [""])[0]
            provider = qs.get("provider", [""])[0]

            if not book_id:
                self.send_json({"status": "error", "message": "bookId required"}, 400)
                return

            if book_id.startswith("melolo_") or provider == "melolo":
                slug = book_id[len("melolo_"):] if book_id.startswith("melolo_") else book_id
                catalog = get_melolo_catalog()
                meta = next((d for d in catalog if d.get("slug") == slug or d.get("bookId") == book_id), None)
                if not meta:
                    meta = {
                        "bookId": f"melolo_{slug}",
                        "bookName": slug.replace("-", " ").title(),
                        "title": slug.replace("-", " ").title(),
                        "slug": slug,
                        "category": "Drama Melolo",
                        "chapterCount": 50,
                        "cover": "",
                        "provider": "melolo",
                        "introduction": "Serial drama pendek Melolo HD."
                    }

                chapters = []
                try:
                    now = int(time.time() * 1000)
                    api_url = f"https://melolo.com/api/series/getSeriesBySlug?language=id&series_slug={slug}&pageType=play&episode_id=1&_refresh={now}"
                    req = urllib.request.Request(api_url, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": f"https://melolo.com/id/dramas/{slug}"
                    })
                    ctx = ssl._create_unverified_context()
                    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        series = data.get("data", [{}])[0]
                        if series.get("series_total_episode") or series.get("episode_count"):
                            meta["chapterCount"] = series.get("series_total_episode") or series.get("episode_count")
                        if series.get("series_name"):
                            meta["bookName"] = series["series_name"]
                        if series.get("series_cover"):
                            meta["cover"] = series["series_cover"]
                        if series.get("series_desc"):
                            meta["introduction"] = series["series_desc"]

                        for ep_item in series.get("episode_list", []):
                            ep_num = int(ep_item.get("episode_id", 0))
                            if ep_num > 0:
                                chapters.append({
                                    "id": ep_num,
                                    "name": f"Part {ep_num}",
                                    "chapterName": f"Part {ep_num}",
                                    "index": ep_num - 1,
                                    "indexStr": f"Part {ep_num}",
                                    # ALWAYS route Melolo through /api/stream to bypass CDN Referer block
                                    "mp4": f"/api/stream?provider=melolo&slug={slug}&ep={ep_num}",
                                    "unlock": True,
                                    "provider": "melolo",
                                    "slug": slug,
                                    "ep": ep_num
                                })
                except Exception as e:
                    sys.stderr.write(f"Melolo live series error for {slug}: {e}\n")

                if not chapters:
                    count = meta.get("chapterCount", 40) or 40
                    for i in range(1, count + 1):
                        chapters.append({
                            "id": i,
                            "name": f"Part {i}",
                            "chapterName": f"Part {i}",
                            "index": i - 1,
                            "indexStr": f"Part {i}",
                            "mp4": f"/api/stream?provider=melolo&slug={slug}&ep={i}",
                            "unlock": True,
                            "provider": "melolo",
                            "slug": slug,
                            "ep": i
                        })

                self.send_json({
                    "status": "success",
                    "bookInfo": meta,
                    "chapterList": chapters,
                    "provider": "melolo"
                })

            else:
                # DramaBox
                catalog = get_dramabox_catalog()
                meta = next((d for d in catalog if str(d.get("bookId")) == str(book_id)), None)
                if not meta:
                    meta = {
                        "bookId": book_id,
                        "bookName": f"DramaBox #{book_id}",
                        "cover": "",
                        "chapterCount": 50,
                        "introduction": "DramaBox Short Drama Series.",
                        "provider": "dramabox"
                    }

                chapters = []
                try:
                    g_url = f"https://dramabox.goodbos.online/api/dramabox/allepisode?bookId={book_id}"
                    headers = {
                        "x-token": "6EB57533425BC1D78ADA1F80354161D4",
                        "User-Agent": "Mozilla/5.0"
                    }
                    req = urllib.request.Request(g_url, headers=headers)
                    ctx = ssl._create_unverified_context()
                    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                        g_data = json.loads(resp.read().decode("utf-8"))
                        g_list = g_data if isinstance(g_data, list) else g_data.get("data", [])
                        for idx, ep in enumerate(g_list):
                            mp4_url = ep.get("videoUrl") or ep.get("videoUrl720") or ep.get("mp4") or ""
                            ch_name = ep.get("chapterName") or f"Part {idx + 1}"
                            chapters.append({
                                "id": ep.get("chapterId", idx + 1),
                                "name": ch_name,
                                "chapterName": ch_name,
                                "index": idx,
                                "indexStr": f"Part {idx + 1}",
                                "mp4": mp4_url,
                                "unlock": True,
                                "provider": "dramabox"
                            })
                except Exception as e:
                    sys.stderr.write(f"Goodbos fetch error for {book_id}: {e}\n")

                if chapters:
                    meta["chapterCount"] = len(chapters)

                self.send_json({
                    "status": "success",
                    "bookInfo": meta,
                    "chapterList": chapters,
                    "provider": "dramabox"
                })

        elif path == "/api/stream":
            self.handle_stream_proxy(is_head=False)

        else:
            self.send_json({"status": "error", "message": "Not found"}, 404)

    def handle_stream_proxy(self, is_head=False):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        provider = qs.get("provider", [""])[0]
        slug = qs.get("slug", [""])[0]
        try:
            ep = int(qs.get("ep", ["1"])[0])
        except ValueError:
            ep = 1

        real_url = ""
        if provider == "melolo" and slug:
            real_url = get_melolo_signed_url(slug, ep)
        elif qs.get("url"):
            real_url = qs.get("url")[0]

        if not real_url:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Stream not found or expired")
            return

        range_header = self.headers.get("Range")
        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://melolo.com/" if "melolo.com" in real_url else ""
        }
        if range_header:
            req_headers["Range"] = range_header

        try:
            req = urllib.request.Request(real_url, headers=req_headers)
            ctx = ssl._create_unverified_context()
            resp = urllib.request.urlopen(req, context=ctx, timeout=12)

            status = resp.status
            self.send_response(status)
            for k, v in resp.headers.items():
                if k.lower() in ("content-type", "content-length", "content-range", "accept-ranges", "last-modified", "etag"):
                    self.send_header(k, v)

            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Range")
            self.end_headers()

            if not is_head:
                try:
                    while True:
                        chunk = resp.read(64 * 1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    pass
        except Exception as e:
            sys.stderr.write(f"Stream proxy error: {e}\n")
            try:
                self.send_response(502)
                self.end_headers()
            except Exception:
                pass

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), DevHandler)
    print(f"🎬 DramaBoxFlow Web Dev Server listening on http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
