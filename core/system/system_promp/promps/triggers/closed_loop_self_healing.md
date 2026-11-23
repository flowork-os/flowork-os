# CLOSED-LOOP AUTONOMOUS SELF-HEALING

## 1. Context & Activation Scope
Activate when modifying, debugging, or triggering `/opt/floworkos/sysd/src/crash_watcher.rs`, `self_healing_sentinel/run.py`, `flowork-sentinel-daemon`, `flowork-snapshot`, `flowork-rollback`, or closed-loop `mrflow -p` remediation.

## 2. Mandatory Behavioral Invariants
- Honor the `/opt/floworkos/flowork.dev` Diagnostic-Only guard: emit `system.crash.diagnosis_ready` unless `--auto-heal` or `FLOWORK_SENTINEL_AUTO_HEAL=1` is explicitly supplied.
- Restrict auto-patching strictly to `/opt/floworkos/apps/` (and test `/tmp/flowork_mock_apps/`), never core OS directories (`/opt/floworkos/{sysd,crates,bin,connector,system}`) or `@lock`/`@freez` files.
- Always create a pre-heal archive (`flowork-snapshot create --tag pre-heal-... --path <app_dir>`) before invoking `mrflow` inside `flowork-sandbox-exec` (`--allowed-tools read_file,replace,write_file`, `FLOWORK_HISTORY_DIR=/tmp/flowork_crashes/.heal_history`).
- Keep the 600-second rolling crash window intact in `/tmp/flowork_sentinel_crash_history.json` so `>= 2` crashes in 10 minutes trip Loop Breaker quarantine (`system.crash.quarantined`) + rollback.
- Run headless verification (`craft-app test` or `py_compile` + `--check-health`) post-patch; crystallize successes into `memory_crystallizer/run.py` and rollback failures (`MAX_HEAL_RETRIES = 2`).

## 3. Strict Prohibitions
- Never grant `run_shell_command` to autonomous background `mrflow -p` self-healing invocations inside `flowork-sandbox-exec`.
- Never write `system.crash.*` payloads to `/api/bus/publish` without the `{type, source, target, action, payload}` JSON envelope.
