# [FLOWORK SOVEREIGN PURE CRYSTAL GLASS DIRECTIVE]

## 1. Context & Activation Scope
Active when designing UI, window themes, terminal aesthetics, apps, HUD overlays, GTK styling, or translucency parameters.

## 2. Mandatory Behavioral Invariants
- **Liquid Glass Base:** Pure Optical Liquid Crystal. Gradient: `linear-gradient(135deg, rgba(255,255,255,0.14) 0%, rgba(240,245,255,0.04) 45%, rgba(255,255,255,0.10) 100%)`. Dual-Kawase blur (strength 14-16 / `backdrop-filter: blur(28px) saturate(190%)`).
- **Refractive Crests (Cembung):** Specular hairline on elevated buttons/pills: `border: 1px solid rgba(255,255,255,0.22); border-top: 1px solid rgba(255,255,255,0.60); box-shadow: inset 0 1px 0 rgba(255,255,255,0.45), 0 16px 36px rgba(0,0,0,0.20)`.
- **Concave Insets (Cekung):** Recessed troughs: `background: rgba(0,0,0,0.14); box-shadow: inset 0 2px 4px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.15)`.
- **Fluid Curves (Lekukan):** Panels use `border-radius: 28px-48px`. Buttons/capsules use `border-radius: 20px-26px` or `9999px`.
- **Color Harmony:** Pure White (`#ffffff`) text in `JetBrains Mono Bold`. Razor Matrix Green (`#00ff66`) and Electric Aqua (`#00f2fe`) cyber accents.
- **Window Frame Invariants:** XFWM4 titlebars: 28px standard height, pure translucent white optical glass slices (alpha 10-22), centered 13px crystal jewel buttons. Grab borders: wafer-thin 2px razor specular rim (1px hairline + 1px glass body). `borderless_maximize` MUST remain `false`.
- **GDK 32-bit RGBA Interceptor:** All GTK3 windows require 32-bit ARGB visuals via `/usr/lib/x86_64-linux-gnu/libflowork-glass.so` (`gdk_screen_get_system_visual` interceptor) to prevent transparent CSS widgets from collapsing into `#000000` black buffer.
- **Dock Invariants (Plank):** Ultra-thin floating glass ribbon (`LineWidth=1`, `OuterStrokeColor=255;;255;;255;;70`, `InnerStrokeColor=0;;0;;0;;0`, `FillStartColor=255;;255;;255;;10`, `FillEndColor=255;;255;;255;;18`, `TopPadding=1`, `BottomPadding=1`). Enable cursor magnification zoom.
- **Compositor Safety:** NEVER hard-kill Picom with `pkill -9 picom` (causes Electron/Chromium Ozone GPU crash `trap int3`). Reload gracefully or via smooth restart.

## 3. Strict Prohibitions
- NEVER use square, sharp-cornered boxes (`border-radius: 0px/4px/8px` forbidden).
- NEVER use thick, bulky opaque frames, milky blocks, or dark `#000000` base tints.
- NEVER use dull gray (`#94a3b8`, `#64748b`) or purple (`#a855f7`).
- NEVER set `borderless_maximize: true` or strip window controls, drag headers, and resize borders.
- NEVER create `.bak`, `.orig`, or backup files anywhere. Git is sovereign.
