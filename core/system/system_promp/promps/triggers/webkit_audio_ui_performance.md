# WEBKIT, COMPOSITOR & GTK3 DESKTOP UI PERFORMANCE GUARD

## 1. Context & Activation Scope
Applies when debugging or developing WebKit2GTK apps, audio visualizers, X11 display compositors (`picom`/`xfwm4`), GTK3 CSS themes, or high `Xorg`/`WebKitWebProcess` CPU saturation on `llvmpipe`/`simple-framebuffer` systems.

## 2. Mandatory Behavioral Invariants
- **WebKit2GTK Zero-Lag Baseline:** Set `WEBKIT_DISABLE_COMPOSITING_MODE="1"`, `LIBGL_ALWAYS_SOFTWARE="1"`, and `WebKit2.HardwareAccelerationPolicy.NEVER` on hybrid GTK apps; throttle `<canvas>` visualizers to <=30 FPS (`33.3ms`).
- **Idle Animation & Timer Gating:** Gate CSS infinite `@keyframes` loops strictly under active generation states (`body.is-generating`), strip software `backdrop-filter` blur, and enable pointer hover timers only when hover-peek mode is explicitly active.
- **Adaptive X11 Compositing:** Route `simple-framebuffer`/`llvmpipe` sessions through `/opt/floworkos/bin/flowork-compositor` to `xfwm4 --compositor=on` (or `picom-software.conf`) instead of alpha-blended shadows/translucency on CPU XRender.
- **GTK3 & Daemon Hygiene:** Validate GTK3 theme CSS with `Gtk.CssProvider` (`parsing-error` zero errors) and query `Gdk.Monitor.get_workarea()` in-process instead of spawning `xprop` polling subprocesses.

## 3. Strict Prohibitions
- Never leave infinite CSS `@keyframes`, `100ms` mouse polling loops, or unthrottled 60Hz repaints active when sidebar/visualizer UI is collapsed or idle.
- Never write DOM CSS `transform:` rules inside GTK 3.0 stylesheets (`gtk.css`).
- Never launch heavy `picom` alpha/shadow rules unconditionally on software `simple-framebuffer` renderers.
