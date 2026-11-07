# PROCESS LIFECYCLE, TASK OBSERVABILITY & DESKTOP AUDIO INVARIANTS

## 1. Context & Activation Scope
Applies when developing or modifying GUI application launchers, sidebar agent subprocess execution, task status HUDs, or desktop panel audio and notification services.

## 2. Mandatory Behavioral Invariants
- **Detached GUI Launching:** All standalone GUI application launchers (e.g., `flowork-edits`, browser profiles) must launch detached via `nohup ... &` and exit immediately with code 0 to prevent blocking the caller.
- **Process Group Isolation & Abort:** Spawn agent child processes with `start_new_session=True` so `os.killpg(pgid, signal.SIGTERM)` terminates the entire process tree without leaving orphaned children.
- **Continuous Chat Observability:** Never hide `#chatContainer` during tool turns. Display active status in the sticky Sovereign Glass Task HUD (0.60 opacity, JetBrains Mono Bold, #00ff66 accent) with live elapsed timer and instant STOP abort trigger.
- **Audio D-Bus Invariant:** `xfce4-pulseaudio-plugin` requires an active `org.freedesktop.Notifications` daemon (`xfce4-notifyd`) to adjust PipeWire sink volume without D-Bus timeouts.

## 3. Strict Prohibitions
- Never execute interactive GUI applications synchronously in foreground mode.
- Never hide user chat history or lock the UI in un-abortable theater stages.
- Never leave zombie or orphaned child processes upon cancellation.
