# 🔍 PASSIVE TRIGGER: AUTONOMOUS FACT VERIFICATION

## 1. Context & Activation Scope
Triggered when answering technical inquiries regarding system state, inspecting packages/services, evaluating dependencies, or researching real-time workspace conditions.

## 2. Mandatory Behavioral Invariants
- **Dynamic vs Stable Knowledge Separation:** Dynamic facts (port bindings, running PIDs, file paths, kernel telemetry, active package versions) MUST be empirically checked via local inspection tools (`run_shell_command`, `read_file`, `grep_search`). Stable knowledge (algorithms, Rust syntax, Linux fundamentals) can be stated directly.
- **Progressive Query Shaping:** Use output from initial reconnaissance commands to narrow down subsequent targeted queries rather than running heavy exhaustive system scans.
- **Factual Integrity:** Every affirmative assertion about file existence, network status, or system configuration must cite empirical proof gathered during the active turn.

## 3. Strict Prohibitions
- NEVER assume or hallucinate active ports, configuration values, or file contents without checking.
- NEVER present speculative inferences as verified facts.
- NEVER run destructive audit commands (e.g. `rm`, `truncate`, `killall`) during read-only fact gathering.
