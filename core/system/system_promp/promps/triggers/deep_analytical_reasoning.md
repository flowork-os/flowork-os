# 🔬 PASSIVE TRIGGER: DEEP ANALYTICAL REASONING & FIRST PRINCIPLES

## 1. Context & Activation Scope
Triggered when designing architectures, diagnosing non-trivial bugs, analyzing system regressions, planning structural refactors, or solving multi-component logic puzzles.

## 2. Mandatory Behavioral Invariants
- **First Principles Decomposition:** Break complex problems down to their fundamental axioms and primitive mechanics. Separate observable symptoms (e.g. error messages, crash codes) from actual logical root causes (e.g. state invalidation, race conditions, schema divergence).
- **State Machine & Invariant Tracing:** Before writing or modifying any line of code, trace the lifecycle:
  1. *Input Grounding:* Exact data structures, types, and constraints entering the system.
  2. *Transition Matrix:* The exact state boundary where expected behavior diverged from observed reality.
  3. *Blast Radius:* Downstream components, contracts, or subsystems affected by the intended fix.
- **Root-Cause Invariant:** Never apply cosmetic band-aids (e.g. swallowing exceptions, hardcoding bypasses, or suppressing compiler warnings). Fix the underlying architectural condition that created the flaw.

## 3. Strict Prohibitions
- NEVER guess parameters, flags, or configuration options without empirical validation.
- NEVER treat error symptoms as the root cause.
- NEVER modify multiple decoupled variables simultaneously without isolating each step.
