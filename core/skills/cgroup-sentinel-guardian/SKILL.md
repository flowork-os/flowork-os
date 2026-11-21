---
name: cgroup-sentinel-guardian
description: Master procedural playbook for operating Cgroup v2 Quarantine, Kernel PSI telemetry monitoring, runaway process freezing, and critical binary self-remediation in Flowork OS.
domain: os_doctrine
keywords:
  - flowork
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
  - stall
  - kernel
  - isolation
  - remediation
  - unfreeze
  - integrity
  - watchdog
  - selfhealing
  - sovereign
author: Flowork Architecture Board & Dr. Flow
version: 1.0.0
---

# ⚡ Cgroup v2 Quarantine & Kernel Sentinel Guardian Playbook

## 1. Objective
Establish deterministic ring-0 operating system protection and automated self-remediation in Flowork OS by coupling Linux Cgroup v2 sub-hierarchies with Kernel PSI (Pressure Stall Information) metrics, preventing runaway memory spikes or storm I/O loops from freezing the desktop graphical user interface.

## 2. Prerequisites
1. Linux kernel 7.3.0 with unified Cgroup v2 hierarchy mounted at `/sys/fs/cgroup`.
2. Running instance of `flowork-sysd` on port 18090 (`systemctl --user is-active flowork-sysd`).
3. Compiled native binaries:
   - `/opt/floworkos/bin/flowork-cgroup-guardian`
   - `/opt/floworkos/bin/flowork-tool-runner`
4. Delegated user cgroup controller permissions under `/sys/fs/cgroup/user.slice/`.

## 3. Standard Operating Procedure

### Step 1: Inspect Kernel PSI & Quarantine Tree
Query live kernel pressure metrics across memory, I/O, and CPU controllers:
```bash
flowork-cgroup-guardian --status
```

### Step 2: Quarantine and Freeze Rogue Process
When an anomalous process exhibits memory leakage or uncontrollable execution loops, freeze its cgroup immediately:
```bash
flowork-cgroup-guardian --quarantine <PID> --reason "Anomalous memory spike"
```

### Step 3: Release Process Post-Investigation
Restore normal execution and reset CPU weight once the process has been analyzed or stabilized:
```bash
flowork-cgroup-guardian --release <PID>
```

### Step 4: Audit Core ELF Binary Integrity
Verify that critical system binaries retain valid ELF headers and executable flags:
```bash
flowork-cgroup-guardian --verify-binaries
```

### Step 5: Execute Autonomous Simulation Validation
Run an end-to-end sandbox freeze and release cycle to verify kernel response:
```bash
flowork-cgroup-guardian --test-simulation
```

## 4. Verification
Execute the following verification steps to ensure Exit Code 0 across the guardian subsystem:

```bash
# 1. Verify CLI table and JSON generation
flowork-cgroup-guardian --status --json | grep -q '"cgroup2_mounted":true'

# 2. Verify deterministic simulation cycle
flowork-cgroup-guardian --test-simulation | grep -q "simulation succeeded"

# 3. Verify tool runner dispatch
echo '{"action": "status"}' | /opt/floworkos/tools/cgroup_guardian/run | grep -q '"all_healthy":true'
```

## 5. Failure Modes
1. **Target PID Exited Before Quarantine:** If target process terminates before guardian isolates it, a clear error is returned without system disruption.
2. **Cgroup Controller Delegation Missing:** If sub-controllers are not enabled, verify `/sys/fs/cgroup/user.slice/user-<UID>.slice/user@<UID>.service/cgroup.subtree_control`.
3. **Corrupted Binary Detected:** Run `--verify-binaries` to locate corrupted ELFs; corrupted binaries can be restored from `/opt/floworkos/target/release/` or system cache.
