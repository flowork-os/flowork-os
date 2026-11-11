# ⚡ Flowork Sovereign Connector (`flowork-connector`)

> **Authoritative Architecture Specification, Operational Guide, and Multi-Provider Switchboard**  
> *Release Version:* 2.18 (Sovereign Dual-Protocol Inference Gateway)  
> *Canonical System Root:* `/opt/floworkos/connector`  
> *Default Port:* `9099` (HTTP / SSE / WebSocket)  
> *Embedded Web GUI:* `http://127.0.0.1:9099/gui`  

---

## 1. Executive Overview

**Flowork Sovereign Connector** (`flowork-connector`) is an ultra-low-latency local inference gateway engineered natively for **Flowork OS**. It bridges native OS agent clients (Mr. Flow CLI, Mr. Flow Companion Sidebar, Antigravity IDE, Cursor, Continue, Roo Code, Cline) with heterogeneous AI inference providers—including high-speed Google CloudCode accounts, local offline Ollama models, and universal OpenAI-compatible gateways (9Router, OpenRouter).

### Core Architecture Highlights
- **Universal Dual-Protocol Translation**: Bi-directionally bridges the **Google Generative AI API** (`/v1beta/models/*:generateContent` and `:streamGenerateContent`) with standard **OpenAI API** formats (`/v1/chat/completions` with SSE streams).
- **Multi-Account Quota Rotator**: Dynamically rotates authenticated Google Pro accounts upon encountering HTTP `429 Quota Exceeded`, applying cooldown algorithms to eliminate downtime.
- **Local Model Optimization**: Built-in JIT prompt condensation and fast-path classifier routing specifically designed to allow local models on CPU or GPU to operate with sub-second responsiveness without triggering 60-second fetch timeouts.
- **Thought Stream Isolation**: Automatically parses DeepSeek and Qwen reasoning deltas (`d.reasoning` / `reasoning_content`) and projects them as `{ thought: true, text: ... }` for clean rendering in Mr. Flow's Thinking Cards.
- **Embedded Web GUI & REST API**: Live dashboard at `/gui` for instant provider switching, real-time quota telemetry, and account health monitoring.

---

## 2. Architecture & Request Pipeline

```text
       ┌─────────────────────────────────────────────────────────────┐
       │             CLIENT LAYER (Mr. Flow & IDE Ecosystem)         │
       │   Mr. Flow Sidebar  │  Mr. Flow CLI  │  Cursor  │  Cline    │
       └──────────────────────────────┬──────────────────────────────┘
                                      │ HTTP Request (:9099)
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │             FLOWORK SOVEREIGN CONNECTOR (:9099)             │
       │                                                             │
       │  ┌───────────────────────┐    ┌──────────────────────────┐  │
       │  │ Fast-Path Classifier  │    │ JIT Prompt Condenser     │  │
       │  │ (Sub-ms Rust JSON)    │    │ (Stripped <session_ctx>) │  │
       │  └───────────┬───────────┘    └────────────┬─────────────┘  │
       │              │                             │                │
       │              ▼                             ▼                │
       │  ┌───────────────────────────────────────────────────────┐  │
       │  │ Protocol Router & Model Switchboard                   │  │
       │  │ Resolves: Google Pool vs Local Ollama vs 9Router      │  │
       │  └──────────────────────────┬────────────────────────────┘  │
       │                             │                               │
       │        ┌────────────────────┼───────────────────┐           │
       │        ▼                    ▼                   ▼           │
       │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
       │  │ CloudCode PA │    │ Local Ollama │    │ 9Router /    │   │
       │  │ Rotator Pool │    │ GPU/CPU Bridge│   │ OpenAI Proxy │   │
       │  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘   │
       └─────────┼───────────────────┼───────────────────┼───────────┘
                 ▼                   ▼                   ▼
       ┌──────────────────┐  ┌───────────────┐   ┌───────────────────┐
       │ Google CloudCode │  │ Ollama Engine │   │ External Gateway  │
       │ Endpoint (:443)  │  │ Local (:11434)│   │ (api.9router.com  │
       └──────────────────┘  └───────────────┘   │ or local :20128)  │
                                                 └───────────────────┘
```

