#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Modern Frosted Glass Launchpad
# Native GTK-3 | Real-time Search | Zero Glitches | Single-Click Launch
# =============================================================================

import sys
import os
import signal
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib

PID_FILE = f"/run/user/{os.getuid()}/flowork-launchpad.pid"

def check_single_instance():
    """Toggle launchpad: if already open, kill existing and exit."""
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

class LaunchpadWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Flowork Launchpad")
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_default_size(980, 620)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

        self._setup_css()
        self._build_ui()
        self._load_apps()

        # Connect signals
        self.connect("key-press-event", self._on_key_press)
        self.connect("focus-out-event", self._on_focus_out)
        self.connect("destroy", self._on_destroy)

    def _setup_css(self):
        css = b'''
        window {
            background-color: transparent;
        }
        .launchpad-card {
            background-color: #131b2c;
            border: 1px solid rgba(255, 255, 255, 0.20);
            border-radius: 28px;
            box-shadow: 0 30px 90px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.35);
            padding: 30px 36px;
        }
        .search-pill {
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 18px;
            color: #ffffff;
            font-size: 14px;
            padding: 10px 20px;
            caret-color: #00e5ff;
        }
        .search-pill:focus {
            background-color: rgba(255, 255, 255, 0.12);
            border-color: #00e5ff;
            box-shadow: 0 0 16px rgba(0, 229, 255, 0.35);
        }
        .app-item {
            background-color: transparent;
            border-radius: 18px;
            padding: 14px 10px;
            border: 1px solid transparent;
            transition: all 140ms ease;
        }
        .app-item:hover, .app-item:focus {
            background-color: rgba(0, 229, 255, 0.14);
            border: 1px solid rgba(0, 229, 255, 0.45);
        }
        .app-title {
            color: #ffffff;
            font-size: 11px;
            font-weight: 500;
            margin-top: 6px;
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
        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.card.get_style_context().add_class('launchpad-card')
        self.add(self.card)

        # Header Search Bar
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search applications, workflows & tools...")
        self.search_entry.get_style_context().add_class('search-pill')
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_search_activate)
        header.pack_start(self.search_entry, True, True, 40)
        self.card.pack_start(header, False, False, 0)

        # Scrolled Grid
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.NONE)
        
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(6)
        self.flowbox.set_min_children_per_line(6)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_column_spacing(16)
        self.flowbox.set_row_spacing(16)
        self.flowbox.set_homogeneous(True)
        
        self.scroll.add(self.flowbox)
        self.card.pack_start(self.scroll, True, True, 0)

    def _load_apps(self):
        self.app_widgets = []
        all_apps = Gio.AppInfo.get_all()
        seen = set()
        
        # Sort apps alphabetically
        sorted_apps = sorted(all_apps, key=lambda a: a.get_display_name().lower())

        for app in sorted_apps:
            if not app.should_show():
                continue
            name = app.get_display_name()
            if name in seen:
                continue
            seen.add(name)

            desc = app.get_description() or ""
            executable = app.get_executable() or ""

            # EventBox to capture single-click
            evbox = Gtk.EventBox()
            evbox.set_visible_window(False)
            evbox.set_can_focus(True)

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            box.get_style_context().add_class('app-item')

            icon_info = app.get_icon()
            if icon_info:
                img = Gtk.Image.new_from_gicon(icon_info, Gtk.IconSize.DIALOG)
            else:
                img = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
            img.set_pixel_size(56)
            box.pack_start(img, False, False, 0)

            lbl = Gtk.Label(label=name)
            lbl.get_style_context().add_class('app-title')
            lbl.set_ellipsize(3) # PANGO_ELLIPSIZE_END
            lbl.set_max_width_chars(12)
            box.pack_start(lbl, False, False, 0)

            evbox.add(box)
            evbox.connect("button-press-event", self._on_app_clicked, app)
            evbox.connect("key-press-event", self._on_app_key_press, app)

            self.flowbox.add(evbox)
            self.app_widgets.append({
                'app': app,
                'widget': evbox,
                'name': name.lower(),
                'desc': desc.lower(),
                'exec': executable.lower()
            })

    def _on_app_clicked(self, widget, event, app):
        if event.button == 1: # Left click
            self._launch_app(app)
            return True
        return False

    def _on_app_key_press(self, widget, event, app):
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_space):
            self._launch_app(app)
            return True
        elif event.keyval == Gdk.KEY_Escape:
            self._close()
            return True
        return False

    def _launch_app(self, app):
        try:
            app.launch([], None)
        except Exception as e:
            try:
                os.system(f"{app.get_executable()} &")
            except Exception:
                pass
        self._close()

    def _on_search_changed(self, entry):
        query = entry.get_text().strip().lower()
        for item in self.app_widgets:
            if not query or query in item['name'] or query in item['desc'] or query in item['exec']:
                item['widget'].show()
            else:
                item['widget'].hide()

    def _on_search_activate(self, entry):
        # Pressing Enter: launch first visible app
        for item in self.app_widgets:
            if item['widget'].get_visible():
                self._launch_app(item['app'])
                break

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self._close()
            return True
        elif event.keyval in (Gdk.KEY_Down, Gdk.KEY_Tab):
            for item in self.app_widgets:
                if item['widget'].get_visible():
                    item['widget'].grab_focus()
                    return True
        return False

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
    win = LaunchpadWindow()
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
