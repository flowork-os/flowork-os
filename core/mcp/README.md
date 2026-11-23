# 🔌 FLOWORK OS — MODEL CONTEXT PROTOCOL (MCP) SUBSYSTEM & AUTHORING GUIDE

> **AUTHORITY:** Flowork Architecture Board & Dr. Flow  
> **TERRITORY:** `/opt/floworkos/mcp/`  
> **CLASSIFICATION:** Sovereign System Architecture Standard (Strict English)

---

## 1. Executive Philosophy: What is MCP in Flowork OS?

The **Model Context Protocol (MCP)** is an open, standardized protocol (JSON-RPC 2.0 over standard I/O or SSE) designed to connect AI agent orchestrators to external tools, system daemons, hardware interfaces, and rich data sources.

In Flowork OS, MCP servers operate as **Decoupled External Service Providers**. Unlike native atomic tools (`/opt/floworkos/tools/`), an MCP server runs as an independent external process that exposes a dynamic cluster of tools, resources, and contextual feeds through a unified JSON-RPC interface.

### Non-Dualism of Runtime Capabilities:
- **NATIVE TOOLS (`/opt/floworkos/tools/<tool_name>/`):** Atomic, single-purpose CLI execution instruments (`run_shell_command`, `read_file`, `write_file`).
- **MCP SERVERS (`/opt/floworkos/mcp/<server_name>/`):** Complex subsystem integrations and persistent service providers running in their own isolated process spaces (e.g. Chrome DevTools Protocol automation, database bridges, language servers).
- **SKILLS (`/opt/floworkos/skills/<skill_name>/`):** Procedural SOPs and playbooks with exactly 20 semantic keywords.
- **PROMPTS (`/opt/floworkos/system/system_promp/promps/`):** Core conscience, behavioral constraints, and dynamic passive triggers.
- **AGENTS (`/opt/floworkos/agents/<agent_name>.md`):** Delegated autonomous workers running in isolated sub-turn sandboxes.

---

## 2. How MCP Works Under the Hood

