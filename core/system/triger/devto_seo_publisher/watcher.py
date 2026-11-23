#!/usr/bin/env python3
"""
Flowork OS — Active Trigger Watchdog: Dev.to SEO Article Publisher
Monitors $HOME/Downloads/devto.txt and schedules daily autonomous SEO publications
between 21:00 (9 PM) and 02:00 (2 AM) at a randomized time, promoting floworkos.com
and https://github.com/flowork-os/flowork-os with zero manual intervention.
"""

import os
import sys
import time
import json
import signal
import random
import datetime
import subprocess
from pathlib import Path

TRIGGER_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(TRIGGER_DIR, "trigger.json")
PID_FILE = os.path.join(TRIGGER_DIR, ".pid")
STATE_FILE = os.path.join(TRIGGER_DIR, ".state.json")
PUBLISHER_CLI = "/opt/floworkos/bin/flowork-devto-publisher"

RUNNING = True

def handle_signal(sig, frame):
    global RUNNING
    RUNNING = False

def resolve_user_home():
    """Dynamically resolves user home directory without hardcoding."""
    home = os.environ.get("HOME")
    if not home or not os.path.exists(home):
        home = str(Path.home())
    return home

def is_devto_present():
    """Checks whether devto.txt or devto exists in user's Downloads directory."""
    home = resolve_user_home()
    downloads_dir = os.path.join(home, "Downloads")
    candidates = [
        os.path.join(downloads_dir, "devto.txt"),
        os.path.join(downloads_dir, "devto")
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.getsize(c) > 0:
            return True, c
    return False, None

def get_current_cycle_info(now=None):
    """
    Computes current night cycle (21:00 to 02:00 next day).
    Subtracting 3 hours maps 21:00 - 01:59:59 to the exact same calendar cycle date!
    """
    if now is None:
        now = datetime.datetime.now()
        
    hour = now.hour
    is_in_window = (hour >= 21 or hour < 2)
    
    # Virtual cycle date
    cycle_date = (now - datetime.timedelta(hours=3)).date()
    cycle_id = cycle_date.strftime("%Y-%m-%d")
    
    # Calculate cycle start (21:00 of cycle_date)
    cycle_start = datetime.datetime.combine(cycle_date, datetime.time(21, 0, 0))
    # Cycle duration = 5 hours = 300 minutes
    cycle_end = cycle_start + datetime.timedelta(hours=5)
    
    return is_in_window, cycle_id, cycle_start, cycle_end

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state):
    try:
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        print(f"[WATCHER WARN] Failed to save state: {e}", file=sys.stderr)

def execute_publisher():
    """Executes flowork-devto-publisher."""
    if not os.path.exists(PUBLISHER_CLI):
        print(f"[WATCHER ERROR] Publisher CLI not found at: {PUBLISHER_CLI}", file=sys.stderr)
        return False
        
    try:
        print(f"[WATCHER INFO] Executing {PUBLISHER_CLI}...", flush=True)
        res = subprocess.run([PUBLISHER_CLI], capture_output=True, text=True, timeout=120)
        print(res.stdout, flush=True)
        if res.returncode == 0:
            return True
        else:
            print(f"[WATCHER ERROR] Publisher exited with code {res.returncode}: {res.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"[WATCHER ERROR] Failed to run publisher: {e}", file=sys.stderr)
        return False

def main():
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Write PID
    try:
        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

    # Support manual forced run via CLI
    if "--now" in sys.argv or "--force" in sys.argv:
        print("[WATCHER] Immediate execution triggered by CLI flag.")
        execute_publisher()
        sys.exit(0)

    print(f"[WATCHER STARTED] Dev.to SEO Publisher active watchdog running (PID: {os.getpid()})", flush=True)

    interval = 60
    while RUNNING:
        try:
            devto_found, devto_path = is_devto_present()
            if not devto_found:
                # Stay dormant when devto.txt is absent
                time.sleep(interval)
                continue

            now = datetime.datetime.now()
            is_in_window, cycle_id, cycle_start, cycle_end = get_current_cycle_info(now)
            state = load_state()

            # Schedule target if inside or approaching window
            if state.get("current_cycle") != cycle_id:
                # Pick a random minute between 0 and 299 (5 hours from 21:00)
                random_minute_offset = random.randint(0, 299)
                target_dt = cycle_start + datetime.timedelta(minutes=random_minute_offset)
                state["current_cycle"] = cycle_id
                state["target_epoch"] = int(target_dt.timestamp())
                state["target_human"] = target_dt.strftime("%Y-%m-%d %H:%M:%S")
                save_state(state)
                print(f"[WATCHER SCHEDULE] Cycle {cycle_id}: Scheduled publication at {state['target_human']}", flush=True)

            if is_in_window:
                target_epoch = state.get("target_epoch", 0)
                last_executed_cycle = state.get("last_executed_cycle", "")

                # Check if time reached and hasn't executed for this cycle
                if now.timestamp() >= target_epoch and last_executed_cycle != cycle_id:
                    print(f"[WATCHER TRIGGER] Night window active & target time reached. Initiating publication for cycle {cycle_id}...", flush=True)
                    success = execute_publisher()
                    if success:
                        state["last_executed_cycle"] = cycle_id
                        state["last_executed_time"] = now.strftime("%Y-%m-%d %H:%M:%S")
                        save_state(state)
                        print(f"[WATCHER SUCCESS] Publication completed for cycle {cycle_id}.", flush=True)

        except Exception as e:
            print(f"[WATCHER EXCEPTION] Error in loop: {e}", file=sys.stderr)

        time.sleep(interval)

    # Clean PID on exit
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass
    print("[WATCHER STOPPED] Clean exit.", flush=True)

if __name__ == "__main__":
    main()
