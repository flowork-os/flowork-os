#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Sovereign Command Deck (Orbit 2.0)
# Ultra-Modern Frosted Glass Command Center & Application Deck
# Zero Windows, Zero macOS — 100% Bespoke Sovereign Architecture.
# Features: Real Favorites, Real Recents, Instant Search, Agent Prompts,
#           and 1-Click Sovereign Wallpaper Switcher.
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================

import os
import sys
import signal
import subprocess
import glob
import xml.etree.ElementTree as ET
import urllib.parse
import gi

try:
    sys.path.insert(0, "/opt/floworkos/connector")
    import flowfs_core
except Exception:
    flowfs_core = None

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib, Pango

PID_FILE = f"/run/user/{os.getuid()}/flowork-orbit.pid"

def check_single_instance():
    """Toggle orbit: if already open, kill existing and exit."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, signal.SIGTERM)
            try:
                os.remove(PID_FILE)
            except OSError:
                pass
            sys.exit(0)
        except (ProcessLookupError, ValueError):
            pass
        except Exception:
            pass

    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

class OrbitDeckWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Flowork Sovereign Deck")
        self.set_role("orbit_deck")

        # Dimensions: 880px wide x 580px high
        self.set_default_size(880, 580)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

        self.all_apps = []
        self.favorites = []
        self.recents = []
        self.current_filter = "ALL"
        self.visible_items = []
        self.selected_index = 0

        self._setup_css()
        self._build_ui()
        self._load_data()

        self.connect("key-press-event", self._on_key_press)
        self.connect("focus-out-event", self._on_focus_out)
        self.connect("destroy", self._on_destroy)

        self._mouse_entered = False
        self._ticks_outside = 0
        self._start_time = GLib.get_monotonic_time()
        GLib.timeout_add(100, self._check_mouse_leave)

    def _setup_css(self):
        css = b'''
        window {
            background-color: transparent;
        }

        .deck-frame {
            background-color: rgba(6, 10, 18, 0.88);
            border: 1.5px solid rgba(0, 242, 254, 0.45);
            border-radius: 26px;
            box-shadow: 0 24px 64px rgba(0, 0, 0, 0.90), inset 0 1px 0 rgba(255, 255, 255, 0.25);
            padding: 24px 28px;
        }

        .deck-title {
            color: #00f2fe;
            font-family: 'JetBrains Mono', monospace;
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 1px;
        }

        .deck-close-btn {
            background-color: rgba(244, 63, 94, 0.12);
            border: 1px solid rgba(244, 63, 94, 0.40);
            border-radius: 8px;
            color: #f43f5e;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            font-weight: 800;
            padding: 3px 10px;
            min-width: 28px;
            min-height: 24px;
            transition: all 120ms ease;
        }
        .deck-close-btn:hover {
            background-color: #f43f5e;
            border-color: #f43f5e;
            color: #ffffff;
            box-shadow: 0 0 14px rgba(244, 63, 94, 0.60);
        }

        .deck-badge {
            background: rgba(0, 255, 136, 0.12);
            border: 1px solid rgba(0, 255, 136, 0.35);
            border-radius: 8px;
            color: #00ff88;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
        }

        .omni-search-input {
            background-color: rgba(14, 22, 36, 0.75);
            border: 1.5px solid rgba(0, 242, 254, 0.35);
            border-radius: 14px;
            color: #ffffff;
            font-family: 'Inter', system-ui, sans-serif;
            font-size: 15px;
            padding: 12px 18px;
            caret-color: #00f2fe;
            transition: all 150ms ease;
        }
        .omni-search-input:focus {
            background-color: rgba(18, 28, 48, 0.95);
            border-color: #00f2fe;
            box-shadow: 0 0 16px rgba(0, 242, 254, 0.45);
        }

        .tab-btn {
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 10px;
            color: #8c9cb8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            padding: 6px 14px;
            transition: all 120ms ease;
        }
        .tab-btn:hover {
            background-color: rgba(0, 242, 254, 0.15);
            border-color: rgba(0, 242, 254, 0.45);
            color: #00f2fe;
        }
        .tab-btn-active {
            background: linear-gradient(180deg, rgba(0, 242, 254, 0.35) 0%, rgba(13, 22, 38, 0.8) 100%);
            border: 1px solid #00f2fe;
            color: #ffffff;
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.4);
        }

        .item-card {
            background-color: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 14px;
            padding: 10px 14px;
            margin: 3px 0;
            transition: all 100ms ease;
        }
        .item-card:hover, .item-card-selected {
            background-color: rgba(0, 242, 254, 0.14);
            border-color: rgba(0, 242, 254, 0.50);
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.25);
        }

        .item-name {
            color: #ffffff;
            font-family: 'Inter', system-ui, sans-serif;
            font-size: 14px;
            font-weight: 600;
        }
        .item-desc {
            color: #7b8ea8;
            font-size: 11px;
            font-family: 'Inter', system-ui, sans-serif;
        }
        .item-badge {
            background: rgba(0, 242, 254, 0.15);
            border: 1px solid rgba(0, 242, 254, 0.35);
            border-radius: 6px;
            color: #00f2fe;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            padding: 3px 8px;
        }

        .wallpaper-pill {
            background: rgba(0, 242, 254, 0.10);
            border: 1px solid rgba(0, 242, 254, 0.30);
            border-radius: 8px;
            color: #00f2fe;
            font-size: 10px;
            font-family: 'JetBrains Mono', monospace;
            padding: 4px 8px;
        }
        .wallpaper-pill:hover {
            background: #00f2fe;
            color: #030712;
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
        self.frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.frame.get_style_context().add_class('deck-frame')
        self.add(self.frame)

        # 1. Top Header Bar
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title = Gtk.Label(label="[ F _ ]  FLOWORK SOVEREIGN DECK")
        title.get_style_context().add_class('deck-title')
        header.pack_start(title, False, False, 0)

        spacer = Gtk.Box()
        header.pack_start(spacer, True, True, 0)

        telemetry = Gtk.Label(label="● ENGINE ACTIVE │ LINUX 7.3.0 RUST │ LSM TIER 3")
        telemetry.get_style_context().add_class('deck-badge')
        header.pack_start(telemetry, False, False, 0)

        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class('deck-close-btn')
        close_btn.set_tooltip_text("Close Deck (Esc)")
        close_btn.connect("clicked", lambda b: self._close())
        header.pack_end(close_btn, False, False, 0)

        self.frame.pack_start(header, False, False, 0)

        # 2. Omni Search Entry
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search apps, recent files, type > for Mr. Flow, ? for Brain...")
        self.search_entry.get_style_context().add_class('omni-search-input')
        self.search_entry.connect("changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_activate)
        self.frame.pack_start(self.search_entry, False, False, 0)

        # 3. Filter Navigation Tabs & 1-Click Wallpaper Switcher
        nav_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.tab_buttons = {}

        tabs = [
            ("ALL", "🚀 ALL APPS"),
            ("FAVORITES", "★ FAVORITES"),
            ("RECENT", "🕒 RECENT"),
            ("AGENT", "⚡ MR. FLOW"),
            ("FLOWFS", "🧠 FLOWFS"),
            ("WALLPAPER", "🖼️ WALLPAPER")
        ]

        for tab_id, tab_label in tabs:
            btn = Gtk.Button(label=tab_label)
            btn.get_style_context().add_class('tab-btn')
            if tab_id == "ALL":
                btn.get_style_context().add_class('tab-btn-active')
            btn.connect("clicked", self._on_tab_clicked, tab_id)
            nav_row.pack_start(btn, False, False, 0)
            self.tab_buttons[tab_id] = btn

        self.frame.pack_start(nav_row, False, False, 0)

        # 4. Results Scroller
        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroller.set_shadow_type(Gtk.ShadowType.NONE)

        self.results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.scroller.add(self.results_box)
        self.frame.pack_start(self.scroller, True, True, 4)

    def _load_data(self):
        # 1. Load All Apps
        apps = Gio.AppInfo.get_all()
        seen = set()
        for a in sorted(apps, key=lambda x: x.get_display_name().lower()):
            if not a.should_show():
                continue
            name = a.get_display_name()
            if name in seen:
                continue
            seen.add(name)

            self.all_apps.append({
                "type": "app",
                "name": name,
                "desc": a.get_description() or "Sovereign Desktop Application",
                "cmd": a.get_executable() or "",
                "app_info": a,
                "icon": a.get_icon()
            })

        # 2. Hardened Sovereign Favorites
        fav_definitions = [
            ("Flowork Stealth Browser", "Camoufox Fingerprint-Hardened Web Browser", "flowork-stealth", "security-medium"),
            ("Flowork Cyber Hub", "Sovereign Pentest & Reconnaissance Operations Center", "/usr/local/bin/flowork-cyber-hub", "security-high"),
            ("DiskCraft", "Sovereign Disk Cleaner, Storage Treemap & System Hygiene", "/opt/floworkos/bin/diskcraft", "drive-harddisk"),
            ("SherlockCraft", "Sovereign OSINT Digital Identity Explorer", "/opt/floworkos/bin/sherlockcraft", "system-search"),
            ("FlowRepo", "Sovereign GitHub Historical Vault & Open-Source Hall of Fame", "/opt/floworkos/bin/flow-repo", "starred"),
            ("Kamidi Mastering Pro", "Professional Audio Mastering Suite & DSP Console", "/opt/floworkos/bin/kamidi-mastering", "kamidi-mastering"),
            ("Cutvii Studio Hub", "Sovereign Canvas & Media Production Suite", "cutvii", "multimedia-video-player"),
            ("Alacritty Terminal", "GPU-Accelerated 0.60 Glass HUD Terminal", "alacritty", "utilities-terminal"),
            ("Nemo Sovereign Vault", "Sovereign File Manager with 11 Pinned Bookmarks", "nemo /opt/floworkos", "system-file-manager"),
            ("Flowork Screenshot", "Sovereign Glass Snipping & Desktop Capture", "flowork-screenshot", "applets-screenshooter"),
            ("Flowork Connector GUI", "Local Inference Proxy & Multi-Account Rotator (:9099)", "google-chrome --app=http://127.0.0.1:9099/gui", "network-server"),
            ("System Settings", "Configure Displays, Audio, Hardware & Preferences", "cinnamon-settings", "preferences-system"),
            ("Google Chrome", "Fast, sovereign web exploration", "google-chrome", "google-chrome")
        ]
        for name, desc, cmd, icon_name in fav_definitions:
            self.favorites.append({
                "type": "fav",
                "name": name,
                "desc": desc,
                "cmd": cmd,
                "icon_name": icon_name
            })

        # 3. Load Real Recently Used Items (from ~/.local/share/recently-used.xbel)
        recent_file = os.path.expanduser("~/.local/share/recently-used.xbel")
        if os.path.exists(recent_file):
            try:
                tree = ET.parse(recent_file)
                root = tree.getroot()
                for bookmark in reversed(root.findall(".//bookmark")):
                    href = bookmark.attrib.get("href", "")
                    if href.startswith("file://"):
                        local_path = urllib.parse.unquote(href[7:])
                        if os.path.exists(local_path):
                            fname = os.path.basename(local_path)
                            self.recents.append({
                                "type": "recent",
                                "name": fname,
                                "desc": local_path,
                                "cmd": f"xdg-open {repr(local_path)}",
                                "icon_name": "text-x-generic"
                            })
                            if len(self.recents) >= 12:
                                break
            except Exception:
                pass

        # If recents still empty, provide system quick items
        if not self.recents:
            self.recents = [
                {"type": "recent", "name": "ARCHITECT.md", "desc": "/opt/floworkos/ARCHITECT.md", "cmd": "x-terminal-emulator -e less /opt/floworkos/ARCHITECT.md", "icon_name": "text-x-generic"},
                {"type": "recent", "name": "Active Triggers", "desc": "/opt/floworkos/system/triger", "cmd": "nemo /opt/floworkos/system/triger", "icon_name": "folder"},
                {"type": "recent", "name": "Flowork Connector Logs", "desc": "/tmp/flowork_connector.log", "cmd": "x-terminal-emulator -e tail -f /tmp/flowork_connector.log", "icon_name": "utilities-terminal"}
            ]

        # 4. Wallpaper Presets
        self.wallpapers = [
            {"type": "wall", "name": "Flowork Quantum Obsidian (Default)", "desc": "Bespoke Void with www.floworkos.com & Cyber Lattice", "cmd": "feh --bg-fill /opt/floworkos/theme/flowork-quantum-wallpaper.png", "icon_name": "preferences-desktop-wallpaper"},
            {"type": "wall", "name": "Monterey Dark Glass", "desc": "Deep indigo vector wave", "cmd": "feh --bg-fill /opt/floworkos/theme/wallpapers/Monterey-dark.jpg", "icon_name": "preferences-desktop-wallpaper"},
            {"type": "wall", "name": "Sonoma Dark Glass", "desc": "Minimalist obsidian horizon", "cmd": "feh --bg-fill /opt/floworkos/theme/wallpapers/Sonoma-dark.jpg", "icon_name": "preferences-desktop-wallpaper"},
            {"type": "wall", "name": "Open System Settings -> Backgrounds", "desc": "Browse and select any custom wallpaper image", "cmd": "cinnamon-settings backgrounds", "icon_name": "preferences-system"}
        ]

        # Initial Render
        self._render_tab("ALL")

    def _render_tab(self, tab_id):
        self.current_filter = tab_id
        for tid, btn in self.tab_buttons.items():
            ctx = btn.get_style_context()
            if tid == tab_id:
                if not ctx.has_class('tab-btn-active'):
                    ctx.add_class('tab-btn-active')
            else:
                ctx.remove_class('tab-btn-active')

        if tab_id == "ALL":
            items = self.favorites[:3] + self.all_apps[:12]
        elif tab_id == "FAVORITES":
            items = self.favorites
        elif tab_id == "RECENT":
            items = self.recents
        elif tab_id == "AGENT":
            items = [
                {"type": "agent", "name": "⚡ Mr. Flow Autonomous Shell", "desc": "Start interactive CLI cognitive loop", "cmd": "alacritty -e mrflow", "icon_name": "utilities-terminal"},
                {"type": "agent", "name": "🔍 Query Knowledge Vault (.fl_brain)", "desc": "Search active lessons, rules and architecture", "cmd": "alacritty -e mrflow search", "icon_name": "system-search"},
                {"type": "agent", "name": "🛡️ Landlock Security Sandbox", "desc": "Inspect 5-tier policy enforcement engine", "cmd": "nemo /opt/floworkos/policies", "icon_name": "security-high"}
            ]
        elif tab_id == "FLOWFS":
            items = self._get_flowfs_overview()
        elif tab_id == "WALLPAPER":
            items = self.wallpapers

        self._render_items(items)

    def _get_flowfs_overview(self):
        items = []
        if flowfs_core:
            try:
                conn = flowfs_core.init_db()
                cur = conn.cursor()
                cur.execute("SELECT filename, path, snippet FROM flow_documents ORDER BY mtime DESC LIMIT 8")
                for r in cur.fetchall():
                    items.append({
                        "type": "flowfs",
                        "name": f"🧠 {r[0]}",
                        "desc": (r[2] or r[1])[:75],
                        "path": r[1],
                        "cmd": f"xdg-open {repr(r[1])}",
                        "icon_name": "text-x-generic"
                    })
                conn.close()
            except Exception:
                pass
        if not items:
            items.append({
                "type": "flowfs",
                "name": "🧠 FlowFS Semantic Search Engine",
                "desc": "Type '?' followed by query in search bar (e.g. ? Landlock security)",
                "path": "",
                "cmd": "",
                "icon_name": "system-search"
            })
        return items

    def _query_flowfs(self, query, limit=8):
        items = []
        if not flowfs_core or not query.strip():
            return items
        try:
            results = flowfs_core.semantic_search(query, limit=limit)
            for r in results:
                score_pct = int(min(1.0, r["score"]) * 100)
                items.append({
                    "type": "flowfs",
                    "name": f"🧠 {r['filename']} ({score_pct}%)",
                    "desc": (r.get("snippet") or r["path"])[:75],
                    "path": r["path"],
                    "cmd": f"xdg-open {repr(r['path'])}",
                    "icon_name": "text-x-generic"
                })
        except Exception:
            pass
        return items

    def _render_items(self, items):
        for ch in self.results_box.get_children():
            self.results_box.remove(ch)

        self.visible_items = items
        self.selected_index = 0

        if not items:
            lbl = Gtk.Label(label="No items found.")
            lbl.get_style_context().add_class('item-desc')
            self.results_box.pack_start(lbl, True, True, 20)
            self.results_box.show_all()
            return

        for idx, it in enumerate(items):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            row.get_style_context().add_class('item-card')
            if idx == 0:
                row.get_style_context().add_class('item-card-selected')

            # Icon
            if it.get("icon"):
                img = Gtk.Image.new_from_gicon(it["icon"], Gtk.IconSize.LARGE_TOOLBAR)
            else:
                ic_name = it.get("icon_name", "application-x-executable")
                if os.path.exists(ic_name):
                    try:
                        from gi.repository import GdkPixbuf
                        pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(ic_name, 34, 34, True)
                        img = Gtk.Image.new_from_pixbuf(pb)
                    except Exception:
                        img = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.LARGE_TOOLBAR)
                else:
                    img = Gtk.Image.new_from_icon_name(ic_name, Gtk.IconSize.LARGE_TOOLBAR)
            img.set_pixel_size(34)
            row.pack_start(img, False, False, 4)

            # Details
            details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name_lbl = Gtk.Label(label=it["name"])
            name_lbl.set_xalign(0)
            name_lbl.get_style_context().add_class('item-name')
            details.pack_start(name_lbl, False, False, 0)

            desc_lbl = Gtk.Label(label=it["desc"])
            desc_lbl.set_xalign(0)
            desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            desc_lbl.set_max_width_chars(65)
            desc_lbl.get_style_context().add_class('item-desc')
            details.pack_start(desc_lbl, False, False, 0)

            row.pack_start(details, True, True, 0)

            # Badge
            badge = Gtk.Label(label=it["type"].upper())
            badge.get_style_context().add_class('item-badge')
            row.pack_end(badge, False, False, 4)

            ev = Gtk.EventBox()
            ev.set_visible_window(False)
            ev.add(row)
            ev.connect("button-press-event", self._on_item_click, idx)

            self.results_box.pack_start(ev, False, False, 0)

        self.results_box.show_all()

    def _on_tab_clicked(self, widget, tab_id):
        self._render_tab(tab_id)

    def _on_item_click(self, widget, event, idx):
        if event.button == 1:
            self._execute_item(self.visible_items[idx])

    def _execute_item(self, it):
        cmd = it.get("cmd", "")
        itype = it.get("type")

        if itype == "agent" and it.get("prompt"):
            subprocess.Popen(["alacritty", "-e", "bash", "-c", f"mrflow run {repr(it['prompt'])}; read"])
        elif itype == "wall":
            os.system(f"{cmd} &")
        elif itype == "flowfs":
            path = it.get("path")
            if path and os.path.exists(path):
                ext = os.path.splitext(path)[1].lower()
                if ext in (".md", ".txt", ".py", ".rs", ".json", ".conf", ".sh", ".c", ".h"):
                    subprocess.Popen(["x-terminal-emulator", "-e", "less", path])
                else:
                    subprocess.Popen(["xdg-open", path])
        elif itype == "app" and it.get("app_info"):
            try:
                it["app_info"].launch([], None)
            except Exception:
                os.system(f"{cmd} &")
        else:
            os.system(f"{cmd} &")

        # Auto-close after launch
        self._close()

    def _on_search_changed(self, entry):
        q = entry.get_text().strip()
        if not q:
            self._render_tab(self.current_filter)
            return

        if q.startswith(">"):
            prompt = q[1:].strip()
            self._render_items([{
                "type": "agent",
                "name": f"⚡ Run with Mr. Flow: {prompt if prompt else 'Type objective...'}",
                "desc": "Autonomous agent task execution loop",
                "prompt": prompt,
                "cmd": ""
            }])
            return

        if q.startswith("?") or q.startswith("/"):
            semantic_q = q.lstrip("?/").strip()
            if semantic_q:
                self._render_items(self._query_flowfs(semantic_q, limit=10))
            else:
                self._render_items([{
                    "type": "flowfs",
                    "name": "🧠 FlowFS Vector Search Mode",
                    "desc": "Type keyword or concept to search files & code semantically...",
                    "cmd": "",
                    "icon_name": "system-search"
                }])
            return

        if self.current_filter == "FLOWFS":
            self._render_items(self._query_flowfs(q, limit=10))
            return

        q_lower = q.lower()
        matched = []
        for it in self.favorites + self.all_apps + self.recents:
            if q_lower in it["name"].lower() or q_lower in it["desc"].lower():
                matched.append(it)
                if len(matched) >= 12:
                    break

        # Enrich with FlowFS semantic results if few app matches and query length >= 3
        if len(matched) < 5 and len(q) >= 3 and flowfs_core:
            flowfs_matches = self._query_flowfs(q, limit=4)
            matched.extend(flowfs_matches)

        self._render_items(matched)

    def _on_activate(self, entry):
        if self.visible_items and 0 <= self.selected_index < len(self.visible_items):
            self._execute_item(self.visible_items[self.selected_index])

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self._close()
            return True

        children = self.results_box.get_children()
        if not children:
            return False

        if event.keyval in (Gdk.KEY_Down, Gdk.KEY_Tab):
            if self.selected_index < len(children) - 1:
                self._set_selected(self.selected_index + 1)
            return True
        elif event.keyval in (Gdk.KEY_Up, Gdk.KEY_ISO_Left_Tab):
            if self.selected_index > 0:
                self._set_selected(self.selected_index - 1)
            return True

        return False

    def _set_selected(self, index):
        children = self.results_box.get_children()
        if 0 <= self.selected_index < len(children):
            row = children[self.selected_index].get_child()
            row.get_style_context().remove_class('item-card-selected')

        self.selected_index = index
        if 0 <= self.selected_index < len(children):
            row = children[self.selected_index].get_child()
            row.get_style_context().add_class('item-card-selected')

    def _check_mouse_leave(self):
        try:
            display = Gdk.Display.get_default()
            seat = display.get_default_seat()
            pointer = seat.get_pointer()
            _, mx, my = pointer.get_position()

            win_x, win_y = self.get_position()
            win_w, win_h = self.get_size()

            inside = (win_x <= mx <= win_x + win_w) and (win_y <= my <= win_y + win_h)
            if inside:
                self._mouse_entered = True
                self._ticks_outside = 0
            else:
                elapsed = (GLib.get_monotonic_time() - self._start_time) / 1000000.0
                if self._mouse_entered or elapsed > 1.5:
                    self._ticks_outside += 1
                    if self._ticks_outside >= 3:
                        self._close()
                        return False
        except Exception:
            pass
        return True

    def _on_focus_out(self, widget, event):
        self._close()
        return False

    def _close(self):
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except OSError:
            pass
        self.destroy()
        Gtk.main_quit()

    def _on_destroy(self, widget):
        self._close()

def main():
    check_single_instance()
    win = OrbitDeckWindow()
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
