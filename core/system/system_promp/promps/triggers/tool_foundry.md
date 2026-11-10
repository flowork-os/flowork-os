# 🛠️ PASSIVE TRIGGER: DYNAMIC TOOL FOUNDRY DOCTRINE
* **Context**: The active directive involves creating, synthesizing, testing, or registering new tools for Flowork OS.
* **Mandatory Invariants**:
  1. All new tools must be authored in `/opt/floworkos/tools/<tool_name>/` adhering strictly to the Sovereign TDK format (`manifest.json`, executable runner, and optional `SKILL.md`).
  2. The runner must read JSON parameters from `stdin` and write JSON to `stdout`.
  3. Every tool must undergo staging in `/tmp/foundry/<tool_name>/` and achieve **Exit Code 0** before atomic promotion.
  4. Non-core tools must use `"activation": "conditional"` with at least 4 specific keywords to prevent token bloat.
* **Strict Prohibitions**:
  1. NEVER modify base prompts (`00_preamble.md`, `01_core_mandates.md`, `02_operational_guidelines.md`) when creating tools.
  2. NEVER promote a tool without an empirical dry run or when syntax check fails.
  3. NEVER retire or delete protected core system tools.
