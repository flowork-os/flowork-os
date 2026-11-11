# 🌊 Flowork OS — Autonomous Sovereign Operating System

```text
  ███████╗██╗      ██████╗ ██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗     ██████╗ ███████╗
  ██╔════╝██║     ██╔═══██╗██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝    ██╔═══██╗██╔════╝
  █████╗  ██║     ██║   ██║██║ █╗ ██║██║   ██║██████╔╝█████╔╝     ██║   ██║███████╗
  ██╔══╝  ██║     ██║   ██║██║███╗██║██║   ██║██╔══██╗██╔═██╗     ██║   ██║╚════██║
  ██║     ███████╗╚██████╔╝╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗    ╚██████╔╝███████║
  ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝
```

> **Authoritative Root Specification**  
> **System Territory:** `/opt/floworkos`  
> **Official Portal:** [floworkos.com](https://floworkos.com)  
> **Architecture Blueprint:** See [ARCHITECT.md](file:///opt/floworkos/ARCHITECT.md)  

---

## 1. What is Flowork OS?

**Flowork OS** is an autonomous, memory-safe, sovereign agent-native desktop operating system. Designed from first principles to bridge classical UNIX computing with modern autonomous artificial intelligence, Flowork OS treats autonomous agent cognition not as an external application, but as a core system capability integrated directly into the operating system.

### Core Pillars of Sovereignty
1. **Rust-Integrated Linux Kernel (`Eust Kernel`)**: Running `Linux 7.3.0-flowork-rust`, leveraging Rust in kernel space for memory safety, Landlock LSM process sandboxing, direct DRM framebuffer capture, and virtual HID emulation.
2. **Mr. Flow Autonomous Engine**: Clean-room Pure Rust runtime (`/usr/local/bin/mrflow` -> `/opt/floworkos/bin/mrflow`) executing Formula 5-3-3 dynamic context routing, 78 native Rust rule sources (`83` compiled ELF binaries in `rules/.bin/`), core native built-in tools, and 70 decoupled manifest tools.
3. **Radical Non-Dualism**: *"Flowork is Linux. Linux applications are Flowork applications."* Every standard Linux tool, binary, desktop environment service, and POSIX interface functions as a first-class Flowork OS component.
4. **Cinnamon Identity Eradication**: All legacy Cinnamon branding and visual traces have been eradicated in favor of the bespoke Flowork Quantum Glass desktop (`flowork-wm`), Plank dock orchestration, and customized Nemo file navigation.
5. **Deterministic Verification (Exit Code 0)**: A strict engineering standard requiring reproducible command-line verification for all system operations and tool actions.
6. **Sovereign Connector Gateway (:9099)**: Pure Rust local inference proxy (`/opt/floworkos/connector/bin/flowork-connector`) providing automatic multi-account quota rotation, HTTP 429 cooldown recovery, and multi-backend switching across Google CloudCode, local Ollama, and 9Router gateway.

---

# 🛑 SUPREME DOCTRINE: ZERO ALWAYS-ON PROMPTS — 100% CONDITIONAL TRIGGER MANDATE
## ⚡ ALL NEW PROMPTS MUST BE CONDITIONALLY ROUTED TO PREVENT FATAL PROMPT BLOAT

> ### 🚨 THE ZERO-BLOAT PROMPT INVARIANT:
> It is **STRICTLY FORBIDDEN** to append new static text or situational rules into the always-loaded Base Prompt (`00_preamble.md`, `01_core_mandates.md`, `02_operational_guidelines.md`), which are protected by `@lock`.
>
> Every new solution, domain doctrine, or behavioral directive **MUST BE 100% CONDITIONAL** (Just-In-Time Injection):
> 1. **ZERO BLOAT:** Never pollute the model context window with situational instructions unrelated to the active turn.
> 2. **MANDATORY TRIGGERS:** Author conditional directives under `promps/triggers/<name>.md` (indexed in `promps/triggers.json` for Formula 5-3-3 routing) OR as compiled native Rust checks in `rules/<name>.rs` (`rules/.bin/<name>` returning Exit Code 0 when active).
> 3. **EXTREME TOKEN ECONOMY:** Conditional trigger prompts must remain concise at **$\le$ 250 words** (~350 tokens).

---

## 2. Master Architecture Blueprint

For full technical specifications covering kernel internals, `flowork-sysd` HTTP REST control plane (`:18090`), Neural Bus (`:18095`), Landlock sandboxing, and IPC fabrics, consult the master architecture guide:

📖 **[ARCHITECT.md](file:///opt/floworkos/ARCHITECT.md)** — *The Complete Master Architecture Specification*

---

## 3. The Sovereign Modular Pillars

Flowork OS organizes its operational subsystems into **modular, decoupled pillars**. Each subsystem provides canonical documentation pinned directly into the Nemo file manager bookmarks (`/etc/skel/.config/gtk-3.0/bookmarks`):

```text
/opt/floworkos/
├── ARCHITECT.md                       <-- Master System Architecture Specification
├── README.md                          <-- This System Root Guide
├── apps/                              <-- 🚀 Sovereign Desktop & CLI Applications
├── connector/                         <-- ⚡ Connector Gateway (:9099)
├── screenshots/                       <-- 📸 Screenshots & Ambient Sight Vault
├── system/
│   ├── system_promp/
│   │   ├── promps/                    <-- ⚡ Master System Prompts & Engine
│   │   ├── rules/                     <-- 📜 Rules & Triggers (Compiled Rust)
│   │   └── triggers.json
│   └── triger/                        <-- 🎯 Active Trigger Daemons
├── tools/                             <-- 🛠️ Decoupled Tools Registry (70 manifests)
├── agents/                            <-- 🤖 Subagents Ecosystem
├── mcp/                               <-- 🔌 Model Context Protocol Hub
├── policies/                          <-- ⚖️ Tiered TOML Security Policies
├── skills/                            <-- 💡 20-Keyword Knowledge Skills
└── history/
    └── chats/                         <-- 💬 Episodic Chat History Vault
```

### Pillar Directory & Cross-Reference Matrix (12 Bookmarked Pillars)

| # | Pillar & Bookmark | Filesystem Path | Authoritative Documentation | Functional Role |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **📸 Screenshots** | `/opt/floworkos/screenshots` | [README.md](file:///opt/floworkos/screenshots/README.md) | Universal visual capture vault; centralizes Ambient Eye frames (`Super+Shift+A`), FlowFS WebP thumbs, and CLI/agent captures. |
| **2** | **⚡ Prompts** | `/opt/floworkos/system/system_promp/promps` | [README.md](file:///opt/floworkos/system/system_promp/promps/README.md) | Canonical prompt engine; houses sovereign preamble, core mandates, conditional triggers, and the Formula 5-3-3 dynamic assembler. |
| **3** | **🛠️ Tools** | `/opt/floworkos/tools` | [README.md](file:///opt/floworkos/tools/README.md) | Decoupled standalone tool foundry (70 manifest tools); native Rust discovery (`flowork-tool-discovery`) and execution (`flowork-tool-runner`). |
| **4** | **🤖 Subagents** | `/opt/floworkos/agents` | [README.md](file:///opt/floworkos/agents/README.md) | Delegated worker ecosystem; built-ins (`codebase_investigator`, `cli_help`, `kernel_sentinel`) plus custom `.md` YAML frontmatter specs with flat 1-level isolation. |
| **5** | **🔌 MCP Servers** | `/opt/floworkos/mcp` | [README.md](file:///opt/floworkos/mcp/README.md) | Model Context Protocol integration hub (`downflow-mcp`, `earshot`); clean stdio / StreamableHttp / SSE IPC isolation decoupled from native tools. |
| **6** | **⚖️ Policies** | `/opt/floworkos/policies` | [README.md](file:///opt/floworkos/policies/README.md) | Tiered TOML security governance engine (`allow`, `ask_user`, `deny`) + safety checkers; evaluated dynamically on-disk without recompilation. |
| **7** | **💡 Skills** | `/opt/floworkos/skills` | [README.md](file:///opt/floworkos/skills/README.md) | Procedural SOP knowledge repository; strictly enforced by `flowork-lint-skills` with YAML frontmatter containing **exactly 20 English keywords**. |
| **8** | **🎯 Active Triggers** | `/opt/floworkos/system/triger` | [README.md](file:///opt/floworkos/system/triger/README.md) | Asynchronous background watchdog supervisor (`supervisor.py`) writing high-priority environmental alerts to `/tmp/flowork_active_trigger.json`. |
| **9** | **📜 Rules & Triggers** | `/opt/floworkos/system/system_promp` | [README.md](file:///opt/floworkos/system/system_promp/README.md) | Master prompt hub & 78 native Rust environmental rule sources (`83` compiled ELF binaries in `rules/.bin/`) linking OS state to prompt injection. |
| **10** | **💬 Chat History** | `/opt/floworkos/history/chats` | [README.md](file:///opt/floworkos/history/chats/README.md) | Canonical append-only JSONL transcript vault (`SessionVault`) partitioned by workspace slug with compression snapshots for lossless `--resume`. |
| **11** | **⚡ Connector** | `/opt/floworkos/connector` | [README.md](file:///opt/floworkos/connector/README.md) | Pure Rust inference gateway (:9099), multi-account OAuth quota shield (`data/vault.json`), and provider routing matrix. |
| **12** | **🚀 Apps** | `/opt/floworkos/apps` | [README.md](file:///opt/floworkos/apps/README.md) | Sovereign desktop & CLI application ecosystem, `flow-app` JIT synthesis, `flowpkg` `.flowapp` bundles & remixing, and XDG/Plank launcher sync. |

---

## 4. Key Subsystem Highlights

### A. Sovereign Connector Gateway (:9099)
- **Multi-Account Quota Shield**: Rotates API accounts persisted in `/opt/floworkos/connector/data/vault.json` dynamically with smart HTTP 429 cooldowns.
- **Model Normalization**: Pins Google CloudCode inference requests reliably to `gemini-3.8-flash-high` (`connector-rs/src/translator.rs`).
- **Multi-Provider Switch**: Seamless routing across Google CloudCode, local Ollama GPU/CPU engines (`:11434`), and OpenAI-compatible gateways (e.g. 9Router).

### B. Dynamic Security & Tool Execution
- **Tiered TOML Policy Hierarchy**: Evaluates tool calls dynamically across **Tier 5 (Admin `/etc/flowork/policies/`, `--admin-policy`) > Tier 2 (User `$HOME/.flowork/policies/`, `--policy`) > Tier 1 (Workspace `.flowork/policies/` & OS `/opt/floworkos/policies/`)**, alongside in-process safety checkers (`conseca`, `allowed-path`).
- **Kernel Landlock LSM**: Hardware-backed path restriction enforced via `flowork-sysd` (`landlock_sandbox.rs`) and `flowpkg` (`syscall 444`) preventing unauthorized workspace escapes.
- **Hybrid Core + Decoupled Tool Foundry**: Combines fast native Rust built-in tools inside `mrflow` (`read_file`, `write_file`, `replace`, `run_shell_command`, `glob`, `grep_search`, `list_directory`, `invoke_agent`, `activate_skill`, `tracker_*`, etc.) with 70 dynamically filtered manifest tools in `/opt/floworkos/tools/`.

### C. Sub-Millisecond Environmental Instincts
- **Formula 5-3-3 Dynamic Sliding Router**: `Formula533Router` (`mrflow-rs/src/cognitive/mod.rs`) scores Intercept Gate `keywords`, `goal`, and `reason` signals (5 points per token hit; activation threshold `>= 10`) to inject **Top 5 Tools**, **Top 3 Skills**, and **Top 3 Conditional Prompts** without token bloat.
- **Native Rust Rules**: `78` pure Rust rule sources (`83` compiled ELF binaries in `rules/.bin/`, 50ms timeout ceiling) inspect git state, ports, active processes, and landmark files during prompt assembly.

### D. Multi-User Portability & ISO Zero-Error
- **Decoupled Root Storage**: Shared runtime artifacts (`screenshots/`, `history/chats/`) reside under `/opt/floworkos/` with universal permissions (`0777`) while user sessions resolve `$HOME` dynamically (`~/.flowork/`).
- **Zero Broken Paths**: New installations provisioned from the Flowork OS ISO inherit all 12 unified bookmarks and desktop configs via `/etc/skel/`.

---

## 5. Quick Start & Operational Commands

### Launching the Autonomous Agent (Mr. Flow)
```bash
# Launch interactive sovereign CLI session
mrflow

# Resume the most recent conversation in the current workspace
mrflow --resume latest

# Execute a one-shot autonomous task
mrflow -p "Inspect system status and report active daemons"
```

### Desktop Snipping, Ambient Sight & Screenshots
- **Ambient Eye Context Capture**: Press `Super + Shift + A` (`flowork-ambient-eye`: captures to `/opt/floworkos/screenshots/`, copies to clipboard, indexes into FlowFS screen memory, and notifies Neural Bus).
- **Full Screen Instant Capture**: Press `PrintScreen` (`flowork-screenshot`).
- **Interactive Snipping Tool**: Press `Shift + PrintScreen` (`flowork-screenshot --area`).

### Navigating the System in Terminal
```bash
# Jump to tools
cd /opt/floworkos/tools

# Jump to prompts
cd /opt/floworkos/system/system_promp/promps

# Jump to active triggers
cd /opt/floworkos/system/triger

# Jump to screenshots vault
cd /opt/floworkos/screenshots

# Jump to chat history
cd /opt/floworkos/history/chats

# Jump to applications
cd /opt/floworkos/apps
```

---

## 6. Codebase Discipline & Invariants

All contributors, engineers, and autonomous subagents must adhere to the following invariants:
1. **Strict Technical English**: All codebase files, manifests, prompts, skills, policies, and documentation must be authored strictly in professional technical English.
2. **Canonical Naming**: Exactly one lowercase `README.md` per folder. Duplicate uppercase `README.MD` files are strictly forbidden.
3. **No New Internal Symlinks**: Keep all pillar directories, tools, and skills as physical files on disk (beyond the pre-existing `/opt/floworkos/prompts -> system/system_promp/promps` compatibility link and `/opt/floworkos/screenshots/ambient_latest.png` runtime capture link).
4. **Sacred Locks**: Lines protected by `@lock` or `@freez` markers must never be modified or removed.

---

*Flowork OS — The Sovereign Operating System for Autonomous Human-Machine Synergy.*
