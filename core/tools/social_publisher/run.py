#!/usr/bin/env python3
"""
Social Publisher - Sovereign Multi-Platform Social Media Publishing Tool for Flowork OS.
Executes automated upload, check, and login operations via patchright anti-detect headless engine.
"""

import sys
import os
import json
import subprocess
from datetime import datetime, timezone

SAU_CLI = "/opt/floworkos/bin/sau"
PYTHON_BIN = "/opt/floworkos/apps/social-auto-upload/.venv/bin/python"
SAU_APP_DIR = "/opt/floworkos/apps/social-auto-upload"

SUPPORTED_PLATFORMS = [
    "youtube", "douyin", "kuaishou", "xiaohongshu", "bilibili",
    "tencent", "alipay", "weibo", "hupu", "facebook", "facebook-page",
    "instagram", "baijiahao", "dayu", "xueqiu", "zhihu"
]

def run_sau_command(cmd_args: list[str]) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = SAU_APP_DIR
    try:
        proc = subprocess.run(
            [PYTHON_BIN, os.path.join(SAU_APP_DIR, "sau_cli.py")] + cmd_args,
            cwd=SAU_APP_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "Execution timed out after 300 seconds."
    except Exception as e:
        return 1, "", str(e)

def main():
    try:
        raw_input = sys.stdin.read().strip()
        params = json.loads(raw_input) if raw_input else {}
    except Exception:
        params = {}

    action = params.get("action")
    platform = params.get("platform", "").lower().strip()
    account = params.get("account", "main").strip()
    file_path = params.get("file_path")
    title = params.get("title")
    desc = params.get("description", "")
    tags = params.get("tags", [])
    visibility = params.get("visibility", "public")
    thumbnail = params.get("thumbnail")
    schedule = params.get("schedule")

    if not action or not platform:
        print(json.dumps({
            "success": False,
            "error": "Both 'action' and 'platform' parameters are mandatory.",
            "supported_platforms": SUPPORTED_PLATFORMS
        }, indent=2))
        sys.exit(1)

    if platform not in SUPPORTED_PLATFORMS:
        print(json.dumps({
            "success": False,
            "error": f"Platform '{platform}' is not supported.",
            "supported_platforms": SUPPORTED_PLATFORMS
        }, indent=2))
        sys.exit(1)

    now_iso = datetime.now(timezone.utc).isoformat()
    cmd = [platform]

    if action == "login":
        cmd.extend(["login", "--account", account])
    elif action in ("check", "check_status"):
        cmd.extend(["check", "--account", account])
    elif action in ("upload", "upload_video"):
        if not file_path or not title:
            print(json.dumps({
                "success": False,
                "error": "For 'upload_video', both 'file_path' and 'title' are required."
            }, indent=2))
            sys.exit(1)

        if not os.path.exists(file_path):
            print(json.dumps({
                "success": False,
                "error": f"Video file not found at path: {file_path}"
            }, indent=2))
            sys.exit(1)

        cmd.extend(["upload-video", "--account", account, "--file", os.path.abspath(file_path), "--title", title])

        if desc:
            cmd.extend(["--desc", desc])

        if tags:
            if isinstance(tags, list):
                tag_str = ",".join(str(t).strip().lstrip("#") for t in tags if t)
            else:
                tag_str = str(tags).strip()
            if tag_str:
                cmd.extend(["--tags", tag_str])

        if thumbnail and os.path.exists(thumbnail):
            cmd.extend(["--thumbnail", os.path.abspath(thumbnail)])

        if schedule:
            cmd.extend(["--schedule", schedule])

        if platform == "youtube" and visibility:
            cmd.extend(["--visibility", visibility])
    else:
        print(json.dumps({
            "success": False,
            "error": f"Unsupported action: '{action}'. Choose from 'upload_video', 'check_status', 'login'."
        }, indent=2))
        sys.exit(1)

    code, stdout, stderr = run_sau_command(cmd)

    response = {
        "success": (code == 0),
        "platform": platform,
        "action": action,
        "account": account,
        "exit_code": code,
        "stdout": stdout.strip(),
        "stderr": stderr.strip(),
        "timestamp": now_iso
    }

    if code == 0:
        response["message"] = f"Operation '{action}' on '{platform}' completed successfully."
    else:
        response["message"] = f"Operation '{action}' on '{platform}' returned non-zero code {code}."

    print(json.dumps(response, indent=2))
    sys.exit(0 if code == 0 else 1)

if __name__ == "__main__":
    main()
