#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Sovereign Muelle Dock (Pure Optical Crystal Glass)
# Mathematical Magnification, Drag & Drop, Muelle Launch Physics & Genie Beam
# Genie Launch & Genie Close Effects (Zero Side Blur), Open Running Apps Tracking,
# Tutorial Mouse Click Locator Circle, Pure Optical Glass Gtk.Menu Context Menu
# Fully Native GTK3 + Cairo + Xlib Architecture (Zero Plank, Zero Ctrl-keys)
# Ported and enhanced from crafter-station/muelle core mathematical models.
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================

import os
import sys
import math
import time
import json
import signal
import subprocess
import threading
import glob
from typing import List, Dict, Optional, Tuple, Set

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
import cairo

try:
    from Xlib import display, X, protocol
    from Xlib.xobject import drawable
    XLIB_AVAILABLE = True
except Exception:
    XLIB_AVAILABLE = False

try:
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
except Exception:
    pass

# --- CONSTANTS & MUELLE PHYSICS PARAMETERS ---
REST_ICON_SIZE = 48.0
PADDING_X = 14.0
PADDING_Y = 10.0
GAP = 10.0
PILL_HEIGHT = 68.0

# Magnification (from muelle-core/src/magnify.rs)
MAGNIFY_RANGE = 180.0
MAGNIFY_MAX_SCALE = 1.48

# Bounce Physics (from muelle-core/src/bounce.rs)
HOP_SECONDS = 0.52
BOUNCE_HEIGHT = 28.0
MAX_HOPS = 3

# Drag & Drop Threshold (12.0px prevents accidental drag on human micro-jitter)
DRAG_THRESHOLD = 12.0
UNPIN_DRAG_DISTANCE = 24.0  # Pixels dragged above dock to trigger unpin/close

# Pure Optical Crystal Glass Colors
ACCENT_GREEN = (0.0, 1.0, 0.4)           # #00ff66 Flowork Emerald
ACCENT_GREEN_HEX = "#00ff66"
GLASS_SPECULAR_RIM = (1.0, 1.0, 1.0, 0.45)
GLASS_BASE_TOP = (0.08, 0.12, 0.16, 0.78)
GLASS_BASE_BOT = (0.04, 0.06, 0.08, 0.88)

CONFIG_DIR = os.path.expanduser("~/.config/flowork")
CONFIG_FILE = os.path.join(CONFIG_DIR, "dock.json")
DEFAULT_CONFIG_FILE = "/opt/floworkos/theme/dock-default.json"

IGNORE_CLASSES = {
    'xfce4-panel', 'plank', 'flowork-muelle-dock', 'mrflow-sidebar',
    'muellegenielaunch', 'muellegenieclose', 'floworkglassmenu',
    'desktop', 'xfdesktop', 'slop', 'fl-terminal-dropdown'
}

DOCK_INSTANCE = None

# =============================================================================
# 📐 MATHEMATICAL MODELS (PORTED FROM MUELLE-CORE)
# =============================================================================

def falloff(d: float) -> float:
    """Inverted smoothstep curve f(d) = 1 − 3d² + 2d³: 1 under cursor, 0 from d=1 onward."""
    d = min(abs(d), 1.0)
    return 1.0 - 3.0 * d * d + 2.0 * d * d * d

def falloff_integral(u: float) -> float:
    """Integral of falloff from 0 to u, odd and clamped at ±1/2."""
    d = min(abs(u), 1.0)
    val = d - d**3 + (d**4) / 2.0
    return math.copysign(val, u)

class CriticallyDampedSpring:
    """Critically damped spring solver for settling icon widths without overshoot."""
    def __init__(self, initial_value: float = 0.0, omega: float = 26.0):
        self.value = initial_value
        self.target = initial_value
        self.velocity = 0.0
        self.omega = omega

    def step(self, dt: float):
        if abs(self.target - self.value) < 0.001 and abs(self.velocity) < 0.001:
            self.value = self.target
            self.velocity = 0.0
            return
        decay = math.exp(-self.omega * dt)
        distance = self.value - self.target
        c = self.velocity + self.omega * distance
        next_val = (distance + c * dt) * decay
        self.velocity = (c - self.omega * (distance + c * dt)) * decay
        self.value = self.target + next_val

# =============================================================================
# 🌟 GENIE OPENING & CLOSING EFFECTS (ZERO SIDE BLUR)
# =============================================================================

class GenieLaunchEffect:
    """Retired in favor of system-wide Picom Quantum Spring-Zoom & Glass Shimmer."""
    def __init__(self, *args, **kwargs):
        pass

class GenieCloseEffect:
    """Retired in favor of system-wide Picom Quantum Spring-Zoom & Glass Shimmer."""
    def __init__(self, *args, **kwargs):
        pass


# =============================================================================
# 🚀 SOVEREIGN MUELLE DOCK CONTROLLER & WINDOW
# =============================================================================

