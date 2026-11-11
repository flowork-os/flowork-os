# 📜 FLOWORK OS — MASTER SYSTEM PROMPT ARCHITECTURE & ENVIRONMENTAL RULES

> **AUTHORITY:** Flowork Architecture Board & Dr. Flow  
> **TERRITORY:** `/opt/floworkos/system/system_promp/`  
> **CLASSIFICATION:** Sovereign System Architecture Standard (Strict English)

---

# 🛑 SUPREME LAW: ABSOLUTE PROHIBITION OF ALWAYS-ON / PERSISTENT PROMPTS
## ⚠️ CREATING ALWAYS-ON GLOBAL PROMPTS IS STRICTLY PROHIBITED
### ⚡ ALL NEW PROMPTS MUST BE 100% CONDITIONAL & TRIGGER-BOUND TO PREVENT PROMPT BLOAT!

> ### 🚨 THE ZERO-BLOAT PROMPT MANDATE (NON-NEGOTIABLE LAW):
> Adding new static instructions to the Base System Prompts (`00_preamble.md`, `01_core_mandates.md`, `02_operational_guidelines.md`) is **STRICTLY FORBIDDEN**.
> 
> Every new prompt, remediation rule, or domain doctrine **MUST BE 100% CONDITIONAL** (*Passive Trigger* / *Event-Driven* / *Keyword-Routed*).
> 
> **THE RATIONALE:**  
> Placing every new fix or rule into the always-loaded base prompt causes **FATAL PROMPT BLOAT**—wasting context window tokens, degrading inference latency, and eroding reasoning fidelity through *context saturation*.
> 
> **MANDATORY EXECUTION INVARIANTS:**
> 1. **STRICTLY FORBIDDEN:** Authoring persistent static prompts loaded unconditionally on every turn. Base anchors (`00`, `01`, `02`) remain protected (`@lock`) against situational bloat.
> 2. **JUST-IN-TIME INJECTION ONLY:** Every new prompt MUST live as a conditional trigger:
>    - In `promps/triggers/<name>.md` indexed via `promps/triggers.json` (evaluated by the `mrflow-rs` Formula 5-3-3 router), OR
>    - In `rules/<name>.rs` compiled into native binary `rules/.bin/<name>` evaluated via Exit Code 0.
> 3. **STRICT CONDITIONAL ACTIVATION BOUNDARY:**
>    - Not configuring Glass HUD? $\rightarrow$ Glass HUD directive **MUST NOT APPEAR**!
>    - Not working with Rust? $\rightarrow$ Rust directive **MUST NOT APPEAR**!
>    - Not building an ISO? $\rightarrow$ ISO directive **MUST NOT APPEAR**!
> 4. **STRICT TOKEN CEILING:** Conditional directives must remain dense and concise: maximum **250 words** (~350 tokens).

---

## 1. Executive Philosophy: The Master System Prompt Hub

In Flowork OS, prompts are not static string literals embedded inside CLI binaries. They form a **Living Cognitive Ecosystem** governed by the master hub at `/opt/floworkos/system/system_promp/`.

This hub orchestrates:
1. **Core Sovereign Doctrines & Guidelines:** The foundational moral invariants and persona mandates residing in `promps/`.
2. **Ambient Environmental Instincts:** 78 native Rust rule checkers residing in `rules/` and compiled into 83 sub-millisecond executable binaries in `rules/.bin/`.
3. **Declarative Trigger Matrix:** The central registry (`triggers.json`, 81 registered entries) that links environmental conditions directly to dynamic prompt injections.

---

## 2. Directory Anatomy & Subsystems

The master system prompt territory is organized into decoupled, high-performance components:

