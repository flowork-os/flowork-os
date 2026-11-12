---
title: "Track 7 — Closed-Loop Autonomous Self-Healing Architecture"
category: self-healing
keywords:
  - crash_watcher
  - self_healing_sentinel
  - flowork_snapshot
  - flowork_rollback
  - landlock_sandbox
  - mrflow_auto_heal
  - loop_breaker_quarantine
  - diagnostic_only_guard
  - episodic_memory
  - systemd_coredump
  - neural_bus_sse
  - ocr_ast_triage
---

# Track 7 — Closed-Loop Self-Healing (`crash_watcher` + `sentinel` + `snapshot` + `rollback`)

## 1. Architecture Summary
- **Pure Rust Real-Time Crash Watcher (`/opt/floworkos/sysd/src/crash_watcher.rs`)**:
  - Polls `/tmp/flowork_launch_*.log` (`500ms`) for Python tracebacks/runtime errors, Rust `panicked at`, and `SIGSEGV`, plus tails `journalctl -f -n 0 -o json -t systemd-coredump`.
  - Deduplicates via FNV-1a hashes, writes atomic incidents to `/tmp/flowork_crashes/<app>_<pid_or_ts>_<hash>.json`, exposes `GET /api/kernel/crashes` on `:18090`, and publishes `system.crash.incident` over `/run/flowork/bus.sock`.
- **Snapshot + Rollback (`/opt/floworkos/bin/flowork-snapshot`, `flowork-rollback`)**:
  - Added `--path <dir>` to atomically archive the target app directory (`target_backup.tar.gz`) alongside system configs before any patch, and `flowork-rollback` restores `target_backup` if repair verification fails.
- **Sentinel Closed-Loop Healer (`/opt/floworkos/tools/self_healing_sentinel/run.py`)**:
  - **Dev-Mode Diagnostic-Only Guard**: When `/opt/floworkos/flowork.dev` exists and `--auto-heal` / `FLOWORK_SENTINEL_AUTO_HEAL=1` is NOT passed, publishes `system.crash.diagnosis_ready` (rendered in `mrflow-sidebar` toast with an **Apply Fix** button) without editing files.
  - **Scope Allowlist**: Permits patches ONLY inside `/opt/floworkos/apps/` or `/tmp/flowork_mock_apps/`, rejecting OS core directories and `@lock`/`@freez` files.
  - **Loop Breaker**: Tracks crashes in a rolling 600s window (`/tmp/flowork_sentinel_crash_history.json`); `>= 2` crashes in 10 minutes trips quarantine (`/tmp/flowork_sentinel_quarantine.json`), rolls back, and emits `system.crash.quarantined`.
  - **Sandboxed Patch + Verification**: Runs `mrflow --policy /opt/floworkos/policies/write.toml --approval-mode auto_edit --allowed-tools read_file,replace,write_file --skip-trust -o json -p ...` inside `flowork-sandbox-exec` (`FLOWORK_HISTORY_DIR=/tmp/flowork_crashes/.heal_history`), validates via `craft-app test` or `py_compile` + `--check-health`, then records episodic learning via `/opt/floworkos/tools/memory_crystallizer/run.py` (with `~/.flowork/history/episodic_memory.db` fallback) OR rolls back cleanly.

## 2. Empirical Verification (2026-11-12)
- `crash_watcher.rs`: Detected Python traceback in `< 250ms`; exposed on `:18090/api/kernel/crashes` and `:18095/api/bus/events`.
- Dev-Mode Guard: Verified `mock_buggy/app.py` SHA-256 unchanged without `--auto-heal`; `system.crash.diagnosis_ready` emitted.
- Closed-Loop Auto-Heal: Repaired `mock_buggy/app.py` inside Landlock jail on attempt 1 -> `HEALTH_OK` (Exit 0) -> `episodic_learned=True` (FTS5 search hit `category="self_healing"`).
- Auto-Rollback: Unfixable FPGA error failed 2 attempts -> `flowork-rollback` restored original SHA-256 (`status="rolled_back"`).
- Loop Breaker & Scope Guard: 2 rapid crashes tripped `loop_breaker_tripped`; `/opt/floworkos/sysd` rejected by core scope guard.
- `qc_evolution_suite.py`: `8 PASSED, 0 FAILED`; `build-live-iso.sh check`: Exit Code 0.
