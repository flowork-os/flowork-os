# 👑 PASSIVE TRIGGER: CROSS-ENGINE CODE REVIEW & BUG HUNTER

## 1. Scope & Activation
Triggered when performing code review, static analysis, refactoring audits, or pre-flight verification (`code_review`, `static_analysis`, `race_condition`, `bug_hunt`, `refactor_audit`, `leak_detection`, `gate_integrity`, `memory_safety`, `subprocess_safety`).

## 2. Mandatory Review Invariants
1. **Production Bug Hunting:** Focus strictly on catastrophic bugs that unit tests miss:
   - Async race conditions, unhandled Promise rejections, and event listener leaks.
   - Resource leaks (unclosed sockets, file descriptors, child process zombies).
   - Process group detachment flaws (missing `setsid` / `start_new_session`).
   - Signal traps and memory corruption vectors (SIGSEGV Exit Code -11).
2. **Gate Integrity (Zero Weakening):** Never weaken test assertions, artificially inflate timeouts, skip lint rules, or suppress errors in `run_shell_command` just to achieve a passing exit code. Every gate must be passed genuinely.
3. **Adversarial Simplification:** Flag over-abstracted layers, redundant wrapper shims, and dead code branches. Recommend surgical extractions with verifiable reliability gains.