class SovereignMuelleDock(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        self.set_title("Flowork Sovereign Muelle Dock")
        self.set_role("flowork_dock")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_accept_focus(False)
        self.set_app_paintable(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.apply_glass_css()

        self.items: List[Dict] = []
        self.known_window_geoms: Dict[int, Tuple[float, float, float, float]] = {}
        self.desktop_cache: Dict[str, Dict] = {}

        # Physics & Animation State
        self.cursor_x: Optional[float] = None
        self.magnify_amount = CriticallyDampedSpring(0.0, omega=26.0)
        self.press_info: Optional[Dict] = None
        self.is_dragging: bool = False
        self.dragging_idx: Optional[int] = None
        self.drag_x: float = 0.0
        self.drag_y: float = 0.0
        self.drag_removing: bool = False
        self.active_ripples: List[Dict] = []
        self.bouncing_items: Dict[int, float] = {}
        self.press_depressions: Dict[int, float] = {}
        self.right_clicked_idx: Optional[int] = None

        # Intellihide / Auto-hide on Open Apps State
        self.hide_spring = CriticallyDampedSpring(0.0, omega=22.0)
        self.is_hovered: bool = False
        self.last_hover_time: float = time.time()
        self.has_open_app: bool = False
        self.is_menu_open: bool = False
        self.base_win_x: int = 0
        self.base_win_y: int = 0
        self.window_width: int = 588
        self.window_height: int = 110
        self.hidden_distance: int = 107
        self.current_win_y: int = 0

        self.build_desktop_cache()
        self.load_dock_config()

        self.connect("draw", self.on_draw)
        self.connect("enter-notify-event", self.on_enter)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("leave-notify-event", self.on_leave)

        self.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.ENTER_NOTIFY_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.BUTTON1_MOTION_MASK |
            Gdk.EventMask.BUTTON_MOTION_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK
        )

        self.last_tick = time.time()
        GLib.timeout_add(16, self.on_animation_frame)
        GLib.timeout_add(200, self.update_running_windows)

        screen.connect("size-changed", lambda s: self.update_geometry())
        self.update_geometry()
        self.show_all()

    def apply_glass_css(self):
        """Applies Pure Optical Crystal Glass CSS styling to Gtk.Menu context menu."""
        css = """
        menu.flowork-glass-menu {
            background-color: rgba(10, 16, 22, 0.94);
            border: 1.2px solid rgba(0, 255, 102, 0.45);
            border-radius: 16px;
            padding: 6px;
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.6);
        }
        menu.flowork-glass-menu menuitem {
            color: #f2f2f2;
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
        }
        menu.flowork-glass-menu menuitem:hover {
            background-color: rgba(0, 255, 102, 0.18);
            color: #00ff66;
            border: 1px solid rgba(0, 255, 102, 0.5);
        }
        menu.flowork-glass-menu separator {
            background-color: rgba(255, 255, 255, 0.12);
            min-height: 1px;
            margin: 4px 6px;
        }
        """
        provider = Gtk.CssProvider()
        try:
            provider.load_from_data(css.encode())
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # 📁 DESKTOP CACHE & CONFIGURATION MANAGEMENT
    # -------------------------------------------------------------------------

    def build_desktop_cache(self):
        """Builds fast lookup cache from .desktop files across the system."""
        self.desktop_cache = {}
        paths = glob.glob("/usr/share/applications/*.desktop") + \
                glob.glob(os.path.expanduser("~/.local/share/applications/*.desktop"))

        for df in paths:
            try:
                kf = GLib.KeyFile()
                if kf.load_from_file(df, GLib.KeyFileFlags.NONE):
                    def g(k):
                        try: return kf.get_string("Desktop Entry", k)
                        except Exception: return ""

                    if g("NoDisplay").lower() == "true" or g("Hidden").lower() == "true":
                        continue

                    name = g("Name")
                    cls = g("StartupWMClass").lower()
                    exec_cmd = g("Exec")
                    exec_bin = os.path.basename(exec_cmd.split()[0]).lower() if exec_cmd else ""
                    icon = g("Icon")
                    stem = os.path.splitext(os.path.basename(df))[0].lower()

                    entry = {
                        "name": name,
                        "desktop": df,
                        "exec": " ".join([arg for arg in exec_cmd.split() if not arg.startswith("%")]),
                        "icon": icon,
                        "wm_class": cls or exec_bin
                    }
                    if cls: self.desktop_cache[cls] = entry
                    if exec_bin: self.desktop_cache[exec_bin] = entry
                    if name: self.desktop_cache[name.lower()] = entry
                    if stem: self.desktop_cache[stem] = entry
            except Exception:
                pass

    def load_dock_config(self):
        """Loads pinned dock applications from json."""
        self.items = []
        raw_items = []

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    raw_items = json.load(f)
            except Exception as e:
                print(f"[Dock] Error reading config: {e}", file=sys.stderr)

        if not raw_items and os.path.exists(DEFAULT_CONFIG_FILE):
            try:
                with open(DEFAULT_CONFIG_FILE, "r") as f:
                    raw_items = json.load(f)
            except Exception:
                pass

        if not raw_items:
            raw_items = [
                {"desktop": "/usr/share/applications/Alacritty.desktop"},
                {"desktop": "/usr/share/applications/nemo.desktop"},
                {"desktop": "/usr/share/applications/google-chrome.desktop"},
                {"desktop": "/usr/share/applications/flowork-launchpad.desktop"},
                {"desktop": "/usr/share/applications/flowork-screenshot.desktop"},
                {"desktop": "/usr/share/applications/flowork-stealth.desktop"},
                {"desktop": "/usr/share/applications/mrflow-agent.desktop"},
                {"uri": "trash:///"}
            ]

        theme = Gtk.IconTheme.get_default()
        for entry in raw_items:
            item = self.resolve_dock_item(entry, theme)
            if item:
                self.items.append(item)

    def resolve_dock_item(self, entry: Dict, theme) -> Optional[Dict]:
        """Resolves desktop file or URI into an actionable dock item."""
        if entry.get("uri") == "trash:///":
            pb = self.load_icon_pixbuf("user-trash", theme)
            return {
                "name": "Trash",
                "uri": "trash:///",
                "exec": "nemo trash:///",
                "icon": "user-trash",
                "pixbuf": pb,
                "pinned": True,
                "is_running": False,
                "wid": None,
                "wids": set()
            }

        desktop_path = entry.get("desktop")
        if not desktop_path or not os.path.exists(desktop_path):
            candidates = glob.glob(f"/usr/share/applications/*{desktop_path}*")
            if candidates:
                desktop_path = candidates[0]
            else:
                return None

        kf = GLib.KeyFile()
        try:
            if not kf.load_from_file(desktop_path, GLib.KeyFileFlags.NONE):
                return None
        except Exception:
            return None

        def get_key(k):
            try: return kf.get_string("Desktop Entry", k)
            except Exception: return ""

        name = get_key("Name") or os.path.splitext(os.path.basename(desktop_path))[0]
        exec_cmd = get_key("Exec")
        icon_name = get_key("Icon") or "application-x-executable"
        wm_class = get_key("StartupWMClass")

        exec_clean = " ".join([arg for arg in exec_cmd.split() if not arg.startswith("%")])
        pb = self.load_icon_pixbuf(icon_name, theme)

        return {
            "name": name,
            "desktop": desktop_path,
            "exec": exec_clean,
            "icon": icon_name,
            "wm_class": wm_class or os.path.basename(exec_clean.split()[0] if exec_clean else ""),
            "pixbuf": pb,
            "pinned": entry.get("pinned", True),
            "is_running": False,
            "wid": None,
            "wids": set()
        }

    def load_icon_pixbuf(self, icon_name_or_path: str, theme, size: int = int(REST_ICON_SIZE)):
        """High-resolution icon resolver with crisp scaling."""
        if os.path.isabs(icon_name_or_path) and os.path.exists(icon_name_or_path):
            try:
                return GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_name_or_path, size, size, True)
            except Exception:
                pass

        for lookup in [icon_name_or_path, icon_name_or_path.lower(), "application-x-executable"]:
            try:
                return theme.load_icon(lookup, size, Gtk.IconLookupFlags.FORCE_SIZE)
            except Exception:
                continue
        return None

    def save_dock_config(self):
        """Persists current pinned dock items to disk."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        export_data = []
        for it in self.items:
            if it.get("pinned", True):
                if it.get("uri"):
                    export_data.append({"uri": it["uri"], "pinned": True})
                elif it.get("desktop"):
                    export_data.append({"desktop": it["desktop"], "pinned": True})

        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(export_data, f, indent=2)
            if os.access("/opt/floworkos/theme", os.W_OK):
                with open(DEFAULT_CONFIG_FILE, "w") as f:
                    json.dump(export_data, f, indent=2)
        except Exception as e:
            print(f"[Dock] Error saving config: {e}", file=sys.stderr)

    # -------------------------------------------------------------------------
    # 📐 RESPONSIVE GEOMETRY & CENTERING (COMPACT, NO RESTRICTIVE INPUT MASK)
    # -------------------------------------------------------------------------

    def update_geometry(self):
        """Calculates centered window size matching the dock pill closely."""
        screen = self.get_screen()
        display = screen.get_display()
        mon = display.get_primary_monitor() or (display.get_monitor(0) if display.get_n_monitors() > 0 else None)
        geom = mon.get_geometry() if mon else Gdk.Rectangle()
        if geom.width == 0:
            geom.width, geom.height = 2560, 1080

        num_items = max(len(self.items), 1)
        resting_dock_width = PADDING_X * 2 + num_items * REST_ICON_SIZE + (num_items - 1) * GAP

        # Window size fits the pill plus small margin for magnification
        window_width = int(resting_dock_width + 48)
        window_height = int(PILL_HEIGHT + BOUNCE_HEIGHT + 14)  # ~110px

        win_x = geom.x + (geom.width - window_width) // 2
        win_y = geom.y + geom.height - window_height - 6

        self.base_win_x = win_x
        self.base_win_y = win_y
        self.window_width = window_width
        self.window_height = window_height
        self.hidden_distance = window_height - 14

        self.set_size_request(window_width, window_height)
        cur_offset = int(self.hide_spring.value * self.hidden_distance)
        self.current_win_y = win_y + cur_offset
        self.move(win_x, self.current_win_y)

    # -------------------------------------------------------------------------
    # 🪟 WINDOW TRACKING (X11), OPEN UNPINNED APPS & GENIE CLOSE
    # -------------------------------------------------------------------------

    def update_running_windows(self):
        """Syncs active running applications and detects window closures for Genie Close."""
        if not XLIB_AVAILABLE:
            return True

        try:
            d = display.Display()
            root = d.screen().root
            net_client_list = d.intern_atom('_NET_CLIENT_LIST')
            net_wm_name = d.intern_atom('_NET_WM_NAME')
            net_wm_state = d.intern_atom('_NET_WM_STATE')
            net_wm_hidden = d.intern_atom('_NET_WM_STATE_HIDDEN')
            net_curr_desktop = d.intern_atom('_NET_CURRENT_DESKTOP')
            net_wm_desktop = d.intern_atom('_NET_WM_DESKTOP')
            net_wm_type = d.intern_atom('_NET_WM_WINDOW_TYPE')
            atom_dock = d.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')
            atom_desktop = d.intern_atom('_NET_WM_WINDOW_TYPE_DESKTOP')

            curr_desk_prop = root.get_full_property(net_curr_desktop, X.AnyPropertyType)
            curr_desk = curr_desk_prop.value[0] if curr_desk_prop else 0

            clients = root.get_full_property(net_client_list, X.AnyPropertyType)
            active_wids: Set[int] = set()
            current_geoms: Dict[int, Tuple[float, float, float, float]] = {}
            theme = Gtk.IconTheme.get_default()
            open_apps_found = False

            if clients:
                for wid in clients.value:
                    try:
                        w = d.create_resource_object('window', wid)

                        # Skip docks, panels, and desktop backgrounds
                        types = w.get_full_property(net_wm_type, X.AnyPropertyType)
                        if types and (atom_dock in types.value or atom_desktop in types.value):
                            continue

                        # Check workspace
                        desk = w.get_full_property(net_wm_desktop, X.AnyPropertyType)
                        win_desk = desk.value[0] if (desk and desk.value and len(desk.value) > 0) else curr_desk
                        is_curr_desk = (win_desk in (curr_desk, 4294967295))

                        cls = w.get_wm_class()
                        if not cls:
                            continue
                        c1, c2 = cls[0].lower(), cls[1].lower()
                        if c1 in IGNORE_CLASSES or c2 in IGNORE_CLASSES:
                            continue

                        geom = w.get_geometry()
                        if geom.width < 160 or geom.height < 100:
                            continue

                        # Determine visibility (not minimized/hidden)
                        attrs = w.get_attributes()
                        state = w.get_full_property(net_wm_state, X.AnyPropertyType)
                        is_hidden = (state and net_wm_hidden in state.value)
                        is_viewable = (attrs.map_state == X.IsViewable and not is_hidden)

                        if is_curr_desk and is_viewable:
                            open_apps_found = True

                        active_wids.add(wid)
                        try:
                            tr = root.translate_coords(w, 0, 0)
                            if tr:
                                current_geoms[wid] = (float(tr.x), float(tr.y), float(geom.width), float(geom.height))
                        except Exception:
                            if wid in self.known_window_geoms:
                                current_geoms[wid] = self.known_window_geoms[wid]

                        name_prop = w.get_full_property(net_wm_name, X.AnyPropertyType)
                        if name_prop:
                            val = name_prop.value
                            if isinstance(val, tuple):
                                val = val[1]
                            title = val.decode('utf-8', 'ignore') if isinstance(val, (bytes, bytearray)) else str(val)
                        else:
                            title = cls[0]

                        # Check if already in items
                        matched_item = None
                        for it in self.items:
                            target_cls = it.get("wm_class", "").lower()
                            target_exec = os.path.basename(it.get("exec", "").split()[0]).lower() if it.get("exec") else ""
                            it_wids = it.get("wids", set())
                            if (target_cls and target_cls in (c1, c2)) or (target_exec and target_exec in (c1, c2)) or (it.get("name") and it.get("name", "").lower() == title.lower()) or (it.get("wid") == wid) or (wid in it_wids):
                                matched_item = it
                                break

                        if matched_item:
                            matched_item["is_running"] = True
                            matched_item["wid"] = wid
                            if "wids" not in matched_item or not isinstance(matched_item["wids"], set):
                                matched_item["wids"] = {wid}
                            else:
                                matched_item["wids"].add(wid)
                        else:
                            # Open running app that is NOT yet on the dock -> Add dynamically!
                            desktop_entry = self.desktop_cache.get(c1) or self.desktop_cache.get(c2) or self.desktop_cache.get(title.lower())
                            if desktop_entry:
                                pb = self.load_icon_pixbuf(desktop_entry.get("icon", "application-x-executable"), theme)
                                new_item = {
                                    "name": desktop_entry.get("name", title),
                                    "desktop": desktop_entry.get("desktop"),
                                    "exec": desktop_entry.get("exec"),
                                    "icon": desktop_entry.get("icon"),
                                    "wm_class": c1,
                                    "pixbuf": pb,
                                    "pinned": False,
                                    "is_running": True,
                                    "wid": wid,
                                    "wids": {wid}
                                }
                            else:
                                pb = self.load_icon_pixbuf("application-x-executable", theme)
                                new_item = {
                                    "name": title,
                                    "desktop": None,
                                    "exec": None,
                                    "icon": "application-x-executable",
                                    "wm_class": c1,
                                    "pixbuf": pb,
                                    "pinned": False,
                                    "is_running": True,
                                    "wid": wid,
                                    "wids": {wid}
                                }

                            # Insert before Trash if trash exists, else append
                            if len(self.items) > 0 and self.items[-1].get("uri") == "trash:///":
                                self.items.insert(len(self.items) - 1, new_item)
                            else:
                                self.items.append(new_item)
                            self.update_geometry()
                    except Exception:
                        continue

            # DETECT WINDOW CLOSURES -> FIRE GENIE CLOSE EFFECT!
            closed_wids = set(self.known_window_geoms.keys()) - active_wids
            win_x, win_y = self.get_position()
            state = self.calculate_magnified_layout(self.get_allocated_width())

            for c_wid in closed_wids:
                last_g = self.known_window_geoms.get(c_wid)
                slot_cx = win_x + (self.get_allocated_width() / 2.0)
                slot_cy = win_y + (self.get_allocated_height() - PILL_HEIGHT / 2.0)

                for i, it in enumerate(self.items):
                    it_wids = it.get("wids", set())
                    if it.get("wid") == c_wid or c_wid in it_wids:
                        if i < len(state):
                            slot_cx = win_x + state[i]["center_x"]
                            slot_cy = win_y + state[i]["y"] + state[i]["height"] / 2.0

                        if isinstance(it.get("wids"), set):
                            it["wids"].discard(c_wid)
                            remaining = it["wids"]
                        else:
                            remaining = set()

                        if not remaining:
                            it["is_running"] = False
                            it["wid"] = None
                            if not it.get("pinned", True):
                                if it in self.items:
                                    self.items.remove(it)
                                    self.update_geometry()
                        else:
                            it["wid"] = next(iter(remaining))
                        break

                if last_g:
                    GenieCloseEffect(last_g[0], last_g[1], last_g[2], last_g[3], slot_cx, slot_cy)

            self.known_window_geoms = current_geoms

            # Update running state and prune closed unpinned items
            for it in list(self.items):
                if isinstance(it.get("wids"), set):
                    it["wids"] = it["wids"] & active_wids
                    if not it["wids"]:
                        it["is_running"] = False
                        it["wid"] = None
                        if not it.get("pinned", True):
                            if it in self.items:
                                self.items.remove(it)
                                self.update_geometry()
                    else:
                        it["is_running"] = True
                        if it.get("wid") not in it["wids"]:
                            it["wid"] = next(iter(it["wids"]))
                else:
                    if it.get("wid") and it["wid"] not in active_wids:
                        it["is_running"] = False
                        it["wid"] = None
                        if not it.get("pinned", True):
                            if it in self.items:
                                self.items.remove(it)
                                self.update_geometry()

            self.has_open_app = open_apps_found
            d.close()
            self.queue_draw()
        except Exception:
            pass
        return True

    # -------------------------------------------------------------------------
    # 🎬 60 FPS ANIMATION LOOP (MAGNIFY, BOUNCE, RIPPLE, PRESS)
    # -------------------------------------------------------------------------

    def on_animation_frame(self):
        now = time.time()
        dt = min(now - self.last_tick, 0.05)
        self.last_tick = now

        # 1. Global pointer tracking for reliable autohide peek & trigger
        try:
            display = Gdk.Display.get_default()
            seat = display.get_default_seat() if display else None
            pointer = seat.get_pointer() if seat else None
            if pointer and self.window_width > 0:
                screen, root_x, root_y = pointer.get_position()
                mon = display.get_primary_monitor() or (display.get_monitor(0) if display.get_n_monitors() > 0 else None)
                geom = mon.get_geometry() if mon else Gdk.Rectangle()
                screen_bottom = geom.y + geom.height

                # Bottom edge trigger zone: bottom 18px of screen, horizontally spanning dock +/- 80px
                in_bottom_trigger = (root_y >= screen_bottom - 18) and ((self.base_win_x - 80) <= root_x <= (self.base_win_x + self.window_width + 80))
                # Active dock area when shown or partially shown
                in_dock_bounds = ((self.base_win_x - 10) <= root_x <= (self.base_win_x + self.window_width + 10)) and (self.current_win_y - 15 <= root_y <= screen_bottom)

                if in_bottom_trigger or in_dock_bounds:
                    self.is_hovered = True
                    self.last_hover_time = now
                else:
                    if (now - self.last_hover_time) > 0.28:
                        self.is_hovered = False
        except Exception:
            pass

        # 2. Intellihide state logic
        # - Mouse hovered / dragging / menu open -> ALWAYS SHOW!
        # - Apps open and mouse NOT over dock -> HIDE!
        # - No apps open (clean desktop) -> STAY SHOWN!
        if self.is_hovered or self.is_dragging or getattr(self, "is_menu_open", False):
            self.hide_spring.target = 0.0
        elif self.has_open_app:
            self.hide_spring.target = 1.0
        else:
            self.hide_spring.target = 0.0

        # When actively hiding/retracting, cancel icon magnification
        if self.hide_spring.value > 0.25:
            self.magnify_amount.target = 0.0

        # 3. Step springs & animate smooth window translation
        self.magnify_amount.step(dt)

        prev_hide = self.hide_spring.value
        self.hide_spring.step(dt)
        if abs(self.hide_spring.value - prev_hide) > 0.0005:
            new_y = self.base_win_y + int(self.hide_spring.value * self.hidden_distance)
            if new_y != self.current_win_y:
                self.current_win_y = new_y
                self.move(self.base_win_x, new_y)

        dead_ripples = []
        for r in self.active_ripples:
            r["progress"] = (now - r["start_time"]) / r["duration"]
            if r["progress"] >= 1.0:
                dead_ripples.append(r)
        for r in dead_ripples:
            self.active_ripples.remove(r)

        dead_bounces = []
        for idx, start_t in self.bouncing_items.items():
            if now - start_t >= HOP_SECONDS * MAX_HOPS:
                dead_bounces.append(idx)
        for idx in dead_bounces:
            del self.bouncing_items[idx]

        dead_press = []
        for idx, start_t in self.press_depressions.items():
            if now - start_t >= 0.15:
                dead_press.append(idx)
        for idx in dead_press:
            del self.press_depressions[idx]

        self.queue_draw()
        return True

    # -------------------------------------------------------------------------
    # 🖱️ MOUSE EVENT HANDLING (CLICK, DRAG, RIGHT-CLICK)
    # -------------------------------------------------------------------------

    def get_slot_center(self, idx: int, win_w: int) -> float:
        num_items = len(self.items)
        dock_w = PADDING_X * 2 + num_items * REST_ICON_SIZE + (num_items - 1) * GAP
        dock_x = (win_w - dock_w) / 2.0
        return dock_x + PADDING_X + idx * (REST_ICON_SIZE + GAP) + REST_ICON_SIZE / 2.0

    def on_enter(self, widget, event):
        self.is_hovered = True
        self.last_hover_time = time.time()
        return False

    def on_motion(self, widget, event):
        self.is_hovered = True
        self.last_hover_time = time.time()
        win_w = max(self.get_allocated_width(), 200)
        win_h = max(self.get_allocated_height(), 100)

        num_items = len(self.items)
        dock_w = PADDING_X * 2 + num_items * REST_ICON_SIZE + (num_items - 1) * GAP
        dock_origin_x = (win_w - dock_w) / 2.0
        dock_origin_y = win_h - PILL_HEIGHT - 6.0

        near = (dock_origin_x - 30 <= event.x <= dock_origin_x + dock_w + 30) and \
               (dock_origin_y - 25 <= event.y <= win_h + 10)

        if near or self.is_dragging:
            self.cursor_x = event.x - dock_origin_x
            self.magnify_amount.target = 1.0
        else:
            self.cursor_x = None
            self.magnify_amount.target = 0.0

        # Handle Dragging
        if self.press_info:
            dx = event.x - self.press_info["start_x"]
            dy = event.y - self.press_info["start_y"]

            if not self.is_dragging and math.hypot(dx, dy) >= DRAG_THRESHOLD:
                self.is_dragging = True
                self.dragging_idx = self.press_info["index"]

            if self.is_dragging:
                self.drag_x = event.x
                self.drag_y = event.y

                if event.y < dock_origin_y - UNPIN_DRAG_DISTANCE:
                    self.drag_removing = True
                else:
                    self.drag_removing = False
                    if self.dragging_idx is not None and self.dragging_idx < len(self.items):
                        cur_idx = self.dragging_idx
                        # Prevent dragging Trash or moving items past Trash
                        max_swap = len(self.items) - 1
                        if len(self.items) > 0 and self.items[-1].get("uri") == "trash:///":
                            max_swap = len(self.items) - 2

                        if cur_idx <= max_swap and self.items[cur_idx].get("uri") != "trash:///":
                            SWAP_DEADBAND = 14.0
                            # Swap left if cursor crossed midpoint into left slot past deadband
                            if cur_idx > 0:
                                mid_left = (self.get_slot_center(cur_idx - 1, win_w) + self.get_slot_center(cur_idx, win_w)) / 2.0
                                if event.x < (mid_left - SWAP_DEADBAND):
                                    item = self.items.pop(cur_idx)
                                    self.items.insert(cur_idx - 1, item)
                                    self.dragging_idx = cur_idx - 1
                                    self.press_info["index"] = cur_idx - 1
                            # Swap right if cursor crossed midpoint into right slot past deadband
                            if cur_idx < max_swap:
                                mid_right = (self.get_slot_center(cur_idx, win_w) + self.get_slot_center(cur_idx + 1, win_w)) / 2.0
                                if event.x > (mid_right + SWAP_DEADBAND):
                                    item = self.items.pop(cur_idx)
                                    self.items.insert(cur_idx + 1, item)
                                    self.dragging_idx = cur_idx + 1
                                    self.press_info["index"] = cur_idx + 1

        self.queue_draw()
        return True

    def on_button_press(self, widget, event):
        win_w = self.get_allocated_width()
        item_idx = self.get_item_under_mouse(event.x, win_w)

        if event.button == 1:  # Left Click
            # Compact circular click locator ("efek bulat kecil")
            self.active_ripples.append({
                "x": event.x,
                "y": event.y,
                "start_time": time.time(),
                "duration": 0.28,
                "progress": 0.0,
                "color": ACCENT_GREEN
            })

            if item_idx is not None:
                self.press_info = {
                    "index": item_idx,
                    "start_x": event.x,
                    "start_y": event.y,
                    "time": time.time(),
                    "item": self.items[item_idx]
                }
                self.press_depressions[item_idx] = time.time()

            self.queue_draw()
            return True

        elif event.button == 3:  # Right Click
            # Compact circular click locator (Cyan for right click)
            self.active_ripples.append({
                "x": event.x,
                "y": event.y,
                "start_time": time.time(),
                "duration": 0.28,
                "progress": 0.0,
                "color": (0.0, 1.0, 0.8)
            })

            if item_idx is not None:
                item = self.items[item_idx]
                self.right_clicked_idx = item_idx
                self.show_context_menu(item, event)

            self.queue_draw()
            return True

        return False

    def on_button_release(self, widget, event):
        if event.button == 1:
            if self.is_dragging:
                if self.dragging_idx is not None and self.dragging_idx < len(self.items):
                    if self.drag_removing:
                        self.unpin_item(self.dragging_idx)
                    else:
                        dropped_item = self.items[self.dragging_idx]
                        dropped_item["pinned"] = True
                        self.save_dock_config()

                self.is_dragging = False
                self.dragging_idx = None
                self.press_info = None
                self.drag_removing = False
                self.queue_draw()
                return True

            if self.press_info:
                idx = self.press_info["index"]
                if idx < len(self.items):
                    item = self.items[idx]
                    self.launch_item(item, slot_idx=idx)

                self.press_info = None
                self.queue_draw()
                return True
        return False

    def on_leave(self, widget, event):
        self.last_hover_time = time.time()
        if not self.is_dragging:
            self.cursor_x = None
            self.magnify_amount.target = 0.0
            self.queue_draw()
        return True

    def get_item_under_mouse(self, mouse_x: float, win_w: int) -> Optional[int]:
        if not self.items:
            return None
        state = self.calculate_magnified_layout(win_w)
        best_idx = None
        best_dist = float('inf')
        for i, rect in enumerate(state):
            dist = abs(mouse_x - rect["center_x"])
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        if best_idx is not None and best_dist <= (REST_ICON_SIZE * 1.5):
            return best_idx
        return None

    # -------------------------------------------------------------------------
    # 💎 PURE OPTICAL CRYSTAL GLASS CONTEXT MENU (GTK.MENU NATIVE & BULLETPROOF)
    # -------------------------------------------------------------------------

    def show_context_menu(self, item: Dict, event):
        """Displays native GTK context menu styled with pure crystal glass."""
        self.is_menu_open = True
        menu = Gtk.Menu()
        menu.set_name("flowork-glass-menu")

        header_item = Gtk.MenuItem()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        pb = item.get("pixbuf")
        if pb:
            scale = 22.0 / max(pb.get_width(), pb.get_height())
            scaled_pb = pb.scale_simple(int(pb.get_width() * scale), int(pb.get_height() * scale), GdkPixbuf.InterpType.BILINEAR)
            img = Gtk.Image.new_from_pixbuf(scaled_pb)
            box.pack_start(img, False, False, 0)

        lbl = Gtk.Label(label=f"<b>{item.get('name', 'Application')}</b>")
        lbl.set_use_markup(True)
        box.pack_start(lbl, False, False, 0)
        header_item.add(box)
        header_item.set_sensitive(False)
        menu.append(header_item)

        menu.append(Gtk.SeparatorMenuItem())

        open_item = Gtk.MenuItem(label="⚡ Open / New Window")
        open_item.connect("activate", lambda w: self.launch_item(item, force_new=True))
        menu.append(open_item)

        is_pinned = item.get("pinned", True)
        pin_label = "✓ Keep in Dock" if is_pinned else "  Keep in Dock"
        pin_item = Gtk.MenuItem(label=pin_label)
        pin_item.connect("activate", lambda w: self.toggle_pin_item(item))
        menu.append(pin_item)

        if item.get("is_running") or item.get("wid"):
            close_item = Gtk.MenuItem(label="🔴 Close")
            close_item.connect("activate", lambda w: self.close_item_windows(item))
            menu.append(close_item)

        menu.connect("selection-done", lambda m: self.on_menu_dismissed())
        menu.attach_to_widget(self, None)
        menu.show_all()
        try:
            menu.popup_at_pointer(event)
        except Exception:
            button = event.button if hasattr(event, 'button') else 3
            ev_time = event.time if hasattr(event, 'time') else Gtk.get_current_event_time()
            menu.popup(None, None, None, None, button, ev_time)

    def on_menu_dismissed(self):
        self.is_menu_open = False
        self.last_hover_time = time.time()
        self.right_clicked_idx = None
        self.queue_draw()

    # -------------------------------------------------------------------------
    # ⚡ APPLICATION LAUNCHING, GENIE & FOCUS / MINIMIZE TOGGLE
    # -------------------------------------------------------------------------

    def get_active_window_id(self) -> Optional[int]:
        """Returns the currently active window ID via _NET_ACTIVE_WINDOW."""
        try:
            if XLIB_AVAILABLE:
                d = display.Display()
                root = d.screen().root
                net_active_win = d.intern_atom('_NET_ACTIVE_WINDOW')
                prop = root.get_full_property(net_active_win, X.AnyPropertyType)
                d.close()
                if prop and prop.value and len(prop.value) > 0 and prop.value[0] > 0:
                    return int(prop.value[0])
        except Exception:
            pass
        try:
            out = subprocess.check_output(["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL).decode().strip()
            return int(out) if out else None
        except Exception:
            return None

    def minimize_window_by_id(self, wid: int) -> bool:
        """Minimizes specific window ID via xdotool and X11 WM_CHANGE_STATE."""
        try:
            subprocess.run(["xdotool", "windowminimize", str(wid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except Exception:
            pass
        if not XLIB_AVAILABLE:
            return False
        try:
            d = display.Display()
            root = d.screen().root
            wm_change_state = d.intern_atom('WM_CHANGE_STATE')
            w = d.create_resource_object('window', wid)

            event = protocol.event.ClientMessage(
                window=w,
                client_type=wm_change_state,
                data=(32, [3, 0, 0, 0, 0])
            )
            root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
            d.flush()
            d.close()
            return True
        except Exception:
            return False

    def focus_window_by_id(self, wid: int) -> bool:
        """Brings specific window ID to front, unminimizes if hidden, and raises focus."""
        try:
            # 1. Unminimize / move to current workspace and raise via wmctrl -R
            subprocess.run(["wmctrl", "-i", "-R", str(wid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # 2. Activate via xdotool for foolproof window focus
            subprocess.run(["xdotool", "windowactivate", "--sync", str(wid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

        if not XLIB_AVAILABLE:
            return False

        try:
            d = display.Display()
            root = d.screen().root
            net_active_win = d.intern_atom('_NET_ACTIVE_WINDOW')
            w = d.create_resource_object('window', wid)

            event = protocol.event.ClientMessage(
                window=w,
                client_type=net_active_win,
                data=(32, [2, X.CurrentTime, 0, 0, 0])
            )
            root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
            d.flush()
            d.close()
            return True
        except Exception:
            return False

    def launch_item(self, item: Dict, slot_idx: Optional[int] = None, force_new: bool = False):
        """Launches app or brings existing running window to front (Never minimizes on click)."""
        if slot_idx is None:
            try:
                slot_idx = self.items.index(item)
            except ValueError:
                slot_idx = 0

        win_x, win_y = self.get_position()
        state = self.calculate_magnified_layout(self.get_allocated_width())
        if slot_idx < len(state):
            slot_cx = win_x + state[slot_idx]["center_x"]
            slot_cy = win_y + state[slot_idx]["y"]
        else:
            slot_cx = win_x + (self.get_allocated_width() / 2.0)
            slot_cy = win_y + (self.get_allocated_height() / 2.0)

        now = time.time()

        # Rapid accidental double-click debouncing when launching new process
        if not force_new and not (item.get("is_running") or item.get("wid")):
            if now - item.get("_last_launch_time", 0) < 2.0:
                self.bouncing_items[slot_idx] = now
                return
            item["_last_launch_time"] = now

        # Running application handling: Toggle Show/Focus vs Hide/Minimize
        if not force_new and (item.get("is_running") or item.get("wid")):
            item_wids = item.get("wids")
            if isinstance(item_wids, (set, list)):
                wids_set = set(item_wids)
            elif item.get("wid"):
                wids_set = {item["wid"]}
            else:
                wids_set = set()

            target_wid = item.get("wid") or (next(iter(wids_set)) if wids_set else None)
            active_wid = self.get_active_window_id()

            if target_wid or wids_set:
                self.bouncing_items[slot_idx] = now

                # Check if this app is CURRENTLY active and focused
                is_currently_active = bool(active_wid and (active_wid == target_wid or active_wid in wids_set))

                if is_currently_active:
                    # MULTI-WINDOW SUPPORT: If app has multiple windows, cycle through them
                    if len(wids_set) > 1 and active_wid in wids_set:
                        sorted_wids = sorted(list(wids_set))
                        try:
                            curr_idx = sorted_wids.index(active_wid)
                            if curr_idx < len(sorted_wids) - 1:
                                next_wid = sorted_wids[curr_idx + 1]
                                if self.focus_window_by_id(next_wid):
                                    item["wid"] = next_wid
                                    return
                        except Exception:
                            pass

                    # Single window or completed cycle -> TOGGLE HIDE / MINIMIZE!
                    wid_to_min = active_wid if active_wid else target_wid
                    if wid_to_min and self.minimize_window_by_id(wid_to_min):
                        return
                else:
                    # App is in background, occluded, or minimized -> TOGGLE SHOW / RAISE / FOCUS!
                    wid_to_focus = target_wid if target_wid else next(iter(wids_set))
                    if self.focus_window_by_id(wid_to_focus):
                        item["wid"] = wid_to_focus
                        return
            elif XLIB_AVAILABLE:
                self.bouncing_items[slot_idx] = now
                if self.focus_running_window(item):
                    return

        # App is NOT running (or force_new=True) -> Launch new process!
        self.bouncing_items[slot_idx] = now
        GenieLaunchEffect(slot_cx, slot_cy)

        exec_cmd = item.get("exec", "")
        if exec_cmd:
            try:
                cmd = f"exec systemd-run --user --scope {exec_cmd}"
                subprocess.Popen(
                    cmd,
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            except Exception:
                try:
                    cmd_fallback = f"exec {exec_cmd}"
                    subprocess.Popen(
                        cmd_fallback,
                        shell=True,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                except Exception as e:
                    print(f"[Dock] Launch error: {e}", file=sys.stderr)

    def focus_running_window(self, item: Dict) -> bool:
        """Brings existing window of this app to front."""
        try:
            target_cls = item.get("wm_class", "").lower()
            d = display.Display()
            root = d.screen().root
            net_client_list = d.intern_atom('_NET_CLIENT_LIST')
            net_active_win = d.intern_atom('_NET_ACTIVE_WINDOW')

            clients = root.get_full_property(net_client_list, X.AnyPropertyType)
            if clients:
                for wid in clients.value:
                    w = d.create_resource_object('window', wid)
                    cls = w.get_wm_class()
                    if cls and any(c.lower() == target_cls for c in cls):
                        event = protocol.event.ClientMessage(
                            window=w,
                            client_type=net_active_win,
                            data=(32, [2, X.CurrentTime, 0, 0, 0])
                        )
                        root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
                        d.flush()
                        d.close()
                        return True
            d.close()
        except Exception:
            pass
        return False

    def close_item_windows(self, item: Dict):
        """Sends WM_DELETE_WINDOW and triggers Genie Close Effect."""
        wid = item.get("wid")
        win_x, win_y = self.get_position()
        state = self.calculate_magnified_layout(self.get_allocated_width())
        try:
            idx = self.items.index(item)
            slot_cx = win_x + state[idx]["center_x"]
            slot_cy = win_y + state[idx]["y"]
        except Exception:
            slot_cx = win_x + (self.get_allocated_width() / 2.0)
            slot_cy = win_y + (self.get_allocated_height() / 2.0)

        if wid and wid in self.known_window_geoms:
            geom = self.known_window_geoms[wid]
            GenieCloseEffect(geom[0], geom[1], geom[2], geom[3], slot_cx, slot_cy)
        else:
            GenieCloseEffect(slot_cx - 200, 200, 400, 300, slot_cx, slot_cy)

        if not XLIB_AVAILABLE:
            return

        try:
            target_cls = item.get("wm_class", "").lower()
            d = display.Display()
            root = d.screen().root
            net_client_list = d.intern_atom('_NET_CLIENT_LIST')
            net_close_win = d.intern_atom('_NET_CLOSE_WINDOW')

            clients = root.get_full_property(net_client_list, X.AnyPropertyType)
            if clients:
                for w_id in clients.value:
                    if wid and w_id == wid:
                        w = d.create_resource_object('window', w_id)
                        event = protocol.event.ClientMessage(
                            window=w,
                            client_type=net_close_win,
                            data=(32, [X.CurrentTime, 2, 0, 0, 0])
                        )
                        root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
                    elif not wid:
                        w = d.create_resource_object('window', w_id)
                        cls = w.get_wm_class()
                        if cls and any(c.lower() == target_cls for c in cls):
                            event = protocol.event.ClientMessage(
                                window=w,
                                client_type=net_close_win,
                                data=(32, [X.CurrentTime, 2, 0, 0, 0])
                            )
                            root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
            d.flush()
            d.close()
        except Exception:
            pass

    def toggle_pin_item(self, item: Dict):
        """Pins or unpins application and updates layout."""
        item["pinned"] = not item.get("pinned", True)
        if not item["pinned"] and not item.get("is_running"):
            self.items.remove(item)
        self.save_dock_config()
        self.update_geometry()
        self.queue_draw()

    def unpin_item(self, idx: int):
        """Removes pinned item or closes unpinned app with Genie close."""
        if idx < len(self.items):
            item = self.items[idx]
            if item.get("is_running") or item.get("wid"):
                self.close_item_windows(item)
            removed = self.items.pop(idx)
            self.save_dock_config()
            self.update_geometry()
            self.queue_draw()

    # -------------------------------------------------------------------------
    # 📐 MATHEMATICAL MAGNIFICATION LAYOUT COMPUTATION
    # -------------------------------------------------------------------------

    def calculate_magnified_layout(self, win_w: int) -> List[Dict]:
        """Calculates positions and scales according to muelle magnify.rs."""
        num_items = len(self.items)
        dock_w = PADDING_X * 2 + num_items * REST_ICON_SIZE + (num_items - 1) * GAP
        dock_x = (win_w - dock_w) / 2.0
        win_h = self.get_allocated_height()
        dock_y = win_h - PILL_HEIGHT - 6.0

        strength = (MAGNIFY_MAX_SCALE - 1.0) * self.magnify_amount.value
        cursor = self.cursor_x if self.cursor_x is not None else -9999.0

        def shift_of(x_pos):
            return strength * MAGNIFY_RANGE * falloff_integral((x_pos - cursor) / MAGNIFY_RANGE)

        shift_left = shift_of(0.0)
        shift_right = shift_of(dock_w)
        centering = -(shift_left + shift_right) / 2.0

        rects = []
        for i in range(num_items):
            rest_center_x = PADDING_X + i * (REST_ICON_SIZE + GAP) + REST_ICON_SIZE / 2.0
            center_x = dock_x + rest_center_x + shift_of(rest_center_x) + centering

            scale = 1.0 + strength * falloff((rest_center_x - cursor) / MAGNIFY_RANGE)
            width = REST_ICON_SIZE * scale
            height = REST_ICON_SIZE * scale

            base_y = dock_y + PILL_HEIGHT - PADDING_Y
            rects.append({
                "x": center_x - width / 2.0,
                "y": base_y - height,
                "width": width,
                "height": height,
                "scale": scale,
                "center_x": center_x,
                "base_y": base_y
            })

        return rects

    # -------------------------------------------------------------------------
    # 🎨 CAIRO RENDERING (PURE OPTICAL CRYSTAL GLASS HUD)
    # -------------------------------------------------------------------------

    def on_draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        win_w = self.get_allocated_width()
        win_h = self.get_allocated_height()
        now = time.time()

        num_items = len(self.items)
        dock_w = PADDING_X * 2 + num_items * REST_ICON_SIZE + (num_items - 1) * GAP
        dock_x = (win_w - dock_w) / 2.0
        dock_y = win_h - PILL_HEIGHT - 6.0

        # 1. RENDER PURE OPTICAL CRYSTAL GLASS PILL
        pill_r = 24.0
        cr.save()
        cr.new_sub_path()
        cr.arc(dock_x + dock_w - pill_r, dock_y + pill_r, pill_r, -math.pi / 2, 0)
        cr.arc(dock_x + dock_w - pill_r, dock_y + PILL_HEIGHT - pill_r, pill_r, 0, math.pi / 2)
        cr.arc(dock_x + pill_r, dock_y + PILL_HEIGHT - pill_r, pill_r, math.pi / 2, math.pi)
        cr.arc(dock_x + pill_r, dock_y + pill_r, pill_r, math.pi, 3 * math.pi / 2)
        cr.close_path()

        base_pat = cairo.LinearGradient(dock_x, dock_y, dock_x, dock_y + PILL_HEIGHT)
        base_pat.add_color_stop_rgba(0.0, GLASS_BASE_TOP[0], GLASS_BASE_TOP[1], GLASS_BASE_TOP[2], GLASS_BASE_TOP[3])
        base_pat.add_color_stop_rgba(1.0, GLASS_BASE_BOT[0], GLASS_BASE_BOT[1], GLASS_BASE_BOT[2], GLASS_BASE_BOT[3])
        cr.set_source(base_pat)
        cr.fill_preserve()

        rim_pat = cairo.LinearGradient(dock_x, dock_y, dock_x + dock_w, dock_y + PILL_HEIGHT)
        rim_pat.add_color_stop_rgba(0.0, GLASS_SPECULAR_RIM[0], GLASS_SPECULAR_RIM[1], GLASS_SPECULAR_RIM[2], 0.55)
        rim_pat.add_color_stop_rgba(0.4, 1.0, 1.0, 1.0, 0.10)
        rim_pat.add_color_stop_rgba(0.8, ACCENT_GREEN[0], ACCENT_GREEN[1], ACCENT_GREEN[2], 0.22)
        rim_pat.add_color_stop_rgba(1.0, 1.0, 1.0, 1.0, 0.40)
        cr.set_source(rim_pat)
        cr.set_line_width(1.3)
        cr.stroke()

        cr.new_sub_path()
        cr.arc(dock_x + dock_w - pill_r, dock_y + pill_r + 1, pill_r - 1, -math.pi / 2, 0)
        cr.arc(dock_x + pill_r, dock_y + pill_r + 1, pill_r - 1, math.pi, 3 * math.pi / 2)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.28)
        cr.set_line_width(1.0)
        cr.stroke()
        cr.restore()

        # 2. CALCULATE MAGNIFIED ITEM RECTS
        state = self.calculate_magnified_layout(win_w)

        # 3. DRAW CRYSTAL SEPARATOR LINES (before trash)
        for i, it in enumerate(self.items):
            if it.get("uri") == "trash:///" and i > 0:
                sep_x = (state[i-1]["center_x"] + state[i]["center_x"]) / 2.0
                cr.save()
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.25)
                cr.set_line_width(1.0)
                cr.move_to(sep_x, dock_y + 14)
                cr.line_to(sep_x, dock_y + PILL_HEIGHT - 14)
                cr.stroke()
                cr.restore()

        # 4. DRAW ICONS, AURA, BOUNCE & PRESS SQUASH
        for i, (item, rect) in enumerate(zip(self.items, state)):
            pb = item.get("pixbuf")
            if not pb:
                continue

            lift = 0.0
            if i in self.bouncing_items:
                elapsed = now - self.bouncing_items[i]
                if elapsed < HOP_SECONDS * MAX_HOPS:
                    phase = abs(math.sin(math.pi * elapsed / HOP_SECONDS))
                    decay = 1.0 - 0.15 * (elapsed / (HOP_SECONDS * MAX_HOPS))
                    lift = BOUNCE_HEIGHT * phase * decay

            press_scale = 1.0
            if i in self.press_depressions:
                p_elapsed = now - self.press_depressions[i]
                if p_elapsed < 0.15:
                    press_scale = 0.82 + 0.18 * (p_elapsed / 0.15)

            if self.is_dragging and self.dragging_idx == i:
                # Render sleek slot placeholder where item will drop
                cr.save()
                cr.arc(rect["center_x"], rect["y"] + rect["height"] / 2.0, REST_ICON_SIZE * 0.40, 0, 2 * math.pi)
                cr.set_source_rgba(ACCENT_GREEN[0], ACCENT_GREEN[1], ACCENT_GREEN[2], 0.16)
                cr.fill_preserve()
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.32)
                cr.set_line_width(1.2)
                cr.stroke()
                cr.restore()
                continue

            draw_cx = rect["center_x"]
            draw_cy = rect["y"] - lift + (rect["height"] / 2.0)
            draw_scale = rect["scale"] * press_scale
            alpha = 1.0

            # Right Click Optical Aura Glow
            if self.right_clicked_idx == i:
                cr.save()
                cr.arc(draw_cx, draw_cy, REST_ICON_SIZE * 0.58 * draw_scale, 0, 2 * math.pi)
                cr.set_source_rgba(ACCENT_GREEN[0], ACCENT_GREEN[1], ACCENT_GREEN[2], 0.32)
                cr.fill()
                cr.restore()

            # Render Icon
            cr.save()
            cr.translate(draw_cx, draw_cy)
            cr.scale(draw_scale, draw_scale)

            cr.set_source_rgba(0.0, 0.0, 0.0, 0.35)
            cr.arc(0, REST_ICON_SIZE / 2.0 - 2, REST_ICON_SIZE * 0.35, 0, 2 * math.pi)
            cr.fill()

            Gdk.cairo_set_source_pixbuf(cr, pb, -REST_ICON_SIZE / 2.0, -REST_ICON_SIZE / 2.0)
            cr.paint_with_alpha(alpha)
            cr.restore()

            # Render Running App Indicator Dot (Emerald #00ff66)
            if item.get("is_running"):
                dot_x = rect["center_x"]
                dot_y = dock_y + PILL_HEIGHT - 6.0
                cr.arc(dot_x, dot_y, 4.5, 0, 2 * math.pi)
                cr.set_source_rgba(ACCENT_GREEN[0], ACCENT_GREEN[1], ACCENT_GREEN[2], 0.35)
                cr.fill()
                cr.arc(dot_x, dot_y, 2.2, 0, 2 * math.pi)
                cr.set_source_rgba(ACCENT_GREEN[0], ACCENT_GREEN[1], ACCENT_GREEN[2], 0.95)
                cr.fill()

        # 5. DRAW FLOATING DRAGGED ICON (ON TOP OF ALL DOCK ITEMS)
        if self.is_dragging and self.dragging_idx is not None and self.dragging_idx < len(self.items):
            drag_item = self.items[self.dragging_idx]
            pb = drag_item.get("pixbuf")
            if pb:
                cr.save()
                cr.translate(self.drag_x, self.drag_y)
                cr.scale(1.22, 1.22)

                # Floating drop shadow
                cr.set_source_rgba(0.0, 0.0, 0.0, 0.45)
                cr.arc(0, REST_ICON_SIZE * 0.48, REST_ICON_SIZE * 0.38, 0, 2 * math.pi)
                cr.fill()

                # Optical aura ring
                cr.arc(0, 0, REST_ICON_SIZE * 0.54, 0, 2 * math.pi)
                cr.set_source_rgba(ACCENT_GREEN[0], ACCENT_GREEN[1], ACCENT_GREEN[2], 0.28)
                cr.fill()

                alpha = 0.45 if self.drag_removing else 0.95
                Gdk.cairo_set_source_pixbuf(cr, pb, -REST_ICON_SIZE / 2.0, -REST_ICON_SIZE / 2.0)
                cr.paint_with_alpha(alpha)
                cr.restore()

        # 6. DRAW REMOVE / CLOSE TOOLTIP WHILE DRAGGING OFF DOCK
        if self.is_dragging and self.drag_removing:
            cr.save()
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(12.0)
            text = "✕ Remove from Dock" if self.items[self.dragging_idx].get("pinned") else "✕ Close App"
            ext = cr.text_extents(text)
            tx = self.drag_x - ext.width / 2.0
            ty = self.drag_y - 32.0

            cr.new_sub_path()
            cr.arc(tx + ext.width + 10, ty - 6, 8, -math.pi / 2, math.pi / 2)
            cr.arc(tx - 10, ty - 6, 8, math.pi / 2, 3 * math.pi / 2)
            cr.close_path()
            cr.set_source_rgba(0.85, 0.15, 0.15, 0.92)
            cr.fill()

            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            cr.move_to(tx, ty)
            cr.show_text(text)
            cr.restore()

        # 7. DRAW TUTORIAL MOUSE CLICK FOCUS CIRCLES ("efek bulat kecil saja")
        for r in self.active_ripples:
            prog = r["progress"]
            radius = 4.0 + 18.0 * prog
            alpha = max(0.0, 1.0 - prog)
            color = r.get("color", ACCENT_GREEN)

            cr.save()
            # Crisp expanding outer ring
            cr.set_line_width(2.0 * alpha)
            cr.arc(r["x"], r["y"], radius, 0, 2 * math.pi)
            cr.set_source_rgba(color[0], color[1], color[2], alpha * 0.95)
            cr.stroke()

            # Specular white center dot (helps focus in video recording)
            center_alpha = max(0.0, 1.0 - prog * 1.5)
            if center_alpha > 0:
                cr.arc(r["x"], r["y"], 3.0 * center_alpha, 0, 2 * math.pi)
                cr.set_source_rgba(1.0, 1.0, 1.0, center_alpha)
                cr.fill()
            cr.restore()

        return False

    def reload_safely(self):
        """Reloads dock configuration and resyncs windows."""
        self.build_desktop_cache()
        self.load_dock_config()
        self.update_running_windows()
        self.update_geometry()
        self.queue_draw()

# =============================================================================
# 🏁 APPLICATION ENTRY POINT
# =============================================================================

def handle_sighup(signum, frame):
    try:
        os.execv(sys.executable, [sys.executable, "/opt/floworkos/theme/flowork-muelle-dock.py"])
    except Exception as e:
        print(f"[Dock] In-place execv failed: {e}", file=sys.stderr)

def handle_sigusr1(signum, frame):
    global DOCK_INSTANCE
    if DOCK_INSTANCE:
        GLib.idle_add(DOCK_INSTANCE.reload_safely)

def main():
    global DOCK_INSTANCE
    signal.signal(signal.SIGHUP, handle_sighup)
    signal.signal(signal.SIGUSR1, handle_sigusr1)

    lock_file = f"/run/user/{os.getuid()}/flowork-muelle-dock.lock"
    try:
        import fcntl
        fd = open(lock_file, "w")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        sys.exit(0)

    try:
        with open(f"/run/user/{os.getuid()}/flowork-muelle-dock.pid", "w") as pf:
            pf.write(str(os.getpid()))
    except Exception:
        pass

    Gtk.init(None)
    DOCK_INSTANCE = SovereignMuelleDock()
    Gtk.main()

if __name__ == "__main__":
    main()
