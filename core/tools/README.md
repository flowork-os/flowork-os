# ⚡ FLOWORK OS — SOVEREIGN TOOL ARCHITECTURE & DEVELOPMENT STANDARD
> **Sovereign Tool Development Kit (TDK) & Runtime Specification**  
> **Authority:** Awenkaudico & TeguhFX (LV99 Super Admin)  
> **System Architect:** Dr. Flow — Chief Architect of Flowork OS  
> **Territory:** `/opt/floworkos/tools/`  
> **Compliance Status:** MANDATORY SYSTEM STANDARD (STRICT ENGLISH — EXIT CODE 0)

---

## 1. CORE DOCTRINE OF FLOWORK OS TOOLS

In Flowork OS, tools are not mere function declarations or API stubs. Tools are sovereign operational instruments executed directly within the operating system environment. The Flowork OS Tool Architecture resolves four fatal architectural flaws found in standard AI agents:

1. **Zero-Token Bloat (Scalability to 1,000,000+ Tools):**  
   Standard agents blindly cram every tool declaration into the initial system prompt, burning tens of thousands of tokens per turn. In Flowork OS, domain-specific tools default to `conditional` activation and remain hidden (*zero token overhead*) until triggered by semantic keywords or environmental behavior.
2. **Dual-Track Triggering & Absolute Exclusion Veto (`keywords` vs `exclude_keywords`):**  
   Tools are dynamically activated when relevant keywords appear in user instructions or agent audit fields (`reason`/`keywords`). Crucially, tools possess an absolute veto rule (`exclude_keywords`) to suppress activation in conflicting contexts (e.g., active on `youtube.com`, but strictly suppressed when working on `studio.youtube.com`).
3. **Just-In-Time (JIT) Skill Injection:**  
   Complex tools carry their own expert procedures via an optional `SKILL.md` file located inside the tool's directory. When an agent executes the tool, the engine automatically injects the procedural guidelines directly into the next turn's function response.
4. **Empirical Verification & Intercept Gate (Exit Code 0):**  
   Every tool invocation requires an audit rationale (`reason`), semantic routing tags (`keywords`), and a high-level operational objective (`goal`). Execution validity is measured strictly by empirical terminal exit codes (`Exit Code 0`).

---

## 2. STANDARD DIRECTORY LAYOUT & CATALOG

Flowork OS pairs **core Rust built-in tools** compiled directly into `mrflow` (`read_file`, `read_many_files`, `write_file`, `replace`, `list_directory`, `glob`, `grep_search`, `run_shell_command`, `list_background_processes`, `read_background_output`, `write_todos`, `tracker_*`, `activate_skill`, `web_fetch`, `flowork_web_search`, `list_mcp_resources`, `read_mcp_resource`, `ask_user`, `enter_plan_mode`, `exit_plan_mode`, `invoke_agent`, `complete_task`, `update_topic`, plus `7` `core_fallback_definitions`) with **70 decoupled manifest tools** under `/opt/floworkos/tools/<tool_name>/`:

```text
/opt/floworkos/tools/<tool_name>/
├── manifest.json       # [MANDATORY] Metadata, activation mode, triggers, & parameter schemas
├── run                 # [RUNNER] Checked by exec_disk_tool in order: manifest.(entrypoint|runner) -> run -> run.sh -> run.py
└── SKILL.md            # [OPTIONAL / RECOMMENDED] Expert SOP & operational rules (JIT auto-injected)
```

> **Naming Conventions:**
> - Directory and tool names must strictly use lowercase snake_case (e.g., `system_log_watcher`, `php_artisan`, `git_advanced`).
> - Spaces, uppercase letters, and special characters are forbidden.

---

## 3. `manifest.json` SPECIFICATION

The `manifest.json` file serves as the identity card and routing descriptor for the native Rust discovery engine (`/opt/floworkos/bin/flowork-tool-discovery`), context evaluator, and dynamic router (`mrflow-rs/src/cognitive/mod.rs`).

