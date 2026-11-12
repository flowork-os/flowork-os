# CONNECTOR ROTATION & SSE STREAM TIMEOUT GUARD

## 1. Context & Activation Scope
Triggered when developing, debugging, or auditing `flowork-connector` account rotation (`vault.rs`, `proxy.rs`) or `mrflow-rs` SSE client streaming (`inference/mod.rs`).

## 2. Mandatory Behavioral Invariants
- **Exclude Tried Accounts:** Pass a per-request `tried_account_ids` `HashSet` into `VaultManager::select_next_available_index_excluding` so the retry loop never re-picks a failing active account on subsequent iterations.
- **Cooldown on Transport & 5xx Failures:** Immediately call `mark_account_cooldown` on upstream send errors, TTFB timeouts, HTTP `5xx` responses, pre-stream read errors, empty `200 OK` closes, and first-chunk stalls so broken accounts move to the queue tail.
- **Bounded Multi-Account TTFB & Pre-Commit First Chunk:** Cap multi-account TTFB and first SSE chunk waits (`<=30s`) BEFORE returning `StatusCode::OK` to the caller so hung CloudCode accounts rotate cleanly.
- **SSE Per-Chunk Idle Bounds:** Enforce finite idle timeouts between SSE chunks (`60s` in `proxy.rs`, `90s` in `mrflow-rs`) to prevent half-open sockets from wedging agents.

## 3. Strict Prohibitions
- Never pass `exclude_id = None` inside multi-attempt account rotation loops.
- Never commit streaming `HTTP 200` headers before verifying an upstream chunk arrives.
