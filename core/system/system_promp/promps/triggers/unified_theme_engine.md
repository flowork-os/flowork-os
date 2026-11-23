# UNIFIED THEME ENGINE & OPTICAL CRYSTAL GLASS DOCTRINE

## 1. Context & Activation Scope
Active whenever modifying desktop aesthetics, theme tokens, GTK styling, XFWM4 window frames, wallpapers, or desktop widgets (`flowork-seo-radar`, Muelle dock).

## 2. Mandatory Behavioral Invariants
- Enforce the unified theme standard: orchestrate Window Manager (XFWM4), GTK 3/4 CSS, Dock indicators, Wallpaper, and Desktop Widgets as a single synchronized system via `/opt/floworkos/bin/flowork-theme-engine`.
- Always store master palettes in `/opt/floworkos/theme/themes.json` and active tokens in `/opt/floworkos/theme/current-theme.json` with dynamic `$HOME/.config/flowork/theme.json` mirror.
- Re-synthesize XFWM4 titlebar hairlines and jewel controls dynamically on theme changes using `/opt/floworkos/theme/generate-xfwm4-theme.py`.
- Desktop widgets must watch `current-theme.json` modification timestamps and adopt active theme palettes automatically.
- Interaction on widget theme controls must dispatch `/opt/floworkos/bin/flowork-theme-engine next` asynchronously.

## 3. Strict Prohibitions
- Strictly forbid generic corporate AI dull gray (`#202123`, `#1e293b`) or tired hero blue styling; enforce Pure Optical Crystal Glass (cosmic obsidian void, 28px blur, pure white specular hairlines, razor neons `#00ff66`, `#00f2fe`, `#ff007f`).
- Never hardcode personal user home paths; always resolve `$HOME` dynamically.
- Never write fragmented theme hacks; all aesthetic changes must flow through the unified theme engine with Exit Code 0 verification.
