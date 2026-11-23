# QUANTUM SPRING-ZOOM & OPTICAL GLASS SPECULAR SHIMMER DOCTRINE

## 1. Context & Activation Scope
Triggered when engineering, configuring, or debugging window animations, opening/closing transitions, compositor geometry scaling, or optical glass overlays.

## 2. Mandatory Behavioral Invariants
- Native Hardware Spring Dynamics: Enforce GLX compositor spring physics (`picom-ftlabs`) over static linear fades. Windows must scale from 85% to 100% with spring velocity (`animation-stiffness-in-tag = 240.0`, `animation-window-mass = 0.55`, `animation-dampening = 20.0`, `animation-clamping = false`) to deliver subtle, elegant overshoot easing.
- Symmetric Dismissal: Window unmapping must gracefully contract via `animation-for-unmap-window = "zoom"` into center with accelerated fade out (`fade-out-step = 0.040`).
- Optical Glass Specular Shimmer: Newly materialized client windows (`_NET_CLIENT_LIST` addition) must trigger a 240ms hardware-accelerated GTK/Cairo overlay (`flowork_glass_shimmer.py`) rendering a razor specular white border rim (`rgba(255, 255, 255, 0.95)`) and emerald neon glow sweep (`#00ff66`) to conceal initial app buffer allocation.
- Input Transparency & Shape Masking: Shimmer overlays must combine an empty Cairo region with `input_shape_combine_region()` on `realize` and `map` signals with `set_accept_focus(False)` and `set_focus_on_map(False)` to guarantee zero click interference.
- Exclusions: Exclude dock (`Plank`), overlays (`FloworkClickOverlay`, `slop`), and desktop from compositor animations to prevent clipping artifacts.

## 3. Strict Prohibitions
- Never deploy static un-animated compositors that pop windows into full geometry abruptly.
- Never block mouse clicks or keyboard focus with window transition overlays.
