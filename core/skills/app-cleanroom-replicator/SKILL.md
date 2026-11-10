---
name: app-cleanroom-replicator
description: Autonomous clean-room application replication and UX reconstruction workflow. Clones functionality, user flows, design systems, and competitive market positioning without infringing copyright or stealing code.
domain: code_dev
keywords:
  - clean_room
  - app_cloning
  - product_reverse_engineering
  - ux_reconstruction
  - feature_matrix
  - recon_map
  - design_system
  - component_tokens
  - market_intelligence
  - competitor_analysis
  - playwright_testing
  - parity_scoring
  - desktop_actuator
  - flowork_stealth
  - frontend_builder
  - backend_architecture
  - auth_billing
  - landing_page
  - product_differentiation
  - rapid_prototyping
author: Flowork Architecture Board
version: 1.0.0
---

# ⚡ FLOWORK OS SOVEREIGN SKILL: APP CLEAN-ROOM REPLICATOR

## 1. Objective
Equip Mr. Flow with an end-to-end procedural playbook to observe, map, reverse-engineer, and rebuild any target software product (Web SaaS, Desktop, or Mobile) using a strict **Clean-Room Engineering Protocol**.
- Rebuild what an app **does**, never what it **owns**.
- Reconstruct UX journeys, interaction flows, relational data models, and feature matrices from public documentation, public pages, user reviews, and active observation.
- Enforce complete freedom from intellectual property infringement: zero stolen source code, zero copied brand assets, zero leaked private tokens.

## 2. Prerequisites
1. **Flowork Sovereign Engines Online**:
   - `desktop_actuator`: Hardware display framebuffer capture (16ms) and evdev virtual input control.
   - `flowork-stealth`: Camoufox C++ anti-detect browser engine configured for bot-immune public web navigation.
   - `memory_crystallizer`: Local SQLite FTS5 database initialized for storing recon maps and competitive insights.
   - `tool_foundry`: Ready to synthesize custom API bridges and test fixtures.
2. **Clean Staging Territory**:
   - All recon artifacts, design tokens, test specs, and feature matrices must be staged strictly inside `replica/` within the project root.

## 3. Standard Operating Procedure (SOP)

### Phase 1: Autonomous Reconnaissance (`replica/recon.md` & `features.csv`)
1. Mobilize `flowork-stealth` or `desktop_actuator` to navigate through public pages, help centers, and walkthroughs.
2. Enumerate every user screen, sub-route, modal state, and navigation tree into `replica/recon.md`.
3. Infer the underlying relational data model (entities, fields, relations, foreign keys, and unique constraints).
4. Author `replica/features.csv` categorizing features into `Core Flow`, `Secondary Utility`, and `Out of Scope`.

### Phase 2: Architecture & Stack Selection (`replica/architecture.md`)
1. Select optimal lightweight stack (Vanilla CSS + React/TypeScript or FastAPI/Python or Go).
2. Author normalized database schema migrations (PostgreSQL / SQLite).
3. Draft clean OpenAPI REST endpoints matching functional domain requirements.

### Phase 3: Design System Tokenization (`replica/design-tokens.json`)
1. Measure visual rhythm, typography scales, 8px layout grid, and color contrast hierarchies.
2. Map visual attributes to semantic tokens (`--color-surface`, `--color-primary`, `--radius-md`).
3. Replace proprietary icons and brand illustrations with open-source SVG alternatives (Lucide / Tabler).

### Phase 4: Screen-by-Screen Frontend Construction
1. Build application shell, navigation rails, and responsiveness breakpoints.
2. Implement each identified screen and interactive modal state, ticking off rows in `features.csv`.
3. Guarantee rich aesthetic standards: platform-native smooth transitions, focus states, and zero layout shift.

### Phase 5: Backend, Auth & Billing Engine
1. Implement stateless authentication (JWT / session cookies).
2. Wire core domain CRUD operations and database transactions.
3. Integrate payment webhooks (Stripe / LemonSqueezy) and transactional notification dispatchers.

### Phase 6: Automated Verification & Parity Scoring
1. Author automated Playwright/integration test suites covering all identified critical paths.
2. Execute test suites; enforce zero open S1/S2 bugs with Exit Code 0 verification.
3. Calculate Parity Score (0 - 100%) against target feature checklist.

### Phase 7: The Entrepreneur (Competitive Market Edge)
1. Crawl public user reviews across App Store, Trustpilot, G2, and Reddit using `flowork-stealth`.
2. Extract and quantify top user complaints (predatory per-seat pricing, missing export features, complex UX).
3. Formulate the "Kill-Shot" Value Proposition: fix the competitor's top 3 complaints directly into your replica.

### Phase 8: Brand Identity & Trademark Cleansing
1. Generate unique product branding, logo brief, and voice.
2. Conduct an automated regex sweep across the entire codebase to ensure zero competitor trademarks or names remain.
3. Write high-converting landing page copy based on the Entrepreneur value proposition.

### Phase 9: Deployment & Production Launch
1. Build production bundle with optimized static assets.
2. Configure systemd unit or containerized daemon with automated restarts.
3. Run post-deploy smoke tests to confirm 100% operational integrity.

## 4. Verification
1. **Artifact Checklist**: Verify existence of `replica/recon.md`, `replica/features.csv`, and `replica/design-tokens.json`.
2. **Zero-Leak Trademark Audit**: Run `grep -ri "<competitor_name>" src/` -> Must return 0 matches.
3. **Empirical Test Suite**: Run project test commands (`npm test`, `pytest`, `cargo test`) -> Must pass with Exit Code 0.

## 5. Failure Modes & Recovery
1. **Target Product Blocks Inspection**:
   - *Cause*: Aggressive anti-bot/Cloudflare challenge on competitor website.
   - *Recovery*: Mobilize `flowork-stealth` with MaxMind GeoIP alignment and resident uBlock Origin.
2. **Missing Accessibility Nodes in Desktop GUI**:
   - *Cause*: Target software uses custom GPU canvas (OpenGL/Vulkan) without AT-SPI exposure.
   - *Recovery*: Deploy `desktop_actuator` to capture DRM framebuffer directly (16ms) and simulate virtual HID clicks.
3. **Trademark / Copy Infringement Risk**:
   - *Cause*: Accidental inclusion of original marketing copy or component labels.
   - *Recovery*: Execute automated brand sweep script and replace all user-facing strings with original phrasing.
