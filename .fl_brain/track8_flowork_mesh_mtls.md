---
title: "Track 8 — Flowork Mesh Zero-Trust mTLS P2P Compute & Bus Offload"
category: distributed-mesh
keywords:
  - flowork_mesh
  - mtls_ed25519
  - zero_trust_p2p
  - policies_mesh_toml
  - landlock_sandbox_jail
  - remote_inference
  - flowpipe_offload
  - zstd_workspace_sync
  - neural_bus_hardware
  - register_provider
  - sse_job_streaming
  - allow_shell_false
---

# Track 8 — Flowork Mesh (`flowork-mesh`, `policies/mesh.toml`, `flowork-pipe-rs --target`)

## 1. Architecture Summary
- **Policy Invariants (`/opt/floworkos/policies/mesh.toml`)**: Zero-Trust by default: `enabled_by_default = false`, `require_mtls = true`, `allow_shell = false`, `allow_inference = true`, `allow_pipeline_offload = true`, `max_artifact_mb = 64`, `allow_media_cli = ["cutvii-cli", "kamidi-mastering-cli", "ocr", "blender"]`, `sandbox_exec = "/opt/floworkos/bin/flowork-sandbox-exec"`.
- **Pure Rust mTLS Daemon & CLI (`/opt/floworkos/crates/flowork-core-rs/src/bin/flowork-mesh.rs`)**:
  - `init` generates an Ed25519 Root CA (`ca.key` `0o600`, `ca.crt`), Node Ed25519 key/leaf X.509 certificate (`serverAuth,clientAuth` EKU + SANs), 6-digit PIN, and `config.json` (`enabled: false`).
  - `pair --export` / `--accept --pin` exchanges signed CA certs cleanly; `serve` refuses unless `enabled == true` and enforces mandatory `WebPkiClientVerifier` client certificate authentication over `tokio-rustls` + Axum (`/mesh/v1/{health,capabilities,infer,job,pipe}`).
  - `exec` tars and `/opt/floworkos/bin/zstd`-compresses the workspace, streams live SSE logs, resolves canonical CLI binary targets + `/opt/floworkos/apps/<app>` into Landlock strict `read_paths` (preventing wholesale `/opt/floworkos` rejection against `hard_deny_invariants`), jails execution strictly to `job_dir`, and returns zstd-packed `out/` artifacts.
  - `register-provider` queries `/mesh/v1/capabilities` over mTLS and registers remote inference into `remote_providers.json` (and optional `--sync` to `connector/config/providers.json`).
- **Neural Bus Hardware Telemetry (`/opt/floworkos/crates/flowork-core-rs/src/bin/flowork-neural-bus.rs`)**:
  - `GET /api/bus/apps` now publishes `hardware` (`cpu_cores`, `ram_total_mb`, `ram_free_mb`, `gpu_available`, `gpu_devices` via `nvidia-smi`, `ollama_models`, and live `mesh` status).
- **Remote DAG Offload (`/opt/floworkos/crates/flowork-core-rs/src/bin/flowork-pipe-rs.rs`)**:
  - Added `--target @<peer>` delegating remote `.flowpipe` execution cleanly to `/opt/floworkos/bin/flowork-mesh pipe --peer @<peer>`.

## 2. Empirical Verification (2026-11-12)
- Default-Off: Host `~/.flowork/mesh` verified `enabled: false`; unauthenticated `serve` refused.
- 2-Node mTLS (`nodeA` <-> `nodeB`): Unauthenticated & rogue self-signed client certs rejected cleanly; authenticated `register-provider` discovered `16` CPU cores, `64134` MB RAM, `NVIDIA GeForce RTX 4060`.
- Remote Inference (`infer @workstation`) & Shell Block (`bash` -> HTTP 403 `allow_shell=false`) passed.
- Studio CLI Landlock Jail: `cutvii-cli --help` & `ocr --help` executed via zstd+SSE inside Landlock (`exit_code: 0`); `flowork-pipe-rs run ... --target @workstation` completed `kamidi-mastering` `mesh_smoke` remotely (`exit_code: 0`).
