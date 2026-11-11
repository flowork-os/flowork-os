# SIDEBAR UI & COLLAPSED EDGE HANDLE GUARD

## 1. Context & Activation Scope
Applies when maintaining Mr. Flow companion sidebar UI, window struts, collapsed edge handles, and abort mechanisms.

## 2. Mandatory Behavioral Invariants
- **Strict English:** All UI labels, badges, and telemetry must use technical English.
- **Instant Abort Protocol:** Kill active CLI process groups via `os.killpg(pgid, signal.SIGKILL)` followed by an async exact-name sweep (`pkill -9 -x mrflow`, `pkill -9 -f flowork_core`) so `mrflow-sidebar.py` and `mrflow-tray-menu.py` never self-terminate.
- **UI State Reset:** Execute `unfreezeUiState()` on cancel/reset: restore `btnSend`, hide `btnStopExecution`, clear `isGenerating`, reset message bubbles, and clear `currentSessionId` to prevent exit code 42.
- **Collapsed Edge Tab:** On collapse, resize to a 16px edge handle (`.is-collapsed`), remove EWMH struts via `xprop -remove _NET_WM_STRUT -remove _NET_WM_STRUT_PARTIAL`, enforce geometry via `xdotool`, and restore struts on hover-peek or show.

## 3. Strict Prohibitions
- Never unmap the sidebar window completely on close or leave struts active while collapsed.
- Never use broad `pkill -f mrflow` substring matches that terminate sidebar/tray daemons.
- Never display dummy code mocks in tool visualizers or leave finished tool cards cluttering chat.
