#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Living Motion Theme & Ambient Wallpaper Engine 3.0
# Ultra-Soft, Organic Gaseous Silk & Liquid Crystal Motion — Zero Dull Gray
# 6 Distinct Motion Art Styles:
#   1. aurora-silk   — Quantum Silk Aurora (Ethereal Polar Ribbons)
#   2. plasma-drift  — Cyber Liquid Plasma (Molten Neon Mercury Drift)
#   3. nebula-mist   — Cosmic Stardust Nebula (Celestial Breathing Void)
#   4. solar-dusk    — Solar Amber Dusk (Velvety Coronal Flare Dunes)
#   5. matrix-ocean  — Bioluminescent Abyss (Deep Midnight Emerald Swells)
#   6. prism-aether  — Holographic Aether (Iridescent Crystal Silk Veils)
# Hardware Optimized: Dynamic 640x270 Bilinear Scaled Canvas (~2% CPU)
# Co-authored-by: Flowork OS Architecture Board & Dr. Flow <agent@floworkos.com>
# =============================================================================

import os
import sys
import math
import time
import json
import signal
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import cairo

try:
    import flowork_neural_bridge
except ImportError:
    sys.path.insert(0, "/opt/floworkos/theme")
    import flowork_neural_bridge

THEME_FILE = "/opt/floworkos/theme/current-theme.json"
CONFIG_FILE = "/opt/floworkos/theme/motion-config.json"
PID_FILE = f"/run/user/{os.getuid()}/flowork-motion-ambient.pid"

MOTION_STYLES = {
    "oceanic-core": {
        "id": "oceanic-core",
        "name": "Mr. Flow Sovereign Oceanic Core",
        "desc": "Deep marine navy abyss with centered holographic arc reactor & dynamic voice/tool visualizer.",
        "bg_top": (0.006, 0.028, 0.065),
        "bg_bottom": (0.001, 0.006, 0.018),
        "colors": [
            (0.00, 0.85, 1.00),   # Electric oceanic cyan (#00d2ff)
            (0.00, 0.50, 0.90),   # Deep marine azure
            (0.00, 1.00, 0.55),   # Phosphor mint (#00ff88)
            (0.40, 0.95, 1.00)    # Ice core white-cyan
        ],
        "speed": 0.005,
        "style": "oceanic"
    },
    "aurora-silk": {
        "id": "aurora-silk",
        "name": "Quantum Silk Aurora",
        "desc": "Ethereal polar ribbons of electric cyan, emerald green, and cosmic violet glowing in the Arctic midnight sky.",
        "bg_top": (0.010, 0.025, 0.055),
        "bg_bottom": (0.002, 0.008, 0.018),
        "colors": [
            (0.00, 0.95, 1.00),   # Glacial cyan
            (0.00, 1.00, 0.45),   # Emerald green
            (0.65, 0.20, 1.00),   # Cosmic violet
            (0.00, 0.80, 0.90)    # Deep aqua
        ],
        "speed": 0.006,
        "style": "aurora"
    },
    "plasma-drift": {
        "id": "plasma-drift",
        "name": "Cyber Liquid Plasma",
        "desc": "Voluptuous molten fluid blobs of neon fuchsia, electric cyan, and deep ultraviolet drifting and morphing softly.",
        "bg_top": (0.035, 0.008, 0.050),
        "bg_bottom": (0.008, 0.002, 0.018),
        "colors": [
            (1.00, 0.00, 0.50),   # Hot fuchsia (#ff007f)
            (0.00, 0.95, 1.00),   # Electric cyan (#00f2fe)
            (0.72, 0.16, 1.00),   # Deep violet
            (1.00, 0.20, 0.65)    # Neon rose
        ],
        "speed": 0.005,
        "style": "plasma"
    },
    "nebula-mist": {
        "id": "nebula-mist",
        "name": "Cosmic Stardust Nebula",
        "desc": "Deep interstellar stardust clouds breathing in cosmic space with celestial magenta and starlight cyan pockets.",
        "bg_top": (0.020, 0.010, 0.045),
        "bg_bottom": (0.005, 0.002, 0.015),
        "colors": [
            (0.72, 0.16, 1.00),   # Cosmic violet (#b829ff)
            (0.00, 0.90, 1.00),   # Starlight aqua
            (1.00, 0.18, 0.55),   # Stellar rose
            (0.40, 0.10, 0.85)    # Deep void indigo
        ],
        "speed": 0.004,
        "style": "nebula"
    },
    "solar-dusk": {
        "id": "solar-dusk",
        "name": "Solar Amber Dusk",
        "desc": "Warm, velvety sunset flare of liquid amber gold, coral crimson, and molten bronze rolling softly like dunes of sunlight.",
        "bg_top": (0.045, 0.018, 0.008),
        "bg_bottom": (0.012, 0.004, 0.002),
        "colors": [
            (1.00, 0.72, 0.00),   # Amber gold (#ffb800)
            (1.00, 0.18, 0.32),   # Sunset coral (#ff2d55)
            (1.00, 0.45, 0.05),   # Molten copper
            (0.85, 0.12, 0.20)    # Deep ruby dusk
        ],
        "speed": 0.005,
        "style": "solar"
    },
    "matrix-ocean": {
        "id": "matrix-ocean",
        "name": "Bioluminescent Abyss",
        "desc": "Deep oceanic abyss with undulating waves of razor emerald, glowing aquamarine, and mint phosphorescence.",
        "bg_top": (0.005, 0.028, 0.018),
        "bg_bottom": (0.001, 0.008, 0.005),
        "colors": [
            (0.00, 1.00, 0.40),   # Razor emerald (#00ff66)
            (0.00, 0.92, 0.80),   # Cyan bioluminescence
            (0.22, 1.00, 0.55),   # Mint glow
            (0.00, 0.65, 0.50)    # Deep oceanic teal
        ],
        "speed": 0.005,
        "style": "matrix"
    },
    "prism-aether": {
        "id": "prism-aether",
        "name": "Holographic Aether",
        "desc": "Shimmering iridescent silk veils of holographic lavender, prism cyan, and sunset peach flowing gracefully.",
        "bg_top": (0.025, 0.022, 0.045),
        "bg_bottom": (0.008, 0.010, 0.020),
        "colors": [
            (0.75, 0.52, 0.98),   # Holographic lavender (#c084fc)
            (0.22, 0.74, 0.97),   # Prism cyan (#38bdf8)
            (0.98, 0.44, 0.52),   # Sunset peach (#fb7185)
            (0.40, 0.85, 0.95)    # Ice crystal aqua
        ],
        "speed": 0.004,
        "style": "prism"
    }
}

THEME_TO_STYLE = {
    "matrix-razor": "oceanic-core",
    "neon-plasma": "plasma-drift",
    "quantum-aurora": "aurora-silk",
    "solar-flare": "solar-dusk",
    "deep-nebula": "nebula-mist"
}

def load_motion_config():
    cfg = {"enabled": True, "style": "oceanic-core", "speed": 1.0, "glow_intensity": 1.0}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg

