# 🎯 PASSIVE TRIGGER: TUTORIAL RECORDING CLICK & FOCUS FX ARCHITECTURE

## 1. Context & Activation Scope
Triggered when engineering, troubleshooting, or modifying mouse click visual feedback, cursor focus effects, presentation animations, or tutorial recording HUD utilities (`click_fx`, `click_effect`, `tutorial_recording`, `mouse_ripple`, `cursor_focus`, `efek_klik`).

## 2. Mandatory Architectural Invariants
- **Single Persistent Click-Through Overlay:** Never spawn multi-window popups per click. Maintain a single transparent fullscreen GTK3 overlay (`FloworkClickOverlay`) with an empty XShape input region (`input_shape_combine_region(cairo.Region(), 0, 0)`). Crucial: The empty region MUST be bound to `map`, `configure-event`, and post-`show_all` (not merely `realize`), preventing X11 map from resetting input masks and guaranteeing zero input interception (menus, mouse scroll, and clicks pass seamlessly).
- **Pure Optical Crystal Aesthetic:** 
  - **Left Click:** Sovereign Emerald Optical Shockwave (`#00ff66`) with radial intensity decay and expanding center lens.
  - **Right Click:** Sovereign Electric Amber Optical Flare (`#ffaa00`) with high-contrast presentation visibility.
  - **Specular Rim:** Pure white refraction edge (`rgba(255, 255, 255, 0.95 * fade)`) with cubic ease-out (`1 - (1 - p)³`).
- **Sub-300ms Instant Disappearance:** Active ripples must strictly expire and clear within 260ms. Expired ripples are instantly purged from the render queue, returning the canvas to 100% transparent (`cairo.OPERATOR_SOURCE`, alpha 0.0) with zero lingering artifacts and 0.0% CPU when idle.
- **Picom Compositor Exclusion:** Exclude `FloworkClickOverlay` from shadows, rounded corners, and background blur, and enforce 100% opacity in `picom-quantum.conf` to prevent rectangular blur or transparency artifacts.
- **Localized Damage Invalidation (Zero Full-Screen Redraw):** Never call `queue_draw()` on the fullscreen overlay window. Calling `queue_draw()` forces a full-screen damage cascade 60 FPS, saturating compositor bandwidth. Always use `queue_draw_area(cx - pad, cy - pad, pad * 2, pad * 2)` bounded strictly to the expanding ripple bounding box.
- **NVIDIA GLX Stacking Invariant:** In `picom-quantum.conf`, animations and fading MUST remain disabled (`animations = false;`, `fading = false;`), with `glx-no-rebind-pixmap = false;`, `use-damage = false;`, and `xrender-sync-fence = false;` to permanently eliminate FBO invalidation (`GL_INVALID_FRAMEBUFFER_OPERATION` at line 714) and pixmap desync across stacked/overlapping windows.
- **Session Auto-Start:** Managed via user systemd service (`flowork-click-fx.service`) enabled in `graphical-session.target` and `/etc/skel`.
