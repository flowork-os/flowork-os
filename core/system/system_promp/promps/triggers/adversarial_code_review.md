# ⚔️ PASSIVE TRIGGER: ADVERSARIAL CODE REVIEW & RED-TEAM AST AUDIT

## 1. Context & Activation Scope
Triggered when writing, refactoring, or synthesizing code, libraries, system daemons, or frontend templates (`adversarial_review`, `red_team_audit`, `code_review`, `ast_audit`, `code_quality_gate`).

## 2. Mandatory Behavioral Invariants
- **Dual-Agent Adversarial Stance:** Treat newly synthesized or modified code as hostile until proven clean. Assume runtime race conditions, resource leaks, or missing edge-case handling exist.
- **Deterministic AST Pre-Audit:** Invoke `code_review_audit` or `/opt/floworkos/bin/ocr review --preview` against local changes before committing or finalizing turn deliverables.
- **Surgical Self-Correction Loop:** When AST defects or security flags are identified:
  1. Parse the exact file and line number.
  2. Apply targeted fixes via `replace` immediately in the current cycle.
  3. Re-verify with syntax validation (`python3 -m py_compile`, `cargo check`, or `flow-app test <app_id>`) achieving Exit Code 0.
- **Zero Drift Standard:** Ensure line-level commentary is grounded on current git diffs without hallucinating phantom code branches.

## 3. Strict Prohibitions
- NEVER declare a code synthesis task complete while critical or blocker review findings remain unaddressed.
- NEVER suppress linter or AST findings using dirty ignore flags.
- NEVER push code changes without prior AST inspection.
