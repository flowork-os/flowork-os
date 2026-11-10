---
name: browser_take_screenshot
description: Procedural SOP for browser automation action "take_screenshot" via Chrome DevTools
keywords: [browser, automation, chrome, cdp, devtools, take, screenshot, web, dom, html, page, tab, session, protocol, flowork, sovereign, headless, interaction, viewport, capture]
---

# 🌐 OPERATIONAL SOP: BROWSER_TAKE_SCREENSHOT

When utilizing `browser_take_screenshot`:
1. **Target Verification:** Confirm that a browser page is currently active by checking `browser_list_pages` if the session was recently opened.
2. **Default Output Vault:** Persist screenshots to `/opt/floworkos/screenshots/` if saving to disk (`filePath`).
3. **Selector Accuracy:** Use robust CSS or XPath selectors with unique attributes (id, data-testid, aria-label) rather than volatile position indices.
4. **Synchronization & Readiness:** Allow sufficient buffer for asynchronous network requests or animations to settle prior to subsequent interactions.
