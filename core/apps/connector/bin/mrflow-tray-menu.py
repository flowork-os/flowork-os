#!/usr/bin/env python3
"""
MrFlow Sovereign Router - Desktop Header Systray Menu with Blinking Neon Indicator
100% English menu, zero Indonesian text, no hidden connector options.
Robust Display and Panel Handshake for Instant and Reliable Tray Binding.
"""

import sys
import os
import time
import subprocess
import urllib.request
import json
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

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

def get_base_dir():
    if os.environ.get("FLOWORK_CONNECTOR_DIR") and os.path.isdir(os.environ["FLOWORK_CONNECTOR_DIR"]):
        return os.environ["FLOWORK_CONNECTOR_DIR"]
    if os.environ.get("MRFLOW_CONNECTOR_DIR") and os.path.isdir(os.environ["MRFLOW_CONNECTOR_DIR"]):
        return os.environ["MRFLOW_CONNECTOR_DIR"]
    script_path = os.path.realpath(__file__)
    candidate = os.path.abspath(os.path.join(os.path.dirname(script_path), ".."))
    if os.path.exists(os.path.join(candidate, "bin", "flowork-connector")) or os.path.exists(os.path.join(candidate, "gui", "assets", "tray_bright.png")):
        return candidate
    for p in [os.path.expanduser("~/connector"), "/opt/floworkos/apps/connector"]:
        if os.path.exists(os.path.join(p, "bin", "flowork-connector")) or os.path.exists(os.path.join(p, "gui", "assets", "tray_bright.png")):
            return p
    return candidate

BASE_DIR = get_base_dir()
ASSETS_DIR = os.path.join(BASE_DIR, "gui", "assets")
ICON_BRIGHT = os.path.join(ASSETS_DIR, "tray_bright.png")
ICON_DIM = os.path.join(ASSETS_DIR, "tray_dim.png")

PORT = 9099
API_STATUS = f"http://127.0.0.1:{PORT}/auth/router/status"
API_PROVIDER = f"http://127.0.0.1:{PORT}/auth/router/provider-config"
API_SYNC = f"http://127.0.0.1:{PORT}/auth/router/sync-cloud"
API_CLEAR_CD = f"http://127.0.0.1:{PORT}/auth/router/clear-cooldown"

