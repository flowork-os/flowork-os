# ZERO-NODE PURE RUST SYSTEM CORE DOCTRINE

## 1. Context & Activation Scope
Triggered when developing, modifying, packaging, or auditing Flowork OS core daemons, CLI binaries, decoupled tools, MCP backends, skills, or ISO builds (`flowork-core-rs`, `connector-rs`, `mrflow-rs`, `flowork-browser-mcp`, `agent-browser`, `agent-desktop`, `zero_node`).

## 2. Mandatory Behavioral Invariants
- **Pure Rust Native Executables:** Core OS daemons, tool runners, linters, and MCP backends reside in native Rust crates (`/opt/floworkos/crates/flowork-core-rs/`, `/opt/floworkos/connector-rs/`, `/opt/floworkos/mrflow-rs/`, `/opt/floworkos/sysd/`, `/opt/floworkos/wm/`) compiled to release ELFs.
- **Verified Native Binaries:** Decoupled system binaries run directly via `/opt/floworkos/bin/flowork-*`, `/opt/floworkos/connector/bin/flowork-connector`, `/opt/floworkos/tools/browser_backend/flowork-browser-mcp`, and `/usr/local/bin/agent-{browser,desktop,desktop-linux-clipboard-owner}`.
- **Python Stdlib Scripting:** Non-compiled orchestration scripts (`last30days`, Foundry, QC suites, GUI controllers) execute strictly on Python 3 stdlib/installed packages or Bash without Node.js dependencies.
- **Browser Frontend Boundary:** Only browser-executed webviews, WebKit UIs, Chromium extensions, and Tauri web assets remain JavaScript/TypeScript.

## 3. Strict Prohibitions
- NEVER require `node`, `npm`, `npx`, `corepack`, `/usr/lib/node_modules`, or legacy `.js` runners (`run.js`, `discovery.js`, `executor.js`, `lint_skills.js`) inside system core services or CLI paths.
- NEVER link or copy external third-party runtimes over native Rust ELFs during packaging.
