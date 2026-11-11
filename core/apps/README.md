# 📱 Flowork OS Sovereign Applications Architecture

## 1. Canonical Territory
All native Flowork OS applications, GUI subsystems, browser extensions, and desktop launchers **MUST** reside within `/opt/floworkos/apps/` (currently **45** `.desktop` launchers and `apps.json` cataloging **18** apps + **6** plugins).

```text
/opt/floworkos/apps/
├── <app_name>/                   # Standalone application root (GUI, runtime, assets, app.json)
├── <app_name>.desktop            # Standard Freedesktop XDG desktop entry (45 total)
├── apps.json                     # System application & plugin registry metadata (18 apps, 6 plugins)
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
- **Favorites Sidebar:** Configured in `/etc/skel/.config/xfce4/panel/whiskermenu-1.rc` and `~/.config/xfce4/panel/whiskermenu-1.rc`:
  ```ini
  favorites=flowork-cyber-hub.desktop,flowork-stealth.desktop,flowork-connector.desktop,nemo.desktop,google-chrome.desktop,flowork-settings.desktop,flowork-wallpaper-settings.desktop,code.desktop,flowork-screenshot.desktop
  ```

### B. Launchpad (Modern Glass App Drawer)
- **Engine:** Native Python GTK-3 application drawer (`/opt/floworkos/theme/flowork-launchpad.py`).
- **Shortcuts:** `Super+A`, `F4`, or clicking the Launchpad icon on the bottom dock.
- **Discovery Mechanism:** Queries `Gio.AppInfo.get_all()`. Any `.desktop` file present in XDG application paths without `NoDisplay=true` appears in the 6-column frosted glass grid with single-click launch.

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

## 3. Sovereign App Toolchain & Headless CLIs

Flowork OS provides dedicated synthesis, packaging, sandboxing, and headless automation binaries in `/opt/floworkos/bin/`:

| Utility | Path | Purpose & Runtime Behavior |
| :--- | :--- | :--- |
| **`flowork-launch`** | `/opt/floworkos/bin/flowork-launch` | Subshell detached GUI launcher (`<0.3s`, Exit Code 0). Resolves `/opt/floworkos/bin/<id>` or `/usr/local/bin/<id>`; supports `--remix <app_id>` to emit `app.open_remix_stage` on Neural Bus (`127.0.0.1:18095`) and invoke `flowpkg remix`. |
| **`flow-app`** | `/opt/floworkos/bin/flow-app` | Sovereign App-on-Demand synthesizer creating `*flow` apps from `/opt/floworkos/apps/craft-anything/templates/quantum-glass`, registering launchers and desktop entries cleanly. |
| **`flowpkg`** | `/opt/floworkos/bin/flowpkg` | Hermetic `.flowapp` (`FLOWORK_FLOWAPP_V1`) package manager supporting `build`, `inspect`, `install`, `run`, `remove`, `list`, and `remix` (stages isolated sandboxes in `~/.flowork/remixes/`) with Linux Landlock LSM (`syscall 444`) enforcement. |
| **Headless `*-cli`** | `/opt/floworkos/bin/*-cli` | Scriptable non-GUI entrypoints (`craft-anything-cli`, `downflow-cli`, `tracedraw-cli`) for autonomous pipeline execution. |

## 4. Authoring New Applications
1. Synthesize scaffolding via `/opt/floworkos/bin/flow-app` or author application assets cleanly inside `/opt/floworkos/apps/<name>/`.
2. Create an executable launcher script in `/opt/floworkos/bin/<name>` or `/usr/local/bin/<name>` (use `/opt/floworkos/bin/flowork-launch` for detached GUI launches exiting with code 0).
3. Author the XDG specification file `/opt/floworkos/apps/<name>.desktop` with `Categories=X-Flowork;Utility;`.
4. Synchronize desktop entries cleanly:
   ```bash
   cp -fu /opt/floworkos/apps/<name>.desktop ~/.local/share/applications/
   ```
   (Mirror into `/usr/share/applications/` when packaging system-wide OS defaults.)
5. (Optional) Package as a portable `.flowapp` archive via `flowpkg build` or pin to the dock via `~/.config/plank/dock1/launchers/<name>.dockitem`.
