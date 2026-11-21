#!/usr/bin/env python3
"""
👑 FLOWORK OS — KAMIDI MASTERING CONSOLE PRO RUNNER
Native WebKit2GTK Sovereign Runner with in-memory Python floworkBridge IPC.
Zero Node.js dependency, zero open network ports, 100% white-label, zero zombie processes.
"""

import sys
import os
import json
import signal
import threading
import argparse

# Enable clean GTK termination
signal.signal(signal.SIGINT, signal.SIG_DFL)

if "DISPLAY" not in os.environ or not os.environ["DISPLAY"]:
    os.environ["DISPLAY"] = ":0"

if "DBUS_SESSION_BUS_ADDRESS" not in os.environ or not os.environ["DBUS_SESSION_BUS_ADDRESS"]:
    if os.path.exists("/run/user/1001/bus"):
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/user/1001/bus"
    if os.path.exists("/run/user/1000/bus"):
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/user/1000/bus"
    os.environ["XDG_RUNTIME_DIR"] = os.path.dirname(os.environ.get("DBUS_SESSION_BUS_ADDRESS", "").split("path=")[-1]) if "path=" in os.environ.get("DBUS_SESSION_BUS_ADDRESS", "") else "/run/user/1001"

# Sovereign WebKit Audio DSP UI Performance Mandate
os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

import gi
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, Gdk, GLib

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUI_PATH = os.path.join(APP_DIR, "gui", "index.html")

# Import backend module
sys.path.insert(0, os.path.join(APP_DIR, "bin"))
import backend


class KamidiAppWindow(Gtk.Window):
    def __init__(self, title="Kamidi Mastering Console Pro", width=1280, height=840, headless_check=False):
        super().__init__(title=title)
        self.headless_check = headless_check
        self.set_default_size(width, height)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(True)

        # Set Window Icon
        icon_path = "/opt/floworkos/icons/kamidi-mastering.png"
        if os.path.exists(icon_path):
            self.set_icon_from_file(icon_path)

        # Visual RGBA Transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)

        # WebKit UserContentManager & floworkBridge IPC
        content_manager = WebKit2.UserContentManager()
        content_manager.register_script_message_handler("floworkBridge")
        content_manager.connect("script-message-received::floworkBridge", self.on_js_message)

        # WebKit Settings
        settings = WebKit2.Settings()
        settings.set_enable_developer_extras(False)
        settings.set_enable_webgl(True)
        settings.set_enable_javascript(True)
        settings.set_javascript_can_access_clipboard(True)
        settings.set_enable_webaudio(True)
        settings.set_allow_file_access_from_file_urls(True)
        settings.set_allow_universal_access_from_file_urls(True)
        settings.set_enable_write_console_messages_to_stdout(True)
        settings.set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.NEVER)

        # Webview
        self.webview = WebKit2.WebView.new_with_user_content_manager(content_manager)
        self.webview.set_settings(settings)
        self.webview.set_background_color(Gdk.RGBA(0.04, 0.04, 0.06, 1.0))
        self.add(self.webview)

        # Connect Events
        self.webview.connect("load-changed", self.on_load_changed)
        self.connect("destroy", self.on_destroy)

        # Load Local UI via file:// URI
        file_uri = f"file://{GUI_PATH}"
        self.webview.load_uri(file_uri)

    def on_load_changed(self, webview, event):
        if event == WebKit2.LoadEvent.FINISHED:
            if self.headless_check:
                print("HEALTH_OK: Kamidi Mastering Console Pro engine & UI operational.")
                Gtk.main_quit()
                sys.exit(0)

    def on_destroy(self, widget):
        Gtk.main_quit()

    def on_js_message(self, content_manager, js_result):
        """Native asynchronous IPC bridge from JavaScript to Python backend."""
        try:
            msg_str = js_result.get_js_value().to_string()
            data = json.loads(msg_str)
            action = data.get("action")
            req_id = data.get("reqId")
            payload = data.get("payload", {})

            if action == "close":
                Gtk.main_quit()
            elif action == "minimize":
                self.iconify()
            elif action == "maximize":
                if self.is_maximized():
                    self.unmaximize()
                else:
                    self.maximize()
            elif action == "execute":
                def worker():
                    try:
                        res = backend.execute(payload)
                    except Exception as err:
                        res = {"status": "error", "error": str(err)}
                    GLib.idle_add(self.respond_to_js, req_id, res)
                threading.Thread(target=worker, daemon=True).start()
        except Exception as e:
            print(f"[Kamidi IPC Error] {e}", file=sys.stderr)

    def respond_to_js(self, req_id, response_data):
        if not req_id:
            return
        json_resp = json.dumps(response_data)
        js_code = (
            f"if (window['_flowork_cb_{req_id}']) {{ "
            f"  window['_flowork_cb_{req_id}']({json_resp}); "
            f"  delete window['_flowork_cb_{req_id}']; "
            f"}}"
        )
        self.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)


def main():
    parser = argparse.ArgumentParser(description="Kamidi Mastering Console Pro Runner")
    parser.add_argument("--check-health", action="store_true", help="Perform headless health check and exit")
    parser.add_argument("--width", type=int, default=1280, help="Initial window width")
    parser.add_argument("--height", type=int, default=840, help="Initial window height")
    parser.add_argument("--title", default="Kamidi Mastering Console Pro", help="Window title")
    args, _ = parser.parse_known_args()

    # GTK Display verification
    if not Gtk.init_check()[0]:
        print("[Kamidi] Error: Unable to initialize GTK display environment.", file=sys.stderr)
        sys.exit(1)

    # Health check timeout guard
    if args.check_health:
        GLib.timeout_add_seconds(6, lambda: (print("TIMEOUT: WebKit2 failed to load within 6s"), sys.exit(1)))

    # Create Sovereign Window
    win = KamidiAppWindow(
        title=args.title,
        width=args.width,
        height=args.height,
        headless_check=args.check_health
    )
    GLib.set_prgname("kamidi-mastering")
    win.set_role("kamidi-mastering")

    if not args.check_health:
        win.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
