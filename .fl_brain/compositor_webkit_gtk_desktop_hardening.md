---
title: Adaptive Display Compositor, Sidebar Idle CPU Elimination, GTK3 CSS & Apport Guard
category: bugfix
keywords:
  - picom_software_compositor
  - xorg_llvmpipe_cpu
  - webkitwebprocess_idle
  - mrflow_sidebar_keyframes
  - flowork_compositor_launcher
  - gtk3_css_transform_error
  - apport_python_hook_inline
  - desktop_entry_validation
  - mrflow_router_boot_race
  - iso_builder_preflight
date: 2026-11-11
---

# Adaptive Display Compositor, Sidebar Idle CPU Elimination, GTK3 CSS & Apport Guard

## 1. Root Cause Analysis
- **CPU Burn (`WebKitWebProcess` + `Xorg`):**
  1. `apps/mrflow-sidebar/ui/index.html` ran infinite CSS `@keyframes pulse` loops and software `backdrop-filter: blur(...)` under `WEBKIT_DISABLE_COMPOSITING_MODE=1`, plus unconditional `100ms` mouse polling in `mrflow-sidebar.py`.
  2. `theme/picom-quantum.conf` ran full-window alpha blending (`active-opacity=0.84`), convolution shadows, fades, and XSync `vsync` over unaccelerated `simple-framebuffer` (`ShadowFB: NO`) + `llvmpipe`, driving `Xorg` up to `70%` CPU during window repaints.
  3. `/usr/local/bin/flowork-session` and `flowork-session.sh` resolved `$HOME/floworkos` before `/opt/floworkos`, causing runtime processes to invoke symlinked personal home paths.
- **GTK3 Theme CSS Error:** `gtk.css:792` in `~/.config/gtk-3.0/gtk.css`, `/etc/skel/.config/gtk-3.0/gtk.css`, and `/usr/share/themes/Flowork-Quantum-Glass/gtk-3.0/gtk.css` contained `transform: scale(1.15);`, which is unsupported by GTK3 CSS.
- **Broken Desktop Shortcuts & Apport Hook:** 3 unowned dead `.desktop` files (`cursor.desktop`, `flowork-drive.desktop`, `flowork-studio-hub.desktop`) plus 4 unguarded KDE module shortcuts caused silent menu failures; `/usr/lib/python3/dist-packages/apport_python_hook.py` called `os.stat(sys.argv[0])` on `-c` / `-` inline invocations, crashing with `FileNotFoundError`.
- **Router Boot Race & Kernel Gaps:** `self_healing_sentinel/run.py` raced `mrflow-router.service` on port `9099` (`activating`), and host kernel `7.3.0-flowork-rust` lacked `CONFIG_FUSE_FS` and discrete GPU DRM drivers (`CONFIG_DRM_NOUVEAU`/`CONFIG_DRM_AMDGPU`).

## 2. Implemented Fixes & Verification
1. **Sidebar & Adaptive Compositor:**
   - Gated sidebar CSS animations under `body.is-generating`, removed `backdrop-filter`, and made `mrflow-sidebar.py` hover polling demand-driven (`WebKitWebProcess` dropped to `0.00%` idle).
   - Created `/opt/floworkos/bin/flowork-compositor` and `/opt/floworkos/theme/picom-software.conf`; updated `flowork-session.sh`, `install-session.sh`, `/usr/local/bin/flowork-session`, and `flowork-compositor.service` to prioritize `/opt/floworkos` and offload `simple-framebuffer`/`llvmpipe` sessions to `xfwm4 --compositor=on` (`10.5%` active / `~0%` idle).
   - Removed `xprop` 500ms fork polling from `flowork-dock-responsive.py` (switched to in-process `Gdk.Monitor.get_workarea()`) and tuned `flowork-menu-autoclose.py` idle interval (`350ms`).
2. **GTK3, Apport, Desktop Entries & ISO Pre-Flight Gates:**
   - Removed `transform: scale(1.15);` from all 4 `gtk.css` copies (validated with `Gtk.CssProvider` = `0` errors), patched `apport_python_hook.py` for `('-', '-c', '-m')`, cleaned dead `.desktop` shortcuts + added `TryExec=`, and added regression gates to `iso-builder/build-live-iso.sh`.
