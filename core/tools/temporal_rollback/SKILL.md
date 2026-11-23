---
name: temporal_rollback
description: FlowFS v2 Temporal Time-Travel and atomic per-file rollback engine. Capture turn checkpoints, inspect snapshot vaults, and revert workspace file mutations atomically across conversation turns.
keywords:
  - temporal
  - rollback
  - timetravel
  - checkpoint
  - snapshot
  - zstd
  - restore
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
  - flowork
---

# ⚡ FLOWORK OS SOVEREIGN TOOL SKILL: TEMPORAL_ROLLBACK

## 1. Overview
FlowFS v2 Temporal Time-Travel provides deterministic checkpointing and atomic per-file restoration across conversation turns. Operating with sub-10ms latency using kernel-grade zstd compression and SHA-256 verification hashes, this engine safeguards developer assets against broken code refactors, unwanted configuration changes, and accidental workspace deletions.

## 2. Prerequisites
- The `flowfs-rollback` binary must be installed at `/opt/floworkos/bin/flowfs-rollback`.
- Checkpoints storage directory `/opt/floworkos/history/checkpoints` must exist with write permissions.
- Inotify daemon `flowfs-indexer.service` running to stream real-time workspace mutations.

## 3. Standard Operating Procedure
1. **List Checkpoints (`list`):**
   Retrieve the chronological list of checkpoints for a specific or current session:
   ```json
   {
     "action": "list",
     "session": "current_session_id"
   }
   ```
2. **Create Turn Checkpoint (`checkpoint`):**
   Lock file snapshots before executing risky modifications or broad architectural changes:
   ```json
   {
     "action": "checkpoint",
     "session": "current_session_id",
     "turn": 4,
     "file": "/opt/floworkos/system/mrflow.env",
     "label": "Sebelum modifikasi environment daemon"
   }
   ```
3. **Rollback Single File (`rollback`):**
   Atomically revert a single target file to its pristine state at a designated turn:
   ```json
   {
     "action": "rollback",
     "session": "current_session_id",
     "turn": 4,
     "file": "/opt/floworkos/system/mrflow.env"
   }
   ```
4. **Revert Entire Turn:**
   Roll back all files modified during a specific turn:
   ```json
   {
     "action": "rollback",
     "session": "current_session_id",
     "revert_turn": 4
   }
   ```

## 4. Verification
- Verify restoration success by inspecting the returned JSON summary containing SHA-256 hash matching the original state.
- Validate that the target file content matches the pre-modification state using standard verification tools.
- Ensure all execution returns verifiable Exit Code 0.

## 5. Failure Modes
- If checkpoint creation returns `Permission denied`, ensure `/opt/floworkos/history/checkpoints` has 0777 permissions.
- If a turn manifest is missing, inspect the session history using `--list` to target a valid recorded turn.
