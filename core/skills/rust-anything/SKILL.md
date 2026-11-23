---
name: rust-anything
slash_command: rust-anything
description: Rewrite TypeScript, Python, C, Go, Ruby, or Java apps in Rust piece by piece. Features profiling, FFI bridging, recorded test case replay diffing, loop batching, and verified gate checks.
domain: code_dev
author: erkamyaman
version: 1.5.1
keywords:
  - rust
  - migration
  - rewrite
  - ffi
  - napi
  - pyo3
  - wasm
  - cgo
  - profiling
  - benchmarking
  - diffing
  - batching
  - transpilation
  - refactoring
  - testing
  - verification
  - optimization
  - performance
  - concurrency
  - code_dev
---

## Executive Summary & Objective

`rust-anything` is an autonomous engineering workflow and CLI suite for rewriting applications written in TypeScript, JavaScript, Python, C, Go, Ruby, or Java into memory-safe, high-performance Rust. The system enforces strict behavioral parity through characterization testing, recording edge-case inputs/outputs from the source language and replaying them bit-for-bit against the compiled Rust port.

The primary objective is zero-downtime, verified migration:
1. Profile workloads under the original runtime to discover genuine performance bottlenecks.
2. Formulate ordered, ranked migration plans (`analyze`).
3. Scaffold FFI and N-API/PyO3/CGO bridges (`bridge`).
4. Record behavior on edge cases and test suites (`record`).
5. Replay recorded cases against Rust implementations (`diff`).
6. Enforce strict gate checks before releasing (`gate`).
7. Deploy side-by-side verification wrappers (`shadow`).

---

## Prerequisites & Tool Dependencies

1. **Host Environment**: Flowork OS Linux (x86_64 or aarch64) with Rust toolchain (`rustc >= 1.97`, `cargo`).
2. **Native CLI Tool**: `/usr/local/bin/rust-anything` (or `/opt/floworkos/apps/rust-anything/bin/rust-anything`).
3. **Language Runtimes** (as applicable):
   - Node.js >= 18 (`/usr/local/bin/node`, `/usr/local/bin/npm`)
   - Python 3.10+ with `pytest`
   - Go 1.20+ (`go test`)
   - GCC / Clang for C FFI
   - Ruby / Java JDK for respective ports
4. **Rust Crates & Tooling**:
   - `cargo`, `cargo-clippy`, `rustfmt`
   - Target bindings: `napi` / `napi-build`, `pyo3`, `wasm-bindgen`, `cgo`

---

## Standard Operating Procedure (SOP)

### Phase 0: Profile Before Migrating (When Speed Matters)

Before writing any Rust, profile a realistic workload under the source language's profiler:

```bash
rust-anything profile <repo> -- node bench.mjs
# or:
rust-anything profile <repo> -- python3 bench.py
rust-anything profile <repo> -- go test -bench . ./pkg
```

- Target functions where time is spent in user logic rather than external syscalls or database I/O.
- Check if functions are already running in compiled C/C++ extensions; `profile` flags them under "Already compiled".

### Phase 1: Repository Analysis & Plan Approval

Map the target repository and generate an ordered migration wave:

```bash
rust-anything analyze <repo> -o plan.md
rust-anything analyze <repo> --json
```

- Inspect the generated plan: identify `start_here` units, `keep` units (UI, display logic), and `blocked` units.
- Review dependency fits (`good`, `none`, `unknown`). Flag missing crates early.
- Secure human or architectural sign-off on the migration wave before scaffolding.

### Phase 2: Unit Scaffolding & Behavioral Recording

For a target migration unit:

```bash
# 1. Scaffold crate with bridge bindings
rust-anything bridge <repo> <unit-id>

# 2. Record behavior on edge cases and test suite calls
rust-anything record <crate>
# or record from test suite:
rust-anything record <crate> --from-tests -- npx jest
rust-anything record <crate> --from-tests -- pytest
```

- When source functions require complex domain structures, append input vectors via:
  `rust-anything record <crate> --inputs cases.jsonl`
- Implement the Rust logic inside `<crate>/src/port.rs` ONLY. Never manually edit generated wrappers in `src/lib.rs`.
- When updating exported function signatures in `src/port.rs`, synchronize bindings:
  `rust-anything refresh <crate>`

