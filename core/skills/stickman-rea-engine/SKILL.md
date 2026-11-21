---
name: stickman-rea-engine
description: Unified autonomous viral concept remake (REA) pipeline, YouTube reference video ingestion, anti-duplicate ledger, directorial storytelling, and soulful 2D stickman rendering.
domain: code_dev
keywords:
  - stickman
  - rea
  - remake
  - youtube
  - shorts
  - deduplication
  - video_pipeline
  - animation
  - scriptwriting
  - audio_mastering
  - ffmpeg
  - procedural
  - retention
  - hook
  - virality
  - sound_design
  - foley
  - seo
  - metadata
  - render
---

# Objective
The `stickman-rea-engine` skill provides a comprehensive, end-to-end autonomous production pipeline for transforming viral curiosity, historical paradoxes, and engineering concepts from reference YouTube channels into 100% original, copyright-safe, high-retention 9:16 YouTube Shorts. It unifies benchmark channel intelligence, automated deduplication checks, viral scriptwriting, directorial comedic timing, expressive 2D stickman character animation, procedural Foley soundscapes, dynamic kinetic typography, and multi-platform SEO packaging.

# Prerequisites
1. **System & Environment:** Flowork OS running Linux kernel with NVMe swap enabled (`/swapfile`, `vm.swappiness=10`).
2. **Audio/Video Tools:** FFmpeg with `libx264`, `aac`, and `drawtext` support; `flowork-ffmpeg-mcp` tools (`check`, `probe`, `loudness`, `look`).
3. **Speech & Audio Synthesis:** `edge-tts` (Neural voiceover, rate +14%), NumPy procedural waveform synthesis for Foley and percussion.
4. **Toolchain & Libraries:** Python 3.10+ with standard library (`sqlite3`, `json`, `re`, `subprocess`, `argparse`, `datetime`) and Pillow (PIL).
5. **Ledger Registry:** Persistent SQLite database at `/opt/floworkos/history/rea_registry.db` and JSON mirror at `/opt/floworkos/history/rea_registry.json`.
6. **Title & SEO Scoring:** YouTube creator suite scripts (`title.py`, `deadair.py`, `retention.py`).

# Standard Operating Procedure

