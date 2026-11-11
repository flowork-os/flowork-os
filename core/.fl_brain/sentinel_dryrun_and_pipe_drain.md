---
title: Sentinel Dry-Run Isolation, Abort Self-Kill Guard & Non-Blocking Shell Pipe Drain
category: bugfix
keywords:
  - self_healing_sentinel
  - flowork_sentinel_daemon
  - qc_evolution_suite
  - simulated_crash_isolation
  - flock_serialization
  - wakeup_cooldown
  - mrflow_sidebar_abort
  - async_pipe_drain
  - watchdog_trigger_ttl
  - crypto_radar_popup_loop
date: 2026-11-11
---

# Sentinel Dry-Run Isolation, Abort Self-Kill Guard & Non-Blocking Shell Pipe Drain

## 1. Root Cause Analysis
- `qc_evolution_suite.py` (`QC-07`) dropped synthetic crash reports (`qc_test_crash.json`, `app: crypto-radar`, `pid: 77777`) into `/tmp/flowork_crashes/` without a simulated flag, while `flowork-sentinel.service` (`--watch --interval 15`) and `--heal` read `/tmp/flowork_sentinel_seen_traps.json` without `fcntl.flock` and never removed consumed files.
- `wake_up_mrflow_agent()` popped open `mrflow-sidebar` and dispatched an autonomous recovery prompt for synthetic `crypto-radar` incidents, causing the agent to repeatedly launch `crypto-radar` and stall for 120s in `mrflow-rs` `exec_shell()` whenever a child kept stdout/stderr pipes open.
- Aborting in `mrflow-sidebar.py` invoked `pkill -9 -f mrflow`, killing `mrflow-sidebar.py` and `mrflow-tray-menu.py` themselves via substring match and triggering immediate systemd respawns.

## 2. Implemented Fixes & Invariants
1. **Sentinel Isolation & Locking (`tools/self_healing_sentinel/run.py`, `bin/flowork-sentinel-daemon`, `qc_evolution_suite.py`):**
   - Serialized trap tracking and crash consumption with `fcntl.flock` + atomic writes, archiving/removing processed crash JSONs.
   - Added `--dry-run` / `FLOWORK_SENTINEL_DRY_RUN=1` and `is_simulated_incident()` detection (`simulated`, `qc_test_*`, synthetic PIDs) to suppress `notify-send`, rollback, and sidebar agent wakeups during QC tests.
   - Enforced a 300s per-app wakeup cooldown, recursion guard against `mrflow*`, `is_busy` check prior to `show`, and headless `--check-health`-only triage instructions.
2. **Rust Engine Pipe & Watchdog Hardening (`mrflow-rs/src/tools/mod.rs`, `src/cognitive/mod.rs`):**
   - Replaced `child.wait_with_output()` with `collect_child_output_with_timeout()` (bounded async pipe readers + `150ms` post-exit drain grace) so background grandchildren cannot stall `run_shell_command`.
   - Enforced a 300s freshness TTL on `/tmp/flowork_active_trigger.json` in `read_active_watchdog_trigger()`.
3. **Sidebar Abort Precision (`apps/mrflow-sidebar/bin/mrflow-sidebar.py`):**
   - Changed `async_kill_remnants()` from `pkill -9 -f mrflow` to exact binary match `pkill -9 -x mrflow`.