### Phase 3: Loop Batching & Parallel Execution

When a function is repeatedly invoked in a hot loop (e.g. search, tokenization, filtering):

```bash
rust-anything bridge <repo> <unit> --batch fn:param
# or:
rust-anything refresh <crate> --batch fn:param
```

- This creates a vectorized batch struct (`FnBatch`) allowing Rust to hold references and evaluate on all CPU cores concurrently via Rayon.
- Construct the batch once in caller code rather than inside the iteration loop.

### Phase 4: Verification, Diffing, and Benchmarking

Compile the bridge and replay recorded inputs against the Rust crate:

```bash
rust-anything build <crate>
rust-anything diff <crate>
rust-anything bench <crate>
```

- Diff output must achieve exact parity: `N / N` cases matched.
- If intentional differences exist (e.g. upstream bug fixes), record them into `<crate>/known-diffs.jsonl`.
- Review `rust-anything bench` output: verify that Rust + FFI overhead outperforms the source language implementation.

### Phase 5: Side-by-Side Shadowing & Production Gating

Generate a drop-in replacement module:

```bash
rust-anything shadow <crate>
```

- Configure `RUST_ANYTHING_MODE`:
  - `shadow`: Runs both implementations side-by-side, logs differences, returns original result.
  - `new`: Direct execution through the compiled Rust port.
  - `old`: Fallback to legacy implementation.

Verify the definition of done with the gate command:

```bash
rust-anything gate <crate>
```

---

## Verification & Quality Gates (Exit Code 0)

Every migrated crate and skill run must satisfy:

1. **CLI Execution**: `rust-anything --version` exits with code 0.
2. **Compilation**: `cargo check --workspace` and `cargo test` pass without warnings.
3. **Format & Lint**: `rustfmt` and `cargo clippy -- -D warnings` exit code 0.
4. **Behavioral Match**: `rust-anything diff <crate>` achieves 100% matched cases.
5. **Gate Definition of Done**: `rust-anything gate <crate>` completes with Exit Code 0.
6. **No Unsafe Violations**: `unsafe` blocks are forbidden or strictly justified with `// SAFETY:` comments.

---

## Failure Modes, Edge Cases & Recovery

1. **String Encoding Discrepancies (UTF-16 vs UTF-8)**:
   - *Symptom*: Offsets, slices, or emoji character lengths differ between JS/Java and Rust.
   - *Fix*: Use `src/utf16.rs` provided by `rust-anything` to index by UTF-16 code units.
2. **Regex Engine Semantic Incompatibilities**:
   - *Symptom*: Lookarounds, backreferences, or non-ASCII word boundaries fail.
   - *Fix*: Replace standard `regex` with `fancy-regex`. Specify `unicode(false)` or explicit ASCII character classes `[A-Za-z0-9_]` where source language regex is ASCII-only.
3. **Floating Point Rounding & FMA Skew**:
   - *Symptom*: Complex float calculations differ at low decimal places.
   - *Fix*: Set `--float-tolerance 1e-9` during recording when non-bit-exact float math is permissible.
4. **Stalled Diff Progress**:
   - *Symptom*: Three edits in a row fail to improve match counts (`trend.stalled`).
   - *Fix*: Inspect the failing JSON cases, check edge-case inputs in `cases.jsonl`, and consult `docs/pitfalls.md`.

---

## Prohibitions & Anti-Patterns

1. **NO Silent Manual Crate Inventions**: Never implement ad-hoc crates when `analyze` flags missing dependencies; resolve or flag them explicitly.
2. **NO Unverified Recording Modifying**: Never edit recorded outputs in `cases.jsonl` to mask a failing Rust implementation; fix `port.rs`.
3. **NO Unchecked Panics**: Never use `.unwrap()` or `.expect()` in `src/port.rs` when the source language handles or throws recoverable exceptions; return `Err(...)`.
4. **NO Manual Wrapper Tampering**: Never manually edit generated `src/lib.rs` or FFI glue; use `rust-anything refresh`.
5. **NO Unprofiled Premature Porting**: Never migrate low-impact or I/O-bound modules without running `rust-anything profile`.
