# 🛡️ SESSION ANTI-BLOAT & OUTPUT HARD-CAP GUARD

## 1. Context & Activation Scope
Applies when running shell commands, executing search tools, parsing session JSONL files, managing chat history, or handling agent turn serialization.

## 2. Mandatory Behavioral Invariants
- **Hard-Cap Output Truncation:** Commands emitting long outputs MUST be scoped with head/tail filters (`head -n 50`, `grep -m 20`). Never dump unconstrained logs, core dumps, or binary streams into tool responses.
- **Strict History Exclusion:** Global text searches (`grep`, `find`, `rg`) MUST always specify `--exclude-dir={history,node_modules,.git,dist,tmp,tool-outputs}` to prevent scanning past session JSONL files and causing recursive context explosion.
- **Session Compaction & Sanitization:** If an active session JSONL file approaches or exceeds 2 MB, the agent must sanitize oversized previous tool responses by truncating them down to concise summaries before inference dispatch.
- **Pre-Emptive Intercept Compliance:** Every tool invocation MUST provide all required schema parameters (`goal`, `reason`, `keywords` with at least 5 keywords) on every call to prevent Intercept Gate rejection loops and frozen turns.

## 3. Strict Prohibitions
- NEVER execute recursive grep across `/opt/floworkos/` or `$HOME` without explicitly excluding `history/` and `tmp/`.
- NEVER permit uncompacted tool outputs exceeding 50 KB into session history.
- NEVER loop on tool failures without providing valid `goal`, `reason`, and `keywords`.
