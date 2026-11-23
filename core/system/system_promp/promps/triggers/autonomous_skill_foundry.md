# Context & Activation Scope
Active when creating, auditing, modifying, or evaluating sovereign skills, tool modules, or subagent SOPs within `/opt/floworkos/skills/` or tool foundry pipelines.

# Mandatory Behavioral Invariants
1. **Canonical Skill Anatomy:** Every sovereign skill must reside in `/opt/floworkos/skills/<skill-name>/` with a clean `SKILL.md` containing: YAML frontmatter (name, description, required dependencies), Operational Invariants, Step-by-Step SOP, and Empirical Validation Proofs.
2. **Progressive Disclosure:** Keep baseline skill specifications compact. Deep execution checklists, scripts, and supplementary schemas must be modularized into sub-files or on-demand references to preserve context window tokens.
3. **Deterministic Evaluation:** Every authored skill must include concrete test cases and verification criteria executable via CLI (Exit Code 0) before being added to available skills.
4. **Tool Grounding:** Ground skill workflows strictly in Flowork OS native tools (`run_shell_command`, `read_file`, `write_file`, `replace`, `agent_browser`, `agent_desktop`).

# Strict Prohibitions
- PROHIBITED: Creating monolithic, multi-thousand-line skills that pollute agent context with redundant instructions.
- PROHIBITED: Declaring hypothetical tools or third-party cloud APIs without native local Flowork OS bindings.
- PROHIBITED: Saving skills outside the canonical `/opt/floworkos/skills/` repository.
