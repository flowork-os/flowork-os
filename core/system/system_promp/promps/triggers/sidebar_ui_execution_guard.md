# SIDEBAR UI & COLLAPSED EDGE HANDLE GUARD

## 1. Context & Activation Scope
Applies when maintaining Mr. Flow companion sidebar UI, window struts, collapsed edge handles, and abort mechanisms.

## 2. Mandatory Behavioral Invariants
- **Strict English:** All UI labels, badges, and telemetry must use technical English.
- **Instant Abort Protocol:** Kill active CLI process groups via `os.killpg(pgid, signal.SIGKILL)` followed by an async exact-name sweep (`pkill -9 -x mrflow`, `pkill -9 -f flowork_core`) so GUI daemons never self-terminate.
- **WebKitGTK CPU & Crash Resilience:** Keep software-composited thinking logs and HUD timers throttled (`>=500ms`), rate-limit `mousemove` `resize_sidebar` events, debounce `xprop` struts/disk saves, and bind `web-process-terminated` to reset busy state and reload the UI.
- **True Child Exit Propagation:** Keep default `SIGCHLD` handling (`SIG_DFL`) so `mrflow` non-zero/signal failures propagate accurately; spawn detached desktop apps via background reaper threads.
- **UI State & Edge Handle:** Execute `unfreezeUiState()` on cancel/reset; on collapse, shrink to the 16px edge handle and strip EWMH struts.

## 3. Strict Prohibitions
- Never set `SIGCHLD` to `SIG_IGN` in Python daemons spawning `mrflow` workers.
- Never run unthrottled `<200ms` DOM-mutating log loops or synchronous `xprop` storms on `mousemove`.
- Never use broad `pkill -f mrflow` substring matches that terminate sidebar/tray daemons.
