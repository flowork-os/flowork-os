# 👑 FLOWORK OS — SOVEREIGN EVOLUTION ROADMAP (PILLARS 1 - 4)
*Document Version: 1.0.0 — Timestamp: 2026-11-09*
*Target Architecture: Linux 7.3.0-flowork-rust (Eust Kernel) | Desktop: Quantum Glass & Orbit Deck*

---

## 🎯 EXECUTIVE SUMMARY & CORE MISSION
Flowork OS has achieved core independence with its native Rust Eust Kernel, Landlock LSM containment, Content-Addressable Delta OTA updates, the Cross-App Neural Pipeline (flowork-pipe), the Application Remix Engine (flowpkg remix), and Multimodal Screen Memory (flowfs-core).

This roadmap defines the concrete architectural execution plan for the next **4 Strategic Evolution Pillars**:
1. **Pillar 1:** GUI "Remix with Mr. Flow" Integration (Orbit Deck & Launchpad)
2. **Pillar 2:** Spotlight Visual Search & Historical Screen Memory UI (Ctrl+Space)
3. **Pillar 3:** Real Autonomous Crash-to-Fix Loop (Kernel & Process Sentinel)
4. **Pillar 4:** Embedded Offline SLM in sysd (Air-Gapped Zero-Cloud Mode)

---

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        FLOWORK OS SOVEREIGN CAPABILITY MATRIX                          │
├──────────────────────────────┬─────────────────────────────┬───────────────────────────┤
│ PILLAR                       │ ESTIMATED HORIZON           │ IMPACT / VALUE            │
├──────────────────────────────┼─────────────────────────────┼───────────────────────────┤
│ 1. GUI App Remix Integration │ Sprint 4 (1-2 Days)         │ Instant JIT UI Customizer │
│ 2. Spotlight Screen Memory   │ Sprint 4 (2-3 Days)         │ Omnipresent Visual Recall │
│ 3. Autonomous Crash-to-Fix   │ Sprint 5 (3-4 Days)         │ Self-Healing Resilience   │
│ 4. Embedded Offline SLM sysd │ Sprint 5-6 (5-7 Days)       │ 100% Air-Gapped Sovereign │
└──────────────────────────────┴─────────────────────────────┴───────────────────────────┘
```

---

## 🛠️ PILLAR 1: GUI "REMIX WITH MR. FLOW" INTEGRATION
### 1. Strategic Context & Operational Value
`flowpkg remix <app_id>` currently runs smoothly in the CLI, allowing developers to inspect components, inject directives into `REMIX_NOTES.md`, and re-test apps. 
**Pillar 1** brings this power directly to the desktop user interface. Any user can right-click an app icon anywhere (Orbit Deck, Plank Dock, or Whisker Start Menu) and select **"🛠️ Remix with Mr. Flow"**, immediately opening Mr. Flow's Focused Execution Stage with the target app's source code, component hierarchy, and an interactive prompt to modify styling, layouts, or logic in real time.

### 2. Technical Architecture & Data Flow
```
User Right-Clicks App Icon (e.g. Crypto Radar)
  │
  ├─► Selects Desktop Action: "Remix with Mr. Flow"
  │
  ├─► Triggers: /usr/local/bin/flowork-launch remix <app_id>
  │
  ├─► Dispatches Event over UNIX Domain Socket: /tmp/mrflow-sidebar-*.sock
  │     Payload: { "action": "open_remix", "app_id": "crypto-radar" }
  │
  ▼
Mr. Flow Sidebar HUD:
  ├─ [1] Sets document.body class "in-stage-mode"
  ├─ [2] Spawns #executionFocusStage with Quantum Glass Remix Canvas
  ├─ [3] Displays live UI files (ui/index.html) and Logic files (bin/app.py)
  ├─ [4] Prompts user for natural language directive:
  │       "Misal: Ubah tema warna jadi neon violet, tambah indikator RSI"
  │
  ▼
Execution Loop:
  ├─ Mr. Flow applies surgical code modification via replace
  ├─ Executes craft-app test <app_id> (headless WebKit validation)
  ├─ If Exit Code 0: Hot-reloads the running app window via IPC signal
