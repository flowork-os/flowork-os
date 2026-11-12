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
import signal
import tempfile
import subprocess
import urllib.request

TRIGGER_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNAL_FILE = "/tmp/flowork_active_trigger.json"
STATE_FILE = os.path.join(TRIGGER_DIR, ".state.json")
PID_FILE = os.path.join(TRIGGER_DIR, ".pid")
SYSD_KERNEL_URL = "http://127.0.0.1:18090/api/kernel/status"


def _atomic_write_json(path, payload):
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_ktele_", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _atomic_write_text(path, content):
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_ktele_", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _cleanup_pid(*_args):
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except OSError:
        pass
    sys.exit(0)


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
    for cmd in (
        ["dmesg", "-T", "--level=emerg,alert,crit,err"],
        ["journalctl", "-k", "-p", "err", "-n", "10", "--no-pager"],
    ):
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode(errors="ignore").strip()
            lines = [l for l in out.splitlines() if l.strip()]
            if lines:
                return lines[-5:]
            return []
        except Exception:
            continue
    return []


def evaluate_kernel_health(emit_alert=True):
    vmstat = read_vmstat_metrics()
    sysd_netlink = check_sysd_netlink()
    dmesg_errs = check_recent_dmesg_errors()

    prev_state = None
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                prev_state = loaded
        except Exception:
            prev_state = None

    # Save current counters atomically
    _atomic_write_json(STATE_FILE, vmstat)

    # First-run baseline: avoid false alert from boot-cumulative counters
    if prev_state is None:
        oom_delta = 0
        fault_delta = 0
    else:
        oom_delta = max(0, vmstat["oom_kill"] - int(prev_state.get("oom_kill", vmstat["oom_kill"])))
        fault_delta = max(0, vmstat["pgmajfault"] - int(prev_state.get("pgmajfault", vmstat["pgmajfault"])))

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
        _atomic_write_json(SIGNAL_FILE, alert_payload)
        print(f"[ACTIVE_TRIGGER:kernel_telemetry] Alert dispatched: {anomaly_reason}", flush=True)

    return status_payload


if __name__ == "__main__":
    if "--check" in sys.argv:
        res = evaluate_kernel_health(emit_alert=False)
        print(json.dumps(res, indent=2))
        sys.exit(0)

    signal.signal(signal.SIGTERM, _cleanup_pid)
    signal.signal(signal.SIGINT, _cleanup_pid)
    _atomic_write_text(PID_FILE, f"{os.getpid()}\n")

    # Continuous daemon execution
    print("🏛️ [FLOWORK OS] Kernel Telemetry Sentinel daemon started.", flush=True)
    while True:
        try:
            evaluate_kernel_health(emit_alert=True)
        except Exception as e:
            print(f"[ERR] Kernel telemetry iteration error: {e}", flush=True)
        time.sleep(10)
