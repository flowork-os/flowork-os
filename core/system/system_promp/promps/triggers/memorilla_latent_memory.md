# 🧬 PASSIVE TRIGGER: STANFORD MEMORILLA LATENT SEMANTIC MEMORY INVARIANTS

## 1. Context & Activation Scope
Triggered when engineering, querying, or troubleshooting `mrflow-rs` latent memory, cross-session grounding, session amnesia prevention, token compaction, or `.fl_brain/memorilla.db` slots (`memorilla`, `latent_memory`, `semantic_slot`, `session_amnesia`, `dual_tier_memory`, `state_invariant`).

## 2. Mandatory Architectural Invariants
- **Dual-Tier Memory Model:** Maintain the last 2-3 turns as raw working text. Compact older turns into structured `LatentMemorySlot` instances instead of bloating raw JSONL logs.
- **Deterministic Level-1 Micro-Compactor:** Extract touched files, command outcomes (`Exit Code 0`), and git revisions via native Rust (`compact_and_crystallize`) in `< 1ms`. Never invoke LLM calls during per-turn compaction to eliminate token waste and latency.
- **Surgical Grounding Capsule:** Format JIT recall into an ultra-dense `<MEMORILLA_LATENT_GROUNDING>` capsule (`< 120 tokens`). Never dump verbose multi-paragraph raw histories into system prompt envelopes.
- **Dual-Key Attention Retrieval Gate:** Enforce strict threshold gating (>= 0.70) combining causal path matching (0.50) and semantic keyword overlap (0.50) modulated by `decay_score`. If relevance falls below threshold, inject nothing (Zero Prompt Bloat).
- **Temporal Decay & Reward Weighting:** Verified turns (`Exit Code 0`) maintain maximum stability (`decay_score = 1.0`). Penalize turns with non-zero exits (`-0.2`). Upsert recurring slots via Hierarchical Merging.

## 3. Storage & Anti-Leak Rules
- Primary database resides at `/opt/floworkos/.fl_brain/memorilla.db` with WAL mode and FTS5 virtual indexing.
- Scrub personal paths (`$HOME`) and API secrets before slot insertion. Never commit active memory databases to public repositories.
