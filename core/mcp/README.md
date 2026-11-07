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

## 2. How MCP Works Under the Hood ("Cara Kerja MCP")

The Flowork OS MCP pipeline consists of four automated stages: discovery, configuration synchronization, process lifecycle management, and dynamic tool routing.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. DISCOVERY & REGISTRATION (/opt/floworkos/mcp/loader.js)             │
│ Scans subdirectories in /opt/floworkos/mcp/ for config.json files.     │
│ Assembles valid servers into an aggregate mcpServers definition map.   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Syncs to ~/.flowork/settings.json]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. LIFECYCLE INITIALIZATION (MrFlow Bootstrap)                         │
│ MrFlow spawns each registered MCP server as a dedicated subprocess:   │
│ exec: /opt/floworkos/mcp/<name>/run.sh                                 │
│ Performs JSON-RPC 2.0 Handshake over stdio:                           │
│ -> initialize request ──> initialize response ──> initialized notify   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Queries tools/list via JSON-RPC]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. DYNAMIC SLIDING WINDOW FILTERING (router.js)                        │
│ Discovered MCP tools (e.g. mcp_browser_*) are ingested by router.js.   │
│ Formula 5-3-3 sliding router suppresses inactive MCP tools to 0 tokens │
│ and only injects matching tool definitions when active keywords match. │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [User request requires action]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. DETERMINISTIC TOOL INVOCATION (tools/call)                          │
│ Orchestrator sends tools/call with parameters over stdio to subprocess.│
│ MCP server executes operation, emitting debug telemetry to stderr.     │
│ Formatted JSON-RPC response returns on stdout with Exit Code 0.        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mandatory MCP Authoring Standards ("Standar MCP")

Every MCP server deployed to `/opt/floworkos/mcp/` MUST conform to the canonical Flowork OS specification:

### 1. Dedicated Isolated Directory
Each server must reside in its own named directory under `/opt/floworkos/mcp/<server_name>/`. No flat, disorganized files are allowed.

```text
/opt/floworkos/mcp/<server_name>/
├── config.json         <-- Mandatory standard MCP server declaration
├── run.sh              <-- Mandatory executable launcher script (chmod +x)
└── [server_assets]     <-- Node.js bundles, compiled Rust binaries, Python virtualenvs
```

### 2. Standard Schema: `config.json`
The `config.json` file is parsed by `loader.js` to register the server with the orchestrator:

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

> **Architecture Decoupling Note:** In Flowork OS, browser automation tools are fully integrated as **native decoupled tools** under `/opt/floworkos/tools/browser_*` with dedicated backend at `/opt/floworkos/tools/browser_backend/`. Browser automation is intentionally **not** registered as an active MCP server in `/opt/floworkos/mcp/` to eliminate double-registration, avoid duplicate tools (`mcp_browser_*` vs `browser_*`), and ensure optimal token conservation.

#### Field Specifications:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | String | **YES** | Unique identifier (`^[a-z0-9_-]+$`). Used as the prefix for registered tools. |
| `description` | String | **YES** | High-level summary of the server's purpose and scope. |
| `command` | String | **YES** | Absolute path to the launcher executable or wrapper script (`run.sh`). |
| `args` | Array | Optional | CLI arguments passed to the launcher command. |
| `env` | Object | Optional | Dedicated environment variables injected into the subprocess. |

### 3. Strict Standard I/O Separation (Doktrin Isolasi stdio)
This is the single most critical invariant for MCP servers:
- **`stdout` (STRICT PROTOCOL ONLY):** Only valid JSON-RPC 2.0 messages (newline-delimited) may be emitted on stdout. Writing debug text, banner headers, or console logs to stdout **corrupts the protocol parser and causes fatal client crashes**.
- **`stderr` (LOGGING & TELEMETRY):** All debug logs, operational diagnostics, connection warnings, and telemetry must be routed exclusively to stderr.

### 4. Zero Process Zombies & Clean Termination
All MCP servers must register proper POSIX signal handlers (`SIGINT`, `SIGTERM`, `SIGHUP`). When the client orchestrator exits or terminates the stdio pipe, the MCP server must cleanly kill any child processes (e.g. browser instances, database connections, background workers) and exit with code 0.

### 5. Strict English Doctrine (Doktrin #9)
All tool names, descriptions, input schemas, property explanations, and error messages MUST be written in strict, professional technical English.

---

## 4. Step-by-Step Tutorial: Authoring a Sovereign MCP Server

Follow this verified protocol to author a new MCP server:

### Step 1: Create the Server Directory
```bash
SERVER_NAME="database"
mkdir -p /opt/floworkos/mcp/${SERVER_NAME}
```

### Step 2: Implement the Server Logic (`server.js` or Compiled Binary)
For Node.js servers, implement the standard MCP protocol handler:

```javascript
#!/usr/bin/env node
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});

function sendResponse(id, result, error) {
    const msg = { jsonrpc: "2.0", id };
    if (error) msg.error = error;
    else msg.result = result;
    process.stdout.write(JSON.stringify(msg) + "\n");
}

rl.on('line', (line) => {
    try {
        const req = JSON.parse(line);
        if (req.method === 'initialize') {
            sendResponse(req.id, {
                protocolVersion: "2024-11-05",
                capabilities: { tools: {} },
                serverInfo: { name: "flowork-database", version: "1.0.0" }
            });
        } else if (req.method === 'tools/list') {
            sendResponse(req.id, {
                tools: [{
                    name: "query_database",
                    description: "Execute a read-only SQL query against the system database.",
                    inputSchema: {
                        type: "object",
                        properties: {
                            query: { type: "string", description: "The SQL statement to execute." }
                        },
                        required: ["query"]
                    }
                }]
            });
        } else if (req.method === 'tools/call') {
            // Log diagnostics to stderr only!
            process.stderr.write(`[MCP] Executing query: ${req.params?.arguments?.query}\n`);
            sendResponse(req.id, {
                content: [{ type: "text", text: JSON.stringify([{ id: 1, status: "healthy" }]) }]
            });
        }
    } catch (err) {
        process.stderr.write(`[MCP ERROR] ${err.message}\n`);
    }
});
```

### Step 3: Author the Executable Launcher (`run.sh`)
Create `/opt/floworkos/mcp/database/run.sh`:

```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec node "$SCRIPT_DIR/server.js" "$@"
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
Verify that `loader.js` registers the new server with Exit Code 0:
```bash
node /opt/floworkos/mcp/loader.js
```
The output will output a clean JSON map containing `"database"` alongside existing servers.

---

## 5. Quality Gate & Acceptance Checklist

Before any MCP server is authorized in `/opt/floworkos/mcp/`:

- [ ] **Gate 1 (Isolation):** Resides in its own dedicated directory at `/opt/floworkos/mcp/<server_name>/`.
- [ ] **Gate 2 (Configuration):** `config.json` exists, is valid JSON, and declares `name`, `description`, and `command`.
- [ ] **Gate 3 (Launcher Permissions):** The `command` executable (`run.sh`) has executable permissions (`chmod +x`).
- [ ] **Gate 4 (Stdio Protocol Discipline):** Emits strictly JSON-RPC on `stdout`; all logging routed to `stderr`.
- [ ] **Gate 5 (Language):** All tool schemas and descriptions written in strict technical English.
- [ ] **Gate 6 (Zero Symlinks):** All files are physical files on disk with zero symlinks.
- [ ] **Gate 7 (Auto-Discovery):** `/opt/floworkos/mcp/loader.js` discovers the server with **Exit Code 0**.
