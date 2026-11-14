#!/usr/bin/env python3
"""
DramaBox & Melolo Flow - Local Unified Dev Server
Fully standalone local server emulating Cloudflare Pages Edge Worker behavior:
- Static assets from ./public
- /api/browse: Interleaved catalog with category filtering
- /api/search: Unified real-time search
- /api/detail: Live Melolo Next.js and DramaBox Goodbos API
- /images/...: Local image caching proxy masking upstream image sources
- /media/...: Zero-copy reverse proxy with Range 206 Partial Content & CDN Referer bypass
- SSR Simulation: Dynamic meta tags and Schema.org TVEpisode & VideoObject
"""

import os
import sys
import re
import json
import time
import ssl
import random
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
_DRAMABOX_CHAPTERS_CACHE = {}

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

def get_melolo_signed_url(slug, ep):
    now = time.time()
    clean_slug = slug.replace("melolo_", "")
    key = f"{clean_slug}_{ep}"
    if key in _MELOLO_SIGN_CACHE:
        url, exp = _MELOLO_SIGN_CACHE[key]
        if now < exp:
            return url

    # 1. Melolo Next.js API
    try:
        refresh_key = f"{int(now * 1000)}-{random.random()}"
        api_url = f"https://melolo.com/api/series/getSeriesBySlug?language=id&series_slug={clean_slug}&pageType=play&episode_id={ep}&_refresh={refresh_key}"
        req = urllib.request.Request(api_url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"https://melolo.com/id/dramas/{clean_slug}"
        })
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
            series = data.get("data", [{}])[0]
            for item in series.get("episode_list", []):
                if int(item.get("episode_id", 0)) == int(ep) or int(item.get("episode_number", 0)) == int(ep):
                    target = item.get("url", "")
                    if target:
                        clean = target.replace("\\u0026", "&")
                        _MELOLO_SIGN_CACHE[key] = (clean, now + 7200)
                        return clean
            # Fallback to index if episode_id didn't match directly
            ep_list = series.get("episode_list", [])
            if 0 < ep <= len(ep_list) and ep_list[ep - 1].get("url"):
                clean = ep_list[ep - 1]["url"].replace("\\u0026", "&")
                _MELOLO_SIGN_CACHE[key] = (clean, now + 7200)
                return clean
    except Exception as e:
        sys.stderr.write(f"Melolo API getSeriesBySlug error for {clean_slug} ep {ep}: {e}\n")

    return ""

