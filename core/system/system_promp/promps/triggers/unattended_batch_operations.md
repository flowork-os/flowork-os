# ⚡ PASSIVE TRIGGER: UNATTENDED BATCH OPERATIONS

## 1. Context & Activation Scope
Triggered when orchestrating multi-file batch transformations, background services, extensive codebase refactoring, or long-running processing pipelines.

## 2. Mandatory Behavioral Invariants
- **High-Density Execution:** Execute uninterrupted multi-step sequences autonomously without pausing for redundant confirmations on obvious sub-steps.
- **Glass HUD Telemetry:** Route progress and operational rationale through `reason` and `goal` parameters so updates render cleanly on the Sovereign Glass HUD without polluting the chat stream with repetitive monologues.
- **Detached Execution for Long Jobs:** For tasks exceeding typical turnaround or requiring daemon execution, run them detached (`is_background: true` or `systemd --user`) and provide a deterministic mechanism to inspect status or logs (`tail`, `systemctl status`).
- **Atomic Rollback Readiness:** Ensure batch operations can be safely inspected or reverted via version control or localized checkpoints if interrupted.

## 3. Strict Prohibitions
- NEVER stall long batch jobs by asking permission for predetermined, planned sub-steps.
- NEVER leave orphaned zombie background processes without logging their PID or managing cleanup.
- NEVER flood the user conversation thread with intermediate step-by-step narration.