```

### 3. Step-by-Step Implementation Plan
* **Phase 1.1 (Desktop Action Registration):**
  - Update `/opt/floworkos/bin/flowpkg` and `/opt/floworkos/bin/craft-app register` to inject desktop actions into generated `.desktop` files:
    ```ini
    Actions=Remix;
    [Desktop Action Remix]
    Name=🛠️ Remix with Mr. Flow
    Exec=/opt/floworkos/bin/flowork-launch --remix %u
    ```
* **Phase 1.2 (Launcher & Socket Forwarder):**
  - Enhance `/opt/floworkos/bin/flowork-launch` to support `--remix <app_id>`:
    - Verifies app existence in `/opt/floworkos/apps/<app_id>`.
    - Connects to `/tmp/mrflow-sidebar-*.sock` and pushes `open_remix_session` event.
    - If Mr. Flow sidebar is hidden, auto-expands the sidebar via `xdotool` or `flowork-sysd`.
* **Phase 1.3 (Sidebar Visual Remix Stage):**
  - Add `renderRemixStage(appId, appMeta)` in sidebar JS:
    - Renders glass visualizer cards with component chips (`HTML`, `CSS`, `JS`, `Py`).
    - Provides a one-click "Test & Preview" and "Apply Changes" button.

### 4. Empirical Verification & Acceptance Test
- Right-click `crypto-radar` in application launcher -> Click "Remix with Mr. Flow".
- Verify Mr. Flow sidebar opens to the remix canvas within `<300ms`.
- Apply sample directive: *"Ganti title bar warna cyan"* -> Verify `craft-app test crypto-radar` returns Exit Code 0 and window hot-reloads.

---

## 👁️ PILLAR 2: SPOTLIGHT VISUAL SEARCH & SCREEN MEMORY UI
### 1. Strategic Context & Operational Value
FlowFS currently indexes screen captures via `flowfs_core.py` and supports vector searches via `flowfs-search --screen "<query>"` with sub-millisecond latency (~0.38ms).
**Pillar 2** exposes this capability directly through the global desktop Spotlight search bar (`Ctrl+Space` or Orbit Deck HUD). Users can type `? <intent>` to instantly retrieve historical screenshots, window titles, and contextual activities from days or weeks prior.

### 2. Technical Architecture & Data Flow
```
User Presses Ctrl + Space ──► Orbit Spotlight Overlay Appears
  │
  ├─ User types: "? codingan rust thread pool" (Prefixed with '?' or toggles Screen Tab)
  │
  ├─ Spotlight frontend calls: /opt/floworkos/bin/flowfs-search --screen "rust thread pool" --json
  │     (Response returned in < 25ms with top 5 visual matches)
  │
  ▼
Spotlight UI Rendering:
  ├─ Grid View of Screenshot Thumbnails (Aspect-ratio preserved cards)
  ├─ Overlaid Glass Badges:
  │    - Relative timestamp (e.g., "Tadi pagi 09:42", "2 hari lalu")
  │    - Active Window Title & App Class (e.g., "kernel.rs — VS Code")
  │    - Match confidence percentage (e.g., "Match: 89%")
  │
  ▼
User Actions:
  ├─ Hover: Enlarged high-resolution lightbox preview
  ├─ Click: Opens full screenshot in Photocraft / Viewer
  └─ Enter: Copies captured file path or window title to clipboard
