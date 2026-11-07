# ⚡ FLOWORK OS — SOVEREIGN PROMPT SUBSYSTEM ARCHITECTURE & AUTHORING GUIDE

> **AUTHORITY:** Flowork Architecture Board & Dr. Flow  
> **TERRITORY:** `/opt/floworkos/system/system_promp/promps/`  
> **CLASSIFICATION:** Sovereign System Architecture Standard (Strict English)

---

# 🛑 SUPREME LAW: ABSOLUTE PROHIBITION OF ALWAYS-ON / PERSISTENT PROMPTS
## ⚠️ HARAM MEMBUAT PROMPT BARU YANG SELALU MUNCUL (STRICTLY PROHIBITED)
### ⚡ ALL NEW PROMPTS MUST BE 100% CONDITIONAL & TRIGGER-BOUND TO PREVENT PROMPT BLOAT!

> ### 🚨 THE ZERO-BLOAT PROMPT MANDATE (NON-NEGOTIABLE LAW):
> **HARAM HUKUMNYA** menambahkan instruksi statis baru ke dalam Base System Prompt (`00_preamble.md`, `01_core_mandates.md`, `02_operational_guidelines.md`).
> 
> Setiap prompt baru, solusi baru, atau doktrin baru **WAJIB 100% BERSIFAT KONDISIONAL** (*Passive Trigger* / *Event-Driven* / *Keyword-Routed*).
> 
> **KENAPA? (THE RATIONALE)**  
> Jika setiap solusi atau aturan baru dimasukkan ke base prompt yang selalu muncul di setiap turn, model akan mengalami **PROMPT BLOAT FATAL**—memboroskan token context window, memperlambat latensi inferensi, dan mendegradasi daya nalar model akibat *context saturation*.
> 
> **ATURAN EKSEKUSI WAJIB (MANDATORY INVARIANTS):**
> 1. **DILARANG KERAS (STRICTLY FORBIDDEN):** Menulis prompt statis baru yang di-load permanen di setiap turn. Base prompt (`00`, `01`, `02`) telah dikunci (`@lock`) dan tidak boleh ditambah-tambah teks situasional.
> 2. **WAJIB KONDISIONAL (JUST-IN-TIME INJECTION):** Setiap prompt baru WAJIB ditempatkan sebagai pemicu bersyarat:
>    - Di `promps/triggers/<name>.md` dengan relasi kata kunci di `router.js` atau kondisi di `promps/triggers.json`, ATAU
>    - Di `rules/<name>.rs` yang dikompilasi ke native binary `rules/.bin/<name>` dengan evaluasi Exit Code 0.
> 3. **PROMPT HANYA MUNCUL KETIKA KONDISI TERPENUHI:**
>    - Operator tidak sedang mengonfigurasi Glass HUD? $\rightarrow$ Prompt Glass HUD **TIDAK BOLEH MUNCUL**!
>    - Operator tidak sedang menyentuh Rust? $\rightarrow$ Prompt Rust **TIDAK BOLEH MUNCUL**!
>    - Operator tidak sedang build ISO? $\rightarrow$ Prompt ISO **TIDAK BOLEH MUNCUL**!
> 4. **TOKEN LIMIT EKSTRIM:** Setiap prompt kondisional wajib padat dan ringkas: maksimal **250 kata** (~350 token).

---

## 1. Executive Philosophy: Prompts as Living Consciousness

In Flowork OS, prompts are **NEVER hardcoded inside CLI binaries, bundle chunks, or UI engines**. Prompts exist exclusively as modular, on-disk living doctrines in `/opt/floworkos/system/system_promp/promps/`.

### Non-Dualism of Runtime Capabilities:
- **TOOL (`/opt/floworkos/tools/`):** The atomic instrument of physical action (Hands & Scalpels).
- **SKILL (`/opt/floworkos/skills/`):** The operational playbook, multi-step SOP, and domain heuristics (Procedural Brain Lobe).
- **PROMPT (`/opt/floworkos/system/system_promp/promps/`):** The living conscience, behavioral constraints, and dynamic environmental instincts (Soul & Reflexes).

---

## 2. Directory Anatomy & Subsystems

The sovereign prompt architecture is organized cleanly under `/opt/floworkos/system/system_promp/`:

