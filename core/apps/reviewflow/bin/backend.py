#!/usr/bin/env python3
"""
👑 FLOWORK OS — REVIEWFLOW STUDIO BACKEND
Dispatches code review commands to /opt/floworkos/bin/ocr routed via Sovereign Connector (:9099).
"""

import os
import sys
import json
import subprocess

OCR_BIN = "/opt/floworkos/bin/ocr"


def execute(payload):
    action = payload.get("action")
    
    if action == "preview_diff":
        repo_dir = payload.get("repo_dir") or "/opt/flowork-os-repo"
        if not os.path.isdir(os.path.join(repo_dir, ".git")):
            return {"status": "error", "error": f"Directory is not a valid git repository: {repo_dir}"}
        
        try:
            cmd = [OCR_BIN, "review", "--repo", repo_dir, "--preview"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Also get git status
            git_st = subprocess.run(["git", "-C", repo_dir, "status", "-s"], capture_output=True, text=True, timeout=10)
            
            return {
                "status": "success",
                "preview": res.stdout.strip(),
                "git_status": git_st.stdout.strip(),
                "repo_dir": repo_dir
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif action == "run_review":
        repo_dir = payload.get("repo_dir") or "/opt/flowork-os-repo"
        if not os.path.isdir(os.path.join(repo_dir, ".git")):
            return {"status": "error", "error": f"Directory is not a valid git repository: {repo_dir}"}

        env = os.environ.copy()
        env["OPENAI_BASE_URL"] = "http://127.0.0.1:9099/v1"
        env["OPENAI_API_KEY"] = "flowork-sovereign"

        try:
            cmd = [OCR_BIN, "review", "--repo", repo_dir, "--audience", "agent", "--format", "json"]
            res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=180)
            
            output_json = None
            try:
                output_json = json.loads(res.stdout)
            except Exception:
                output_json = {"raw": res.stdout, "stderr": res.stderr}

            return {
                "status": "success",
                "review": output_json,
                "returncode": res.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Review execution timed out (exceeded 180s)."}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif action == "get_default_repos":
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "flowork-os-repo"),
            os.path.join(home, "project"),
            "/opt/floworkos"
        ]
        valid_repos = [c for c in candidates if os.path.isdir(os.path.join(c, ".git"))]
        return {
            "status": "success",
            "repos": valid_repos if valid_repos else [os.path.join(home, "flowork-os-repo")]
        }

    return {"status": "error", "error": f"Unknown action: {action}"}
