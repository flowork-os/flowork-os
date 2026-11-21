# DOCK AND WINDOWING SYSTEM INTEGRITY

## 1. Context & Activation Scope
Triggered when configuring, modifying, or diagnosing Flowork desktop shell components, Sovereign Muelle Dock, Plank autostart, window managers, APK hardware containers, or compositor visual effects.

## 2. Mandatory Behavioral Invariants
- Never allow Plank or secondary dock utilities to launch alongside Flowork Muelle Dock; remove legacy dock startup calls from session runners.
- **Intellihide & Responsive Autohide:** The dock MUST implement intelligent autohide:
  - If viewable, non-minimized application windows exist on the active workspace (`has_open_app = True`), the dock slides down below the bottom screen edge (`window_height - 3px` offset), leaving a subtle 3px peek trigger zone.
  - When the pointer moves to the bottom edge (`root_y >= screen_h - 8` within dock horizontal bounds +/- 80px) or enters the dock window, it smoothly animates up via a critically damped spring (`omega=22.0`).
  - When the pointer moves away, apply a 280ms debounce before retracting to prevent jitter during micro-slips.
  - If no applications are open (clean desktop or all windows minimized), the dock remains resting fully visible.
  - During icon drag (`is_dragging`) or context menu interaction (`is_menu_open`), the dock MUST remain pinned open.
- **Dynamic Window Tracking & Minimized Retention:**
  - Query all client windows in `_NET_CLIENT_LIST`. Never skip minimized windows (`_NET_WM_STATE_HIDDEN` or `IsUnmapped`) in running window sets.
  - Dynamically add unpinned applications opened from Start Menu/Launchpad/terminal with running dot indicators.
  - Retain icons and glowing indicator dots when applications are minimized so users never lose visibility of background tasks. Only prune unpinned items when the client window is destroyed.
- **Smart Click Toggle & Duplicate Prevention:**
  - Left-clicking a running dock item must toggle state: if currently focused/active, minimize it via `WM_CHANGE_STATE` (Genie close); if inactive or minimized, restore and focus it via `_NET_ACTIVE_WINDOW` (Genie launch).
  - Debounce rapid launches (<2.0s) to completely eradicate accidental duplicate instances on double-clicks. Force new instances only via Right-Click -> "Open / New Window".
- In Muelle Dock Cairo render loops (`on_draw`), ensure all variable references are strictly defined to prevent 60 FPS crash loops, CPU throttling, and file descriptor exhaustion.
- Enforce a minimum 12px drag-and-drop threshold and 14px deadband hysteresis for dock icon reordering to prevent click interception and rapid slot oscillation.
- Mobile APK window containers must specify ICCCM `PAspect` hints (9:16) and maintain at least 50px vertical clearance above the bottom dock.
- Fullscreen effect popups (Genie launch/close beams) must declare explicit `WM_CLASS` to match compositor blur exclusions.

## 3. Strict Prohibitions
- Never run multiple dock processes simultaneously on the same display.
- Never drop unpinned apps from the dock when minimized; background tasks must remain visible and restorable.
- Never spawn duplicate application instances on rapid left-clicks.
- Never keep a DOCK window statically pinned on top of open applications without intellihide retraction.
- Never invoke `menu.popup_at_pointer` on X11 docks without first attaching the menu to the widget.
- Never claim resolution without verifying active service status and Exit Code 0.
