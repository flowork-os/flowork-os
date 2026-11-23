#!/usr/bin/env python3
"""
Flowork OS Sovereign FFmpeg Suite Executor.
Supports both standard CLI arguments and stdin JSON payload from Flowork ToolRegistry.
"""
import sys
import json
import subprocess
from pathlib import Path

def main():
    launcher = Path("/opt/floworkos/bin/flowork-ffmpeg")
    cmd_args = []

    # Check if JSON payload passed via stdin (standard ToolRegistry execution)
    if not sys.stdin.isatty():
        try:
            stdin_content = sys.stdin.read().strip()
            if stdin_content:
                payload = json.loads(stdin_content)
                subcommand = payload.get("command")
                extra_args = payload.get("args", [])
                if subcommand:
                    cmd_args = [subcommand] + [str(a) for a in extra_args]
        except Exception:
            pass

    # If no stdin JSON payload, use sys.argv
    if not cmd_args:
        cmd_args = sys.argv[1:]

    if not cmd_args:
        cmd_args = ["--help"]

    if launcher.exists():
        res = subprocess.run([str(launcher)] + cmd_args)
        sys.exit(res.returncode)
    else:
        scripts_dir = Path("/opt/floworkos/skills/ffmpeg-skill/scripts")
        subcmd = cmd_args[0]
        target = scripts_dir / f"{subcmd}.py"
        if not target.exists():
            print(f"Unknown ffmpeg tool: {subcmd}", file=sys.stderr)
            sys.exit(1)
        res = subprocess.run([sys.executable, str(target)] + cmd_args[1:])
        sys.exit(res.returncode)

if __name__ == "__main__":
    main()