```text
/opt/floworkos/system/system_promp/
├── promps/                          <-- Canonical prompt storage & runtime directory
│   ├── 00_preamble.md               <-- Sovereign Agent Identity & Approval Modes
│   ├── 01_core_mandates.md          <-- Security, Testing, Context & Intercept Gate
│   ├── 02_operational_guidelines.md <-- Monospace formatting, Tone, Project Instructions & Memory
│   ├── browser_issues/              <-- 207 DevTools CDP browser issue descriptors
│   ├── triggers/                    <-- Modular passive environmental triggers
│   ├── triggers.json                <-- Fast-path trigger condition matrix
│   ├── engine.js                    <-- Base prompt assembler & environmental instinct loader
│   ├── router.js                    <-- Formula 5-3-3 Dynamic Sliding Window Router
│   ├── watchdog_config.json         <-- Watchdog active IPC buffer configuration
│   └── README.md                    <-- This authoritative architecture guide
├── rules/                           <-- 60+ Compiled Rust environmental rule checkers
│   ├── *.rs                         <-- Rust source rule files
│   └── .bin/                        <-- Native compiled executable binaries (sub-ms eval)
└── triggers.json                    <-- Master system trigger registry linking rules to prompts
```

---

## 3. How Prompts Work ("Cara Kerja Prompt")

