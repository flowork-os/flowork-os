#!/usr/bin/env python3
"""
⚡ FLOWORK OS — AGENTIC SEO & GEO AUDITOR CLI
Autonomous SEO, Schema.org JSON-LD, llms.txt, and GEO Citability Analyzer.
Non-Dual Sovereign Tool for Mr. Flow.
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

def parse_html_content(html: str):
    """Parses key SEO and semantic elements from raw HTML using robust regex."""
    data = {
        "title": None,
        "title_len": 0,
        "meta_description": None,
        "description_len": 0,
        "canonical": None,
        "robots": None,
        "og_title": None,
        "og_description": None,
        "og_image": None,
        "h1_tags": [],
        "h2_tags": [],
        "json_ld_blocks": [],
        "word_count": 0,
        "statistics_count": 0,
        "quotable_snippets": []
    }

    # Title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if title_match:
        data["title"] = title_match.group(1).strip()
        data["title_len"] = len(data["title"])

    # Meta Description
    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
    if not desc_match:
        desc_match = re.search(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE)
    if desc_match:
        data["meta_description"] = desc_match.group(1).strip()
        data["description_len"] = len(data["meta_description"])

    # Canonical Link
    canon_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\']', html, re.IGNORECASE)
    if canon_match:
        data["canonical"] = canon_match.group(1).strip()

    # Robots
    robots_match = re.search(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
    if robots_match:
        data["robots"] = robots_match.group(1).strip()

    # OpenGraph Tags
    for prop in ["title", "description", "image"]:
        m = re.search(rf'<meta[^>]*property=["\']og:{prop}["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
        if not m:
            m = re.search(rf'<meta[^>]*content=["\']([^"\']*)["\'][^>]*property=["\']og:{prop}["\']', html, re.IGNORECASE)
        if m:
            data[f"og_{prop}"] = m.group(1).strip()

    # Headings
    h1s = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    data["h1_tags"] = [re.sub(r'<[^>]+>', '', h).strip() for h in h1s if h.strip()]

    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.IGNORECASE | re.DOTALL)
    data["h2_tags"] = [re.sub(r'<[^>]+>', '', h).strip() for h in h2s if h.strip()]

    # Schema JSON-LD
    json_ld_matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.IGNORECASE | re.DOTALL)
    for raw_json in json_ld_matches:
        try:
            parsed = json.loads(raw_json.strip())
            data["json_ld_blocks"].append(parsed)
        except json.JSONDecodeError as e:
            data["json_ld_blocks"].append({"error": "Malformed JSON-LD", "raw": raw_json.strip()[:100]})

    # Text Analysis (Strip HTML tags)
    clean_text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r'<style[^>]*>.*?</style>', ' ', clean_text, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    words = clean_text.split()
    data["word_count"] = len(words)

    # Statistical Density (percentage, numbers, currency metrics)
    stat_matches = re.findall(r'\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?|\b\d{2,}(?:,\d{3})+\b', clean_text)
    data["statistics_count"] = len(stat_matches)

    return data

def evaluate_geo_citability(data: dict) -> dict:
    """Evaluates Generative Engine Optimization (GEO) probability metrics."""
    score = 0
    checks = []

    # 1. Title clarity
    if 30 <= data["title_len"] <= 65:
        score += 15
        checks.append(("Title Tag Length (30-65 chars)", True, f"{data['title_len']} chars"))
    else:
        checks.append(("Title Tag Length (30-65 chars)", False, f"{data['title_len']} chars"))

    # 2. Meta description density
    if 100 <= data["description_len"] <= 165:
        score += 15
        checks.append(("Meta Description (100-165 chars)", True, f"{data['description_len']} chars"))
    else:
        checks.append(("Meta Description (100-165 chars)", False, f"{data['description_len']} chars"))

    # 3. Heading Structure
    h1_count = len(data["h1_tags"])
    if h1_count == 1:
        score += 15
        checks.append(("Single Authoritative H1 Tag", True, f"Found 1 H1: '{data['h1_tags'][0]}'"[:60]))
    elif h1_count == 0:
        checks.append(("Single Authoritative H1 Tag", False, "Missing H1 tag"))
    else:
        checks.append(("Single Authoritative H1 Tag", False, f"Multiple H1 tags ({h1_count}) found"))

    # 4. Schema.org JSON-LD Graph
    valid_schemas = [s for s in data["json_ld_blocks"] if "error" not in s]
    if valid_schemas:
        types = []
        for s in valid_schemas:
            t = s.get("@type", "Unknown")
            types.append(str(t))
        score += 25
        checks.append(("Schema.org JSON-LD Entities", True, f"Valid schemas found: {', '.join(types)}"))
    else:
        checks.append(("Schema.org JSON-LD Entities", False, "No valid JSON-LD entity graph detected"))

    # 5. OpenGraph Tags
    if data["og_title"] and data["og_description"]:
        score += 10
        checks.append(("OpenGraph Social Meta", True, "og:title and og:description present"))
    else:
        checks.append(("OpenGraph Social Meta", False, "Missing og:title or og:description"))

    # 6. Factual / Statistical Density (GEO Quotability)
    if data["statistics_count"] >= 3:
        score += 20
        checks.append(("Factual & Quantitative Claims (GEO)", True, f"Found {data['statistics_count']} statistical data points"))
    else:
        checks.append(("Factual & Quantitative Claims (GEO)", False, f"Low statistical grounding ({data['statistics_count']} points)"))

    return {
        "geo_score": min(score, 100),
        "checks": checks
    }

def audit_target(target: str) -> dict:
    """Audits local path or remote URL."""
    is_remote = target.startswith("http://") or target.startswith("https://")
    html_content = ""
    llms_txt_found = False
    llms_full_found = False

    if is_remote:
        parsed_url = urlparse(target)
        base_origin = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Fetch main HTML
        req = Request(target, headers={"User-Agent": "Flowork-Agentic-Auditor/1.0 (+https://floworkos.org)"})
        try:
            with urlopen(req, timeout=10) as resp:
                html_content = resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return {"error": f"Failed to fetch remote URL: {e}"}

        # Probe llms.txt
        try:
            llm_req = Request(f"{base_origin}/llms.txt", headers={"User-Agent": "Flowork-Agentic-Auditor/1.0"})
            with urlopen(llm_req, timeout=5) as r:
                if r.status == 200:
                    llms_txt_found = True
        except Exception:
            pass

        # Probe llms-full.txt
        try:
            llmf_req = Request(f"{base_origin}/llms-full.txt", headers={"User-Agent": "Flowork-Agentic-Auditor/1.0"})
            with urlopen(llmf_req, timeout=5) as r:
                if r.status == 200:
                    llms_full_found = True
        except Exception:
            pass

    else:
        p = Path(target).resolve()
        if not p.exists():
            return {"error": f"Local target path does not exist: {target}"}

        # Check local llms.txt
        for loc in [p / "llms.txt", p / "public" / "llms.txt"]:
            if loc.exists():
                llms_txt_found = True
                break

        for loc in [p / "llms-full.txt", p / "public" / "llms-full.txt"]:
            if loc.exists():
                llms_full_found = True
                break

        # Locate primary HTML file
        if p.is_file() and p.suffix.lower() in [".html", ".htm"]:
            html_content = p.read_text(encoding='utf-8', errors='ignore')
        else:
            candidates = [p / "index.html", p / "public" / "index.html", p / "dist" / "index.html"]
            found = False
            for c in candidates:
                if c.exists():
                    html_content = c.read_text(encoding='utf-8', errors='ignore')
                    found = True
                    break
            if not found:
                # Search first html
                html_files = list(p.glob("**/*.html"))
                if html_files:
                    html_content = html_files[0].read_text(encoding='utf-8', errors='ignore')
                else:
                    return {"error": "No HTML entrypoint found in target directory."}

    parsed_data = parse_html_content(html_content)
    geo_eval = evaluate_geo_citability(parsed_data)

    # Remediation prioritization
    remediations = []
    if not llms_txt_found:
        remediations.append({"priority": "P0", "title": "Missing llms.txt", "action": "Generate /llms.txt for autonomous agent discoverability."})
    if not parsed_data["canonical"]:
        remediations.append({"priority": "P1", "title": "Missing Canonical Tag", "action": "Inject <link rel='canonical' href='...'> to prevent duplicate content penalty."})
    if not parsed_data["json_ld_blocks"]:
        remediations.append({"priority": "P1", "title": "Missing Schema JSON-LD", "action": "Inject Schema.org Organization and WebSite JSON-LD entity graph."})
    if len(parsed_data["h1_tags"]) != 1:
        remediations.append({"priority": "P1", "title": "Improper H1 Structure", "action": f"Ensure exactly one H1 tag (currently {len(parsed_data['h1_tags'])})."})
    if parsed_data["statistics_count"] < 3:
        remediations.append({"priority": "P2", "title": "Low GEO Citability Density", "action": "Add specific quantitative metrics and research citations under H2 headers."})

    return {
        "target": target,
        "is_remote": is_remote,
        "agentic_readiness": {
            "llms_txt": llms_txt_found,
            "llms_full_txt": llms_full_found,
        },
        "seo_data": parsed_data,
        "geo_evaluation": geo_eval,
        "remediations": remediations
    }

def print_human_report(report: dict):
    print("=================================================================")
    print("⚡ FLOWORK OS — AGENTIC SEO & GEO AUDIT REPORT")
    print(f"Target: {report['target']}")
    print("=================================================================\n")

    agentic = report["agentic_readiness"]
    print("🤖 1. AGENTIC WEB READINESS:")
    print(f"   - /llms.txt Presence:      {'✅ FOUND' if agentic['llms_txt'] else '❌ MISSING (P0)'}")
    print(f"   - /llms-full.txt Presence: {'✅ FOUND' if agentic['llms_full_txt'] else '⚪ OPTIONAL'}")

    geo = report["geo_evaluation"]
    print(f"\n🔮 2. GENERATIVE ENGINE OPTIMIZATION (GEO) SCORE: [{geo['geo_score']}/100]")
    for title, status, note in geo["checks"]:
        symbol = "✅" if status else "❌"
        print(f"   {symbol} {title:35}: {note}")

    seo = report["seo_data"]
    print(f"\n🔍 3. TECHNICAL SEO & GRAPH INTEGRITY:")
    print(f"   - Title:             {seo['title'] or 'NONE'} ({seo['title_len']} chars)")
    print(f"   - Meta Description:  {seo['meta_description'] or 'NONE'} ({seo['description_len']} chars)")
    print(f"   - Canonical Link:    {seo['canonical'] or 'MISSING'}")
    print(f"   - H1 Tag Count:      {len(seo['h1_tags'])}")
    print(f"   - Schema.org Blocks: {len(seo['json_ld_blocks'])} block(s)")
    print(f"   - Word Count:        {seo['word_count']} words")

    remedies = report["remediations"]
    print(f"\n⚡ 4. PRIORITIZED REMEDIATION ACTIONS ({len(remedies)}):")
    if not remedies:
        print("   ✅ Perfect audit score! No remediation needed.")
    else:
        for r in remedies:
            print(f"   [{r['priority']}] {r['title']}: {r['action']}")
    print("\n=================================================================")

def main():
    parser = argparse.ArgumentParser(description="Flowork Sovereign Agentic SEO & GEO Auditor")
    parser.add_argument("target", help="Target URL (e.g. https://example.com) or local project path")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON format")
    args = parser.parse_args()

    report = audit_target(args.target)
    if "error" in report:
        sys.stderr.write(f"❌ Error: {report['error']}\n")
        sys.exit(1)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human_report(report)

    sys.exit(0)

if __name__ == "__main__":
    main()
