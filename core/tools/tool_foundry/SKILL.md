# 🛠️ FLOWORK OS — DYNAMIC TOOL FOUNDRY PROCEDURES (SKILL.md)

## 1. Executive Purpose
The `tool_foundry` enables Mr. Flow to autonomously create, test, and register new tools in `/opt/floworkos/tools/` without restarting the system or modifying immutable base prompts.

## 2. Invariants & Rules
1. **Lowercase snake_case Naming**: Tools must strictly match `^[a-z][a-z0-9_]{1,63}$`.
2. **Decoupled Architecture**: Each tool must reside in its own folder under `/opt/floworkos/tools/<tool_name>/`.
3. **Clean I/O Contract**:
   - Inputs are sent via `stdin` as a single JSON object.
   - Outputs are written to `stdout` as valid JSON (or cleanly formatted text).
   - Any unhandled exceptions must output details to `stderr` and exit with non-zero exit code.
4. **Conditional Triggering**: All domain-specific tools MUST use `"activation": "conditional"` with at least 4 descriptive keywords to avoid token bloat.
5. **No Base Prompt Bloat**: New tools must NEVER inject guidelines into base prompts (`00_preamble.md`, etc.). Always document tool behavior inside its own `SKILL.md`.

## 3. Standard Foundry Actions
- `create`: Validates manifest, creates isolated staging `/tmp/foundry/<name>/`, executes test run with `test_input`, verifies Exit Code 0, and atomically promotes to `/opt/floworkos/tools/<name>/`.
- `test`: Performs staging and test execution without permanent promotion.
- `inspect`: Reads manifest and lists files of an existing registered tool.
- `retire`: Safely deletes an obsolete synthesized tool from registry (protected core tools cannot be retired).