class MrFlowDesktopHeaderMenu:
    def __init__(self):
        self.is_bright = True
        self.router_state = {
            "online": False,
            "user": os.environ.get("USER", "operator"),
            "tier": "enterprise",
            "active_provider": "connector",
            "total_accounts": 0,
            "healthy_count": 0,
            "cooldown_count": 0,
            "active_email": ""
        }

        # Initialize Gtk StatusIcon in the desktop header
        self.icon = Gtk.StatusIcon()
        self.icon.set_from_file(ICON_BRIGHT)
        self.icon.set_tooltip_text("MrFlow Sovereign Router (Initializing...)")
        self.icon.set_visible(True)

        # Connect click handlers
        self.icon.connect("activate", self.on_click)
        self.icon.connect("popup-menu", self.on_popup_menu)

        # Continuous blinking timer: alternates icon every 500ms
        GLib.timeout_add(500, self.blink_tick)

        # Watchdog for tray docking resilience every 3 seconds
        GLib.timeout_add(3000, self.watchdog_tick)

        # Poll router status every 4 seconds
        GLib.timeout_add(4000, self.fetch_status)
        self.fetch_status()

    def watchdog_tick(self):
        """Ensures the tray icon is cleanly docked and visible in the desktop panel."""
        if hasattr(self.icon, "is_embedded") and not self.icon.is_embedded():
            try:
                self.icon.set_visible(False)
                self.icon.set_from_file(ICON_BRIGHT)
                self.icon.set_visible(True)
            except Exception:
                pass
        return True

    def blink_tick(self):
        """Blinks the icon in the desktop header bar."""
        if hasattr(self.icon, "is_embedded") and not self.icon.is_embedded():
            return True
        self.is_bright = not self.is_bright
        current_icon = ICON_BRIGHT if self.is_bright else ICON_DIM
        try:
            self.icon.set_from_file(current_icon)
        except Exception:
            pass
        return True

    def fetch_status(self):
        """Fetches live router metrics to update tooltip and menu labels."""
        try:
            req = urllib.request.Request(API_STATUS, headers={"User-Agent": "MrFlow-DesktopHeader/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.router_state["online"] = True
                self.router_state["active_provider"] = data.get("active_provider", "connector")
                self.router_state["total_accounts"] = data.get("total_accounts", 0)
                self.router_state["healthy_count"] = data.get("healthy_count", 0)
                self.router_state["cooldown_count"] = data.get("cooldown_count", 0)
                self.router_state["active_email"] = data.get("active_email", "")

                user = data.get("user") or {}
                if user:
                    self.router_state["user"] = user.get("username", "Operator")
                    self.router_state["tier"] = user.get("tier", "enterprise")

                prov = self.router_state["active_provider"].upper()
                total = self.router_state["total_accounts"]
                healthy = self.router_state["healthy_count"]
                cd = self.router_state["cooldown_count"]

                tooltip = f"⚡ MrFlow Sovereign Router [ONLINE]\nEngine: {prov}\nAccounts: {healthy}/{total} Ready ({cd} Cooldown)"
                self.icon.set_tooltip_text(tooltip)
        except Exception:
            self.router_state["online"] = False
            self.icon.set_tooltip_text("⚡ MrFlow Sovereign Router [OFFLINE - Click to Launch]")
        return True

    def build_menu(self):
        """Builds the 100% English native popup menu."""
        self.fetch_status()
        menu = Gtk.Menu()

        prov = self.router_state["active_provider"].lower()
        online_txt = "ONLINE" if self.router_state["online"] else "OFFLINE"
        healthy = self.router_state["healthy_count"]
        total = self.router_state["total_accounts"]

        # 1. Header Banner
        title_item = Gtk.MenuItem(label=f"⚡ MrFlow Sovereign Router: [{online_txt}]")
        title_item.set_sensitive(False)
        menu.append(title_item)

        # 2. Account & Passport Status
        user_item = Gtk.MenuItem(label=f"👤 @{self.router_state['user']} [{self.router_state['tier'].upper()}] • {healthy}/{total} Accounts Ready")
        user_item.set_sensitive(False)
        menu.append(user_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 3. Open Sidebar Chat, GUI Dashboard & Terminal CLI
        chat_item = Gtk.MenuItem(label="💬 Toggle Mr. Flow Sidebar Chat (Super+C)")
        chat_item.connect("activate", lambda _: self.launch_sidebar())
        menu.append(chat_item)

        side_item = Gtk.MenuItem(label="💬 Toggle Mr. Flow Companion")
        side_item.connect("activate", lambda _: subprocess.Popen(["/usr/local/bin/mrflow-sidebar", "toggle"]))
        menu.append(side_item)

        dash_item = Gtk.MenuItem(label="🪟 Open Router Control Panel")
        dash_item.connect("activate", lambda _: self.launch_dashboard())
        menu.append(dash_item)

        cli_item = Gtk.MenuItem(label="🤖 Open MrFlow Terminal CLI")
        cli_item.connect("activate", lambda _: self.launch_cli())
        menu.append(cli_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 4. Inference Engine Selector (Directly visible, not hidden)
        engine_label = f"🔀 Active Engine: {prov.upper()}"
        engine_menu_item = Gtk.MenuItem(label=engine_label)
        engine_sub = Gtk.Menu()

        # Engine A: Sovereign Connector
        chk_conn = "● " if prov == "connector" else "○ "
        item_conn = Gtk.MenuItem(label=f"{chk_conn}Sovereign Connector (Google Pro Pool)")
        item_conn.connect("activate", lambda _: self.switch_provider("connector"))
        engine_sub.append(item_conn)

        # Engine B: Ollama Local
        chk_ollama = "● " if prov == "ollama" else "○ "
        item_ollama = Gtk.MenuItem(label=f"{chk_ollama}Ollama Local Engine (Offline GPU)")
        item_ollama.connect("activate", lambda _: self.switch_provider("ollama"))
        engine_sub.append(item_ollama)

        # Engine C: 9Router Universal Gateway
        chk_9r = "● " if prov == "9router" else "○ "
        item_9r = Gtk.MenuItem(label=f"{chk_9r}9Router Universal Gateway (Proxy)")
        item_9r.connect("activate", lambda _: self.switch_provider("9router"))
        engine_sub.append(item_9r)

        engine_menu_item.set_submenu(engine_sub)
        menu.append(engine_menu_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 5. Cloud Vault Sync
        sync_item = Gtk.MenuItem(label="☁️ Sync Cloud Vault (Download Accounts)")
        sync_item.connect("activate", lambda _: self.sync_vault())
        menu.append(sync_item)

        # 6. Reset 429 Limit Cooldowns
        clear_item = Gtk.MenuItem(label="⚡ Reset All 429 Quota Cooldowns")
        clear_item.connect("activate", lambda _: self.clear_cooldowns())
        menu.append(clear_item)

        # 7. Refresh Status
        ref_item = Gtk.MenuItem(label="🔄 Refresh Router Status")
        ref_item.connect("activate", lambda _: self.fetch_status())
        menu.append(ref_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 8. Quit
        quit_item = Gtk.MenuItem(label="❌ Exit Desktop Header Indicator")
        quit_item.connect("activate", lambda _: Gtk.main_quit())
        menu.append(quit_item)

        menu.show_all()
        return menu

    def on_click(self, icon):
        """Triggered on left-click on the desktop header icon."""
        menu = self.build_menu()
        menu.popup(None, None, self.icon.position_menu, icon, 1, Gtk.get_current_event_time())

    def on_popup_menu(self, icon, button, time):
        """Triggered on right-click on the desktop header icon."""
        menu = self.build_menu()
        menu.popup(None, None, self.icon.position_menu, icon, button, time)

    def launch_sidebar(self):
        env = dict(os.environ)
        if "DISPLAY" not in env or not env["DISPLAY"]:
            env["DISPLAY"] = ":0"
        subprocess.Popen(["/usr/local/bin/mrflow-sidebar", "toggle"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def launch_dashboard(self):
        env = dict(os.environ)
        if "DISPLAY" not in env or not env["DISPLAY"]:
            env["DISPLAY"] = ":0"

        # Raise window if already open
        try:
            res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, env=env)
            for line in res.stdout.splitlines():
                if "MrFlow Router" in line:
                    win_id = line.split()[0]
                    subprocess.run(["wmctrl", "-ia", win_id], env=env)
                    return
        except Exception:
            pass

        # If not running, launch GUI directly
        gui_script = os.path.join(BASE_DIR, "bin", "mrflow-gui.py")
        subprocess.Popen(["python3", gui_script], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def launch_cli(self):
        env = dict(os.environ)
        if "DISPLAY" not in env or not env["DISPLAY"]:
            env["DISPLAY"] = ":0"
        try:
            res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, env=env)
            for line in res.stdout.splitlines():
                if "MrFlow Sovereign AI CLI" in line:
                    win_id = line.split()[0]
                    subprocess.run(["wmctrl", "-ia", win_id], env=env)
                    return
        except Exception:
            pass
        subprocess.Popen(["/usr/local/bin/mrflow-terminal"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def switch_provider(self, prov):
        try:
            data = json.dumps({"active_provider": prov}).encode("utf-8")
            req = urllib.request.Request(API_PROVIDER, data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=2.0)
            self.fetch_status()
            self.notify("AI Engine Switched", f"Active inference engine set to: {prov.upper()}")
        except Exception as e:
            self.notify("Failed to Switch Engine", str(e))

    def sync_vault(self):
        try:
            req = urllib.request.Request(API_SYNC, data=b"{}", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("success"):
                    self.notify("Cloud Vault Sync", res.get("message", "Accounts successfully synced!"))
                else:
                    self.notify("Sync Error", res.get("error", "Failed to sync accounts"))
            self.fetch_status()
        except Exception as e:
            self.notify("Sync Error", str(e))

    def clear_cooldowns(self):
        try:
            req = urllib.request.Request(API_CLEAR_CD, data=b"{}", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                count = res.get("cleared_count", 0)
                self.notify("Cooldowns Cleared", f"Reset cooldown state for {count} accounts.")
            self.fetch_status()
        except Exception as e:
            self.notify("Clear Error", str(e))

    def notify(self, title, message):
        try:
            subprocess.Popen(["notify-send", "-i", ICON_BRIGHT, title, message])
        except Exception:
            pass

def main():
    import fcntl
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or str(os.getuid())
    lock_file = open(f"/tmp/mrflow-router-tray-{user}.lock", "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sys.exit(0)

    wait_for_display_and_panel()
    app = MrFlowDesktopHeaderMenu()
    Gtk.main()
    return lock_file


if __name__ == "__main__":
    main()

