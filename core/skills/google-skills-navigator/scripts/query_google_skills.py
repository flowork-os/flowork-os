#!/usr/bin/env python3
"""
⚡ FLOWORK OS — GOOGLE SKILLS NAVIGATOR CLI
High-speed local/remote search and JIT retriever for 100+ Google Agent Skills.
Complies with Sovereign Anti-Bloat Law (Zero Token Bloat).
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request
import ssl

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "index.json"
REMOTE_CATALOG_URL = "https://raw.githubusercontent.com/google/skills/main/index.json"
LOCAL_CLONE_FALLBACK = Path.home() / ".flowork" / "tmp" / "floworkos" / "google-skills"

def load_catalog():
    if CATALOG_PATH.exists():
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("skills", [])
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to read local catalog: {e}\n")

    # Fallback to curl remote fetch
    try:
        proc = subprocess.run(["curl", "-sL", REMOTE_CATALOG_URL], capture_output=True, text=True, timeout=10)
        if proc.returncode == 0 and proc.stdout.strip():
            return json.loads(proc.stdout).get("skills", [])
    except Exception as e:
        sys.stderr.write(f"Warning: curl remote fetch failed: {e}\n")

    return []

def cmd_search(args, skills):
    query_terms = [q.lower() for q in args.query]
    matches = []

    for s in skills:
        name = s.get("name", "").lower()
        desc = s.get("description", "").lower()
        
        score = 0
        for term in query_terms:
            if term in name:
                score += 5
            elif term in desc:
                score += 1
        
        if score > 0:
            matches.append((score, s))

    matches.sort(key=lambda x: x[0], reverse=True)

    limit = args.limit
    results = matches[:limit]

    print(f"⚡ Flowork Google Skills Search: Found {len(matches)} match(es) for '{' '.join(args.query)}' (showing top {len(results)}):")
    print("-" * 75)
    for idx, (_, s) in enumerate(results, 1):
        name = s.get("name")
        desc = s.get("description", "")
        preview = desc[:180] + "..." if len(desc) > 180 else desc
        entrypoint = s.get("entrypoint", "")
        print(f"[{idx}] {name}")
        print(f"    Description: {preview}")
        print(f"    Entrypoint : {entrypoint}")
        print()

def cmd_show(args, skills):
    target = args.name.lower()
    for s in skills:
        if s.get("name", "").lower() == target:
            print(f"Skill Name : {s.get('name')}")
            print(f"Entrypoint : {s.get('entrypoint')}")
            print(f"\nDescription:\n{s.get('description')}")
            return
    sys.stderr.write(f"Error: Skill '{args.name}' not found in catalog.\n")
    sys.exit(1)

def fetch_skill_content(entrypoint, skill_name):
    # Strategy 1: Check if local repository clone has the file
    if LOCAL_CLONE_FALLBACK.exists():
        rel_match = list(LOCAL_CLONE_FALLBACK.glob(f"**/{skill_name}/SKILL.md"))
        if rel_match and rel_match[0].is_file():
            try:
                with open(rel_match[0], "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass

    # Strategy 2: curl fetch (OpenSSL CA store)
    try:
        proc = subprocess.run(["curl", "-sL", entrypoint], capture_output=True, text=True, timeout=15)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout
    except Exception:
        pass

    # Strategy 3: Python urllib with permissive SSL
    try:
        ctx = ssl._create_unverified_context()
        req = Request(entrypoint, headers={"User-Agent": "FloworkOS-MrFlow/1.0"})
        with urlopen(req, context=ctx, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        sys.stderr.write(f"Error fetching skill content: {e}\n")
        sys.exit(1)

def cmd_fetch(args, skills):
    target = args.name.lower()
    entrypoint = None
    for s in skills:
        if s.get("name", "").lower() == target:
            entrypoint = s.get("entrypoint")
            break

    if not entrypoint:
        sys.stderr.write(f"Error: Skill '{args.name}' not found in catalog.\n")
        sys.exit(1)

    print(f"Fetching '{target}'...", file=sys.stderr)
    content = fetch_skill_content(entrypoint, target)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully saved to {out_path}")
    else:
        print(content)

def main():
    parser = argparse.ArgumentParser(description="Google Skills Sovereign Navigator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search
    p_search = subparsers.add_parser("search", help="Search skills by keyword")
    p_search.add_argument("query", nargs="+", help="Keywords to search")
    p_search.add_argument("--limit", type=int, default=5, help="Max results to display")

    # Show
    p_show = subparsers.add_parser("show", help="Show full details of a specific skill")
    p_show.add_argument("name", help="Exact name of the skill")

    # Fetch
    p_fetch = subparsers.add_parser("fetch", help="Fetch raw SKILL.md content for a skill")
    p_fetch.add_argument("name", help="Exact name of the skill")
    p_fetch.add_argument("-o", "--output", help="Optional output file path")

    args = parser.parse_args()
    skills = load_catalog()
    if not skills:
        sys.stderr.write("Error: Skill catalog is empty or unreachable.\n")
        sys.exit(1)

    if args.command == "search":
        cmd_search(args, skills)
    elif args.command == "show":
        cmd_show(args, skills)
    elif args.command == "fetch":
        cmd_fetch(args, skills)

if __name__ == "__main__":
    main()
