#!/usr/bin/env python3
"""
👑 FLOWORK OS — DETERMINISTIC AST & AI CODE REVIEW RUNNER (code_review_audit)
Powered by Flowork Sovereign Code Review Engine (`ocr`) routed via Sovereign Connector (:9099).
"""

import sys
import os
import json
import subprocess

OCR_BIN = "/opt/floworkos/bin/ocr"


def main():
    try:
        raw_input = sys.stdin.read()
        params = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        params = {}

    repo_dir = params.get("repo_dir") or os.getcwd()
    from_ref = params.get("from_ref")
    to_ref = params.get("to_ref")
    commit = params.get("commit")
    staged = params.get("staged", True)
    audience = params.get("audience", "agent")
    format_type = params.get("format", "json")
    preview = params.get("preview", False)

    if not os.path.exists(OCR_BIN):
        output = {
            "status": "error",
            "error": f"OCR binary not found at {OCR_BIN}"
        }
        print(json.dumps(output))
        sys.exit(1)

    cmd = [OCR_BIN, "review", "--repo", repo_dir, "--audience", audience]

    if preview:
        cmd.append("--preview")
    else:
        cmd.extend(["--format", format_type])

    if commit:
        cmd.extend(["--commit", commit])
    elif from_ref and to_ref:
        cmd.extend(["--from", from_ref, "--to", to_ref])
    elif from_ref:
        cmd.extend(["--from", from_ref])

    # Run OCR review
    env = os.environ.copy()
    env["OPENAI_BASE_URL"] = "http://127.0.0.1:9099/v1"
    env["OPENAI_API_KEY"] = "flowork-sovereign"

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )
        
        stdout = res.stdout.strip()
        stderr = res.stderr.strip()

        if format_type == "json" and not preview:
            try:
                data = json.loads(stdout)
                print(json.dumps({"status": "ok", "results": data}))
                sys.exit(0)
            except Exception:
                pass

        print(json.dumps({
            "status": "ok" if res.returncode == 0 else "failed",
            "returncode": res.returncode,
            "stdout": stdout,
            "stderr": stderr
        }))
        sys.exit(res.returncode)

    except subprocess.TimeoutExpired:
        print(json.dumps({"status": "timeout", "error": "Code review execution timed out."}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
