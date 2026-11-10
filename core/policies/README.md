# ⚖️ FLOWORK OS — SOVEREIGN POLICY SUBSYSTEM & GOVERNANCE GUIDE

> **AUTHORITY:** Flowork Architecture Board & Dr. Flow  
> **TERRITORY:** `/opt/floworkos/policies/`  
> **CLASSIFICATION:** Sovereign System Architecture Standard (Strict English)

---

## 1. Executive Philosophy: What is Policy in Flowork OS?

In Flowork OS, **Policies** serve as the **Constitutional Law & Security Enforcement Engine** of the operating system. 

While the model's persona and instructions (Prompts) dictate what the agent *should* do, and operational playbooks (Skills) dictate *how* to accomplish tasks, **Policies** are the immutable, system-level security gates that dictate what actions the agent is **permitted** to perform.

### Non-Dualism of Runtime Capabilities:
- **TOOL (`/opt/floworkos/tools/<tool_name>/`):** The atomic instrument of physical action (Hands & Scalpels).
- **SKILL (`/opt/floworkos/skills/<skill_name>/`):** The operational playbook, multi-step SOP, and domain heuristics (Procedural Brain Lobe).
- **PROMPT (`/opt/floworkos/system/system_promp/promps/`):** The living conscience, behavioral constraints, and dynamic environmental instincts (Soul & Reflexes).
- **AGENT (`/opt/floworkos/agents/<agent_name>.md`):** The delegated autonomous worker running in an isolated sub-turn sandbox.
- **POLICY (`/opt/floworkos/policies/*.toml`):** The system-level legal constitution and security governance gate. Every tool call is intercepted by the `PolicyEngine` before physical execution.

---

## 2. How Policies Work Under the Hood ("Cara Kerja Policy")

