#!/usr/bin/env python3
# [FL_INDEX: keywords="watcher_daemon, runaway_process, resource_telemetry, psutil_monitor, edge_trigger" | purpose="Active standalone watchdog monitoring runaway tool PIDs and anomalous resource loads"]
import os
import sys
import time
import json
import subprocess

TRIGGER_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(TRIGGER_DIR, "trigger.json")
PID_FILE = os.path.join(TRIGGER_DIR, ".pid")
STATE_FILE = os.path.join(TRIGGER_DIR, ".last_alert")

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
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

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
                is_target = any(k in args.lower() for k in ["flowork", "scratch/helpers", "python", "node", "ffmpeg", "yt_"])
                if not is_target:
                    continue

                if cpu >= cpu_limit or rss_mb >= mem_limit_mb:
                    anomalies.append({
                        "pid": pid,
                        "comm": comm,
                        "cpu": cpu,
                        "rss_mb": round(rss_mb, 1),
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
    with open(STATE_FILE, "w") as f:
        f.write(str(time.time()))

def main():
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
            # Edge-triggered signal: alert payload logged to stderr/stdout for Flowork Active Watchdog Runtime
            print(f"[TRIGGER:process_watchdog] Anomalies detected: {len(anomalies)} runaway process(es)", flush=True)

        time.sleep(interval)

if __name__ == "__main__":
    main()
