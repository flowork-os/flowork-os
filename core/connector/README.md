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
       │  │ (0ms Zod routing)     │    │ (Stripped <session_ctx>) │  │
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
       │ Endpoint (:443)  │  │ Local (:11434)│   │ (:20128)          │
       └──────────────────┘  └───────────────┘   └───────────────────┘
```

---

## 3. How to Connect & Configure Ollama

The Sovereign Connector seamlessly translates Mr. Flow's internal Google Gemini calls into OpenAI-compatible requests for Ollama.

### Step 1: Ensure Ollama is Running
Verify that the Ollama daemon is active on port `11434`:
```bash
# Check daemon status
curl -s http://127.0.0.1:11434/api/tags

# If not running, start Ollama service
/opt/floworkos/bin/ollama serve
```

### Step 2: Download or Verify Local Models
Ensure you have pulled your desired models into Ollama:
```bash
# Lightweight model (Recommended for CPU-only systems: ultra-fast, ~3s latency)
/opt/floworkos/bin/ollama pull qwen2.5-coder:1.5b

# Medium model (Balanced for GPU or fast multi-core CPUs)
/opt/floworkos/bin/ollama pull qwen2.5-coder:7b

# Deep reasoning model (Recommended for NVIDIA GPU acceleration)
/opt/floworkos/bin/ollama pull deepseek-v4-9b-uncensored:latest
```

List installed models:
```bash
/opt/floworkos/bin/ollama list
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

When standard agent frameworks connect to local LLMs on CPU, they frequently experience **endless spinning, UI freezes, or fetch timeouts** due to prompt bloat and slow inference. Flowork OS solves this at the gateway layer:

### 1. JIT Prompt Condensation
- **The Problem**: Mr. Flow by default includes `<session_context>` containing a 200-item directory tree dump and a 5,000-word system instruction (~12,000 tokens). On a CPU, evaluating 12,000 tokens takes 12–15 minutes, exceeding HTTP fetch timeouts and causing endless retry storms.
- **The Solution**: When routing to Ollama (`isLocal = true`), the connector automatically strips the raw file tree listing and condenses the system instruction down to ~50 essential tokens. Prompt evaluation on CPU drops from **12 minutes to under 3 seconds**.

### 2. Fast-Path Pre-Turn Classifier
- **The Problem**: Mr. Flow executes an internal classification call (`NumericalClassifierStrategy` / `generateJson`) before every turn. A local 9B model on CPU takes 40+ seconds just to return this single integer classification.
- **The Solution**: The connector intercepts non-streaming classification requests and returns a Zod-compliant response (`complexity_reasoning: "Direct query"`, `complexity_score: 1`, `category: 0`) in **0.001 milliseconds**. Mr. Flow bypasses the delay and immediately begins streaming the real answer.

### 3. Reasoning Stream Isolation (`thought: true`)
- **The Problem**: DeepSeek models output thoughts in `<think>` blocks or `d.reasoning`. If dumped directly into the response text, it clutters the chat bubble or breaks JSON parsing.
- **The Solution**: The connector inspects delta chunks and tags reasoning tokens as `{ thought: true, text: ... }`. Mr. Flow renders thoughts cleanly inside the collapsible Thinking Card and displays the clean final answer in the chat bubble.

### 4. Context Window Tuning
- Ollama context is capped to `num_ctx: 8192` by default instead of `32768` on CPU systems, saving over 3.5 GB of RAM overhead and dramatically speeding up self-attention computation.

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

Verify the connection between the Sovereign Connector and Ollama using standard terminal commands:

```bash
# 1. Test Connector Health
curl -s http://127.0.0.1:9099/health
# Output: {"status":"ok","online":true}

# 2. Test Connector Ollama Bridge
curl -s http://127.0.0.1:9099/auth/test/ollama
# Output: {"success":true,"online":true,"count":3}

# 3. Test Full End-to-End Gemini Streaming over Ollama
curl -s -N "http://127.0.0.1:9099/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse" \
  -H "Content-Type: application/json" \
  -d '{"contents": [{"role": "user", "parts": [{"text": "Hello Mr. Flow"}]}]}'

# 4. Test Mr. Flow CLI Turn with DeepSeek
mrflow -p "ping" --skip-trust --approval-mode=sovereign
# Output: Exit Code 0 with immediate sovereign response
```

---

## 7. Directory & File Structure

```text
/opt/floworkos/connector/
├── bin/
│   ├── flowork-connector              <-- Pure Rust Gateway ELF (/opt/floworkos/connector-rs/)
│   ├── mrflow-gui.py                  <-- Desktop switchboard GUI
│   ├── mrflow-router                  <-- Daemon lifecycle launcher
│   └── mrflow-tray-menu.py            <-- System tray provider indicator
├── config/
│   ├── accounts.json                  <-- Active OAuth token pool (Protected)
│   ├── models.json                    <-- Model aliases & catalog definitions
│   ├── network.json                   <-- Upstream timeouts and retry policies
│   ├── providers.json                 <-- Provider endpoints & routing matrix
│   └── settings.json                  <-- Port (:9099) and rate-limit configs
├── data/
│   └── vault.json                     <-- Local credentials store (Strictly Git-Ignored)
├── gui/                               <-- Embedded glass switchboard web assets
├── start.sh                           <-- Manual daemon launcher
└── README.md                          <-- Authoritative Architecture & Setup Guide
```

---

*Flowork OS Sovereign Workspace — Built for Autonomous AI Systems & Infinite Continuity.*
