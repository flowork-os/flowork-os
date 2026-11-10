# PROCESS LIFECYCLE, TASK OBSERVABILITY & DESKTOP AUDIO INVARIANTS

## 1. Context & Activation Scope
Applies when developing or modifying GUI application launchers, sidebar agent subprocess execution, task status HUDs, or desktop panel audio and notification services.

## 2. Mandatory Behavioral Invariants
- **Detached GUI Launching:** All standalone GUI application launchers (e.g., `flowork-edits`, browser profiles, or any synthesized app) must launch detached via `flowork-launch <app>` or `nohup ... >/dev/null 2>&1 &` and exit immediately with code 0 to prevent blocking the caller.
- **Agent Shell Execution Law:** When executing GUI applications via shell tools (`run_shell_command`), ALWAYS use `is_background: true` or invoke via `flowork-launch <app>` to guarantee instant return (<0.3s) without hanging.
- **Process Group Isolation & Abort:** Spawn agent child processes with `start_new_session=True` so `os.killpg(pgid, signal.SIGTERM)` terminates the entire process tree without leaving orphaned children.
- **Continuous Chat Observability:** Never hide `#chatContainer` during tool turns. Display active status in the sticky Sovereign Glass Task HUD (0.60 opacity, JetBrains Mono Bold, #00ff66 accent) with live elapsed timer and instant STOP abort trigger.
- **Audio D-Bus Invariant:** `xfce4-pulseaudio-plugin` requires an active `org.freedesktop.Notifications` daemon (`xfce4-notifyd`) to adjust PipeWire sink volume without D-Bus timeouts.

## 3. Strict Prohibitions
- Never execute interactive GUI applications synchronously in foreground mode.
- Never hide user chat history or lock the UI in un-abortable theater stages.
- Never leave zombie or orphaned child processes upon cancellation.
- Never run blanket text manipulation (dos2unix, sed, tr) indiscriminately across `/opt/floworkos/bin/` or compiled ELF binaries; always verify file types via `file` command to prevent corrupting executable headers (which triggers SIGSEGV Exit Code -11).
