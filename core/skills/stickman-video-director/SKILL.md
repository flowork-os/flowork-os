---
name: stickman-video-director
description: Autonomous viral stickman video direction and faceless channel orchestration workflow. Turns scripts or articles into multi-style animated stickman storyboards, narration audio, dynamic captions, and sound effects.
domain: code_dev
keywords:
  - stickman_animation
  - video_director
  - faceless_channel
  - storyboard_engine
  - narrative_arc
  - golden_hook
  - viral_scripting
  - visual_pacing
  - gemini_prompts
  - sound_effects
  - caption_sync
  - voiceover_direction
  - classic_minimalist
  - modern_beanie
  - dark_psychology
  - explainer_video
  - ffmpeg_rendering
  - amber_noir
  - desktop_actuator
  - flowork_studio
author: Flowork Architecture Board
version: 1.0.0
---

# 🎬 FLOWORK OS SOVEREIGN SKILL: STICKMAN VIDEO DIRECTOR

## 1. Objective
Equip Mr. Flow with an autonomous video directing and orchestration pipeline to transform raw articles, concepts, or scripts into production-ready viral animated stickman videos for faceless storytelling, science explainers, and dark psychology channels.
- Eliminate expensive SaaS video animation subscriptions ($50+/month) through 100% open-source local orchestration.
- Structure every narrative through the **5-Stage High-Completion Heartbeat Engine** ensuring high viewer retention.
- Deliver production artifacts: calibrated storyboard breakdown, 10-second standalone visual prompts, voiceover timing, single-line semantic subtitles, and causal sound effects (SFX).

## 2. Prerequisites
1. **Flowork Multimedia & Audio Stack**:
   - `ffmpeg`: Native CLI installed on Linux for stitching video clips, audio tracks, and burned-in subtitles.
   - Sovereign Connector (`:9099`): High-throughput LLM gateway for script generation and pacing calibration.
   - `desktop_actuator`: Hardware display capture and virtual HID controller if interacting with local video editor GUI (Flowork Studio Hub / Cutvii).
2. **Project Working Territory**:
   - All production artifacts staged strictly inside `stickman_project/` (`storyboard.json`, `prompts/`, `audio/`, `captions.srt`).

## 3. Standard Operating Procedure (SOP)

### Phase 1: Setup & Format Locking Gate
Require these core parameters before generating output:
1. **Aspect Ratio**: `16:9` (Long-form YouTube) or `9:16` (Shorts / TikTok / Reels).
2. **Target Duration**: Multiples of 10 seconds (`30s`, `60s`, `90s`, `180s`, `300s`).
   - Clip Count $N = \text{Duration} / 10$ (default: 6 clips for 60 seconds).
   - Voiceover pacing: strictly ~20–25 English words per 10-second clip (~120–150 words for 60s).
3. **Visual Style**:
   - *Style 1 (Classic Minimalist)*: High-contrast white stickman on black obsidian background (or black on white).
   - *Style 2 (Modern Beanie)*: Red beanie character with perspective grid and floating cyan glass UI.
   - *Style 3 (Prehistoric Hand-Drawn)*: Earthy caveman styling with comedic timing.
   - *Style 4 (Cozy Storytelling)*: Minimalist white-filled figures in full-color 2D atmospheric backgrounds.
   - *Style 5 (Historical Cartoon)*: Expressive cel-shaded figures in period settings.
   - *Style 6 (Amber Noir)*: High-contrast orange-hoodie figure with cinematic chiaroscuro shadows.

### Phase 2: The 5-Stage Heartbeat Narrative Engine
Structure the script across $N$ clips according to the retention curve:
1. **Beat 1: Golden Hook (0–5s)**: Immediate curiosity trigger, visual paradox, or counter-intuitive premise. Never open with pleasantries or generic greetings.
2. **Beat 2: Disrupting Assumptions (5–15s)**: Challenge conventional wisdom in a single devastating sentence to create cognitive dissonance.
3. **Beat 3: Unveiling Insider Secrets (15–35s)**: Reveal the hidden mechanism, psychological truth, or behind-the-scenes reality.
4. **Beat 4: Ultimate Truth Revelation (35–50s)**: Deliver the core takeaway with maximum philosophical or tactical payoff.
5. **Beat 5: Elevation & Debate Prompt (50–60s)**: Conclude with a memorable punchline and an irresistible question that compels viewers to comment.

