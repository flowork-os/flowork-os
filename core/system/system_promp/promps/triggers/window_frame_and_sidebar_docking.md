# WINDOW FRAME RESIZING & SOVEREIGN SIDEBAR DRAGGING

## 1. Context & Activation Scope
Applies when engineering XFWM4 window frames, grab hitboxes, resize mechanics, or undecorated GTK3 sidebars and embedded display containers (Melolo, DramaBox, MrFlow).

## 2. Mandatory Behavioral Invariants
- **Hitbox Integrity via Solid Backing:** XFWM4 derives X11 input bounding masks via `XShapeCombineMask` with alpha threshold 128. Keep borders at 4px solid obsidian backing (`alpha=255`) with a 1px glowing specular hairline on the outer edge, and corner grips at `18x18px`. Never use 0-alpha or transparent pixels across resize boundaries as they punch click-through holes into root.
- **Snapping & Resize Smoothness:** Disable edge snapping (`/general/snap_to_border = false`, `/general/snap_width = 2`, `/general/snap_resist = false`) to eliminate hitching and resistance during live edge resizing.
- **Dual Drag Architecture for Undecorated Windows:** Undecorated GTK windows (`set_decorated(False)`) may reject `begin_move_drag` under certain window managers. Always implement dual move handling: trigger `begin_move_drag` AND subscribe to `motion-notify-event` on event boxes to manually call `self.move(x + dx, y + dy)` during active pointer motion. Provide visual feedback with `grab` and `grabbing` cursors and a visible drag grip (`⠿`).
- **Aspect Ratio & Socket Embedding:** Always embed QEMU/SDL display windows using `Gtk.Socket` with solid `#070a0e` canvas backing to bypass Android `FLAG_SECURE` blackouts while completely eliminating blank or transparent canvases.

## 3. Strict Prohibitions
- Never reduce XFWM4 border pixmaps below 3px or leave corner hitboxes under 16px.
- Never use transparent (`alpha < 128`) inner borders in XFWM4 themes.
- Never rely exclusively on WM `begin_move_drag` for undecorated companion sidebars without motion-tracking fallback.
