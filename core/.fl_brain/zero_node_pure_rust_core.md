---
title: Zero-Node Pure Rust System Core Migration & Native Binary Cutover
category: architecture
keywords:
  - zero_node_pure_rust
  - flowork_core_rs
  - connector_rs
  - flowork_neural_bus
  - flowork_browser_mcp
  - flowork_tool_runner
  - flowork_lint_skills
  - flowork_tool_discovery
  - flowork_edits_daemon
  - bird_x_python_graphql
  - agent_browser_native_elf
  - agent_desktop_native_elf
date: 2026-11-11
---

# Zero-Node Pure Rust System Core Migration & Native Binary Cutover

## 1. Architectural Shift
Replaced the host `nodejs` runtime dependency and all legacy Node/JS core backends inside `/opt/floworkos` with clean-room Pure Rust ELFs and pure Python 3 stdlib tooling:
- **Core Daemons & Runners (`/opt/floworkos/crates/flowork-core-rs/`):** `flowork-neural-bus` (`:18095`), `flowork-edits-daemon` (`:3456`), `flowork-lint-skills`, `flowork-tool-discovery`, `flowork-tool-executor`, `flowork-tool-runner` (hardlinked across `tools/*/run`), and `flowork-browser-mcp` (`/opt/floworkos/tools/browser_backend/flowork-browser-mcp`).
- **Sovereign Connector (`/opt/floworkos/connector-rs/`):** `flowork-connector` (`:9099`, `/opt/floworkos/connector/bin/flowork-connector`), eliminating `connector/server/index.js`.
- **Native Desktop & Browser Agent CLIs:** Relocated stripped Rust ELFs (`agent-browser`, `agent-desktop`, `agent-desktop-linux-clipboard-owner`) into `/usr/local/bin/` before removing `/usr/bin/agent-*` symlinks, `/usr/lib/node_modules`, and `nodejs` + `nodesource` APT sources.
- **Last30Days X GraphQL Client (`/opt/floworkos/skills/last30days/scripts/lib/bird_x.py`):** Replaced vendored `bird-search` Node runner with a pure-Python GraphQL `SearchTimeline` client and Python `brotli` decompression in `grok_audit.py`.

## 2. Guardrails & Boundaries
- Only browser-executed frontends (Chromium extensions, WebKit webviews, Tauri web assets) and the standalone Antigravity IDE (`/opt/floworkos/agent/`) remain outside this purge.
- `iso-builder/build-live-iso.sh` enforces Zero-Node / Pure Rust ELF pre-flight verification and excludes `crates/*/target`, `connector-rs/target`, `sysd/target`, `wm/target`, `apps/cutvii/src-tauri/target`, and `node_modules` from SquashFS mastering.