### Phase 3: Phase A — Director's Storyboard Proposal
Generate `stickman_project/storyboard.json` containing:
- Target ratio, duration, and style declaration.
- Table of scenes with timestamp intervals (`[00:00-00:10]`, `[00:10-00:20]`, etc.).
- Spoken voiceover text with exact word count verification.
- Visual action descriptions: character posture, props, and camera movement.
- Embedded sound effects cues (`[SFX: vinyl scratch]`, `[SFX: low bass drop]`, `[SFX: clock tick]`).

### Phase 4: Phase B — Standalone Visual Prompt Synthesis
Upon storyboard confirmation, generate $N$ discrete visual generation prompts saved in `stickman_project/prompts/clip_XX.txt`.
- Each prompt must be self-contained (character consistency, lighting, camera framing, background style).
- Include 3 distinct sub-second visual beats per clip to prevent static visual boredom.
- Enforce style rules (e.g. Amber Noir requires deep obsidian shadows and warm incandescent accents).

### Phase 5: Voiceover & Subtitle Synchronization
1. Generate natural speech audio using configured TTS engine or local voice synthesizer.
2. Format subtitles into single-line semantic cues (`captions.srt`):
   - Never break mid-phrase; split along natural grammatical pauses.
   - Restrict to maximum 6-8 words per screen to guarantee readability on mobile displays.

### Phase 6: Procedural Sound Scoring & Final Assembly
1. Compose raw video and speech timeline using local `ffmpeg`:
   ```bash
   ffmpeg -y -loop 1 -i clip_%02d.png -i voiceover.mp3 -vf "subtitles=captions.srt" -c:v libx264 -c:a aac -shortest video_raw.mp4
   ```
2. **Causal Procedural Audio Scoring**:
   Utilize `flowork-sound-forge score` to synthesize and stamp millisecond-accurate sound effects on key visual cuts and transition beats (e.g. whoosh on scene change, thock on point reveal, sub_hit on climax, success on payoff) without external audio file bloat:
   ```bash
   flowork-sound-forge score video_raw.mp4 --cues "0.0:whoosh,5.0:thock,15.2:sub_hit,25.0:riser,55.0:success" -o final_output.mp4
   ```
3. Inspect rendered output with `desktop_actuator` or media probe to confirm audio-visual synchronization.

## 4. Verification
1. **Duration & Beat Alignment**: Verify total runtime equals exact multiple of 10 seconds.
2. **Word Count Strictness**: Verify voiceover word count matches 20-25 words per 10s clip.
3. **Integrity Check**: Run `ffmpeg -v error -i final_output.mp4 -f null -` -> Must return **Exit Code 0** with zero stream corruptions.

## 5. Failure Modes & Recovery
1. **Voiceover Exceeds Clip Bounds**:
   - *Cause*: Voiceover word count exceeds 25 words per 10-second segment.
   - *Recovery*: Trim non-essential filler words and re-pace text to hit exactly ~22 words/clip.
2. **Visual Inconsistency Across Clips**:
   - *Cause*: Prompts omit persistent character descriptions across segments.
   - *Recovery*: Prepend the global Character Style Anchor (e.g., "Minimalist white head, black stick limbs, red knit beanie") into every clip prompt.
3. **Desynchronized Subtitle Pacing**:
   - *Cause*: Mechanical word-splitting without respect for speech pauses.
   - *Recovery*: Regenerate SRT timestamps based on forced audio alignment timestamps.

## 6. Prohibitions & Anti-Patterns
1. NEVER deliver silent videos without causal sound effects (SFX) synchronized to visual cuts.
2. NEVER bundle static external WAV/MP3 files when procedural mathematical SFX can be rendered via `flowork-sound-forge`.
3. NEVER allow voiceover text to desync from visual 10-second clip boundaries.
