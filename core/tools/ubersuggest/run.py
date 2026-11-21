#!/usr/bin/env python3
"""
👑 FLOWORK OS — SOVEREIGN UBERSUGGEST SEO ENGINE RUNNER (ubersuggest)
Reverse-engineered headless SEO intelligence engine.
Delivers real-time search volume, CPC, SEO difficulty, and keyword ideas without Chrome.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import ssl

TOKEN_CACHE_FILE = "/tmp/flowork_ubersuggest_token.json"
EXTENSION_VERSION = "4.0.37.2016"
ORIGIN_HEADER = "chrome-extension://nmpgaoofmjlimabncmnmnopjabbflegf"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

LOC_MAP = {
    "id": 2360, "indonesia": 2360,
    "us": 2840, "united states": 2840, "usa": 2840,
    "uk": 2826, "united kingdom": 2826, "gb": 2826,
    "sg": 2702, "singapore": 2702,
    "my": 2458, "malaysia": 2458,
    "au": 2036, "australia": 2036,
    "in": 2356, "india": 2356,
    "ph": 2608, "philippines": 2608,
    "ca": 2124, "canada": 2124,
    "de": 2276, "germany": 2276,
    "jp": 2392, "japan": 2392
}

def get_ssl_context():
    ctx = ssl._create_unverified_context()
    return ctx

def get_auth_token():
    # Check cache
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                cached = json.load(f)
            token = cached.get("token")
            ttl_str = cached.get("ttl")
            if token:
                # Return cached token
                return token
        except Exception:
            pass

    # Fetch new token headlessly
    url = "https://ubersuggest.com/api/get_extension_token"
    headers = {
        "User-Agent": USER_AGENT,
        "Origin": ORIGIN_HEADER,
        "X-UBS-Ext-Version": EXTENSION_VERSION
    }
    req = urllib.request.Request(url, headers=headers)
    ctx = get_ssl_context()
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        token = data.get("token")
        if token:
            try:
                with open(TOKEN_CACHE_FILE, "w") as f:
                    json.dump(data, f)
            except Exception:
                pass
            return token
    raise RuntimeError("Failed to obtain extension authentication token")

def fetch_keyword_info(keyword, loc_id, lang, token):
    ts = str(int(time.time()))
    encoded_kw = urllib.parse.quote_plus(keyword.strip().lower())
    url = f"https://ubersuggest.com/api/keyword_info?keyword={encoded_kw}&language={lang}&locId={loc_id}"
    headers = {
        "User-Agent": USER_AGENT,
        "Origin": ORIGIN_HEADER,
        "X-UBS-Ext-Version": EXTENSION_VERSION,
        "ts": ts,
        "Authorization": f"Bearer {token}"
    }
    req = urllib.request.Request(url, headers=headers)
    ctx = get_ssl_context()
    with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
        return json.loads(resp.read().decode())

def fetch_google_suggestions(keyword, lang, country):
    encoded_kw = urllib.parse.quote_plus(keyword.strip())
    url = f"https://suggestqueries.google.com/complete/search?client=chrome&hl={lang}&gl={country}&q={encoded_kw}"
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)
    ctx = get_ssl_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                return data[1][:15]
    except Exception:
        pass
    return []

def fetch_youtube_suggestions(keyword, lang, country):
    encoded_kw = urllib.parse.quote_plus(keyword.strip())
    url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl={lang}&gl={country}&q={encoded_kw}"
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)
    ctx = get_ssl_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                return data[1][:20]
    except Exception:
        pass
    return []

def evaluate_difficulty(sd):
    if sd is None:
        return "UNKNOWN"
    if sd < 30:
        return "EASY (High ranking potential for new/small websites)"
    elif sd < 60:
        return "MEDIUM (Requires solid backlinks & topical authority)"
    else:
        return "HARD (Dominated by massive enterprise brands)"

def main():
    try:
        raw_input = sys.stdin.read()
        params = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        params = {}

    keyword = params.get("keyword") or params.get("query")
    if not keyword:
        # CLI fallback
        if len(sys.argv) > 1:
            keyword = " ".join(sys.argv[1:])
        else:
            print(json.dumps({
                "status": "error",
                "message": "Missing required parameter 'keyword' or 'query'"
            }))
            sys.exit(1)

    country = str(params.get("country", "id")).strip().lower()
    lang = str(params.get("language", "id" if country == "id" else "en")).strip().lower()
    loc_id = LOC_MAP.get(country, 2360 if lang == "id" else 2840)
    include_ideas = params.get("include_ideas", True)

    try:
        token = get_auth_token()
        try:
            raw_data = fetch_keyword_info(keyword, loc_id, lang, token)
        except urllib.error.HTTPError as he:
            if he.code in (401, 403):
                # Token expired, clear cache and retry once
                if os.path.exists(TOKEN_CACHE_FILE):
                    os.remove(TOKEN_CACHE_FILE)
                token = get_auth_token()
                raw_data = fetch_keyword_info(keyword, loc_id, lang, token)
            else:
                raise

        kw_info = raw_data.get("keywordInfo", {})
        volume = kw_info.get("volume", 0)
        sd = kw_info.get("sd", 0)
        pd = kw_info.get("pd", 0)
        cpc = kw_info.get("cpc", 0.0)
        cpc_usd = kw_info.get("cpcDollars", 0.0)
        competition = kw_info.get("competition", 0.0)
        monthly_trends = kw_info.get("ms", {})
        intents_raw = kw_info.get("searchIntent", [])

        intent_map = {
            1: "Informational (Learn/Guide)",
            2: "Navigational (Find specific website)",
            3: "Commercial (Comparison/Research)",
            4: "Transactional (Buy/Order)"
        }
        intents = [intent_map.get(i, f"Intent {i}") for i in intents_raw] if intents_raw else ["General"]

        # Fetch related long-tail keyword ideas
        related_ideas = []
        youtube_ideas = []
        if include_ideas:
            related_ideas = fetch_google_suggestions(keyword, lang, country)
            youtube_ideas = fetch_youtube_suggestions(keyword, lang, country)

        result = {
            "status": "success",
            "keyword": keyword,
            "location": {
                "country": country.upper(),
                "language": lang,
                "locId": loc_id
            },
            "metrics": {
                "monthly_search_volume": volume,
                "seo_difficulty_score": sd,
                "seo_difficulty_assessment": evaluate_difficulty(sd),
                "paid_difficulty_score": pd,
                "cost_per_click_idr": round(cpc, 2) if cpc else 0.0,
                "cost_per_click_usd": round(cpc_usd, 2) if cpc_usd else 0.0,
                "paid_competition_index": round(competition, 2),
                "search_intent": intents
            },
            "historical_monthly_trends": monthly_trends,
            "related_keyword_ideas": related_ideas,
            "youtube_suggestions": youtube_ideas
        }

        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        error_output = {
            "status": "error",
            "keyword": keyword,
            "error_type": type(e).__name__,
            "message": str(e)
        }
        print(json.dumps(error_output, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
