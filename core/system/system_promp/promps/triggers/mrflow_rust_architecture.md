# MRFLOW CLEAN-ROOM RUST ENGINE ARCHITECTURE

## 1. Context & Activation Scope
Triggered when inspecting, modifying, compiling, or packaging `/opt/floworkos/mrflow-rs/` or `/opt/floworkos/bin/mrflow`.

## 2. Mandatory Behavioral Invariants
- Preserve byte-level NDJSON compatibility (`init`, `message`, `thought`, `tool_use`, `tool_result`, `error`, `result`) consumed by `mrflow-sidebar.py`.
- Sanitize every dynamic and MCP tool schema through `sanitize_gemini_schema()` so array types (`["string", "null"]`) flatten into `{ type, nullable: true }` before CloudCode submission.
- Keep interactive HUD cell backgrounds strictly transparent (`Color::Reset`) with `#ffffff` crystal white and `#00ff66` accents.
- Compile release distributions stripped with `--remap-path-prefix=$HOME=/opt/build` and verify `strings` contains zero personal usernames or legacy bundle strings before installing to `/opt/floworkos/bin/mrflow`.
- Drain child `stdout`/`stderr` pipes via bounded async readers with a short post-exit grace period (`PIPE_DRAIN_GRACE`) so detached background descendants holding pipe FDs cannot stall `run_shell_command`, and enforce a 300s TTL in `read_active_watchdog_trigger()`.
- Maintain dual lossless + compacted JSONL (`compression_snapshot`, `$rewind`, `$set.summary`, coalesced `rawParts`) paired with 3-layer output offloading/masking and `prepare_history_for_api()` call/response pairing.
- Dynamically discover external `/opt/floworkos/` assets (`triggers.json` DSL + `.bin` rules, multi-transport `Stdio`/`StreamableHttp`/`Sse` MCP with `${VAR}` expansion & `includeTools`/`excludeTools`, policies, tools, skills, agents) without recompiling.

## 3. Strict Prohibitions
- Never reintroduce Node.js wrappers, `@google/gemini-cli`, or legacy filename lookups (`GEMINI.md`) inside `mrflow-rs`.
- Never hardcode personal user home paths into Rust sources or compiled ELF binaries.
