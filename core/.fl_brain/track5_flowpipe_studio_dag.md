---
title: "Track 5: Flowpipe Studio Deterministic DAG Engine & Macro Recorder"
date: "2026-11-12"
keywords:
  - flowpipe
  - flowork-pipe-rs
  - flowork-neural-bus
  - dag-execution
  - tokio-joinset
  - sha256-cache
  - macro-recorder
  - zero-llm-replay
  - kamidi-mastering
  - cutvii-render
  - orbit-flowpipe
  - sidebar-sse
---

# Track 5: Flowpipe Studio Deterministic DAG Engine & Macro Recorder

## Architecture Implemented
- **DAG Core (`/opt/floworkos/crates/flowork-core-rs/src/flowpipe.rs`):**
  - Parses TOML/JSON `.flowpipe` manifests from `/opt/floworkos/pipelines/` and `$HOME/.flowork/pipelines/`.
  - Validates node graph topology via Kahn layering + cycle rejection, resolves `{{inputs.*}}`, `{{work}}`, `{{out}}`, and `{{<node>.out}}` placeholders, and runs independent DAG layers concurrently via `tokio::task::JoinSet`.
  - Computes SHA-256 content-addressable cache keys across node command, args, sorted params, dependency outputs, and input/output file digests (`$HOME/.cache/flowork/flowpipe/artifacts/<sha>.json`), hitting `cache_hits=3` in `~1ms` on replay with `llm_calls=0`.
  - Supports `bus_cli`, `tool_runner`, `sysd_cdp`, `sysd_uinput`, and `slm_local` nodes, pre-execution `wait_for` assertions (`window_title`, `dom_selector`, `file_exists`), bounded retries, and env-secret stripping (`SandboxScope::default()` strips API tokens).
- **Neural Bus Runtime (`flowork-neural-bus.rs`) & Pure Rust CLI (`flowork-pipe-rs.rs`):**
  - Exposes `/api/bus/pipe/{list,validate,run,runs,pause,resume,cancel}` and UNIX socket RPC (`seq`-filtered from interleaved broadcast frames), broadcasting `pipe.run.started`, `pipe.node.started`, `pipe.node.done`, and `pipe.run.finished` onto SSE `/api/bus/stream`.
  - Preserves `/opt/floworkos/bin/flowork-pipe` AST compatibility (`os.execv` shim to `flowork-pipe-rs`) and includes `flowork-pipe record` SSE capture -> `.flowpipe` macro synthesis.
- **Desktop HUD Integration:**
  - `flowork-orbit.py` adds the `FLOWPIPE` tab for 1-click async pipeline launch; `apps/mrflow-sidebar/ui/index.html` adds a Sovereign Glass `#flFlowpipeHud` SSE listener with Pause/Resume/Cancel/Replay buttons.

## Verification
- `cargo test -p flowork-core-rs` (`13/13`), `cargo clippy ... -D warnings`, `flowork-pipe run /opt/floworkos/pipelines/demo_media.flowpipe` (`277ms` cold -> `1ms` cached `3/3` hits, `0` LLM calls), `flowork-pipe record`, `qc_evolution_suite.py` (`8/8 PASSED`), and `build-live-iso.sh check` (`Exit Code 0`).
