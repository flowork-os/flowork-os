---
name: agentic-seo-auditor
description: Autonomous Generative Engine Optimization (GEO) and Agentic SEO audit and remediation playbook. Audits AI search citations, llms.txt, schema JSON-LD, and Core Web Vitals.
domain: browser
keywords:
  - seo
  - search_engine_optimization
  - geo
  - generative_engine_optimization
  - llms_txt
  - agentic_web
  - webmcp
  - schema_jsonld
  - core_web_vitals
  - audit
  - crawler
  - perplexity
  - entity_graph
  - sitemap
  - robots_txt
  - structured_data
  - canonical
  - meta_tags
  - performance
  - lighthouse
author: Flowork Architecture Board
version: 1.0.0
---

# ⚡ FLOWORK OS SOVEREIGN SKILL: AGENTIC SEO & GEO AUDITOR

## 1. Objective
Equip Mr. Flow with an autonomous, multi-domain Standard Operating Procedure (SOP) to audit, score, and remediate web applications for both traditional Search Engine Optimization (SEO) and modern Generative Engine Optimization (GEO).
- Evaluate website readiness for autonomous AI agents (`llms.txt`, Markdown negotiation, WebMCP endpoints).
- Quantify citation and extraction probabilities across AI answer engines (Perplexity, ChatGPT Search, Google Gemini, Claude, and Google AI Overviews).
- Validate Schema.org JSON-LD entity graphs, canonical chains, OpenGraph metadata, and Core Web Vitals.
- Synthesize drop-in code fixes (`llms.txt`, valid JSON-LD schemas, Next.js metadata, robots.txt) with zero consulting fluff.

## 2. Prerequisites & Tool Dependencies
1. **Flowork Sovereign Execution Instruments**:
   - `run_shell_command`: Execute Python inspection scripts, CDP tools, and validation binaries.
   - `read_file`: Inspect local source code, metadata, HTML templates, and configuration files.
   - `write_to_file`: Generate drop-in remediation assets (`llms.txt`, JSON-LD scripts, sitemaps).
   - `replace_file_content`: Surgically inject structured data and metadata into existing codebases.
   - `browser_navigate_page` / `browser_evaluate_script`: Interact with live web pages and inspect DOM.
   - `browser_take_screenshot`: Capture visual layout shifts (CLS) and responsive render states.
   - `flowork_web_search`: Perform real-time live verification of competitor rankings and indexing.
   - `invoke_subagent`: Orchestrate parallel subagent fan-out for multi-domain audits.
   - `flowork-stealth`: Bot-immune web inspection runner (`/opt/floworkos/bin/flowork-stealth`).
2. **Local Python Utilities**:
   - Python 3.10+ runtime with `urllib` / `json` / `re` modules.
   - Local helper scripts located in `/opt/floworkos/skills/agentic-seo-auditor/scripts/`.

## 3. Standard Operating Procedure (SOP)

### Phase 1: Target Ingestion & Scope Definition
Determine whether the audit target is a **local project codebase** (e.g. Next.js, Astro, Nuxt, static HTML) or a **live production URL**.
1. If local codebase: Inspect `public/`, `src/app/`, or root directory for existing `robots.txt`, `sitemap.xml`, and metadata definitions using `read_file`.
2. If live URL: Execute `/opt/floworkos/skills/agentic-seo-auditor/scripts/seo_auditor.py <url>` via `run_shell_command` to retrieve HTTP status, response headers, canonical link, and HTML payload.

### Phase 2: Agentic Web Readiness Audit (`/seo agentic`)
Verify whether the target exposes clean, deterministic semantic contracts for autonomous AI agents:
1. **`llms.txt` & `llms-full.txt`**:
   - Probe `<url>/llms.txt` and `<url>/llms-full.txt`.
   - Validate format: H1 project name, summary paragraph, Markdown links organized under concise H2 sections.
   - If missing: Execute `scripts/generate_llmstxt.py` to auto-generate standard-compliant files.
2. **Markdown Content Negotiation**:
   - Probe target with HTTP header `Accept: text/markdown`.
   - Record whether the server returns raw semantic markdown or unparsed HTML.
3. **WebMCP & API Tool Exposure**:
   - Probe for `/.well-known/mcp.json` or Model Context Protocol declarations enabling agents to invoke API endpoints directly.

### Phase 3: Generative Engine Optimization (GEO) Citability
Calculate citation likelihood across AI engines (Perplexity, ChatGPT Search, Gemini, Claude):
1. **Factual Grounding & Statistic Density**:
   - Evaluate ratio of quantitative claims, research data, and specific metrics versus generic marketing prose.
2. **Entity Salience & Knowledge Graph Anchoring**:
   - Identify core entities (Organization, Product, Person) and check if named entities resolve to unambiguous Wikipedia/Wikidata ontology nodes.
3. **Quotable Snippet Architecture**:
   - Ensure introductory sentences under H2/H3 headers provide definitive 40-60 word answers directly usable as featured snippets.

