---
name: last30days
description: Research what people actually say about any topic in the last 30 days across social media, reddit, x, and developer communities.
domain: browser
keywords:
  - research
  - trends
  - reddit
  - youtube
  - hackernews
  - recency
  - social_signals
  - sentiment
  - web_search
  - citations
  - query_expansion
  - multi_source
  - engagement
  - analysis
  - data_mining
  - scraping
  - doctor
  - diagnostics
  - feed
  - sovereign
---

# 📰 FLOWORK OS SOVEREIGN SKILL: LAST30DAYS

## 1. Objective
Equip Mr. Flow and Flowork OS agents to research recent public sentiment, trends, and discussions from the last 30 days across social and developer platforms (Reddit, X, YouTube, TikTok, Hacker News, Polymarket, GitHub, and the web) with verified citations and health auditing.

## 2. Prerequisites
1. Python 3.12+ runtime available on Flowork OS.
2. Local Python engine located at `/opt/floworkos/skills/last30days/scripts/last30days.py`.
3. Valid permissions to read references in `/opt/floworkos/skills/last30days/references/`.
4. Execution tools: `run_shell_command`, `read_file`, `write_file`.

## 3. Standard Operating Procedure
1. **Bootstrap and Directory Binding**:
   Bind `SKILL_DIR` to `/opt/floworkos/skills/last30days`. Retain this path across commands.
2. **Interpreter Resolution**:
   Validate Python runtime before running engine commands:
   `python3 /opt/floworkos/skills/last30days/scripts/last30days.py --preflight`
3. **Execution & Search**:
   Run the CLI engine with target query keywords and platforms:
   `python3 /opt/floworkos/skills/last30days/scripts/last30days.py "<topic>" --emit=compact`
4. **Synthesis & Evidence Extraction**:
   Extract at least two attributed real comments and cite authoritative sources. Maintain strict adherence to raw platform data.
5. **Output Delivery**:
   Save reports and summaries to `/opt/floworkos/documents/` or `$HOME/Documents/Last30Days/`.

## 4. Verification
1. Run preflight diagnostic check:
   `python3 /opt/floworkos/skills/last30days/scripts/last30days.py doctor`
2. Validate that engine runs without unhandled exceptions and outputs valid JSON or formatted Markdown.
3. Verify compliance with sovereign skill standards using `/opt/floworkos/bin/flowork-lint-skills`.

## 5. Failure Modes
1. **API Rate Limiting or Missing Tokens**: When optional API keys are absent, fallback gracefully to unauthenticated sources (Hacker News, public Reddit feeds, Polymarket).
2. **Empty Search Returns**: If a topic has zero hits within 30 days, broaden keywords rather than hallucinating recent mentions.
3. **Stale References or Broken Modules**: If modules fail to import, run `doctor` to isolate missing dependencies.

---

## Detailed Reference & Routing
Paths resolve relative to `SKILL_DIR`.

| Condition | Required read | Return point |
|---|---|---|
| Before any engine command | Read `references/runtime.md` in full. | Stale-clone check, interpreter bootstrap, and trusted save/config resolution precede commands. |
| Library search, feed, or queue intent | Read `references/library-queue.md` in full. | Execute the selected offline fast path, then stop. |
| First-run setup is required | Read `references/setup-wizard.md` in full. | Evaluate all credential sources; complete the applicable host flow. |
| Source repair requested or indicated by doctor | Read `references/setup-wizard.md` in full. | Use repair entry and preserve user consent. |

## Security & Permissions
- Does not modify or write to remote social media platforms.
- Stores local research briefings as `.md` files in designated workspace directories.
- Hacker News and Polymarket are always available without third-party API keys.
