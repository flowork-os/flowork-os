---
title: Mr. Flow Clean-Room Native Rust Autonomous Agent Engine (v2.0.0-sovereign)
category: architecture
keywords:
  - mrflow_rust_engine
  - clean_room_rewrite
  - native_elf_binary
  - sovereign_glass_hud
  - ratatui_transparent_reset
  - connector_gateway_sse
  - gemini_schema_sanitizer
  - flowork_bookmarks_parity
  - five_tier_policy_engine
  - formula_533_router
  - stdio_mcp_client
  - dynamic_tool_manifest
  - append_only_jsonl_vault
  - subagent_orchestrator
  - pgid_process_isolation
  - zero_node_bundle_cutover
date: 2026-11-11
---

# Mr. Flow Clean-Room Native Rust Autonomous Agent Engine (`v2.0.0-sovereign`)

## 1. Cutover Summary & Performance Metrics
- **Source Crate:** `/opt/floworkos/mrflow-rs/` (`edition = "2021"`, compiled with `--release` LTO + strip + `--remap-path-prefix=$HOME=/opt/build`).
- **Installed Binary:** `/opt/floworkos/bin/mrflow` (`6.3 MB` native x86-64 ELF; `/usr/local/bin/mrflow -> /opt/floworkos/bin/mrflow`; 25 unit tests passing).
- **Startup Latency:** `0.002s` (`2 ms` for `--version`, vs ~2s Node.js startup).
- **Removed Legacy Artifacts:** Eradicated `/opt/floworkos/lib/mrflow/mrflow-core.mjs`, `/usr/lib/node_modules/@google/gemini-cli/`, `/usr/bin/gemini`, and GitHub `licenses/gemini-cli/` notices.

## 2. Preserved Flowork OS External & Context Parity
- **Cognitive Subsystem (`src/cognitive/mod.rs`):** Loads `00_preamble.md`, `01_core_mandates.md`, `02_operational_guidelines.md`, evaluates `prompts/triggers.json` DSL dynamically, executes parallel native rule binaries (`/opt/floworkos/system/system_promp/rules/.bin/*` + scripts), `/tmp/flowork_active_trigger.json` alerts (300s TTL), `FLOWORK.md` hierarchy (`src/memory/mod.rs`), 13+ skills (`/opt/floworkos/skills/` & `~/.flowork/skills/`), and Formula 5-3-3 sliding window router with flat `keywords` support & carryover.
- **Context & Compression (`src/context/mod.rs`, `src/engine.rs`):** 3-layer tool output truncation/offload (`truncate_and_offload_output`), backward FIFO masking, old response collapse/binary eviction, `prepare_history_for_api()` part coalescing + unanswered call repair, and real 2-pass LLM `<state_snapshot>` compression (`/compress` + auto threshold).
- **Tools & Intercept Gate (`src/tools/mod.rs`):** Fast built-ins (`read_file` + screenshot `InlineBlob`, `write_file`, `replace`, `list_directory`, `glob`, `grep_search`, PTY/PGID `run_shell_command`, `write_todos`, `.flowork/tracker` DAG, `activate_skill`, `web_fetch`, `ask_user`, plan mode tools, `invoke_agent`), multi-dir dynamic tool scanner with first-use `<flowork_tool_skill>` injection & `tool_foundry` rescan, and strict `(reason, keywords, goal)` intercept validation.
- **MCP & Subagents (`src/mcp/mod.rs`, `src/agents/mod.rs`):** Multi-transport `Stdio` / `StreamableHttp` / `Sse` MCP client with `${VAR}` interpolation & `includeTools`/`excludeTools` filtering scanning `/opt/floworkos/mcp/*`, `~/.flowork/mcp/*`, `.mcp.json`, and `settings.json`; isolated subagent spawner with tool allowlists, `max_turns`, and flat-1 recursion guard.
- **Inference & Protobuf Schema Sanitizer (`src/inference/mod.rs`):** Streams CloudCode SSE via `:9099/v1beta/models/...:streamGenerateContent?alt=sse` and OpenAI/Ollama SSE via `/v1/chat/completions`, preserving `thought` & `thoughtSignature`. Recursive `sanitize_gemini_schema()` converts draft-2020-12 array types and unions into valid CloudCode OpenAPI protobuf schemas (`nullable: true`) and prevents retry/failover on `INVALID_ARGUMENT`.
- **Policy, Dual Session Vault, Stream-JSON & Glass HUD (`src/policy`, `src/session`, `src/output`, `src/tui`):** 5-tier TOML policy evaluator respecting `allowRedirection`/`allowCommandSubstitution`/scoped rules; dual lossless (`user`/`gemini`/`toolCalls`/`rawParts`) + compressed (`compression_snapshot`/`$rewind`/`$set.summary`) append-only JSONL vault compatible with `mrflow-sidebar.py` & `--resume`; `StreamJsonEmitter`; `ratatui` `Color::Reset` interactive HUD with `| Ctx: XX%` meter.
