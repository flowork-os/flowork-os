#!/usr/bin/env python3
"""
Mr. Flow Sovereign Companion — Desktop Sidebar Chat Daemon
Engineered for Flowork OS (Linux 7.3.0 Rust)
Canonical Path: /opt/floworkos/apps/mrflow-sidebar/bin/mrflow-sidebar.py
FULL UNIFIED ARCHITECTURE: 1 Body, 2 Faces (CLI & Chat GUI)
"""

import sys
import os

if "/opt/floworkos/lib/python3" not in sys.path:
    sys.path.insert(0, "/opt/floworkos/lib/python3")

import re
import json
import glob
import socket
import threading
import subprocess
import urllib.request
import urllib.error
import signal
import time
import fcntl
import warnings
warnings.filterwarnings("ignore")

# Optimize WebKitGTK for Linux X11 without hardware DRI3 (prevents 115% CPU llvmpipe spin)
os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

USER = os.environ.get("USER") or os.environ.get("LOGNAME") or os.path.basename(os.path.expanduser("~"))
HOME = os.path.expanduser("~")
SOCKET_PATH = f"/tmp/mrflow-sidebar-{USER}.sock"
APP_DIR = "/opt/floworkos/apps/mrflow-sidebar"
UI_INDEX = os.path.join(APP_DIR, "ui", "index.html")
CONFIG_PATH = os.path.join(HOME, ".flowork", "sidebar_config.json")
HISTORY_DIR = os.path.join(HOME, ".flowork", "history", "chats")
os.makedirs(HISTORY_DIR, exist_ok=True)

def log_sidebar(msg):
    try:
        with open("/tmp/mrflow-sidebar.log", "a") as f:
            f.write(f"[{time.strftime('%X')}] {msg}\n")
    except Exception:
        pass

