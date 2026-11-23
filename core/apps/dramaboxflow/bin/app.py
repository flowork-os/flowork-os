#!/usr/bin/env python3
"""
👑 FLOWORK OS — DRAMABOX QUANTUM GLASS RUNNER
WebKit2GTK Micro-webview Harness with Floating PiP, Always-on-Top, and Video Acceleration.
"""

import os
import sys
import json
import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

# Ensure local bin directory is on import path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import backend


class DramaBoxWindow(Gtk.Window):
    def __init__(self, app_dir, title="DramaBox & Melolo Flow", width=960, height=680, headless_check=False):
        super().__init__(title=title)
        self.app_dir = os.path.abspath(app_dir)
        self.headless_check = headless_check
        self.is_pinned = False
        self.pip_mode = "normal"
        self.set_default_size(width, height)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)
        self.set_size_request(300, 200)
        self.set_decorated(True)
        icon_path = "/opt/floworkos/icons/dramaboxflow.png"
        if os.path.exists(icon_path):
            try:
                self.set_icon_from_file(icon_path)
            except Exception:
                pass

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

        # WebKit Settings with Video Hardware Acceleration & Autoplay
        settings = WebKit2.Settings()
        settings.set_enable_developer_extras(False)
        settings.set_enable_webgl(True)
        settings.set_enable_javascript(True)
        settings.set_javascript_can_access_clipboard(True)
        settings.set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.ALWAYS)
        settings.set_media_playback_requires_user_gesture(False)
        settings.set_media_playback_allows_inline(True)
        settings.set_enable_mediasource(True)
        settings.set_enable_webaudio(True)
        if hasattr(settings, "set_enable_write_console_messages_to_stdout"):
            settings.set_enable_write_console_messages_to_stdout(True)
        if hasattr(settings, "set_allow_file_access_from_file_urls"):
            settings.set_allow_file_access_from_file_urls(True)
        if hasattr(settings, "set_allow_universal_access_from_file_urls"):
            settings.set_allow_universal_access_from_file_urls(True)

        # Webview
        self.webview = WebKit2.WebView.new_with_user_content_manager(content_manager)
        self.webview.set_settings(settings)
        self.webview.set_size_request(300, 200)
        self.webview.set_background_color(Gdk.RGBA(0.05, 0.05, 0.08, 0.95))

        self.add(self.webview)

        # Load local index.html UI
        ui_path = os.path.join(self.app_dir, "ui", "index.html")
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file missing at: {ui_path}")
        self.webview.load_uri(f"file://{ui_path}")

        # Connect Events
        self.connect("destroy", Gtk.main_quit)
        self.webview.connect("load-changed", self.on_load_changed)
        self.connect("button-press-event", self.on_button_press)

    def on_load_changed(self, webview, event):
        if event == WebKit2.LoadEvent.FINISHED:
            if self.headless_check:
                print("HEALTH_OK: WebKit2 loaded index.html successfully.")
                Gtk.main_quit()
                sys.exit(0)

    def on_button_press(self, widget, event):
        # Allow dragging window from top glass region (< 42px)
        if event.button == 1 and event.y < 42:
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
                    self.respond_to_js(req_id, {"isMaximized": False})
                else:
                    self.maximize()
                    self.respond_to_js(req_id, {"isMaximized": True})
            elif action == "unmaximize":
                if self.is_maximized():
                    self.unmaximize()
                self.respond_to_js(req_id, {"isMaximized": False})
            elif action == "toggle_pin":
                self.is_pinned = not self.is_pinned
                self.set_keep_above(self.is_pinned)
                self.respond_to_js(req_id, {"status": "success", "isPinned": self.is_pinned})
            elif action == "set_pip_mode":
                mode = payload.get("mode", "compact")
                self.pip_mode = mode
                if mode == "compact":
                    self.unmaximize()
                    self.set_decorated(False)
                    self.resize(380, 680)
                    self.set_keep_above(True)
                    self.is_pinned = True
                elif mode == "landscape":
                    self.unmaximize()
                    self.set_decorated(False)
                    self.resize(580, 380)
                    self.set_keep_above(True)
                    self.is_pinned = True
                elif mode == "normal":
                    self.set_decorated(True)
                    self.set_keep_above(False)
                    self.is_pinned = False
                    self.resize(960, 680)
                self.respond_to_js(req_id, {"status": "success", "mode": mode, "isPinned": self.is_pinned})
            elif action == "get_window_pos":
                cx, cy = self.get_position()
                self.respond_to_js(req_id, {"x": cx, "y": cy})
            elif action == "get_window_geometry":
                w, h = self.get_size()
                x, y = self.get_position()
                self.respond_to_js(req_id, {
                    "width": w,
                    "height": h,
                    "x": x,
                    "y": y,
                    "isMaximized": self.is_maximized()
                })
            elif action == "resize_window":
                try:
                    if self.is_maximized():
                        self.unmaximize()
                    w = payload.get("width")
                    h = payload.get("height")
                    if w is not None and h is not None:
                        self.resize(max(300, int(w)), max(200, int(h)))
                        self.respond_to_js(req_id, {"status": "ok", "width": w, "height": h})
                except Exception as resize_err:
                    sys.stderr.write(f"[Resize Error] {resize_err}\n")
            elif action == "start_resize":
                try:
                    if self.is_maximized():
                        self.unmaximize()
                    edge_map = {
                        "nw": Gdk.WindowEdge.NORTH_WEST,
                        "n": Gdk.WindowEdge.NORTH,
                        "ne": Gdk.WindowEdge.NORTH_EAST,
                        "w": Gdk.WindowEdge.WEST,
                        "e": Gdk.WindowEdge.EAST,
                        "sw": Gdk.WindowEdge.SOUTH_WEST,
                        "s": Gdk.WindowEdge.SOUTH,
                        "se": Gdk.WindowEdge.SOUTH_EAST
                    }
                    edge_val = edge_map.get(payload.get("edge", "se"), Gdk.WindowEdge.SOUTH_EAST)
                    rx = int(payload.get("root_x", 0))
                    ry = int(payload.get("root_y", 0))
                    self.begin_resize_drag(edge_val, 1, rx, ry, Gdk.CURRENT_TIME)
                except Exception as resize_err:
                    sys.stderr.write(f"[begin_resize_drag Error] {resize_err}\n")
            elif action == "move_window_to":
                try:
                    if self.is_maximized():
                        self.unmaximize()
                    x = payload.get("x")
                    y = payload.get("y")
                    if x is not None and y is not None:
                        self.move(int(x), int(y))
                except Exception as move_err:
                    sys.stderr.write(f"[Move Error] {move_err}\n")
            elif action == "move_window_by":
                try:
                    if self.is_maximized():
                        self.unmaximize()
                    dx = payload.get("dx", 0)
                    dy = payload.get("dy", 0)
                    cx, cy = self.get_position()
                    self.move(int(cx + dx), int(cy + dy))
                except Exception as move_err:
                    sys.stderr.write(f"[Move Error] {move_err}\n")
            elif action == "execute":
                def worker():
                    try:
                        result = backend.execute(payload)
                    except Exception as err:
                        result = {"status": "error", "message": str(err)}
                    GLib.idle_add(self.respond_to_js, req_id, result)
                threading.Thread(target=worker, daemon=True).start()
        except Exception as e:
            sys.stderr.write(f"[DramaBox IPC Error] {e}\n")

    def respond_to_js(self, req_id, data):
        if not req_id:
            return False
        try:
            json_str = json.dumps(data)
            escaped_json = json.dumps(json_str)
            js_code = f"if (window.onFloworkBridgeResponse) {{ window.onFloworkBridgeResponse('{req_id}', JSON.parse({escaped_json})); }}"
            self.webview.run_javascript(js_code, None, None, None)
        except Exception as err:
            sys.stderr.write(f"[respond_to_js Error] {err}\n")
        return False


def main():
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    headless = "--headless-check" in sys.argv
    win = DramaBoxWindow(app_dir, title="DramaBox Player Flow", width=960, height=680, headless_check=headless)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
