# 🛠️ Dynamic Tool Foundry — Sovereign Architecture & Implementation Plan

## 1. Objective & Overview
Build the **Dynamic Tool Foundry** subsystem in `/opt/floworkos/tools/tool_foundry/` and `/opt/floworkos/tools/fl_tool_foundry.py`. 
This allows Mr. Flow to autonomously synthesize, test, validate, and register new tools within `/opt/floworkos/tools/` under a strict 4-stage empirical verification pipeline (Exit Code 0), zero-token bloat, and automated rollback upon failure.

---

## 2. Key Files & Architecture

### Existing System Context
- `/opt/floworkos/tools/README.md` — Sovereign TDK Specification & directory layout (`manifest.json`, runner, `SKILL.md`).
- `/opt/floworkos/tools/discovery.js` — Dynamic tool discovery runner scanning `/opt/floworkos/tools/` and injecting Flowork Intercept Gate fields (`reason`, `keywords`, `goal`).
- `/opt/floworkos/tools/executor.js` — Standard dispatcher handling stdin/stdout and runner selection (`run`, `run.js`, `run.py`, `run.sh`).

### New Components to Create
1. **`/opt/floworkos/tools/fl_tool_foundry.py`**
   - Core Python engine providing CLI & API for:
     - `validate_manifest`: Verifies TDK compliance (`name`, `description`, `activation`, `triggers`, `parametersJsonSchema`).
     - `stage_and_test`: Stages tool in isolated `/tmp/foundry/<tool_name>/`, executes test run with provided sample input, checks timeout, exit code, and stdout JSON validity.
     - `promote_tool`: Atomically moves validated tool to `/opt/floworkos/tools/<tool_name>/`, applies `chmod +x`, and confirms registration in `discovery.js`.
     - `rollback_tool`: Purges staging and restores prior state if promotion fails.
     - `retire_tool`: Safely unregisters/deletes a synthesized tool when obsolete.
2. **`/opt/floworkos/tools/tool_foundry/`**
   - `manifest.json`: Tool manifest declaring action parameters (`action: create | test | retire | inspect`, tool spec, code, test input).
   - `run.py`: Executable runner bridging tool calls from Mr. Flow CLI / `executor.js` to `fl_tool_foundry.py`.
   - `SKILL.md`: JIT-injected procedural guidelines on how to craft robust, minimal, decoupled tools.
3. **Automated Verification Harness (`/opt/floworkos/tools/test_tool_foundry.py`)**
   - Unit and integration tests verifying both success paths and failure rollback paths.

---

## 3. Four-Stage Verification Pipeline (Empirical Exit Code 0)

Every tool synthesized by the foundry must strictly pass 4 validation gates before promotion:
1. **Gate 1: TDK Schema & Naming Linting**
   - Tool name must match regex `^[a-z0-9_]+$` (lowercase snake_case).
   - Manifest must have valid `description`, `activation` (`"conditional"` or `"always"`), `triggers.keywords` (>= 4 keywords), and compliant `parametersJsonSchema`.
2. **Gate 2: Isolated Staging & Dependency Check**
   - Files created in `/tmp/foundry/<tool_name>/` with correct file permissions (`0o755`).
   - Runner syntax check (`python3 -m py_compile`, `node --check`, or `bash -n`).
3. **Gate 3: Empirical Test Execution**
   - Subprocess spawned in staging sandbox with specified `test_input` via `stdin`.
   - Enforce execution timeout (max 10s).
   - Must finish with **Exit Code 0** and emit valid JSON/text to `stdout`.
4. **Gate 4: Atomic Promotion & Discovery Verification**
   - Directory moved to `/opt/floworkos/tools/<tool_name>/`.
   - Run `node /opt/floworkos/tools/discovery.js` to empirically confirm the tool is discovered and valid.
   - If any step fails, immediate rollback is triggered; workspace remains clean.

---

## 4. Implementation Steps

1. **Step 1: Core Engine (`/opt/floworkos/tools/fl_tool_foundry.py`)**
   - Implement manifest schema validator.
   - Implement runner syntax validator for Node.js, Python, and Bash.
   - Implement sandbox execution runner with stdin injection and exit code inspection.
   - Implement atomic directory promotion and rollback.
2. **Step 2: Tool Manifest & Runner (`/opt/floworkos/tools/tool_foundry/`)**
   - Author `manifest.json` with conditional trigger keywords: `foundry`, `create tool`, `synthesize tool`, `new tool`, `register tool`.
   - Author `run.py` that reads stdin JSON, executes requested action, and outputs structured status.
   - Author `SKILL.md` documenting best practices for synthetic tools.
3. **Step 3: Verification & Test Suite**
   - Author `/opt/floworkos/tools/test_tool_foundry.py`.
   - Test 1: Synthesize a sample utility tool (e.g., `fl_hash_digest`).
   - Test 2: Trigger intentional failure (bad syntax / non-zero exit code) to confirm rollback leaves `/opt/floworkos/tools/` untouched.
   - Test 3: Confirm `discovery.js` detects the new tool.
   - Test 4: Retire the sample test tool and verify cleanup.

---

## 5. Verification & Finality Standard
- Execute `python3 /opt/floworkos/tools/test_tool_foundry.py` -> Must pass all tests with Exit Code 0.
- Execute `node /opt/floworkos/tools/discovery.js` -> Must discover `tool_foundry` without schema warnings.
