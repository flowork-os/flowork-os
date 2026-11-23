# Implementation Plan: Google Skills Sovereign Navigator for Flowork OS

## 1. Objective
Integrate the official Google Skills repository (`google/skills`) into Flowork OS as a sovereign meta-skill (`google-skills-navigator`) residing in `/opt/floworkos/skills/google-skills-navigator/`. This provides on-demand, Just-In-Time (JIT) skill discovery, querying, and execution for 100+ Google Cloud, Gemini, and developer workflows while strictly adhering to the Flowork Anti-Bloat Law (Zero Token Bloat) and passing the sovereign skill linter (`lint_skills.js`).

## 2. Key Files & Context
- Target Directory: `/opt/floworkos/skills/google-skills-navigator/`
- Target Skill Document: `/opt/floworkos/skills/google-skills-navigator/SKILL.md`
- Target Utility Script: `/opt/floworkos/skills/google-skills-navigator/scripts/query_google_skills.py`
- Local Cache Catalog: `/opt/floworkos/skills/google-skills-navigator/data/index.json`
- Quality Gate Validator: `/opt/floworkos/skills/lint_skills.js`
- Reference Skill: `/opt/floworkos/skills/app-cleanroom-replicator/SKILL.md`

## 3. Mandatory Standards & Invariants
1. **Frontmatter Constraints:**
   - `name`: `google-skills-navigator`
   - `domain`: `code_dev`
   - `description`: Minimum 20 characters, highly descriptive routing trigger.
   - `keywords`: EXACTLY 20 English keywords.
   - `version`: `1.0.0`
   - `author`: `Flowork Architecture Board`
2. **Mandatory Sections in `SKILL.md`:**
   - `## 1. Objective`
   - `## 2. Prerequisites`
   - `## 3. Standard Operating Procedure (SOP)`
   - `## 4. Verification`
   - `## 5. Failure Modes`
   - `## 6. Prohibitions & Anti-Patterns`
3. **Anti-Bloat & Zero Symlink Invariant:**
   - No symlinks anywhere in `/opt/floworkos/skills/google-skills-navigator/`.
   - Never inject 100+ skills into base prompts or active context.
   - JIT load a maximum of 1-2 specific skills per operational task.

## 4. Implementation Steps
1. **Directory Setup:**
   Create `/opt/floworkos/skills/google-skills-navigator/` and subdirectories `scripts/` and `data/`.
2. **Seed Local Offline Cache:**
   Copy the verified catalog `index.json` from the temporary repository clone into `data/index.json` so the skill operates 100% offline with zero external network dependency, while retaining an automatic fallback to live GitHub fetch.
3. **Build Query Helper CLI (`scripts/query_google_skills.py`):**
   Author a high-speed Python script (Exit Code 0 verified) with subcommands:
   - `search <query>`: Fuzzy and keyword search over titles and descriptions in `index.json`.
   - `show <skill-name>`: Display metadata and direct raw content or local/remote path.
   - `fetch <skill-name>`: Retrieve a skill's `SKILL.md` to a temporary task path for surgical reading.
4. **Author `SKILL.md`:**
   Author `/opt/floworkos/skills/google-skills-navigator/SKILL.md` complying with all 6 Flowork OS quality gates, containing detailed SOPs for searching, evaluating, and applying Google skills (such as `migrate-to-rust`, `agent-platform-inference`, `gke-inference`, etc.).
5. **Quality Gate Verification:**
   Execute `node /opt/floworkos/skills/lint_skills.js` and verify Exit Code 0 with 8/8 skills passing.
6. **Functional Verification:**
   Execute `python3 /opt/floworkos/skills/google-skills-navigator/scripts/query_google_skills.py search rust` and verify stdout and Exit Code 0.

## 5. Verification & Testing
- Quality Gate: `node /opt/floworkos/skills/lint_skills.js` -> 0 failures.
- CLI Test: `python3 /opt/floworkos/skills/google-skills-navigator/scripts/query_google_skills.py search "cloud storage"` -> returns matching skills.
- Zero Symlinks Test: `find /opt/floworkos/skills/google-skills-navigator -type l` -> returns empty.
