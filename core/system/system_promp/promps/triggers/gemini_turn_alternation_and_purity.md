# GEMINI TURN ALTERNATION & TOOL RESPONSE PURITY DOCTRINE

## 1. Context & Activation Scope
Triggered when developing, debugging, or reviewing chat history serialization, session resume (`--resume`), tool responses, or Gemini CloudCode API turn sequencing in `mrflow-rs` (`context/mod.rs`, `session/mod.rs`) and `connector-rs` (`translator.rs`, `proxy.rs`).

## 2. Mandatory Architectural Invariants
- **Strict Turn Alternation:** Google Gemini API requires strict role alternation (`user` -> `model` -> `user` -> `model`). Consecutive same-role turns without intervening responses are forbidden.
- **Pure FunctionResponse Turns:** A `user` turn containing `functionResponse` parts MUST contain ONLY `functionResponse` parts. Never mix `text` and `functionResponse` within the same turn.
- **Model Bridging on User Follow-Up:** When user text prompts follow an unacknowledged tool response (e.g. during session resumes or asynchronous steers), ALWAYS insert a synthetic model acknowledgment turn (`role: "model", parts: [{"text": "Tool execution completed."}]`) between the tool response turn and the subsequent user turn.
- **Anti-Coalesce Isolation:** In `coalesce_consecutive_turns` and `merge_adjacent_same_role`, NEVER merge a `functionResponse` turn with a standard chat `text` turn. Merge only like-with-like (text with text, or tool responses with tool responses).
- **No Blunt Watchdogs:** Never use arbitrary client-side SIGKILL timers (such as a 90s hard watchdog) on streaming agents. Respect transport backoff and user-driven aborts (`SIGINT`/`SIGTERM`/Stop button).

## 3. Strict Prohibitions
- NEVER append trailing user text directly into `ordered` function response vectors.
- NEVER send adjacent `user` turns without a intervening `model` turn to Gemini API.
