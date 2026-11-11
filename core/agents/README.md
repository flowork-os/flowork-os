# 🤖 FLOWORK OS — SOVEREIGN SUBAGENTS ECOSYSTEM & DELEGATION SPECIFICATION

> **AUTHORITY:** Flowork Architecture Board & Dr. Flow  
> **TERRITORY:** `/opt/floworkos/agents/` (Custom Profiles) & `mrflow-rs/src/agents/mod.rs` (Native Registry)  
> **CLASSIFICATION:** Sovereign System Architecture Standard (Strict English)

---

## 1. Executive Architecture

In **Flowork OS**, complex multi-file research, low-level kernel inspection, and domain-isolated workloads are delegated to **Subagents** executed by `NativeSubagentSpawner` (`mrflow-rs/src/agents/mod.rs`) via the native `invoke_agent` tool.

Every subagent executes in an **isolated turn context** with its own system prompt, bounded tool allowlist, and loop ceiling (`FLOWORK_SUBAGENT_MAX_TURNS`, default `300`), returning a concise structured synthesis via `complete_task` back to the parent orchestrator.

---

## 2. Built-In Native Subagents (`mrflow-rs/src/agents/mod.rs`)

Flowork OS ships three built-in local subagent profiles registered directly by `discover_agent_profiles`:

| Subagent ID | Display Name | Operational Domain | Authorized Tool Allowlist |
| :--- | :--- | :--- | :--- |
| **`codebase_investigator`** | Codebase Investigator | Deep codebase exploration, dependency tracing, symbol verification, and architecture discovery across repositories. | `read_file`, `read_many_files`, `list_directory`, `glob`, `grep_search`, `complete_task` |
| **`cli_help`** | CLI Help Agent | Mr. Flow CLI usage, slash commands, runtime configuration, and Flowork OS troubleshooting using `/opt/floworkos` docs. | `read_file`, `list_directory`, `glob`, `grep_search`, `complete_task` |
| **`kernel_sentinel`** | Kernel Sentinel | `Linux 7.3.0-flowork-rust` telemetry, `dmesg` diagnostics, Landlock LSM audit, and hardware/GPU surveillance (read-only inspection). | `run_shell_command`, `read_file`, `glob`, `grep_search`, `list_directory`, `complete_task` |

---

## 3. Custom Subagent Discovery & Resolution Order

`discover_agent_profiles` in `mrflow-rs/src/agents/mod.rs` aggregates profiles in deterministic priority order (first-seen `name` wins; duplicates are ignored):

1. **Built-in Native Profiles:** `codebase_investigator`, `cli_help`, `kernel_sentinel`.
2. **System Subagents Directory:** `/opt/floworkos/agents/*.md`
3. **User Subagents Directory:** `$HOME/.flowork/agents/*.md`
4. **Workspace Subagents Directory:** `<cwd>/.flowork/agents/*.md`

> **Documentation Exclusion Rule:** Files whose stem equals `readme` (case-insensitive, including `/opt/floworkos/agents/README.md`) and non-`.md` files are automatically skipped during agent discovery.

---

## 4. Custom Subagent Schema (`.md` + YAML Frontmatter)

Custom agents placed in `/opt/floworkos/agents/<agent_name>.md` are parsed by `parse_agent_markdown` (`mrflow-rs/src/agents/mod.rs`). The Markdown body following the closing `---` delimiter becomes the subagent's verbatim `system_prompt`.

### Authoritative Example Template (`/opt/floworkos/agents/<agent_name>.md`)

```markdown
---
name: network_auditor
display_name: Network Perimeter Auditor
description: Read-only inspection of listening sockets, firewall policies, and DNS resolution health.
kind: local
model: inherit
max_turns: 40
tools:
  - run_shell_command
  - read_file
  - grep_search
  - list_directory
  - complete_task
---

# Sovereign Network Perimeter Auditor

You are `network_auditor`, operating strictly in read-only diagnostic mode inside Flowork OS.

## Operational Mandates
1. Inspect listening TCP/UDP sockets (`ss -tulnp`), DNS state, and NetworkManager configs under `/opt/floworkos/system/network*`.
2. Never mutate firewall state, sockets, or system configs unless explicitly authorized by the parent task.
3. Return an empirical Markdown table of verified ports, owning processes, and exit codes using `complete_task`.
```

### Frontmatter Field Reference (`parse_agent_markdown`)

| Field | Accepted Keys | Type | Default / Behavior |
| :--- | :--- | :--- | :--- |
| `name` | `name` | String | Defaults to filename stem if omitted; must uniquely identify the agent. |
| `display_name` | `display_name`, `displayName` | String | Optional human-readable label. |
| `description` | `description` | String | Defaults to `"Custom specialist agent '<name>'"`. |
| `kind` | `kind` | String | Defaults to `"local"`. |
| `model` | `model` | String | Optional model override; `"inherit"` or empty reuses the active parent model. |
| `max_turns` | `max_turns`, `maxTurns` | Integer (`usize > 0`) | Overrides `FLOWORK_SUBAGENT_MAX_TURNS` for this profile. |
| `tools` | `tools` | List / CSV | Accepts YAML `- item` lines, inline `[a, b]`, or comma-separated strings. `complete_task` is always enabled for termination. |

---

## 5. Runtime Isolation & Governance Invariants

1. **Flat 1-Level Recursion Guard:**  
   `NativeSubagentSpawner` instantiates child `ToolRegistry` instances with `is_subagent = true`. Inside any subagent turn, `invoke_agent` is omitted from tool declarations and blocked at dispatch (`"Recursion guard: subagents cannot spawn child subagents."`).
2. **Read-Only Tool Enforcement:**  
   Child tool dispatch strictly filters both model declarations and incoming function calls against the profile's `tools` allowlist (plus `complete_task`).
3. **Policy Governance:**  
   Subagent invocation requires policy authorization. Baseline `/opt/floworkos/policies/agents.toml` permits `invoke_agent` across `default`, `autoEdit`, and `sovereign` modes (`priority = 50`), while `/opt/floworkos/policies/plan.toml` governs behavior in `plan` mode. Subagent-specific TOML rules can also match `subagent = "<agent_name>"`.
4. **Conditional Prompt Overhead Control:**  
   Subagent turns assemble context with `is_subagent = true` via `assemble_system_prompt`, preserving low token footprint.
5. **No Symlinks / Strict Technical English:**  
   All custom `.md` agent definitions under `/opt/floworkos/agents/` must be physical files written strictly in professional technical English.

---

## 6. Verification Checklist (Exit Code 0)

```bash
# 1. Verify documented built-in agents are registered in native source & docs
grep -E "codebase_investigator|cli_help|kernel_sentinel" /opt/floworkos/agents/README.md

# 2. Verify policy governance for invoke_agent
cat /opt/floworkos/policies/agents.toml

# 3. Verify zero internal symlinks under /opt/floworkos/agents/
find /opt/floworkos/agents -type l
```
