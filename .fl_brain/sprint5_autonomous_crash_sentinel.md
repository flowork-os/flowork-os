---
title: Sprint 5 Milestone - Autonomous Kernel & Process Crash Sentinel Loop
category: architecture
keywords:
  - pillar3_crash_sentinel
  - flowork_sentinel_daemon
  - dmesg_traps
  - segfault_interception
  - autonomous_remediation
  - self_healing_sentinel
date: 2026-11-09
---

# Sprint 5: Autonomous Kernel & Process Crash Sentinel Loop

## 1. Pillar 3 Overview
Upgraded Flowork OS from a passive restart-on-failure script into an active **Autonomous Crash-to-Fix Operating System**. The Sentinel daemon continuously monitors kernel traps, process crashes, and systemd degraded services, executing automated triage, integrity testing, snapshot rollback, and Neural Bus incident reporting.

## 2. Technical Components
- **Kernel Traps Interceptor (`check_kernel_traps()` in `run.py`):**
  - Parses `dmesg` buffer for segfault signatures:
    `r"(\w+)\[(\d+)\]:\s+segfault\s+at\s+([0-9a-f]+)\s+ip\s+([0-9a-f]+)\s+sp\s+([0-9a-f]+)\s+error\s+(\d+)\s+in\s+([^\s\[]+)"`
  - Scans `/tmp/flowork_crashes/` for app-level uncaught exceptions and core dumps.
- **Remediation Loop (`remediate_crash_incident()` in `run.py`):**
  - Runs `/opt/floworkos/bin/craft-app test <app_id>` to diagnose the failure mode.
  - Automatically restores backup or triggers `/opt/floworkos/bin/flowork-rollback <app_id>` if snapshot exists.
  - Dispatches event `system.crash.remediated` to Neural Bus (:18095).
  - Emits desktop notification to notify the user of autonomous healing.
  - Autonomous Agent Wake-Up (`wake_up_mrflow_agent()`): Directly invokes Mr. Flow sidebar IPC (`/tmp/mrflow-sidebar-{user}.sock`) via `send_prompt` action, automatically opening the HUD and dispatching the incident for autonomous triage and resolution.
- **Daemon CLI (`/opt/floworkos/bin/flowork-sentinel-daemon`):**
  - `--audit`: Outputs comprehensive JSON diagnostic report.
  - `--heal`: Runs diagnostic and applies auto-remediation actions.
  - `--watch`: Non-blocking continuous background event loop.
- **Systemd Unit & Triple-Lock Boot Persistence:**
  - `flowork-sentinel.service` installed with `WantedBy=default.target` in `~/.config/systemd/user/` and `/etc/systemd/user/`.
  - Mirrored into `/etc/skel/.config/systemd/user/default.target.wants/` for 100% reboot and live ISO persistence.
  - Integrated into `/opt/floworkos/session/flowork-session.sh` desktop session bootstrap.

## 3. Empirical Verification
- Verified one-shot `--audit` with Exit Code 0.
- Verified simulated crash remediation loop with mock incident JSON.
- Verified Neural Bus event dispatch and Exit Code 0.
- Verified systemd user service `flowork-sentinel.service` active and running (PID 344122) with Exit Code 0.
