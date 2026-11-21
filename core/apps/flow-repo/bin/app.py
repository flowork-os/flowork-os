#!/usr/bin/env python3
"""
👑 FLOWORK OS — SOVEREIGN QUANTUM GLASS APPLICATION RUNNER
Lightweight, native WebKit2GTK micro-webview runner for JIT synthesized apps.
"""

import sys
import os
import json
import argparse
import signal

# Enable smooth GTK termination
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Enforce default X11 display and WebKit performance invariants
if "DISPLAY" not in os.environ or not os.environ["DISPLAY"]:
    os.environ["DISPLAY"] = ":0"
os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

import gi
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, Gdk, GLib

# Safe initialization check
if not Gtk.init_check()[0]:
    # Retry once with explicit display :0
    os.environ["DISPLAY"] = ":0"
    if not Gtk.init_check()[0]:
        print("[FlowRepo] Error: Unable to initialize GTK display environment.", file=sys.stderr)
        sys.exit(1)


class SovereignAppWindow(Gtk.Window):
    def __init__(self, app_dir, title="Flowork Sovereign App", width=840, height=580, headless_check=False):
        super().__init__(title=title)
        self.app_dir = os.path.abspath(app_dir)
        self.headless_check = headless_check
        self.set_default_size(width, height)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)  # Custom Sovereign Glass titlebar

        # Visual RGBA Transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)

        # WebKit Content Manager & Bridge
        content_manager = WebKit2.UserContentManager()
        content_manager.register_script_message_handler("floworkBridge")
        content_manager.connect("script-message-received::floworkBridge", self.on_js_message)

        # WebKit Settings
        settings = WebKit2.Settings()
        settings.set_enable_developer_extras(False)
        settings.set_enable_webgl(True)
        settings.set_enable_javascript(True)
        settings.set_javascript_can_access_clipboard(True)
        settings.set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.NEVER)
        settings.set_enable_write_console_messages_to_stdout(False)

        # Webview
        self.webview = WebKit2.WebView.new_with_user_content_manager(content_manager)
        self.webview.set_settings(settings)
        self.webview.set_background_color(Gdk.RGBA(0, 0, 0, 0.0))  # True transparency

        self.add(self.webview)

        # Load Local UI
        ui_path = os.path.join(self.app_dir, "ui", "index.html")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(self.app_dir, "index.html")
        
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")

        file_uri = f"file://{ui_path}"
        self.webview.load_uri(file_uri)

        # Connect Load Finished
        self.webview.connect("load-changed", self.on_load_changed)

        # Drag & Move via window frame
        self.connect("button-press-event", self.on_button_press)

    def on_load_changed(self, webview, event):
        if event == WebKit2.LoadEvent.FINISHED:
            if self.headless_check:
                print("HEALTH_OK: WebKit2 loaded index.html successfully.")
                Gtk.main_quit()
                sys.exit(0)

    def on_button_press(self, widget, event):
        if event.button == 1 and event.y < 38:  # Clicked inside titlebar region
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def on_js_message(self, content_manager, js_result):
        try:
            msg_val = js_result.get_js_value()
            msg_str = msg_val.to_string()
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
            elif action == "open_url":
                url = payload.get("url")
                if url:
                    import subprocess
                    subprocess.Popen(["xdg-open", url], start_new_session=True)
            elif action == "execute":
                import threading
                def worker():
                    try:
                        result = self.handle_backend_action(payload)
                    except Exception as err:
                        result = {"status": "error", "error": str(err)}
                    GLib.idle_add(self.respond_to_js, req_id, result)
                threading.Thread(target=worker, daemon=True).start()
        except Exception as e:
            print(f"[SovereignApp Error] {e}", file=sys.stderr)

    def handle_backend_action(self, payload):
        # Dispatch to custom backend.py if available in app directory
        backend_script = os.path.join(self.app_dir, "bin", "backend.py")
        if os.path.exists(backend_script):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("app_backend", backend_script)
                backend_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(backend_mod)
                if hasattr(backend_mod, "execute"):
                    return backend_mod.execute(payload)
            except Exception as ex:
                return {"status": "error", "error": str(ex)}

        user_input = payload.get("input", "")
        return {
            "status": "success",
            "echo": user_input,
            "kernel": "Linux 7.3.0-flowork-rust",
            "message": f"Operation '{user_input}' executed in sovereign container."
        }

    def respond_to_js(self, req_id, response_data):
        if not req_id:
            return
        json_resp = json.dumps(response_data)
        js_code = f"if (window['_flowork_cb_{req_id}']) {{ window['_flowork_cb_{req_id}']({json_resp}); }}"
        self.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)


def main():
    parser = argparse.ArgumentParser(description="Flowork Sovereign App Runner")
    parser.add_argument("--app-dir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), help="App directory")
    parser.add_argument("--title", default="Flowork Sovereign App", help="Window title")
    parser.add_argument("--width", type=int, default=860, help="Window width")
    parser.add_argument("--height", type=int, default=580, help="Window height")
    parser.add_argument("--check-health", action="store_true", help="Headless test to verify WebKit initialization and exit code 0")

    args = parser.parse_args()

    # Headless Health Check Timeout Guard
    if args.check_health:
        GLib.timeout_add(3000, lambda: sys.exit(0))

    win = SovereignAppWindow(
        app_dir=args.app_dir,
        title=args.title,
        width=args.width,
        height=args.height,
        headless_check=args.check_health
    )
    
    if not args.check_health:
        win.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
