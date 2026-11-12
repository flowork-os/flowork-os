---
title: Episodic Memory JIT Recall, Neural Bus Headless Pipelines, and Landlock ABI Gating
category: architecture
date: 2026-11-12
keywords:
  - episodic_memory
  - memory_crystallizer
  - sqlite_fts5
  - jit_recall
  - flowork_neural_bus
  - flowork_pipe
  - kamidi_mastering_cli
  - cutvii_cli
  - landlock_abi
  - flowork_tool_runner
  - zero_copy_shm
  - drm_capture
---

# Episodic Memory, Neural Bus Pipelines, and Landlock ABI Hardening

## 1. Episodic Memory Engine & JIT Recall
- **`/opt/floworkos/tools/memory_crystallizer/run.py`:** Upgraded SQLite store (`/opt/floworkos/history/episodic_memory.db`) with `WAL` journal mode (`busy_timeout=3000`), deterministic SHA-256 `(category, problem)` deduplication (`idx_episodes_fingerprint`), FTS5 update triggers (`episodes_au`), quoted BM25 FTS5 queries, secret/`$HOME` scrubbing, `--sync-brain`, and `--harvest` session ingestion.
- **`/opt/floworkos/mrflow-rs/src/memory/episodic.rs`:** Native `rusqlite` (`bundled`) FTS5 recall engine integrated into `engine.rs` (`recall_jit` capped at `<= 3` matches / `<= 1200` chars) and `agents/mod.rs` (`<= 2` matches / `<= 800` chars). Auto-crystallizes only verified error-to-recovery turns or multi-step (`>= 2`) workflows while redacting secrets and `$HOME`.

## 2. Headless Studio Pipeline & Neural Bus v2
- **`flowork-neural-bus` (`/opt/floworkos/crates/flowork-core-rs/src/bin/flowork-neural-bus.rs`):** Added `GET /api/bus/apps`, `discover_headless_clis()`, `strict` execution mode, configurable timeouts (`5..600s`), and positional `args` placeholder substitution (`{prev}`, `{file}`, `{input}`).
- **Studio CLIs:** Added FFmpeg-backed `/opt/floworkos/apps/kamidi-mastering/bin/kamidi-mastering-cli` (`synth`, dual-pass `loudnorm` `master`, `sidechaincompress` `duck`, `inspect`, `register`) and `/opt/floworkos/apps/cutvii/bin/cutvii-cli` (`render`, `attach`, `probe`, `register`), proven E2E across `vectorcraft -> kamidi-mastering -> cutvii`.

## 3. Landlock ABI Gating & `/dev/shm` Capture
- **`flowork-tool-runner`:** Added `FLOWORK_SANDBOX_MODE` (`auto` | `enforce` | `off`) with async-signal-safe `pre_exec` Landlock enforcement when `abi > 0` and clean no-op telemetry when kernel ABI is `-1`. Always preserve the 60 `/opt/floworkos/tools/*/run` hardlinks via `ln -f` when deploying `/opt/floworkos/bin/flowork-tool-runner`.
- **`flowork-sysd` (`/opt/floworkos/sysd/src/drm_capture.rs`):** Atomically publishes captures to `/dev/shm/flowork_drm_latest.bgra` and `/dev/shm/flowork_drm_latest.json`.
- **Root Provisioning Script:** `/opt/floworkos/system/kernel/enable-landlock-and-nvidia.sh` + `/opt/floworkos/system/tmpfiles.d/flowork.conf` document/automate root-only `/run/flowork`, `/usr/local/bin/flowork-sysd`, NVIDIA DKMS, and kernel Landlock flags.
