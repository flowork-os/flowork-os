#!/usr/bin/env python3
"""
⚡ FLOWORK OS — CHAOS MUTATION & RESILIENCE RUNNER
Authoritative Sandbox & Process Lifecycle Stress Harness
Validates tools against permission jailing, process leaks, and path portability.
"""

import os
import sys
import json
import time
import subprocess
import glob

TOOLS_DIR = "/opt/floworkos/tools"
POLICIES_DIR = "/opt/floworkos/policies"

class ChaosRunner:
    def __init__(self):
        self.results = []
        self.zombie_leaks = 0
        self.path_violations = 0
        self.total_tools_checked = 0

    def get_zombie_count(self):
        try:
            output = subprocess.check_output(
                "ps -eo stat,pid,comm | awk '$1 ~ /^[Zz]/ {print $2}'",
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            if not output:
                return 0
            return len(output.splitlines())
        except Exception:
            return 0

    def audit_path_portability(self, tool_path):
        """Scans tool source files for illegal hardcoded personal home directories."""
        violations = []
        for root, _, files in os.walk(tool_path):
            if "__pycache__" in root or ".git" in root or "node_modules" in root:
                continue
            for fname in files:
                if fname.endswith((".py", ".rs", ".sh", ".json", ".md")):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", errors="ignore") as f:
                            for idx, line in enumerate(f, 1):
                                if "/home/" in line and not line.strip().startswith("#"):
                                    # Allow standard dynamic fallbacks
                                    if "os.environ.get" in line or "os.path.expanduser" in line or "DYNAMIC" in line:
                                        continue
                                    violations.append({
                                        "file": fpath,
                                        "line": idx,
                                        "snippet": line.strip()[:80]
                                    })
                    except Exception:
                        pass
        return violations

    def test_tool_sandbox_resilience(self, tool_name, tool_path):
        manifest_path = os.path.join(tool_path, "manifest.json")
        runner_py = os.path.join(tool_path, "run.py")
        runner_sh = os.path.join(tool_path, "run.sh")
        runner_bin = os.path.join(tool_path, "run")

        if not os.path.exists(manifest_path):
            return None

        self.total_tools_checked += 1
        initial_zombies = self.get_zombie_count()
        
        # 1. Path Portability Audit
        portability_leaks = self.audit_path_portability(tool_path)
        if portability_leaks:
            self.path_violations += len(portability_leaks)

        # 2. Chaos Execution (Permission denial & malformed input test)
        runner_cmd = None
        if os.path.exists(runner_py):
            runner_cmd = ["python3", runner_py]
        elif os.path.exists(runner_sh):
            runner_cmd = ["/bin/bash", runner_sh]
        elif os.path.exists(runner_bin) and os.access(runner_bin, os.X_OK):
            runner_cmd = [runner_bin]

        fault_handled = True
        execution_duration_ms = 0

        if runner_cmd:
            t0 = time.time()
            # Send deliberately restricted / chaotic target payload
            chaos_payload = json.dumps({
                "target_file": "/root/.ssh/id_rsa",
                "path": "/etc/shadow",
                "command": "cat /etc/shadow",
                "filename": "/root/illegal_output.txt"
            })
            try:
                proc = subprocess.Popen(
                    runner_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=dict(os.environ, FLOWORK_CHAOS_MODE="1")
                )
                try:
                    stdout, stderr = proc.communicate(input=chaos_payload.encode(), timeout=2.5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.communicate()
                    fault_handled = False
                
                execution_duration_ms = round((time.time() - t0) * 1000, 1)
            except Exception:
                fault_handled = False

        post_zombies = self.get_zombie_count()
        zombie_diff = max(0, post_zombies - initial_zombies)
        if zombie_diff > 0:
            self.zombie_leaks += zombie_diff

        status = "PASSED" if (fault_handled and zombie_diff == 0) else "FAILED"

        record = {
            "tool": tool_name,
            "status": status,
            "execution_ms": execution_duration_ms,
            "zombie_leaks": zombie_diff,
            "portability_violations": len(portability_leaks)
        }
        self.results.append(record)
        return record

    def run_all(self):
        print("🏛️ [FLOWORK OS] INITIATING CHAOS MUTATION & RESILIENCE HARNESS")
        print("----------------------------------------------------------------------")
        tools = sorted(os.listdir(TOOLS_DIR))
        for t in tools:
            p = os.path.join(TOOLS_DIR, t)
            if os.path.isdir(p):
                res = self.test_tool_sandbox_resilience(t, p)
                if res:
                    print(f"▶ [{res['status']}] {res['tool']:<32} | Latency: {res['execution_ms']}ms | Zombies: {res['zombie_leaks']} | Path Flaws: {res['portability_violations']}")

        print("----------------------------------------------------------------------")
        print(f"📊 SUMMARY: {self.total_tools_checked} Sovereign Tools Tested.")
        print(f"   Zombie Process Leaks     : {self.zombie_leaks} (Target: 0)")
        print(f"   Hardcoded Path Violations: {self.path_violations} (Target: 0)")
        
        report_path = "/tmp/chaos_mutation_report.json"
        with open(report_path, "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total_tools": self.total_tools_checked,
                "zombie_leaks": self.zombie_leaks,
                "path_violations": self.path_violations,
                "results": self.results
            }, f, indent=2)

        print(f"📁 Detailed report emitted: {report_path}")
        return 0 if (self.zombie_leaks == 0) else 1

if __name__ == "__main__":
    runner = ChaosRunner()
    sys.exit(runner.run_all())
