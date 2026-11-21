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

## 2. How Policies Work Under the Hood

The policy enforcement pipeline operates on strict pre-execution interception, dynamic filesystem scanning (`std::fs::read_dir`), and a deterministic tiered priority system (`mrflow-rs/src/policy/mod.rs`).

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
                                    │ [Resolves highest (tier, priority) rule]
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
2. **`ask_user`:** The tool call is paused, and an interactive confirmation prompt is presented to the user (also accepts `"ask"` alias in TOML). Tools requiring human judgment (e.g. `ask_user`) default to `ask_user` interactively or `deny` in non-interactive runs (`non-interactive.toml`).
3. **`deny`:** The tool call is strictly rejected by the operating system. Attempting to execute prohibited commands produces an immediate rejection error (optionally customized via `denyMessage`).

---

## 3. Tiered Hierarchical Priority System

To prevent conflicting rules and guarantee that system security cannot be undermined, `PolicyEngine::load` in `mrflow-rs/src/policy/mod.rs` enforces a deterministic **Tiered Priority Hierarchy** across the 5-tier conceptual model:

| Active Tier | Name | Filesystem / CLI Sources | Scope & Authority | Sort Tuple |
| :---: | :--- | :--- | :--- | :--- |
| **5** | **Admin / System Tier** | `/etc/flowork/policies/` and CLI `--admin-policy` | Absolute system root security. Cannot be overridden by user or OS baselines. | `(5, priority)` |
| **2** | **User Tier** | `$HOME/.flowork/policies/` and CLI `--policy` | Personal preferences and per-user overrides across projects. | `(2, priority)` |
| **1** | **OS & Workspace Tier** | `/opt/floworkos/policies/` and `<cwd>/.flowork/policies/` | Core Flowork OS baseline policies (`sovereign.toml`, `write.toml`, etc.) and workspace `.flowork/policies/` files (evaluated together at Tier 1 in `mrflow-rs`; Tiers 3–4 are reserved for future extension/workspace separation). | `(1, priority)` |

### How Priority Resolution Works:
Rules are sorted in descending order by `(tier, priority)` (`i64` integer, default `50`, baseline OS rules use `1..999`):

* **Example:**
  - A default OS rule in `/opt/floworkos/policies/` with `priority = 998` evaluates at **`(tier = 1, priority = 998)`**.
  - A user rule in `$HOME/.flowork/policies/` with `priority = 10` evaluates at **`(tier = 2, priority = 10)`**.
  - **Result:** The user rule `(2, 10)` overrides the baseline rule `(1, 998)`, while an admin rule in `/etc/flowork/policies/` `(5, priority)` unconditionally overrides both.

---

## 4. Zero-Recompile Architecture: Adding Policies Without Rebuilding `mrflow`

> **YES, ABSOLUTELY 100%! THE SUBSYSTEM IS EXCLUSIVELY DESIGNED FOR THIS.**

Policies are **NEVER hardcoded inside the compiled CLI binary**.

When MrFlow starts:
1. `PolicyEngine::load` dynamically scans all configured `.toml` policy paths via Pure Rust `std::fs::read_dir` and canonical path deduplication.
2. Every `.toml` file is parsed natively via the `toml` and `regex` crates with zero JS/Zod overhead.
3. Rules are sorted by `(tier DESC, priority DESC)` and evaluated pre-execution on every tool call.

**Operational Implication:**
- **You never need to recompile `mrflow` to add, change, or revoke policies.**
- Drop a new `.toml` file into `/opt/floworkos/policies/`, `$HOME/.flowork/policies/`, `<cwd>/.flowork/policies/`, or pass `--policy <path>` / `--admin-policy <path>`.
- The binary discovers, parses, and enforces the updated rules on startup.

---

## 5. Standard TOML Policy Specification

