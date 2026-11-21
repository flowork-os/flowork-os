#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Active Trigger Daemon Supervisor
# Autostart daemon managing all active background watchers
# =============================================================================
import os
import sys
import time
import json
import signal
import subprocess

TRIGGERS_DIR = "/opt/floworkos/system/triger"
CHILDREN = {}

def is_pid_alive(pid, expected_dir=None):
    try:
        if pid <= 0 or pid == os.getpid():
            return False
        os.kill(pid, 0)
        stat_path = f"/proc/{pid}/stat"
        if os.path.exists(stat_path):
            with open(stat_path, "r", encoding="utf-8", errors="ignore") as sf:
                stat_txt = sf.read()
            rparen = stat_txt.rfind(")")
            if rparen != -1:
                state_char = stat_txt[rparen + 2 : rparen + 3]
                if state_char in ("Z", "X"):
                    return False
        if expected_dir:
            cmd_path = f"/proc/{pid}/cmdline"
            if os.path.exists(cmd_path):
                with open(cmd_path, "rb") as cf:
                    cmdline = cf.read().replace(b"\x00", b" ").decode("utf-8", errors="ignore")
                if os.path.abspath(expected_dir) not in cmdline and os.path.basename(expected_dir) not in cmdline:
                    return False
        return True
    except OSError:
        return False

def clean_stale_pid(pid_file, expected_dir=None):
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            if not is_pid_alive(pid, expected_dir=expected_dir):
                os.remove(pid_file)
    except Exception:
        try:
            os.remove(pid_file)
        except Exception:
            pass

def spawn_watcher(trigger_id, t_dir):
    cfg_file = os.path.join(t_dir, "trigger.json")
    if not os.path.exists(cfg_file):
        return

    try:
        with open(cfg_file, 'r') as f:
            cfg = json.load(f)
        if not cfg.get("enabled", False):
            return
    except Exception:
        return

    if trigger_id in CHILDREN:
        tracked = CHILDREN[trigger_id]
        if tracked.poll() is None:
            return
        CHILDREN.pop(trigger_id, None)

    pid_file = os.path.join(t_dir, ".pid")
    clean_stale_pid(pid_file, expected_dir=t_dir)

    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            if is_pid_alive(pid, expected_dir=t_dir):
                return
        except Exception:
            pass

    # Determine watcher executable: watcher (ELF) -> watcher.sh -> watcher.py -> watcher.rs
    elf_bin = os.path.join(t_dir, "watcher")
    sh_bin = os.path.join(t_dir, "watcher.sh")
    py_bin = os.path.join(t_dir, "watcher.py")
    rs_src = os.path.join(t_dir, "watcher.rs")

    cmd = None
    if os.path.exists(elf_bin) and os.access(elf_bin, os.X_OK):
        cmd = [elf_bin]
    elif os.path.exists(sh_bin):
        os.chmod(sh_bin, 0o755)
        cmd = [sh_bin]
    elif os.path.exists(py_bin):
        os.chmod(py_bin, 0o755)
        cmd = [sys.executable, py_bin]
    elif os.path.exists(rs_src):
        # Auto-compile rust watcher
        compile_res = subprocess.run(["rustc", "-O", rs_src, "-o", elf_bin], capture_output=True)
        if compile_res.returncode == 0:
            cmd = [elf_bin]

    if not cmd:
        return

    try:
        proc = subprocess.Popen(cmd, cwd=t_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        CHILDREN[trigger_id] = proc
        with open(pid_file, 'w') as f:
            f.write(str(proc.pid))
        print(f"[SUPERVISOR] Spawned active trigger '{trigger_id}' (PID {proc.pid})", flush=True)
    except Exception as e:
        print(f"[SUPERVISOR] Failed to spawn '{trigger_id}': {e}", file=sys.stderr)

def scan_and_supervise():
    if not os.path.exists(TRIGGERS_DIR):
        return
    for item in os.listdir(TRIGGERS_DIR):
        item_path = os.path.join(TRIGGERS_DIR, item)
        if os.path.isdir(item_path) and item not in ["templates", "__pycache__"]:
            spawn_watcher(item, item_path)

def shutdown_handler(signum, frame):
    print("\n[SUPERVISOR] Shutting down active triggers...", flush=True)
    for tid, proc in list(CHILDREN.items()):
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        pid_file = os.path.join(TRIGGERS_DIR, tid, ".pid")
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except Exception:
            pass
    sys.exit(0)

def main():
    print("==================================================================", flush=True)
    print("  ⚡ Flowork OS Active Trigger Supervisor Daemon Started", flush=True)
    print(f"  Watching: {TRIGGERS_DIR}", flush=True)
    print("==================================================================", flush=True)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    while True:
        scan_and_supervise()
        time.sleep(15)

if __name__ == "__main__":
    main()
