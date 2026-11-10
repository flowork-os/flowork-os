# ⚡ PASSIVE TRIGGER: SUPERPOWERS SOFTWARE ENGINEERING DISCIPLINE

## 1. Context & Activation Scope
Triggered when executing software engineering tasks, implementing architectural plans, debugging system bugs, or driving multi-subagent workflows (`superpowers`, `tdd`, `systematic_debugging`, `rulings_not_stalls`, `subagent_development`, `code_review`).

## 2. Mandatory Behavioral Invariants
- **Rulings, Not Stalls:** Once a plan or task is authorized, execute continuously without pausing for trivial permissions. Autonomously resolve ambiguities with reasoned rulings: `Ruling: <decision> — <reason> — <cost_if_wrong>`, record them in context, and continue. Only halt for destructive actions, security hazards, or broken plans.
- **Systematic Debugging (4-Phase Protocol):** Zero speculative guessing. Strictly adhere to: (1) Empirical Reproduction (confirm failure with logs/exit code) -> (2) Formulate single testable hypothesis -> (3) Minimal surgical isolation -> (4) Empirical verification (Exit Code 0).
- **Test-Driven Discipline (Red-Green-Refactor):** Author a failing reproduction test before writing implementation code. Verify failure, apply targeted fix, and prove green passing state.
- **Subagent Context Isolation:** Delegate heavy, repetitive, or decoupled batch sub-tasks to fresh subagents with isolated context to preserve orchestrator context. Review subagent diffs for spec compliance, code quality, and zero secret leaks before merging.

## 3. Strict Prohibitions
- NEVER stall active plan execution to ask "Should I continue?" or prompt for minor procedural approvals.
- NEVER practice "shotgun debugging" by applying speculative code edits without empirical root-cause isolation.
- NEVER claim a task is complete without empirical verification passing with terminal Exit Code 0.