Every policy file must be valid TOML containing rule blocks (`[[rule]]`, `[[rules]]`, `[commands] [[rules]]`) and/or `[[safety_checker]]` declarations. Both camelCase and snake_case keys (e.g. `toolName`/`tool_name`, `argsPattern`/`args_pattern`, `commandPrefix`/`command_prefix`, `commandRegex`/`command_regex`, `denyMessage`/`deny_message`) are accepted by `parse_single_rule`.

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
denyMessage = "Blocked destructive root deletion."
```

### Schema Field Definitions (`[[rule]]` / `[[rules]]` / `[commands.rules]`):

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | String | Optional | Descriptive human-readable label for debugging and audit logs. |
| `toolName` | String or Array | Optional (default `"*"`) | Exact tool identifier (e.g. `"run_shell_command"`), prefix wildcard (`"mcp_*"`), wildcard `"*"`, or array of names. Defaults to shell tools if `commandPrefix`/`commandRegex` is set. |
| `decision` | Enum | **YES** | Strictly `"allow"`, `"ask_user"` (or `"ask"`), or `"deny"`. |
| `priority` | Integer | Optional (default `50`) | Signed integer `i64` priority within a tier (typically `1`–`999`; higher wins). |
| `modes` | Array | Optional | Approval modes where this rule applies: `"default"`, `"autoEdit"`, `"sovereign"`, `"plan"` (matches `ApprovalMode::as_policy_mode()`, where CLI `--approval-mode` accepts `auto_edit`/`autoedit`, `sovereign`/`yolo`, `plan`, `default`). |
| `argsPattern` | String (Regex) | Optional | Regular expression tested against serialized JSON tool arguments (`\x00` markers normalized cleanly for Rust `regex`). |
| `commandPrefix` | String or Array | Optional | Shell command prefix matchers (`"git status"`, `["cargo ", "rustc "]`). |
| `commandRegex` | String (Regex) | Optional | Regular expression matched directly against shell `command` strings. |
| `interactive` | Boolean | Optional | Restricts rule to interactive sessions (`true`) or headless runs (`false`). |
| `allowRedirection` | Boolean | Optional | If `false`, shell piping/redirection (`>`, `<`, `\|`, `;`, `&&`) prevents automatic allow. Set `true` for sovereign builds. |
| `allowCommandSubstitution` | Boolean | Optional | Controls backticks / `$()` / `<()` command substitution inside shell commands. |
| `mcpName` | String | Optional | Targets tools belonging to a specific MCP server name (or `"*"` for all MCP tools). |
| `toolAnnotations` | Table | Optional | Supports `{ readOnlyHint = true }` to scope rules to read-only tools. |
| `subagent` | String | Optional | Restricts rule to a specific delegated agent profile name (e.g. `"codebase_investigator"`). |
| `denyMessage` | String | Optional | Custom explanation returned to the model/operator when `decision = "deny"`. |

### In-Process Safety Checkers (`[[safety_checker]]`):
```toml
[[safety_checker]]
toolName = "*"
priority = 100
[safety_checker.checker]
type = "in-process"
name = "conseca" # Also supports "allowed-path"
```

---

## 6. Production Policies in `/opt/floworkos/policies/`

The live OS baseline policies currently deployed in `/opt/floworkos/policies/` are:

| Policy File | Role & Invariants |
| :--- | :--- |
| `sovereign.toml` | **The Constitution of Sovereign Mode.** Grants `allow` to wildcard tools (`*`) with `priority = 998` and `allowRedirection = true`, locks `ask_user` to interactive confirmation (`priority = 999`), and blocks `enter_plan_mode`. |
| `plan.toml` | Enforces read-only safety inside `plan` mode, permits `codebase_investigator` and `cli_help` subagents, and limits writes strictly to `.flowork`/`plans/*.md` plan artifacts. |
| `agents.toml` | Authorizes `invoke_agent` across `default`, `autoEdit`, and `sovereign` modes (`priority = 50`). |
| `conseca.toml` | Enables the in-process `conseca` safety checker across wildcard tool calls (`priority = 100`). |
| `discovered.toml` | Authorizes `discovered_tool_*` and wildcard tool execution (`priority = 990`, `allowRedirection = true`). |
| `non-interactive.toml` | Denies `ask_user` prompts when `interactive = false` (`priority = 999`) to prevent headless hangs. |
| `write.toml` | Defines baseline rules for filesystem modification tools (`write_file`, `replace`). |
| `read-only.toml` | Grants baseline `allow` to non-destructive inspection tools (`read_file`, `list_directory`, `grep_search`). |
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
3. Test immediately with `mrflow`. The rules load dynamically with **Exit Code 0**!

---

### Tutorial B: Creating a Repository-Level Policy
To grant specialized automated permissions for a specific software project without altering global settings:

1. In the root of your project, create `<project>/.flowork/policies/project_build.toml`:
```toml
# Project-specific policy loaded from <cwd>/.flowork/policies/
[[rule]]
name = "Allow Cargo & Test Suite Autonomously"
toolName = "run_shell_command"
decision = "allow"
priority = 800
modes = ["sovereign", "default"]
argsPattern = "^cargo\\s+(test|build|clippy|check)"
allowRedirection = true
```
2. When MrFlow launches inside that directory, `.flowork/policies/` rules activate automatically (or pass `--policy` explicitly for User Tier 2 precedence).

---

## 8. Quality Gate & Acceptance Checklist

Before any policy file is deployed to `/opt/floworkos/policies/`:

- [ ] **Gate 1 (Territory):** Policy resides strictly as a physical `.toml` file under `/opt/floworkos/policies/`.
- [ ] **Gate 2 (TOML & Regex Syntax):** Parses cleanly with zero TOML parse or regex compilation errors.
- [ ] **Gate 3 (Enum Validation):** `modes` only declares valid policy mode enums: `"sovereign"`, `"default"`, `"autoEdit"`, `"plan"`.
- [ ] **Gate 4 (Decision Values):** `decision` must be strictly `"allow"`, `"ask_user"` (or `"ask"`), or `"deny"`.
- [ ] **Gate 5 (Language):** All comments, `name`, and `denyMessage` strings written in strict technical English.
- [ ] **Gate 6 (Zero Symlinks):** No symlinks anywhere in policy directories.
- [ ] **Gate 7 (Empirical Runtime Verification):** Verified with `cargo test` in `mrflow-rs` and live `mrflow` runs returning **Exit Code 0**.
