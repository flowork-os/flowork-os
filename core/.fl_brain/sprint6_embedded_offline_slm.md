---
title: Sprint 6 Milestone - Embedded Offline SLM and Air-Gapped Fallback
category: architecture
keywords:
  - pillar4_offline_slm
  - air_gapped_mode
  - embedded_slm
  - sysd_inference
  - intent_router
  - flowork_archon
date: 2026-11-09
---

# Sprint 6: Embedded Offline SLM & Air-Gapped Fallback

## 1. Pillar 4 Overview
Flowork OS has achieved absolute offline sovereignty. When network interfaces are down or cloud quotas are exhausted, Mr. Flow operates in Air-Gapped Zero-Cloud Mode powered by the native embedded SLM engine in `sysd` and the `flowork-slm` / `flowork-archon` runtime.

## 2. Technical Implementation
- **Pure Rust SLM Module (`/opt/floworkos/sysd/src/embedded_slm.rs`):**
  - High-performance deterministic natural language intent resolution and tool synthesis.
  - Intercepts and parses Indonesian and English command intents (`cari file`, `cari layar`, `remix`, `buka`, `cek sistem`).
  - Dispatches actions directly to native tools (`flowfs-search`, `flowpkg`, `flowork-launch`, `flowork-sentinel-daemon`) with sub-5ms latency.
- **Sysd Routing API (`/opt/floworkos/sysd/src/routes.rs`):**
  - `/api/agent/ai/chat`: High-density tool and reasoning response.
  - `/v1/chat/completions`: Full OpenAI-compatible chat completion payload endpoint supporting air-gapped web and IDE clients.
- **CLI Runner (`/opt/floworkos/bin/flowork-slm` & `/opt/floworkos/bin/flowork-archon`):**
  - Standalone command line interface for offline natural language task routing.
  - Supports `--json` programmatic mode and custom `--model` selection.
- **Model Storage Root (`/opt/floworkos/models/`):**
  - Prepared local model weights mount for quantized GGUF models.

## 3. Empirical Verification
- Verified app remix intent (`remix crypto-radar`) triggering `flowpkg_remix`.
- Verified visual screen search intent (`cari layar Orbit`) querying `flowfs_screen_memory`.
- Verified system diagnostic intent (`cek sistem`) invoking sentinel audit.
- All 8 tests in `/opt/floworkos/qc_evolution_suite.py` passed with Exit Code 0.
