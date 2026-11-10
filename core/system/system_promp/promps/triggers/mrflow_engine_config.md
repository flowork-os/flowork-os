# ⚙️ Mr. Flow Engine Configuration & Dynamic Runtime Parameters
- **Context:** Managing runtime execution horizons, turn limits, loop detection, and standalone binary packaging for Mr. Flow.
- **Mandatory Invariants:**
  1. **Canonical Config:** All runtime limits (`FLOWORK_MAX_TURNS`, `FLOWORK_SUBAGENT_MAX_TURNS`, `FLOWORK_LOOP_THRESHOLD`, `FLOWORK_LLM_CHECK_AFTER_TURNS`) reside exclusively in `/opt/floworkos/system/mrflow.env`.
  2. **Cascading Precedence:** Runtime evaluation must follow: CLI flags > `$HOME/.flowork/mrflow.env` > `/opt/floworkos/system/mrflow.env` > Invariant fallbacks (300 turns, 300 subagents, 5 loop threshold).
  3. **Zero Hardcoded Limits:** Any compiled binary of Mr. Flow must dynamically parse environment variables and external configs rather than embedding immutable integers.
- **Prohibitions:**
  - FORBIDDEN to bake static turn limits into binary builds or bundle chunks without environment variable fallback.
  - FORBIDDEN to pollute base system prompts with transient operational configs.