```text
/opt/floworkos/system/system_promp/
├── promps/                          <-- Canonical prompt storage & runtime assets
│   ├── 00_preamble.md               <-- Sovereign Agent Identity & Approval Modes
│   ├── 01_core_mandates.md          <-- Security, Testing, Context & Intercept Gate
│   ├── 02_operational_guidelines.md <-- Reserved base anchor (currently 0 bytes)
│   ├── browser_issues/              <-- 207 DevTools CDP browser issue descriptors
│   ├── triggers/                    <-- 56 modular passive environmental trigger directives
│   ├── triggers.json                <-- Fast-path trigger condition matrix
│   ├── watchdog_config.json         <-- Watchdog active IPC buffer configuration
│   └── README.md                    <-- Detailed prompt subsystem guide
├── rules/                           <-- 78 Native Rust environmental rule sources
│   ├── *.rs                         <-- Rust source rule files
│   └── .bin/                        <-- 83 Native compiled executable binaries (<1ms eval)
├── triggers.json                    <-- Master system trigger registry (81 rule bindings)
├── SKILL.md                         <-- Skill specification for environmental rule evaluation
└── README.md                        <-- This authoritative architecture guide
```

---

## 3. How the Subsystem Works: The Boot & Turn Assembly Pipeline

The prompt synthesis pipeline combines static baseline mandates, native compiled rule evaluation, and per-turn dynamic routing inside `mrflow-rs/src/cognitive/mod.rs`:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. BOOTSTRAP: Base System Prompt Assembly                              │
│ When MrFlow launches, native Rust engine loads the core anchors:       │
│ [00_preamble.md] ──> [01_core_mandates.md] ──> [02_operational_guidelines.md] │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Scans system_promp/triggers.json]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. ENVIRONMENTAL INSTINCTS: Native Compiled Rust Rules Evaluation      │
│ mrflow-rs executes compiled binaries in rules/.bin/ with 50ms timeout  │
│ Evaluates: git status, open ports, landmark files, active package stack │
│ If Exit Code == 0: Matching prompt payload from promps/ is appended   │
│ into <PASSIVE_ENVIRONMENTAL_INSTINCT> envelope.                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Intercepts active watchdog buffer (300s TTL)]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. ACTIVE WATCHDOG INTERRUPT: Emergency Telemetry Signals              │
│ If /tmp/flowork_active_trigger.json is active and timestamp <= 300s:   │
│ Prepend emergency watchdog warning (RAM/Disk/Runaway PID) immediately. │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [User invokes tool with keywords & reason]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. PER-TURN DELIVERY: Native Rust Formula 5-3-3 Dynamic Sliding Router │
│ Ingests active reason, keywords, and goal:                             │
│ Calculates keyword vector overlap and injects Top 3 relevant prompts.  │
│ Suppresses unneeded prompts to maintain 0 token waste.                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. The Native Compiled Rust Rule Engine (`rules/` & `.bin/`)

### Why Native Compiled Rust?
In traditional AI systems, checking environmental conditions requires spawning heavy shell interpreters (`bash -c "..."` or Python scripts), creating massive latency spikes (100ms - 500ms) on every turn. 

In Flowork OS, environmental sensors are written in **pure Rust** and compiled to standalone native ELF binaries in `rules/.bin/`:
- **Execution Speed:** Sub-millisecond latency (<1ms per rule check).
- **Zero Interpreter Overhead:** No runtime dependencies or shell subshells.
- **Resource Footprint:** Negligible RAM footprint during turn assembly.

### The Exit Code Invariant:
Every native rule in `rules/*.rs` communicates with the engine via POSIX exit codes:
- **`Exit Code 0` (SUCCESS):** Condition is **SATISFIED**. The engine immediately injects the mapped prompt file into the agent's context envelope.
- **`Exit Code 1` (or non-zero):** Condition is **NOT SATISFIED**. The rule is quiescent, and the prompt payload is suppressed with zero token cost.

---

## 5. Master Trigger Registry Specification (`triggers.json`)

The central file `/opt/floworkos/system/system_promp/triggers.json` binds native rule binaries to prompt payloads:

```json
[
  {
    "id": "conditional_bash_fl_obligation",
    "name": "Flowork Bash Packaging Obligation",
    "enabled": true,
    "scope": "universal_all",
    "rule": "rules/conditional_bash_fl_obligation.rs",
    "prompt": "promps/13_conditional_bash_fl_obligation.md"
  },
  {
    "id": "git_contribution_directive",
    "name": "Mandatory Official Git Contributor Attribution",
    "enabled": true,
    "scope": "default_solo",
    "rule": "rules/git_contribution_directive.rs",
    "prompt": "promps/20_git_contribution_directive.md"
  }
]
```