```

### 3. Step-by-Step Implementation Plan
* **Phase 2.1 (Spotlight Query Routing):**
  - Update Orbit Spotlight (`apps/flowork-launchpad` / spotlight GUI):
    - Add regex detector: if input starts with `?` or user clicks the **"👁️ Screen Memory"** filter pill, divert query from application launcher to `flowfs-search --screen`.
* **Phase 2.2 (Thumbnail Generation & Caching):**
  - In `flowfs_core.py`, when `index_screen_capture()` is called:
    - Generate a fast 320px WebP thumbnail saved at `/opt/floworkos/screenshots/thumbs/<hash>.webp` using Pillow or image tools.
    - Store `thumbnail_path` in `flow_screen_memory` table.
* **Phase 2.3 (Lightbox & Viewer Integration):**
  - In the Spotlight result card, implement keyboard navigation (Arrow keys + Enter).
  - Pressing `Space` triggers an instant quick-look modal displaying the full DRM frame capture.

### 4. Empirical Verification & Acceptance Test
- Run `flowork-ambient-eye` to capture current workspace.
- Press `Ctrl+Space` -> Type `? terminal mrflow`.
- Verify Spotlight displays visual cards with accurate thumbnail, timestamp, and match percentage > 30% within `<50ms`.

---

## 🛡️ PILLAR 3: REAL AUTONOMOUS CRASH-TO-FIX LOOP (SENTINEL)
### 1. Strategic Context & Operational Value
Currently, `self_healing_sentinel` only performs ping checks against ports 18090 and 9099.
**Pillar 3** upgrades Flowork OS to an autonomous self-healing operating system. When any userland application, Craft app, or system daemon segfaults (SIGSEGV / Exit Code 139), throws uncaught JS exceptions, or triggers a kernel Landlock violation, the **Kernel Sentinel Daemon** intercepts the crash, extracts the exact stack trace and failing file, and engages Mr. Flow to test and apply an autonomous hotfix or rollback without requiring user intervention.

### 2. Technical Architecture & Data Flow
```
App Crash Event Occurs (e.g. Cutvii crashes due to null pointer / uncaught JS exception)
  │
  ├─ System Event Intercept:
  │    - Watcher 1: Linux Kernel Ring Buffer (/dev/kmsg) for segfault traps
  │    - Watcher 2: systemd-coredump journal stream via SD-Journal API
  │    - Watcher 3: Neural Bus process.crashed emission
  │
  ▼
Kernel Sentinel Engine (/opt/floworkos/sysd/src/sentinel.rs):
  ├─ Extracts: PID, Executable Path, Exit Code, Signal (e.g. SIGSEGV 11), Crash Dump
  ├─ Compiles Incident Payload:
  │    {
  │       "target_app": "cutvii",
  │       "file_path": "/opt/floworkos/apps/cutvii/src-tauri/src/main.rs",
  │       "stack_trace": "...",
  │       "crash_time": "..."
  │    }
  │
  ▼
Autonomous Triage Loop:
  ├─ Sentinel dispatches task to Mr. Flow Subagent (kernel_sentinel / triage_agent)
  ├─ Mr. Flow:
  │    1. Inspects failing source file via read_file
  │    2. Checks recent git diff or OTA update history
  │    3. If transient bug: applies surgical fix via replace
  │    4. Executes headless validation: craft-app test <app> or cargo check
  │    5. PASS? ──► Restarts app seamlessly & displays desktop notification:
  │                 "✓ Cutvii encountered crash; Mr. Flow applied autonomous hotfix."
  │    6. FAIL? ──► Executes flowork-rollback <app> to last known good snapshot.
```

### 3. Step-by-Step Implementation Plan
* **Phase 3.1 (Native Rust Sentinel Watcher in sysd):**
  - Implement `sysd/src/crash_watcher.rs`:
    - Uses non-blocking polling on `/proc/sys/kernel/core_pattern` or systemd journal socket.
    - Filters events belonging exclusively to `/opt/floworkos/apps/` and system binaries.
* **Phase 3.2 (Incident Payload Dispatcher):**
  - Posts incident report to local Neural Bus topic `system.crash.incident`.
* **Phase 3.3 (Autonomous Remediation Subagent):**
  - Author `/opt/floworkos/tools/crash_remediator/run.py`:
    - Parses traceback, isolates offending line, generates patch candidate.
    - Staged verification in Landlock sandbox before touching production binary.
    - If tests fail 3 times, triggers atomic rollback via `/opt/floworkos/bin/flowork-rollback`.

### 4. Empirical Verification & Acceptance Test
- Intentionally inject a syntax/runtime error into a mock app (e.g. `mock_crash_app`).
- Launch `mock_crash_app` and trigger segfault/crash.
- Observe Sentinel intercept within `<500ms`, witness Mr. Flow isolate the trace, apply fix, and re-launch app successfully with Exit Code 0.

---

## 🧠 PILLAR 4: EMBEDDED OFFLINE SLM IN `sysd` (AIR-GAPPED MODE)
### 1. Strategic Context & Operational Value
Today, Mr. Flow relies on the Sovereign Connector (:9099) routed to Google CloudCode pool or an external Ollama daemon.
**Pillar 4** establishes absolute offline sovereignty. By embedding a high-performance, quantized Small Language Model (SLM, 1.5B–3B parameters like *Qwen2.5-Coder-1.5B-Instruct* or *SmolLM2-1.7B*) directly into the native Rust `sysd` daemon, Flowork OS can understand natural language intents, route desktop tasks, and synthesize shell pipelines even if physical network interfaces are severed.

### 2. Technical Architecture & Data Flow
```
Network State: Disconnected (No Internet, Connector CloudCode Quota Exhausted)
  │
  ▼
