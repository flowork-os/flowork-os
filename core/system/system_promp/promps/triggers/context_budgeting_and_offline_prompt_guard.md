# CONTEXT BUDGETING & OFFLINE PROMPT EXTRACTION GUARD

## 1. Context & Activation Scope
Triggered when developing, debugging, or auditing `mrflow-rs` context management (`context/mod.rs`), `flowork-sysd` completions routing (`routes.rs`), or multi-step agent tool loops.

## 2. Mandatory Behavioral Invariants
- **Multi-Step Token Ceiling:** Enforce `MAX_AUTO_COMPRESS_TOKENS_CEILING` (`65,000` tokens) in `should_auto_compress` to prevent multi-turn tool loops from breaching cloud 1,000,000 TPM quotas and exhausting account pools.
- **Aggressive Older Tool Response Collapsing:** Keep `COLLAPSE_HISTORY_BYTE_THRESHOLD` (`40,000` bytes) and `RECENT_TURNS_PROTECTED` (`2` turns) tight. Collapse tool output blobs exceeding 2KB into concise references for older turns.
- **Reverse User Prompt Extraction:** In `flowork-sysd/src/routes.rs:openai_chat_completions`, scan messages in reverse (`msgs.iter().rev()`) specifically for `role == "user"`. Strip `<session_context>` and extract `<USER_REQUEST>` contents.
- **Skip Binary Eviction Notices:** Never parse synthetic markers like `[Binary content ... omitted]` or `[Continued session turn]` as user intent during offline SLM failovers.
- **Sidebar Stage Lifecycle:** In `mrflow-sidebar` UI, invoke `closeExecutionStage()` on all terminal stream events (`done`, `result`, `cancelled`, `error`) to guarantee chat visibility. Merge adjacent assistant turns in session loading.

## 3. Strict Prohibitions
- Never allow uncompressed conversation history to exceed 75,000 tokens during multi-step tool turns.
- Never loop forward through OpenAI messages overwriting prompt text with intermediate assistant or memory placeholders.
