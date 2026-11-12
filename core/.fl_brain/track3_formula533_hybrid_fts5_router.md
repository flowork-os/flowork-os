---
title: Track 3 Milestone - Formula533Router v2 Hybrid FTS5, Bilingual Aliases, Cross-Pillar Graph, and Telemetry
category: architecture
keywords:
  - formula533_router
  - sqlite_fts5
  - bm25_scoring
  - router_aliases
  - pillar_graph
  - cross_pillar_affinity
  - bilingual_intent_routing
  - zero_bloat_doctrine
  - router_telemetry
  - dry_run_route
  - stemmer_tokenization
  - mrflow_rs
date: 2026-11-12
---

# Track 3: Formula533Router v2 Hybrid Cognitive Routing Engine

## 1. Architectural Upgrade Overview
Upgraded `Formula533Router` inside `/opt/floworkos/mrflow-rs/src/cognitive/mod.rs` from strict exact-token intersection into a 3-layer hybrid router while preserving strict `5-3-3` hard caps and Zero-Bloat thresholds.

## 2. Core Components Implemented
- **Layer 1 (Stemming & Compound Tokenization):**
  - Added deterministic suffix stemmer (`stem_token`) and underscore/hyphen sub-token expansion inside `tokenize_set` so snake_case skill/tool keywords (`audio_mastering`, `vulnerability_audit`) match standalone stem queries cleanly.
  - Preserved conservative tokenization inside `load_conditional_prompts` so compound trigger tokens (`kamidi_mastering_cli`) do not cause passive-trigger prompt bloat on unrelated turns.
- **Layer 2 (Hot-Reloadable Bilingual Aliases + In-Memory SQLite FTS5 BM25):**
  - Created `/opt/floworkos/system/system_promp/router_aliases.json` mapping Indonesian/slang/general queries to canonical English tokens with mtime-based hot-reload (no `mrflow` recompilation needed).
  - Built an in-memory SQLite FTS5 virtual table (`tokenize='porter unicode61'`) indexing tools, skills, and prompts; BM25 ranking corroborates lexical/alias hits (`signals >= 2` required for alias-only activation).
- **Layer 3 (Cross-Pillar Affinity Graph & Telemetry):**
  - Created `/opt/floworkos/system/system_promp/pillar_graph.json` defining `+6..+8` structural affinity edges across CWD apps (`detect_cwd_affinity_nodes`), active skills, and tools.
  - Recorded impressions and activations (`record_activation`) to WAL SQLite `router_metrics.db` (`FLOWORK_ROUTER_METRICS_DB` -> `/opt/floworkos/history/router_metrics.db` if writable -> `~/.flowork/history/router_metrics.db`).
  - Added CLI diagnostics `mrflow --dry-run-route "<prompt>"` and `mrflow --router-audit`.

## 3. Verification
- `cargo test -p mrflow`: 30 passed, 0 failed.
- Verified `mrflow --dry-run-route "tolong bersihin noise rekaman suara podcast"` injects `kamidi-mastering` and `mcp_earshot_*` audio tools with `0` extraneous prompt triggers.
