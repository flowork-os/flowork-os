#!/usr/bin/env python3
"""
VidIQ Intelligence Engine (vidIQ Vision Cleanroom Replicator)
Autonomous YouTube SEO, Video Tags, View Velocity & Competitive Intelligence.
Native to Flowork OS.
"""

import sys
import json
import re
import subprocess
import urllib.parse
import urllib.request
import ssl
from datetime import datetime, timezone

def parse_video_id(url_or_id: str) -> str:
    s = url_or_id.strip()
    if len(s) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', s):
        return s
    m = re.search(r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{11})', s)
    if m:
        return m.group(1)
    return s

def calculate_seo_score(title: str, description: str, tags: list[str]) -> dict:
    score = 0
    breakdown = {}
    
    # 1. Tag count (Max 20 pts)
    t_count = len(tags)
    if t_count >= 15:
        tag_score = 20
    elif t_count >= 8:
        tag_score = 15
    elif t_count >= 3:
        tag_score = 10
    elif t_count > 0:
        tag_score = 5
    else:
        tag_score = 0
    score += tag_score
    breakdown["tag_count_score"] = tag_score
    
    # 2. Title length (Max 20 pts: 40-70 chars is sweet spot)
    t_len = len(title)
    if 35 <= t_len <= 75:
        title_score = 20
    elif 20 <= t_len <= 95:
        title_score = 14
    elif t_len > 0:
        title_score = 8
    else:
        title_score = 0
    score += title_score
    breakdown["title_length_score"] = title_score
    
    # 3. Tags in Title (Max 20 pts)
    title_lower = title.lower()
    matching_title_tags = [t for t in tags if t.lower() in title_lower]
    if len(matching_title_tags) >= 3:
        tt_score = 20
    elif len(matching_title_tags) >= 1:
        tt_score = 12
    else:
        tt_score = 4
    score += tt_score
    breakdown["tags_in_title_score"] = tt_score
    
    # 4. Tags in Description (Max 20 pts)
    desc_lower = description.lower()
    matching_desc_tags = [t for t in tags if t.lower() in desc_lower]
    if len(matching_desc_tags) >= 5:
        td_score = 20
    elif len(matching_desc_tags) >= 2:
        td_score = 14
    elif len(matching_desc_tags) >= 1:
        td_score = 8
    else:
        td_score = 0
    score += td_score
    breakdown["tags_in_desc_score"] = td_score
    
    # 5. Description Depth & Links (Max 20 pts)
    d_len = len(description)
    has_links = bool(re.search(r'https?://', description))
    desc_points = 0
    if d_len >= 300:
        desc_points += 12
    elif d_len >= 100:
        desc_points += 6
    if has_links:
        desc_points += 8
    score += desc_points
    breakdown["desc_depth_and_links_score"] = desc_points
    
    return {
        "overall_score": min(100, score),
        "rating": "Excellent" if score >= 80 else ("Good" if score >= 60 else ("Needs Work" if score >= 40 else "Poor")),
        "breakdown": breakdown
    }

def analyze_video(url_or_id: str) -> dict:
    video_id = parse_video_id(url_or_id)
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Extract via native yt-dlp
    cmd = ["/usr/local/bin/yt-dlp", "--dump-json", "--no-warnings", "--skip-download", url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode != 0:
            return {"error": f"Failed to retrieve video details: {proc.stderr.strip()[:200]}"}
        info = json.loads(proc.stdout)
    except Exception as e:
        return {"error": str(e)}
        
    title = info.get("title", "")
    description = info.get("description", "")
    tags = info.get("tags") or []
    uploader = info.get("uploader", "")
    uploader_id = info.get("uploader_id", "")
    channel_url = info.get("channel_url", "")
    view_count = info.get("view_count", 0)
    like_count = info.get("like_count", 0)
    duration = info.get("duration", 0)
    timestamp = info.get("timestamp")
    
    # Compute velocity (VPH)
    vph = 0.0
    age_hours = 0.0
    if timestamp:
        now_ts = datetime.now(timezone.utc).timestamp()
        age_hours = max(0.1, (now_ts - timestamp) / 3600.0)
        vph = round(view_count / age_hours, 1)
        upload_date_str = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    else:
        upload_date_str = info.get("upload_date", "N/A")
        
    # Calculate SEO score
    seo_audit = calculate_seo_score(title, description, tags)
    
    # Duration formatted
    mins, secs = divmod(duration, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        duration_fmt = f"{hours}:{mins:02d}:{secs:02d}"
    else:
        duration_fmt = f"{mins}:{secs:02d}"
        
    return {
        "status": "success",
        "video_id": video_id,
        "url": url,
        "title": title,
        "uploader": uploader,
        "uploader_id": uploader_id,
        "channel_url": channel_url,
        "views": view_count,
        "likes": like_count,
        "duration_seconds": duration,
        "duration_formatted": duration_fmt,
        "upload_date": upload_date_str,
        "age_hours": round(age_hours, 1),
        "views_per_hour": vph,
        "tags_count": len(tags),
        "tags": tags,
        "seo_score": seo_audit["overall_score"],
        "seo_rating": seo_audit["rating"],
        "seo_breakdown": seo_audit["breakdown"],
        "description_snippet": description[:300] + ("..." if len(description) > 300 else "")
    }

def analyze_keyword_competitors(keyword: str, max_competitors: int = 5) -> dict:
    ctx = ssl._create_unverified_context()
    q = urllib.parse.quote_plus(keyword)
    search_url = f"https://www.youtube.com/results?search_query={q}"
    req = urllib.request.Request(search_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    })
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return {"error": f"Failed to search YouTube: {str(e)}"}
        
    video_ids = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", html)
    unique_ids = list(dict.fromkeys(video_ids))[:max_competitors]
    
    competitors = []
    all_tags = []
    total_views = 0
    total_likes = 0
    
    for v_id in unique_ids:
        c_res = analyze_video(v_id)
        if "error" not in c_res:
            competitors.append({
                "video_id": v_id,
                "title": c_res["title"],
                "uploader": c_res["uploader"],
                "views": c_res["views"],
                "vph": c_res["views_per_hour"],
                "seo_score": c_res["seo_score"],
                "tags": c_res["tags"]
            })
            all_tags.extend(c_res.get("tags") or [])
            total_views += (c_res.get("views") or 0)
            total_likes += (c_res.get("likes") or 0)
            
    # Calculate tag frequency
    tag_freq = {}
    for t in all_tags:
        t_clean = t.strip()
        if t_clean:
            tag_freq[t_clean] = tag_freq.get(t_clean, 0) + 1
            
    sorted_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)
    avg_views = int(total_views / max(1, len(competitors)))
    
    return {
        "status": "success",
        "keyword": keyword,
        "competitor_count": len(competitors),
        "average_views": avg_views,
        "high_opportunity_tags": [{"tag": k, "frequency": v} for k, v in sorted_tags[:15]],
        "top_competitors": competitors
    }