The Flowork OS MCP pipeline (`mrflow-rs/src/mcp/mod.rs`) consists of four automated stages: configuration discovery, transport & JSON-RPC 2.0 initialization, schema sanitization + Intercept Gate injection, and pre-dispatch execution.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. DISCOVERY & PRECEDENCE (McpManager::discover_configs)               │
│ Scans sources in override precedence order:                            │
│  1) /opt/floworkos/mcp/*/{config.json,manifest.json}                   │
│  2) ~/.flowork/mcp/*/{config.json,manifest.json}                       │
│  3) <cwd>/.mcp.json, <cwd>/.flowork/mcp_config.json, .flowork/settings │
│  4) ~/.flowork/settings.json (mcpServers & disabledMcpServers filters) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Expands ${VAR} & ${VAR:-default}]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. LIFECYCLE INITIALIZATION (MrFlow Native MCP Client)                 │
│ Connects over 3 transports: Stdio subprocess, StreamableHttp, or SSE.  │
│ Performs JSON-RPC 2.0 Handshake:                                       │
│ -> initialize request ──> initialize response ──> initialized notify   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Queries tools/list, resources, prompts]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. FILTERING, SCHEMA SANITIZATION & INTERCEPT GATE                     │
│ Registers qualified tools (`mcp_<server>_<tool>`), applies             │
│ `includeTools`/`excludeTools`, runs `sanitize_gemini_schema()`         │
│ (`inference/mod.rs`), and attaches `reason`/`keywords`/`goal` fields.  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [User request requires action]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. DETERMINISTIC TOOL INVOCATION (McpManager::call_tool)               │
│ Strips `reason`/`keywords`/`goal` Intercept Gate telemetry before      │
│ dispatching `tools/call` upstream; routes stdout JSON-RPC cleanly.     │
└────────────────────────────────────────────────────────────────────────┘
```

### Live Configured System Servers (`/opt/floworkos/mcp/`)
Currently active MCP server definitions discovered on boot:
- **`downflow-mcp`** (`/opt/floworkos/mcp/downflow/config.json`) $\rightarrow$ `/usr/local/bin/downflow-mcp`
- **`earshot`** (`/opt/floworkos/mcp/earshot/config.json`) $\rightarrow$ `/usr/bin/python3 /opt/floworkos/mcp/earshot/earshot_server.py`

Manage registrations anytime via `mrflow mcp {add|remove|list|enable|disable}`.

---

## 3. Mandatory MCP Authoring Standards

Every MCP server deployed to `/opt/floworkos/mcp/` MUST conform to the canonical Flowork OS specification:

### 1. Dedicated Isolated Directory
Each server must reside in its own named directory under `/opt/floworkos/mcp/<server_name>/`. No flat, disorganized files are allowed.

```text
/opt/floworkos/mcp/<server_name>/
├── config.json         <-- Standard MCP server declaration (or manifest.json)
├── run.sh              <-- Executable launcher script (chmod +x) or server binary/script
└── [server_assets]     <-- Compiled Rust binaries or Python modules
```

### 2. Standard Schema: `config.json` (Stdio, StreamableHttp, SSE)
Parsed by `mrflow-rs/src/mcp/mod.rs` (`scan_mcp_folder_dir`) to register the server with the orchestrator:

```json
{
  "name": "database",
  "description": "Flowork OS Sovereign Database Integration MCP Server",
  "command": "/opt/floworkos/mcp/database/run.sh",
  "args": [
    "--port=5432",
    "--read-only"
  ],
  "env": {
    "FLOWORK_TRUST_WORKSPACE": "true"
  }
}
```

> **Architecture Decoupling Note:** In Flowork OS, browser automation tools (`browser_*`) reside as **native decoupled manifest tools** under `/opt/floworkos/tools/` backed by Pure Rust binaries rather than an active `/opt/floworkos/mcp/` server, avoiding duplicate `mcp_browser_*` declarations and conserving context tokens.

#### Field Specifications:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | String | Optional (folder name fallback) | Unique identifier (`^[a-z0-9_-]+$`). Prefixes registered tools as `mcp_<name>_<tool>`. |
| `description` | String | Recommended | High-level summary of the server's purpose and scope. |
| `command` | String | Stdio transport | Absolute path to executable binary or wrapper script. |
| `args` | Array | Optional | CLI arguments passed to `command` (`${workspaceFolder}` / `${VAR:-default}` expanded). |
| `env` | Object | Optional | Environment variables injected into subprocess or reused by URL/header expansion. |
| `cwd` | String | Optional | Working directory for Stdio subprocess (defaults to the MCP folder path). |
| `url` / `httpUrl` | String | HTTP/SSE transport | Remote endpoint URL (`httpUrl` or `url` selects `StreamableHttp`; `url` ending in `/sse` or `"type": "sse"` selects `SSE`). |
| `type` | String | Optional | Explicit transport selector: `"stdio"`, `"http"`/`"streamable-http"`, or `"sse"`. |
| `headers` | Object | Optional | HTTP headers sent on `StreamableHttp` / `SSE` requests. |
| `timeout` | Integer (ms) | Optional | Request timeout clamped to `2000..300000` ms (default `60000` ms). |
| `trust` | Boolean | Optional | Marks server as trusted when evaluating approval prompts. |
| `includeTools` / `excludeTools` | Array | Optional | Glob-filtered tool allowlist/blocklist (`prefix*` supported). |
| `disabled` | Boolean | Optional | Disables server loading when `true`. |

### 3. Strict Standard I/O Separation (Stdio Isolation)
For `Stdio` MCP servers, standard stream separation is non-negotiable:
- **`stdout` (STRICT PROTOCOL ONLY):** Only valid JSON-RPC 2.0 messages (newline-delimited) may be emitted on stdout. Writing debug text, banner headers, or console logs to stdout **corrupts the protocol parser and causes fatal client crashes**.
- **`stderr` (LOGGING & TELEMETRY):** All debug logs, operational diagnostics, connection warnings, and telemetry must be routed exclusively to stderr.

### 4. Zero Process Zombies & Clean Termination
All MCP servers must register proper POSIX signal handlers (`SIGINT`, `SIGTERM`, `SIGHUP`). When the client orchestrator exits or terminates the stdio pipe, the MCP server must cleanly kill any child processes (e.g. browser instances, database connections, background workers) and exit with code 0.

### 5. Strict English Doctrine
All tool names, descriptions, input schemas, property explanations, and error messages MUST be written in strict, professional technical English.

---

## 4. Step-by-Step Tutorial: Authoring a Sovereign MCP Server

Follow this verified protocol to author a new MCP server:

### Step 1: Create the Server Directory
```bash
SERVER_NAME="database"
mkdir -p /opt/floworkos/mcp/${SERVER_NAME}
```

### Step 2: Implement the Server Logic (Compiled Rust Binary or Python Stdlib `server.py`)
For lightweight zero-dependency MCP servers, use a compiled Rust ELF or pure Python 3 stdlib handler:

```python
#!/usr/bin/env python3
import json
import sys