User Input in Terminal / Sidebar:
  "mrflow cari file pdf laporan keuangan di folder download lalu pindahin ke arsip"
  │
  ▼
sysd Routing Decision Gateway (sysd/src/inference_router.rs):
  ├─ [1] Probes Connector (:9099) health & cloud connectivity.
  ├─ [2] If DOWN / OFFLINE ──► Automatically switches to Embedded Rust Engine.
  │
  ▼
Native Rust SLM Engine (sysd/src/embedded_slm.rs):
  ├─ Powered by Candle (Hugging Face pure Rust ML framework) or llama-cpp-sys bindings
  ├─ Model: Qwen2.5-Coder-1.5B-Instruct.Q4_K_M.gguf (~1.1 GB in /opt/floworkos/models/)
  ├─ Acceleration: CPU AVX2/NEON + Vulkan Compute Shader (Zero CUDA/Nvidia lock-in)
  │
  ▼
Execution & Tool Dispatch:
  ├─ Extracts structured JSON tool call:
  │    { "tool": "run_shell_command", "command": "find ~/Downloads -name '*.pdf' -exec mv {} ~/Archive/ \\;" }
  ├─ Executes via Landlock sandbox
  └─ Returns result to user terminal in < 1.5 seconds.
```

### 3. Step-by-Step Implementation Plan
* **Phase 4.1 (Rust ML Engine Integration):**
  - Add `candle-core = "0.7"` and `candle-transformers = "0.7"` (or `llama-cpp-2`) to `/opt/floworkos/sysd/Cargo.toml`.
  - Feature flag: `[features] embedded-slm = []` to maintain modular compile times.
* **Phase 4.2 (Model Quantization & Local Storage):**
  - Store model weights at `/opt/floworkos/models/qwen2.5-coder-1.5b-q4.gguf`.
  - Implement memory-mapped (`mmap`) loading for instantaneous zero-copy startup (<150ms).
* **Phase 4.3 (JIT Fallback Gateway):**
  - Implement fallback in `/opt/floworkos/connector/`: if cloud API returns 429/timeout or network is offline, seamlessly divert prompt payload to `http://127.0.0.1:18090/v1/chat/completions`.

### 4. Empirical Verification & Acceptance Test
- Disable networking (`sudo ip link set lo up; sudo ip link set dev eth0 down; sudo ip link set dev wlan0 down`).
- Execute CLI: `mrflow "list semua file python di /opt/floworkos/connector"`.
- Verify response generated entirely by embedded `sysd` SLM with Exit Code 0 and zero cloud calls.

---

## 📅 TIMELINE & ROADMAP EXECUTION SCHEDULE
```
Sprint 4 (Current Horizon):
  ├─ [Milestone 4.1] Complete Pillar 1: GUI App Remix Integration in Launchpad & .desktop
  └─ [Milestone 4.2] Complete Pillar 2: Spotlight Screen Memory UI with Thumbnail Cache

Sprint 5 (Resilience & Self-Healing):
  ├─ [Milestone 5.1] Complete Pillar 3: Kernel Sentinel Core Dump Interceptor & Auto-Fix Loop
  └─ [Milestone 5.2] Integrate Crash Remediation Subagent with Btrfs/Tar Snapshot Rollback

Sprint 6 (Ultimate Kedaulatan / Air-Gapped Autonomy):
  ├─ [Milestone 6.1] Integrate Candle/GGML embedded inference inside sysd
  ├─ [Milestone 6.2] Benchmark CPU/Vulkan token-per-second performance (Target: >25 tok/s)
  └─ [Milestone 6.3] Full End-to-End Air-Gapped OS Verification Pass
```

---
*Generated autonomously by Mr. Flow (Flowork OS Sovereign Agent)*
*Approved for system deployment.*
