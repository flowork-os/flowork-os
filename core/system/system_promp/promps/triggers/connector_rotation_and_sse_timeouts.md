# CONNECTOR ROTATION, SSE TIMEOUTS & RESTART PERSISTENCE GUARD

## 1. Context & Activation Scope
Triggered when developing, debugging, or auditing `flowork-connector` account rotation, `mrflow-sidebar` turn events, `mrflow-rs` streaming inference, or system updates.

## 2. Mandatory Behavioral Invariants
- **Strict Model Lock:** Lock exclusively to `gemini-3.8-flash-high`. Strictly forbid degradation or fallback to lower tier models. Retry up to 6 times with jitter backoff.
- **Heartbeat Pulse Engine:** Spawn asynchronous 6s heartbeat ticker in `mrflow-rs` emitting `StreamEvent::ThoughtDelta` while awaiting TTFB to prevent UI/watchdog starvation during deep reasoning.
- **Companion Watchdog:** Set inference timeout to 360s. Bind watchdog activity to both stdout and stderr telemetry lines to avoid killing active processes.
- **Dynamic Account Controls:** In `mrflow-gui.py`, toggle authenticated state into dynamic Switch Account and Logout buttons with modal confirmation and non-destructive account retention.
- **Fast Failover & Jitter:** Honor `retry-after` HTTP headers; apply 250ms–1000ms randomized jitter; use 35s per-account TTFB timeout for fast pool rotation.
- **OTA Restart Persistence:** To prevent changes disappearing upon restart, always push via `upload-flowork-os.sh` to regenerate `manifest.json.gz` SHA-256 hashes matching `/opt/floworkos`. Ensure `flowork.dev` guards dev mode.

## 3. Strict Prohibitions
- Never downgrade models below `gemini-3.8-flash-high`.
- Never hardcode user paths; use dynamic resolution.
- Never edit `/etc/passwd` directly during live ISO builds.
