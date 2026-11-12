# L0 COGNITIVE ROUTER & PRE-EGRESS PRIVACY SHIELD

## 1. Context & Activation Scope
Triggered when developing, debugging, or auditing `flowork-sysd` L0 SLM routing (`slm_loader.rs`, `embedded_slm.rs`), `llama-cpp-2` GGUF lifecycle, `privacy_shield.rs`, `flowork-connector` redaction/failover (`privacy.rs`, `providers.rs`), or `flowork-slm`.

## 2. Mandatory Behavioral Invariants
- **Strict Lazy & Memory Guardrails:** Keep `SlmManager` lazy-loaded with `/proc/meminfo` pressure guards (`<1200 MB` disables, `<2048 MB` idle-unloads) and run inference exclusively via `tokio::task::spawn_blocking`.
- **Schema-Safe Pre-Egress Redaction:** Apply `privacy_shield` in `connector-rs` BEFORE debug dumps (`/tmp/flowork_connector_last_req.json`) and upstream egress while preserving `tools`, `functionDeclarations`, and `parameters`.
- **Failover Header Telemetry:** Preserve `x-flowork-failover: sysd-l0-slm` and `x-flowork-failover-reason` when falling back across CloudCode, Ollama, and `:18090`.
- **Python CLI Contract:** Keep `/opt/floworkos/bin/flowork-slm` executable as a thin Python wrapper against `:18090` to preserve QC runner compatibility.

## 3. Strict Prohibitions
- NEVER commit `.gguf` weights into Git or bundle `.gguf` files into Live ISO SquashFS images (`build-live-iso.sh` excludes them).
- NEVER place 30+ char dummy secret tokens in source tests or docs; construct synthetic test tokens dynamically so anti-leak CI passes.
- NEVER hold stdout/stderr open on background daemons or run blocking FFI inference on Tokio async worker threads.