### Complete Schema Template:
```json
{
  "name": "your_tool_name",
  "description": "Clear, concise technical description in English explaining what the tool does.",
  "activation": "conditional",
  "triggers": {
    "keywords": [
      "primary_keyword",
      "action_keyword",
      "technical_term",
      "domain_phrase"
    ],
    "exclude_keywords": [
      "conflicting_context",
      "unsupported_environment"
    ],
    "behavior": {
      "file_extensions": [".php", ".py", ".rs"],
      "domains": ["github.com", "api.example.com"],
      "files": ["composer.json", "Cargo.toml", "pyproject.toml"]
    }
  },
  "skill": "SKILL.md",
  "parametersJsonSchema": {
    "type": "object",
    "properties": {
      "target_param": {
        "type": "string",
        "description": "Detailed explanation of this input argument."
      },
      "dry_run": {
        "type": "boolean",
        "description": "Optional flag to simulate execution without state changes."
      }
    },
    "required": [
      "target_param"
    ]
  }
}
```

### Property Breakdown:

| Property | Type | Options | Description |
|---|---|---|---|
| `name` | String | `snake_case` | Unique identifier. Must match the tool directory name exactly. |
| `description` | String | Strict English | Technical summary of capabilities exposed to the LLM. |
| `activation` | String | `"always"` \| `"conditional"` | **`always`**: Core fundamental tool (declared in every turn).<br>**`conditional`**: Domain-specific tool (hidden until triggered). |
| `triggers.keywords` | Array | English strings | Keywords that trigger tool activation when found in user input or agent's `reason`/`keywords`. |
| `triggers.exclude_keywords` | Array | English strings | **Absolute Veto:** If any listed word appears in context, the tool is strictly suppressed, overriding inclusion. |
| `triggers.behavior` | Object | Rules object | Environmental context sniffer matching active workspace file extensions, browser domains, or landmark root files. |
| `skill` | String | `"SKILL.md"` | Relative path to expert procedural documentation injected upon first successful execution. |
| `entrypoint` / `runner` | String | Optional | Explicit relative runner path prioritized before `run` / `run.sh` / `run.py`. |
| `parametersJsonSchema` | Object | JSON Schema | Standard JSON Schema defining input parameters required by the runner. |

> **CRITICAL INVARIANT:**  
> Do **NOT** declare `reason`, `keywords`, or `goal` inside `parametersJsonSchema`. `ToolRegistry` (`mrflow-rs/src/tools/mod.rs`) and `flowork-tool-discovery` automatically inject these Intercept Gate parameters into tool definitions.

---

## 4. `run` / `run.py` / `run.sh` EXECUTOR SPECIFICATION

`ToolRegistry::exec_disk_tool` (`mrflow-rs/src/tools/mod.rs`) resolves decoupled runners in strict priority order: explicit `manifest.entrypoint` / `manifest.runner`, then `run` (ELF binary or executable), then `run.sh` (`/bin/bash`), then `run.py` (`/usr/bin/python3`), injecting `FLOWORK_TOOL_NAME` and writing JSON arguments on `stdin`.

### Implementation Rules:
1. Must be an ELF executable (`run`) or begin with `#!/usr/bin/env python3` (`run.py`) / `#!/usr/bin/env bash` (`run.sh`).
2. Must have executable file permissions (`chmod +x`).
3. Must accept JSON input via `STDIN` (and optionally CLI arguments or environment variables).
4. Must output clean, structured data (JSON preferred) to `stdout`.
5. **MANDATORY EXIT CODE 0:** Successful execution must terminate with exit code `0`. Errors must write diagnostic output to `stderr` and exit non-zero (`1`).

### Reference Template (`run.py`):
```python
#!/usr/bin/env python3
"""
⚡ FLOWORK OS — STANDALONE SOVEREIGN TOOL RUNNER
Tool: your_tool_name
"""

import json
import sys
from datetime import datetime, timezone

raw_input = sys.stdin.read().strip()
payload = json.loads(raw_input) if raw_input else {}
target_param = payload.get("target_param") or (sys.argv[1] if len(sys.argv) > 1 else "")

if not target_param:
    sys.stderr.write("FLOWORK TOOL ERROR: 'target_param' is mandatory.\n")
    sys.exit(1)

try:
    execution_result = {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": target_param,
        "payload": f"Sovereign execution for {target_param} completed.",
    }
    print(json.dumps(execution_result, indent=2))
    sys.exit(0)
except Exception as exc:
    sys.stderr.write(f"FLOWORK TOOL EXECUTION FAILED: {exc}\n")
    sys.exit(1)
```

---

## 5. `SKILL.md` SPECIFICATION (JUST-IN-TIME INJECTION)

