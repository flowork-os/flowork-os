#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Live Wallpaper Sync Daemon
# Bridges System Settings (Cinnamon/GNOME/XFCE) to X11 Root Window live
# Whenever user picks any wallpaper in settings, it updates desktop instantly.
# =============================================================================

import os
import sys
import subprocess
import urllib.parse
from gi.repository import Gio, GLib

def apply_wallpaper(uri):
    if not uri:
        return
    uri = uri.strip("'\"")
    if uri.startswith("file://"):
        file_path = urllib.parse.unquote(uri[7:])
    else:
        file_path = uri

    if os.path.isfile(file_path):
        print(f"[Wallpaper Sync] Applying: {file_path}", flush=True)
        if file_path.lower().endswith(".svg"):
            cache_png = f"/run/user/{os.getuid()}/flowork_wallpaper_rendered.png"
            try:
                subprocess.run(["rsvg-convert", "-w", "2560", "-h", "1080", file_path, "-o", cache_png], check=True)
                file_path = cache_png
            except Exception as e:
                print(f"[Wallpaper Sync] SVG conversion failed: {e}", flush=True)

        res = subprocess.run(["feh", "--no-fehbg", "--bg-fill", file_path], check=False)
        if res.returncode != 0:
            try:
                subprocess.run(["python3", "/opt/floworkos/theme/set-root-wallpaper.py", file_path], check=False)
            except Exception:
                pass

def on_cinnamon_changed(settings, key):
    uri = settings.get_string("picture-uri")
    apply_wallpaper(uri)

def on_gnome_changed(settings, key):
    uri = settings.get_string(key)
    if not uri and key == "picture-uri-dark":
        uri = settings.get_string("picture-uri")
    apply_wallpaper(uri)

def main():
    # 1. Cinnamon settings listener
    try:
        c_settings = Gio.Settings.new("org.cinnamon.desktop.background")
        c_settings.connect("changed::picture-uri", on_cinnamon_changed)
    except Exception as e:
        print(f"Cinnamon schema not found: {e}", flush=True)

    # 2. GNOME settings listener
    try:
        g_settings = Gio.Settings.new("org.gnome.desktop.background")
        g_settings.connect("changed::picture-uri", on_gnome_changed)
        try:
            g_settings.connect("changed::picture-uri-dark", on_gnome_changed)
        except Exception:
            pass
    except Exception as e:
        print(f"GNOME schema not found: {e}", flush=True)

    print("✅ Flowork Live Wallpaper Sync Daemon running...", flush=True)
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
