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
> **System Territory:** `/opt/floworkos` (Mirrored to `/home/mrflow/floworkos`)  
> **Official Portal:** [floworkos.com](https://floworkos.com)  
> **Architecture Blueprint:** See [ARCHITECT.md](file:///opt/floworkos/ARCHITECT.md)  

---

## 1. What is Flowork OS?

**Flowork OS** is an autonomous, memory-safe, sovereign agent-native desktop operating system. Designed from first principles to bridge classical UNIX computing with modern autonomous artificial intelligence, Flowork OS treats autonomous agent cognition not as an external application, but as a core system capability integrated directly into the operating system.

### Core Pillars of Sovereignty
1. **Rust-Integrated Linux Kernel (`Eust Kernel`)**: Running `Linux 7.3.0-flowork-rust`, leveraging Rust in kernel space for memory safety, Landlock LSM process sandboxing, direct DRM framebuffer capture, and virtual HID emulation.
2. **Mr. Flow Autonomous Engine**: An integrated autonomous agent runtime (`/usr/local/bin/mrflow`) executing dynamically routed prompts, 60+ native compiled Rust environmental rules, and decoupled modular tools.
3. **Radical Non-Dualism**: *"Flowork is Linux. Linux applications are Flowork applications."* Every standard Linux tool, binary, desktop environment service, and POSIX interface functions as a first-class Flowork OS component.
4. **Cinnamon Identity Eradication**: All legacy Cinnamon branding and visual traces have been eradicated in favor of the bespoke Flowork Dark Glass desktop with Plank docking and customized Nemo file navigation.
5. **Deterministic Verification (Exit Code 0)**: A strict engineering standard requiring reproducible command-line verification for all system operations and tool actions.
6. **Sovereign Connector Gateway (:9099)**: High-performance local inference proxy providing automatic multi-account quota rotation, error 429 recovery, and multi-backend switching across Google CloudCode, local Ollama, and 9Router gateway.

---

# 🛑 DOKTRIN SUPREMUM: HARAM MEMBUAT PROMPT BARU YANG SELALU MUNCUL!
## ⚡ WAJIB 100% KONDISIONAL (PASSIVE TRIGGER) UNTUK MENCEGAH FATAL PROMPT BLOAT

> ### 🚨 THE ZERO-BLOAT PROMPT INVARIANT:
> **HARAM HUKUMNYA** menambahkan teks atau aturan baru ke dalam Base Prompt (`00_preamble.md`, `01_core_mandates.md`, `02_operational_guidelines.md`) yang selalu muncul di setiap turn!
>
> Setiap solusi baru, doktrin baru, atau inteligensi baru **WAJIB DIJADIKAN TRIGGER KONDISIONAL** (Just-In-Time Injection):
> 1. **DILARANG BLOAT:** Jangan menjejali konteks model dengan aturan situasional yang tidak relevan dengan turn aktif.
> 2. **WAJIB TRIGGER:** Buat prompt di `promps/triggers/<name>.md` atau `rules/<name>.rs` (native compiled binary). Prompt HANYA boleh diinjeksi saat kondisi terpenuhi (misal: saat membuka Rust, ISO build, atau glass config).
> 3. **TOKEN EKONOMIS:** Prompt trigger maksimal **250 kata** (~350 token).

---

## 2. Master Architecture Blueprint

For full technical specifications covering kernel internals, `sysd` native daemons, Landlock sandboxing, and IPC fabrics, consult the master architecture guide:

📖 **[ARCHITECT.md](file:///opt/floworkos/ARCHITECT.md)** — *The Complete Master Architecture Specification*

---

## 3. The Sovereign Modular Pillars

Flowork OS organizes its operational subsystems into **modular, decoupled pillars**. Each subsystem is self-contained with its own canonical documentation and pinned directly into the Nemo file manager sidebar:

```text
/opt/floworkos/
├── ARCHITECT.md                       <-- Master System Architecture Specification
├── README.md                          <-- This System Root Guide
├── connector/                         <-- ⚡ Connector Gateway (:9099)
├── screenshots/                       <-- 📸 Screenshots Vault
├── system/
│   ├── system_promp/
│   │   ├── promps/                    <-- ⚡ Master System Prompts & Engine
│   │   ├── rules/                     <-- 📜 Rules & Triggers (Compiled Rust)
│   │   └── triggers.json
│   └── triger/                        <-- 🎯 Active Trigger Daemons
├── tools/                             <-- 🛠️ Decoupled Tools Registry
├── agents/                            <-- 🤖 Subagents Ecosystem
├── mcp/                               <-- 🔌 Model Context Protocol Hub
├── policies/                          <-- ⚖️ 5-Tier Security Policies
├── skills/                            <-- 💡 20-Keyword Knowledge Skills
└── history/
    └── chats/                         <-- 💬 Episodic Chat History Vault
```

### Pillar Directory & Cross-Reference Matrix

| # | Pillar & Bookmark | Filesystem Path | Authoritative Documentation | Functional Role |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **📸 Screenshots** | `/opt/floworkos/screenshots` | [README.md](file:///opt/floworkos/screenshots/README.md) | Universal system capture vault; centralizes headless browser screenshots, CLI captures, and desktop snipping. |
| **2** | **⚡ Prompts** | `/opt/floworkos/system/system_promp/promps` | [README.md](file:///opt/floworkos/system/system_promp/promps/README.md) | Canonical prompt engine; houses sovereign preamble, core mandates, guidelines, and the Formula 5-3-3 dynamic assembler. |
| **3** | **🛠️ Tools** | `/opt/floworkos/tools` | [README.md](file:///opt/floworkos/tools/README.md) | Decoupled tool engine; completely external from the CLI binary; dynamic discovery (`discovery.js`) and execution (`executor.js`). |
| **4** | **🤖 Subagents** | `/opt/floworkos/agents` | [README.md](file:///opt/floworkos/agents/README.md) | Autonomous delegate ecosystem; enforces mandatory `goal` and `golden_rules` schema, isolated sub-turns, and flat 1-level hierarchy. |
| **5** | **🔌 MCP Servers** | `/opt/floworkos/mcp` | [README.md](file:///opt/floworkos/mcp/README.md) | Model Context Protocol integration hub; clean stdio IPC isolation; decoupled from native agent tools. |
| **6** | **⚖️ Policies** | `/opt/floworkos/policies` | [README.md](file:///opt/floworkos/policies/README.md) | 5-tier security governance engine (`allow`, `ask_user`, `deny`); 100% dynamic TOML rules evaluated on-disk without recompilation. |
| **7** | **💡 Skills** | `/opt/floworkos/skills` | [README.md](file:///opt/floworkos/skills/README.md) | Procedural SOP knowledge repository; strictly enforced with YAML frontmatter containing **exactly 20 English keywords**. |
| **8** | **🎯 Active Triggers** | `/opt/floworkos/system/triger` | [README.md](file:///opt/floworkos/system/triger/README.md) | Asynchronous background daemon supervisors writing high-priority environmental alerts to `/tmp/flowork_active_trigger.json`. |
| **9** | **📜 Rules & Triggers** | `/opt/floworkos/system/system_promp` | [README.md](file:///opt/floworkos/system/system_promp/README.md) | Master prompt hub & 60+ native compiled Rust rule checkers in `rules/.bin/` linking environmental state to prompt injection. |
| **10** | **💬 Chat History** | `/opt/floworkos/history/chats` | [README.md](file:///opt/floworkos/history/chats/README.md) | Canonical streaming JSONL transcript repository partitioned by workspace namespaces for persistent `--resume` state. |
| **11** | **⚡ Connector** | `/opt/floworkos/connector` | [README.md](file:///opt/floworkos/connector/README.md) | High-performance inference proxy (:9099), multi-account quota shield, and provider routing matrix. |

---

## 4. Key Subsystem Highlights

### A. Sovereign Connector Gateway (:9099)
- **Multi-Account Quota Shield**: Rotates API accounts dynamically with smart 429 cooldowns and zero token interruption.
- **Model Normalization**: Guarantees rock-solid reliability by pinning requests to `gemini-3.8-flash-high`.
- **Multi-Provider Switch**: Seamless routing to Local Ollama GPU or Universal 9Router.

### B. Dynamic Security & Sandboxing
- **5-Tier Policy Hierarchy**: Evaluates tool calls across `Admin > User > Workspace > Extension > Default` scopes.
- **Kernel Landlock LSM**: Hardware-level path restriction preventing unauthorized workspace escapes.
- **Zero Hardcoded Core Tools**: The CLI binary contains empty tool arrays; all tools are discovered dynamically from `/opt/floworkos/tools/`.

### B. Sub-Millisecond Environmental Instincts
- **Formula 5-3-3 Context Routing**: Balances core identity, reactive environmental instincts, and conversation memory.
- **Native Rust Rules**: Over 60 native Rust binaries execute in `< 2ms` total to inspect git status, dirty branches, active processes, and system metrics during prompt assembly.

### C. Multi-User Portability & ISO Zero-Error
- **Decoupled Root Storage**: Runtime artifacts (`screenshots/`, `history/chats/`) reside in `/opt/floworkos/` with universal permissions (`0777`).
- **Zero Broken Paths**: New installations generated from the Flowork OS installer inherit unified bookmarks and settings via `/etc/skel/`.

---

## 5. Quick Start & Operational Commands

### Launching the Autonomous Agent (Mr. Flow)
```bash
# Launch interactive sovereign CLI session
mrflow

# Resume the most recent conversation in the current workspace
mrflow --resume

# Execute a one-shot autonomous task
mrflow -p "Inspect system status and report active daemons"
```

### Desktop Snipping & Screenshots
- **Full Screen Instant Capture**: Press `PrintScreen` (persisted to `/opt/floworkos/screenshots/`).
- **Interactive Snipping Tool**: Press `Shift + PrintScreen` (macOS-style preview popup with instant copy and open).

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
```

---

## 6. Codebase Discipline & Invariants

All contributors, engineers, and autonomous subagents must adhere to the following invariants:
1. **Strict Technical English**: All codebase files, manifests, prompts, skills, policies, and documentation must be authored strictly in professional technical English.
2. **Canonical Naming**: Exactly one lowercase `README.md` per folder. Duplicate uppercase `README.MD` files are strictly forbidden.
3. **No Internal Symlinks**: All assets inside `/opt/floworkos/` must be physical directories and files; symlinks inside `/opt/floworkos/` are prohibited.
4. **Sacred Locks**: Lines protected by `@lock` or `@freez` markers must never be modified or removed.

---

*Flowork OS — The Sovereign Operating System for Autonomous Human-Machine Synergy.*
