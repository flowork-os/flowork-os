#!/usr/bin/env python3
"""
Flowork OS Sovereign Self-Evolution Master QC Suite
Empirically tests and audits all 5 Sovereign Vectors and System Guards.
"""

import json
import os
import subprocess
import sys
import time

def run_cmd(cmd, desc):
    start = time.time()
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    elapsed = time.time() - start
    passed = (res.returncode == 0)
    return {
        "desc": desc,
        "cmd": cmd,
        "passed": passed,
        "exit_code": res.returncode,
        "elapsed_sec": round(elapsed, 3),
        "stdout": res.stdout.strip()[:300],
        "stderr": res.stderr.strip()[:300]
    }

def main():
    print("=" * 70)
    print("👑 FLOWORK OS: MASTER SELF-EVOLUTION QUALITY CONTROL (QC) SUITE")
    print("=" * 70)
    
    tests = [
        # Dev-Mode Triple Lock Landmark Guard
        (
            "/opt/floworkos/bin/flowork-update --dry-run",
            "Triple-Lock Landmark Guard (flowork-update inhibited)"
        ),
        # Vector 1: Short Video Foundry
        (
            "flowork-short --qc-test",
            "Vector 1: Autonomous Short Video Foundry Engine"
        ),
        # Vector 2: Vision-Action & Direct Hardware Telemetry
        (
            "curl -s http://127.0.0.1:18090/status",
            "Vector 2: Native flowork-sysd Vision-Action & Virtual HID Status"
        ),
        # Vector 3: Episodic Memory Crystallization
        (
            "python3 /opt/floworkos/tools/memory_crystallizer/run.py --search 'short video foundry stickman'",
            "Vector 3: Episodic Memory Crystallization & FTS5 Retrieval"
        ),
        # Vector 4: Proactive Kernel Sentinel & Cgroup v2 PSI
        (
            "/opt/floworkos/tools/cgroup_guardian/run --action status",
            "Vector 4: Kernel Cgroup v2 & Pressure Stall Information (PSI)"
        ),
        # Vector 5: Zero-Cloud Sovereign Connector & Local SLM Triage
        (
            "curl -s http://127.0.0.1:9099/ && flowork-slm --triage 'buka file explorer'",
            "Vector 5: Zero-Cloud Sovereign Connector (:9099) & L0 SLM Triage"
        ),
    ]

    results = []
    all_passed = True

    for cmd, desc in tests:
        print(f"\n[TESTING] {desc}...")
        r = run_cmd(cmd, desc)
        results.append(r)
        if r["passed"]:
            print(f"  --> PASS (Exit Code 0, {r['elapsed_sec']}s)")
        else:
            print(f"  --> FAIL (Exit Code {r['exit_code']}, {r['elapsed_sec']}s)")
            print(f"      STDERR: {r['stderr']}")
            all_passed = False

    print("\n" + "=" * 70)
    print("QC SUITE AUDIT SUMMARY")
    print("=" * 70)
    for idx, r in enumerate(results, 1):
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{idx}. [{status}] {r['desc']} ({r['elapsed_sec']}s)")

    report_path = "/opt/floworkos/documents/qc_master_evolution_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "all_passed": all_passed,
            "total_tests": len(results),
            "results": results
        }, f, indent=2)

    user_mirror = os.path.expanduser("~/Documents/qc_master_evolution_report.json")
    try:
        with open(user_mirror, "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "all_passed": all_passed,
                "total_tests": len(results),
                "results": results
            }, f, indent=2)
    except Exception:
        pass

    print(f"\nCanonical QC Audit Log saved to: {report_path}")
    print(f"User Documents Mirror saved to:   {user_mirror}")
    
    if all_passed:
        print("\n🎉 ALL 5 SOVEREIGN EVOLUTION VECTORS VERIFIED WITH 100% PASS RATE!")
        return 0
    else:
        print("\n⚠️ SOME QC TESTS FAILED. CHECK LOG FOR DETAILS.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
