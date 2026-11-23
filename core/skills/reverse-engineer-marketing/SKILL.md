---
name: reverse-engineer-marketing
slash_command: /reverse-engineer-marketing
description: "Reverse engineer how any company acquires customers from one link: paid ad libraries, organic social, SEO sitemaps, founder profiles, tracking pixels, and funnel strategy."
domain: browser
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "reverse-engineering"
  - "marketing-analysis"
  - "paid-ads"
  - "meta-ad-library"
  - "google-ad-transparency"
  - "seo-audit"
  - "sitemap-inspection"
  - "tracking-pixels"
  - "google-tag-manager"
  - "customer-acquisition"
  - "growth-strategy"
  - "competitor-teardown"
  - "hacker-news-mentions"
  - "app-store-intelligence"
  - "play-store-seo"
  - "attribution-funnel"
  - "cli-rem"
  - "brand-positioning"
  - "playbook-extraction"
  - "evidence-gathering"
---

# 🔍 Marketing Reverse-Engineering Subsystem: REM

## 1. Executive Summary & Objective
Reverse engineer how any company acquires customers from one link: paid ad libraries, organic social, SEO sitemaps, founder profiles, tracking pixels, and funnel strategy.
This skill equips Mr. Flow to deconstruct any target company's customer acquisition engine from a single URL, gathering hard evidence across 8 distinct marketing pillars: website, tracking stack, SEO, archive history, app stores, paid ad libraries, social channels, and founder narratives.

## 2. Prerequisites & Tool Dependencies
1. **CLI Engine**: `rem` (`/usr/local/bin/rem`) powered by Node.js v22+.
2. **Network Access**: HTTP/HTTPS egress for crawling public ad libraries, sitemaps, and tag registries.
3. **Optional API Keys**:
   - `SCRAPECREATORS_API_KEY`: Enables deep programmatic scraping of ad platforms and social accounts.
   - `ANTHROPIC_API_KEY`: Unlocks standalone Claude model synthesis for the report.
4. **Flowork OS Actuators**: `run_shell_command` for running `rem <url> --no-ai` or `rem doctor`.

## 3. Standard Operating Procedure (SOP)

### Technical Specifications & Upstream Doctrine
# Reverse Engineer Marketing (REM)

Use REM when someone wants to know how a company acquires customers, or wants a growth playbook copied from a competitor. REM collects public evidence; you interpret it and write the report.

## Connect

If the `reverse_engineer_marketing` tool is available, use it. If not:

- Add the MCP server: `claude mcp add reverse-engineer-marketing -e SCRAPECREATORS_API_KEY=… -- npx -y reverse-engineer-marketing mcp` (then restart the agent), or
- Use the CLI directly: `npx -y reverse-engineer-marketing <url> --json` returns the same evidence bundle.

`npx -y reverse-engineer-marketing doctor` shows which sources are unlocked. Without `SCRAPECREATORS_API_KEY`, ad libraries, social stats and founders come back as unknowns with manual-check links; website, pixels, SEO, Wayback, App Store and Hacker News still work.

## Workflow

1. `reverse_engineer_marketing({ url })`. One call collects everything (~20–40s, ~25–50 Scrape Creators credits). If you already know a handle the site doesn't link, pass `handles: { tiktok: "…" }`.
2. Read the returned scorecard and evidence index. The scorecard is deterministic: don't contradict it, explain it.
3. `get_playbook()` once for the analyst role, evidence rules, report template and lesson library. Pull a channel playbook (`paid-meta`, `seo-geo`, `organic-short-form`, `founder-led`, …) when that channel matters.
4. `get_evidence({ run_id, ids })` for the items you'll quote: Meta longest-running ads, top TikTok/IG/X posts, sitemap families, founders, pricing.
5. Write the report in the template's sections. Every fact cites `[E#]`. Label inferences "Likely…". Put unknowns in their own section with the manual-check links.
6. `validate_report({ run_id, markdown })` and fix anything that fails before answering.

## Rules that matter most

- Unknown ≠ not doing it. Only a checked-and-empty source is a negative.
- A pixel means intent or past use. Only the ad library confirms current ads.
- No dollar spend figures unless a source states them; use spend proxies (active ads, ad longevity, launch rate).
- Ads running 60+ days are the proven winners. Lead with them and quote their hooks exactly.
- Founders carry a confidence (high = Wikidata/JSON-LD or two sources). Never state a low-confidence name as fact. Search-based matches (TikTok handle, Product Hunt) can be wrong too.
- Reddit affiliation ("brand/founder posts") is inferred from usernames and "I'm the founder"-style phrases; say "likely".
- Finish with "Steal this playbook": 5–10 concrete steps with numbers, each tied to evidence.

### Global CLI Invocation
- Perform headless evidence extraction:
  ```bash
  rem https://target.com --no-ai --out /opt/floworkos/documents/rem-teardown
  ```
- Check platform source status:
  ```bash
  rem doctor
  ```

## 4. Verification & Quality Gates (Exit Code 0)
1. **CLI Execution Gate**:
   - Run `rem doctor`:
     ```bash
     rem doctor
     ```
   - Must output system status and exit with Exit Code 0.
2. **Evidence Verification**:
   - Output bundle in target directory must contain:
     - `evidence.json`: Valid JSON schema containing structured findings.
     - `evidence.md`: Clean Markdown summary with verified source links.
   - Every claim must map directly to evidence (e.g. ad library link, sitemap URL, or pixel ID).

## 5. Failure Modes, Edge Cases & Recovery
- **Missing API Keys**: If `SCRAPECREATORS_API_KEY` is not configured, `rem` degrades gracefully by outputting direct manual-check links to Meta Ad Library, Google Ads Transparency Center, and LinkedIn Ad Library.
- **Aggressive Bot Protection / Cloudflare**: Use `web_fetch` or `agent_browser` with Camoufox anti-detect profile to retrieve raw page contents and extract pixels.
- **Subdomain Confusion**: Always resolve apex domain vs product subdomains (e.g. `app.slack.com` vs `slack.com`).

## 6. Prohibitions & Anti-Patterns
- **NEVER** guess or hallucinate advertising budgets or CAC without empirical data.
- **NEVER** claim a company runs paid ads without linking to the specific Ad Library search URL.
- **NEVER** omit the "Steal this playbook" actionable breakdown.
- **NEVER** produce unverified assertions; mark unconfirmed hypotheses explicitly as "tentative" or "likely".
