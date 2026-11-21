#!/usr/bin/env python3
"""
👑 FLOWORK OS — SEOFlow Backend IPC Service
Bridges Quantum Glass WebKit frontend with /usr/local/bin/ubersuggest engine.
"""

import sys
import os
import json
import subprocess

UBERSUGGEST_RUNNER = "/opt/floworkos/tools/ubersuggest/run.py"
VIDIQ_RUNNER = "/opt/floworkos/tools/vidiq/run.py"
SIMILARWEB_RUNNER = "/opt/floworkos/tools/similarweb/run.py"

def execute(payload):
    if not isinstance(payload, dict):
        return {"status": "error", "error": "Invalid payload format"}

    action_type = payload.get("type") or payload.get("action") or "ubersuggest"

    # Route 1: VidIQ YouTube Intelligence
    if action_type == "vidiq":
        target = payload.get("video") or payload.get("url") or payload.get("keyword") or payload.get("query")
        if not target:
            return {"status": "error", "error": "Video URL, ID, or keyword is required for VidIQ"}
        
        mode = payload.get("mode")
        if mode == "video" or "youtube.com" in target or "youtu.be" in target or (len(target) == 11 and " " not in target and "/" not in target):
            inp_dict = {"video": target}
        else:
            inp_dict = {"keyword": target}

        try:
            proc = subprocess.run(
                [sys.executable, VIDIQ_RUNNER],
                input=json.dumps(inp_dict),
                text=True,
                capture_output=True,
                timeout=25
            )
            if proc.returncode != 0:
                return {"status": "error", "error": proc.stderr.strip() or "VidIQ execution failed"}
            return json.loads(proc.stdout)
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # Route 2: SimilarWeb Domain Traffic
    if action_type == "similarweb":
        domain = payload.get("domain") or payload.get("url") or payload.get("target") or payload.get("keyword")
        if not domain:
            return {"status": "error", "error": "Domain name or URL is required for SimilarWeb"}
        
        try:
            proc = subprocess.run(
                [sys.executable, SIMILARWEB_RUNNER],
                input=json.dumps({"domain": domain}),
                text=True,
                capture_output=True,
                timeout=15
            )
            if proc.returncode != 0:
                return {"status": "error", "error": proc.stderr.strip() or "SimilarWeb execution failed"}
            return json.loads(proc.stdout)
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # Route 3: Standard Ubersuggest + Dual Suggestions
    keyword = payload.get("keyword") or payload.get("query")
    if not keyword:
        return {"status": "error", "error": "Keyword parameter is required"}

    country = payload.get("country", "id")
    language = payload.get("language", "id" if country == "id" else "en")
    include_ideas = payload.get("include_ideas", True)

    input_json = json.dumps({
        "keyword": keyword,
        "country": country,
        "language": language,
        "include_ideas": include_ideas
    })

    try:
        proc = subprocess.run(
            [sys.executable, UBERSUGGEST_RUNNER],
            input=input_json,
            text=True,
            capture_output=True,
            timeout=25
        )
        if proc.returncode != 0:
            return {
                "status": "error",
                "error": proc.stderr.strip() or "Engine execution failed",
                "raw_stdout": proc.stdout.strip()
            }
        
        result_data = json.loads(proc.stdout)
        return result_data
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "SEO query timed out (25s limit)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    test_res = execute({"keyword": "test", "country": "id"})
    print(json.dumps(test_res, indent=2))