def send_response(msg_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        method = req.get("method")
        msg_id = req.get("id")
        if method == "initialize":
            send_response(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "flowork-database", "version": "1.0.0"},
            })
        elif method == "tools/list":
            send_response(msg_id, {
                "tools": [{
                    "name": "query_database",
                    "description": "Execute a read-only SQL query against the system database.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The SQL statement to execute."}
                        },
                        "required": ["query"],
                    },
                }]
            })
        elif method == "tools/call":
            args = req.get("params", {}).get("arguments", {})
            sys.stderr.write(f"[MCP] Executing query: {args.get('query')}\n")
            sys.stderr.flush()
            send_response(msg_id, {
                "content": [{"type": "text", "text": json.dumps([{"id": 1, "status": "healthy"}])}]
            })
    except Exception as exc:
        sys.stderr.write(f"[MCP ERROR] {exc}\n")
        sys.stderr.flush()
```

### Step 3: Author the Executable Launcher (`run.sh`)
Create `/opt/floworkos/mcp/database/run.sh`:

```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/server.py" "$@"
```
Make the script executable:
```bash
chmod +x /opt/floworkos/mcp/database/run.sh
```

### Step 4: Author the Manifest (`config.json`)
Create `/opt/floworkos/mcp/database/config.json`:

```json
{
  "name": "database",
  "description": "Flowork OS Sovereign Database Integration MCP Server",
  "command": "/opt/floworkos/mcp/database/run.sh",
  "args": [],
  "env": {}
}
```

### Step 5: Test Discovery & Runtime Verification
Verify that Mr. Flow discovers the new MCP server with Exit Code 0:
```bash
mrflow mcp list
```
The command validates handshake & tool discovery for `"database"` alongside existing servers.

---

## 5. Quality Gate & Acceptance Checklist

Before any MCP server is authorized in `/opt/floworkos/mcp/`:

- [ ] **Gate 1 (Isolation):** Resides in its own dedicated directory at `/opt/floworkos/mcp/<server_name>/`.
- [ ] **Gate 2 (Configuration):** `config.json` exists, is valid JSON, and declares `name`, `description`, and `command`.
- [ ] **Gate 3 (Launcher Permissions):** The `command` executable (`run.sh`) has executable permissions (`chmod +x`).
- [ ] **Gate 4 (Stdio Protocol Discipline):** Emits strictly JSON-RPC on `stdout`; all logging routed to `stderr`.
- [ ] **Gate 5 (Language):** All tool schemas and descriptions written in strict technical English.
- [ ] **Gate 6 (Zero Symlinks):** All files are physical files on disk with zero symlinks.
- [ ] **Gate 7 (Auto-Discovery):** `mrflow mcp list` discovers and connects the server cleanly with **Exit Code 0**.
