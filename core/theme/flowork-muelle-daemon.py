#!/usr/bin/env python3
# ==============================================================================
# ⚡ Flowork Sovereign OS — Muelle Launch FX & Optical Glass Shimmer Daemon
# Listens for application launch events and window materializations:
# 1. Optical crystal ripples & emerald shockwaves on launch clicks.
# 2. Specular rim sweep & emerald lens bloom on newly materialized windows.
# Auto-reaping, zero zombie processes, 100% click-through.
# ==============================================================================

import sys
import os
import time
import subprocess
import signal
import threading
from Xlib import X, display, error
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gi
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib

# Automatically reap child processes so they never become zombies
try:
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
except Exception:
    pass

LAUNCH_FX_BIN = "/opt/floworkos/theme/muelle_launch_fx.py"

LAST_LAUNCH_TRIGGER = 0
DEBOUNCE_SEC = 0.35

def trigger_launch_effect(view_path=None, view_type=None):
    global LAST_LAUNCH_TRIGGER
    now = time.time()
    if now - LAST_LAUNCH_TRIGGER < DEBOUNCE_SEC:
        return
    LAST_LAUNCH_TRIGGER = now

    try:
        display_gdk = Gdk.Display.get_default()
        seat = display_gdk.get_default_seat() if display_gdk else None
        pointer = seat.get_pointer() if seat else None
        if pointer:
            _, px, py = pointer.get_position()
        else:
            px, py = 960, 1000

        if os.path.exists(LAUNCH_FX_BIN):
            subprocess.Popen(
                [LAUNCH_FX_BIN, str(px), str(py)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
    except Exception:
        pass

def trigger_window_shimmer(x, y, w, h):
    # Retired: Picom native GLX quantum spring-zoom provides a single, unified 60 FPS animation
    pass

def x11_window_shimmer_watcher():
    """No-op stub: retired to avoid duplicate overlay window spawning."""
    pass

def main():
    # Shimmer watcher retired to ensure single-pass buttery-smooth window zoom without duplicate frames
    DBusGMainLoop(set_as_default=True)
    try:
        bus = dbus.SessionBus()
        bus.add_signal_receiver(
            trigger_launch_effect,
            signal_name="ViewOpened",
            dbus_interface="org.ayatana.bamf.matcher"
        )
    except Exception as e:
        print(f"BAMF connection warning: {e}", file=sys.stderr)

    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
