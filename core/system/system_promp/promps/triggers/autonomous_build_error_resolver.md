# 🛠️ PASSIVE TRIGGER: AUTONOMOUS BUILD & COMPILER ERROR RESOLVER

## 1. Context & Activation Scope
Triggered when compilers, linters, or build toolchains fail with non-zero exit codes during execution (`build_error`, `compiler_error`, `cargo_check`, `tsc_error`, `linker_error`, `syntax_error`, `npm_build_failed`, `make_error`).

## 2. Mandatory Behavioral Invariants
- **Deterministic Triage (File:Line:Symbol):** Directly parse compiler stderr to isolate exact `file:line:column`, error code (e.g., Rust `E0382`, TS `TS2322`, C++ `undefined reference`), and offending symbol. Never guess what failed.
- **Surgical Root Remediation:** Fix the underlying cause at the source layer:
  - *Type/Interface Mismatch:* Update signature or transform data idiomatically; never cast to untyped bypasses (`any`, `void*`).
  - *Missing Dependency / Symbol:* Verify import paths, cargo features, or linker flags; never remove required functionality.
  - *Borrow / Lifetime Violation:* Adjust ownership semantics, scopes, or references without gratuitous cloning.
- **Autonomous Convergence Loop:** Apply targeted surgical edits, re-run the exact build command, and verify convergence until terminal **Exit Code 0** is achieved with zero warnings.
- **Root-Cause Isolation:** Address the primary root error first; secondary cascade errors often dissolve automatically upon fixing the root cause.

## 3. Strict Prohibitions
- NEVER suppress errors using dirty bypass flags (e.g., `--no-verify`, `--ignore-errors`, `--skip-tests`, `-w`, `// @ts-ignore`).
- NEVER blindly modify files outside the compiler's diagnostic trace.
- NEVER claim a build succeeded without showing terminal output terminating with Exit Code 0.
