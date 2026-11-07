# ⚡ Flowork Sovereign Connector (`flowork-connector`)

> **Authoritative Architecture Specification, Operational Guide, and Multi-Provider Matrix**  
> *Release Version:* 2.17 (Sealed Binary Release)  
> *Canonical Territory:* `/opt/floworkos/connector` (Sovereign Gateway Root)  
> *Default Port:* `9099` (HTTP / SSE / WebSocket)  
> *Web GUI:* `http://127.0.0.1:9099/gui`  

---

## 1. Executive Overview

**Flowork Connector** (`flowork-connector`) is an independent, high-performance local inference proxy gateway engineered specifically for **Flowork OS**. It bridges standard AI clients (Mr. Flow CLI, Antigravity IDE, Cursor, Continue, Roo Code, Cline, etc.) with diverse AI inference backends—including high-speed Google CloudCode pools, local GPU acceleration (Ollama), and universal multi-model routers (9Router / 8Router / OpenRouter).

### Core Capabilities
- **Standalone Sealed Binary**: Built as a self-contained single ELF executable (94 MB) using the Bun runtime. Operates without external `node`, `npm`, or runtime dependencies in production.
- **Single Model Lock Policy**: Normalizes all sub-model requests (`gemini-3.5-flash-lite`, `gemini-3-flash-preview`, etc.) to the authoritative stable model: **`gemini-3.8-flash-high`**, guaranteeing 100% operational reliability.
- **Zero-Hardcode Path Doctrine**: Completely decoupled from user home directories (`/home/<user>`); all paths resolve dynamically to support zero-error Flowork OS ISO builds.
- **Multi-Account Matrix & Quota Rotator**: Dynamically rotates authenticated Google accounts upon encountering HTTP `429 Too Many Requests`, applying intelligent cooldown algorithms to eliminate inference downtime.
- **OpenAI Protocol Translation**: Bi-directional translation between standard OpenAI API formats (`/v1/chat/completions` with SSE streaming) and internal Google CloudCode PA protocols.
- **Embedded Management Web GUI**: Embedded dashboard at `/gui` providing real-time account status, quota health, provider switching, and telemetry.

---

## 2. System Architecture

```text
       ┌─────────────────────────────────────────────────────────────┐
       │             CLIENT LAYER (OpenAI Compatible API)            │
       │   Mr. Flow CLI  │  Antigravity IDE  │  Cline / Roo  │ Web UI│
       └──────────────────────────────┬──────────────────────────────┘
                                      │ HTTP Request (:9099 /v1/chat/completions)
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │             FLOWORK CONNECTOR SEALED BINARY                 │
       │            (/opt/floworkos/connector/bin/flowork-connector) │
       │                                                             │
       │  ┌────────────────────┐   ┌───────────────────────────────┐ │
       │  │ Dynamic Config Mgr │   │ Embedded Web GUI Server       │ │
       │  │ (config/*.json)    │   │ (http://127.0.0.1:9099/gui)   │ │
       │  └─────────┬──────────┘   └───────────────────────────────┘ │
       │            │                                                │
       │            ▼                                                │
       │  ┌────────────────────────────────────────────────────────┐ │
       │  │ Protocol Normalizer & Model Router                     │ │
       │  │ - Normalizes sub-models to gemini-3.8-flash-high       │ │
       │  │ - Resolves Provider: Google Pool vs Ollama vs 9Router  │ │
       │  └─────────────────────────┬──────────────────────────────┘ │
       │                            │                                │
       │       ┌────────────────────┼───────────────────┐            │
       │       ▼                    ▼                   ▼            │
       │  ┌──────────────┐   ┌──────────────┐    ┌──────────────┐    │
       │  │ CloudCode PA │   │ Local Ollama │    │ 9Router /    │    │
       │  │ Quota Rotator│   │ GPU Adapter  │    │ 8Router Proxy│    │
       │  └──────┬───────┘   └──────┬───────┘    └──────┬───────┘    │
       └─────────┼──────────────────┼───────────────────┼────────────┘
                 ▼                  ▼                   ▼
       ┌──────────────────┐ ┌───────────────┐   ┌────────────────────┐
       │ Google CloudCode │ │ Local GPU     │   │ External OpenAI-   │
       │ Endpoint Pool    │ │ (:11434)      │   │ Compatible Gateway │
       └──────────────────┘ └───────────────┘   └────────────────────┘
```