The policy enforcement pipeline operates on strict pre-execution interception, dynamic filesystem scanning, and a deterministic 5-tier hierarchical priority system.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. TOOL CALL ATTEMPT (Agent requests tool execution)                   │
│ e.g. Agent invokes run_shell_command(command="rm -rf /")               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Intercepted before execution]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. DYNAMIC POLICY DISCOVERY & EVALUATION (PolicyEngine)                │
│ PolicyEngine evaluates all loaded TOML rules matching active Approval  │
│ Mode (e.g. "sovereign"), toolName, arguments, and execution context.   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Resolves highest priority rule]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. THE THREE DETERMINISTIC DECISIONS                                   │
│                                                                        │
│ [ALLOW]   ──> Tool executes immediately without friction.             │
│ [ASK_USER]──> Execution paused; interactive prompt presented to user.  │
│ [DENY]    ──> Execution permanently blocked; rejection error returned. │
└────────────────────────────────────────────────────────────────────────┘
```

### The Three Policy Decisions:
1. **`allow`:** The tool call is authorized to proceed immediately without human confirmation. In `sovereign` mode, non-destructive tools and sovereign operations default to `allow` to ensure autonomous execution.
2. **`ask_user`:** The tool call is paused, and an interactive confirmation prompt is presented to the user. Tools requiring human judgment (e.g. `ask_user`) are hardcoded to `ask_user`.
3. **`deny`:** The tool call is strictly rejected by the operating system. Attempting to execute prohibited commands (e.g. entering plan mode in sovereign mode, or destructive system deletions) produces an immediate rejection error.

---

## 3. The 5-Tier Hierarchical Priority System

To prevent conflicting rules and guarantee that system security cannot be undermined, Flowork OS enforces a **strict 5-Tier Priority Hierarchy**. 

Rules in higher tiers **always defeat** rules in lower tiers, regardless of individual rule priorities:

| Tier | Name | Filesystem Location | Scope & Authority | Effective Priority Formula |
| :---: | :--- | :--- | :--- | :--- |
| **5** | **Admin / System Tier** | `/etc/flowork/policies/` | Absolute system root security. Cannot be overridden by users or workspaces. | `5.000 + (priority / 1000)` |
| **4** | **User Tier** | `~/.flowork/policies/` or `policyPaths` | Personal preferences and persistent security configurations across all projects. | `4.000 + (priority / 1000)` |
| **3** | **Workspace Tier** | `<project>/.flowork/policies/` | Repository-specific rules declared for a specific project codebase. | `3.000 + (priority / 1000)` |
| **2** | **Extension Tier** | Contributed by plugins/extensions | Third-party integrations and supplemental tools. | `2.000 + (priority / 1000)` |
| **1** | **Default / OS Tier** | `/opt/floworkos/policies/` | Core Flowork OS baseline policies (`sovereign.toml`, `write.toml`, etc.). | `1.000 + (priority / 1000)` |

### How Priority Resolution Works:
Within each TOML rule, you specify an integer `priority` from `1` to `999`. 
The engine calculates:
$$\text{Effective Priority} = \text{Tier Number} + \frac{\text{priority}}{1000}$$

* **Example:**
  - A default OS rule in `/opt/floworkos/policies/` with `priority = 998` has an effective score of **`1.998`**.
  - A user rule in `~/.flowork/policies/` with `priority = 10` has an effective score of **`4.010`**.
  - **Result:** The user rule (`4.010`) wins over the default rule (`1.998`), while an admin rule in `/etc/flowork/policies/` (`5.xxx`) will always win over both.

---

## 4. Zero-Recompile Architecture: Can We Add Policies Without Rebuilding the CLI Binary?

> **YES, ABSOLUTELY 100%! THE SUBSYSTEM IS EXCLUSIVELY DESIGNED FOR THIS.**

Policies are **NEVER hardcoded inside the compiled CLI binary**. 

When MrFlow starts:
1. `PolicyEngine` dynamically scans all configured policy directories (`fs.readdir`).
2. Every file ending in `.toml` is parsed on-the-fly using standard TOML schema validation.
3. Rules are sorted into memory by effective priority and evaluated in real time.

**Operational Implication:**
- If you build or compile the MrFlow CLI into a standalone ELF binary, **you never need to recompile the binary to add, change, or revoke policies**.
- You simply drop a new `.toml` file into `/opt/floworkos/policies/`, `~/.flowork/policies/`, or your project's `.flowork/policies/`.
- The CLI binary will instantly discover, parse, and enforce the new rules on its very next turn!

---

## 5. Standard TOML Policy Specification ("Standar Policy")

Every policy file must be valid TOML containing one or more `[[rule]]` blocks.

### Complete Rule Schema:

```toml
[[rule]]
name = "Protect System Root Directories"
toolName = "run_shell_command"
decision = "deny"
priority = 999
modes = ["sovereign", "default"]
argsPattern = "rm\\s+-rf\\s+/(boot|etc|usr|var|home|opt)?"
interactive = false
allowRedirection = false
```

### Schema Field Definitions:

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | String | Optional | Descriptive human-readable label for debugging and audit logs. |
| `toolName` | String or Array | **YES** | Exact tool identifier (e.g. `"run_shell_command"`), array of tool names (`["read_file", "write_file"]`), or wildcard `"*"` for all tools. |
| `decision` | Enum | **YES** | One of: `"allow"`, `"ask_user"`, or `"deny"`. |
| `priority` | Integer | **YES** | Priority integer between `1` and `999` (higher wins within the same tier). |
| `modes` | Array | Optional | Whitelist of approval modes where this rule applies: `["sovereign"]`, `["default"]`, `["autoEdit"]`, `["plan"]`. If omitted, applies across all modes. |
| `argsPattern` | String (Regex) | Optional | Regular expression tested against command-line arguments or parameters. If matched, the rule applies. |
| `interactive` | Boolean | Optional | Restricts rule to interactive sessions (`true`) or non-interactive headless sessions (`false`). |
| `allowRedirection` | Boolean | Optional | If `false`, shell piping/redirection (`>`, `>>`, `|`) triggers a downgrade check. Set `true` for sovereign builds. |
| `subagent` | Boolean | Optional | Restricts rule to delegated subagents (`true`) or main orchestrator sessions (`false`). |

---

## 6. Production Policies in `/opt/floworkos/policies/`

The baseline OS policies governing Flowork OS sovereignty include:

| Policy File | Role & Invariants |
| :--- | :--- |
| `sovereign.toml` | **The Constitution of Sovereign Mode.** Grants `allow` to wildcard tools (`*`) with `priority = 998`, locks `ask_user` tool to interactive confirmation (`priority = 999`), and denies plan mode switching. |
| `agents.toml` | Authorizes `invoke_agent` across default, autoEdit, and sovereign modes (`priority = 50`). |
| `write.toml` | Defines default behavior for filesystem modification tools (`write_file`, `replace`). |
| `read-only.toml` | Grants baseline allow to non-destructive inspection tools (`read_file`, `list_directory`, `grep_search`). |
| `sandbox-default.toml` | Establishes workspace filesystem boundaries and path traversal restrictions. |

---

## 7. Step-by-Step Tutorial: Creating a Custom Policy

### Tutorial A: Creating an OS-Wide Root Protection Policy
To permanently prohibit destructive root deletion across all sessions on Flowork OS:

1. Create `/opt/floworkos/policies/guard_system.toml`:
```toml
# ==============================================================================
# Flowork OS — System Directory Guard Policy
# ==============================================================================

