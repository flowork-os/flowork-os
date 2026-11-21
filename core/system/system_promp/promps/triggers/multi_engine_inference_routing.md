# MULTI-ENGINE AI INFERENCE ROUTING & SESSION RECOVERY

## 1. Context & Activation Scope
Applies when configuring, troubleshooting, or switching AI inference engines between Google CloudCode (Gemini 3.8 Flash), Ollama Local Engine (DeepSeek, Qwen), and 9Router Gateway across Mr. Flow CLI, Mr. Flow Sidebar, and Sovereign Connector.

## 2. Mandatory Behavioral Invariants
- SINGLE UNIFIED GATEWAY: All Mr. Flow agent traffic routes through Sovereign Router (`http://127.0.0.1:9099`). Never bypass port 9099.
- DYNAMIC PROVIDER CONFIG: Switch active inference engines via `POST http://127.0.0.1:9099/auth/router/provider-config` with JSON `{"active_provider": "connector" | "ollama" | "9router", "ollama": {"default_model": "<model>"}}`.
- CUSTOM DROPDOWN MANDATE: Native HTML `<select>` elements fail in borderless X11 WebKitGTK windows; all UI selectors MUST use custom CSS/HTML glass dropdown menus with event delegation.
- BROKEN SESSION AUTO-RECOVERY: If `mrflow` exits with non-zero code (e.g., code 42 from `$rewindTo` corruption), `mrflow-sidebar.py` must drain stderr, purge `currentSessionId`, and dispatch an error event to prevent endless retry loops.
- CPU VS CLOUD MODEL SELECTION: When GPU acceleration is unavailable, large local models (9B) experience high CPU latency for multi-thousand token contexts; prefer `qwen2.5-coder:1.5b` for rapid local inference or Gemini CloudCode for instant responses.
- ENVIRONMENT LOCK: Execution environments must explicitly supply `FLOWORK_CONNECTOR_URL="http://127.0.0.1:9099"` and `GOOGLE_GEMINI_BASE_URL="http://127.0.0.1:9099"` sourced from `/opt/floworkos/system/mrflow.env`.

## 3. Strict Prohibitions
- NEVER use native `<select>` tags inside WebKitGTK borderless sidebar windows.
- NEVER retain a crashed `session_id` after non-zero process exits.
- NEVER upload `/opt/floworkos/connector/data/vault.json` or active tokens to public repositories.
