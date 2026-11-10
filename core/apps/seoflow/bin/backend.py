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

def execute(payload):
    if not isinstance(payload, dict):
        return {"status": "error", "error": "Invalid payload format"}

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
