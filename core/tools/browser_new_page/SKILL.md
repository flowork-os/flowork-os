---
name: browser_new_page
description: Procedural SOP for browser automation action "new_page" via Chrome DevTools
keywords: [browser, automation, chrome, cdp, devtools, new, page, web, dom, html, page, tab, session, protocol, flowork, sovereign, headless, interaction, viewport, navigation, element]
---

# 🌐 OPERATIONAL SOP: BROWSER_NEW_PAGE

When utilizing `browser_new_page`:
1. **Target Verification:** Confirm that a browser page is currently active by checking `browser_list_pages` if the session was recently opened.
2. **Selector Accuracy:** Use robust CSS or XPath selectors with unique attributes (id, data-testid, aria-label) rather than volatile position indices.
3. **Synchronization & Readiness:** Allow sufficient buffer for asynchronous network requests or animations to settle prior to subsequent interactions.
