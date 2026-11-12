#!/usr/bin/env python3
# [FL_INDEX: keywords="watcher_daemon, runaway_process, resource_telemetry, psutil_monitor, edge_trigger" | purpose="Active standalone watchdog monitoring runaway tool PIDs and anomalous resource loads"]
import os
import sys
import time
import json
import signal
import tempfile
import subprocess

TRIGGER_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(TRIGGER_DIR, "trigger.json")
PID_FILE = os.path.join(TRIGGER_DIR, ".pid")
STATE_FILE = os.path.join(TRIGGER_DIR, ".last_alert")
SIGNAL_FILE = "/tmp/flowork_active_trigger.json"

def parse_etime_seconds(etime_str):
    try:
        etime_str = etime_str.strip()
        days = 0
        if '-' in etime_str:
            days_str, etime_str = etime_str.split('-', 1)
            days = int(days_str)
        parts = [int(p) for p in etime_str.split(':')]
        if len(parts) == 3:
            h, m, s = parts
        elif len(parts) == 2:
            h = 0
            m, s = parts
        elif len(parts) == 1:
            h = 0
            m = 0
            s = parts[0]
        else:
            return 0
        return days * 86400 + h * 3600 + m * 60 + s
    except Exception:
        return 0

def _atomic_write_text(path, content):
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_procwd_", dir=parent)
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

def get_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "interval_seconds": 10,
        "cooldown_seconds": 180,
        "thresholds": {"cpu_percent": 80.0, "memory_mb": 1500, "runtime_seconds": 120}
    }

def record_pid():
    _atomic_write_text(PID_FILE, f"{os.getpid()}\n")

def check_heavy_processes(cpu_limit, mem_limit_mb, runtime_limit_sec):
    anomalies = []
    try:
        # Using standard Linux ps to avoid external unpinned dependencies
        cmd = ["ps", "-eo", "pid,ppid,%cpu,rss,etime,comm,args"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = res.stdout.strip().split("\n")[1:]
        
        my_pid = os.getpid()
        for line in lines:
            parts = line.strip().split(None, 6)
            if len(parts) < 7:
                continue
            pid_str, ppid_str, cpu_str, rss_kb_str, etime_str, comm, args = parts
            try:
                pid = int(pid_str)
                if pid == my_pid:
                    continue
                cpu = float(cpu_str)
                rss_mb = float(rss_kb_str) / 1024.0
                
                # Filter strictly for flowork workspace tools or runaway worker tasks
                is_target = any(k in args.lower() for k in ["flowork", "scratch/helpers", "python", "rust", "ffmpeg", "yt_"])
                if not is_target:
                    continue

                runtime_sec = parse_etime_seconds(etime_str)
                is_cpu_runaway = (cpu >= cpu_limit and runtime_sec >= runtime_limit_sec)
                is_mem_leak = (rss_mb >= mem_limit_mb)

                if is_cpu_runaway or is_mem_leak:
                    anomalies.append({
                        "pid": pid,
                        "comm": comm,
                        "cpu": cpu,
                        "rss_mb": round(rss_mb, 1),
                        "runtime_seconds": runtime_sec,
                        "etime": etime_str,
                        "args": args[:120]
                    })
            except (ValueError, IndexError):
                continue
    except Exception:
        pass
    return anomalies

def can_trigger(cooldown_sec):
    if not os.path.exists(STATE_FILE):
        return True
    try:
        with open(STATE_FILE, "r") as f:
            last_ts = float(f.read().strip())
        return (time.time() - last_ts) >= cooldown_sec
    except Exception:
        return True

def mark_triggered():
    _atomic_write_text(STATE_FILE, f"{time.time()}\n")

def main():
    signal.signal(signal.SIGTERM, _cleanup_pid)
    signal.signal(signal.SIGINT, _cleanup_pid)
    record_pid()
    while True:
        cfg = get_config()
        interval = cfg.get("interval_seconds", 10)
        cooldown = cfg.get("cooldown_seconds", 180)
        thresholds = cfg.get("thresholds", {})
        cpu_lim = thresholds.get("cpu_percent", 80.0)
        mem_lim = thresholds.get("memory_mb", 1500)
        run_lim = thresholds.get("runtime_seconds", 120)

        anomalies = check_heavy_processes(cpu_lim, mem_lim, run_lim)
        if anomalies and can_trigger(cooldown):
            mark_triggered()
            alert_payload = {
                "active": True,
                "source": "process_watchdog",
                "timestamp": int(time.time()),
                "telemetry": {
                    "anomalies_count": len(anomalies),
                    "anomalies": anomalies
                },
                "instruction": f"Process Watchdog Alert: {len(anomalies)} runaway process(es) detected. Review resource consumption."
            }
            try:
                _atomic_write_text(SIGNAL_FILE, json.dumps(alert_payload, indent=2) + "\n")
            except Exception as e:
                print(f"[ERR] Failed to write signal file: {e}", file=sys.stderr)
            print(f"[TRIGGER:process_watchdog] Anomalies detected: {len(anomalies)} runaway process(es)", flush=True)

        time.sleep(interval)

if __name__ == "__main__":
    main()