The prompt delivery pipeline combines static base loading, native environmental rule execution, and dynamic per-turn sliding window routing:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. BOOTSTRAP: Base System Prompt Assembly                              │
│ When MrFlow CLI launches, engine.js loads:                            │
│ [00_preamble.md] ──> [01_core_mandates.md] ──> [02_operational_guidelines.md] │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
┌────────────────────────────────────▼───────────────────────────────────┐
│ 2. ENVIRONMENTAL INSTINCTS: Compiled Native Rules Evaluation           │
│ engine.js scans system_promp/triggers.json & executes rules/.bin/*.rs │
│ Sub-millisecond evaluation checks: git, landmark files, environment    │
│ Matching prompts from promps/ are appended to system prompt envelope   │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
┌────────────────────────────────────▼───────────────────────────────────┐
│ 3. PER-TURN DELIVERY: Formula 5-3-3 Sliding Router (router.js)         │
│ When tools are invoked with reason, keywords, and goal:                │
│ Evaluates keyword overlap and injects Top 3 Passive Directives JIT    │
│ [<flowork_system_directive type="passive_trigger">]                    │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
┌────────────────────────────────────▼───────────────────────────────────┐
│ 4. BROWSER ISSUES GUIDANCE: On-Demand DevTools Descriptors             │
│ When CDP browser tools audit pages, chrome-devtools-mcp loads          │
│ descriptors from promps/browser_issues/ to diagnose web failures       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Prompt Authoring Standards ("Standar Prompt")

Every prompt file authored in `/opt/floworkos/system/system_promp/promps/` MUST conform to these mandatory standards:

### 1. Strict English Doctrine (Doktrin #9)
All system instructions, directives, markdown headers, and logs MUST be in strict technical English. Zero Indonesian or conversational filler.

### 2. Conciseness & Token Economy
- Trigger prompts must be under **250 words** (~350 tokens).
- Base mandates must justify every single line against token consumption costs.
- Never write redundant explanations: assume the underlying model is already capable; guide its judgment rather than reiterating basic concepts.

### 3. Imperative & Authoritative Voice
Write in direct, imperative technical language:
- *"Verify every file modification with empirical Exit Code 0."*
- *"Do not touch lines protected by @lock or @freez."*
- *"State your objective concisely via the goal parameter on initial tool calls."*

### 4. Standard 3-Part Directive Structure
Every trigger prompt file in `promps/triggers/<name>.md` must follow this structure:

```markdown
# [DIRECTIVE TITLE IN CAPITALIZED ENGLISH]

## 1. Context & Activation Scope
Define the exact scenario and trigger boundary where this directive applies.

## 2. Mandatory Behavioral Invariants
List non-negotiable operational rules that must be executed.
- Rule 1
- Rule 2

## 3. Strict Prohibitions
Explicitly state what the agent is forbidden from doing during this task.
- Never assume command output without checking exit codes.
- Never introduce non-sovereign dependencies.
```

---

## 5. Connecting Prompts to Passive Triggers ("Menghubungkan Prompt dengan Trigger Pasif")

Flowork OS provides two deterministic methods to connect prompts to passive triggers:

### Method A: Fast Landmark & Keyword Routing (via `promps/triggers/` & `router.js`)
Use this for workflow rules, tool hints, and keyword-triggered directives.

1. **Create the Markdown file:**
   `/opt/floworkos/system/system_promp/promps/triggers/iso_build.md`
2. **Register in `promps/triggers.json`:**
   ```json
   {
     "id": "iso_doctrine",
     "file": "triggers/iso_build.md",
     "rule": "Triggered when ISO build scripts or packaging keywords are found in workspace.",
     "condition": "workspaceContains(['*iso*', 'build-iso.sh'])"
   }
   ```
3. **Add to `router.js` Catalog:**
   The router automatically reads all `triggers/*.md` and calculates semantic overlap with the active turn's `keywords`, `goal`, and `reason`.

---

### Method B: Native Compiled Rust Rule (via `rules/*.rs` & `system_promp/triggers.json`)
Use this for high-precision, sub-millisecond environmental conditions (e.g. detecting open network ports, specific binary formats, daemon status, or deep filesystem structures).

1. **Create the Prompt file:**
   `/opt/floworkos/system/system_promp/promps/13_conditional_bash_fl_obligation.md`
2. **Author the Rust Rule:**
   Create `/opt/floworkos/system/system_promp/rules/conditional_bash_fl_obligation.rs`:
   ```rust
   use std::process::ExitCode;
   fn main() -> ExitCode {
       // Inspect environment variable or filesystem condition
       if std::path::Path::new("build-iso.sh").exists() {
           ExitCode::SUCCESS // Exit Code 0 -> Triggers the prompt!
       } else {
           ExitCode::FAILURE // Non-zero -> Prompt is NOT injected
       }
   }
   ```
3. **Compile the Native Binary:**
   ```bash
   rustc -O /opt/floworkos/system/system_promp/rules/conditional_bash_fl_obligation.rs \
         -o /opt/floworkos/system/system_promp/rules/.bin/conditional_bash_fl_obligation
   chmod +x /opt/floworkos/system/system_promp/rules/.bin/conditional_bash_fl_obligation
   ```
4. **Register in `/opt/floworkos/system/system_promp/triggers.json`:**
   ```json
   {
     "id": "conditional_bash_fl_obligation",
     "name": "Flowork Bash Packaging Obligation",
     "enabled": true,
     "rule": "rules/conditional_bash_fl_obligation.rs",
     "prompt": "promps/13_conditional_bash_fl_obligation.md"
   }
   ```
   When `engine.js` runs, it executes `/opt/floworkos/system/system_promp/rules/.bin/conditional_bash_fl_obligation` with a 25ms timeout. If it exits with 0, the prompt is injected instantly!

---

## 6. Lifecycle Management & Formula 5-3-3 Integration (Option C)

Prompts are managed under the **Contextual Retention & Lifecycle Engine**:

### 1. Short-Response Carryover
When the user replies with a terse confirmation ($\le 4$ words: *"ok"*, *"lanjut"*, *"gas"*, *"yes proceed"*, *"nomor 2"*):
- Active top 3 passive prompts from the previous turn are **RETAINED** in `/tmp/flowork_lifecycle_state.json`.
- The agent does NOT experience conversational amnesia or lose its active task guidance.

### 2. Domain Shift Sliding Window
When the user transitions to a distinct new domain (e.g. from `browser` $\rightarrow$ `shell_system`):
- Previous domain passive directives slide out of the context window.
- Up to 3 relevant prompts for the new domain slide in seamlessly.

---

## 7. Active Watchdog IPC Interrupts (`/tmp/flowork_active_trigger.json`)

System health daemons and background watchdogs can inject urgent directives into MrFlow's active turn asynchronously:

```json
{
  "active": true,
  "source": "KERNEL_WATCHDOG",
  "instruction": "🚨 CRITICAL: High memory pressure detected (>92% RAM). Suspend memory-intensive builds and clean cache before proceeding.",
  "timestamp": "2026-11-04T21:15:00.000Z"
}
```

When detected by `engine.js`, this IPC buffer is immediately prepended to the system prompt with maximum priority.

---

## 8. Quality Gate & Acceptance Checklist

Before any prompt is committed to `/opt/floworkos/system/system_promp/promps/`:

- [ ] **Gate 1 (Territory):** Prompt resides strictly in `/opt/floworkos/system/system_promp/promps/`.
- [ ] **Gate 2 (Language):** Written in strict, imperative technical English (zero Indonesian).
- [ ] **Gate 3 (Sovereignty):** Pure Flowork OS Sovereign DNA; zero external legacy remnants or non-sovereign branding.
- [ ] **Gate 4 (Token Efficiency):** Trigger directives are under 250 words.
- [ ] **Gate 5 (Zero Symlinks):** No symlinks anywhere in the prompt directory.
- [ ] **Gate 6 (Empirical Verification):** `engine.js` and `router.js` evaluate cleanly with **Exit Code 0**.
