#!/usr/bin/env python3
"""
Sync full Melolo Indonesian drama catalog (all 1,480 titles) with real CDN covers and Indonesian titles.
Run in background or CLI.
"""
import urllib.request
import ssl
import re
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET

CATALOG_PATH = "/opt/floworkos/apps/dramaboxflow/assets/melolo_catalog.json"
SITEMAP_URL = "https://melolo.com/sitemap/movie.xml"
LOG_PATH = os.path.expanduser("~/.flowork/logs/melolo_sync.log")

ctx = ssl._create_unverified_context()

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    print(formatted, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def get_sitemap_urls():
    log(f"Mengambil sitemap XML dari {SITEMAP_URL}...")
    req = urllib.request.Request(SITEMAP_URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    content = urllib.request.urlopen(req, context=ctx, timeout=15).read().decode("utf-8")
    root = ET.fromstring(content)
    urls = []
    for child in root:
        loc = child.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        if loc is not None and loc.text and "/id/dramas/" in loc.text:
            urls.append(loc.text.strip())
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    log(f"Total URL drama Indonesia di sitemap: {len(unique)}")
    return unique

def parse_drama(url):
    slug = url.rstrip("/").split("/")[-1]
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
            res = urllib.request.urlopen(req, context=ctx, timeout=12)
            chunk = res.read(16384).decode("utf-8", errors="ignore")
            
            # Title & Category
            t_m = re.search(r'<title>(.*?)</title>', chunk)
            raw_title = t_m.group(1) if t_m else ""
            
            title = ""
            cat = "Drama Pendek"
            if " - Drama Pendek " in raw_title:
                parts = raw_title.split(" - Drama Pendek ")
                title = parts[0].strip()
                cat = parts[1].split(" | Melolo")[0].strip()
            elif " | Melolo" in raw_title:
                title = raw_title.split(" | Melolo")[0].strip()
            else:
                title = raw_title.strip()
            
            # Description
            desc_m = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', chunk)
            if not desc_m:
                desc_m = re.search(r'<meta name=\"description\" content=\"(.*?)\"', chunk)
            desc = desc_m.group(1).strip() if desc_m else ""
            
            # Cover
            img_m = re.search(r'<meta property=\"og:image\" content=\"(.*?)\"', chunk)
            cover = img_m.group(1).strip() if img_m else ""
            
            if not cover or not cover.startswith("http") or cover.endswith("/Logo.svg"):
                return None
            
            clean_title = (title or slug.replace("-", " ").title()).strip()
            clean_desc = (desc or f"Drama Pendek Bahasa Indonesia ({cat}) [Sub Indo].").strip()
            
            return {
                "bookId": f"melolo_{slug}",
                "bookName": clean_title,
                "title": clean_title,
                "slug": slug,
                "category": cat or "Drama Pendek",
                "chapterCount": 50,
                "cover": cover,
                "provider": "melolo",
                "lang": "id",
                "isSubIndo": True,
                "introduction": clean_desc
            }
        except Exception:
            if attempt == 0:
                time.sleep(1)
            else:
                return None
    return None

def save_catalog(combined):
    payload = {
        "version": "2.2.0",
        "updated_at": time.strftime("%Y-%m-%d"),
        "total": len(combined),
        "language": "id",
        "dramas": combined
    }
    tmp_path = CATALOG_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, CATALOG_PATH)

def main():
    log("=== Memulai Sinkronisasi Penuh Katalog Melolo Indonesia ===")
    sitemap_urls = get_sitemap_urls()
    
    existing_by_slug = {}
    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("dramas", []):
                    s = item.get("slug")
                    c = item.get("cover", "")
                    if s and c.startswith("http") and not c.endswith("/Logo.svg"):
                        existing_by_slug[s] = item
        except Exception as e:
            log(f"Peringatan membaca katalog lama: {e}")
    
    log(f"Ditemukan {len(existing_by_slug)} drama tervalidasi sebelumnya.")
    
    to_fetch = [u for u in sitemap_urls if u.rstrip("/").split("/")[-1] not in existing_by_slug]
    log(f"Perlu mengambil {len(to_fetch)} drama tersisa...")
    
    newly_fetched = {}
    done_count = 0
    t0 = time.time()
    last_save_time = time.time()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(parse_drama, u): u for u in to_fetch}
        for f in as_completed(futures):
            res = f.result()
            done_count += 1
            if res:
                newly_fetched[res["slug"]] = res
            
            # Incremental save every 60 items or 20 seconds
            if done_count % 60 == 0 or (time.time() - last_save_time > 20):
                # Build current combined list
                cur_combined = []
                for u in sitemap_urls:
                    s = u.rstrip("/").split("/")[-1]
                    if s in existing_by_slug:
                        cur_combined.append(existing_by_slug[s])
                    elif s in newly_fetched:
                        cur_combined.append(newly_fetched[s])
                save_catalog(cur_combined)
                last_save_time = time.time()
                elapsed = time.time() - t0
                log(f"Progress: {done_count}/{len(to_fetch)} diekstrak. Total aktif di katalog sekarang: {len(cur_combined)} ({elapsed:.1f}s)")

    # Final save
    final_combined = []
    for u in sitemap_urls:
        s = u.rstrip("/").split("/")[-1]
        if s in existing_by_slug:
            final_combined.append(existing_by_slug[s])
        elif s in newly_fetched:
            final_combined.append(newly_fetched[s])
    
    save_catalog(final_combined)
    log(f"=== Selesai 100%! Total drama Melolo Indonesia aktif: {len(final_combined)} ===")

if __name__ == "__main__":
    main()
