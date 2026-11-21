# ACTION-BIAS ASSET SYNTHESIS & ANTI-PARALYSIS DIRECTIVE

## 1. Context & Activation Scope
Active when generating videos, animation pipelines, code templates, multimedia assets, or executing skill workflows (`githubtoyoutube`, `cutvii`, `flow-repo`, `video_render`, `creative_production`).

## 2. Mandatory Behavioral Invariants
- **Direct Template Instantiation:** When generating videos or procedural animations, clone reference template scripts directly into target files (`cp <template> <target>`) and adapt parameters via targeted replacements. Maximum 2 read operations per reference file.
- **Render-First Execution Velocity:** Achieve initial prototype render within 10 turns. Never delay rendering to perform exhaustive micro-inspections of fonts, encoders, or sub-functions.
- **Stateless Session Continuation:** When user resumes (`lanjut`, `continue`), immediately inspect workspace deliverables and existing generated artifacts (`/tmp/*.wav`, `*.mp4`, screenshots). Never parse or dump previous session JSONL transcripts.
- **Strict Turn Ceiling:** Allocate maximum 15 turns for complete end-to-end asset generation pipeline (Research -> Audio -> Script Clone -> Hardware Render -> Ledger Commit).

## 3. Strict Prohibitions
- NEVER read template files piecemeal in multiple consecutive slices (>3 slices strictly forbidden).
- NEVER execute repetitive environment or font verification commands (`fc-list`, `python -c "import..."`) after the first check.
- NEVER parse or grep session transcript files (`session-*.jsonl`) during continuation turns.
