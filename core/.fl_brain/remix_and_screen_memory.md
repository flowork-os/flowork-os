---
title: Sovereign App Remix Engine and FlowFS Multimodal Screen Memory
category: architecture
keywords:
  - flowpkg_remix
  - flowfs_screen_memory
  - ambient_eye
  - vector_database
  - semantic_search
  - app_customization
date: 2026-11-09
---

# Sovereign App Remix Engine & FlowFS Multimodal Screen Memory

## 1. Track 2: Instant App "Remix" Engine (`flowpkg remix`)
- **CLI Subcommand:** `/opt/floworkos/bin/flowpkg remix <target> [--prompt "..." | --inspect | --apply]`
- **Capabilities:**
  - Dynamic discovery and staging of applications directly from `/opt/floworkos/apps/<app_id>` or standalone `.flowapp` bundles.
  - Component introspection: maps interactive Quantum Glass WebKit frontend (`ui/index.html`, CSS, JS) and Python/Rust logic entrypoints.
  - Neural Bus Integration: dispatches `app.remix_started` events over port 18095.
  - In-place directive tracking via `REMIX_NOTES.md` and automated headless test/registration passes via `craft-app test` & `register`.

## 2. Track 3: FlowFS Multimodal Screen Memory & Visual Search
- **Storage Layer (`flowfs_core.py`):**
  - Added `flow_screen_memory` table with full 128-dim vector embeddings and timestamp indexing.
  - Implemented `index_screen_capture(screenshot_path, window_title, app_class, text)` computing semantic cosine embeddings.
  - Implemented `search_screen_memory(query, limit)` achieving sub-millisecond vector retrieval (~0.38ms).
- **Capture Integration (`flowork-ambient-eye`):**
  - Seamlessly links background desktop screenshots to FlowFS vector memory without blocking the user.
- **Search CLI (`flowfs-search --screen`):**
  - Added `--screen` (`-c`) flag to retrieve historical visual desktop moments with matching percentages, timestamps, active window contexts, and screenshot preview file paths.
  - Fully supports `--json` programmatic output mode.
