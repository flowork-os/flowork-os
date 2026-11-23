#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Interactive Desktop Surface Daemon
# Pins the live Flowork Canvas directly into the Linux Desktop background layer
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================

import sys
import os
import time
import subprocess
import signal

PID_FILE = "/tmp/flowork_desktop_canvas.pid"
APP_TITLE = "Flowork OS — Swarmflow War Room"
PROFILE_DIR = os.path.expanduser("~/.flowork_desktop_canvas_profile")
CANVAS_URL = "http://127.0.0.1:19890/canvas/member-area/index.html"

def get_screen_geometry():
    """Detect primary monitor resolution and subtract 44px for bottom taskbar."""
    width, height = 2560, 1036
    try:
        out = subprocess.check_output(["xrandr", "--current"]).decode()
        for line in out.splitlines():
            if " connected" in line and ("primary" in line or "+" in line):
                parts = line.split()
                for p in parts:
                    if "x" in p and "+" in p:
                        res = p.split("+")[0]
                        w, h = map(int, res.split("x"))
                        return w, max(h - 44, 600)
    except Exception:
        pass
    return width, height

def get_canvas_window_id():
    """Find the X11 window ID matching the Canvas title."""
    try:
        out = subprocess.check_output(["wmctrl", "-l"]).decode()
        for line in out.splitlines():
            if APP_TITLE in line:
                return line.split()[0]
    except Exception:
        pass
    return None

def is_running():
    win = get_canvas_window_id()
    if win:
        return True, win
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True, None
        except Exception:
            try:
                os.remove(PID_FILE)
            except Exception:
                pass
    return False, None

def stop():
    print("==========================================================")
    print("🛑 STOPPING FLOWORK DESKTOP SURFACE")
    print("==========================================================")
    win = get_canvas_window_id()
    if win:
        try:
            subprocess.run(["wmctrl", "-i", "-c", win], check=False)
        except Exception:
            pass

    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        try:
            os.remove(PID_FILE)
        except Exception:
            pass

    # Ensure any lingering chrome instance with our custom profile is cleaned
    subprocess.run(["pkill", "-f", "flowork_desktop_canvas_profile"], check=False)
    import glob
    for p in glob.glob(os.path.join(PROFILE_DIR, "Default", "Network*")):
        try:
            os.remove(p)
        except Exception:
            pass
    print("✅ Flowork Desktop Canvas stopped cleanly.")

def start():
    running, win = is_running()
    if running and win:
        print(f"🟢 Flowork Desktop Canvas is already active (Window ID: {win})")
        return

    print("==========================================================")
    print("🖥️  STARTING FLOWORK OS INTERACTIVE DESKTOP SURFACE")
    print(f"🌐 Canvas URL: {CANVAS_URL}")
    print("==========================================================")

    # 1. Ensure Flowork Core supervisor is running
    try:
        subprocess.run(["curl", "-s", "--max-time", "1", "http://127.0.0.1:19890/"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("⚠️ Flowork Engine not responding on 19890. Starting engine stack...")
        engine_script = os.path.expanduser("~/flowork/run.sh")
        if os.path.exists(engine_script):
            subprocess.Popen(["bash", engine_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)

    width, height = get_screen_geometry()
    print(f"📏 Target Geometry: {width}x{height} (Bottom Taskbar preserved: 40px)")

    # 2. Spawn Chrome detached with independent process group
    chrome_bin = "/usr/bin/google-chrome"
    for b in ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"]:
        if os.path.exists(b):
            chrome_bin = b
            break

    os.makedirs(os.path.join(PROFILE_DIR, "Default"), exist_ok=True)
    import glob
    for p in glob.glob(os.path.join(PROFILE_DIR, "Default", "Network*")):
        try:
            os.remove(p)
        except Exception:
            pass
    try:
        os.symlink("/dev/null", os.path.join(PROFILE_DIR, "Default", "Network Persistent State"))
    except Exception:
        pass

    cmd = [
        chrome_bin,
        "--ozone-platform=x11",
        f"--user-data-dir={PROFILE_DIR}",
        f"--app={CANVAS_URL}",
        f"--window-position=0,0",
        f"--window-size={width},{height}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=TranslateUI,BlockInsecurePrivateNetworkRequests,LocalNetworkAccessChecks,PrivateNetworkAccessSendPreflights",
        "--disable-session-crashed-bubble",
        "--disable-infobars",
        "--test-type",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-web-security",
        "--allow-running-insecure-content",
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        "--enable-logging=stderr"
    ]

    log_file = open("/tmp/flowork_desktop_canvas.log", "a")
    proc = subprocess.Popen(
        cmd,
        preexec_fn=os.setpgrp,
        stdout=log_file,
        stderr=log_file
    )

    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    print(f"🚀 Canvas process launched (PID: {proc.pid}). Waiting for X11 Window registration...")

    # 3. Wait for window ID
    captured_win = None
    for _ in range(30):
        time.sleep(0.2)
        captured_win = get_canvas_window_id()
        if captured_win:
            break

    if not captured_win:
        print("⚠️ Window ID not captured within timeout, checking background PID...")
        return

    print(f"🎯 Window Captured: {captured_win}")

    # 4. Remove borders and titlebar (_MOTIF_WM_HINTS)
    subprocess.run([
        "xprop", "-id", captured_win,
        "-f", "_MOTIF_WM_HINTS", "32c",
        "-set", "_MOTIF_WM_HINTS", "0x2, 0x0, 0x0, 0x0, 0x0"
    ], check=False)

    # 5. Strictly enforce DESKTOP window type so Docks/Taskbar and Sidebars are ALWAYS layered on top
    subprocess.run([
        "xprop", "-id", captured_win,
        "-f", "_NET_WM_WINDOW_TYPE", "32a",
        "-set", "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_DESKTOP"
    ], check=False)

    # 6. Ensure fullscreen flag is NEVER applied to prevent covering the taskbar
    subprocess.run(["wmctrl", "-i", "-r", captured_win, "-b", "remove,fullscreen"], check=False)

    # 7. Set EWMH properties: below all apps, sticky across workspaces, skip taskbar, skip alt-tab
    subprocess.run(["wmctrl", "-i", "-r", captured_win, "-b", "add,below,sticky"], check=False)
    subprocess.run(["wmctrl", "-i", "-r", captured_win, "-b", "add,skip_taskbar,skip_pager"], check=False)

    # 8. Fit precisely across workspace above the 40px bottom taskbar slot
    subprocess.run(["wmctrl", "-i", "-r", captured_win, "-e", f"0,0,0,{width},{height}"], check=False)

    print("==========================================================")
    print("✨ SUCCESS: Flowork Canvas is LIVE as the Desktop Workspace!")
    print(f"🖥️  Resolution: {width}x{height}")
    print("🔘 Bottom Taskbar & Start Menu fully functional on top.")
    print("==========================================================")

def status():
    running, win = is_running()
    if running:
        print(f"🟢 Flowork Desktop Canvas is ACTIVE (Window ID: {win or 'Attached'})")
    else:
        print("⚪ Flowork Desktop Canvas is NOT running.")

def toggle():
    running, win = is_running()
    if running:
        stop()
    else:
        start()

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "toggle"
    if arg in ["start", "--start"]:
        start()
    elif arg in ["stop", "--stop"]:
        stop()
    elif arg in ["toggle", "--toggle"]:
        toggle()
    elif arg in ["status", "--status"]:
        status()
    elif arg in ["restart", "--restart"]:
        stop()
        time.sleep(1)
        start()
    else:
        print(f"Usage: {sys.argv[0]} [start|stop|toggle|restart|status]")

if __name__ == "__main__":
    main()