Flowork OS tools are self-instructing: they carry expert procedural wisdom that is injected into working memory only once per session upon first use.

### Lifecycle of JIT Skill Injection:
1. The agent calls the tool and execution succeeds with `Exit Code 0`.
2. `ToolRegistry::execute_with_id` (`mrflow-rs/src/tools/mod.rs`) checks `meta.skill_file` (e.g. `/opt/floworkos/tools/<tool_name>/SKILL.md`) against the session `activated_tool_skills` set.
3. On first successful execution in the session, the directives are wrapped in `<flowork_tool_skill>` and appended to `display_text` plus the `_tool_skill_guidance` JSON field:
   ```text
   <flowork_tool_skill tool="your_tool_name">
   ... (Content of SKILL.md) ...
   </flowork_tool_skill>
   ```
4. Subsequent calls to the same tool skip re-injection, keeping context overhead at zero for repeated invocations.

### Reference Template:
```markdown
---
name: your_tool_name
description: Expert operational protocol and best practices for your_tool_name
keywords: [system, flowork, database, optimization, performance, query, execution, audit, telemetry, isolation, security, pipeline, protocol, verification, linux, terminal, bash, exitcode, storage, buffer]
---

# 🛠️ OPERATIONAL SOP: YOUR_TOOL_NAME

When utilizing `your_tool_name`, you MUST comply with the following procedural standards:

### 1. Usage Guidelines
- Explicitly identify appropriate execution contexts and contraindications.
- Recommend optimal argument configurations for deterministic outcomes.

### 2. Constraints & Safety Rules
- Payload and memory safety boundaries (e.g., maximum batch sizes).
- Timeout handling and non-blocking asynchronous process management.

### 3. Error Recovery & Verification
- Prescribe diagnostic steps when specific error codes are encountered.
- Enforce output verification using standard read tools prior to declaring completion.
```

---

## 6. STEP-BY-STEP TUTORIAL: BUILDING A SOVEREIGN TOOL FROM SCRATCH

In this walkthrough, we build a production tool named **`system_log_watcher`** designed to query systemd journal events with severity filtering.

### Step 1: Create Directory Structure
```bash
mkdir -p /opt/floworkos/tools/system_log_watcher
cd /opt/floworkos/tools/system_log_watcher
```

### Step 2: Create `manifest.json`
```json
{
  "name": "system_log_watcher",
  "description": "Inspect and parse systemd journal and syslog events with keyword filtering.",
  "activation": "conditional",
  "triggers": {
    "keywords": [
      "journalctl",
      "syslog",
      "system error",
      "service failure",
      "kernel panic",
      "dmesg",
      "log inspection"
    ],
    "exclude_keywords": [
      "frontend log",
      "console.log",
      "npm log",
      "browser console"
    ],
    "behavior": {
      "files": ["/var/log/syslog", "/var/log/messages"]
    }
  },
  "skill": "SKILL.md",
  "parametersJsonSchema": {
    "type": "object",
    "properties": {
      "service": {
        "type": "string",
        "description": "Optional specific systemd unit name (e.g., nginx, NetworkManager)."
      },
      "lines": {
        "type": "integer",
        "description": "Number of recent log lines to retrieve. Default is 50."
      },
      "priority": {
        "type": "string",
        "enum": ["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"],
        "description": "Optional systemd priority level."
      }
    },
    "required": []
  }
}
```

### Step 3: Implement `run.py`
```python
#!/usr/bin/env python3
import json
import os
import subprocess
import sys

payload = json.loads(sys.stdin.read() or "{}")
service = payload.get("service") or os.environ.get("SERVICE", "")
lines = int(payload.get("lines") or os.environ.get("LINES", "50"))
priority = payload.get("priority") or os.environ.get("PRIORITY", "")

cmd = ["journalctl", "-n", str(lines), "--no-pager"]
if service:
    cmd += ["-u", service]
if priority:
    cmd += ["-p", priority]

try:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=True)
    print(json.dumps({
        "status": "success",
        "command": " ".join(cmd),
        "lineCount": len(res.stdout.splitlines()),
        "logs": res.stdout.strip(),
    }, indent=2))
    sys.exit(0)
except Exception as exc:
    sys.stderr.write(json.dumps({"status": "error", "error": str(exc)}) + "\n")
    sys.exit(1)
```

Make the script executable:
```bash
chmod +x /opt/floworkos/tools/system_log_watcher/run.py
```

