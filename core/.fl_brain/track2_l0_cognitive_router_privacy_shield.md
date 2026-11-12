---
title: Track 2 Milestone - L0 Cognitive Router, Pre-Egress Privacy Shield, and Air-Gapped Failover
category: architecture
keywords:
  - l0_cognitive_router
  - embedded_slm
  - llama_cpp_2
  - gbnf_grammar
  - privacy_shield
  - secret_redaction
  - air_gapped_failover
  - connector_rs
  - sysd_inference
  - memory_pressure_guard
  - flowork_slm
  - zero_quota_triage
date: 2026-11-12
---

# Track 2: L0 Cognitive Router & Pre-Egress Privacy Shield

## 1. Architectural Overview
Track 2 upgrades `flowork-sysd` (`:18090`) and `flowork-connector` (`:9099`) into a unified Layer-0 (L0) Cognitive Router with built-in pre-egress secret redaction and seamless air-gapped failover.

## 2. Implemented Subsystems
- **`sysd` Inference & Model Lifecycle (`/opt/floworkos/sysd/src/slm_loader.rs`, `embedded_slm.rs`, `routes.rs`):**
  - Integrated `llama-cpp-2` under default feature `embedded-slm` with `mmap` loading, `OnceLock<SlmManager>` lazy init, `/proc/meminfo` memory-pressure guard (`MemAvailable < 1200 MB` disables model load; `< 2048 MB` triggers 600s idle reaper unload), and `L0_TRIAGE_GBNF` constrained JSON sampling.
  - Exposes `POST /api/agent/l0/triage`, `GET /api/agent/l0/status`, `POST /api/agent/l0/unload`, `POST /api/agent/privacy/redact`, `/api/agent/ai/chat`, and `/v1/chat/completions`.
  - Runs CPU inference via `tokio::task::spawn_blocking` and ignores `"system"` role messages during intent keyword extraction.
- **Pre-Egress Privacy Shield (`/opt/floworkos/sysd/src/privacy_shield.rs`, `/opt/floworkos/connector-rs/src/privacy.rs`):**
  - Redacts PEM blocks, OAuth tokens, API keys, JWTs, ENV secrets, RFC1918 LAN IPs (preserving `127.0.0.1`), and sensitive user home paths inside JSON payloads while preserving `tools`, `functionDeclarations`, and `parameters` schemas.
  - Applied in `connector-rs/src/proxy.rs` prior to `/tmp/flowork_connector_last_req.json` logging and upstream dispatch (`cloudcode` / `9router`).
- **Air-Gapped Failover & Thin CLI (`/opt/floworkos/connector-rs/src/providers.rs`, `/opt/floworkos/bin/flowork-slm`):**
  - Probes Ollama `:11434` then fails over to `:18090/v1/chat/completions` (`x-flowork-failover: sysd-l0-slm`) on 401/403/429/timeout/exhausted pool across OpenAI JSON/SSE, Gemini JSON/SSE, and CloudCode SSE formats.
  - `/opt/floworkos/bin/flowork-slm` routes `--triage`, `--redact`, `--status`, `--unload`, and `--pull-model` cleanly to `:18090`; `.gguf` weights remain excluded from Live ISO SquashFS and GitHub.
