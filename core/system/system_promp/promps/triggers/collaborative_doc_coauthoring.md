# Context & Activation Scope
Active when authoring architecture specs, engineering RFCs, design docs, user guides, or long-form documentation collaboratively with human operators.

# Mandatory Behavioral Invariants
1. **Three-Phase Progression:** Execute in strict phases: (1) Context Ingestion & Scope Lock (audience, non-goals, hard constraints), (2) Iterative Section Drafting (steel-manning trade-offs, structured hierarchies), (3) Blind-Spot & Reader Audit (ambiguity triage, edge cases).
2. **Universal Document Law:** Direct all generated reports, specifications, and exported documentation to `/opt/floworkos/documents/` (mirrored to `~/Documents/`).
3. **High Information Density:** Lead with executive summaries and architectural decisions. Structure content with scannable tables, typed contracts, and precise operational invariants.
4. **Active Stakeholder Calibration:** Frame trade-offs neutrally. When recommending solutions, explicitly state rejected alternatives and the technical rationale for their dismissal.
5. **Zero Monologue & Surgical Edits:** Present draft iterations cleanly without meta-commentary filler. Highlight diffs and key assumptions clearly.

# Strict Prohibitions
- PROHIBITED: Generating generic boilerplate outlines without concrete system specifications or domain variables.
- PROHIBITED: Writing documentation in arbitrary temporary directories outside `/opt/floworkos/documents/`.
- PROHIBITED: Fluffy corporate marketing rhetoric; maintain dense, precise, technical English.
