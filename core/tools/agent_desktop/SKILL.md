# ⚡ FLOWORK OS SOVEREIGN TOOL SKILL: AGENT_DESKTOP

---
name: agent_desktop
description: Master procedural doctrine for OS accessibility tree inspection, semantic @ref element targeting, high-speed action batching, and instant semantic injection without vision models.
keywords: [agent-desktop, accessibility, tree, atspi, desktop, window, click, type, batch, set_value, select, sovereign, audit, safety, flowork, doctrine]
---

## 1. Executive Summary
The `agent_desktop` tool operates Linux desktop application windows directly through the native AT-SPI2 OS accessibility tree. It provides deterministic, zero-token-vision UI inspection, high-speed multi-action batching, and sub-millisecond semantic value injection using `@ref` tags.

## 2. Core Operational Loop
1. **List Windows:** Run `list_windows` to identify active application names, titles, and window IDs.
2. **Snapshot UI:** Run `snapshot` (optionally filtered with `app: "<name>"` or `window_id: "<id>"`) with `interactive_only: true` to retrieve structured JSON containing clickable and typeable elements with unique `@ref` identifiers.
3. **Dispatch Agile Actions:**
   - **High-Speed Batching (`batch`):** Execute up to 64 sequential commands in a SINGLE turn without multi-turn LLM latency.
     ```json
     {
       "action": "batch",
       "batch": [
         {"command": "click", "args": ["@ref1"]},
         {"command": "set-value", "args": ["@ref2", "admin@flowork.dev"]},
         {"command": "click", "args": ["@ref3"]}
       ]
     }
     ```
   - **Semantic Instant Set (`set_value`):** Directly mutate input field content in ~1ms via AT-SPI `SetTextContents` without physical typing delay:
     `{ "action": "set_value", "ref": "@ref", "value": "text" }`
   - **Semantic Dropdown Selection (`select`):** Directly select list item or combo option:
     `{ "action": "select", "ref": "@ref", "option": "OptionName" }`
   - **Direct Single Actions:** `click`, `dblclick`, `clear`, `type`, `press_key`, `hotkey`, `hover`, `drag`, `scroll`, `scroll_to`, `focus`, `find`, `wait`.
4. **Verify State:** Take a follow-up `snapshot` or inspect batch receipts to verify state update with Exit Code 0.

## 3. Strict Prohibitions
- NEVER guess `@ref` identifiers; always obtain fresh IDs from a current snapshot.
- Avoid slow 1-char-at-a-time typing for large strings; use `set_value` for instant injection.
- When performing sequential multi-field form fills or multi-step dialogs, ALWAYS prefer `batch` to eliminate round-trip turn latencies.
- NEVER send raw credentials or secrets into untrusted desktop applications.