### Step 4: Write `SKILL.md`
```markdown
---
name: system_log_watcher
description: Protocol for system journal investigation, priority triage, and service debugging
keywords: [systemd, journal, syslog, kernel, dmesg, service, debug, triage, error, critical, audit, logs, watcher, inspection, failure, daemon, incident, troubleshooting, triage, flowork]
---

# 📜 OPERATIONAL SOP: SYSTEM LOG WATCHER

When conducting incident triage with `system_log_watcher`:
1. **Priority Filtering:** Always begin with `priority: "err"` to eliminate low-value informational log noise.
2. **Unit Isolation:** When investigating daemon failures, constrain queries with the `service` parameter.
3. **Context Conservation:** Never request more than 200 lines in a single turn to avoid context window degradation.
```

---

## 7. VERIFICATION & EMPIRICAL TESTING PROTOCOL

Before any tool is accepted into production, it must pass three verification stages with `Exit Code 0`:

### Stage 1: Discovery Schema Verification
Verify that the discovery engine initializes cleanly and attaches Intercept Gate fields:
```bash
/opt/floworkos/bin/flowork-tool-discovery --check
/opt/floworkos/bin/flowork-tool-discovery --tools-dir /opt/floworkos/tools | grep -A 10 "system_log_watcher"
```
*Expected Outcome:* `--check` prints `OK (native Rust)` and JSON schema contains `reason`, `keywords`, and `goal`.

### Stage 2: Context Sniffer & Trigger Self-Test Verification
Validate the Pure Rust context sniffer and trigger matching suite:
```bash
/opt/floworkos/bin/flowork-tool-discovery --test-sniffer
```
*Expected Outcome:* Exit Code 0 confirming keyword trigger inclusion and `exclude_keywords` veto logic.

### Stage 3: Live Autonomous Runtime Test
Execute an end-to-end operational query with the MrFlow agent:
```bash
mrflow -p "check system logs for any err priority events using system_log_watcher"
```
*Expected Outcome:*  
- Model supplies `goal`, `reason`, and `keywords` compliant with the Intercept Gate.
- Tool executes autonomously without confirmation modals.
- `<flowork_tool_skill tool="...">` SOP directives are injected once on first execution (`display_text` + `_tool_skill_guidance`).
- Command terminates cleanly with **Exit Code 0**.

---

## 8. QUALITY GATE CHECKLIST

Before deploying any tool to `/opt/floworkos/tools/`, verify that all criteria are met:

- [ ] Tool resides cleanly in `/opt/floworkos/tools/<tool_name>/` (no personal home copies).
- [ ] `manifest.json` contains valid `name`, `description`, `activation`, `triggers`, and `parametersJsonSchema`.
- [ ] Exclusion rules (`exclude_keywords`) are configured to prevent false-positive activations.
- [ ] Executable runner (`run` ELF, `run.py`, or `run.sh`) includes valid shebang/ELF header and `chmod +x`.
- [ ] Runner handles failures with descriptive `stderr` and explicit non-zero exit status (`1`).
- [ ] Runner returns deterministic output with exit code `0` on success.
- [ ] `SKILL.md` (if present) includes YAML frontmatter with exactly 20 English keywords.
- [ ] Sovereign Connector at port 9099 remains **100% UNTOUCHED** throughout development.
- [ ] Empirical terminal verification yields **Exit Code 0**.

---

## 9. DYNAMIC TOOL FOUNDRY (`tool_foundry`)

Flowork OS includes an autonomous **Dynamic Tool Foundry** (`/opt/floworkos/tools/tool_foundry/run.py`, which delegates stdin cleanly to `/opt/floworkos/tools/fl_tool_foundry.py`).
The foundry provides autonomous self-synthesis of tools with a strict 4-stage verification gate:
1. **Schema & Naming Linting:** lowercase snake_case validation, TDK parameter schema.
2. **Isolated Staging:** `/tmp/foundry/<tool_name>/` sandboxing and syntax dry-run.
3. **Empirical Execution Gate:** stdin test payload injection with mandatory Exit Code 0 and valid stdout.
4. **Atomic Promotion & Discovery:** Promotes to `/opt/floworkos/tools/<tool_name>/` and verifies registration via `/opt/floworkos/bin/flowork-tool-discovery`. Automated rollback ensures zero workspace pollution upon any failure.

