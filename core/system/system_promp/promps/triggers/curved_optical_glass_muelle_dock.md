# 💎 PASSIVE TRIGGER: CURVED OPTICAL GLASS & MUELLE DOCK ARCHITECTURE

## 1. Context & Activation Scope
Triggered when styling, configuring, or engineering Flowork OS desktop interfaces, dock launch effects, window transitions, or dock items (`curved_glass`, `optical_glass`, `muelle_dock`, `launch_effect`, `genie_effect`, `drag_and_drop`).

## 2. Mandatory Behavioral Invariants
- **Thin Optical Glass Translucency:** Ultra-thin glass gradients (`rgba(255, 255, 255, 0.06 - 0.09)` over `0.02 - 0.05`) with 28px dual-kawase blur. Razor specular white rim (`rgba(255, 255, 255, 0.45)`).
- **Muelle Physics Engine:** Implement inverted smoothstep Gaussian magnification (`falloff(d) = 1 - 3d² + 2d³`) with closed-form integrals. Dock item clicks require squash depression (0.82x scale), emerald `#00ff66` ripple shockwave, and sinusoidal bounce (`lift(t) = H * |sin(π*t / 0.52)|`, 3 hops).
- **Bidirectional Genie Transitions:** Application launches trigger upward expanding optical glass funnels; application closures trigger reverse S-curve funnel collapse into the slot.
- **Natural Drag & Drop Reordering:** Reorder items via center-comparison swapping (`cursor > center_x`) without modifier keys. Dragging > 35px upwards triggers unpin/close with red tag.
- **Process Scope Isolation:** Dock services must enforce `KillMode=process` in systemd. Launch child applications via `systemd-run --user --scope` to prevent cgroup fate-sharing.

## 3. Strict Prohibitions
- Never execute global service restarts that kill shared user cgroups.
- Never use full-screen rectangular blur windows that obscure underlying applications.
