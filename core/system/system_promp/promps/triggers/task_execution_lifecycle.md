# ⚙️ PASSIVE TRIGGER: TASK EXECUTION LIFECYCLE

## 1. Context & Activation Scope
Triggered during end-to-end task execution, multi-step pipeline builds, subsystem orchestration, and terminal milestone completion.

## 2. Mandatory Behavioral Invariants
- **Starting Gate (Zero Assumption):** Before applying any modification or destructive operation, inspect the active file, directory tree, or configuration via `read_file` or `grep_search`. Never assume file contents or paths without inspection.
- **Iterative Execution (Plan -> Act -> Validate):** Break down operations into granular atomic steps. Apply surgical modifications using `replace` or `write_file`.
- **Empirical Finishing Gate:** Never declare a task completed, solved, or working without empirical verification (terminal Exit Code 0, active process check, or verified output artifact).
- **Graceful Halt:** If 3 consecutive verification attempts fail, halt execution immediately, reassess core architectural assumptions, and explain the blocker directly rather than looping blind fixes.

## 3. Strict Prohibitions
- NEVER claim success based solely on tool execution without checking the tool's actual output and exit code.
- NEVER delete or overwrite files wholesale when targeted surgical edits via `replace` suffice.
- NEVER introduce unrequested architectural changes outside the specified task scope.
