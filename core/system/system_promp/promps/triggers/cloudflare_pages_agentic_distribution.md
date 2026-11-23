# CLOUDFLARE PAGES AGENTIC DISTRIBUTION DIRECTIVE

## 1. Context & Activation Scope
Applies when publishing, updating, or maintaining Flowork OS web applications and landing pages on Cloudflare Pages (e.g. `floworkos.com`, `floworkhome`, `*.pages.dev`).

## 2. Mandatory Behavioral Invariants
- Deploy static builds headlessly via `npx wrangler pages deploy <dir> --project-name=<project> --branch=no-auto-deploy-sealed --commit-dirty=true` using `/opt/floworkos/apps/nodejs/bin` in PATH.
- Verify production domains directly via HTTP HEAD before marking tasks complete: require HTTP/2 200 on both apex and `pages.dev` endpoints.
- Enforce the official Flowork sovereign vector emblem (`assets/flowork-logo.svg` copied from `/opt/floworkos/system/icons/flowork-logo.svg`) in all headers and footers; never substitute with generic emojis or unbranded shapes.
- Enforce mobile-first responsive invariants across viewports (390px, 768px, 1280px); verify full readability of CTAs, comparison tables, and terminal viewports.
- Maintain Agentic Web readiness: deploy `_headers` (caching, security headers, `Link: </llms.txt>`), `_redirects`, and authoritative `/llms.txt` and `/llms-full.txt`.
- Validate Schema.org JSON-LD entities (`SoftwareApplication`, `WebSite`, `Organization`, `FAQPage`) and GEO quotability via `/opt/floworkos/skills/agentic-seo-auditor/scripts/seo_auditor.py <url>` achieving a 100/100 score.

## 3. Strict Prohibitions
- Never hardcode transient tokens into git repositories or committed static assets.
- Never deploy broken responsive viewports with horizontal scroll overflows on mobile screens.
- Never mark deployments successful without empirical HTTP 200 terminal confirmation.