[[rule]]
name = "Deny Root Deletion"
toolName = "run_shell_command"
decision = "deny"
priority = 999
modes = ["sovereign", "default", "autoEdit"]
argsPattern = "rm\\s+-(r|f|rf|fr)\\s+(/|/boot|/etc|/opt|/usr|/var)"

[[rule]]
name = "Deny Raw Device Formatting"
toolName = "run_shell_command"
decision = "deny"
priority = 999
modes = ["sovereign", "default"]
argsPattern = "mkfs(\\.[a-z0-9]+)?\\s+/dev/"
```
2. Save the file.
3. Test immediately with `mrflow`. The rules are live with **Exit Code 0**!

---

### Tutorial B: Creating a Repository-Level Policy
To grant specialized automated permissions for a specific software project without altering global settings:

1. In the root of your project, create `.flowork/policies/project_build.toml`:
```toml
# Project-specific policy (Workspace Tier 3)
[[rule]]
name = "Allow Cargo & Test Suite Autonomously"
toolName = "run_shell_command"
decision = "allow"
priority = 800
modes = ["sovereign", "default"]
argsPattern = "^cargo\\s+(test|build|clippy|check)"
allowRedirection = true
```
2. When MrFlow is launched inside this project directory, Workspace Tier 3 rules activate automatically.

---

## 8. Quality Gate & Acceptance Checklist

Before any policy file is deployed to `/opt/floworkos/policies/`:

- [ ] **Gate 1 (Territory):** Policy resides strictly as a physical `.toml` file under `/opt/floworkos/policies/`.
- [ ] **Gate 2 (TOML Syntax):** Parses cleanly with zero syntax errors.
- [ ] **Gate 3 (Enum Validation):** `modes` only declares valid enums: `"sovereign"`, `"default"`, `"autoEdit"`, `"plan"`.
- [ ] **Gate 4 (Decision Values):** `decision` must be strictly `"allow"`, `"ask_user"`, or `"deny"`.
- [ ] **Gate 5 (Language):** All comments and `name` strings written in strict technical English.
- [ ] **Gate 6 (Zero Symlinks):** No symlinks anywhere in policy directories.
- [ ] **Gate 7 (Empirical Runtime Verification):** Tested with `mrflow` returning **Exit Code 0** with zero Zod validation warnings.
