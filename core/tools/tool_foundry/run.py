#!/usr/bin/env python3
"""
⚡ FLOWORK OS — TOOL FOUNDRY RUNNER (run.py)
Bridges tool invocations from Mr. Flow CLI / flowork-tool-executor to fl_tool_foundry.py.
"""

import sys
import os
import subprocess

FOUNDRY_ENGINE = "/opt/floworkos/tools/fl_tool_foundry.py"

def main():
    raw_input = sys.stdin.read()
    res = subprocess.run(
        [sys.executable, FOUNDRY_ENGINE],
        input=raw_input,
        capture_output=True,
        text=True
    )
    if res.stdout:
        sys.stdout.write(res.stdout)
    if res.stderr:
        sys.stderr.write(res.stderr)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
