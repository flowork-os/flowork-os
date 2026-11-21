---
name: youtube-creator-suite
description: "Comprehensive YouTube creator workflow engine: concept planning, scriptwriting, hook scoring, editing, retention analytics, title packaging, SEO tags, chapters, and channel audits."
domain: code_dev
keywords:
  - youtube
  - shorts
  - creator_suite
  - scriptwriting
  - hook_scoring
  - title_optimization
  - packaging
  - retention_analysis
  - chapters_generator
  - dead_air_cut
  - swipe_file
  - seo_tags
  - comment_pinning
  - thumbnail_strategy
  - channel_audit
  - video_editing
  - ffmpeg
  - metadata_scoring
  - analytics
  - engagement
---

# Objective
The `youtube-creator-suite` skill unifies all YouTube growth, production, and optimization playbooks into a single comprehensive command center. It provides programmatic tools and structured workflows for the entire creator lifecycle: concept validation, viral scriptwriting with hook scoring, jump-cut silence removal, automatic chaptering, title CTR scoring, SEO tagging, retention diagnosis, and channel-wide audits.

# Prerequisites
1. **Python Runtime:** Python 3.10+ with standard libraries (`json`, `re`, `subprocess`, `argparse`, `sys`).
2. **Media Engine:** FFmpeg with `silencedetect` and `loudnorm` filters.
3. **Creator Suite Toolset:** Local Python scripts located at `/opt/floworkos/skills/youtube-creator-suite/scripts/`:
   - `hookscore.py` & `hooks.json`: Analyzes and scores opening hooks (0–100 scale).
   - `title.py`: Evaluates title CTR potential, character lengths, and curiosity gaps.
   - `deadair.py`: Detects and removes dead air or silent pauses from speech audio.
   - `chapters.py`: Generates YouTube timestamp chapters from transcripts or EDL markers.
   - `retention.py`: Models audience retention curves and flags drop-off risk zones.
   - `swipe.py`: Queries proven viral hook and storytelling swipe templates.
4. **Metadata Standards:** Titles <= 45 chars for mobile readability, uppercase key phrases, dual thumbnail text contrast.

# Standard Operating Procedure

## Phase 1: Planning & Hook Engineering
1. **Concept & Curiosity Gap:** Formulate a single clear curiosity gap without multi-clause confusion.
2. **Hook Formulation & Scoring:** Run `hookscore.py` against candidate opening lines:
   ```bash
   python3 /opt/floworkos/skills/youtube-creator-suite/scripts/hookscore.py "Scientists thought this loop was safe, until riders started blacking out."
   ```
   *Requirement:* Target score $\ge 85/100$. Reject openings that use greetings, self-introductions, or generic statements.
3. **Swipe File Query:** Pull proven retention structures from the viral swipe library:
   ```bash
   python3 /opt/floworkos/skills/youtube-creator-suite/scripts/swipe.py --category curiosity
   ```

## Phase 2: Scriptwriting & Pacing Structure
1. Structure long-form videos with the **Heartbeat Pacing Arc** (re-hooking every 90–120 seconds).
2. For YouTube Shorts, strictly conform to **50–55s duration** at 145–160 WPM (~130–150 words total).
3. Ensure the final sentence serves as a loop bridge connecting back to the opening statement.

## Phase 3: Edit & Dead Air Elimination
1. Detect and trim pauses longer than 0.3s using `deadair.py`:
   ```bash
   python3 /opt/floworkos/skills/youtube-creator-suite/scripts/deadair.py input_speech.wav --threshold -35 --min-silence 0.3 --output tight_speech.wav
   ```
2. Verify dialogue energy maintains continuous momentum without clipping word plosives.

## Phase 4: Packaging (Title, Thumbnail & Chapters)
1. **Title CTR Evaluation:** Test candidate titles using `title.py`:
   ```bash
   python3 /opt/floworkos/skills/youtube-creator-suite/scripts/title.py "Why Roller Coasters NEVER Use Circle Loops"
   ```
   *Gate:* Must achieve score >= 90/100, length <= 50 characters, zero punctuation spam.
2. **Thumbnail Concept Pairing:** Thumbnail must illustrate the tension rather than repeat title words. Use 2–4 bold uppercase badge words (`12G DISASTER`).
3. **Chapter Generation:** Generate timestamped chapters for long-form uploads:
   ```bash
   python3 /opt/floworkos/skills/youtube-creator-suite/scripts/chapters.py transcript.json --min-duration 30
   ```

## Phase 5: SEO & Engagement Setup
1. **Description & Tags:** Include primary keyword in line 1 of the description, followed by chapter marks, 3 relevant hashtags, and SEO tags.
2. **Pinned Comment Strategy:** Draft an engagement-sparking pinned comment presenting an open binary debate or thought-provoking prompt within 1 hour of publishing.

## Phase 6: Retention Analytics & Post-Mortem Audit
1. Audit published video retention graphs using `retention.py`:
   ```bash
   python3 /opt/floworkos/skills/youtube-creator-suite/scripts/retention.py retention_data.csv
   ```
2. Identify dips exceeding 15% and categorize the cause: boring b-roll, pacing lull, or visual confusion.

# Verification
1. **Hook Quality:** Execute `hookscore.py` on the chosen script hook; ensure score is $\ge 85$.
2. **Title Quality:** Execute `title.py` on the candidate title; ensure score is $\ge 90$.
3. **Audio Tightness:** Verify that no dead air gaps $> 0.5\text{s}$ remain in the final render.
4. **Metadata Deliverable:** Ensure every release folder contains an isolated `.txt` and `.md` SEO package.

# Failure Modes
1. **Weak Opening Retention (Dip at 0–5s):** Caused by slow introductory context. Mitigated by immediate visual shock and cutting directly to the dilemma in frame 1.
2. **Mobile Title Truncation:** Titles exceeding 50 characters are truncated on mobile screens. Mitigated by `title.py` hard character length validation.
3. **Over-Editing Speech Clippings:** Overly aggressive silence removal cutting off natural breath or word endings. Mitigated by enforcing a 0.05s padding buffer on cut boundaries.