---

## 3. Service Operations & Endpoints

### Starting the Service
The connector runs as a persistent system daemon, but can also be controlled manually:

```bash
# Start via standalone script
/opt/floworkos/connector/start.sh

# Start binary directly
/opt/floworkos/connector/bin/flowork-connector

# Check daemon health status
curl -s http://127.0.0.1:9099/health
# Output: {"status":"ok","online":true}
```

### Core API Endpoints

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `http://127.0.0.1:9099/health` | `GET` | Health check and readiness probe. |
| `http://127.0.0.1:9099/gui` | `GET` | Embedded visual web administration interface. |
| `http://127.0.0.1:9099/v1/chat/completions` | `POST` | OpenAI-compatible chat completion endpoint (supports streaming). |
| `http://127.0.0.1:9099/v1/models` | `GET` | Returns list of available models and active routing targets. |
| `http://127.0.0.1:9099/metrics` | `GET` | Real-time throughput, latency, and quota exhaustion telemetry. |

---

## 4. Multi-Provider Matrix Configuration

The connector dynamically routes inference requests based on the selected provider configured in `/opt/floworkos/connector/config/`:

### A. Google CloudCode Pro Pool (Default)
- **Engine:** Direct CloudCode PA API with OAuth token authentication.
- **Failover:** Automatic account rotation upon encountering HTTP `429`. Accounts in cooldown are automatically re-activated after the expiry period.
- **Model:** Locked to `gemini-3.8-flash-high`.

### B. Local Ollama GPU Engine
- **Target URL:** `http://127.0.0.1:11434`
- **Use Case:** 100% offline air-gapped sovereign development without internet connectivity.
- **Switching:** Set active provider to `ollama` via Web GUI or CLI router:
  ```bash
  mrflow-router --provider=ollama
  ```

### C. 9Router / 8Router Multi-Model Gateway
- **Target URL:** Configured in `config/providers.json`.
- **Use Case:** Universal OpenAI-compatible proxy supporting Claude, GPT-4o, DeepSeek, and open-weights models through a single key.
- **Switching:**
  ```bash
  mrflow-router --provider=9router
  ```

---

## 5. Client Integration Standards

### Mr. Flow CLI Integration
Mr. Flow automatically binds to the local connector gateway:
```bash
export FLOWORK_CONNECTOR_URL="http://127.0.0.1:9099"
export GOOGLE_GEMINI_BASE_URL="$FLOWORK_CONNECTOR_URL"
export GEMINI_API_KEY="flowork-sovereign-token"
```

### Third-Party IDEs & Tools (Cursor, VS Code, Cline)
Configure the OpenAI API endpoint in your tool settings:
- **Base URL:** `http://127.0.0.1:9099/v1`
- **API Key:** `flowork-sovereign-token` (or any non-empty string)
- **Model:** `gemini-3.8-flash-high`

---

## 6. Directory Layout & File Architecture

```text
/opt/floworkos/connector/
├── bin/
│   └── flowork-connector              <-- Standalone 94MB Bun ELF binary
├── config/
│   ├── accounts.json                  <-- Active OAuth token pool
│   ├── providers.json                 <-- Provider endpoints & routing matrix
│   └── settings.json                  <-- Port, rate-limits, and cooldown configs
├── data/
│   └── metrics.db                     <-- Local SQLite metrics and session tracking
├── gui/                               <-- Embedded dashboard web assets
├── start.sh                           <-- Service launch script
└── README.md                          <-- This Authoritative Architecture Guide
```

---

*Flowork OS Sovereign Workspace — Canonical Inference Gateway & Quota Matrix.*
