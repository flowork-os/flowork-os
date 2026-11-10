#!/usr/bin/env python3
"""
Mr. Flow Sovereign Companion — Desktop Header Systray Indicator & Controller
100% Native English, Zero-Hardcode Path Doctrine, High-Speed Socket IPC.
Docked in top desktop header right next to Sovereign Connector.
"""

import sys
import os
import time
import json
import socket
import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib

USER = os.environ.get("USER") or os.environ.get("LOGNAME") or "operator"
HOME = os.path.expanduser("~")
SOCKET_PATH = f"/tmp/mrflow-sidebar-{USER}.sock"
ICON_PATH = "/opt/floworkos/icons/mrflow-agent.png"


def send_socket_command(action, extra=None, timeout=1.5):
    """Sends action to sidebar socket and returns decoded response or None."""
    if not os.path.exists(SOCKET_PATH):
        return None
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(timeout)
        client.connect(SOCKET_PATH)
        payload = {"action": action}
        if extra and isinstance(extra, dict):
            payload.update(extra)
        client.sendall(json.dumps(payload).encode("utf-8") + b"\n")
        resp = client.recv(4096).decode("utf-8").strip()
        client.close()
        return resp
    except Exception:
        return None


class MrFlowTrayApplet:
    def __init__(self):
        self.sidebar_state = {
            "online": False,
            "is_open": False,
            "is_pinned": False,
            "hover_to_open": False,
            "is_busy": False
        }

        # Initialize Gtk StatusIcon
        self.icon = Gtk.StatusIcon()
        self._load_icon()

        # Connect click handlers
        self.icon.connect("activate", self.on_left_click)
        self.icon.connect("popup-menu", self.on_right_click)

        # Polling status loop every 2 seconds
        GLib.timeout_add(2000, self.poll_status)
        self.poll_status()

    def _load_icon(self):
        try:
            if os.path.exists(ICON_PATH):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(ICON_PATH, 22, 22, True)
                self.icon.set_from_pixbuf(pixbuf)
            else:
                self.icon.set_from_icon_name("dialog-information")
        except Exception:
            self.icon.set_from_icon_name("dialog-information")
        self.icon.set_visible(True)

    def poll_status(self):
        resp = send_socket_command("status", timeout=0.8)
        if resp:
            try:
                data = json.loads(resp)
                self.sidebar_state["online"] = True
                self.sidebar_state["is_open"] = data.get("is_open", False)
                self.sidebar_state["is_pinned"] = data.get("is_pinned", False)
                self.sidebar_state["hover_to_open"] = data.get("hover_to_open", False)
                self.sidebar_state["is_busy"] = data.get("is_busy", False)

                status_txt = "Generating / Working ⚡" if self.sidebar_state["is_busy"] else "Ready"
                mode_txt = "Hover Peek" if self.sidebar_state["hover_to_open"] else "Manual Click"
                dock_txt = "Pinned (Docked)" if self.sidebar_state["is_pinned"] else "Floating"

                tooltip = (
                    f"🤖 Mr. Flow AI Companion [{status_txt}]\n"
                    f"State: {'Expanded' if self.sidebar_state['is_open'] else 'Collapsed'}\n"
                    f"Mode: {mode_txt} • {dock_txt}\n"
                    f"Click: Toggle Sidebar (Super+C)"
                )
                self.icon.set_tooltip_text(tooltip)
                return True
            except Exception:
                pass

        self.sidebar_state["online"] = False
        self.icon.set_tooltip_text("🤖 Mr. Flow AI Companion [Offline - Click to launch]")
        return True

    def on_left_click(self, icon):
        """Single click toggles sidebar immediately."""
        resp = send_socket_command("toggle", timeout=1.0)
        if not resp:
            # If socket failed, attempt to start the service
            subprocess.run(["systemctl", "--user", "start", "flowork-mrflow-sidebar.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            send_socket_command("show", timeout=1.0)
        self.poll_status()

    def on_right_click(self, icon, button, activate_time):
        """Right click shows rich control popup menu."""
        menu = self.build_menu()
        menu.popup(None, None, self.icon.position_menu, icon, button, activate_time)

    def build_menu(self):
        self.poll_status()
        menu = Gtk.Menu()

        online = self.sidebar_state["online"]
        busy = self.sidebar_state["is_busy"]
        is_open = self.sidebar_state["is_open"]
        is_pinned = self.sidebar_state["is_pinned"]
        hover_peek = self.sidebar_state["hover_to_open"]

        # 1. Title Item
        status_symbol = "⚡" if busy else ("🟢" if online else "🔴")
        status_word = "GENERATING" if busy else ("READY" if online else "OFFLINE")
        title_item = Gtk.MenuItem(label=f"🤖 Mr. Flow Companion [{status_symbol} {status_word}]")
        title_item.set_sensitive(False)
        menu.append(title_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 2. Toggle Sidebar
        toggle_label = "◀ Collapse Sidebar" if is_open else "▶ Expand Sidebar (Super+C)"
        toggle_item = Gtk.MenuItem(label=toggle_label)
        toggle_item.connect("activate", lambda _: self.on_left_click(None))
        menu.append(toggle_item)

        # 3. Mode Toggles: Auto-Peek Hover
        peek_chk = "✓ " if hover_peek else "   "
        peek_item = Gtk.MenuItem(label=f"{peek_chk}Auto-Peek on Mouse Hover")
        peek_item.connect("activate", lambda _: self._toggle_hover_peek())
        menu.append(peek_item)

        # 4. Mode Toggles: Docked Workspace Pin
        pin_chk = "✓ " if is_pinned else "   "
        pin_item = Gtk.MenuItem(label=f"{pin_chk}Pin to Workspace (Docked)")
        pin_item.connect("activate", lambda _: self._toggle_pin())
        menu.append(pin_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 5. Quick Actions: New Chat & Terminal
        new_chat_item = Gtk.MenuItem(label="➕ New Chat Session (Ctrl+L)")
        new_chat_item.connect("activate", lambda _: self._new_chat())
        menu.append(new_chat_item)

        term_item = Gtk.MenuItem(label="📟 Open in Alacritty Terminal CLI")
        term_item.connect("activate", lambda _: subprocess.Popen(["/usr/local/bin/mrflow-terminal"], cwd=HOME, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        menu.append(term_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 6. Service Management
        restart_item = Gtk.MenuItem(label="🔄 Restart Sidebar Daemon")
        restart_item.connect("activate", lambda _: subprocess.Popen(["systemctl", "--user", "restart", "flowork-mrflow-sidebar.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        menu.append(restart_item)

        menu.show_all()
        return menu

    def _toggle_hover_peek(self):
        send_socket_command("toggle_hover_peek")
        GLib.timeout_add(200, self.poll_status)

    def _toggle_pin(self):
        send_socket_command("toggle_pin")
        GLib.timeout_add(200, self.poll_status)

    def _new_chat(self):
        send_socket_command("new_chat")
        send_socket_command("show")
        GLib.timeout_add(200, self.poll_status)


def wait_for_display_and_panel():
    """Waits for X11 server and desktop panel before initializing Gtk StatusIcon."""
    if "DISPLAY" not in os.environ or not os.environ["DISPLAY"]:
        os.environ["DISPLAY"] = ":0"
    
    for attempt in range(45):
        try:
            res = subprocess.run(["xset", "q"], capture_output=True, env=os.environ)
            if res.returncode == 0:
                p_check = subprocess.run(["pgrep", "-f", "xfce4-panel|flowork"], capture_output=True)
                if p_check.returncode == 0:
                    time.sleep(1.5)
                    return True
        except Exception:
            pass
        time.sleep(1)
    return True


def main():
    wait_for_display_and_panel()
    import fcntl
    lock_file = open(f"/tmp/mrflow-tray-{USER}.lock", "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sys.exit(0)

    applet = MrFlowTrayApplet()
    Gtk.main()


if __name__ == "__main__":
    main()