class MrFlowSidebar(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Mr. Flow Sovereign Companion")
        self.set_role("mrflow-sidebar")

        # Window decorations and hints
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.stick()

        # Load persisted config
        self.config = self._load_config()
        self.sidebar_w = self.config.get("width", 480)
        self.is_pinned = self.config.get("is_pinned", False)
        self.hover_to_open = self.config.get("hover_to_open", False)
        self.position = self.config.get("position", "right")
        self.current_workspace = self.config.get("current_workspace", HOME)
        if not os.path.isdir(self.current_workspace):
            self.current_workspace = HOME

        # Screen geometry
        self.screen = Gdk.Screen.get_default()
        self.panel_h = 29
        self._update_geometry()

        self.set_default_size(self.sidebar_w, self.sidebar_h)
        self.move(self.pos_x, self.pos_y)

        # State
        self.is_open = False
        self.current_session_id = None
        self.active_agent_proc = None
        self.last_mouse_inside = time.time()
        self.last_open_time = time.time()
        self.mouse_has_entered = False
        self.pointer_device = None

        # Setup Gdk pointer device for zero-warning coordinate tracking
        try:
            display = Gdk.Display.get_default()
            seat = display.get_default_seat()
            self.pointer_device = seat.get_pointer()
        except Exception:
            pass

        # WebKit User Content Manager & PyBridge
        self.ucm = WebKit2.UserContentManager()
        self.ucm.register_script_message_handler("pybridge")
        self.ucm.connect("script-message-received::pybridge", self.on_js_message)

        # WebKit WebView
        self.webview = WebKit2.WebView.new_with_user_content_manager(self.ucm)
        self.webview.set_background_color(Gdk.RGBA(0.03, 0.05, 0.09, 0.96))

        settings = self.webview.get_settings()
        settings.set_enable_developer_extras(False)
        settings.set_enable_javascript(True)
        settings.set_enable_webgl(False)
        settings.set_javascript_can_access_clipboard(True)
        settings.set_allow_file_access_from_file_urls(True)
        settings.set_allow_universal_access_from_file_urls(True)
        settings.set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.NEVER)

        self.add(self.webview)

        # Load UI
        self.webview.load_uri(f"file://{UI_INDEX}")

        # Connect window events
        self.connect("destroy", self.on_destroy)
        self.connect("key-press-event", self.on_key_press)
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        self.connect("enter-notify-event", self.on_enter_notify)
        self.webview.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        self.webview.connect("enter-notify-event", self.on_enter_notify)

        # Start mouse position & auto-hide watcher (runs every 100ms for instant hover reaction)
        GLib.timeout_add(100, self._check_mouse_position)

    def _run_js(self, js_code):
        def _do_run():
            try:
                self.webview.run_javascript(js_code, None, None, None)
            except Exception as e:
                log_sidebar(f"JavaScript execution error: {e}")
        GLib.idle_add(_do_run)

    def _load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"width": 480, "is_pinned": False, "hover_to_open": False, "current_workspace": HOME, "auto_show_on_start": True, "position": "right"}

    def _save_config(self):
        try:
            self.config["width"] = self.sidebar_w
            self.config["is_pinned"] = self.is_pinned
            self.config["hover_to_open"] = self.hover_to_open
            self.config["position"] = self.position
            self.config["current_workspace"] = self.current_workspace
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def _update_geometry(self):
        self.screen_w = self.screen.get_width()
        self.screen_h = self.screen.get_height()
        self.sidebar_h = self.screen_h - self.panel_h
        if self.position == "left":
            self.pos_x = 0
        else:
            self.pos_x = self.screen_w - self.sidebar_w
        self.pos_y = self.panel_h

    def _check_mouse_position(self):
        """Auto-hide when mouse leaves, and peek/open when mouse touches right screen edge or handle."""
        if not self.pointer_device:
            return True

        try:
            _, mx, my = self.pointer_device.get_position()
            now = time.time()

            if self.is_open:
                # If window is pinned or active agent is running, stay open
                if self.is_pinned or self.active_agent_proc:
                    self.last_mouse_inside = now
                    return True

                # If manual click mode is active, do NOT auto-hide on mouse leave
                # (User explicitly closes via Esc or close button ✕)
                if not self.hover_to_open:
                    self.last_mouse_inside = now
                    return True

                # Check if mouse is inside window bounds (for hover auto-peek mode)
                if self.position == "left":
                    inside = (mx <= (self.sidebar_w + 20)) and (my >= self.pos_y)
                else:
                    inside = (mx >= (self.pos_x - 20)) and (my >= self.pos_y)

                if inside:
                    self.last_mouse_inside = now
                    self.mouse_has_entered = True
                else:
                    # Mouse is outside
                    grace = 1.8 if self.mouse_has_entered else 4.0
                    if now - self.last_mouse_inside > grace:
                        self.hide_sidebar()

            else:
                # Window is hidden/collapsed:
                # Only auto-open if hover_to_open is enabled!
                if not self.hover_to_open:
                    return True

                if self.position == "left":
                    touch_edge = (mx <= 30) and (my >= self.pos_y)
                else:
                    touch_edge = (mx >= (self.screen_w - 30) or mx >= (self.pos_x - 10)) and (my >= self.pos_y)

                if touch_edge:
                    self.show_sidebar()
                    self.last_mouse_inside = now

        except Exception:
            pass
        return True

    def on_enter_notify(self, widget, event):
        if not self.is_open and self.hover_to_open:
            self.show_sidebar()
        return False

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            if self.active_agent_proc:
                self._abort_agent_turn()
                return True
            if not self.is_pinned:
                self.hide_sidebar(force=True)
                return True
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and (event.keyval in [Gdk.KEY_v, Gdk.KEY_V]):
            GLib.idle_add(self._check_and_paste_system_clipboard)
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and (event.keyval in [Gdk.KEY_c, Gdk.KEY_C]):
            if self.active_agent_proc:
                self._abort_agent_turn()
                return True
        return False

    def on_js_message(self, manager, js_result):
        try:
            val = js_result.get_js_value()
            data_str = val.to_string()
            data = json.loads(data_str)
            action = data.get("action")
            log_sidebar(f"PyBridge action: {action}")

            if action == "log_preview_status":
                log_sidebar(f"PREVIEW_STATUS_REPORT: {json.dumps(data)}")
                return

            if action in ("hide_window", "collapse_window"):
                self.collapse_sidebar(force=True)
            elif action == "show_window":
                self.show_sidebar()

            elif action in ("abort_agent", "stop_agent", "kill_process", "abort", "stop"):
                self._abort_agent_turn()

            elif action == "launch_terminal":
                session_id = data.get("sessionId") or self.current_session_id
                cmd = ["/usr/local/bin/mrflow-terminal"]
                if session_id:
                    cmd.extend(["--resume", session_id])
                subprocess.Popen(cmd, cwd=self.current_workspace, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            elif action == "set_pinned":
                pinned = data.get("pinned", False)
                self.set_pinned_mode(pinned)

            elif action in ("toggle_hover_peek", "set_hover_peek"):
                val = data.get("enabled")
                self.set_hover_peek_mode(not self.hover_to_open if val is None else bool(val))

            elif action == "resize_sidebar":
                width = int(data.get("width", 480))
                self.resize_sidebar(width)

            elif action == "new_chat":
                self.current_session_id = None
                self._abort_agent_turn()

            elif action == "get_workspaces":
                self._send_workspaces_to_ui()

            elif action == "set_workspace":
                path = data.get("path")
                if path and os.path.isdir(path):
                    self.current_workspace = path
                    self._save_config()
                    self.current_session_id = None

            elif action == "browse_workspace_dialog":
                self._open_folder_chooser()

            elif action == "get_history_list":
                threading.Thread(target=self._send_history_list_to_ui, daemon=True).start()

            elif action == "load_session_data":
                sess_id = data.get("sessionId")
                fname = data.get("filename")
                threading.Thread(target=self._load_session_into_ui, args=(sess_id, fname), daemon=True).start()

            elif action == "delete_session":
                sess_id = data.get("sessionId")
                filename = data.get("filename")
                threading.Thread(target=self._delete_session_file, args=(sess_id, filename), daemon=True).start()

            elif action == "clear_all_history":
                self._clear_all_history()

            elif action == "set_position":
                pos = data.get("position", "right")
                self.set_position(pos)

            elif action == "capture_screenshot":
                mode = data.get("mode", "snippet")
                threading.Thread(target=self._capture_user_screenshot, args=(mode,), daemon=True).start()

            elif action == "save_pasted_image":
                b64 = data.get("base64Data") or data.get("base64", "")
                threading.Thread(target=self._save_pasted_image, args=(b64,), daemon=True).start()

            elif action == "paste_from_system_clipboard":
                GLib.idle_add(self._check_and_paste_system_clipboard)

            elif action == "open_file_location":
                target_p = data.get("path")
                if target_p and os.path.exists(target_p):
                    parent_d = os.path.dirname(target_p)
                    subprocess.Popen(["xdg-open", parent_d])

            elif action == "get_initial_state":
                self._send_initial_state()

            elif action == "check_system_update":
                threading.Thread(target=self._check_system_update_async, daemon=True).start()

            elif action == "run_system_update":
                threading.Thread(target=self._run_system_update_async, daemon=True).start()

            elif action == "get_inference_engine":
                threading.Thread(target=self._fetch_and_send_engine_status, daemon=True).start()

            elif action == "set_inference_engine":
                provider = data.get("provider", "connector")
                model = data.get("model")
                threading.Thread(target=self._apply_inference_engine, args=(provider, model), daemon=True).start()

            elif action == "send_agent_message":
                prompt = data.get("prompt", "")
                session_id = data.get("sessionId")
                workspace = data.get("workspace") or self.current_workspace
                attached_b64 = data.get("attachedImageB64")
                if attached_b64 and ("[User Attached Screenshot:" not in prompt):
                    try:
                        import base64
                        from PIL import Image
                        import io
                        if "," in attached_b64:
                            attached_b64 = attached_b64.split(",", 1)[1]
                        raw_bytes = base64.b64decode(attached_b64)
                        home = os.environ.get("HOME") or HOME
                        target_dir = os.path.join(home, "Pictures/Screenshots")
                        os.makedirs(target_dir, exist_ok=True)
                        ts = time.strftime("%Y%m%d_%H%M%S")
                        dest_path = os.path.join(target_dir, f"User_Attached_{ts}.jpg")
                        with Image.open(io.BytesIO(raw_bytes)) as img:
                            if img.mode != "RGB":
                                img = img.convert("RGB")
                            max_w, max_h = 1280, 800
                            w, h = img.size
                            if w > max_w or h > max_h:
                                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                            img.save(dest_path, "JPEG", quality=75, optimize=True)
                        kb = round(os.path.getsize(dest_path) / 1024, 1)
                        prompt = f'[User Attached Screenshot: {dest_path} ({kb} KB)]\nSYSTEM DIRECTIVE: The user has attached a screenshot at "{dest_path}". You MUST execute view_file with AbsolutePath="{dest_path}" to visually inspect the image before answering.\n\nUser Instruction/Question:\n{prompt}'
                        log_sidebar(f"Saved inline attached b64 image: {dest_path} ({kb} KB)")
                    except Exception as ex:
                        log_sidebar(f"Failed to save inline attached b64 image: {ex}")
                threading.Thread(target=self._run_agent_turn, args=(prompt, session_id, workspace), daemon=True).start()

        except Exception as e:
            print(f"[MrFlow Sidebar] Error processing JS message: {e}", file=sys.stderr)

    def _check_system_update_async(self):
        try:
            res = subprocess.run(["/usr/local/bin/flowork-update", "--json"], capture_output=True, text=True, timeout=15)
            if res.returncode in (0, 10) and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                js = f"if (window.onSystemUpdateChecked) {{ window.onSystemUpdateChecked({json.dumps(data)}); }}"
                GLib.idle_add(lambda: self.webview.run_javascript(js, None, None, None))
        except Exception as e:
            log_sidebar(f"Check system update error: {e}")

    def _run_system_update_async(self):
        try:
            js_start = "if (window.onSystemUpdateStarted) { window.onSystemUpdateStarted(); }"
            GLib.idle_add(lambda: self.webview.run_javascript(js_start, None, None, None))

            res = subprocess.run(["sudo", "/usr/local/bin/flowork-update"], capture_output=True, text=True, timeout=120)
            success = (res.returncode == 0)
            data = {"success": success, "output": res.stdout, "error": res.stderr}
            js_done = f"if (window.onSystemUpdateFinished) {{ window.onSystemUpdateFinished({json.dumps(data)}); }}"
            GLib.idle_add(lambda: self.webview.run_javascript(js_done, None, None, None))
        except Exception as e:
            log_sidebar(f"Run system update error: {e}")
            js_err = f"if (window.onSystemUpdateFinished) {{ window.onSystemUpdateFinished({{'success': false, 'error': {json.dumps(str(e))}}}); }}"
            GLib.idle_add(lambda: self.webview.run_javascript(js_err, None, None, None))

    def _send_initial_state(self):
        js = f"window.renderWorkspaceList({{ current: {json.dumps(self.current_workspace)}, list: {json.dumps(self._get_workspace_list())} }});\n"
        js += f"if (window.setPinnedState) {{ window.setPinnedState({json.dumps(self.is_pinned)}); }}\n"
        js += f"if (window.setHoverPeekState) {{ window.setHoverPeekState({json.dumps(self.hover_to_open)}); }}\n"
        js += f"if (window.updatePositionState) {{ window.updatePositionState({json.dumps(self.position)}); }}\n"
        self.webview.run_javascript(js, None, None, None)
        threading.Thread(target=self._check_system_update_async, daemon=True).start()
        threading.Thread(target=self._fetch_and_send_engine_status, daemon=True).start()

    def _fetch_and_send_engine_status(self):
        try:
            req = urllib.request.Request("http://127.0.0.1:9099/auth/router/status", headers={"User-Agent": "MrFlow-Sidebar/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                active_prov = data.get("active_provider", "connector")
                provs = data.get("providers", {})
                ollama_cfg = provs.get("ollama") or (provs.get("providers", {}).get("ollama", {}) if isinstance(provs, dict) else {})
                active_model = ollama_cfg.get("default_model") or ollama_cfg.get("model") or "deepseek-v4-9b-uncensored:latest"
                
                payload = {
                    "active_provider": active_prov,
                    "active_model": active_model,
                    "ollama_models": ollama_cfg.get("custom_models") or ["deepseek-v4-9b-uncensored:latest", "qwen2.5-coder:7b", "qwen2.5-coder:1.5b"]
                }
                js = f"if (window.updateEngineStatus) {{ window.updateEngineStatus({json.dumps(payload)}); }}"
                GLib.idle_add(lambda: self.webview.run_javascript(js, None, None, None))
        except Exception as e:
            log_sidebar(f"Fetch engine status error: {e}")

    def _apply_inference_engine(self, provider, model=None):
        try:
            body = {"active_provider": provider}
            if provider == "ollama" and model:
                body["ollama"] = {"default_model": model, "model": model}
            payload = json.dumps(body).encode("utf-8")
            req = urllib.request.Request("http://127.0.0.1:9099/auth/router/provider-config", data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                pass
            self._fetch_and_send_engine_status()
        except Exception as e:
            log_sidebar(f"Apply engine error: {e}")

    def _get_workspace_list(self):
        workspaces = [HOME, "/opt/floworkos"]
        projects_file = os.path.expanduser("~/.flowork/projects.json")
        if os.path.exists(projects_file):
            try:
                with open(projects_file) as f:
                    projs = json.load(f).get("projects", {})
                    for p in projs.keys():
                        if os.path.isdir(p) and p not in workspaces:
                            workspaces.append(p)
            except Exception:
                pass
        return workspaces

    def _send_workspaces_to_ui(self):
        data = {"current": self.current_workspace, "list": self._get_workspace_list()}
        js = f"window.renderWorkspaceList({json.dumps(data)});"
        self.webview.run_javascript(js, None, None, None)

    def _open_folder_chooser(self):
        dialog = Gtk.FileChooserDialog(
            title="Choose Project Workspace",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.set_current_folder(self.current_workspace)
        resp = dialog.run()
        if resp == Gtk.ResponseType.OK:
            chosen = dialog.get_filename()
            dialog.destroy()
            if chosen and os.path.isdir(chosen):
                self.current_workspace = chosen
                self._save_config()
                self._send_workspaces_to_ui()
                js = f"switchWorkspace({json.dumps(chosen)});"
                self.webview.run_javascript(js, None, None, None)
        else:
            dialog.destroy()

    def _get_workspace_slug(self, workspace_path):
        slug = os.path.basename(workspace_path.rstrip("/"))
        projects_file = os.path.expanduser("~/.flowork/projects.json")
        if os.path.exists(projects_file):
            try:
                with open(projects_file) as f:
                    slug = json.load(f).get("projects", {}).get(workspace_path, slug)
            except Exception:
                pass
        return slug

    def _extract_chat_title_and_stats(self, file_path):
        title = ""
        user_questions = 0
        real_sess_id = ""
        mtime = os.path.getmtime(file_path)

        def clean_text(t):
            if not t: return ""
            m_req = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", t, re.DOTALL)
            if m_req:
                t = m_req.group(1)
            else:
                m_sys = re.search(r"content=(.*?)(?:\n\[Message\]|\n\n|$)", t, re.DOTALL)
                if m_sys:
                    t = m_sys.group(1)

            t = re.sub(r"<session_context>.*?</session_context>", "", t, flags=re.DOTALL)
            t = re.sub(r"<environment_details>.*?</environment_details>", "", t, flags=re.DOTALL)
            t = re.sub(r"<CONTEXT_SUMMARY>.*?</CONTEXT_SUMMARY>", "", t, flags=re.DOTALL)
            t = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", t, flags=re.DOTALL)
            t = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", t, flags=re.DOTALL)
            t = re.sub(r"\[User Attached Screenshot:[^\]]+\]\s*", "", t)
            t = re.sub(r"<[^>]+>", "", t)
            t = t.replace("\r", " ").replace("\n", " ")
            t = re.sub(r"#{1,6}\s*", "", t)
            t = re.sub(r"-{2,}", " ", t)
            t = re.sub(r"\*{1,3}", "", t)
            t = re.sub(r"`{1,3}", "", t)
            t = re.sub(r"\s+", " ", t).strip()
            if t.startswith("Ran command:") or t.startswith("Command output:"): return ""
            return t

        # Fast streaming title extraction: scan at most 35 lines (sub-millisecond)
        try:
            if file_path.endswith(".json") and not file_path.endswith(".jsonl"):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
                    data = json.load(fp)
                    if isinstance(data, list):
                        for item in data[:30]:
                            if isinstance(item, dict) and "user" in item:
                                user_questions += 1
                                if not title:
                                    title = clean_text(item["user"])
            else:
                lines_read = 0
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
                    for line in fp:
                        lines_read += 1
                        if lines_read > 35 and title:
                            break
                        try:
                            o = json.loads(line)
                            if "sessionId" in o and not real_sess_id:
                                real_sess_id = o["sessionId"]

                            is_user = (
                                o.get("type") in ["user", "USER_INPUT"] or
                                o.get("source") in ["USER_EXPLICIT", "USER"] or
                                o.get("role") == "user" or
                                "user" in o
                            )

                            if is_user:
                                txt = ""
                                c = o.get("content") or o.get("user") or o.get("parts")
                                if isinstance(c, str):
                                    txt = c
                                elif isinstance(c, list) and len(c) > 0:
                                    for sub in c:
                                        if isinstance(sub, dict) and "text" in sub:
                                            txt = sub["text"]
                                            break
                                        elif isinstance(sub, str):
                                            txt = sub
                                            break
                                cand = clean_text(txt)
                                if cand:
                                    user_questions += 1
                                    if not title:
                                        title = cand
                            elif not title and o.get("type") == "SYSTEM_MESSAGE":
                                cand = clean_text(str(o.get("content", "")))
                                if cand:
                                    title = cand
                                    user_questions += 1
                        except Exception:
                            pass
        except Exception:
            pass

        if not title:
            title = f"Sesi Operasi ({time.strftime('%b %d, %H:%M', time.localtime(mtime))})"
        else:
            if len(title) > 55:
                title = title[:52].strip() + "..."

        return title, max(user_questions, 1 if title else 0), real_sess_id

    def _send_history_list_to_ui(self):
        """Asynchronously queries recent chat history and emits JSON array to WebKit."""
        candidate_files = []
        
        # 1. Flowork workspace chat history
        flowork_dirs = [
            os.path.expanduser("~/.flowork/history/chats"),
            "/opt/floworkos/history/chats"
        ]
        for pdir in flowork_dirs:
            if os.path.isdir(pdir):
                for root, dirs, files in os.walk(pdir):
                    for f in files:
                        if f.endswith(".jsonl") or (f.endswith(".json") and not f.endswith(".url.json")):
                            candidate_files.append(os.path.join(root, f))

        # 2. Antigravity / Gemini brain transcripts (only compact transcript.jsonl, skip 10MB transcript_full)
        for bdir in glob.glob(os.path.expanduser("~/.gemini/antigravity/brain/*")):
            if os.path.isdir(bdir) and not os.path.basename(bdir).startswith("temp"):
                tf_norm = os.path.join(bdir, ".system_generated", "logs", "transcript.jsonl")
                if os.path.exists(tf_norm):
                    candidate_files.append(tf_norm)

        # Deduplicate files while preserving newest first
        seen_files = set()
        unique_files = []
        for f in candidate_files:
            try:
                real_p = os.path.realpath(f)
                if real_p not in seen_files:
                    seen_files.add(real_p)
                    unique_files.append(f)
            except Exception:
                pass

        try:
            unique_files.sort(key=os.path.getmtime, reverse=True)
        except Exception:
            pass

        results = []
        for f in unique_files[:40]:
            try:
                sess_name = os.path.basename(f)
                mtime = os.path.getmtime(f)
                title, user_questions, real_sess_id = self._extract_chat_title_and_stats(f)
                
                if not real_sess_id:
                    if "/brain/" in f:
                        real_sess_id = f.split("/brain/")[1].split("/")[0]
                    else:
                        parts = sess_name.replace(".jsonl", "").replace(".json", "").split("-")
                        real_sess_id = parts[-1] if len(parts) >= 2 else sess_name.replace(".jsonl", "").replace(".json", "")

                results.append({
                    "filename": f,
                    "session_id": real_sess_id,
                    "title": title,
                    "date_str": time.strftime("%b %d, %H:%M", time.localtime(mtime)),
                    "message_count": user_questions,
                    "user_questions": user_questions
                })
            except Exception:
                pass

        js = f"window.renderHistoryList({json.dumps(results)});"
        GLib.idle_add(lambda: self.webview.run_javascript(js, None, None, None))

    def _load_session_into_ui(self, session_id, filename=None):
        """Asynchronously parses and loads selected chat session into WebKit chatContainer."""
        matched_file = None
        
        # 1. Direct filename hit (instant 0ms)
        if filename and os.path.exists(filename):
            matched_file = filename

        # 2. Match by session_id in brain
        elif session_id:
            brain_file = os.path.expanduser(f"~/.gemini/antigravity/brain/{session_id}/.system_generated/logs/transcript.jsonl")
            if os.path.exists(brain_file):
                matched_file = brain_file
            else:
                flowork_dirs = [
                    os.path.expanduser("~/.flowork/history/chats"),
                    "/opt/floworkos/history/chats"
                ]
                for pdir in flowork_dirs:
                    if os.path.isdir(pdir):
                        for root, dirs, files in os.walk(pdir):
                            for f in files:
                                if session_id in f or f == session_id or f == f"{session_id}.jsonl":
                                    matched_file = os.path.join(root, f)
                                    break
                            if matched_file: break
                    if matched_file: break

        messages = []
        if matched_file and os.path.exists(matched_file):
            try:
                if matched_file.endswith(".json") and not matched_file.endswith(".jsonl"):
                    with open(matched_file, "r", encoding="utf-8", errors="ignore") as fp:
                        data = json.load(fp)
                        if isinstance(data, list):
                            for item in data[-60:]:
                                if "user" in item:
                                    messages.append({"role": "user", "content": item["user"]})
                                if "assistant" in item:
                                    messages.append({"role": "assistant", "content": item["assistant"]})
                else:
                    with open(matched_file, "r", encoding="utf-8", errors="ignore") as fp:
                        for line in fp:
                            try:
                                o = json.loads(line)
                                t = o.get("type")
                                src = o.get("source")
                                
                                # User turn
                                if t in ["user", "USER_INPUT"] or src in ["USER_EXPLICIT", "USER"]:
                                    c = o.get("content")
                                    txt = ""
                                    if isinstance(c, str):
                                        txt = c
                                    elif isinstance(c, list) and c and isinstance(c[0], dict) and "text" in c[0]:
                                        txt = c[0]["text"]
                                    if txt and not txt.startswith("<session_context>") and not txt.startswith("<environment_details>"):
                                        m_req = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", txt, re.DOTALL)
                                        if m_req: txt = m_req.group(1).strip()
                                        messages.append({"role": "user", "content": txt})
                                
                                # Assistant / Model turn
                                elif t in ["gemini", "assistant", "PLANNER_RESPONSE", "GENERIC"] or src == "MODEL":
                                    c = o.get("content", "")
                                    content_str = ""
                                    if isinstance(c, str):
                                        content_str = c
                                    elif isinstance(c, list) and c and isinstance(c[0], dict) and "text" in c[0]:
                                        content_str = c[0]["text"]

                                    tool_calls = o.get("toolCalls") or o.get("tool_calls") or []
                                    tools_list = []
                                    for tc in tool_calls:
                                        res_str = tc.get("resultDisplay") or str(tc.get("result", ""))
                                        if len(res_str) > 800:
                                            res_str = res_str[:780] + "..."
                                        tools_list.append({
                                            "id": tc.get("id", ""),
                                            "name": tc.get("displayName") or tc.get("name") or "Tool",
                                            "args": tc.get("args", {}),
                                            "status": tc.get("status", "success"),
                                            "result": res_str
                                        })

                                    if content_str or tools_list:
                                        messages.append({
                                            "role": "assistant",
                                            "content": content_str,
                                            "tools": tools_list
                                        })
                            except Exception:
                                pass
            except Exception:
                pass

        if len(messages) > 60:
            messages = messages[-60:]

        self.current_session_id = session_id
        js = f"window.onSessionLoaded({json.dumps(session_id)}, {json.dumps(messages)});"
        GLib.idle_add(lambda: self.webview.run_javascript(js, None, None, None))

    def _delete_session_file(self, session_id, filename=None):
        import urllib.parse
        import shutil

        deleted = False

        # 0. Unquote if URL-encoded
        if filename:
            try:
                filename = urllib.parse.unquote(filename).strip()
            except Exception:
                pass

        # 1. Direct file path check (instant hit)
        if filename and os.path.exists(filename):
            try:
                # If Antigravity brain session, remove the entire session dir
                if "/brain/" in filename:
                    parts = filename.split("/brain/")
                    b_id = parts[1].split("/")[0]
                    b_dir = os.path.join(parts[0], "brain", b_id)
                    if os.path.isdir(b_dir):
                        shutil.rmtree(b_dir, ignore_errors=True)
                        deleted = True
                if os.path.exists(filename):
                    os.unlink(filename)
                    deleted = True
                log_sidebar(f"Deleted history session file directly: {filename}")
            except Exception as e:
                log_sidebar(f"Error unlinking {filename}: {e}")

        # 2. Check brain dir by session_id
        if not deleted and session_id:
            for b_dir in glob.glob(os.path.expanduser("~/.gemini/antigravity/brain/*")):
                if session_id in os.path.basename(b_dir):
                    try:
                        shutil.rmtree(b_dir, ignore_errors=True)
                        deleted = True
                        log_sidebar(f"Deleted brain session directory: {b_dir}")
                        break
                    except Exception as e:
                        log_sidebar(f"Error removing brain dir {b_dir}: {e}")

        # 3. Search across all Flowork history directories
        search_dirs = [
            os.path.expanduser("~/.flowork/history/chats"),
            "/opt/floworkos/history/chats"
        ]

        fname_base = os.path.basename(filename) if filename else ""
        sess_prefix = session_id[:8] if (session_id and len(session_id) >= 8) else session_id

        if not deleted and (session_id or fname_base):
            for base_d in search_dirs:
                if not os.path.isdir(base_d):
                    continue
                for root, dirs, files in os.walk(base_d):
                    for f in files:
                        full_f = os.path.join(root, f)
                        match = False
                        if fname_base and f == fname_base:
                            match = True
                        elif session_id and (session_id in f or (sess_prefix and sess_prefix in f)):
                            match = True
                        else:
                            try:
                                with open(full_f, "r", encoding="utf-8", errors="ignore") as fp:
                                    for idx, line in enumerate(fp):
                                        if idx > 20: break
                                        if session_id and session_id in line:
                                            match = True
                                            break
                            except Exception:
                                pass

                        if match:
                            try:
                                os.unlink(full_f)
                                deleted = True
                                log_sidebar(f"Deleted history file: {full_f}")
                            except Exception as e:
                                log_sidebar(f"Error unlinking {full_f}: {e}")

        # If deleted session is currently active in chat, reset chat view
        if session_id and (session_id == self.current_session_id or (self.current_session_id and session_id[:8] in self.current_session_id)):
            self.current_session_id = None
            js_reset = "currentSessionId = ''; chatContainer.innerHTML = ''; chatContainer.appendChild(heroBanner); heroBanner.style.display = 'flex'; sessionStatus.textContent = 'Sovereign Agent: Ready';"
            GLib.idle_add(lambda: self.webview.run_javascript(js_reset, None, None, None))

        self._send_history_list_to_ui()

    def _clear_all_history(self):
        slug = self._get_workspace_slug(self.current_workspace)
        flowork_dirs = [
            os.path.expanduser(f"~/.flowork/history/chats/{slug}"),
            os.path.expanduser("~/.flowork/history/chats"),
            "/opt/floworkos/history/chats"
        ]
        for base_d in flowork_dirs:
            if not os.path.isdir(base_d):
                continue
            for root, dirs, files in os.walk(base_d):
                for f in files:
                    if f.endswith(".jsonl") or (f.endswith(".json") and not f.endswith(".url.json")):
                        try:
                            os.unlink(os.path.join(root, f))
                        except Exception:
                            pass

        self.current_session_id = None
        js_reset = "currentSessionId = ''; chatContainer.innerHTML = ''; chatContainer.appendChild(heroBanner); heroBanner.style.display = 'flex'; sessionStatus.textContent = 'Sovereign Agent: Ready';"
        GLib.idle_add(lambda: self.webview.run_javascript(js_reset, None, None, None))
        self._send_history_list_to_ui()

    def resize_sidebar(self, new_width):
        self.sidebar_w = max(360, min(new_width, 1200))
        self._update_geometry()
        self.move(self.pos_x, self.pos_y)
        self.resize(self.sidebar_w, self.sidebar_h)
        if self.is_open:
            self._apply_struts(True)
        self._save_config()

    def _apply_struts(self, apply_state):
        win = self.get_window()
        if not win:
            GLib.idle_add(lambda: self._apply_struts(apply_state))
            return
        try:
            xid = win.get_xid()
            if apply_state:
                # Dock safe area: Leave bottom 120px unreserved so Plank dock at screen bottom
                # retains full screen width (2560px) and never gets shifted or clamped.
                dock_safe_bottom = max(0, self.screen_h - 120)
                if self.position == "left":
                    strut_val = f"{self.sidebar_w}, 0, 0, 0"
                    strut_partial = f"{self.sidebar_w}, 0, 0, 0, {self.pos_y}, {dock_safe_bottom}, 0, 0, 0, 0, 0, 0"
                else:
                    strut_val = f"0, {self.sidebar_w}, 0, 0"
                    strut_partial = f"0, {self.sidebar_w}, 0, 0, 0, 0, {self.pos_y}, {dock_safe_bottom}, 0, 0, 0, 0"

                subprocess.run(["xprop", "-id", str(xid), "-f", "_NET_WM_STRUT", "32c", "-set", "_NET_WM_STRUT", strut_val], check=False)
                subprocess.run(["xprop", "-id", str(xid), "-f", "_NET_WM_STRUT_PARTIAL", "32cccccccccccc", "-set", "_NET_WM_STRUT_PARTIAL", strut_partial], check=False)
            else:
                subprocess.run(["xprop", "-id", str(xid), "-remove", "_NET_WM_STRUT"], check=False)
                subprocess.run(["xprop", "-id", str(xid), "-remove", "_NET_WM_STRUT_PARTIAL"], check=False)
        except Exception as e:
            log_sidebar(f"Error applying struts: {e}")

    def set_pinned_mode(self, pinned):
        self.is_pinned = pinned
        self.set_keep_above(True)
        self.present()
        if self.is_open:
            self._apply_struts(True)
        self._save_config()

    def set_hover_peek_mode(self, enabled):
        self.hover_to_open = bool(enabled)
        self._save_config()
        js = f"if (window.setHoverPeekState) {{ window.setHoverPeekState({json.dumps(self.hover_to_open)}); }}"
        GLib.idle_add(lambda: self.webview.run_javascript(js, None, None, None))
        log_sidebar(f"Auto-peek hover mode set to: {self.hover_to_open}")

    def set_position(self, pos):
        if pos not in ["left", "right"]:
            pos = "right"
        self.position = pos
        self._update_geometry()
        self.move(self.pos_x, self.pos_y)
        self.resize(self.sidebar_w, self.sidebar_h)
        if self.is_open:
            self._apply_struts(True)
        self._save_config()
        js = f"if (window.updatePositionState) {{ window.updatePositionState({json.dumps(self.position)}); }}"
        self.webview.run_javascript(js, None, None, None)

    def _capture_user_screenshot(self, mode="snippet"):
        home = os.environ.get("HOME") or HOME
        target_dir = os.path.join(home, "Pictures/Screenshots")
        os.makedirs(target_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(target_dir, f"User_Screenshot_{ts}.jpg")
        raw_tmp = f"/tmp/user_raw_snip_{os.getpid()}.png"

        env = dict(os.environ)
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
        if "XAUTHORITY" not in env and os.path.exists(os.path.expanduser("~/.Xauthority")):
            env["XAUTHORITY"] = os.path.expanduser("~/.Xauthority")

        try:
            if mode == "snippet":
                GLib.idle_add(self.hide)
                time.sleep(0.35)
                res = None
                try:
                    res = subprocess.run(["/usr/bin/maim", "-s", raw_tmp], env=env, timeout=45)
                except Exception as ex:
                    print(f"[MrFlow Sidebar] maim execution error: {ex}", file=sys.stderr)
                finally:
                    # Guarantees the sidebar is uncollapsed, focused, and visible
                    GLib.idle_add(self.show_sidebar)

                if not res or res.returncode != 0 or not os.path.exists(raw_tmp) or os.path.getsize(raw_tmp) == 0:
                    # If user cancelled maim or used external shortcut, check recent screenshot across directories
                    now = time.time()
                    recent_shots = []
                    check_dirs = [target_dir, "/opt/floworkos/screenshots", "/tmp"]
                    for c_dir in check_dirs:
                        if os.path.isdir(c_dir):
                            for f in os.listdir(c_dir):
                                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                                    fp = os.path.join(c_dir, f)
                                    try:
                                        mt = os.path.getmtime(fp)
                                        if now - mt < 30:
                                            recent_shots.append((mt, fp))
                                    except Exception:
                                        pass
                    if recent_shots:
                        recent_shots.sort(key=lambda x: x[0], reverse=True)
                        self._process_image_file(recent_shots[0][1])
                    return
            else:
                try:
                    subprocess.run(["/usr/bin/maim", raw_tmp], env=env, timeout=10)
                except Exception:
                    pass

            if not os.path.exists(raw_tmp):
                return

            from PIL import Image
            import io
            import base64

            with Image.open(raw_tmp) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                w, h = img.size
                max_w, max_h = 1280, 800
                if w > max_w or h > max_h:
                    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                img.save(dest_path, "JPEG", quality=75, optimize=True)

                thumb = img.copy()
                thumb.thumbnail((160, 100), Image.Resampling.LANCZOS)
                thumb_buf = io.BytesIO()
                thumb.save(thumb_buf, format="JPEG", quality=65)
                thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(thumb_buf.getvalue()).decode()

            size_bytes = os.path.getsize(dest_path)
            size_kb = round(size_bytes / 1024, 1)

            # Copy to clipboard via xclip so user can also paste it anywhere
            try:
                subprocess.run(["/usr/bin/xclip", "-selection", "clipboard", "-target", "image/png", "-i", dest_path], env=env, timeout=0.8, stderr=subprocess.DEVNULL)
            except Exception:
                pass

            payload = {
                "path": dest_path,
                "filename": os.path.basename(dest_path),
                "thumbnail": thumb_b64,
                "sizeKb": size_kb,
                "size_kb": size_kb
            }
            log_sidebar(f"User screenshot captured successfully: {dest_path} ({size_kb} KB)")
            js = f"if (window.onUserScreenshotCaptured) {{ window.onUserScreenshotCaptured({json.dumps(payload)}); }}"
            self._run_js(js)
        except Exception as e:
            log_sidebar(f"Screenshot error: {e}")
            print(f"[MrFlow Sidebar] Screenshot error: {e}", file=sys.stderr)
        finally:
            if os.path.exists(raw_tmp):
                try: os.unlink(raw_tmp)
                except Exception: pass

    def _save_pasted_image(self, base64_data):
        if not base64_data:
            return
        try:
            import base64
            from PIL import Image
            import io

            if "," in base64_data:
                base64_data = base64_data.split(",", 1)[1]
            raw_bytes = base64.b64decode(base64_data)

            home = os.environ.get("HOME") or HOME
            target_dir = os.path.join(home, "Pictures/Screenshots")
            os.makedirs(target_dir, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            dest_path = os.path.join(target_dir, f"User_Pasted_{ts}.jpg")

            with Image.open(io.BytesIO(raw_bytes)) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                w, h = img.size
                max_w, max_h = 1280, 800
                if w > max_w or h > max_h:
                    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                img.save(dest_path, "JPEG", quality=75, optimize=True)

                thumb = img.copy()
                thumb.thumbnail((160, 100), Image.Resampling.LANCZOS)
                thumb_buf = io.BytesIO()
                thumb.save(thumb_buf, format="JPEG", quality=65)
                thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(thumb_buf.getvalue()).decode()

            size_bytes = os.path.getsize(dest_path)
            size_kb = round(size_bytes / 1024, 1)

            payload = {
                "path": dest_path,
                "filename": os.path.basename(dest_path),
                "thumbnail": thumb_b64,
                "sizeKb": size_kb,
                "size_kb": size_kb
            }
            log_sidebar(f"Pasted image saved successfully: {dest_path} ({size_kb} KB)")
            js = f"if (window.onUserScreenshotCaptured) {{ window.onUserScreenshotCaptured({json.dumps(payload)}); }}"
            self._run_js(js)
        except Exception as e:
            log_sidebar(f"Pasted image error: {e}")
            print(f"[MrFlow Sidebar] Pasted image error: {e}", file=sys.stderr)

    def _check_and_paste_system_clipboard(self):
        try:
            now = time.time()
            if hasattr(self, "_last_clipboard_paste_time") and (now - self._last_clipboard_paste_time < 0.6):
                return False
            self._last_clipboard_paste_time = now

            cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            if cb.wait_is_image_available():
                pix = cb.wait_for_image()
                if pix:
                    self._process_clipboard_pixbuf(pix)
                    return True

            # Fallback 1: check uris (e.g. copied screenshot file from file manager)
            uris = cb.wait_for_uris()
            if uris:
                for uri in uris:
                    if uri.startswith("file://"):
                        local_p = uri[7:]
                        if os.path.exists(local_p) and any(local_p.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]):
                            self._process_image_file(local_p)
                            return True

            # Fallback 2: check xclip directly for image/png or image/jpeg
            try:
                env = dict(os.environ)
                if "DISPLAY" not in env: env["DISPLAY"] = ":0"
                if "XAUTHORITY" not in env and os.path.exists(os.path.expanduser("~/.Xauthority")):
                    env["XAUTHORITY"] = os.path.expanduser("~/.Xauthority")
                res = subprocess.run(["/usr/bin/xclip", "-selection", "clipboard", "-t", "image/png", "-o"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env, timeout=1.0)
                if res.returncode == 0 and res.stdout and len(res.stdout) > 32:
                    self._process_raw_image_bytes(res.stdout)
                    return True
            except Exception:
                pass

            # Fallback 3: check newest screenshot in ~/Pictures/Screenshots and /opt/floworkos/screenshots (last 5 minutes)
            home = os.environ.get("HOME") or HOME
            check_dirs = [os.path.join(home, "Pictures/Screenshots"), "/opt/floworkos/screenshots", "/tmp"]
            recent_shots = []
            for c_dir in check_dirs:
                if os.path.isdir(c_dir):
                    for f in os.listdir(c_dir):
                        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                            fp = os.path.join(c_dir, f)
                            try:
                                mt = os.path.getmtime(fp)
                                if now - mt < 300:
                                    recent_shots.append((mt, fp))
                            except Exception:
                                pass
            if recent_shots:
                recent_shots.sort(key=lambda x: x[0], reverse=True)
                self._process_image_file(recent_shots[0][1])
                return True

        except Exception as e:
            print(f"[MrFlow Sidebar] Clipboard check error: {e}", file=sys.stderr)
        return False

    def _process_image_file(self, file_path):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            self._process_raw_image_bytes(data)
        except Exception as e:
            print(f"[MrFlow Sidebar] Process file error: {e}", file=sys.stderr)

    def _process_raw_image_bytes(self, raw_bytes):
        try:
            from PIL import Image
            import io
            import base64

            with Image.open(io.BytesIO(raw_bytes)) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                w, h = img.size
                max_w, max_h = 1280, 800
                if w > max_w or h > max_h:
                    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

                home = os.environ.get("HOME") or HOME
                target_dir = os.path.join(home, "Pictures/Screenshots")
                os.makedirs(target_dir, exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                dest_path = os.path.join(target_dir, f"User_Pasted_{ts}.jpg")

                img.save(dest_path, "JPEG", quality=75, optimize=True)

                thumb = img.copy()
                thumb.thumbnail((160, 100), Image.Resampling.LANCZOS)
                thumb_buf = io.BytesIO()
                thumb.save(thumb_buf, format="JPEG", quality=65)
                thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(thumb_buf.getvalue()).decode()

                size_bytes = os.path.getsize(dest_path)
                size_kb = round(size_bytes / 1024, 1)

                payload = {
                    "path": dest_path,
                    "filename": os.path.basename(dest_path),
                    "thumbnail": thumb_b64,
                    "sizeKb": size_kb,
                    "size_kb": size_kb
                }
                log_sidebar(f"Pasted raw bytes saved successfully: {dest_path} ({size_kb} KB)")
                js = f"if (window.onUserScreenshotCaptured) {{ window.onUserScreenshotCaptured({json.dumps(payload)}); }}"
                self._run_js(js)
        except Exception as e:
            log_sidebar(f"Process raw bytes error: {e}")
            print(f"[MrFlow Sidebar] Process raw bytes error: {e}", file=sys.stderr)

    def _process_clipboard_pixbuf(self, pix):
        try:
            from PIL import Image
            import io
            import base64

            w, h = pix.get_width(), pix.get_height()
            pixels = pix.get_pixels()
            rowstride = pix.get_rowstride()
            n_channels = pix.get_n_channels()
            mode = "RGBA" if n_channels == 4 else "RGB"
            img = Image.frombytes(mode, (w, h), pixels, "raw", mode, rowstride)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Compress: max 1280x800, JPEG 75%
            max_w, max_h = 1280, 800
            if w > max_w or h > max_h:
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            home = os.environ.get("HOME") or HOME
            target_dir = os.path.join(home, "Pictures/Screenshots")
            os.makedirs(target_dir, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            dest_path = os.path.join(target_dir, f"User_Pasted_{ts}.jpg")

            img.save(dest_path, "JPEG", quality=75, optimize=True)

            thumb = img.copy()
            thumb.thumbnail((160, 100), Image.Resampling.LANCZOS)
            thumb_buf = io.BytesIO()
            thumb.save(thumb_buf, format="JPEG", quality=65)
            thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(thumb_buf.getvalue()).decode()

            size_bytes = os.path.getsize(dest_path)
            size_kb = round(size_bytes / 1024, 1)

            payload = {
                "path": dest_path,
                "filename": os.path.basename(dest_path),
                "thumbnail": thumb_b64,
                "sizeKb": size_kb,
                "size_kb": size_kb
            }
            log_sidebar(f"Clipboard pixbuf saved successfully: {dest_path} ({size_kb} KB)")
            js = f"if (window.onUserScreenshotCaptured) {{ window.onUserScreenshotCaptured({json.dumps(payload)}); }}"
            self._run_js(js)
        except Exception as e:
            log_sidebar(f"Process pixbuf error: {e}")
            print(f"[MrFlow Sidebar] Process pixbuf error: {e}", file=sys.stderr)

    def _abort_agent_turn(self):
        """Immediately and safely terminates running Mr. Flow agent and its child process tree."""
        log_sidebar("ABORT AGENT TURN REQUESTED")
        proc = self.active_agent_proc
        self.active_agent_proc = None

        if proc:
            pid = proc.pid
            # 1. KILL FIRST: Terminate entire process group with SIGKILL directly (0ms)
            # DO NOT close proc.stdout/stderr here! Closing a TextIOWrapper from another thread
            # deadlocks the GTK main loop because readline() holds the I/O stream lock.
            try:
                pgid = os.getpgid(pid)
                log_sidebar(f"Terminating process group {pgid} with SIGKILL")
                os.killpg(pgid, signal.SIGKILL)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

        # 2. Asynchronously eradicate any runaway mrflow wrappers, orphan node workers, and shell commands
        def async_kill_remnants():
            try:
                subprocess.run(["pkill", "-9", "-f", "mrflow"], timeout=0.5, stderr=subprocess.DEVNULL)
                subprocess.run(["pkill", "-9", "-f", "flowork_core"], timeout=0.5, stderr=subprocess.DEVNULL)
                subprocess.run(["pkill", "-9", "-f", "flowork-screenshot"], timeout=0.5, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        threading.Thread(target=async_kill_remnants, daemon=True).start()

        # Always clear current_session_id on abort so next message doesn't hit exit 42!
        self.current_session_id = None
        GLib.idle_add(lambda: self.webview.run_javascript("currentSessionId = '';", None, None, None))
        GLib.idle_add(self._dispatch_event, {"type": "cancelled", "message": "Execution stopped by user"})

    def _run_agent_turn(self, prompt, session_id, workspace):
        """Runs Mr. Flow CLI backend and streams line-by-line JSON events to WebKit."""
        log_sidebar(f"STARTING AGENT TURN: prompt='{prompt}', session_id='{session_id}', ws='{workspace}'")
        # Ensure any lingering or overlapping previous turn is terminated first
        if self.active_agent_proc:
            log_sidebar("Terminating overlapping previous agent turn")
            self._abort_agent_turn()
            time.sleep(0.05)

        cmd = ["/usr/local/bin/mrflow", "-p", prompt, "-o", "stream-json"]
        if session_id:
            cmd.extend(["--resume", session_id])

        # Allow access to Screenshots and temp directories outside workspace sandbox
        screenshots_dir = os.path.join(HOME, "Pictures", "Screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        for extra_dir in [screenshots_dir, "/opt/floworkos/screenshots", "/tmp"]:
            if os.path.isdir(extra_dir):
                cmd.extend(["--include-directories", extra_dir])

        env = dict(os.environ)
        env["TERM"] = "xterm-256color"
        env["HOME"] = HOME
        mrflow_env_path = "/opt/floworkos/system/mrflow.env"
        if os.path.exists(mrflow_env_path):
            try:
                with open(mrflow_env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("export "):
                            k, _, v = line[7:].partition("=")
                            env[k.strip()] = v.strip(' "\'')
            except Exception as e:
                log_sidebar(f"Failed to load mrflow.env: {e}")
        env.setdefault("FLOWORK_CONNECTOR_URL", "http://127.0.0.1:9099")
        env.setdefault("GOOGLE_GEMINI_BASE_URL", "http://127.0.0.1:9099")
        env.setdefault("FLOWORK_API_KEY", "flowork-sovereign-token")
        env.setdefault("GEMINI_API_KEY", "flowork-sovereign-token")

        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=workspace,
                env=env,
                start_new_session=True
            )
            self.active_agent_proc = proc

            stderr_lines = []
            def _drain_stderr(pipe):
                try:
                    for err_l in iter(pipe.readline, ''):
                        err_str = err_l.strip()
                        if err_str:
                            log_sidebar(f"AGENT STDERR: {err_str}")
                            stderr_lines.append(err_str)
                except Exception:
                    pass
                finally:
                    try:
                        pipe.close()
                    except Exception:
                        pass

            err_thread = threading.Thread(target=_drain_stderr, args=(proc.stderr,), daemon=True)
            err_thread.start()

            for line in iter(proc.stdout.readline, ''):
                trimmed = line.strip()
                if not trimmed:
                    continue

                if trimmed.startswith("{") and trimmed.endswith("}"):
                    try:
                        event = json.loads(trimmed)
                        if event.get("type") == "init":
                            self.current_session_id = event.get("session_id")

                        GLib.idle_add(self._dispatch_event, event)
                    except Exception:
                        pass

            try:
                proc.wait(timeout=0.1)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            ret = proc.returncode
            if ret in (-signal.SIGTERM, -signal.SIGKILL, 137, 143):
                log_sidebar(f"AGENT TURN FINISHED: exit={ret} (ABORTED INSTANTLY)")
                GLib.idle_add(self._dispatch_event, {"type": "cancelled", "message": "Execution stopped by user"})
                return

            err_thread.join(timeout=0.2)
            log_sidebar(f"AGENT TURN FINISHED: exit={ret}")
            if ret != 0:
                # Session corrupted (e.g. exit 42) or execution error
                if session_id:
                    log_sidebar(f"Resetting broken session_id={session_id} due to exit code {ret}")
                    self.current_session_id = None
                    GLib.idle_add(lambda: self.webview.run_javascript("currentSessionId = '';", None, None, None))
                err_text = "\n".join(stderr_lines[-3:]) if stderr_lines else f"Agent exited with code {ret}"
                GLib.idle_add(self._dispatch_event, {"type": "error", "message": err_text})
            else:
                GLib.idle_add(self._dispatch_event, {"type": "done"})

        except (ValueError, IOError, BrokenPipeError):
            log_sidebar("Agent turn stream closed cleanly upon abort.")
            GLib.idle_add(self._dispatch_event, {"type": "cancelled", "message": "Execution stopped by user"})
        except Exception as ex:
            log_sidebar(f"AGENT TURN EXCEPTION: {ex}")
            GLib.idle_add(self._dispatch_event, {"type": "error", "message": str(ex)})
        finally:
            self.active_agent_proc = None
            if proc:
                try:
                    if proc.stdout and not proc.stdout.closed:
                        proc.stdout.close()
                except Exception:
                    pass
                try:
                    if proc.stderr and not proc.stderr.closed:
                        proc.stderr.close()
                except Exception:
                    pass

    def _dispatch_event(self, event):
        # DOKTRIN KEDAULATAN: Injeksi baris kode nyata langsung dari disk / parameter
        # Tidak boleh ada kode dummy pada visualisasi view & write
        if event.get("type") == "tool_use":
            tool_name = (event.get("tool_name") or "").lower()
            params = event.get("parameters") or {}

            # 1. READ / VIEW FILE: Baca baris nyata langsung dari disk
            if any(k in tool_name for k in ("read", "view", "cat", "inspect", "open")):
                fpath = params.get("file_path") or params.get("AbsolutePath") or params.get("path") or params.get("filename") or params.get("TargetFile")
                if fpath:
                    full_path = os.path.expanduser(fpath)
                    if os.path.isfile(full_path):
                        try:
                            start_line = int(params.get("start_line") or params.get("StartLine") or 1)
                            end_line = int(params.get("end_line") or params.get("EndLine") or (start_line + 15))
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                all_lines = f.readlines()
                                total = len(all_lines)
                                s_idx = max(0, start_line - 1)
                                e_idx = min(total, max(s_idx + 8, min(s_idx + 12, end_line)))
                                real_slice = [l.rstrip("\r\n") for l in all_lines[s_idx:e_idx]]
                                if not real_slice and all_lines:
                                    real_slice = [l.rstrip("\r\n") for l in all_lines[:10]]
                                params["_real_file_lines"] = real_slice
                                params["_start_line_actual"] = s_idx + 1
                                params["_total_lines"] = total
                                params["_file_size_bytes"] = os.path.getsize(full_path)
                        except Exception:
                            pass

            # 2. WRITE / EDIT / REPLACE: Ekstrak baris kode nyata yang sedang ditulis
            if any(k in tool_name for k in ("write", "replace", "edit", "patch", "modify")):
                content_text = params.get("CodeContent") or params.get("content") or params.get("ReplacementContent") or params.get("replacement") or ""
                if content_text:
                    lines = [l.rstrip("\r\n") for l in content_text.split("\n") if l.strip()]
                    params["_real_code_lines"] = lines[:12]
                    params["_code_bytes"] = len(content_text.encode("utf-8"))

        js = f"window.onAgentEvent({json.dumps(event)});"
        self.webview.run_javascript(js, None, None, None)

    def show_sidebar(self):
        self._update_geometry()
        self.resize(self.sidebar_w, self.sidebar_h)
        self.move(self.pos_x, self.pos_y)
        win = self.get_window()
        if win:
            try:
                xid = win.get_xid()
                subprocess.run(["xdotool", "windowsize", str(xid), str(self.sidebar_w), str(self.sidebar_h)], check=False)
                subprocess.run(["xdotool", "windowmove", str(xid), str(self.pos_x), str(self.pos_y)], check=False)
            except Exception:
                pass
        self.stick()
        self.set_keep_above(True)
        self.show_all()
        self.present()
        self.set_focus(self.webview)
        self.is_open = True
        self.last_mouse_inside = time.time()
        self.mouse_has_entered = False
        self.webview.run_javascript("document.body.classList.remove('is-collapsed'); setTimeout(() => document.getElementById('userInput')?.focus(), 50);", None, None, None)
        self._apply_struts(True)

    def collapse_sidebar(self, force=False):
        if self.is_pinned and not force:
            return
        self._apply_struts(False)
        self.is_open = False
        collapsed_w = 16
        if self.position == "left":
            cx = 0
        else:
            cx = self.screen_w - collapsed_w
        self.resize(collapsed_w, self.sidebar_h)
        self.move(cx, self.pos_y)
        win = self.get_window()
        if win:
            try:
                xid = win.get_xid()
                subprocess.run(["xdotool", "windowsize", str(xid), str(collapsed_w), str(self.sidebar_h)], check=False)
                subprocess.run(["xdotool", "windowmove", str(xid), str(cx), str(self.pos_y)], check=False)
            except Exception:
                pass
        self.stick()
        self.set_keep_above(True)
        self.show_all()
        self.present()
        self.webview.run_javascript("document.body.classList.add('is-collapsed');", None, None, None)

    def hide_sidebar(self, force=False):
        self.collapse_sidebar(force=force)

    def toggle_sidebar(self):
        if self.is_open:
            self.collapse_sidebar(force=True)
        else:
            self.show_sidebar()

    def on_destroy(self, widget):
        self._apply_struts(False)
        if os.path.exists(SOCKET_PATH):
            try:
                os.unlink(SOCKET_PATH)
            except Exception:
                pass


def socket_server_thread(app_window):
    """Listens for toggle/show/hide commands from CLI."""
    if os.path.exists(SOCKET_PATH):
        try:
            os.unlink(SOCKET_PATH)
        except Exception:
            pass

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)
    os.chmod(SOCKET_PATH, 0o777)

    while True:
        try:
            conn, _ = server.accept()
            conn.settimeout(2.0)
            raw = conn.recv(65536).decode("utf-8").strip()
            if raw:
                try:
                    msg = json.loads(raw)
                except Exception:
                    msg = {"action": raw}

                action = msg.get("action", "toggle")
                if action == "toggle":
                    GLib.idle_add(app_window.toggle_sidebar)
                elif action == "show":
                    GLib.idle_add(app_window.show_sidebar)
                elif action == "hide":
                    GLib.idle_add(lambda: app_window.hide_sidebar(force=True))
                elif action in ("abort", "stop", "abort_agent"):
                    GLib.idle_add(app_window._abort_agent_turn)
                elif action in ("toggle_hover_peek", "set_hover_peek"):
                    val = msg.get("enabled")
                    GLib.idle_add(lambda: app_window.set_hover_peek_mode(not app_window.hover_to_open if val is None else bool(val)))
                elif action == "toggle_pin":
                    GLib.idle_add(lambda: app_window.set_pinned_mode(not app_window.is_pinned))
                elif action == "new_chat":
                    GLib.idle_add(lambda: app_window.webview.run_javascript("document.getElementById('btnNewChat')?.click();", None, None, None))
                elif action == "status":
                    state = {
                        "is_open": app_window.is_open,
                        "is_pinned": app_window.is_pinned,
                        "hover_to_open": app_window.hover_to_open,
                        "is_busy": app_window.active_agent_proc is not None
                    }
                    conn.sendall(json.dumps(state).encode("utf-8") + b"\n")
                    conn.close()
                    continue
                elif action == "ping":
                    pass
                elif action == "eval_js":
                    code = msg.get("code", "")
                    GLib.idle_add(lambda c=code: app_window.webview.run_javascript(c, None, None, None))
                elif action == "send_prompt":
                    prompt = msg.get("prompt", "")
                    GLib.idle_add(lambda p=prompt: threading.Thread(target=app_window._run_agent_turn, args=(p, app_window.current_session_id, app_window.current_workspace), daemon=True).start())
                elif action == "dispatch_event":
                    ev = msg.get("event", {})
                    GLib.idle_add(app_window._dispatch_event, ev)

            conn.sendall(b"OK\n")
            conn.close()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass


def send_socket_command(action, extra=None):
    """Attempts to send command to existing running instance."""
    if not os.path.exists(SOCKET_PATH):
        return False
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2.0)
        client.connect(SOCKET_PATH)
        payload = {"action": action}
        if extra and isinstance(extra, dict):
            payload.update(extra)
        client.sendall(json.dumps(payload).encode("utf-8"))
        res = client.recv(1024)
        client.close()
        return res.strip() == b"OK"
    except Exception as e:
        return False


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "toggle"

    # Client CLI actions: toggle, show, hide, ping, eval_js, send_prompt
    if action in ["toggle", "show", "hide", "ping"]:
        if send_socket_command(action):
            sys.exit(0)
        else:
            # If socket command failed and action is ping, exit 1
            if action == "ping":
                sys.exit(1)
            # Try to start via systemd if installed
            subprocess.run(["systemctl", "--user", "start", "flowork-mrflow-sidebar.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            if send_socket_command(action):
                sys.exit(0)
            if action == "hide":
                sys.exit(0)

    # If action is daemon or running standalone
    if action == "daemon" or action == "standalone":
        # Check if already running via socket
        if send_socket_command("ping"):
            sys.exit(0)

        # Atomic kernel flock to prevent concurrent startup race conditions
        lock_file_path = f"/tmp/mrflow-sidebar-{USER}.lock"
        try:
            global_lock_fd = open(lock_file_path, "w")
            fcntl.flock(global_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, BlockingIOError):
            log_sidebar(f"Another instance already holds the lock on {lock_file_path}. Exiting.")
            sys.exit(0)

        app = MrFlowSidebar()

        # Start socket server
        t = threading.Thread(target=socket_server_thread, args=(app,), daemon=True)
        t.start()

        # Auto-show or hide on start
        if action == "daemon":
            if app.config.get("auto_show_on_start", True):
                app.show_sidebar()
            else:
                app.hide_sidebar()
        else:
            app.show_sidebar()

        Gtk.main()
        sys.exit(0)

    # Fallback for unrecognized action or direct run
    if not send_socket_command(action):
        lock_file_path = f"/tmp/mrflow-sidebar-{USER}.lock"
        try:
            global_lock_fd = open(lock_file_path, "w")
            fcntl.flock(global_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, BlockingIOError):
            sys.exit(0)

        app = MrFlowSidebar()
        t = threading.Thread(target=socket_server_thread, args=(app,), daemon=True)
        t.start()
        app.show_sidebar()
        Gtk.main()


if __name__ == "__main__":
    main()
