#!/usr/bin/env python3
"""
⚡ FLOWORK OS — ACTIVE TRIGGER: KERNEL TELEMETRY SENTINEL
Pure Python/Sysfs Monitor | Zero Destructive Actions | Read-Only Ring-0 Audit
Polls /proc/vmstat, dmesg, and sysd netlink status for kernel-level anomalies.
"""

import os
import sys
import time
import json
import subprocess
import urllib.request

SIGNAL_FILE = "/tmp/flowork_active_trigger.json"
STATE_FILE = "/tmp/flowork_kernel_telemetry_state.json"
SYSD_KERNEL_URL = "http://127.0.0.1:18090/api/kernel/status"

def read_vmstat_metrics():
    metrics = {"oom_kill": 0, "pgmajfault": 0}
    try:
        with open("/proc/vmstat", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    if parts[0] in metrics:
                        metrics[parts[0]] = int(parts[1])
    except Exception:
        pass
    return metrics

def check_sysd_netlink():
    try:
        req = urllib.request.Request(SYSD_KERNEL_URL, headers={"User-Agent": "FloworkKernelSentinel/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode())
    except Exception:
        pass
    return None

def check_recent_dmesg_errors():
    try:
        out = subprocess.check_output(
            ["dmesg", "-T", "--level=emerg,alert,crit,err"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        lines = [l for l in out.splitlines() if l.strip()]
        return lines[-5:] if lines else []
    except Exception:
        return []

def evaluate_kernel_health(emit_alert=True):
    vmstat = read_vmstat_metrics()
    sysd_netlink = check_sysd_netlink()
    dmesg_errs = check_recent_dmesg_errors()

    prev_state = {"oom_kill": 0, "pgmajfault": 0}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                prev_state = json.load(f)
        except Exception:
            pass

    oom_delta = vmstat["oom_kill"] - prev_state.get("oom_kill", 0)
    fault_delta = vmstat["pgmajfault"] - prev_state.get("pgmajfault", 0)

    # Save state
    with open(STATE_FILE, "w") as f:
        json.dump(vmstat, f)

    anomaly_detected = False
    anomaly_reason = ""

    if oom_delta > 0:
        anomaly_detected = True
        anomaly_reason = f"Kernel OOM event detected ({oom_delta} processes killed)."
    elif fault_delta > 50000:
        anomaly_detected = True
        anomaly_reason = f"Abnormal major page fault surge ({fault_delta} faults in interval)."

    status_payload = {
        "timestamp": int(time.time()),
        "kernel_healthy": not anomaly_detected,
        "oom_kills_total": vmstat["oom_kill"],
        "oom_kills_delta": oom_delta,
        "major_faults_total": vmstat["pgmajfault"],
        "major_faults_delta": fault_delta,
        "sysd_netlink": sysd_netlink,
        "recent_dmesg_errs_count": len(dmesg_errs)
    }

    if anomaly_detected and emit_alert:
        alert_payload = {
            "active": True,
            "source": "kernel_telemetry",
            "timestamp": int(time.time()),
            "telemetry": status_payload,
            "instruction": f"Kernel Sentinel Alert: {anomaly_reason} Investigate root cause without modifying sysctl or killing PIDs."
        }
        with open(SIGNAL_FILE, "w") as f:
            json.dump(alert_payload, f, indent=2)
        print(f"[ACTIVE_TRIGGER:kernel_telemetry] Alert dispatched: {anomaly_reason}")

    return status_payload

if __name__ == "__main__":
    if "--check" in sys.argv:
        res = evaluate_kernel_health(emit_alert=False)
        print(json.dumps(res, indent=2))
        sys.exit(0)
    
    # Continuous daemon execution
    print("🏛️ [FLOWORK OS] Kernel Telemetry Sentinel daemon started.")
    while True:
        try:
            evaluate_kernel_health(emit_alert=True)
        except Exception as e:
            print(f"[ERR] Kernel telemetry iteration error: {e}")
        time.sleep(10)
