# ⚡ FLOWORK OS SOVEREIGN TOOL SKILL: AGENT_BROWSER

---
name: agent_browser
description: Master procedural doctrine for native Rust browser automation via Chrome DevTools Protocol (CDP), compact accessibility snapshots, and semantic @ref interactions.
keywords: [agent-browser, browser, web, cdp, automation, scrape, url, click, type, fill, sovereign, audit, safety, flowork, doctrine]
---

## 1. Executive Summary
The `agent_browser` tool provides high-speed browser automation for AI agents. It communicates with a persistent background daemon via Chrome DevTools Protocol (CDP) and generates ultra-compact text snapshots with `@ref` IDs, eliminating visual screenshot token costs.

## 2. Core Operational Loop
1. **Open URL:** `agent_browser {"action":"open", "url":"https://target.com"}`
2. **Snapshot Page:** `agent_browser {"action":"snapshot", "interactive_only":true}`
   Returns compact lines such as:
   ```text
   - link "Login" [ref=e1]
   - textbox "Email" [ref=e2]
   - button "Sign In" [ref=e3]
   ```
3. **Dispatch Semantic Action:**
   - Click: `{"action":"click", "ref":"@e1"}`
   - Fill: `{"action":"fill", "ref":"@e2", "text":"user@example.com"}`
   - Press Key: `{"action":"press", "key":"Enter"}`
4. **Verify State:** Call `snapshot` or `get url` to empirically confirm state change.
5. **Session Teardown:** Call `{"action":"close"}` when finished.

## 3. Strict Prohibitions
- NEVER guess `@ref` identifiers; always obtain fresh IDs from a current snapshot after any navigation.
- NEVER leave orphaned headless browser daemons open indefinitely.
- Always communicate execution outcomes in clean technical English.