def save_motion_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

class FloworkMotionAmbient(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Flowork Living Motion Wallpaper")
        self.set_role("flowork-living-wallpaper")

        # Desktop Invariants
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)
        self.set_app_paintable(True)

        screen = self.get_screen()
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        self.resize(self.screen_w, self.screen_h)
        self.move(0, 0)

        # Dynamic low-res buffer preserving screen aspect ratio (~2% CPU)
        self.buf_w = 640
        self.buf_h = max(180, int(640 * self.screen_h / self.screen_w))
        self.surface_buf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.buf_w, self.buf_h)

        # Style & Theme State
        self.config = load_motion_config()
        self.current_theme_id = "matrix-razor"
        self.active_style_key = "oceanic-core"
        self.style_data = MOTION_STYLES["oceanic-core"]
        self.last_theme_mtime = 0.0
        self.last_config_mtime = 0.0

        self.t = 0.0
        self.sync_active_style()

        # Neural Reactor State (Living Desktop Canvas for Tools & Voice)
        self.reactor_intensity = 0.0
        self.active_morphology = "morph-idle"
        self.active_amplitude = 0.0
        self.target_amplitude = 0.0
        self.active_tool_name = ""
        self.active_action = ""
        self.radar_angle = 0.0
        self.laser_scan_y = 0.5
        self.laser_scan_dir = 1.0
        self.swarm_phase = 0.0
        self.matrix_offsets = [(i * 37) % 100 for i in range(24)]
        self.raw_state = "idle"
        self.thinking_flux = 0.0

        self.connect("draw", self.on_draw)
        self.connect("realize", self.on_realize)
        GLib.timeout_add(33, self.on_animation_tick)   # 30 FPS: ultra-silky audio tracking
        GLib.timeout_add_seconds(2, self.periodic_check)

    def on_realize(self, widget):
        self.stick()
        self.set_keep_below(True)
        gdk_win = self.get_window()
        if gdk_win:
            gdk_win.lower()

    def sync_active_style(self):
        # 1. Check Theme
        if os.path.exists(THEME_FILE):
            try:
                mtime = os.path.getmtime(THEME_FILE)
                if mtime != self.last_theme_mtime:
                    self.last_theme_mtime = mtime
                    with open(THEME_FILE, "r", encoding="utf-8") as f:
                        tdata = json.load(f)
                    self.current_theme_id = tdata.get("id", tdata.get("theme_id", "matrix-razor"))
            except Exception:
                pass

        # 2. Check Config
        if os.path.exists(CONFIG_FILE):
            try:
                mtime = os.path.getmtime(CONFIG_FILE)
                if mtime != self.last_config_mtime:
                    self.last_config_mtime = mtime
                    self.config = load_motion_config()
            except Exception:
                pass

        cfg_style = self.config.get("style", "auto")
        if cfg_style in MOTION_STYLES:
            self.active_style_key = cfg_style
        else:
            self.active_style_key = THEME_TO_STYLE.get(self.current_theme_id, "aurora-silk")

        self.style_data = MOTION_STYLES.get(self.active_style_key, MOTION_STYLES["aurora-silk"])

    def periodic_check(self):
        self.sync_active_style()
        return True

    def on_animation_tick(self):
        speed_factor = self.config.get("speed", 1.0)
        self.t += self.style_data.get("speed", 0.005) * speed_factor
        if self.t > 100000.0:
            self.t = 0.0

        # Update Neural Reactor state from shared memory (/dev/shm)
        try:
            n_state = flowork_neural_bridge.get_neural_state()
            self.raw_state = n_state.get("state", "idle")
            target_int = 1.0 if self.raw_state in ("tool_use", "speaking", "thinking") else 0.0
            self.active_morphology = n_state.get("morphology", "morph-idle")
            self.target_amplitude = n_state.get("amplitude", 0.7 if self.raw_state in ("tool_use", "thinking") else 0.0)
            self.active_tool_name = n_state.get("tool_name", "")
            self.active_action = n_state.get("action", "")
        except Exception:
            target_int = 0.0

        # Smooth interpolation (ease in / ease out)
        self.reactor_intensity += (target_int - self.reactor_intensity) * 0.12
        if self.target_amplitude > self.active_amplitude:
            self.active_amplitude += (self.target_amplitude - self.active_amplitude) * 0.65
        else:
            self.active_amplitude += (self.target_amplitude - self.active_amplitude) * 0.30

        # Dynamic cognitive thinking flux (smooth transition 0.0 -> 1.0)
        target_thinking = 1.0 if (self.raw_state == "thinking" or self.active_morphology in ("morph-thinking", "morph-circle")) else 0.0
        self.thinking_flux += (target_thinking - self.thinking_flux) * 0.14

        # Update dynamic animation phases
        self.radar_angle = (self.radar_angle + 0.08) % (2 * math.pi)
        self.laser_scan_y += 0.012 * self.laser_scan_dir
        if self.laser_scan_y > 0.85:
            self.laser_scan_dir = -1.0
        elif self.laser_scan_y < 0.25:
            self.laser_scan_dir = 1.0
        self.swarm_phase = (self.swarm_phase + 0.04) % (2 * math.pi)
        for idx in range(len(self.matrix_offsets)):
            self.matrix_offsets[idx] = (self.matrix_offsets[idx] + 1.2 + (idx % 3) * 0.4) % 100.0

        self.render_buffer()
        self.queue_draw()
        return True

    def render_buffer(self):
        cr = cairo.Context(self.surface_buf)
        bw, bh = float(self.buf_w), float(self.buf_h)
        style_type = self.style_data.get("style", "aurora")
        colors = self.style_data.get("colors", [])
        bg_t = self.style_data.get("bg_top", (0.01, 0.02, 0.04))
        bg_b = self.style_data.get("bg_bottom", (0.002, 0.005, 0.015))
        glow = self.config.get("glow_intensity", 1.0)

        # 1. Base Atmospheric Sky Gradient (Zero generic dull gray)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        base_grad = cairo.LinearGradient(0, 0, bw * 0.4, bh)
        base_grad.add_color_stop_rgb(0.0, bg_t[0], bg_t[1], bg_t[2])
        base_grad.add_color_stop_rgb(1.0, bg_b[0], bg_b[1], bg_b[2])
        cr.set_source(base_grad)
        cr.paint()

        cr.set_operator(cairo.OPERATOR_OVER)

        # 2. Render Selected Motion Version
        if style_type == "oceanic":
            self.render_oceanic_abyss(cr, bw, bh, colors, glow)
        elif style_type == "aurora":
            self.render_aurora_silk(cr, bw, bh, colors, glow)
        elif style_type == "plasma":
            self.render_plasma_drift(cr, bw, bh, colors, glow)
        elif style_type == "nebula":
            self.render_nebula_mist(cr, bw, bh, colors, glow)
        elif style_type == "solar":
            self.render_solar_dusk(cr, bw, bh, colors, glow)
        elif style_type == "matrix":
            self.render_matrix_ocean(cr, bw, bh, colors, glow)
        elif style_type == "prism":
            self.render_prism_aether(cr, bw, bh, colors, glow)

        # 3. Soft Atmospheric Vignette (Delicate rim falloff)
        vig = cairo.RadialGradient(bw * 0.5, bh * 0.45, bw * 0.25, bw * 0.5, bh * 0.5, bw * 0.70)
        vig.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, 0.0)
        vig.add_color_stop_rgba(0.65, 0.0, 0.0, 0.0, 0.08)
        vig.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.35)
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source(vig)
        cr.paint()

        # 4. Living Desktop Neural Reactor Layer (Tools & Voice Waveform)
        if style_type == "oceanic" or self.reactor_intensity > 0.005:
            self.render_neural_reactor(cr, bw, bh, glow)

    def render_aurora_silk(self, cr, bw, bh, colors, glow):
        """Silky sweeping polar curtains undulating across the upper-mid horizon."""
        # Layer 1: Ambient background glow pools
        for i, c in enumerate(colors[:3]):
            ox = bw * (0.25 + 0.25 * i + 0.10 * math.sin(self.t * 0.6 + i))
            oy = bh * (0.42 + 0.08 * math.cos(self.t * 0.5 + i * 1.5))
            r = bw * (0.35 + 0.08 * math.sin(self.t * 0.4 + i))
            rad = cairo.RadialGradient(ox, oy, 10.0, ox, oy, r)
            rad.add_color_stop_rgba(0.0, c[0], c[1], c[2], 0.28 * glow)
            rad.add_color_stop_rgba(0.4, c[0], c[1], c[2], 0.14 * glow)
            rad.add_color_stop_rgba(0.8, c[0], c[1], c[2], 0.02 * glow)
            rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(rad)
            cr.paint()

        # Layer 2: Ethereal flowing silk ribbons
        cr.set_operator(cairo.OPERATOR_SCREEN)
        for idx in range(3):
            phase = self.t * (0.7 + idx * 0.25) + idx * 1.6
            c = colors[idx % len(colors)]
            mid_y = bh * (0.32 + 0.15 * idx)
            wave_amp = 30.0 + 8.0 * idx

            cr.new_sub_path()
            cr.move_to(0, bh)
            cr.line_to(0, mid_y)

            # 4 Organic cubic bezier control nodes
            p1_x = bw * 0.25
            p1_y = mid_y + math.sin(phase) * wave_amp
            p2_x = bw * 0.50
            p2_y = mid_y + math.cos(phase * 0.85) * wave_amp * 1.25
            p3_x = bw * 0.75
            p3_y = mid_y + math.sin(phase * 0.65 + 1.2) * wave_amp
            p4_x = bw
            p4_y = mid_y + math.cos(phase * 0.90) * wave_amp * 0.9

            cr.curve_to(p1_x * 0.6, p1_y, p1_x, p1_y, p2_x, p2_y)
            cr.curve_to(p3_x * 0.9, p3_y, p3_x, p3_y, p4_x, p4_y)
            cr.line_to(bw, bh)
            cr.close_path()

            grad = cairo.LinearGradient(0, mid_y - 35.0, 0, bh)
            alpha = (0.24 + 0.06 * math.sin(phase * 0.7)) * glow
            grad.add_color_stop_rgba(0.0, c[0], c[1], c[2], alpha)
            grad.add_color_stop_rgba(0.35, c[0], c[1], c[2], alpha * 0.65)
            grad.add_color_stop_rgba(0.75, c[0], c[1], c[2], alpha * 0.15)
            grad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(grad)
            cr.fill()

    def render_plasma_drift(self, cr, bw, bh, colors, glow):
        """Voluptuous molten fluid blobs morphing, merging, and floating across the screen."""
        cr.set_operator(cairo.OPERATOR_SCREEN)
        orbs = [
            (bw * (0.32 + 0.22 * math.sin(self.t * 0.6)), bh * (0.45 + 0.18 * math.cos(self.t * 0.5)), bw * 0.38, colors[0]),
            (bw * (0.68 + 0.20 * math.cos(self.t * 0.45)), bh * (0.52 + 0.20 * math.sin(self.t * 0.7)), bw * 0.42, colors[1]),
            (bw * (0.50 + 0.18 * math.sin(self.t * 0.8)), bh * (0.35 + 0.15 * math.sin(self.t * 0.35)), bw * 0.34, colors[2]),
            (bw * (0.18 + 0.14 * math.cos(self.t * 0.55)), bh * (0.65 + 0.16 * math.sin(self.t * 0.65)), bw * 0.30, colors[3 % len(colors)]),
        ]
        for ox, oy, r, c in orbs:
            rad = cairo.RadialGradient(ox, oy, 15.0, ox, oy, r)
            rad.add_color_stop_rgba(0.0, c[0], c[1], c[2], 0.38 * glow)
            rad.add_color_stop_rgba(0.35, c[0], c[1], c[2], 0.22 * glow)
            rad.add_color_stop_rgba(0.70, c[0], c[1], c[2], 0.06 * glow)
            rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(rad)
            cr.paint()

    def render_nebula_mist(self, cr, bw, bh, colors, glow):
        """Interstellar stardust clouds breathing in cosmic space with deep luminescence."""
        cr.set_operator(cairo.OPERATOR_SCREEN)
        centers = [
            (bw * (0.28 + 0.08 * math.sin(self.t * 0.35)), bh * (0.48 + 0.08 * math.cos(self.t * 0.3)), bw * 0.46, colors[0]),
            (bw * (0.72 + 0.07 * math.cos(self.t * 0.28)), bh * (0.40 + 0.09 * math.sin(self.t * 0.32)), bw * 0.48, colors[1]),
            (bw * (0.50 + 0.10 * math.sin(self.t * 0.42)), bh * (0.65 + 0.08 * math.cos(self.t * 0.4)), bw * 0.40, colors[2]),
            (bw * (0.85 + 0.06 * math.sin(self.t * 0.3)), bh * (0.70 + 0.08 * math.sin(self.t * 0.25)), bw * 0.32, colors[3 % len(colors)])
        ]
        for cx, cy, r, c in centers:
            breathe = 1.0 + 0.08 * math.sin(self.t * 0.5 + cx)
            rad = cairo.RadialGradient(cx, cy, 25.0, cx, cy, r * breathe)
            rad.add_color_stop_rgba(0.0, c[0], c[1], c[2], 0.32 * glow)
            rad.add_color_stop_rgba(0.40, c[0], c[1], c[2], 0.18 * glow)
            rad.add_color_stop_rgba(0.75, c[0], c[1], c[2], 0.04 * glow)
            rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(rad)
            cr.paint()

    def render_solar_dusk(self, cr, bw, bh, colors, glow):
        """Warm molten gold & amber coronal waves rising softly like liquid dusk."""
        # Horizon soft glow
        horizon_y = bh * 0.60
        sun_x = bw * (0.50 + 0.15 * math.sin(self.t * 0.3))
        sun_rad = cairo.RadialGradient(sun_x, horizon_y, 20.0, sun_x, horizon_y, bw * 0.55)
        sun_rad.add_color_stop_rgba(0.0, colors[0][0], colors[0][1], colors[0][2], 0.40 * glow)
        sun_rad.add_color_stop_rgba(0.35, colors[1][0], colors[1][1], colors[1][2], 0.22 * glow)
        sun_rad.add_color_stop_rgba(0.75, colors[2][0], colors[2][1], colors[2][2], 0.05 * glow)
        sun_rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SCREEN)
        cr.set_source(sun_rad)
        cr.paint()

        # Rolling coronal wave dunes
        for idx in range(3):
            phase = self.t * (0.65 + idx * 0.25) + idx * 1.5
            c = colors[idx % len(colors)]
            mid_y = bh * (0.52 + 0.14 * idx)

            cr.new_sub_path()
            cr.move_to(0, bh)
            cr.line_to(0, mid_y)

            steps = 10
            sw = bw / float(steps)
            for s in range(steps + 1):
                cur_x = s * sw
                cur_y = mid_y + math.sin(phase + s * 0.55) * (18.0 + 7.0 * idx)
                cr.line_to(cur_x, cur_y)

            cr.line_to(bw, bh)
            cr.close_path()

            grad = cairo.LinearGradient(0, mid_y - 40.0, 0, bh)
            alpha = (0.26 + 0.05 * math.cos(phase * 0.7)) * glow
            grad.add_color_stop_rgba(0.0, c[0], c[1], c[2], alpha)
            grad.add_color_stop_rgba(0.40, c[0], c[1], c[2], alpha * 0.6)
            grad.add_color_stop_rgba(0.80, c[0], c[1], c[2], alpha * 0.12)
            grad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(grad)
            cr.fill()

    def render_matrix_ocean(self, cr, bw, bh, colors, glow):
        """Deep oceanic abyss with harmonic waves of razor emerald and cyan bioluminescence."""
        # Deep organic luminescent pools
        cr.set_operator(cairo.OPERATOR_SCREEN)
        for i, c in enumerate(colors[:2]):
            ox = bw * (0.35 + 0.30 * i + 0.12 * math.cos(self.t * 0.5 + i))
            oy = bh * (0.55 + 0.12 * math.sin(self.t * 0.4 + i))
            r = bw * (0.42 + 0.06 * math.sin(self.t * 0.35 + i))
            rad = cairo.RadialGradient(ox, oy, 15.0, ox, oy, r)
            rad.add_color_stop_rgba(0.0, c[0], c[1], c[2], 0.34 * glow)
            rad.add_color_stop_rgba(0.40, c[0], c[1], c[2], 0.16 * glow)
            rad.add_color_stop_rgba(0.75, c[0], c[1], c[2], 0.03 * glow)
            rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(rad)
            cr.paint()

        # Undulating ocean swells
        for idx in range(3):
            phase = self.t * (0.60 + idx * 0.22) + idx * 1.8
            c = colors[idx % len(colors)]
            mid_y = bh * (0.40 + 0.16 * idx)

            cr.new_sub_path()
            cr.move_to(0, bh)
            cr.line_to(0, mid_y)

            steps = 12
            sw = bw / float(steps)
            for s in range(steps + 1):
                cur_x = s * sw
                cur_y = mid_y + math.sin(phase + s * 0.50) * (20.0 + 8.0 * idx)
                cr.line_to(cur_x, cur_y)

            cr.line_to(bw, bh)
            cr.close_path()

            grad = cairo.LinearGradient(0, mid_y - 35.0, 0, bh)
            alpha = (0.28 + 0.05 * math.sin(phase * 0.6)) * glow
            grad.add_color_stop_rgba(0.0, c[0], c[1], c[2], alpha)
            grad.add_color_stop_rgba(0.45, c[0], c[1], c[2], alpha * 0.55)
            grad.add_color_stop_rgba(0.85, c[0], c[1], c[2], alpha * 0.10)
            grad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(grad)
            cr.fill()

    def render_prism_aether(self, cr, bw, bh, colors, glow):
        """Holographic iridescent crystal silk veils sliding across the screen."""
        cr.set_operator(cairo.OPERATOR_SCREEN)
        for idx in range(4):
            phase = self.t * (0.50 + idx * 0.18) + idx * 1.4
            c = colors[idx % len(colors)]
            cx = bw * (0.20 + 0.22 * idx + 0.10 * math.sin(phase))
            cy = bh * (0.40 + 0.15 * math.cos(phase * 0.8))
            r = bw * (0.36 + 0.08 * math.sin(phase * 0.6))

            rad = cairo.RadialGradient(cx, cy, 20.0, cx, cy, r)
            rad.add_color_stop_rgba(0.0, c[0], c[1], c[2], 0.30 * glow)
            rad.add_color_stop_rgba(0.35, c[0], c[1], c[2], 0.18 * glow)
            rad.add_color_stop_rgba(0.70, c[0], c[1], c[2], 0.04 * glow)
            rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(rad)
            cr.paint()

    def render_oceanic_abyss(self, cr, bw, bh, colors, glow):
        """Clean deep ocean navy abyss with tranquil central luminescence pool."""
        cx, cy = bw * 0.5, bh * 0.5
        cr.set_operator(cairo.OPERATOR_SCREEN)
        
        # Central deep-sea luminescence aura
        glow_rad = cairo.RadialGradient(cx, cy, 10.0, cx, cy, bw * 0.45)
        glow_rad.add_color_stop_rgba(0.0, 0.0, 0.45, 0.85, 0.22 * glow)
        glow_rad.add_color_stop_rgba(0.5, 0.0, 0.20, 0.55, 0.07 * glow)
        glow_rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(glow_rad)
        cr.paint()

    def render_mrflow_holographic_core(self, cr, bw, bh, glow):
        """
        Mr. Flow Sovereign Centered Holographic Core Arc Reactor (Oceanic AI OS Engine).
        Positioned at the golden intersection (x=50%, y=50%).
        Dynamically reacts to Voice Cadence, Tool Execution, and Neural Cognitive Thinking.
        """
        cx, cy = bw * 0.5, bh * 0.5
        rint = max(0.38, self.reactor_intensity * glow)
        morph = self.active_morphology
        t = self.t
        amp = self.active_amplitude
        tf = self.thinking_flux
        is_thinking = (tf > 0.04)

        # Dynamic Rotational Velocity: accelerates up to 2.8x during cognitive thinking
        rot_mult = 1.0 + 1.8 * tf

        # Dynamic Audio Pulse & Thinking Aperture Breathing Factors
        if morph == "morph-speech":
            pulse = 1.0 + 0.22 * amp
            iris_pulse = 1.0 + 0.35 * amp
            glow_pulse = 1.0 + 0.50 * amp
        elif is_thinking:
            # Hyper-focused aperture breathing rhythm at ~1.4 Hz (cognitive calculation)
            pulse = 1.0 + 0.05 * math.sin(t * 7.0) * tf
            iris_pulse = 1.0 - 0.10 * tf + 0.08 * math.sin(t * 9.0) * tf
            glow_pulse = 1.0 + 0.45 * tf + 0.15 * math.sin(t * 8.0) * tf
        else:
            pulse = 1.0
            iris_pulse = 1.0
            glow_pulse = 1.0

        cr.set_operator(cairo.OPERATOR_SCREEN)

        # Dynamic Color Shift: Smooth transition from Ocean Cyan to Electric Indigo
        # Ocean Cyan: rgb(0.0, 0.85, 1.0) -> Electric Indigo: rgb(0.48, 0.28, 1.0)
        cr_r = 0.0 * (1.0 - tf) + 0.48 * tf
        cr_g = 0.85 * (1.0 - tf) + 0.28 * tf
        cr_b = 1.0

        # 0. Thinking Luminescence Ripples (concentric wave ripples flowing outward into abyss)
        if is_thinking:
            for rip in range(2):
                phase = (t * 1.5 + rip * 0.5) % 1.0
                rip_r = (28.0 * iris_pulse) + phase * 44.0
                rip_alpha = (1.0 - phase) * 0.32 * tf * rint
                cr.set_line_width(1.0)
                cr.arc(cx, cy, rip_r, 0, 2 * math.pi)
                cr.set_source_rgba(0.55, 0.35, 1.0, rip_alpha)
                cr.stroke()

        # 1. Outer Concentric Precision Arc Ring
        cr.set_line_width(1.0 + 0.5 * amp + 0.3 * tf)
        cr.arc(cx, cy, 50.0 * pulse, 0, 2 * math.pi)
        cr.set_source_rgba(cr_r, cr_g * 0.85, cr_b, (0.25 + 0.15 * amp + 0.15 * tf) * rint)
        cr.stroke()

        # 2. Segmented rotating outer brackets (Fast Gyroscopic Counter-Rotation when thinking)
        for s in range(4):
            a_start = t * 0.35 * rot_mult + s * (math.pi / 2.0) + 0.15
            a_end = a_start + 0.75
            cr.set_line_width(1.8 + 1.2 * amp + 0.5 * tf)
            cr.arc(cx, cy, 56.0 * pulse, a_start, a_end)
            cr.set_source_rgba(cr_r, cr_g, cr_b, (0.75 + 0.25 * amp) * rint)
            cr.stroke()

        # 3. Precision Ticks on Outer Ring
        num_ticks = 40
        for i in range(num_ticks):
            ang = i * (2 * math.pi / num_ticks) + t * 0.12 * rot_mult
            is_major = (i % 4 == 0)
            r1 = 51.0 * pulse if is_major else 52.0 * pulse
            r2 = 55.0 * pulse if is_major else 54.0 * pulse
            cr.set_line_width((1.2 if is_major else 0.6) + 0.4 * amp + 0.2 * tf)
            cr.move_to(cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))
            cr.line_to(cx + r2 * math.cos(ang), cy + r2 * math.sin(ang))
            cr.set_source_rgba(cr_r, cr_g, cr_b, (0.65 if is_major else 0.25) * rint)
            cr.stroke()

        # 4. Middle counter-rotating ring with satellite nodes
        cr.set_line_width(0.8 + 0.4 * amp + 0.3 * tf)
        cr.arc(cx, cy, 40.0 * pulse, 0, 2 * math.pi)
        cr.set_source_rgba(cr_r * 0.8, cr_g * 0.8, cr_b, (0.35 + 0.15 * tf) * rint)
        cr.stroke()

        satellite_coords = []
        for d in range(6):
            ang = -t * 0.50 * rot_mult + d * (math.pi / 3.0)
            dot_x = cx + (40.0 * pulse) * math.cos(ang)
            dot_y = cy + (40.0 * pulse) * math.sin(ang)
            satellite_coords.append((dot_x, dot_y))
            cr.arc(dot_x, dot_y, 1.8 + 1.2 * amp + 0.6 * tf, 0, 2 * math.pi)
            cr.set_source_rgba(0.4 + 0.35 * tf, 0.95 - 0.45 * tf, 1.0, (0.85 + 0.15 * amp) * rint)
            cr.fill()

        # 4b. Synaptic inter-node laser web during thinking
        if is_thinking:
            cr.set_line_width(0.7)
            for i in range(len(satellite_coords)):
                next_node = satellite_coords[(i + 2) % len(satellite_coords)]
                cr.move_to(satellite_coords[i][0], satellite_coords[i][1])
                cr.line_to(next_node[0], next_node[1])
            cr.set_source_rgba(0.70, 0.40, 1.0, 0.30 * tf * rint)
            cr.stroke()

        # 5. Inner Glowing Iris Ring
        cr.set_line_width(1.4 + 1.4 * amp + 0.6 * tf)
        cr.arc(cx, cy, 28.0 * iris_pulse, 0, 2 * math.pi)
        cr.set_source_rgba(cr_r, cr_g, cr_b, (0.60 + 0.35 * amp + 0.25 * tf) * rint)
        cr.stroke()

        # 6. Center Morphology Inside Iris
        if morph == "morph-thinking" or (is_thinking and morph not in ("morph-terminal", "morph-frameless", "morph-chamfer", "morph-swarm")):
            # High-Frequency Synaptic Brainwave Oscillations (Cognitive Reasoning Core)
            r_iris = 28.0 * iris_pulse
            num_pts = 44
            dx = (r_iris * 1.7) / float(num_pts - 1)
            x_start = cx - (r_iris * 0.85)

            # Wave 1: Primary Synaptic Cognitive Flow (Electric Violet/Cobalt)
            cr.set_line_width(1.6)
            for i in range(num_pts):
                px = x_start + i * dx
                norm_x = (float(i) / (num_pts - 1) - 0.5) * 2.0
                envelope = max(0.0, 1.0 - norm_x * norm_x)
                py = cy + envelope * (7.5 * math.sin(norm_x * 9.0 + t * 14.0) * math.cos(norm_x * 4.0 - t * 8.0))
                if i == 0:
                    cr.move_to(px, py)
                else:
                    cr.line_to(px, py)
            cr.set_source_rgba(0.65, 0.30, 1.0, 0.95 * rint)
            cr.stroke()

            # Wave 2: Fast Harmonic Synaptic Spark (Pure Optical White / Cyan Spark)
            cr.set_line_width(1.0)
            for i in range(num_pts):
                px = x_start + i * dx
                norm_x = (float(i) / (num_pts - 1) - 0.5) * 2.0
                envelope = max(0.0, 1.0 - norm_x * norm_x)
                py = cy + envelope * (4.5 * math.sin(norm_x * 16.0 - t * 20.0))
                if i == 0:
                    cr.move_to(px, py)
                else:
                    cr.line_to(px, py)
            cr.set_source_rgba(0.95, 0.90, 1.0, 0.90 * rint)
            cr.stroke()

            # Wave 3: Sub-Synaptic Resonance Filament (Razor Cyan)
            cr.set_line_width(0.7)
            for i in range(num_pts):
                px = x_start + i * dx
                norm_x = (float(i) / (num_pts - 1) - 0.5) * 2.0
                envelope = max(0.0, 1.0 - norm_x * norm_x)
                py = cy - envelope * (5.0 * math.sin(norm_x * 12.0 + t * 10.0))
                if i == 0:
                    cr.move_to(px, py)
                else:
                    cr.line_to(px, py)
            cr.set_source_rgba(0.0, 0.95, 1.0, 0.60 * rint)
            cr.stroke()

            # Center Synaptic Spark Node
            spark_r = 2.4 + 1.2 * math.sin(t * 18.0)
            cr.arc(cx, cy, spark_r, 0, 2 * math.pi)
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.95 * rint)
            cr.fill()

        elif morph == "morph-terminal":
            # Cybernetic Phosphor Streams cascading inside core
            cols = 7
            cdx = 36.0 / float(cols)
            cr.set_line_width(1.2)
            for c in range(cols):
                x = cx - 18.0 + (c + 0.5) * cdx
                offset = self.matrix_offsets[c % len(self.matrix_offsets)]
                h = 24.0 * (0.35 + 0.65 * math.sin(t * 3.0 + c * 0.8))
                y_top = cy - h / 2.0
                grad = cairo.LinearGradient(x, cy + 12, x, y_top)
                grad.add_color_stop_rgba(0.0, 0.0, 1.0, 0.4, 0.15)
                grad.add_color_stop_rgba(0.5, 0.0, 1.0, 0.6, 0.80 * rint)
                grad.add_color_stop_rgba(1.0, 0.8, 1.0, 0.9, 0.95 * rint)
                cr.set_source(grad)
                cr.move_to(x, cy + 12)
                cr.line_to(x, y_top)
                cr.stroke()
                cr.arc(x, y_top, 1.2, 0, 2 * math.pi)
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.90 * rint)
                cr.fill()

        elif morph == "morph-circle":
            # Sonar Radar Scan inside core
            cr.arc(cx, cy, 24, 0, 2 * math.pi)
            cr.set_source_rgba(0.0, 0.90, 1.0, 0.35 * rint)
            cr.stroke()
            cr.new_sub_path()
            cr.move_to(cx, cy)
            cr.arc(cx, cy, 26, self.radar_angle - 0.5, self.radar_angle)
            cr.close_path()
            rsw = cairo.RadialGradient(cx, cy, 2.0, cx, cy, 26.0)
            rsw.add_color_stop_rgba(0.0, 0.0, 0.9, 1.0, 0.70 * rint)
            rsw.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(rsw)
            cr.fill()

        elif morph == "morph-frameless":
            # Holographic Laser Scanner traversing inside core
            scan_y = cy - 20.0 + (abs((t * 24.0) % 40.0) - 20.0)
            cr.set_line_width(1.5)
            cr.move_to(cx - 24.0, scan_y)
            cr.line_to(cx + 24.0, scan_y)
            cr.set_source_rgba(0.7, 1.0, 1.0, 0.95 * rint)
            cr.stroke()
            smist = cairo.LinearGradient(0, scan_y - 8.0, 0, scan_y)
            smist.add_color_stop_rgba(0.0, 0.0, 0.5, 1.0, 0.0)
            smist.add_color_stop_rgba(1.0, 0.0, 0.9, 1.0, 0.35 * rint)
            cr.set_source(smist)
            cr.rectangle(cx - 24.0, scan_y - 8.0, 48.0, 8.0)
            cr.fill()

        elif morph == "morph-chamfer":
            # Crystalline Hexagonal Lattices interlocking inside core
            for ring in (1, 2):
                cr.new_sub_path()
                for corner in range(6):
                    ang = corner * (math.pi / 3.0) + t * (0.8 if ring == 1 else -0.8)
                    px = cx + ring * 10.0 * math.cos(ang)
                    py = cy + ring * 10.0 * math.sin(ang)
                    if corner == 0:
                        cr.move_to(px, py)
                    else:
                        cr.line_to(px, py)
                cr.close_path()
                cr.set_source_rgba(0.0, 1.0, 0.5, (0.85 if ring == 1 else 0.55) * rint)
                cr.set_line_width(1.2)
                cr.stroke()

        elif morph == "morph-swarm":
            # Swarm inter-node gravitational web
            cr.set_line_width(0.8)
            for i in range(len(satellite_coords)):
                for j in range(i + 1, len(satellite_coords)):
                    if (i + j) % 2 == 0:
                        cr.move_to(satellite_coords[i][0], satellite_coords[i][1])
                        cr.line_to(satellite_coords[j][0], satellite_coords[j][1])
                        cr.set_source_rgba(0.0, 1.0, 0.7, 0.35 * rint)
                        cr.stroke()

        else:
            # Speaking & Idle Harmonic Waveform inside core
            r_iris = 28.0 * iris_pulse
            steps = 40
            wave_w = r_iris * 1.85
            x_start = cx - wave_w / 2.0
            dx = wave_w / float(steps)
            cur_amp = max(0.12, amp) if morph == "morph-speech" else 0.18

            layers = [
                ((0.0, 0.50, 1.00), 0.45 * rint, 1.0, 0.0, 1.2 + 0.6 * amp, r_iris * 0.35),
                ((0.0, 1.00, 0.60), 0.75 * rint, 1.6, 1.2, 1.8 + 0.8 * amp, r_iris * 0.55),
                ((0.8, 1.00, 1.00), 1.00 * rint, 2.4, 2.4, 2.4 + 1.0 * amp, r_iris * 0.75),
            ]
            for col, alpha, freq_mul, phase_off, line_w, base_h in layers:
                cr.set_line_width(line_w)
                cr.set_source_rgba(col[0], col[1], col[2], alpha)
                cr.new_sub_path()
                for s in range(steps + 1):
                    wx = x_start + s * dx
                    norm = float(s) / float(steps)
                    env = math.sin(norm * math.pi)
                    wy = cy + math.sin(t * 8.0 * freq_mul + s * 0.35 + phase_off) * (base_h * cur_amp) * env
                    if s == 0:
                        cr.move_to(wx, wy)
                    else:
                        cr.line_to(wx, wy)
                cr.stroke()

        # 7. Central Radiant Core Node Glow
        core_glow = cairo.RadialGradient(cx, cy, 1.0, cx, cy, (28.0 * iris_pulse) * 0.90)
        cg_r = 0.0 * (1.0 - tf) + 0.35 * tf
        cg_g = 0.85 * (1.0 - tf) + 0.20 * tf
        cg_b = 1.0
        core_glow.add_color_stop_rgba(0.0, 0.85 + 0.15 * tf, 1.0, 1.0, 0.95)
        core_glow.add_color_stop_rgba(0.4, cg_r, cg_g, cg_b, (0.50 + 0.40 * amp + 0.25 * tf) * rint)
        core_glow.add_color_stop_rgba(1.0, cg_r * 0.4, cg_g * 0.3, 0.6, 0.0)
        cr.set_source(core_glow)
        cr.arc(cx, cy, (28.0 * iris_pulse) * 0.90, 0, 2 * math.pi)
        cr.fill()

    def render_neural_reactor(self, cr, bw, bh, glow):
        """
        Renders the active Sovereign Tool or Voice animation directly into the wallpaper canvas.
        Morphologies:
          1. morph-speech     -> Harmonic Synaptic Audio Waveform
          2. morph-terminal   -> Cybernetic Matrix Phosphor Grid
          3. morph-circle     -> Sonar Radar Scan Wavefronts
          4. morph-frameless  -> Holographic Laser Inspection Sweep
          5. morph-chamfer    -> Crystalline Hexagonal Optical Lattice
          6. morph-swarm      -> Tri-Node Gravitational Swarm Constellation
        """
        style_type = self.style_data.get("style", "oceanic")
        if style_type == "oceanic":
            self.render_mrflow_holographic_core(cr, bw, bh, glow)
            return

        morph = self.active_morphology
        rint = self.reactor_intensity * glow

        cr.set_operator(cairo.OPERATOR_SCREEN)

        if morph == "morph-speech":
            self._render_speech_wave(cr, bw, bh, rint)
        elif morph == "morph-terminal":
            self._render_terminal_grid(cr, bw, bh, rint)
        elif morph == "morph-circle":
            self._render_radar_sonar(cr, bw, bh, rint)
        elif morph == "morph-frameless":
            self._render_laser_sweep(cr, bw, bh, rint)
        elif morph == "morph-chamfer":
            self._render_crystal_lattice(cr, bw, bh, rint)
        elif morph == "morph-swarm":
            self._render_swarm_orbits(cr, bw, bh, rint)
        else:
            self._render_horizon_idle(cr, bw, bh, rint)

    def _render_speech_wave(self, cr, bw, bh, rint):
        """Harmonic Synaptic Audio Waveform undulating across the bottom horizon."""
        horizon_y = bh * 0.78
        base_amp = (8.0 + 28.0 * self.active_amplitude) * rint

        layers = [
            ((0.0, 0.75, 1.0), 0.30 * rint, 1.0, 0.0, 1.5),
            ((0.0, 1.0, 0.4), 0.50 * rint, 1.4, 1.2, 2.0),
            ((0.3, 1.0, 0.7), 0.85 * rint, 1.9, 2.4, 2.5),
        ]
        steps = 32
        dx = bw / float(steps)

        for col, alpha, freq_mul, phase_off, line_w in layers:
            cr.set_line_width(line_w)
            cr.set_source_rgba(col[0], col[1], col[2], alpha)
            cr.new_sub_path()
            for s in range(steps + 1):
                cur_x = s * dx
                norm_x = float(s) / float(steps)
                env = math.sin(norm_x * math.pi)
                cur_y = horizon_y + math.sin(self.t * 8.0 * freq_mul + s * 0.35 + phase_off) * base_amp * env
                if s == 0:
                    cr.move_to(cur_x, cur_y)
                else:
                    cr.line_to(cur_x, cur_y)
            cr.stroke()

        glow_rad = cairo.RadialGradient(bw * 0.5, horizon_y + 10.0, 10.0, bw * 0.5, horizon_y + 10.0, bw * 0.35)
        glow_rad.add_color_stop_rgba(0.0, 0.0, 1.0, 0.4, 0.28 * rint)
        glow_rad.add_color_stop_rgba(0.4, 0.0, 0.8, 1.0, 0.12 * rint)
        glow_rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(glow_rad)
        cr.paint()

    def _render_terminal_grid(self, cr, bw, bh, rint):
        """Cybernetic Phosphor Matrix Grid for terminal and shell execution."""
        cols = 20
        dx = bw / float(cols)
        bottom_y = bh * 0.95
        cr.set_line_width(1.6)

        # Baseline phosphor glow
        bglow = cairo.LinearGradient(0, bottom_y - 25, 0, bh)
        bglow.add_color_stop_rgba(0.0, 0.0, 1.0, 0.4, 0.25 * rint)
        bglow.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(bglow)
        cr.rectangle(0, bottom_y - 25, bw, 35)
        cr.fill()

        for c in range(cols):
            x = (c + 0.5) * dx
            offset = self.matrix_offsets[c % len(self.matrix_offsets)]
            h = bh * 0.50 * (0.35 + 0.65 * math.sin(self.t * 2.5 + c * 0.65))
            y_head = bottom_y - (offset / 100.0) * h

            grad = cairo.LinearGradient(x, y_head, x, bottom_y)
            grad.add_color_stop_rgba(0.0, 0.7, 1.0, 0.8, 0.95 * rint)
            grad.add_color_stop_rgba(0.35, 0.0, 1.0, 0.4, 0.50 * rint)
            grad.add_color_stop_rgba(1.0, 0.0, 0.2, 0.1, 0.0)
            cr.set_source(grad)
            cr.move_to(x, bottom_y)
            cr.line_to(x, y_head)
            cr.stroke()

            node_r = 2.2 + 1.2 * math.sin(self.t * 4.0 + c)
            cr.arc(x, y_head, node_r, 0, 2 * math.pi)
            cr.set_source_rgba(0.85, 1.0, 0.9, 0.85 * rint)
            cr.fill()

    def _render_radar_sonar(self, cr, bw, bh, rint):
        """Expanding Sonar Radar wavefronts for Search, Grep, Web & Thinking."""
        cx = bw * 0.5
        cy = bh * 0.74
        max_r = bw * 0.38

        cr.set_line_width(1.6)
        for i in range(4):
            r = ((self.t * 28.0 + i * (max_r / 4.0)) % max_r) + 8.0
            norm_r = r / max_r
            alpha = (1.0 - norm_r) * 0.70 * rint
            cr.arc(cx, cy, r, 0, 2 * math.pi)
            cr.set_source_rgba(0.0, 0.92, 1.0, alpha)
            cr.stroke()

        cr.new_sub_path()
        cr.move_to(cx, cy)
        cr.arc(cx, cy, max_r * 0.75, self.radar_angle - 0.45, self.radar_angle)
        cr.close_path()
        rad = cairo.RadialGradient(cx, cy, 5.0, cx, cy, max_r * 0.75)
        rad.add_color_stop_rgba(0.0, 0.0, 1.0, 0.4, 0.40 * rint)
        rad.add_color_stop_rgba(0.7, 0.0, 0.85, 1.0, 0.15 * rint)
        rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(rad)
        cr.fill()

        cr.arc(cx, cy, 4.0, 0, 2 * math.pi)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.95 * rint)
        cr.fill()

    def _render_laser_sweep(self, cr, bw, bh, rint):
        """Holographic Laser Inspection Sweep for reading and inspecting files."""
        y = bh * self.laser_scan_y
        cr.set_line_width(2.0)

        cr.move_to(0, y)
        cr.line_to(bw, y)
        cr.set_source_rgba(0.7, 1.0, 1.0, 0.90 * rint)
        cr.stroke()

        mist_h = 24.0
        grad = cairo.LinearGradient(0, y - mist_h * self.laser_scan_dir, 0, y)
        grad.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, 0.0)
        grad.add_color_stop_rgba(1.0, 0.0, 0.85, 1.0, 0.25 * rint)
        cr.set_source(grad)
        cr.rectangle(0, min(y, y - mist_h * self.laser_scan_dir), bw, mist_h)
        cr.fill()

        ticks = 24
        tdx = bw / float(ticks)
        cr.set_line_width(1.0)
        for i in range(ticks + 1):
            tx = i * tdx
            th = 4.0 if i % 4 == 0 else 2.0
            cr.move_to(tx, y - th)
            cr.line_to(tx, y + th)
        cr.set_source_rgba(0.0, 1.0, 0.5, 0.65 * rint)
        cr.stroke()

    def _render_crystal_lattice(self, cr, bw, bh, rint):
        """Crystalline Hexagonal Optical Lattice for modifying and writing code."""
        cx = bw * 0.5
        cy = bh * 0.70
        cr.set_line_width(1.4)

        # Central crystalline core glow
        rad = cairo.RadialGradient(cx, cy, 2.0, cx, cy, bw * 0.15)
        rad.add_color_stop_rgba(0.0, 0.0, 1.0, 0.5, 0.40 * rint)
        rad.add_color_stop_rgba(0.5, 0.0, 0.8, 1.0, 0.15 * rint)
        rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
        cr.set_source(rad)
        cr.paint()

        hex_r = 30.0
        rings = 3
        for ring in range(1, rings + 1):
            cur_r = hex_r * ring * (0.95 + 0.05 * math.sin(self.t * 3.0 + ring))
            alpha = (1.0 - (ring / float(rings + 1))) * 0.75 * rint
            cr.new_sub_path()
            for corner in range(6):
                ang = corner * (math.pi / 3.0) + self.t * 0.5 * (1.0 if ring % 2 == 0 else -1.0)
                px = cx + cur_r * math.cos(ang)
                py = cy + cur_r * math.sin(ang) * 0.65
                if corner == 0:
                    cr.move_to(px, py)
                else:
                    cr.line_to(px, py)
                cr.arc(px, py, 2.2, 0, 2 * math.pi)
            cr.close_path()
            cr.set_source_rgba(0.0, 1.0, 0.45, alpha)
            cr.stroke()

    def _render_swarm_orbits(self, cr, bw, bh, rint):
        """Tri-Node Gravitational Swarm Constellation for subagents and swarm tasks."""
        cx = bw * 0.5
        cy = bh * 0.70
        orbs = [
            (0.0, 1.0, 0.4, bw * 0.16, 1.0, 0.0, 4.0),
            (0.0, 0.9, 1.0, bw * 0.22, -0.8, 1.5, 3.5),
            (0.7, 0.3, 1.0, bw * 0.27, 0.6, 3.0, 3.0),
        ]
        coords = []
        for r, g, b, radius, spd, phase, size in orbs:
            ang = self.swarm_phase * spd + phase
            ox = cx + radius * math.cos(ang)
            oy = cy + radius * math.sin(ang) * 0.55
            coords.append((ox, oy, r, g, b, size))

        # Dynamic inter-node gravitational web
        cr.set_line_width(0.9)
        for i in range(len(coords)):
            for j in range(i + 1, len(coords)):
                cr.move_to(coords[i][0], coords[i][1])
                cr.line_to(coords[j][0], coords[j][1])
                cr.set_source_rgba(0.0, 1.0, 0.7, 0.22 * rint)
                cr.stroke()

        cr.set_line_width(1.2)
        for r, g, b, radius, spd, phase, size in orbs:
            cr.arc(cx, cy, radius, 0, 2 * math.pi)
            cr.set_source_rgba(r, g, b, 0.12 * rint)
            cr.stroke()

        for ox, oy, r, g, b, size in coords:
            rad = cairo.RadialGradient(ox, oy, 1.0, ox, oy, size * 3.2)
            rad.add_color_stop_rgba(0.0, r, g, b, 0.90 * rint)
            rad.add_color_stop_rgba(0.5, r, g, b, 0.40 * rint)
            rad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
            cr.set_source(rad)
            cr.arc(ox, oy, size * 3.2, 0, 2 * math.pi)
            cr.fill()

    def _render_horizon_idle(self, cr, bw, bh, rint):
        """Soft resting horizon breathing wave."""
        horizon_y = bh * 0.80
        breathe = 3.0 * math.sin(self.t * 1.5)
        cr.set_line_width(1.0)
        cr.move_to(0, horizon_y + breathe)
        cr.line_to(bw, horizon_y - breathe)
        cr.set_source_rgba(0.0, 1.0, 0.4, 0.18 * rint)
        cr.stroke()

    def on_draw(self, widget, cr):
        scale_x = float(self.screen_w) / float(self.buf_w)
        scale_y = float(self.screen_h) / float(self.buf_h)

        cr.save()
        cr.scale(scale_x, scale_y)
        cr.set_source_surface(self.surface_buf, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint()
        cr.restore()
        return True

def main():
    if "--stop" in sys.argv or "-k" in sys.argv:
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                os.remove(PID_FILE)
                print("✅ Flowork Living Motion Wallpaper stopped.")
            except Exception as e:
                print(f"Notice: {e}")
        return

    if "--status" in sys.argv:
        cfg = load_motion_config()
        is_running = False
        pid = None
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                is_running = True
            except OSError:
                pass
        print(json.dumps({
            "running": is_running,
            "pid": pid,
            "config": cfg,
            "available_styles": list(MOTION_STYLES.keys())
        }, indent=2))
        return

    for i, a in enumerate(sys.argv):
        if a in ("--style", "-s") and i + 1 < len(sys.argv):
            target_style = sys.argv[i + 1]
            if target_style in MOTION_STYLES or target_style == "auto":
                cfg = load_motion_config()
                cfg["style"] = target_style
                save_motion_config(cfg)
                print(f"✅ Motion style configured to: {target_style}")
                return
            else:
                print(f"❌ Unknown style '{target_style}'. Available: {list(MOTION_STYLES.keys())}")
                return

    if "--toggle" in sys.argv:
        cfg = load_motion_config()
        new_state = not cfg.get("enabled", True)
        cfg["enabled"] = new_state
        save_motion_config(cfg)
        if not new_state:
            if os.path.exists(PID_FILE):
                try:
                    with open(PID_FILE, "r") as f:
                        old_pid = int(f.read().strip())
                    os.kill(old_pid, signal.SIGTERM)
                    os.remove(PID_FILE)
                except OSError:
                    pass
            print("✅ Flowork Living Motion Wallpaper toggled OFF.")
            return
        else:
            print("✅ Flowork Living Motion Wallpaper toggled ON. Launching daemon...")

    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            print(f"Flowork Motion Wallpaper already running (PID {old_pid}).")
            return
        except OSError:
            pass

    # Save PID
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    print("⚡ Flowork Living Motion Wallpaper running (Ultra-Soft Mode 3.0)...")
    app = FloworkMotionAmbient()
    app.show_all()

    def handle_signal(sig, frame):
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception:
            pass
        Gtk.main_quit()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    Gtk.main()

if __name__ == "__main__":
    main()
