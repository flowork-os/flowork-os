# 👑 FLOWORK OS — SOVEREIGN CODE REVIEW ENGINE ROADMAP
*Document: open_code_review_integration_roadmap.md*
*Component: Flowork Sovereign OpenCodeReview (`ocr`) Integration across Flowork OS*
*Version: 1.0.0 — Timestamp: 2026-11-10 — Target: Eust Kernel / Flowork OS*

---

## 🎯 EXECUTIVE SUMMARY & CORE MISSION
`flowork-os/open-code-review` (`ocr`) provides an enterprise-tested, hybrid deterministic AST + LLM code review architecture. By delegating repository traversal, diff parsing, and reflection verification to compiled Go pipelines, it reduces LLM token consumption to **~1/9th of standard agents** while guaranteeing zero line drift on review comments.

This roadmap articulates the end-to-end integration of `ocr` into Flowork OS across **4 Evolutionary Pillars**:
1. **Pillar 1:** Native Tool & Sovereign Connector Routing (`/opt/floworkos/bin/ocr` + `:9099`)
2. **Pillar 2:** Sovereign Pre-Push Anti-Slop & Quality Gate (`upload-flowork-os.sh` + pre-commit)
3. **Pillar 3:** Dual-Agent Adversarial Loop (Red Team OCR vs Blue Team Mr. Flow)
4. **Pillar 4:** `reviewflow` Standalone Quantum Glass Desktop Review Studio

---

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      OCR SOVEREIGN INTEGRATION CAPABILITY MATRIX                       │
├──────────────────────────────┬─────────────────────────────┬───────────────────────────┤
│ PILLAR                       │ ESTIMATED HORIZON           │ IMPACT / OPERATIONAL VALUE│
├──────────────────────────────┼─────────────────────────────┼───────────────────────────┤
│ 1. Native Tool & Gateway     │ Phase 1 (1 Day)             │ Instant Line-Level Review │
│ 2. Pre-Push Anti-Slop Gate   │ Phase 1 (1-2 Days)          │ Zero-Defect Upstream Push │
│ 3. Dual-Agent Adversarial    │ Phase 2 (2-3 Days)          │ Autonomous Self-Correction│
│ 4. `reviewflow` Desktop App  │ Phase 3 (3-4 Days)          │ Local CodeRabbit Rival    │
└──────────────────────────────┴─────────────────────────────┴───────────────────────────┘
```

---

## ⚡ PILLAR 1: NATIVE TOOL & SOVEREIGN CONNECTOR ROUTING
### 1. Architectural Strategy
Embed the compiled `ocr` engine directly into `/opt/floworkos/bin/ocr` and configure its backend provider to route through the local **Sovereign Connector (`http://127.0.0.1:9099`)**. This allows `ocr` to tap into multi-account Google Gemini CloudCode pools or local Ollama (Qwen2.5-Coder / DeepSeek) without external SaaS subscriptions or API leaks.

### 2. IPC & Execution Pipeline
```
Mr. Flow / CLI / Script
  │
  ├─► Calls: ocr review --audience agent --diff-only
  │
  ├─► Environment:
  │     OPENAI_BASE_URL="http://127.0.0.1:9099/v1"
  │     OPENAI_API_KEY="flowork-sovereign"
  │     OCR_MODEL="gemini-3.8-flash"
  │
  ▼
Sovereign OCR Engine (Go Pipeline):
  ├─ [1] Deterministic Git Diff extraction & AST chunking (1/9th token load)
  ├─ [2] Line-level positioning & reflection check (Zero-drift validation)
  ├─ [3] Query dispatched to Sovereign Gateway (:9099)
  │
  ▼
Sovereign Gateway (:9099):
  ├─ Dispatches to Gemini Pool or local Ollama
  ├─ Emits structured JSON findings (severity, file, line, rule, suggestion)
```

### 3. Implementation Steps
* **Phase 1.1 (Engine Embedding):**
  - Download or compile release binary for `x86_64` Linux to `/opt/floworkos/bin/ocr`.
  - Enforce `chmod +x /opt/floworkos/bin/ocr`.
  - Validate binary integrity with `file /opt/floworkos/bin/ocr`.
* **Phase 1.2 (Sovereign Tool Foundry Packaging):**
  - Synthesize native tool `/opt/floworkos/tools/code_review_audit/`:
    - `manifest.json`: Triggers on keywords `["code_review", "diff_audit", "pr_review", "ocr", "lint_review"]`.
    - `run.py`: Standardized stdin/stdout JSON wrapper executing `ocr review`.
* **Phase 1.3 (Empirical Verification):**
  - Execute `/opt/floworkos/bin/ocr --version` returning Exit Code 0.
  - Review an active Git diff against `:9099` mock verifying valid JSON output.

---

## 🛡️ PILLAR 2: SOVEREIGN PRE-PUSH ANTI-SLOP & QUALITY GATE
### 1. Architectural Strategy
Upgrade the distribution script (`/home/awenk/Downloads/upload-flowork-os.sh`) and local developer git repos with an automated **Quality Gate Stage**. Before any commit or remote push to `flowork-os/flowork-os`, `ocr` evaluates the diff against strict Flowork OS invariants.

