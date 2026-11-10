---
name: google-skills-navigator
description: Sovereign on-demand navigator for 100+ Google Agent Skills. Enables Just-In-Time discovery, retrieval, and execution for Google Cloud, Gemini API, GKE, databases, security, and Safe Rust migration without prompt bloat.
domain: code_dev
keywords:
  - google_skills
  - cloud_architecture
  - gemini_platform
  - gke_inference
  - model_garden
  - bigquery_analytics
  - alloydb_database
  - cloud_storage
  - iam_governance
  - secops_investigation
  - yara_rules
  - developer_knowledge
  - migrate_to_rust
  - vertex_ai
  - spanner_sql
  - cloud_run
  - jit_skill_retrieval
  - anti_bloat
  - agent_gateway
  - sovereign_navigator
author: Flowork Architecture Board
version: 1.0.0
---

# ⚡ FLOWORK OS SOVEREIGN SKILL: GOOGLE SKILLS NAVIGATOR

## 1. Objective
Equip Mr. Flow with an authoritative, on-demand discovery and execution mechanism for official Google Agent Skills (`google/skills`).
- Provide instant lookup and runtime loading for 100+ Google Cloud, Gemini, and developer workflows.
- Enforce the **Flowork Anti-Bloat Law**: maintain zero persistent token bloat in base prompts by pulling skill instructions purely on-demand (*Just-In-Time injection*).
- Support offline-first querying via local cached registry `/opt/floworkos/skills/google-skills-navigator/data/index.json` with seamless fallback to GitHub upstream.

## 2. Prerequisites
1. **Flowork Environment & Tooling**:
   - Python 3 runtime available at `/usr/bin/python3`.
   - Local catalog cache present at `/opt/floworkos/skills/google-skills-navigator/data/index.json`.
   - Fast CLI navigator present at `/opt/floworkos/skills/google-skills-navigator/scripts/query_google_skills.py`.
2. **Network Connectivity (Optional for Live Fetch)**:
   - Outbound HTTPS to `raw.githubusercontent.com` if updating catalog or fetching newly published remote skills.

## 3. Standard Operating Procedure (SOP)

### Phase 1: Context Detection & Keyword Routing
1. Identify when user requests involve Google Cloud products, Google developer APIs, Gemini Agent Platform, GKE TPU/GPU clusters, BigQuery, SecOps, or language migration.
2. Formulate 1 to 3 search keywords capturing the core service (e.g., `migrate-to-rust`, `bigquery`, `storage`, `iam`, `gke`).

### Phase 2: High-Speed Catalog Query
1. Run the local navigator script to discover matching skills:
   ```bash
   python3 /opt/floworkos/skills/google-skills-navigator/scripts/query_google_skills.py search <keyword>
   ```
2. Inspect the match candidates and their trigger descriptions to choose the exact skill that applies.

### Phase 3: Surgical Skill Retrieval (JIT Loading)
1. Fetch and stage the target skill into a temporary path:
   ```bash
   python3 /opt/floworkos/skills/google-skills-navigator/scripts/query_google_skills.py fetch <skill-name> -o /tmp/active_skill_<skill-name>.md
   ```
2. Read the surgical instructions using `read_file` with targeted line slicing.
3. Obey the specific Execution Contract and bounded error loops (max 5 iterations) stipulated in the retrieved skill.

### Phase 4: Execution & Verification
1. Execute the actions instructed by the retrieved skill (e.g., generating Terraform, running gcloud validation commands, or executing Rust migration steps).
2. Clean up temporary skill files in `/tmp` upon task completion to keep the filesystem pristine.

## 4. Verification
1. **Catalog Integrity**: Verify `/opt/floworkos/skills/google-skills-navigator/data/index.json` contains valid JSON with a non-empty `skills` array.
2. **CLI Executability**: Run `python3 /opt/floworkos/skills/google-skills-navigator/scripts/query_google_skills.py search gemini` -> Must exit with Code 0 and show results.
3. **Quality Gate Compliance**: Run `node /opt/floworkos/skills/lint_skills.js` -> Must pass all checks with Exit Code 0.
4. **Anti-Symlink Audit**: Run `find /opt/floworkos/skills/google-skills-navigator -type l` -> Must return 0 symlinks.

## 5. Failure Modes
1. **Network Disconnected During Remote Fetch**:
   - *Cause*: Host machine has no outbound internet access.
   - *Recovery*: Use local cached index and existing system skills in `/opt/floworkos/skills/`.
2. **Skill Not Found in Catalog**:
   - *Cause*: Keyword mismatch or unregistered custom skill name.
   - *Recovery*: Broaden search query via `search <generic-term>` (e.g., `cloud` or `agent`) to find related meta-skills.
3. **Rate Limiting on Raw GitHub Fetch**:
   - *Cause*: Too many repetitive curl/HTTP requests to GitHub CDN.
   - *Recovery*: Navigator script automatically caches and prefers local `data/index.json`.

## 6. Prohibitions & Anti-Patterns
- NEVER inject all 100+ skills into base prompts (`00_preamble.md`, etc.). Always load JIT.
- NEVER load more than 2 skills simultaneously into active conversation context.
- NEVER create filesystem symlinks inside `/opt/floworkos/skills/`.
- NEVER bypass the empirical Exit Code 0 verification requirement when running generated scripts.
