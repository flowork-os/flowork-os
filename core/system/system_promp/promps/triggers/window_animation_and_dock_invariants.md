# WINDOW ANIMATION & DOCK FOCUS INVARIANTS

## 1. Context & Activation Scope
Applies when configuring window management, dock interactions, compositor animations, picom configuration, or switching between desktop applications (e.g., Flowork Studio, Android APK subsystem apps).

## 2. Mandatory Behavioral Invariants
- Instant Zero-Overhead GLX Blit: On NVIDIA hardware, window transitions must avoid intermediate offscreen FBO zoom buffers (`animations = false;`, `fading = false;` in `picom-quantum.conf`) to permanently prevent `GL_INVALID_FRAMEBUFFER_OPERATION` at line 714 and texture invalidation when dragging, overlapping, or restacking windows. Never spawn secondary overlay windows (such as shimmer GTK popups) on top of new client windows to prevent duplicate ghost frames.
- Dock Click-Toggle State Machine: Clicking an open application icon on the dock must toggle state intelligently: if the window is in background, occluded, or minimized, bring it to the front and focus (`wmctrl -i -R` + `xdotool windowactivate`); if the window is ALREADY the active foreground window, minimize/hide it (`xdotool windowminimize` / ICCCM `WM_CHANGE_STATE`). If multiple windows of the same app exist, cycle through them sequentially.
- Multi-Workspace Window Retention: The dock must track client XIDs across all virtual desktops and workspaces. Never drop unpinned apps from the dock during workspace switches or window drag-wrap transitions.
- Identity & Window Class Matching: Every application must provide an authentic `.desktop` entry with `StartupWMClass` matching its X11 window class and a dedicated icon path (e.g., Flowork Studio WhiteSur SVG, Android APK packages).

## 3. Strict Prohibitions
- Never unconditionally re-focus an already-active window when clicked; respect user toggle to minimize/hide.
- Never purge unpinned running applications on workspace desktop changes.
- Never spawn secondary GTK popup frames over opening windows.
- Never set `Hidden=true` or `NoDisplay=true` on essential developer tools or system desktop files.