def print_human_video(res: dict):
    if "error" in res:
        print(f"\033[91m[!] Error: {res['error']}\033[0m")
        return
        
    print(f"\033[1;36m═══════════════════════════════════════════════════════════\033[0m")
    print(f"\033[1;32m  ⚡ VidIQ Video Intelligence Audit\033[0m")
    print(f"\033[1;36m═══════════════════════════════════════════════════════════\033[0m")
    print(f"  \033[1mTitle:\033[0m       {res['title']}")
    print(f"  \033[1mChannel:\033[0m     {res['uploader']}")
    print(f"  \033[1mDuration:\033[0m    {res['duration_formatted']} | \033[1mUploaded:\033[0m {res['upload_date']}")
    print(f"  \033[1mViews:\033[0m       {res['views']:,} | \033[1mLikes:\033[0m {res['likes']:,}")
    print(f"  \033[1mVelocity:\033[0m    \033[1;33m{res['views_per_hour']:,} VPH (Views/Hour)\033[0m")
    print(f"  \033[1mSEO Score:\033[0m   \033[1;32m{res['seo_score']}/100 ({res['seo_rating']})\033[0m")
    print(f"\033[1;36m───────────────────────────────────────────────────────────\033[0m")
    print(f"  \033[1mTags ({res['tags_count']}):\033[0m")
    if res['tags']:
        for i, tag in enumerate(res['tags'], 1):
            print(f"    \033[90m{i:02d}.\033[0m \033[97m{tag}\033[0m")
    else:
        print("    \033[90m(No public tags found for this video)\033[0m")
    print(f"\033[1;36m═══════════════════════════════════════════════════════════\033[0m")

def print_human_keyword(res: dict):
    if "error" in res:
        print(f"\033[91m[!] Error: {res['error']}\033[0m")
        return
        
    print(f"\033[1;36m═══════════════════════════════════════════════════════════\033[0m")
    print(f"\033[1;32m  ⚡ VidIQ Keyword & Competitor Intelligence\033[0m")
    print(f"\033[1;36m═══════════════════════════════════════════════════════════\033[0m")
    print(f"  \033[1mKeyword:\033[0m       {res['keyword']}")
    print(f"  \033[1mAvg Views:\033[0m     \033[1;33m{res['average_views']:,}\033[0m")
    print(f"  \033[1mCompetitors:\033[0m   {res['competitor_count']} analyzed")
    print(f"\033[1;36m─────���─────────────────────────────────────────────────────\033[0m")
    print(f"  \033[1mWinning Competitor Tags (Most Frequent):\033[0m")
    for item in res['high_opportunity_tags']:
        print(f"    \033[1;32m•\033[0m {item['tag']} \033[90m(used in {item['frequency']} top videos)\033[0m")
    print(f"\033[1;36m═══════════════════════════════════════════════════════════\033[0m")

def main():
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if args[0] in ("-h", "--help"):
            print("Usage:")
            print("  vidiq <video_url_or_id>        Analyze YouTube video tags & SEO score")
            print("  vidiq --kw <keyword>           Analyze YouTube competitors & tags for keyword")
            print("  vidiq --json <video_or_kw>     Return JSON payload")
            sys.exit(0)
            
        json_mode = False
        if "--json" in args:
            json_mode = True
            args.remove("--json")
            
        if not args:
            print("Error: Target missing.", file=sys.stderr)
            sys.exit(1)
            
        if args[0] in ("--kw", "-k"):
            kw = " ".join(args[1:])
            res = analyze_keyword_competitors(kw)
            if json_mode:
                print(json.dumps(res, indent=2))
            else:
                print_human_keyword(res)
        else:
            target = args[0]
            res = analyze_video(target)
            if json_mode:
                print(json.dumps(res, indent=2))
            else:
                print_human_video(res)
        sys.exit(0)
        
    # Tool Foundry Stdin/Stdout Mode
    try:
        raw_input = sys.stdin.read().strip()
        if raw_input:
            params = json.loads(raw_input)
        else:
            params = {}
    except Exception:
        params = {}
        
    video = params.get("video") or params.get("url") or params.get("video_id")
    keyword = params.get("keyword") or params.get("query")
    
    if video:
        result = analyze_video(video)
    elif keyword:
        result = analyze_keyword_competitors(keyword)
    else:
        result = {"error": "Missing 'video' or 'keyword' parameter."}
        
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
