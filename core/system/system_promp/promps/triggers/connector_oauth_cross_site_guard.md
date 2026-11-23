# CONNECTOR OAUTH CROSS-SITE REDIRECT & CSRF INVARIANT

## 1. Context & Activation Scope
Triggered when developing, modifying, or auditing `flowork-connector` (port 9099 / aux 51121 & 8080), OAuth callback handlers, CSRF origin guards, or Google/CloudCode browser authentication flows.

## 2. Mandatory Behavioral Invariants
- **Bypass Top-Level OAuth GET Navigations:** In `csrf_origin_guard`, always permit cross-site GET redirects destined for OAuth callback routes (`/oauth-callback`, `/callback`, `/auth/callback`, `/auth/flowork-callback`, `/oauth/callback`). Browsers navigating from external Identity Providers (e.g. `accounts.google.com`) strictly emit `Sec-Fetch-Site: cross-site`.
- **Rely on Cryptographic State & PKCE:** Authorize OAuth callbacks via verified PKCE verifier exchanges and state nonce checks (`flw_multi_*`), never by asserting loopback `Sec-Fetch-Site` or `Origin` headers on callback redirects.
- **Maintain Strict CSRF on Mutating Routes:** Unconditionally enforce `Sec-Fetch-Site: cross-site` rejections and trusted origin verification on all state-altering API methods (`POST`, `PUT`, `DELETE`).

## 3. Strict Prohibitions
- Never apply generic `cross-site` blanket blocks to auxiliary OAuth callback listeners or GET callback paths.
- Never strip CSRF protection from mutating endpoints (`/auth/logout`, `/auth/router/*`).
