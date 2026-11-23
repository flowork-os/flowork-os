#!/usr/bin/env python3
# ==============================================================================
# 💎 Flowork Sovereign OS — Muelle Optical Glass Launch Effect
# Inspired by crafter-station/muelle:
# Real-time GPU-accelerated translucent optical glass ripple & emerald shockwave
# on application launch. Click-through, zero lag, auto-terminates in ~380ms.
# ==============================================================================

import sys
import os
import math
import time

# Suppress noisy GTK/CSS C-level parsing warnings
try:
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, 2)
    os.close(devnull_fd)
except Exception:
    pass

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import cairo

class MuelleLaunchFX(Gtk.Window):
    def __init__(self, target_x=None, target_y=None, size=180, duration=0.38):
        super().__init__(type=Gtk.WindowType.POPUP)

        self.set_title("MuelleLaunchEffect")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_app_paintable(True)

        # Transparent RGBA visual
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.size = size
        self.duration = duration
        self.start_time = time.time()

        # Resolve launch center point
        if target_x is None or target_y is None:
            display = Gdk.Display.get_default()
            seat = display.get_default_seat()
            pointer = seat.get_pointer() if seat else None
            if pointer:
                _, px, py = pointer.get_position()
                target_x, target_y = px, py
            else:
                target_x, target_y = screen.get_width() // 2, screen.get_height() - 60

        half = size // 2
        self.move(int(target_x - half), int(target_y - half))
        self.set_size_request(size, size)

        # Make window 100% click-through (input-transparent)
        self.connect("realize", self.on_realize)
        self.connect("draw", self.on_draw)

        # 60 FPS animation timer (~16ms)
        GLib.timeout_add(16, self.on_tick)

    def on_realize(self, widget):
        # Empty input shape = clicks pass straight through to desktop/apps
        region = cairo.Region()
        widget.get_window().input_shape_combine_region(region, 0, 0)

    def on_tick(self):
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            self.destroy()
            Gtk.main_quit()
            return False
        self.queue_draw()
        return True

    def on_draw(self, widget, cr):
        elapsed = time.time() - self.start_time
        progress = min(1.0, elapsed / self.duration)

        # Cubic ease-out expansion: f(p) = 1 - (1 - p)^3
        ease_out = 1.0 - math.pow(1.0 - progress, 3)

        # Sinusoidal energy pulse from Muelle physics: lift = sin(pi * progress)
        pulse = math.sin(math.pi * progress)
        fade = 1.0 - progress

        w = self.size
        h = self.size
        cx = w / 2.0
        cy = h / 2.0

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        # Max radius
        max_r = (min(w, h) / 2.0) - 6.0
        current_r = max_r * ease_out

        if current_r > 2.0:
            # 1. Optical Glass Translucent Lens Gradient
            grad = cairo.RadialGradient(cx, cy, 0, cx, cy, current_r)
            grad.add_color_stop_rgba(0.0, 0.0, 1.0, 0.4, 0.15 * fade * pulse)
            grad.add_color_stop_rgba(0.4, 1.0, 1.0, 1.0, 0.08 * fade)
            grad.add_color_stop_rgba(0.85, 0.0, 1.0, 0.4, 0.22 * fade)
            grad.add_color_stop_rgba(1.0, 1.0, 1.0, 1.0, 0.0)

            cr.arc(cx, cy, current_r, 0, 2 * math.pi)
            cr.set_source(grad)
            cr.fill()

            # 2. Emerald Radiant Core Shockwave (#00ff66)
            emerald_r = current_r * 0.92
            if emerald_r > 1.0:
                cr.arc(cx, cy, emerald_r, 0, 2 * math.pi)
                cr.set_source_rgba(0.0, 1.0, 0.4, 0.70 * fade * pulse)
                cr.set_line_width(2.5 * fade)
                cr.stroke()

            # 3. Razor-Thin Dual Specular Refraction Rim (Muelle Optical Glass)
            cr.arc(cx, cy, current_r, 0, 2 * math.pi)
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.85 * fade)
            cr.set_line_width(1.5 * fade)
            cr.stroke()

            # 4. Secondary Outer Specular Echo Ring
            echo_r = current_r * 1.06
            if echo_r < (min(w, h) / 2.0):
                cr.arc(cx, cy, echo_r, 0, 2 * math.pi)
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.35 * fade * pulse)
                cr.set_line_width(1.0 * fade)
                cr.stroke()

        return False

def main():
    target_x = None
    target_y = None
    if len(sys.argv) >= 3:
        try:
            target_x = float(sys.argv[1])
            target_y = float(sys.argv[2])
        except ValueError:
            pass

    win = MuelleLaunchFX(target_x, target_y)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