---

## 3. How to Connect & Configure Ollama

The Sovereign Connector seamlessly translates Mr. Flow's internal Google Gemini calls into OpenAI-compatible requests for an optional local Ollama daemon.

### Step 1: Ensure Ollama is Running
Verify that an Ollama daemon is active on port `11434` (`ollama` must be installed if using local GPU/CPU inference):
```bash
# Check daemon status
curl -s http://127.0.0.1:11434/api/tags

# If installed and not running, start the system Ollama service
ollama serve
```

### Step 2: Download or Verify Local Models
Ensure you have pulled your desired models into Ollama:
```bash
# Lightweight model (Recommended for CPU-only systems: ultra-fast, ~3s latency)
ollama pull qwen2.5-coder:1.5b

# Medium model (Balanced for GPU or fast multi-core CPUs)
ollama pull qwen2.5-coder:7b

# Deep reasoning model (Recommended for NVIDIA GPU acceleration)
ollama pull deepseek-v4-9b-uncensored:latest
```

List installed models:
```bash
ollama list
```

### Step 3: Switch Active Provider to Ollama
You can switch the Sovereign Connector to route all agent traffic to Ollama using any of the following methods:

#### Method A: Via REST API / Terminal (Fastest)
Send an HTTP POST request to the provider configuration endpoint:
```bash
curl -X POST http://127.0.0.1:9099/auth/router/provider-config \
  -H "Content-Type: application/json" \
  -d '{
    "active_provider": "ollama",
    "ollama": {
      "host": "http://127.0.0.1:11434",
      "default_model": "deepseek-v4-9b-uncensored:latest"
    }
  }'
```

#### Method B: Via Embedded Web GUI
1. Open `http://127.0.0.1:9099/gui` in your browser.
2. Under **Inference Providers**, select **Ollama Local Engine**.
3. Choose your default model from the dropdown.
4. Click **Apply Changes**.

#### Method C: Via Mr. Flow Companion Sidebar
1. Open the sidebar (press `Super+C` or click the glowing edge handle).
2. Click the model pill badge in the top navigation header.
3. Select **DeepSeek 9B** or **Qwen 2.5 Coder**. The switch takes effect immediately.

---

## 4. Local Model Optimization: Anti-Freeze & Anti-Timeout Architecture

When standard agent frameworks connect to local LLMs on CPU, they frequently experience **endless spinning, UI freezes, or fetch timeouts** due to prompt bloat and slow inference. Flowork OS solves this in Pure Rust (`connector-rs/src/translator.rs` & `connector-rs/src/providers.rs`):

### 1. JIT Prompt Condensation
- **The Problem**: Full agent turns include `<session_context>` metadata and large system instructions that take excessive prefill time on CPU-only inference.
- **The Solution**: When routing to Ollama (`is_local = true`), `gemini_to_openai` replaces verbose `<session_context>...</session_context>` blocks with a compact one-line OS descriptor and condenses the system prompt to essential Mr. Flow identity rules.

### 2. Fast-Path Pre-Turn Classifier
- **The Problem**: Internal non-streaming pre-turn classification calls (`generateContent` without streaming) add 40+ seconds of extra inference latency on CPU models.
- **The Solution**: `handle_ollama_request` (`connector-rs/src/providers.rs`) intercepts non-streaming `generateContent` calls and synthesizes a direct `serde_json` response (`complexity_reasoning: "Direct query"`, `complexity_score: 1`, `category: 0`, `status: "ok"`) in sub-millisecond Rust, allowing immediate streaming execution.

