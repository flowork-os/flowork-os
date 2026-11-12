# RUST SYSTEMS & UNIFIED WORKSPACE DOCTRINE

## 1. Context & Activation Scope
Triggered when writing, compiling, auditing, or refactoring Rust crates, `.rs` source files, or `Cargo.toml` manifests inside `/opt/floworkos/`.

## 2. Mandatory Behavioral Invariants
- **Unified Workspace Commands:** Run `export PATH="$HOME/.cargo/bin:$PATH" && cd /opt/floworkos && cargo check --workspace && cargo test --workspace` to validate all workspace members (`crates/flowork-core-rs`, `mrflow-rs`, `connector-rs`, `sysd`, `wm`; `apps/cutvii/src-tauri` excluded).
- **Zero-Cost Memory Ownership:** Minimize unnecessary `.clone()` calls; prefer borrowed slices (`&str`, `&[T]`) and zero-copy parsing.
- **Explicit Error Handling:** Propagate failures using `Result<T, E>` and `?`; handle mutex/channel/IO boundaries cleanly with contextual logs.
- **Zero New Compiler Warnings:** Keep modified Rust code warning-free under `cargo check` and `cargo clippy` before releasing binaries built via `cargo build --release`.

## 3. Strict Prohibitions
- NEVER leave `.unwrap()` or `.expect()` in production runtime paths.
- NEVER copy build artifacts directly into `/opt/floworkos/bin/` without verifying the ELF target architecture and running `--help` / `--check` post-swap.
