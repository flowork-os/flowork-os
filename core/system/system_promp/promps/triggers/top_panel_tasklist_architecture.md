# TOP PANEL TASKLIST AND AUTHENTIC ICON INTEGRATION

## 1. Context & Activation Scope
Triggered when configuring or styling top panel headers, window tasklists, running application capsules, or resolving desktop application icons in XFCE4 panel.

## 2. Mandatory Behavioral Invariants
- **Compact Glass Pill Format:** Open application windows in the top panel must render as compact optical crystal glass pills with border-radius: 14px, minimal padding (`padding: 2px 6px`), and active highlight `#00ff66`.
- **Authentic Icon Resolution:** Application icons MUST be genuine application assets (e.g. Chrome, OpenScreen, Terminal, AI Sidebar). Ensure `/opt/floworkos/icons/*.png` are populated into `/usr/share/pixmaps/` and `/usr/share/icons/hicolor/48x48/apps/` so `libwnck` / `libtasklist` resolves authentic pixmaps instead of generic placeholders.
- **XFCE Tasklist Sizing Invariants:** In XFCE 4.18 `libtasklist`, maintain `show-labels=true`, `icon-size=18`, `max-button-length=36`, `min-button-length=28`, and `grouping=1` to enforce compact square/pill capsules without crushing icons to 0px.
- **Top Bar Panel Plugin Ordering:** Position the tasklist (`plugin-11`) directly between the center clock spacer (`plugin-5`) and the right-hand systray (`plugin-8`). Preserve the screenshot tool launcher (`plugin-2`) at the far-right edge.
- **Zero Session Disruption:** Never restart `xfce4-panel` violently (`xfce4-panel -r`); execute updates via live `xfconf-query` property manipulation and GTK CSS auto-reloads.

## 3. Strict Prohibitions
- NEVER use generic placeholder or fallback shapes when authentic app icons are available.
- NEVER set `show-labels=false` without explicit icon-size fallback to avoid empty crushed buttons.
- NEVER kill active desktop session or panel processes during runtime updates.