### 2. Enforced Rules & Invariants
1. **Zero Secret Leakage:** Detect hardcoded API tokens, JWTs, private keys, and `vault.json` additions.
2. **Anti-Slop & Clean Architecture:**
   - Detect hardcoded home paths (`/home/awenk`, `/home/user`) in system-wide scripts.
   - Detect synchronous/blocking GUI launches that violate Detached Spawning Laws.
   - Detect unhandled exceptions in daemon event loops.
3. **AST Safety Checks:**
   - Detect Null Pointer Dereferences, race conditions, and un-sanitized subprocess shell calls.

### 3. Workflow Integration in `upload-flowork-os.sh`
```bash
# STAGE 3.5: Sovereign Open-Code-Review Audit
echo -e "[STAGE 3.5] Running Flowork Sovereign OpenCodeReview (AST + Security)..."
OCR_REPORT=$(/opt/floworkos/bin/ocr review --audience cli --staged --severity high,critical || true)
if echo "$OCR_REPORT" | grep -E "CRITICAL|BLOCKER"; then
    echo -e "[FATAL] Critical code quality or security vulnerability detected by OCR:"
    echo "$OCR_REPORT"
    exit 1
fi
echo -e "✓ Open-Code-Review Audit Passed (Zero Blocker Vulnerabilities)."
```

---

## 🔄 PILLAR 3: DUAL-AGENT ADVERSARIAL LOOP (RED TEAM VS BLUE TEAM)
### 1. Architectural Strategy
Transform Mr. Flow's autonomous app synthesis and bugfixing into an **Adversarial Self-Healing Loop**:
* **Blue Team (Mr. Flow):** Implements code, layouts, and system repairs.
* **Red Team (OCR Sentinel):** Interrogates the modified diff, identifying logic gaps, edge cases, and styling bugs.

### 2. Closed-Loop Data Flow
```
User Requests Feature / Bugfix
  │
  ▼
Mr. Flow (Blue Team):
  ├─ Generates or modifies source files (e.g. apps/crypto-radar/ui/index.html)
  ├─ Verifies structural syntax
  │
  ▼
Adversarial OCR Gate (Red Team):
  ├─ Executes: ocr review --audience agent --diff-against HEAD~1
  ├─ Emits structured issue list:
  │    - Issue #1: "Missing error handling on WebSocket disconnect"
  │    - Issue #2: "Color literal '#112233' violates Sovereign Root Token Law"
  │
  ▼
Autonomous Self-Refinement:
  ├─ If issues found: Mr. Flow automatically applies surgical patches via replace
  ├─ Re-runs craft-app test <app_id>
  │
  ▼
Final Delivery to User:
  └─ Labeled: "Verified & Hardened by Dual-Agent OCR Audit"
```

### 3. Implementation Steps
* Author passive trigger prompt: `/opt/floworkos/system/system_promp/promps/triggers/adversarial_code_review.md`.
* Register in `triggers.json` to activate during `craft_app`, `app_synthesis`, and refactoring tasks.

---

## 🖥️ PILLAR 4: `reviewflow` STANDALONE QUANTUM GLASS DESKTOP APP
### 1. Architectural Strategy
Synthesize a native Flowork OS desktop application: **`reviewflow`** (`/opt/floworkos/apps/reviewflow/`). It acts as a local, private, sovereign competitor to commercial SaaS tools (CodeRabbit, Bito, Cursor PR Review).

### 2. Key Features & Visual Design
* **Aesthetic Standard:** Sovereign Quantum Glass (0.60 opacity, Obsidian neutral `#080c10`, Matrix Green `#00ff66` and Cyan `#00f2fe` accents, JetBrains Mono font).
* **Repository & Branch Selector:** One-click directory picker to load any local Git repository.
* **Diff Visualizer:** Split or unified view with color-coded additions, deletions, and AST token highlights.
* **One-Click Autonomous Review:**
  - Fast Mode (AST Deterministic rules only, <200ms, 0 tokens).
  - Deep AI Review (Go AST + Gemini Flash / Ollama DeepSeek via port :9099).
* **Interactive Line Annotations:**
  - Expandable suggestion cards attached to the exact line of code.
  - "Apply Fix" button that immediately patches the file on disk.

### 3. Desktop Integration
* Register desktop entry: `/usr/share/applications/reviewflow.desktop`.
* Add launcher icon: `/opt/floworkos/icons/reviewflow.png`.
* Register in Flowork Launchpad (Orbit Deck).

---

## 📅 EXECUTION TIMELINE & ACCEPTANCE MILESTONES

| Milestone | Deliverables | Verification Metric |
| :--- | :--- | :--- |
| **Milestone 1** | Binary embedding & Sovereign Connector :9099 routing | `ocr --version` and API ping return Exit Code 0 |
| **Milestone 2** | `code_review_audit` tool registered in Flowork OS | Tool execution via `run.py` parses git diff accurately |
| **Milestone 3** | Pre-Push Security & Quality Hook in `upload-flowork-os.sh` | Clean commits pass; intentional security flaws trigger hard abort |
| **Milestone 4** | Dual-Agent Adversarial trigger in Mr. Flow's prompt engine | Mr. Flow auto-remediates review findings in single turn |
| **Milestone 5** | `reviewflow` GUI synthesized and tested via `craft-app` | Headless WebKit test and interactive desktop launch Exit Code 0 |
