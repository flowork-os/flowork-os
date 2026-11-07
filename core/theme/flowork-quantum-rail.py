#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Quantum Glass Rail (The Sovereign Left HUD)
# Standalone Floating Frosted Glass Command Rail
# Replaces traditional docks and taskbars with a sleek, vertical agent-native HUD.
# =============================================================================

import os
import sys
import signal
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

PID_FILE = f"/run/user/{os.getuid()}/flowork-quantum-rail.pid"

def check_single_instance():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, signal.SIGTERM)
            try:
                os.remove(PID_FILE)
            except OSError:
                pass
        except Exception:
            pass
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

class QuantumRailWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Flowork Quantum Rail")
        self.set_role("quantum_rail")

        # Window properties for sovereign HUD
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)

        # RGBA for true glass transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

        self.rail_width = 54
        self.rail_height = 640
        self.margin_left = 14

        # Calculate position on primary display
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geom = monitor.get_geometry()
        pos_y = (geom.height - self.rail_height) // 2

        self.set_default_size(self.rail_width, self.rail_height)
        self.move(self.margin_left, max(pos_y, 40))

        self.current_desktop = 0
        self.sphere_buttons = []

        self._setup_css()
        self._build_ui()

        # Connect cleanup
        self.connect("destroy", self._on_destroy)

        # Periodic desktop & agent status watchdog (every 300ms)
        GLib.timeout_add(300, self._update_state)

    def _setup_css(self):
        css = b'''
        window {
            background-color: transparent;
        }

        .quantum-rail-panel {
            background-color: rgba(6, 10, 18, 0.65);
            border: 1px solid rgba(0, 242, 254, 0.35);
            border-radius: 27px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.25);
            padding: 12px 6px;
        }

        .monolith-btn {
            background: linear-gradient(180deg, rgba(0, 242, 254, 0.25) 0%, rgba(0, 255, 136, 0.15) 100%);
            border: 1px solid rgba(0, 242, 254, 0.6);
            border-radius: 18px;
            color: #00f2fe;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            font-weight: 800;
            padding: 10px 4px;
            transition: all 180ms ease;
        }
        .monolith-btn:hover {
            background: linear-gradient(180deg, rgba(0, 242, 254, 0.45) 0%, rgba(0, 255, 136, 0.3) 100%);
            border-color: #00ff88;
            box-shadow: 0 0 16px rgba(0, 242, 254, 0.6);
            color: #ffffff;
        }

        .divider {
            background-color: rgba(255, 255, 255, 0.12);
            margin: 6px 4px;
            min-height: 1px;
        }

        .sphere-btn {
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            color: #7b93b8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            font-weight: 700;
            padding: 8px 0px;
            transition: all 140ms ease;
        }
        .sphere-btn:hover {
            background-color: rgba(0, 242, 254, 0.15);
            border-color: rgba(0, 242, 254, 0.5);
            color: #00f2fe;
        }
        .sphere-active {
            background: linear-gradient(180deg, rgba(0, 242, 254, 0.3) 0%, rgba(13, 22, 38, 0.6) 100%);
            border: 1px solid #00f2fe;
            color: #ffffff;
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.4);
        }

        .agent-orb {
            background: radial-gradient(circle, #00ff88 0%, #008855 70%);
            border: 1px solid #00ff88;
            border-radius: 50%;
            min-width: 14px;
            min-height: 14px;
            box-shadow: 0 0 10px #00ff88;
            margin: 6px 4px;
            transition: all 200ms ease;
        }
        .agent-orb-busy {
            background: radial-gradient(circle, #00f2fe 0%, #0077aa 70%);
            border-color: #00f2fe;
            box-shadow: 0 0 14px #00f2fe;
        }
        .agent-orb-amber {
            background: radial-gradient(circle, #ffb703 0%, #bb7700 70%);
            border-color: #ffb703;
            box-shadow: 0 0 12px #ffb703;
        }

        .tool-btn {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 12px;
            color: #8c9cb8;
            font-size: 15px;
            padding: 7px 0px;
            transition: all 140ms ease;
        }
        .tool-btn:hover {
            background-color: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
            color: #ffffff;
        }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.card.get_style_context().add_class('quantum-rail-panel')
        self.add(self.card)

        # 1. Monolith Emblem [F_] (Triggers Flowork Orbit)
        self.monolith_btn = Gtk.Button(label="F_")
        self.monolith_btn.get_style_context().add_class('monolith-btn')
        self.monolith_btn.set_tooltip_text("Flowork Sovereign Orbit (Super + Space)")
        self.monolith_btn.connect("clicked", self._on_orbit_clicked)
        self.card.pack_start(self.monolith_btn, False, False, 0)

        # Top Divider
        div1 = Gtk.Box()
        div1.get_style_context().add_class('divider')
        self.card.pack_start(div1, False, False, 2)

        # 2. Cognitive Domain Spheres (Ω Core, λ Code, Ψ Agent, ◈ Studio)
        spheres = [
            ("Ω", "Sphere 0: Core Terminal & Root [Super+1]", 0),
            ("λ", "Sphere 1: Code IDE & Dev [Super+2]", 1),
            ("Ψ", "Sphere 2: Mr. Flow Swarm & Agents [Super+3]", 2),
            ("◈", "Sphere 3: Studio & Creative Suite [Super+4]", 3)
        ]

        self.sphere_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for symbol, tooltip, desk_idx in spheres:
            btn = Gtk.Button(label=symbol)
            btn.get_style_context().add_class('sphere-btn')
            btn.set_tooltip_text(tooltip)
            btn.connect("clicked", self._on_sphere_clicked, desk_idx)
            self.sphere_box.pack_start(btn, False, False, 0)
            self.sphere_buttons.append(btn)
        self.card.pack_start(self.sphere_box, False, False, 0)

        # Mid Divider
        div2 = Gtk.Box()
        div2.get_style_context().add_class('divider')
        self.card.pack_start(div2, False, False, 2)

        # 3. Agent Cognitive Core Orb
        self.agent_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.agent_orb = Gtk.Box()
        self.agent_orb.get_style_context().add_class('agent-orb')
        self.agent_orb_btn = Gtk.Button()
        self.agent_orb_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.agent_orb_btn.add(self.agent_orb)
        self.agent_orb_btn.set_tooltip_text("Mr. Flow Cognitive Core (Idle & Ready)")
        self.agent_orb_btn.connect("clicked", self._on_agent_clicked)
        self.agent_box.pack_start(self.agent_orb_btn, False, False, 0)
        self.card.pack_start(self.agent_box, False, False, 4)

        # Expand space
        spacer = Gtk.Box()
        self.card.pack_start(spacer, True, True, 0)

        # 4. Sovereign Quick Tools (Terminal, Nemo Files, Connector Telemetry, Power)
        tools = [
            ("💻", "Terminal Console", self._on_tool_terminal),
            ("📁", "Nemo Vault Files", self._on_tool_files),
            ("📡", "Connector Matrix (:9099)", self._on_tool_connector),
            ("⚙", "Flowork Settings", self._on_tool_settings),
            ("⏻", "Sovereign Power / Session", self._on_tool_power)
        ]

        for icon, tooltip, callback in tools:
            btn = Gtk.Button(label=icon)
            btn.get_style_context().add_class('tool-btn')
            btn.set_tooltip_text(tooltip)
            btn.connect("clicked", callback)
            self.card.pack_start(btn, False, False, 0)

    def _on_orbit_clicked(self, widget):
        subprocess.Popen(["/usr/local/bin/flowork-orbit"])

    def _on_sphere_clicked(self, widget, desk_idx):
        try:
            subprocess.run(["wmctrl", "-s", str(desk_idx)], check=False)
            self._update_desktop_highlight(desk_idx)
        except Exception:
            pass

    def _on_agent_clicked(self, widget):
        # Open instant Mr. Flow terminal prompt
        cmd = "x-terminal-emulator -e bash -c 'mrflow; bash' &"
        os.system(cmd)

    def _on_tool_terminal(self, widget):
        os.system("x-terminal-emulator &")

    def _on_tool_files(self, widget):
        os.system("nemo /opt/floworkos &")

    def _on_tool_connector(self, widget):
        os.system("google-chrome --app=http://127.0.0.1:9099/gui &")

    def _on_tool_settings(self, widget):
        os.system("xfce4-settings-manager &")

    def _on_tool_power(self, widget):
        os.system("xfce4-session-logout &")

    def _update_desktop_highlight(self, current):
        for idx, btn in enumerate(self.sphere_buttons):
            ctx = btn.get_style_context()
            if idx == current:
                if not ctx.has_class('sphere-active'):
                    ctx.add_class('sphere-active')
            else:
                if ctx.has_class('sphere-active'):
                    ctx.remove_class('sphere-active')

    def _update_state(self):
        # 1. Update current desktop
        try:
            out = subprocess.check_output(["xdotool", "get_desktop"], stderr=subprocess.DEVNULL).decode().strip()
            desk = int(out)
            if desk != self.current_desktop:
                self.current_desktop = desk
                self._update_desktop_highlight(desk)
        except Exception:
            pass

        # 2. Update agent orb status
        try:
            active_trigger_file = "/tmp/flowork_active_trigger.json"
            ctx = self.agent_orb.get_style_context()
            if os.path.exists(active_trigger_file):
                if not ctx.has_class('agent-orb-busy'):
                    ctx.add_class('agent-orb-busy')
                if ctx.has_class('agent-orb'):
                    ctx.remove_class('agent-orb')
                self.agent_orb_btn.set_tooltip_text("Mr. Flow: Autonomous Cognitive Cycle Active")
            else:
                if ctx.has_class('agent-orb-busy'):
                    ctx.remove_class('agent-orb-busy')
                if not ctx.has_class('agent-orb'):
                    ctx.add_class('agent-orb')
                self.agent_orb_btn.set_tooltip_text("Mr. Flow Cognitive Core (Idle & Ready)")
        except Exception:
            pass

        return True

    def _on_destroy(self, widget):
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except OSError:
            pass
        Gtk.main_quit()

def main():
    check_single_instance()
    win = QuantumRailWindow()
    win.show_all()
    # Reserve strut partial so windows don't overlap left rail
    Gtk.main()

if __name__ == '__main__':
    main()
