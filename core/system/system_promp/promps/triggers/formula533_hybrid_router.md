# FORMULA 5-3-3 HYBRID ROUTER v2 DOCTRINE

## 1. Context & Activation Scope
Triggered when maintaining, auditing, or extending `Formula533Router` inside `mrflow-rs/src/cognitive/mod.rs`, `router_aliases.json`, `pillar_graph.json`, `--dry-run-route`, or `--router-audit`.

## 2. Mandatory Behavioral Invariants
- **Strict Zero-Bloat Caps:** Enforce hard `5` tools, `3` skills, and `3` deduplicated passive prompts; alias/FTS5 candidates require at least `2` independent matched signals or a validated Layer-3 affinity anchor before crossing score `>= 10`.
- **Conservative Prompt Tokenization:** Keep underscore CLI trigger identifiers (e.g. `*_cli`) intact inside `PromptTriggerMeta` so multi-word audio or dev manifests never leak unrelated passive triggers.
- **Hot-Reload & Non-Blocking Telemetry:** Load `router_aliases.json` and `pillar_graph.json` dynamically via mtime checks; route metrics fallback cleanly to `$HOME/.flowork/history/router_metrics.db` when `/opt/floworkos/history/` is not user-writable.
- **Diagnostics Zero-Contamination:** Run `mrflow --dry-run-route` with `telemetry_enabled = false` and empty synthetic `reason` tokens so diagnostics never distort routing scores or metrics.

## 3. Strict Prohibitions
- NEVER raise cap limits above `5-3-3` or inject uncorroborated single-token BM25 matches into system prompts.
- NEVER pass unescaped punctuation directly into SQLite FTS5 `MATCH` expressions; sanitize tokens first.
