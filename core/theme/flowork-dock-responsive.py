#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Responsive Dock Centering & Display Sync Daemon
# Ensures Plank dock remains perfectly centered, dynamically responsive, and
# symmetrically aligned across all monitor resolutions, aspect ratios, and
# companion sidebar geometry changes.
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================

import os
import sys
import time
import signal
import subprocess
import re
import argparse

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gio, GLib

PLANK_SETTINGS_SCHEMA = "net.launchpad.plank.dock.settings"
PLANK_SETTINGS_PATH = "/net/launchpad/plank/docks/dock1/"

def detect_active_monitor_plug():
    """Detect the active primary or connected X11 monitor plug name via xrandr."""
    try:
        out = subprocess.check_output(["xrandr", "--query"], stderr=subprocess.DEVNULL).decode("utf-8")
        primary = None
        first_connected = None
        for line in out.splitlines():
            if " connected" in line:
                m = re.match(r"^(\S+)\s+connected", line)
                if m:
                    plug_name = m.group(1)
                    if "primary" in line:
                        primary = plug_name
                    if not first_connected:
                        first_connected = plug_name
        return primary or first_connected or ""
    except Exception:
        return ""

def calculate_responsive_dock_geometry():
    """Calculate optimal responsive dock geometry and centering offset."""
    display = Gdk.Display.get_default()
    if not display:
        return 2560, 1080, 48, 140, "", 0

    mon = display.get_primary_monitor() or (display.get_monitor(0) if display.get_n_monitors() > 0 else None)
    if mon:
        geom = mon.get_geometry()
        w_screen, h_screen = geom.width, geom.height
    else:
        screen = display.get_default_screen()
        w_screen, h_screen = screen.get_width(), screen.get_height()

    plug_name = detect_active_monitor_plug()

    # Query active X11 workarea width (accounting for companion sidebar struts)
    w_work = w_screen
    try:
        out = subprocess.check_output(["xprop", "-root", "_NET_WORKAREA"], stderr=subprocess.DEVNULL).decode("utf-8")
        m = re.search(r"=\s*\d+,\s*\d+,\s*(\d+),\s*(\d+)", out)
        if m:
            w_work = int(m.group(1))
    except Exception:
        w_work = w_screen

    # Dynamic responsive icon size & zoom calculation:
    # - 4K UHD & 5K (w >= 3840 or h >= 2160): 56px icons
    # - Ultrawide, QHD & 1080p (w >= 1920 and h >= 1080): 48px icons
    # - Mid-tier (w >= 1600 or h >= 900): 44px icons
    # - Budget Laptop & compact (w <= 1366 or h <= 768): 40px icons
    if w_screen >= 3840 or h_screen >= 2160:
        icon_size = 56
        zoom = 140
    elif w_screen <= 1366 or h_screen <= 768:
        icon_size = 40
        zoom = 130
    elif w_screen <= 1600 or h_screen <= 900:
        icon_size = 44
        zoom = 135
    else:
        icon_size = 48
        zoom = 140

    # Centering Alignment Invariant:
    # Plank spans full monitor width and natively centers items with alignment='center'.
    # Offset must remain strictly 0 to guarantee symmetrical equilibrium.
    offset = 0

    return w_screen, h_screen, icon_size, zoom, plug_name, offset

def apply_plank_dock_responsiveness():
    """Apply responsive centering parameters to Plank GSettings."""
    try:
        w_screen, h_screen, icon_size, zoom, plug_name, offset = calculate_responsive_dock_geometry()
        settings = Gio.Settings.new_with_path(PLANK_SETTINGS_SCHEMA, PLANK_SETTINGS_PATH)

        if plug_name:
            settings.set_string("monitor", plug_name)
        settings.set_string("alignment", "center")
        settings.set_string("items-alignment", "center")
        settings.set_int("offset", offset)
        settings.set_int("icon-size", icon_size)
        settings.set_int("zoom-percent", zoom)
        settings.set_string("theme", "Flowork-Modern")
        settings.set_string("hide-mode", "intelligent")
        Gio.Settings.sync()

        print(f"[Dock Responsive] Synced: Screen={w_screen}x{h_screen}, IconSize={icon_size}px, Offset={offset}%", flush=True)
        return True
    except Exception as e:
        print(f"[Dock Responsive] Error applying settings: {e}", file=sys.stderr, flush=True)
        return False

class DockResponsiveWatcher:
    def __init__(self):
        self.display = Gdk.Display.get_default()
        if not self.display:
            time.sleep(1)
            self.display = Gdk.Display.get_default()

        self.screen = self.display.get_default_screen() if self.display else None
        self._debounce_timer = None
        self._last_workarea = None

        if self.display:
            self.display.connect("monitor-added", self._on_display_event)
            self.display.connect("monitor-removed", self._on_display_event)
        if self.screen:
            self.screen.connect("size-changed", self._on_display_event)
            self.screen.connect("monitors-changed", self._on_display_event)

        # Apply initial settings immediately
        apply_plank_dock_responsiveness()

        # Monitor workarea changes (e.g. sidebar resize or toggle) in-process with zero subprocess forks
        GLib.timeout_add(1500, self._check_workarea_change)

    def _check_workarea_change(self):
        try:
            if self.display:
                mon = self.display.get_primary_monitor() or (self.display.get_monitor(0) if self.display.get_n_monitors() > 0 else None)
                if mon:
                    wa = mon.get_workarea()
                    geom = (wa.x, wa.y, wa.width, wa.height)
                    if geom != self._last_workarea:
                        self._last_workarea = geom
                        apply_plank_dock_responsiveness()
        except Exception:
            pass
        return True

    def _on_display_event(self, *args):
        if self._debounce_timer is not None:
            GLib.source_remove(self._debounce_timer)
        self._debounce_timer = GLib.timeout_add(300, self._do_debounced_sync)

    def _do_debounced_sync(self):
        self._debounce_timer = None
        apply_plank_dock_responsiveness()
        return False

def handle_sig(sig, frame):
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Flowork Sovereign OS Dock Responsive Sync")
    parser.add_argument("--sync", action="store_true", help="Sync dock configuration once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run background monitor change listener daemon")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    if args.sync or not args.daemon:
        success = apply_plank_dock_responsiveness()
        sys.exit(0 if success else 1)

    print("⚡ Flowork Dock Responsive Daemon active...", flush=True)
    watcher = DockResponsiveWatcher()
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
