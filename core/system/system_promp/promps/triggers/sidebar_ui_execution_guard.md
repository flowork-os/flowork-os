# SIDEBAR UI & COLLAPSED EDGE HANDLE GUARD

## 1. Context & Scope
Applies when maintaining Mr. Flow companion sidebar, window struts, collapsed edge handles, and hover transitions.

## 2. Mandatory Invariants
- STRICT ENGLISH: UI labels, badges, and telemetry must be in English.
- INSTANT ABORT: Stop button clears timers and terminates process trees (`SIGKILL`).
- REAL VISUALIZERS: Real disk lines and syntax forging. Zero dummy mocks.
- ZERO CHAT CLUTTER: Finished tool calls dissolve smoothly (`display: none`).
- COLLAPSED EDGE HANDLE (SEMBUNYI BUKAN HILANG):
  - When closed, collapse to 16px glowing cyan edge tab (`.is-collapsed`), deleting struts via `xprop -remove _NET_WM_STRUT -remove _NET_WM_STRUT_PARTIAL`. Never unmap window completely.
  - Enforce geometry via X11 (`xdotool windowsize`/`windowmove`) to bypass GTK minimum requisition clamping.
  - Hovering mouse over edge tab or within 30px screen edge expands sidebar instantly and focuses input.
- WORKAREA TILING:
  - When open: apply EWMH struts reserving desktop workarea.
  - When collapsed: remove struts so desktop applications expand full screen.

## 3. Strict Prohibitions
- Never unmap the sidebar window completely into non-existence on close.
- Never rely on pure GTK resize without X11 enforcement for collapsed geometry.
- Never leave struts active after sidebar collapses.
