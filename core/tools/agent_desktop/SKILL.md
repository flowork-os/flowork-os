# ⚡ FLOWORK OS SOVEREIGN TOOL SKILL: AGENT_DESKTOP

---
name: agent_desktop
description: Master procedural doctrine for OS accessibility tree inspection, semantic @ref element targeting, and desktop application interaction without vision models.
keywords: [agent-desktop, accessibility, tree, atspi, desktop, window, click, type, interaction, sovereign, audit, safety, flowork, doctrine]
---

## 1. Executive Summary
The `agent_desktop` tool operates Linux desktop application windows directly through the native AT-SPI2 OS accessibility tree. It provides deterministic, zero-token-vision UI inspection and control using semantic `@ref` tags.

## 2. Core Operational Loop
1. **List Windows:** Run `list_windows` to identify active application names, titles, and window IDs.
2. **Snapshot UI:** Run `snapshot` (optionally filtered with `app: "<name>"`) with `interactive_only: true` to get structured JSON containing all clickable and typeable elements with unique `@ref` identifiers.
3. **Dispatch Action:** 
   - Call `click` with `ref: "<target_ref>"` to click a button, tab, or menu.
   - Call `type` with `ref: "<target_ref>"` and `text: "<string>"` to fill inputs.
   - Call `press_key` with `key: "Return"` to submit or trigger shortcuts.
4. **Verify State:** Take a follow-up `snapshot` to empirically verify that the UI state updated as intended.

## 3. Strict Prohibitions
- NEVER guess `@ref` identifiers; always obtain fresh IDs from a current snapshot.
- NEVER send raw credentials or secrets into untrusted desktop applications.
- Always communicate execution outcomes in clean technical English.
