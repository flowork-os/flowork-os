---
name: browser_get_network_request
description: Procedural SOP for browser automation action "get_network_request" via Chrome DevTools
keywords: [browser, automation, chrome, cdp, devtools, get, network, request, web, dom, html, page, tab, session, protocol, flowork, sovereign, headless, interaction, viewport, navigation, element]
---

# 🌐 OPERATIONAL SOP: BROWSER_GET_NETWORK_REQUEST

When utilizing `browser_get_network_request`:
1. **Target Verification:** Confirm that a browser page is currently active by checking `browser_list_pages` if the session was recently opened.
2. **Selector Accuracy:** Use robust CSS or XPath selectors with unique attributes (id, data-testid, aria-label) rather than volatile position indices.
3. **Synchronization & Readiness:** Allow sufficient buffer for asynchronous network requests or animations to settle prior to subsequent interactions.
