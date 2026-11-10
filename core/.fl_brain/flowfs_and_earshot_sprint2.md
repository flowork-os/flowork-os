---
title: FlowFS Semantic Vector Search and Earshot Procedural Sound Architecture
category: architecture
keywords:
  - flowfs
  - semantic_search
  - vector_database
  - sqlite_vec
  - cosine_similarity
  - low_latency
  - background_indexer
  - resource_governance
  - cpu_throttling
  - earshot
  - procedural_audio
  - model_context_protocol
  - orbit_deck
  - spotlight
  - mcp_server
---
# FlowFS Semantic Vector Search and Earshot Procedural Sound Architecture

## Problem Statement
Traditional Linux desktop search relies on exact filename matches (`find`) or slow recursive disk scans (`grep`), failing when queries are conceptual or natural language. Furthermore, conventional operating systems bundle static `.wav` sound files that bloat ISO sizes and cannot dynamically adapt to user interface events.

## Architectural Solutions

### 1. FlowFS Vector Search Engine (`flowfs_core.py` & `flowfs-search`)
- **Normalized Vector Projections:** Generates 128-dimensional normalized deterministic feature hash projection vectors directly from document tokens without heavyweight cloud dependencies or massive LLM containers.
- **Sub-15ms Retrieval:** In-process BLAS dot-product caching (`flowfs_core.py`) executes cosine similarity scans across thousands of documents in **2.80 to 12.35 ms**.
- **Orbit Deck Spotlight Integration:** Querying Orbit Deck / Spotlight with `?` or entering any natural search phrase automatically enriches results with semantic matches from FlowFS.

### 2. Background Resource Governance (`flowfs-indexer-daemon`)
- **CPU & IO Constraints:** Runs with `nice +19`, `ionice class 3 (idle)`, and systemd unit cgroup slices `CPUWeight=20` and `IOWeight=20`.
- **Active Load Throttling:** Reads `/proc/stat` and automatically pauses indexing passes whenever system CPU utilization exceeds 70%, preventing UI lag or disk thrashing.

### 3. Earshot Procedural Sound Engine (`earshot_engine.py`)
- **Zero-Blob Audio Synthesis:** Generates high-fidelity UI feedback sounds (`click`, `pop`, `bell`, `shutter`, `laser`, `whoosh`) using mathematical DSP wave formulas on the CPU, removing static `.wav` files from the ISO.
- **MCP Tool Protocol:** Exposes `sfx_list`, `sfx_render`, `sfx_play`, and `audio_audit` to Mr. Flow via Model Context Protocol stdio JSON-RPC.
