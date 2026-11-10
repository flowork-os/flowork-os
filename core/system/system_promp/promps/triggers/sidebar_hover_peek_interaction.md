# SIDEBAR AUTO-PEEK HOVER AND DOCKED WORKSPACE INTERACTION

## 1. Context & Activation Scope
Triggered when developing, configuring, or refactoring the Mr. Flow desktop companion sidebar, edge touch listeners, mouse hover peek behavior, or workspace docking.

## 2. Mandatory Behavioral Invariants
- Default `hover_to_open` to `false` (manual click mode) to prevent accidental edge hover expansions while browsing or working near screen boundaries.
- The edge tab (`#edgeTab`) MUST expand the sidebar unconditionally upon direct click. Hover expansion (`mouseenter`, `mouseover`, `mousemove`) MUST only trigger if `hover_to_open` (`isHoverPeekEnabled`) is explicitly true.
- In manual click mode (`hover_to_open: false`), the expanded sidebar MUST remain open when the mouse leaves. It closes only via `Escape` key, close button (`✕`), or Super hotkeys.
- When pinned (`is_pinned: true`), apply X11 WM struts (`_NET_WM_STRUT` / `_NET_WM_STRUT_PARTIAL`) to dock the window and prevent desktop overlap.
- Synchronize state dynamically between the GTK Python runtime (`~/.flowork/sidebar_config.json`) and WebKit JavaScript via `#btnAutoPeek` and `updateSidebarModeBadge()`.

## 3. Strict Prohibitions
- Never reintroduce unconditional mouse edge auto-expansion without an active toggle.
- Never auto-hide the sidebar on mouse leave when in manual click or pinned mode.
- Never hardcode personal home directory paths in configuration serializers.
