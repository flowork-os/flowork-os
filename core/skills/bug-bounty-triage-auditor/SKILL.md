---
name: bug-bounty-triage-auditor
description: Autonomous authorized vulnerability auditing and bug bounty triage workflow. Implements the strict 7-Question Gate, A-to-B cluster analysis, auth-aware state inspection, and submission-ready report generation.
domain: security
keywords:
  - vulnerability_audit
  - bug_bounty
  - triage_gate
  - idor_testing
  - auth_bypass
  - privilege_escalation
  - business_logic
  - cluster_hunting
  - attack_surface
  - false_positive_elimination
  - cvss_scoring
  - report_generation
  - flowork_stealth
  - desktop_actuator
  - memory_crystallizer
  - semgrep_audit
  - scope_verification
  - proof_of_concept
  - api_security
  - remediation_guidance
author: Flowork Architecture Board
version: 1.0.0
---

# 🛡️ FLOWORK OS SOVEREIGN SKILL: BUG BOUNTY & TRIAGE AUDITOR

## 1. Objective
Equip Mr. Flow with a battle-tested, authorized vulnerability auditing and triage framework adapted from the industry-leading **Agentic Bug Hunter** methodology.
- **The Core Invariant**: *"Can an attacker do this RIGHT NOW against a real user who has taken NO unusual actions — and does it cause real, verifiable harm (leaked PII, money lost, account takeover, or code execution)?"*
- Eradicate theoretical fluff, unexploitable findings, and out-of-scope reports before writing. If the answer is NO, **STOP immediately and move on**.
- Provide a standardized, reproducible workflow across Web2 APIs, cloud endpoints, microservices, and desktop applications using the **7-Question Gate** and **A-to-B Cluster Hunting**.

## 2. Prerequisites
1. **Scope & Authorization Verification**:
   - Target assets MUST be explicitly confirmed in-scope. Never probe or scan unauthorized production targets.
   - For authenticated audits, prepare credentials/tokens in `.private/<target>.json` (gitignored, zero credentials leaked).
2. **Flowork Native Tooling Stack**:
   - `flowork-stealth`: Camoufox C++ engine for clean session isolation and proxy/GeoIP routing without bot detection.
   - `memory_crystallizer`: Local SQLite FTS5 for recording identified parameter patterns and prior audit resolutions.
   - `desktop_actuator`: Hardware display capture to document visual authentication flows and modal states.

## 3. Standard Operating Procedure (SOP)

### Phase 1: Attack Surface Reconnaissance & Scope Locking
1. Define in-scope root domains and API basepaths. Exclude third-party providers (Stripe, Google OAuth, AWS CDN) unless custom integrations are flawed.
2. Enumerate functional entry points:
   - Identify high-value business endpoints (authentication, payment processing, credit calculation, user profile update).
   - Trace API diffs: compare web application endpoints vs mobile/v2 endpoints.
3. Map endpoints and parameters into `audit/surface_map.json`.

### Phase 2: Auth-Aware State Auditing (IDOR & Privilege Escalation)
1. Establish two distinct non-privileged testing identities (`User A` and `User B`).
2. Capture authentic session tokens using `flowork-stealth`.
3. Perform cross-identity verification:
   - Submit requests using User A's session token containing User B's object IDs (`account_id`, `doc_uuid`, `order_num`).
   - If User B's sensitive data is returned or mutated without authorization, flag as candidate BOLA/IDOR.

### Phase 3: The 7-Question Triage Gate (Pre-Report Elimination)
Every candidate finding MUST pass all 7 questions in order. A single failure terminates investigation:
1. **Q1: Immediate Execution**: Can you write the exact HTTP request (method, URL, headers, payload) that triggers the issue right now? *(If theoretical only -> KILL IT)*.
2. **Q2: Program Acceptance**: Is the vulnerability class accepted by the target security policy? *(If listed in exclusions -> KILL IT)*.
3. **Q3: In-Scope Asset**: Is the asset in the authorized scope list? *(If third-party or out-of-scope -> KILL IT)*.
4. **Q4: Realistic Privilege**: Does it avoid requiring impossible preconditions like physical machine access or pre-existing server root? *(If admin-only behavior -> KILL IT)*.
5. **Q5: Not Documented Behavior**: Is the behavior undocumented and unintended, not an accepted product feature? *(Check CHANGELOG and public docs)*.
6. **Q6: Real-World Harm**: Does it directly cause financial loss, PII exfiltration, account takeover, or arbitrary code execution? *(If harmless implementation flaw -> KILL IT)*.
7. **Q7: Clean Remediation**: Can you provide a concrete architectural patch rather than a superficial patch?

### Phase 4: A-to-B Cluster Hunting (Chain Escalation)
When vulnerability A is confirmed, systematically hunt for adjacent vectors:
- **IDOR Read (Signal)** $\rightarrow$ Test `PUT`, `PATCH`, and `DELETE` on the same endpoint for state mutation.
- **SSRF Endpoint (Signal)** $\rightarrow$ Probe local cloud metadata (`169.254.169.254`) or container socket interfaces.
- **Stored XSS (Signal)** $\rightarrow$ Inspect `HttpOnly` and `SameSite` flags on session cookies for account takeover viability.
- **Open Redirect (Signal)** $\rightarrow$ Test OAuth `redirect_uri` validation to construct an authorization code theft chain.

### Phase 5: Submission-Ready Report Generation
Author structured markdown report in `audit/reports/<target>_<vuln_id>.md`:
1. **Title**: Structured summary (e.g. `[IDOR] Unauthorized PII Exfiltration via /api/v2/users/{id}/billing`).
2. **Severity & CVSS 3.1**: Objective vector string and numerical score.
3. **Vulnerability Overview**: Clear 2-sentence summary of the defect.
4. **Step-by-Step Proof of Concept (PoC)**: Exact curl commands with sanitized tokens.
5. **Impact Analysis**: Concrete description of business harm.
6. **Remediation**: Specific code snippet fix (e.g. enforce tenant ownership check in ORM layer).

## 4. Verification
1. **7-Question Checklist Audit**: Verify all 7 triage questions are explicitly answered in the audit report.
2. **Reproducibility Test**: Re-execute the documented PoC request from terminal; verify matching response status and payload.
3. **Zero False Positives**: Ensure dead code, theoretical exploits without PoC, and out-of-scope assets are completely purged.

## 5. Failure Modes & Recovery
1. **Rate Limiting / WAF Blocking**:
   - *Cause*: Automated fuzzing triggered cloud WAF rate limit.
   - *Recovery*: Slow down requests, route traffic through `flowork-stealth` with native proxy rotation, and test manually.
2. **Session Expiry During Testing**:
   - *Cause*: Testing tokens expired or invalidated by target backend.
   - *Recovery*: Re-authenticate via `flowork-stealth` and refresh `.private/<target>.json` session store.
3. **Informative / Duplicate Rejection**:
   - *Cause*: Feature is documented or previously patched.
   - *Recovery*: Always grep target issue tracker and changelogs before investing time into deep exploit chains.
