---
title: GitHub Update Active Trigger & Agent Wakeup Advisor
date: 2026-11-11
keywords:
  - active_trigger
  - github_update_watch
  - agent_wakeup
  - etag_conditional_polling
  - mrflow_sidebar_ipc
  - supervisor_pid_validation
  - flowork_active_trigger
  - neural_bus_event
  - flowork_dev_guard
  - delta_ota_status
  - update_recommendations
  - systemd_persistence
---

# GitHub Update Active Trigger & Agent Wakeup Advisor

## Architecture Implemented
1. **Active Watchdog Daemon (`/opt/floworkos/system/triger/github_update_watch/`)**:
   - `trigger.json`: Registered under Flowork Active Trigger spec (`type: "active"`, `interval_seconds: 300`, `cooldown_seconds: 1800`, strictly English).
   - `watcher.py`: Polls `api.github.com/repos/flowork-os/flowork-os/commits/main` using `If-None-Match` (`ETag` -> `304 Not Modified` costs zero GitHub REST quota), with fallback to `raw.githubusercontent.com/.../manifest.json.gz`.
   - **Directionality Guard**: Calls GitHub `/compare/{local}...{remote}` so local unpushed commits behind/ahead never trigger false-positive update alerts.
   - **Priority-Safe IPC Signal**: Writes `/tmp/flowork_active_trigger.json` unless an active critical emergency trigger (`kernel_telemetry`, `system_telemetry`, `disk_guard`) is unexpired (<300s).
   - **Proactive Agent Wakeup**: Updates `btnUpdateOS` badge (`window.onSystemUpdateChecked`), publishes `system.github.update_detected` to Neural Bus (`:18095`), dispatches desktop notification, and wakes `/tmp/mrflow-sidebar-$USER.sock` cleanly when `is_busy == false` (deferring with 30s retry while busy, never interrupting running user turns).
2. **Supervisor & Sidebar IPC Hardening**:
   - Fixed recycled/zombie `.pid` detection in `/opt/floworkos/system/triger/supervisor.py` via `/proc/{pid}/stat` and `/proc/{pid}/cmdline`.
   - Added `window.onAutonomousTriggerWakeup` in `/opt/floworkos/apps/mrflow-sidebar/ui/index.html` and clean `new_session` / `BUSY` handling in `/opt/floworkos/apps/mrflow-sidebar/bin/mrflow-sidebar.py`.
   - Added read-only `--json` flag in `/opt/floworkos/bin/flowork-update` for non-destructive UI update status queries.
3. **Persistence & Sync**:
   - Locked `flowork-active-triggers.service` across `/etc/systemd/user/` & `/etc/skel/.config/systemd/user/`, excluded runtime trigger state files in `/opt/floworkos/iso-builder/build-live-iso.sh`, synced full `/opt/floworkos/system/triger/` tree in `upload-flowork-os.sh`, and registered conditional `/opt/floworkos/system/system_promp/promps/triggers/github_update_advisor.md`.