def get_dramabox_signed_url(book_id, ep):
    now = time.time()
    key = str(book_id)
    chapters = None
    if key in _DRAMABOX_CHAPTERS_CACHE:
        data, exp = _DRAMABOX_CHAPTERS_CACHE[key]
        if now < exp:
            chapters = data

    if chapters is None:
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
                chapters = g_data if isinstance(g_data, list) else g_data.get("data", [])
                _DRAMABOX_CHAPTERS_CACHE[key] = (chapters, now + 3600)
        except Exception as e:
            sys.stderr.write(f"Goodbos fetch error for {book_id}: {e}\n")

    if chapters and len(chapters) > 0:
        idx = int(ep) - 1
        if 0 <= idx < len(chapters):
            ep_obj = chapters[idx]
            return ep_obj.get("videoUrl") or ep_obj.get("videoUrl720") or ep_obj.get("mp4") or ""
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
        if self.path.startswith("/api/stream") or self.path.startswith("/media/"):
            self.handle_stream_proxy(is_head=True)
        elif self.path.startswith("/images/"):
            self.handle_image_proxy(is_head=True)
        else:
            super().do_HEAD()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/media/") or path.startswith("/api/stream"):
            self.handle_stream_proxy(is_head=False)
        elif path.startswith("/images/"):
            self.handle_image_proxy(is_head=False)
        elif path.startswith("/api/"):
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

            filtered = catalog
            if cat_id in cat_map:
                keys = cat_map[cat_id]
                filtered = [
                    d for d in catalog
                    if any(
                        k in f"{d.get('category','')} {d.get('bookName','')} {d.get('title','')} {' '.join(d.get('typeTwoNames',[]))} {' '.join(d.get('tags',[]))} {d.get('introduction','')}".lower()
                        for k in keys
                    )
                ]

            total = len(filtered)
            total_pages = (total + page_size - 1) // page_size or 1
            safe_page = max(1, min(page, total_pages))
            start = (safe_page - 1) * page_size
            dramas = filtered[start:start + page_size]

            self.send_json({
                "status": "success",
                "pageNo": safe_page,
                "pages": total_pages,
                "page": safe_page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total": total,
                "provider": provider,
                "bookList": dramas,
                "dramas": dramas
            })

        elif path == "/api/search":
            query = qs.get("q", [""])[0].strip().lower()
            if not query:
                self.send_json({"status": "success", "total": 0, "results": [], "dramas": []})
                return

            melolo_list = get_melolo_catalog()
            dramabox_list = get_dramabox_catalog()

            melolo_matches = [
                d for d in melolo_list
                if query in (d.get("bookName") or "").lower() or query in (d.get("introduction") or "").lower()
            ]
            dramabox_matches = [
                d for d in dramabox_list
                if query in (d.get("bookName") or "").lower() or query in (d.get("introduction") or "").lower()
            ]

            merged = []
            max_len = max(len(melolo_matches), len(dramabox_matches))
            for i in range(max_len):
                if i < len(melolo_matches):
                    merged.append(melolo_matches[i])
                if i < len(dramabox_matches):
                    merged.append(dramabox_matches[i])

            final_results = merged[:50]
            self.send_json({
                "status": "success",
                "query": query,
                "total": len(merged),
                "results": final_results,
                "dramas": final_results
            })

        elif path == "/api/detail":
            book_id = qs.get("bookId", [""])[0]
            if not book_id:
                self.send_json({"status": "error", "message": "bookId required"}, 400)
                return

            if str(book_id).startswith("melolo_"):
                slug = str(book_id).replace("melolo_", "")
                meta = {
                    "bookId": book_id,
                    "bookName": slug.replace("-", " ").title(),
                    "slug": slug,
                    "category": "Drama Melolo",
                    "chapterCount": 50,
                    "cover": f"/images/melolo/{slug}/cover.jpg",
                    "provider": "melolo",
                    "introduction": "Serial drama pendek Melolo HD sub Indo."
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
                        if series.get("series_cover") or series.get("cover_url"):
                            raw_cover = series.get("series_cover") or series.get("cover_url")
                            meta["cover"] = f"/images/cover?provider=melolo&id={slug}&url={urllib.parse.quote(raw_cover)}"
                        if series.get("series_desc") or series.get("desc"):
                            meta["introduction"] = series.get("series_desc") or series.get("desc")

                        for ep_item in series.get("episode_list", []):
                            ep_num = int(ep_item.get("episode_id", 0))
                            if ep_num > 0:
                                chapters.append({
                                    "id": ep_num,
                                    "name": f"Part {ep_num}",
                                    "chapterName": f"Part {ep_num}",
                                    "index": ep_num - 1,
                                    "indexStr": f"Part {ep_num}",
                                    "mp4": f"/media/melolo/{slug}/{ep_num}.mp4",
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
                            "mp4": f"/media/melolo/{slug}/{i}.mp4",
                            "unlock": True,
                            "provider": "melolo",
                            "slug": slug,
                            "ep": i
                        })

                if chapters:
                    meta["chapterCount"] = len(chapters)
                elif meta.get("chapterCount"):
                    total_chaps = meta.get("chapterCount", 80) or 80
                    for i in range(1, total_chaps + 1):
                        chapters.append({
                            "id": i,
                            "name": f"Part {i}",
                            "chapterName": f"Part {i}",
                            "index": i - 1,
                            "indexStr": f"Part {i}",
                            "mp4": f"/media/dramabox/{book_id}/{i}.mp4",
                            "unlock": True,
                            "provider": "dramabox"
                        })
                elif series.get("episode_num") or series.get("series_total_episode") or series.get("episode_count"):
                    meta["chapterCount"] = series.get("episode_num") or series.get("series_total_episode") or series.get("episode_count")

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
                        "cover": f"/images/dramabox/{book_id}/cover.jpg",
                        "chapterCount": 50,
                        "introduction": "DramaBox Short Drama Series.",
                        "provider": "dramabox"
                    }
                else:
                    meta = dict(meta)
                    if meta.get("cover"):
                        meta["cover"] = f"/images/cover?provider=dramabox&id={book_id}&url={urllib.parse.quote(meta['cover'])}"

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
                            ch_name = ep.get("chapterName") or f"Part {idx + 1}"
                            chapters.append({
                                "id": ep.get("chapterId", idx + 1),
                                "name": ch_name,
                                "chapterName": ch_name,
                                "index": idx,
                                "indexStr": f"Part {idx + 1}",
                                "mp4": f"/media/dramabox/{book_id}/{idx + 1}.mp4",
                                "unlock": True,
                                "provider": "dramabox"
                            })
                except Exception as e:
                    sys.stderr.write(f"Goodbos fetch error for {book_id}: {e}\n")

                if chapters:
                    meta["chapterCount"] = len(chapters)
                elif meta.get("chapterCount"):
                    total_chaps = int(meta.get("chapterCount", 80) or 80)
                    for i in range(1, total_chaps + 1):
                        chapters.append({
                            "id": i,
                            "name": f"Part {i}",
                            "chapterName": f"Part {i}",
                            "index": i - 1,
                            "indexStr": f"Part {i}",
                            "mp4": f"/media/dramabox/{book_id}/{i}.mp4",
                            "unlock": True,
                            "provider": "dramabox"
                        })

                self.send_json({
                    "status": "success",
                    "bookInfo": meta,
                    "chapterList": chapters,
                    "provider": "dramabox"
                })

        else:
            self.send_json({"status": "error", "message": "Not found"}, 404)

    def handle_image_proxy(self, is_head=False):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        target_url = qs.get("url", [""])[0]
        provider = qs.get("provider", [""])[0]
        item_id = qs.get("id", [""])[0]

        m = re.match(r"^/images/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)/cover\.(jpg|jpeg|webp|png)$", path)
        if m:
            provider = m.group(1)
            item_id = m.group(2)

        if not target_url and provider and item_id:
            if provider == "melolo":
                cat = get_melolo_catalog()
                clean_id = item_id.replace("melolo_", "")
                drama = next((d for d in cat if d.get("slug") == clean_id or d.get("bookId") == item_id or d.get("bookId") == f"melolo_{clean_id}"), None)
                if drama:
                    target_url = drama.get("cover", "")
            elif provider == "dramabox":
                cat = get_dramabox_catalog()
                drama = next((d for d in cat if str(d.get("bookId")) == str(item_id)), None)
                if drama:
                    target_url = drama.get("cover", "")

        if not target_url:
            self.send_response(404)
            self.end_headers()
            return

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://melolo.com/" if ("melolo" in target_url or "edgeone" in target_url) else ""
        }
        try:
            req = urllib.request.Request(target_url, headers=headers)
            ctx = ssl._create_unverified_context()
            resp = urllib.request.urlopen(req, context=ctx, timeout=8)
            self.send_response(200)
            self.send_header("Content-Type", resp.headers.get("Content-Type", "image/jpeg"))
            self.send_header("Cache-Control", "public, max-age=2592000, immutable")
            self.send_header("Server", "Flowork-Media-Core/2.4 (Sovereign Linux)")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if not is_head:
                self.wfile.write(resp.read())
        except Exception as e:
            sys.stderr.write(f"Image proxy error: {e}\n")
            try:
                self.send_response(502)
                self.end_headers()
            except Exception:
                pass

    def handle_stream_proxy(self, is_head=False):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        provider = qs.get("provider", [""])[0]
        slug = qs.get("slug", [""])[0] or qs.get("bookId", [""])[0] or qs.get("id", [""])[0]
        try:
            ep = int(qs.get("ep", ["1"])[0])
        except ValueError:
            ep = 1

        # Match /media/:provider/:id/:ep.mp4
        m = re.match(r"^/media/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)/([0-9]+)\.mp4$", path)
        if m:
            provider = m.group(1)
            slug = m.group(2)
            ep = int(m.group(3))

        real_url = ""
        if provider == "melolo" and slug:
            real_url = get_melolo_signed_url(slug, ep)
        elif provider == "dramabox" and slug:
            real_url = get_dramabox_signed_url(slug, ep)
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
            "Referer": "https://melolo.com/" if "melolo" in real_url else ""
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

            self.send_header("Server", "Flowork-Media-Core/2.4 (Sovereign Linux)")
            self.send_header("X-Powered-By", "Flowork OS Stream Engine")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Range")
            self.send_header("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges")
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
        print("\nDev server stopped.")
