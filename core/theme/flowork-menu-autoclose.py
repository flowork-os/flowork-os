#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Auto-Close Daemon for Menus & Start
# Closes Whisker Menu (Start Menu) automatically whenever mouse leaves bounds.
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================

import os
import sys
import time
import signal
import subprocess
import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib

def handle_sig(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sig)
signal.signal(signal.SIGTERM, handle_sig)

class MenuAutoCloseWatcher:
    def __init__(self):
        self.display = Gdk.Display.get_default()
        if not self.display:
            time.sleep(1)
            self.display = Gdk.Display.get_default()
        self.screen = self.display.get_default_screen()
        self.seat = self.display.get_default_seat()

        self.menu_open = False
        self.mouse_entered = False
        self.ticks_outside = 0
        self.open_time = 0

    def check_tick(self):
        try:
            stack = self.screen.get_window_stack()
            whisker = None
            if stack:
                for w in stack:
                    origin = w.get_root_origin()
                    geom = w.get_geometry()
                    # Whisker Menu is positioned at top-left x=0, y=29 (width=560, height=620)
                    if w.get_type_hint() == Gdk.WindowTypeHint.MENU and origin.x == 0 and origin.y <= 36:
                        whisker = (origin.x, origin.y, geom.width, geom.height)
                        break

            if whisker:
                wx, wy, ww, wh = whisker
                now = time.time()
                if not self.menu_open:
                    self.menu_open = True
                    self.mouse_entered = False
                    self.ticks_outside = 0
                    self.open_time = now

                pointer = self.seat.get_pointer()
                _, mx, my = pointer.get_position()

                # Allowed area: Inside the menu window or over the start button on top panel
                inside = (0 <= mx <= (wx + ww)) and (0 <= my <= (wy + wh))

                if inside:
                    self.mouse_entered = True
                    self.ticks_outside = 0
                else:
                    elapsed = now - self.open_time
                    # If mouse was in the menu and now left, OR grace period of 1.2s passed with mouse outside
                    if self.mouse_entered or elapsed > 1.2:
                        self.ticks_outside += 1
                        if self.ticks_outside >= 2: # ~200ms debounce
                            subprocess.run(["xdotool", "key", "Escape"], check=False)
                            self.menu_open = False
                            self.mouse_entered = False
                            self.ticks_outside = 0
            else:
                self.menu_open = False
                self.mouse_entered = False
                self.ticks_outside = 0
        except Exception:
            pass
        return True

def main():
    watcher = MenuAutoCloseWatcher()
    GLib.timeout_add(100, watcher.check_tick)
    loop = GLib.MainLoop()
    loop.run()

if __name__ == '__main__':
    main()
