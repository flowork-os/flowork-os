# [FLOWORK SOVEREIGN RESPONSIVE DOCK CENTERING DIRECTIVE]

## 1. Context & Activation Scope
Active when configuring, troubleshooting, or styling the desktop task dock (Plank), bottom taskbar, monitor resolution changes, display hotplug events, or companion sidebar workspace struts.

## 2. Mandatory Behavioral Invariants
- **Dynamic Monitor Binding:** Dock MUST bind dynamically to the active X11 monitor plug name (`monitor` setting via `xrandr`), never hardcoded or left to arbitrary workarea defaults.
- **Physical Center Invariant (Zero Offset):** Plank window spans the full physical display geometry and natively centers items when `alignment='center'` and `items-alignment='center'`. The `offset` setting MUST strictly remain `0%` so the dock stays locked at the true physical monitor center without asymmetrical drift.
- **Responsive Icon Scaling:** Dynamically scale `icon-size`:
  - 4K UHD (W >= 3840): `56px`
  - Ultrawide/QHD/1080p (W >= 1920): `48px`
  - Mid-tier (W >= 1600): `44px`
  - Compact/Laptop (W <= 1366): `40px`
- **Sovereign Daemon Sync:** Execute `/opt/floworkos/theme/flowork-dock-responsive.py --sync` upon boot, and run `--daemon` to reactively track display events.

## 3. Strict Prohibitions
- NEVER hardcode monitor output names (e.g. `None-1`, `eDP-1`) in persistent dotfiles.
- NEVER allow right sidebar resize to push bottom dock off physical center.
- NEVER push changes to remote git repositories without operator QC clearance.
