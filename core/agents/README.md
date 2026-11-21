# 🤖 FLOWORK OS — DELEGATED SUBAGENTS SUBSYSTEM & REGISTRY

> **AUTHORITY:** Flowork Architecture Board & Dr. Flow  
> **TERRITORY:** `/opt/floworkos/agents/`  
> **CLASSIFICATION:** Sovereign System Architecture Standard (Strict English)

---

## 1. Executive Philosophy: Subagents in Flowork OS

In Flowork OS, **Subagents** are specialized, delegated autonomous workers operating in isolated context sandboxes.
The primary agent orchestrator (**Mr. Flow**) delegates computationally heavy, repetitive, or research-intensive operations to subagents to preserve context window bandwidth, eliminate context pollution, and enforce strict principle-of-least-privilege tool execution.

### Architectural Invariants:
1. **Isolated Context Sandbox:** Subagents execute in dedicated multi-turn context loops without polluting the primary orchestrator's history or degrading its reasoning capacity.
2. **Dynamic Profile Discovery & Synthesis:** Subagents are loaded dynamically from `/opt/floworkos/agents/` and user directories (`~/.flowork/agents/`) via YAML frontmatter markdown profiles, and can be synthesized at runtime via `define_subagent`.
3. **Workspace Isolation Tiers:** Subagents operate under explicit workspace boundaries (`inherit`, `branch`, or `share` via git worktrees).
4. **Reactive Wakeup (Zero Polling):** The parent orchestrator never polls in busy loops. The engine automatically resumes parent execution upon subagent message delivery or task completion.
5. **Process-Tree Safety:** `ProcessRegistry` guarantees clean process-tree management, eliminating zombie processes and preventing self-PID termination.

---

## 2. Core Built-in Subagents

Flowork OS ships with standard built-in system operatives natively recognized by `mrflow-rs`:

### 1. `self` (Parent Configuration Clone)
- **Role:** Clones the calling agent's full configuration, active model, and tool suite into an isolated conversation thread.
- **Use Case:** Executing multi-step side tasks that require full tool capabilities without cluttering parent conversation history.
- **Allowed Tools:** Inherits all parent tools (subject to subagent depth guards).

### 2. `research` (Read-Only Codebase & Web Explorer)
- **Role:** Deep codebase exploration, web searches, documentation extraction, and static file inspection.
- **Use Case:** Broad codebase surveys and documentation queries that generate large outputs.
- **Allowed Tools:** `read_file`, `read_many_files`, `list_directory`, `glob`, `grep_search`, `search_web`, `read_url_content`, `complete_task`.
- **Execution Mode:** Read-only, zero side-effects.

### 3. `codebase_investigator`
- **Role:** Deep codebase exploration, dependency tracing, symbol verification, and architectural discovery.
- **Allowed Tools:** `read_file`, `read_many_files`, `list_directory`, `glob`, `grep_search`, `complete_task`.
- **Execution Mode:** Read-only AST analysis.

### 4. `cli_help`
- **Role:** Flowork OS runtime assistance, CLI usage, slash commands, shell troubleshooting, and system documentation retrieval.
- **Allowed Tools:** `read_file`, `list_directory`, `glob`, `grep_search`, `complete_task`.
- **Execution Mode:** Read-only guidance and command formulation.

### 5. `kernel_sentinel`
- **Role:** Low-level Linux 7.3.0 Eust Kernel telemetry, ring-0 diagnostics, `dmesg` panic triage, Landlock LSM audit, and PSI hardware surveillance.
- **Allowed Tools:** `run_shell_command`, `read_file`, `glob`, `grep_search`, `list_directory`, `complete_task`.
- **Execution Mode:** Sovereign ring-0 read-only diagnostics and non-destructive health verification.

---

## 3. Subagent Swarm Invocation (`invoke_subagent`)

The orchestrator spawns subagents concurrently using `invoke_subagent`:

```json
{
  "Subagents": [
    {
      "TypeName": "research",
      "Role": "API Latency Auditor",
      "Prompt": "Investigate upstream Google CloudCode TTFB and report exact latency metrics.",
      "Model": "inherit",
      "Workspace": "inherit"
    },
    {
      "TypeName": "self",
      "Role": "Unit Test Specialist",
      "Prompt": "Run cargo test on mrflow-rs and report any failing assertions.",
      "Model": "inherit",
      "Workspace": "inherit"
    }
  ],
  "toolAction": "Spawning audit swarm",
  "toolSummary": "Audit swarm"
}
```

### Workspace Isolation Modes:
- **`inherit` (default):** Shares the current working directory with the parent process.
- **`branch`:** Creates a new isolated directory branched or cloned from the parent workspace.
- **`share`:** Creates a new workspace sharing the parent's underlying git repository via `git worktree`, allowing independent branching without duplicating storage.

---

## 4. Dynamic Subagent Definition (`define_subagent`)

Subagent profiles can be synthesized on-the-fly via the `define_subagent` tool:

```json
{
  "name": "perf_auditor",
  "description": "High performance Rust auditor",
  "system_prompt": "Audit hot loops and lock contentions strictly.",
  "enable_write_tools": true,
  "enable_mcp_tools": false,
  "enable_subagent_tools": false,
  "toolAction": "Defining perf auditor",
  "toolSummary": "Agent definition"
}
```

### Profile Specification (`<name>.md`):
When defined, the engine performs a write-probe test and persists the agent specification to `~/.flowork/agents/<name>.md` or `/opt/floworkos/agents/<name>.md`:

```markdown
---
name: perf_auditor
description: High performance Rust auditor
tools:
  - read_file
  - view_file
  - read_many_files
  - list_directory
  - glob
  - grep_search
  - complete_task
  - write_file
  - write_to_file
  - replace
  - replace_file_content
  - run_shell_command
  - run_command
model: inherit
---
Audit hot loops and lock contentions strictly.
```

---

## 5. Subagent Lifecycle Supervision (`manage_subagents`)

The primary orchestrator inspects and manages running subagents via `manage_subagents`:

### Actions:
- **`list`:** Returns JSON array of active direct subagents:
  ```json
  [
    {
      "conversationId": "subagent-8b081e22-5a74-494c-acfc-8395cbcfe535",
      "role": "API Latency Auditor",
      "type": "research",
      "transcript": "file:///opt/floworkos/history/chats/subagent-8b081e22.jsonl",
      "state": "running",
      "stateDetail": "Executing web fetch benchmark"
    }
  ]
  ```
- **`kill`:** Terminates specific subagents identified by `ConversationIds`.
- **`kill_all`:** Terminates all currently active subagents cleanly.

### Safety Invariant (Self-PID Protection):
`ProcessRegistry::kill_all_active` validates `info.pid != std::process::id()` before sending `libc::kill` signals, ensuring subagent management never terminates the primary agent engine.

---

## 6. Inter-Agent Communication (`send_message`)

Parent and subagents communicate via `send_message`:
- **Parent to Subagent:** Sends follow-up instructions or checks on status using `conversationId`.
- **Subagent to Parent:** Emits structured task outcomes upon completion.
- **Reactive Wakeup:** When a subagent emits a response, the parent is immediately awakened by the event bus without polling.

---

*Flowork OS Sovereign Subagent Subsystem — Built for Scalable, Safe, Multi-Agent Concurrency.*