## 1. Reference Channels & Concept Benchmark Intelligence
The engine continuously models high-performing curiosity and engineering concepts from benchmark channels:
- **Primary Benchmark Channel:** `@RicksClips3000` (Rick's Clips) — Viral engineering, historical phenomena, and cognitive paradox Shorts.
- **Top Concept Candidates Pipeline:**
  1. `VS1Z_Q-Klt8`: *"The Ancient Jar That Warned an Empire"* (35M views — 132 AD Zhang Heng dragon seismoscope & bronze frogs).
  2. `0m6G8pDtzNs`: *"The Job Nobody Wants in Japan"* (18M views — Tokyo subway pushers / Oshiya phenomenon).
  3. `Mz72MuPgnGY`: *"Why Sailors Carried Storm Oil"* (16M views — Benjamin Franklin wave calming & fluid physics).
  4. `GM9UKnZ6JFw`: *"What the Grave Bell Really Meant"* (13M views — Safety coffins & Victorian taphophobia).
  5. `HxqtHI62otM`: *"The Pink Prison Cell Experiment"* (11M views — Baker-Miller pink psychological aggression dampening).
  6. `lnYLIWP2l-I`: *"Levels of Pirate Cannonballs"* (9.9M views — Chain shot, canister shot, and maritime ballistics).

## 2. Completed REA Production Catalog (Active Ledger)
All final video files, metadata, and contact sheets reside strictly in `/home/awenkaudico/Documents/videos/finish/` (mirrored in `/opt/floworkos/documents/videos/finish/`):

| ID | Title & Concept | Reference URL | File Deliverable | Specs & Metrics |
|---|---|---|---|---|
| **#1** | **Why Perfect Railroads Don't Work (Conical Wheels)** | `ref_railroads_01` | `STICKMAN_RAILROADS_VIRAL_9X16.mp4` | 54.60s, 5.7 MB, 1080x1920 @ 30fps CFR, -15.1 LUFS, -1.0 dBTP, Title 100/100 |
| **#2** | **Why Roller Coasters NEVER Use Circle Loops (12G Clothoid Loop)** | `ref_coaster_02` | `STICKMAN_COASTER_VIRAL_9X16.mp4` | 54.80s, 3.8 MB, 1,644 frames @ 30fps CFR, -14.8 LUFS, -0.9 dBTP, Title 100/100 |
| **#3** | **The Instinct That Makes You Crash (Target Fixation)** | `@RicksClips3000/aD73kaL_PtY` | `STICKMAN_TARGET_FIXATION_9X16.mp4` | 54.70s, 4.2 MB, 1,641 frames @ 30fps CFR, -15.2 LUFS, -1.0 dBTP, Title 100/100 |

Associated deliverables generated for every completed project:
- `<TOPIC>_VIRAL_9X16.mp4`: Master video with burned yellow kinetic typography + embedded soft English subtitle stream.
- `<TOPIC>_VIRAL_9X16.txt`: Plain text sidecar metadata (Title options, description, pinned comment, tags).
- `<TOPIC>_SEO_PACKAGE.md`: Full multi-platform SEO package with YouTube title scoring metrics (score >= 90/100).
- `<topic>_contact_sheet.png`: 4x3 visual grid verifying character expression soul and safe area compliance.

## 3. Deduplication Ledger Operation
Before any concept remake begins, query the ledger to avoid duplicate remakes:
```bash
# Check if a concept or reference URL was already produced
python3 /opt/floworkos/skills/stickman-rea-engine/ledger.py check "<url_or_title>"

# List all tracked remakes
python3 /opt/floworkos/skills/stickman-rea-engine/ledger.py list
```
If `exists: true`, halt immediately with exit code 2 and reference the existing output path.

## 4. 5-Stage Directorial Heartbeat Engine
1. **Beat 1 (0–3s) - Cognitive-Gap Hook:** Immediate visual paradox or shock. Zero greetings or pleasantries.
2. **Beat 2 (3–12s) - Intuition Disruption:** State why common sense fails catastrophically.
3. **Beat 3 (12–25s) - Slapstick Disaster:** High-energy comedic physical failure with expressive stickman animations (bugging eyes, accordion squish, neck brace, spinning dizzy stars).
4. **Beat 4 (25–42s) - Mechanical Epiphany:** Clear, intuitive animated explanation of the true mathematical or physical solution.
5. **Beat 5 (42–50s) - Stickman Triumph:** Stickman masters the principle with comedic swagger (cool sunglasses, smooth ride).
6. **Beat 6 (50–55s) - Infinite Loop Bridge:** The concluding line flows seamlessly back into the opening hook word for infinite looping.

## 5. Audio Engineering & Master Loudness Pipeline
1. Synthesize neural speech via `edge-tts` (rate +14%) and parse timestamps from `voice.vtt`.
2. Generate procedural 124–128 BPM percussive groove and cue-matched Foley sound effects (whip whoosh, pop, alarm, crash, bell, sparkle).
3. Master full audio mix using two-pass EBU R128 loudness normalizer:
   - Integrated Loudness: `-14 LUFS` (±2 LUFS)
   - True Peak Ceiling: `<= -1.0 dBTP` (+0.1 dB tolerance)
   - Format: 48,000 Hz AAC mono (192–256 kbps)

## 6. Procedural 2D Stickman Renderer & Packaging
1. Stream procedural PIL drawing directly into FFmpeg `rawvideo rgb24`:
   - Resolution: `1080x1920` (9:16 vertical), Constant 30.00 fps CFR.
   - Dynamic boxed subtitle pill (`InterDisplay-Black`, active-word yellow `#FFD200` on dark pill, Y ≈ 1380–1450).
2. Embed soft subtitle stream (`mov_text`, language `eng`) without re-encoding video.
3. Package all deliverables into `/home/awenkaudico/Documents/videos/finish/` and mirror to `/opt/floworkos/documents/videos/finish/`.
4. Register completion in SQLite and JSON ledger.

# Verification
1. **Deduplication Check:** `python3 /opt/floworkos/skills/stickman-rea-engine/ledger.py check "<topic>"` returns valid status.
2. **Audio Compliance:** Measured via `flowork-ffmpeg-mcp loudness --measure-only` within `-14.0 ± 2.0 LUFS` and `<= -1.0 dBTP`.
3. **Visual Frame Verification:** Contact sheets inspected via `flowork-ffmpeg-mcp look` or PIL to confirm character soul and safe margins.
4. **Platform Compliance:** `flowork-ffmpeg-mcp check --platform shorts` confirms 0 errors and 0 warnings.
5. **Anti-Leak Integrity:** Run `git status` to verify no video deliverables or render directories are tracked in git.

# Failure Modes
1. **Duplicate Remake Collision:** Concept already exists in ledger. Handled by exiting with code 2 and linking to existing file.
2. **Duration Overrun (>55s):** Voice script too long. Handled by tightening script to <= 150 words or adjusting speech speed to +16%.
3. **Variable Frame Rate Jitter:** Handled by streaming frames strictly through FFmpeg `-f rawvideo -r 30` to enforce 30.00 fps CFR.
4. **Audio Clipping or YouTube Volume Penalty:** Handled by automated two-pass EBU R128 loudness normalization.
