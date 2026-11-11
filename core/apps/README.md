# 📱 Flowork OS Sovereign Applications Architecture

## 1. Canonical Territory
All native Flowork OS applications, GUI subsystems, and desktop launchers **MUST** reside within `/opt/floworkos/apps/`.

```
/opt/floworkos/apps/
├── <app_name>/                   # Standalone application root (GUI, runtime, assets)
├── <app_name>.desktop            # Standard Freedesktop XDG desktop entry
├── apps.json                     # System application registry metadata
└── (launch via /opt/floworkos/bin/flowork-launch)
```

## 2. Desktop & Menu Integration Matrix

Flowork OS provides a unified triple-surface application presentation layer:

### A. Start Menu (XFCE4 Whisker Menu)
- **Engine:** `xfce4-popup-whiskermenu` triggered via `Alt+F1` or physical `Super` key (remapped via `xcape`).
- **Discovery Paths:** Scans `/usr/share/applications/` and `~/.local/share/applications/`.
- **Session Sync:** `/opt/floworkos/session/flowork-session.sh` automatically synchronizes all `.desktop` files:
  ```bash
  cp -fu "$FLOWORK_OS_ROOT/apps/"*.desktop "$HOME/.local/share/applications/"
  ```
- **Favorites Sidebar:** Configured in `~/.config/xfce4/panel/whiskermenu-1.rc`:
  ```ini
  favorites=flowork-cyber-hub.desktop,flowork-studio-hub.desktop,flowork-connector.desktop,nemo.desktop,google-chrome.desktop,flowork-settings.desktop,flowork-wallpaper-settings.desktop,code.desktop,flowork-screenshot.desktop
  ```

### B. Launchpad (Modern Glass App Drawer)
- **Engine:** Native Python GTK-3 application drawer (`/opt/floworkos/theme/flowork-launchpad.py`).
- **Shortcuts:** `Super+A`, `F4`, or clicking the Launchpad icon on the bottom dock.
- **Discovery Mechanism:** Queries `Gio.AppInfo.get_all()`. Any `.desktop` file present in XDG application paths without `NoDisplay=true` will automatically appear in the 6-column frosted glass grid with its high-resolution icon and single-click launch.

### C. Bottom Dock (Plank Modern Dock)
- **Engine:** Plank running the `Flowork-Modern` glass theme.
- **Pinned Launchers:** Stored in `~/.config/plank/dock1/launchers/<name>.dockitem`.
- **DockItem Format:**
  ```ini
  [PlankDockItemPreferences]
  Launcher=file:///usr/share/applications/<name>.desktop
  ```
- **Reboot Persistence (Triple-Lock Protocol):**
  When pinning a new app to the bottom dock, mirror the `.dockitem` into `/etc/skel/.config/plank/dock1/launchers/` to guarantee persistence across user resets and new sessions.

## 3. Authoring New Applications
1. Author application logic inside `/opt/floworkos/apps/<name>/`.
2. Create an executable launcher script in `/usr/local/bin/<name>` (launching detached via `nohup ... &` and exiting with code 0).
3. Author the XDG specification file `/opt/floworkos/apps/<name>.desktop` with `Categories=X-Flowork;Utility;`.
4. Synchronize to system paths:
   ```bash
   sudo cp /opt/floworkos/apps/<name>.desktop /usr/share/applications/
   cp /opt/floworkos/apps/<name>.desktop ~/.local/share/applications/
   ```
5. (Optional) To pin to the bottom dock, create `~/.config/plank/dock1/launchers/<name>.dockitem`.
