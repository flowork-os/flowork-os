---
name: temporal-time-travel
description: Master procedural playbook for operating FlowFS v2 Temporal Time-Travel and atomic per-file rollback engine across conversation turns and filesystem changes.
domain: os_doctrine
keywords:
  - flowork
  - temporal
  - timetravel
  - rollback
  - checkpoint
  - snapshot
  - zstd
  - restoration
  - history
  - turns
  - flowfs
  - integrity
  - sha256
  - backup
  - revert
  - atomic
  - semantic
  - filesystem
  - recovery
  - sovereign
author: Flowork Architecture Board & Dr. Flow
version: 1.0.0
---

# ⚡ FlowFS v2 Temporal Time-Travel & Granular Rollback Playbook

## 1. Objective
Establish zero-loss, deterministic turn-based filesystem recovery in Flowork OS by providing atomic per-file and batch turn rollback using kernel-grade zstd compressed blobs, SHA-256 verification hashes, and sub-10ms latency.

## 2. Prerequisites
1. Running instance of `flowork-sysd` on port 18090 (`systemctl --user is-active flowork-sysd`).
2. Real-time background file indexer active (`systemctl --user is-active flowfs-indexer.service`).
3. Compiled native binaries:
   - `/opt/floworkos/bin/flowfs-rollback`
   - `/opt/floworkos/bin/flowfs-indexer-daemon`
4. Storage directory `/opt/floworkos/history/checkpoints` writable by system and user processes.

## 3. Standard Operating Procedure

### Step 1: List Historical Checkpoints
Inspect available conversation turns and recorded file manifests:
```bash
flowfs-rollback --list --session <SESSION_ID>
```

### Step 2: Create Turn Checkpoint
Capture snapshots of critical files prior to executing mutations or system refactoring:
```bash
flowfs-rollback --checkpoint --session <SESSION_ID> --turn <TURN_NUM> --file /path/to/target.conf --label "Pre-modification snapshot"
```

### Step 3: Roll Back Target File Atomically
Restore a modified or corrupted file back to the state recorded at a prior turn:
```bash
flowfs-rollback --session <SESSION_ID> --turn <TURN_NUM> --file /path/to/target.conf
```

### Step 4: Batch Turn Reversion
Revert all files modified during a specific turn:
```bash
flowfs-rollback --session <SESSION_ID> --revert-turn <TURN_NUM>
```

## 4. Verification
Execute the following verification steps to ensure Exit Code 0 across the temporal subsystem:

```bash
# 1. Verify flowfs-rollback binary execution
flowfs-rollback --list --session default --json

# 2. Verify tool runner dispatch
echo '{"action": "list"}' | /opt/floworkos/tools/temporal_rollback/run

# 3. Verify inotify indexer service health
flowfs-indexer-daemon --status
```

## 5. Failure Modes
1. **Permission Denied on Checkpoint:** Ensure `/opt/floworkos/history/checkpoints` has 0777 permissions (`sudo chmod -R 0777 /opt/floworkos/history/checkpoints`).
2. **Turn Not Found:** Run `--list` to verify turn existence before requesting restoration.
3. **File Not in Manifest:** Ensure the file was explicitly included in the checkpoint command or tracked by the inotify stream.
