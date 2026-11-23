---
name: cgroup_guardian
description: Flowork Sovereign Cgroup v2 Quarantine and Kernel Sentinel Guardian doctrine. Monitor kernel PSI pressure metrics, freeze rogue processes, throttle CPU weights, and audit critical binary ELF integrity.
keywords:
  - cgroup
  - quarantine
  - sentinel
  - telemetry
  - ebpf
  - freeze
  - throttle
  - psi
  - pressure
  - memory
  - io
  - kernel
  - isolation
  - remediation
  - unfreeze
  - integrity
  - watchdog
  - selfhealing
  - sovereign
  - flowork
---

# ⚡ FLOWORK OS SOVEREIGN TOOL SKILL: CGROUP_GUARDIAN

## 1. Overview
The `cgroup_guardian` provides ring-0 kernel protection by coupling Linux Cgroup v2 tree management with Kernel PSI (Pressure Stall Information) metrics. When a process leaks memory or enters a destructive storm I/O loop, the guardian freezes the target cgroup instantaneously (`cgroup.freeze = 1`), throttles its CPU allocation to minimum priority (`cpu.weight = 1`), and dispatches an optical glass HUD crimson alert without risking desktop lockups.

## 2. Prerequisites
- Linux kernel 7.3.0 with Cgroup v2 mounted at `/sys/fs/cgroup`.
- Binary executable `/opt/floworkos/bin/flowork-cgroup-guardian`.
- Delegated user cgroup controller permissions or root privilege.

## 3. Standard Operating Procedure
1. **Inspect Guardian & PSI Status (`status`):**
   Query kernel pressure metrics and list any quarantined processes:
   ```json
   {
     "action": "status"
   }
   ```
2. **Quarantine & Freeze Rogue Process (`quarantine`):**
   Freeze and isolate a runaway process by PID:
   ```json
   {
     "action": "quarantine",
     "pid": 12345,
     "reason": "Runaway memory allocation detected"
   }
   ```
3. **Release & Unfreeze Process (`release`):**
   Restore normal execution and return process to standard session slice:
   ```json
   {
     "action": "release",
     "pid": 12345
   }
   ```
4. **Audit Binary ELF Integrity (`verify_binaries`):**
   Validate all critical system binaries against corrupted ELFs:
   ```json
   {
     "action": "verify_binaries"
   }
   ```
5. **Run Deterministic Simulation (`test_simulation`):**
   Execute an end-to-end sandbox freeze and release cycle:
   ```json
   {
     "action": "test_simulation"
   }
   ```

## 4. Verification
- Confirm `cgroup.events` reports `frozen 1` upon quarantine.
- Verify Exit Code 0 across all guardian executions.
- Inspect HUD table and JSON telemetry for zero anomalies.

## 5. Failure Modes
- If process has already exited prior to quarantine, an error is returned.
- If cgroup controllers are disabled in parent hierarchy, inspect `/sys/fs/cgroup/cgroup.subtree_control`.