### 3. Reasoning Stream Isolation (`thought: true`)
- **The Problem**: Reasoning models output thoughts in `d.reasoning` / `reasoning_content` or `<think>` blocks that clutter chat responses if emitted verbatim.
- **The Solution**: `OpenAiToGeminiState` tags reasoning tokens as `{ thought: true, text: ... }`, isolating them cleanly into Thinking UI cards.

### 4. Context Window Tuning
- Ollama payloads default to `options: { "num_ctx": 8192 }` inside `handle_ollama_request` to prevent memory pressure on host CPU/VRAM.

---

## 5. Model Selection Guide (CPU vs GPU)

| Hardware | Recommended Model | Latency | Memory / VRAM | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **CPU Only (Default)** | `qwen2.5-coder:1.5b` | **3–5 seconds** | ~1.5 GB RAM | Extremely responsive, zero timeout risk on CPU. |
| **CPU (Deep Reasoning)** | `deepseek-v4-9b-uncensored:latest` | **30–45 seconds** | ~8.0 GB RAM | Deep reasoning; requires prompt condensation. |
| **NVIDIA GPU (CUDA)** | `deepseek-v4-9b-uncensored:latest` | **1–2 seconds** | ~6.5 GB VRAM | High-speed local inference with full GPU acceleration. |
| **Cloud (Zero CPU load)** | `gemini-3.8-flash-high` | **1–2 seconds** | 0 MB Local | Multi-account rotation pool via Google CloudCode. |

---

## 6. Verification & Health Probes

Verify the Sovereign Connector runtime using standard terminal commands:

```bash
# 1. Test Connector Health
curl -s http://127.0.0.1:9099/health
# Output: {"online":true,"status":"ok"}

# 2. Inspect Active Router Status, Provider Config & Account Pool Telemetry
curl -s http://127.0.0.1:9099/auth/router/status | head -c 500

# 3. Probe Ollama Bridge Availability (:11434)
curl -s http://127.0.0.1:9099/auth/test/ollama
# Returns {"success":true,"online":true,"models":[...],"count":N} when Ollama is running

# 4. Test Mr. Flow CLI End-to-End through Connector (:9099)
mrflow -p "ping" --skip-trust --approval-mode=sovereign
# Output: Exit Code 0 with immediate sovereign response
```

> **Note:** In addition to port `9099`, `flowork-connector` binds auxiliary local OAuth callback listeners on `127.0.0.1:8080` and `127.0.0.1:51121` for interactive account onboarding.

---

## 7. Directory & File Structure

```text
/opt/floworkos/connector/
├── bin/
│   ├── flowork-connector              <-- Pure Rust Gateway ELF (/opt/floworkos/connector-rs/, symlinked at /usr/local/bin/flowork-connector)
│   ├── mrflow-gui.py                  <-- Desktop switchboard GUI
│   ├── mrflow-router                  <-- Daemon lifecycle launcher
│   └── mrflow-tray-menu.py            <-- System tray provider indicator
├── config/
│   ├── default.json                   <-- Port, host, account limit & cooldown defaults
│   ├── models.json                    <-- Model aliases & catalog definitions (`default_model`)
│   ├── network.json                   <-- Upstream host, user-agent & retry policies
│   ├── providers.json                 <-- Provider endpoints, failover order & defaults
│   └── settings.json                  <-- Runtime gateway settings (`single_model_lock`, cache)
├── data/
│   ├── vault.json                     <-- Protected OAuth account pool, Flowork token & active provider state
│   └── vault.clean.json               <-- Clean sanitized vault template for ISO mastering
├── gui/                               <-- Embedded glass switchboard web assets (embedded fallback + disk override)
├── flowfs_core.py                     <-- FlowFS SQLite vector index & ambient screen memory core
├── start.sh                           <-- Manual daemon launcher
└── README.md                          <-- Authoritative Architecture & Setup Guide
```

---

*Flowork OS Sovereign Workspace — Built for Autonomous AI Systems & Infinite Continuity.*