### Registry Field Definitions:
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique slug identifier for the trigger rule. |
| `name` | String | Human-readable title of the environmental instinct. |
| `enabled` | Boolean | Master switch. If `false`, the rule is skipped during turn assembly. |
| `scope` | String | Execution scope: `"universal_all"`, `"default_solo"`, or `"team_worker"`. |
| `rule` | String | Relative path to the Rust source rule (`rules/<name>.rs`). Evaluates binary at `rules/.bin/<name>`. |
| `prompt` | String | Relative path to the markdown prompt payload (`promps/<number>_<name>.md`). |

---

## 6. Step-by-Step Tutorial: Authoring a New Passive Environmental Rule

Follow this verified protocol to author a new native passive trigger:

### Step 1: Create the Markdown Prompt Payload
Create `/opt/floworkos/system/system_promp/promps/25_docker_environment_guide.md`:
```markdown
# [DOCKER ENVIRONMENT DIRECTIVE]

## 1. Context & Scope
Active when a `Dockerfile` or `compose.yaml` landmark is detected in the workspace.

## 2. Mandatory Behavioral Invariants
- Verify all container builds using multi-stage alpine base images.
- Test docker commands with `--no-cache` flag during validation.
- Always check container exit codes before declaring build completion.
```

### Step 2: Author the Native Rust Rule
Create `/opt/floworkos/system/system_promp/rules/docker_environment_guide.rs`:
```rust
use std::path::Path;
use std::process::ExitCode;

fn main() -> ExitCode {
    let has_dockerfile = Path::new("Dockerfile").exists();
    let has_compose = Path::new("compose.yaml").exists() || Path::new("docker-compose.yml").exists();

    if has_dockerfile || has_compose {
        ExitCode::SUCCESS // Exit Code 0 -> Condition met!
    } else {
        ExitCode::FAILURE // Exit Code 1 -> Suppress prompt
    }
}
```

### Step 3: Compile the Native ELF Binary
Compile the rule into the native `.bin/` execution cache:
```bash
rustc -O /opt/floworkos/system/system_promp/rules/docker_environment_guide.rs \
      -o /opt/floworkos/system/system_promp/rules/.bin/docker_environment_guide
chmod +x /opt/floworkos/system/system_promp/rules/.bin/docker_environment_guide
```

### Step 4: Register in `triggers.json`
Append the entry to `/opt/floworkos/system/system_promp/triggers.json`:
```json
{
  "id": "docker_environment_guide",
  "name": "Docker Container Environment Guide",
  "enabled": true,
  "scope": "universal_all",
  "rule": "rules/docker_environment_guide.rs",
  "prompt": "promps/25_docker_environment_guide.md"
}
```

### Step 5: Empirical Verification
Test the compiled rule directly:
```bash
/opt/floworkos/system/system_promp/rules/.bin/docker_environment_guide
echo "Exit Code: $?"
```
The binary evaluates in <1ms and returns Exit Code 0 when landmarks exist.

---

## 7. Quality Gate & Acceptance Checklist

Before any rule or prompt is committed to `/opt/floworkos/system/system_promp/`:

- [ ] **Gate 1 (Territory):** Rule resides in `rules/`, compiled binary in `rules/.bin/`, and prompt in `promps/`.
- [ ] **Gate 2 (Binary Compilation):** The Rust rule compiles cleanly with `rustc -O` and is marked executable (`chmod +x`).
- [ ] **Gate 3 (Registry Integrity):** `triggers.json` is valid JSON and all referenced paths physically exist.
- [ ] **Gate 4 (Language):** All prompt directives, rule comments, and registry names written in strict technical English.
- [ ] **Gate 5 (Zero Symlinks):** No symlinks anywhere within the prompt or rule directories.
- [ ] **Gate 6 (Empirical Verification):** `mrflow-rs` cognitive suite and `triggers.json` evaluate cleanly with **Exit Code 0**.