### Phase 4: Schema.org Entity Graph & Technical SEO
1. **JSON-LD Syntax & Semantic Graph**:
   - Extract `<script type="application/ld+json">` blocks.
   - Validate JSON syntax and required Schema.org properties (`@context`, `@type`, `name`, `url`, `description`).
   - Ensure primary types are represented: `Organization`, `WebSite`, `SoftwareApplication` (for SaaS), `TechArticle`, `FAQPage`.
2. **Technical Head Hygiene**:
   - Ensure exactly **one** `<title>` tag (30-60 characters).
   - Ensure `<meta name="description">` exists (120-160 characters).
   - Ensure valid `<link rel="canonical">` points to authoritative self-URL.
   - Verify OpenGraph (`og:title`, `og:image`, `og:description`) and Twitter Cards.
   - Validate single `<h1>` tag per page and sequential heading hierarchy (`h1` -> `h2` -> `h3`).

### Phase 5: Core Web Vitals & Performance Profiling
1. **CDP & Render Metrics**:
   - Use `flowork-stealth` or CDP browser evaluation to extract Largest Contentful Paint (LCP), Interaction to Next Paint (INP), and Cumulative Layout Shift (CLS).
2. **Asset Optimization**:
   - Verify modern image formats (`.webp`, `.avif`), explicit `width`/`height` attributes to prevent CLS, and lazy-loading on below-the-fold media.

### Phase 6: Subagent Fan-Out Orchestration
For complex, full-scale site audits, fan out parallel subagents using `invoke_subagent`:
1. **Subagent 1 (`Technical & Crawlability`)**: Inspects robots.txt, sitemaps, canonical chains, HTTP headers, and 404/301 loops.
2. **Subagent 2 (`Schema & Entity Graph`)**: Extracts and validates all JSON-LD blocks and graph relations.
3. **Subagent 3 (`GEO & Agentic Readability`)**: Audits `llms.txt`, citation density, and AI search extractability.
4. **Synthesis**: Aggregate subagent findings into a unified Prioritized Action Matrix (P0 to P3).

### Phase 7: Deterministic Remediation & Code Synthesis
Do NOT merely list errors—produce drop-in code fixes:
1. **Schema JSON-LD**: Provide complete, valid JSON-LD code blocks ready to be pasted into the HTML `<head>` or Next.js layout.
2. **`llms.txt`**: Author a complete `llms.txt` file summarizing the project's documentation and core interfaces.
3. **Metadata Config**: For React/Next.js codebases, generate the exact `generateMetadata()` TypeScript export.

## 4. Verification & Quality Gates (Exit Code 0)
Every audit and remediation must be empirically proven via terminal execution:
1. **Auditor Script Execution**:
   ```bash
   python3 /opt/floworkos/skills/agentic-seo-auditor/scripts/seo_auditor.py --target /path/to/project --json
   ```
   Must exit with **Exit Code 0** and emit a structured audit report.
2. **JSON-LD Schema Validation**:
   ```bash
   python3 -c "import json; json.loads(open('schema.json').read()); print('VALID JSON-LD')"
   ```
   Must output `VALID JSON-LD` with Exit Code 0.
3. **`llms.txt` Presence & Format Gate**:
   ```bash
   test -f public/llms.txt && grep -q '^# ' public/llms.txt && echo "OK"
   ```
   Must return `OK` with Exit Code 0.

## 5. Failure Modes, Edge Cases & Recovery
1. **Client-Side SPA Without SSR**:
   - *Problem*: Pure React/Vue SPAs render empty `<div id="root">` to crawlers without metadata.
   - *Recovery*: Guide operator to implement pre-rendering, static site generation (SSG), or dynamic server-side OpenGraph injection.
2. **Malformed JSON-LD in Upstream Templates**:
   - *Problem*: Unescaped quotes or trailing commas crash the JSON parser.
   - *Recovery*: Run `seo_auditor.py` to pinpoint the exact line, then use `replace_file_content` to fix the delimiter syntax.
3. **Headless Browser Blocked by Cloudflare / WAF**:
   - *Problem*: HTTP 403 or Cloudflare challenge during live URL crawl.
   - *Recovery*: Switch execution to `/opt/floworkos/bin/flowork-stealth` with native TLS/hardware fingerprint spoofing.

## 6. Prohibitions & Anti-Patterns
- **Zero Generic Advice**: Never output generic consulting advice (e.g. "Create high quality content"). Always specify exact tags, attributes, schemas, or file contents.
- **Zero Non-Sovereign Tool Names**: Never reference non-Flowork tool names (e.g. `Bash`, `View`, `Edit`, `GlobTool`). Strictly use canonical Flowork OS tools (`read_file`, `write_to_file`, `replace_file_content`, `run_shell_command`).
- **Never Overwrite Code Blindly**: Never replace entire components without reading their existing structure via `read_file`. Use `replace_file_content` for surgical injections.
- **Zero Zombie Test Files**: Remove all temporary crawl dumps or scratch fixtures from workspace roots upon mission completion.
