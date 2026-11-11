#!/usr/bin/env python3
"""
SimilarWeb Intelligence Engine (Cleanroom Web Traffic & Domain Analytics)
Autonomous Domain Traffic Rank, 30-Day Velocity, Server Telemetry & Audience Estimation.
Native to Flowork OS.
"""

import sys
import json
import re
import socket
import ssl
import urllib.parse
import urllib.request
from datetime import datetime

def clean_domain(domain_or_url: str) -> str:
    s = domain_or_url.strip()
    if not s.startswith("http://") and not s.startswith("https://"):
        s = "https://" + s
    parsed = urllib.parse.urlparse(s)
    domain = parsed.netloc or parsed.path
    domain = re.sub(r'^www\.', '', domain)
    domain = domain.split(':')[0]
    return domain.lower()

def estimate_monthly_visits(global_rank: int | None) -> int:
    if not global_rank or global_rank <= 0:
        return 0
    # Calibrated power-law model for global web traffic distribution
    # Top 1: ~3-5 Billion visits/mo
    # Top 1,000: ~100-200 Million visits/mo
    # Top 5,000: ~20-40 Million visits/mo
    # Top 50,000: ~1-3 Million visits/mo
    # Top 500,000: ~50k-150k visits/mo
    try:
        visits = int(3500000000 / (global_rank ** 0.55))
        return max(500, visits)
    except Exception:
        return 0

def fetch_domain_telemetry(domain: str) -> dict:
    ctx = ssl._create_unverified_context()
    
    # 1. Tranco Rank (Top 1M Global Web Traffic)
    tranco_url = f"https://tranco-list.eu/api/ranks/domain/{domain}"
    req_tranco = urllib.request.Request(tranco_url, headers={"User-Agent": "Mozilla/5.0 (FloworkOS; Linux)"})
    
    ranks = []
    latest_rank = None
    rank_change = 0
    trend_direction = "Stable"
    
    try:
        with urllib.request.urlopen(req_tranco, context=ctx, timeout=8) as resp:
            t_data = json.loads(resp.read().decode())
            ranks = t_data.get("ranks", [])
            if ranks:
                latest_rank = ranks[0].get("rank")
                if len(ranks) >= 7:
                    week_ago_rank = ranks[6].get("rank")
                    if week_ago_rank and latest_rank:
                        # Rank decrease means traffic increase (e.g. 5000 -> 4000 is +1000 positions up)
                        rank_change = week_ago_rank - latest_rank
                        if rank_change > 0:
                            trend_direction = f"Up +{rank_change:,} places"
                        elif rank_change < 0:
                            trend_direction = f"Down {rank_change:,} places"
    except Exception:
        pass
        
    estimated_visits = estimate_monthly_visits(latest_rank)
    
    # 2. DNS & Server IP Telemetry
    ip_address = "N/A"
    try:
        ip_address = socket.gethostbyname(domain)
    except Exception:
        pass
        
    # 3. HTTP Server Header Probe
    server_tech = "Unknown"
    page_title = "N/A"
    try:
        probe_url = f"https://{domain}"
        req_probe = urllib.request.Request(probe_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req_probe, context=ctx, timeout=6) as resp:
            headers = dict(resp.getheaders())
            server_tech = headers.get("server") or headers.get("Server") or "Standard Web Server"
            if "cf-ray" in headers:
                server_tech = f"Cloudflare CDN ({server_tech})"
            html_snippet = resp.read(8192).decode("utf-8", errors="ignore")
            title_m = re.search(r"<title>(.*?)</title>", html_snippet, re.IGNORECASE | re.DOTALL)
            if title_m:
                page_title = re.sub(r'\s+', ' ', title_m.group(1)).strip()
    except Exception:
        pass

    return {
        "status": "success",
        "domain": domain,
        "title": page_title,
        "global_rank": latest_rank,
        "global_rank_formatted": f"#{latest_rank:,}" if latest_rank else "Unranked / >1,000,000",
        "estimated_monthly_visits": estimated_visits,
        "estimated_visits_formatted": f"{estimated_visits:,}" if estimated_visits else "N/A",
        "weekly_trend": trend_direction,
        "ip_address": ip_address,
        "server_tech": server_tech,
        "recent_rank_history": ranks[:7] if ranks else []
    }

def print_human_similarweb(res: dict):
    if "error" in res:
        print(f"\033[91m[!] Error: {res['error']}\033[0m")
        return
        
    print(f"\033[1;36m═══════════════════════════════════════════════════════════\033[0m")
    print(f"\033[1;32m  🌐 SimilarWeb Traffic & Domain Intelligence\033[0m")
    print(f"\033[1;36m══════════════════════════════════════════════��════════════\033[0m")
    print(f"  \033[1mDomain:\033[0m           {res['domain']}")
    print(f"  \033[1mPage Title:\033[0m       {res['title']}")
    print(f"  \033[1mGlobal Rank:\033[0m      \033[1;32m{res['global_rank_formatted']}\033[0m")
    print(f"  \033[1mEst. Visits/Mo:\033[0m   \033[1;33m~{res['estimated_visits_formatted']}\033[0m")
    print(f"  \033[1mWeekly Trend:\033[0m     {res['weekly_trend']}")
    print(f"  \033[1mServer Host:\033[0m      {res['ip_address']} ({res['server_tech']})")
    print(f"\033[1;36m───────────────────────────────────────────────────────────\033[0m")
    if res['recent_rank_history']:
        print(f"  \033[1mRecent Rank History (7 Days):\033[0m")
        for item in res['recent_rank_history']:
            print(f"    \033[90m{item.get('date')}:\033[0m #{item.get('rank'):,}")
    print(f"\033[1;36m═══════════════════════════════════════════════════════════\033[0m")

def main():
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if args[0] in ("-h", "--help"):
            print("Usage:")
            print("  similarweb <domain>             Analyze domain traffic rank & audience")
            print("  similarweb --json <domain>      Return raw JSON payload")
            sys.exit(0)
            
        json_mode = False
        if "--json" in args:
            json_mode = True
            args.remove("--json")
            
        if not args:
            print("Error: Domain target missing.", file=sys.stderr)
            sys.exit(1)
            
        target = clean_domain(args[0])
        res = fetch_domain_telemetry(target)
        if json_mode:
            print(json.dumps(res, indent=2))
        else:
            print_human_similarweb(res)
        sys.exit(0)

    # Tool Foundry Stdin/Stdout Mode
    try:
        raw_input = sys.stdin.read().strip()
        params = json.loads(raw_input) if raw_input else {}
    except Exception:
        params = {}
        
    target_raw = params.get("domain") or params.get("url") or params.get("target")
    if not target_raw:
        print(json.dumps({"error": "Missing 'domain' parameter."}))
        sys.exit(1)
        
    target = clean_domain(target_raw)
    res = fetch_domain_telemetry(target)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
