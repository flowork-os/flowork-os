---
name: githubtoyoutube
description: Autonomous pipeline converting trending GitHub repositories into high-retention cartoon animated YouTube documentaries and 55-60s vertical shorts with 100% English audio/text, zero-overflow safe margins, visible GitHub repository URLs, non-white backgrounds, rubber-hose kinematics, and stacked FLOWORKOS.COM branding.
triggers:
  - trending github repository to youtube video
  - automate github repo cartoon video
  - github to youtube documentary animation
  - trending code to viral video
  - generate video for github repo
  - convert repo to animation
tags:
  - video_production
  - youtube_automation
  - animation_pipeline
  - stickman_animation
  - pycairo
  - ffmpeg_nvenc
  - edge_tts
  - narrative_cadence
  - sentence_cadence
  - broadcast_vocal_chain
  - automated_subtitles
  - youtube_seo
  - safe_frame_margins
  - github_url_prominence
  - english_only_production
  - bulk_syndication
  - theme_vault_organization
---

# GitHub To YouTube (`githubtoyoutube`)

## 1. Core Directorial Mandates (The 3 Sovereign Laws)

> [!IMPORTANT]
> Every automated video generated under this skill MUST strictly satisfy three non-negotiable production invariants:

### Law 1: 100% English Production (Wajib Bahasa Inggris)
* **Audio Narration:** Exclusively English neural voices via `edge-tts`:
  * `en-US-ChristopherNeural` (Default authoritative male; deep, punchy, crisp cadence).
  * `en-US-GuyNeural` (Energetic, passionate, playful tech enthusiast).
  * `en-US-JennyNeural` (Clear, modern, high-intelligibility female).
  * *Strict Prohibition:* Never use Indonesian, mixed slang, or non-English voices for YouTube productions.
* **On-Screen Typography & Captions:**
  * 100% English text across all assets: Hook title cards, subtitles/captions, dialogue speech bubbles, warning badges, UI cards, error popups, and terminal mockups.
* **Metadata & Packaging:**
  * Title, Description, Tags, Hashtags, and Pinned Comment must be 100% English, engineered for high global CTR and international developer audience retention.

### Law 2: Zero-Overflow & Safe Margin Framing (Tulisan Nggak Boleh Keluar Frame)
* **9:16 Vertical Safe Area (1080x1920):**
  * **Horizontal Safe Zone:** $X \in [90, 990]$ (Minimum 90px margin on left and right; max content width = $900\text{px}$). No text glyph, card boundary, or badge may ever cross $X < 90$ or $X > 990$.
  * **Vertical Safe Zone:** $Y \in [180, 1680]$:
    * Top 180px reserved: Prevents overlap with YouTube Shorts top search, sound title, and channel overlays.
    * Bottom 240px reserved: Prevents overlap with YouTube Shorts bottom title, channel handle, sound tag, and like/comment buttons.
    * Subtitle Anchor: Clamped strictly at $Y \in [1460, 1540]$, ensuring captions sit safely above the bottom action bar.
* **Algorithmic Text Auto-Wrap & Auto-Scale (Mandatory Cairo Math):**
  * Measure extents before rendering via `ctx.text_extents(text)`.
  * If measured width exceeds `max_allowed_width`:
    1. Multi-line word wrapping (`wrap_text_to_width` function splitting words into lines with width $\le \text{max\_width}$).
    2. Dynamic font scaling: `font_size = font_size * min(1.0, max_allowed_width / measured_width)`.
  * Subtitle sizing: Clamped between 46px and 56px, limited to 2–4 punchy words per line.
  * Internal Card Padding: All badges, cards, and dialogue bubbles must maintain a minimum of 24px inner padding. Text must never touch or clip container borders.
  * *Helper Module:* Always utilize `/opt/floworkos/skills/githubtoyoutube/scripts/safe_render_tools.py` (`draw_safe_text_centered`).

### Law 3: Mandatory On-Screen GitHub Repository URL (URL GitHub Wajib Ada)
* **Visual Repository Identifier:**
  * Every generated video MUST prominently and visibly display the repository URL (`github.com/<owner>/<repo>`):
  * **Top Persistent / Periodic Header Pill ($Y \approx 200–260$):** High-contrast glassmorphic pill displaying the GitHub Octocat icon, exact URL `github.com/<owner>/<repo>`, and star count counter pill (`★ 55.4k`).
  * **Scene 1 & Scene 3 Holographic Card:** Showcase the real GitHub web UI header showing the repo URL, author, and star count.
  * **Scene 4 Outro Dual-CTA ($t \ge 50\text{s}$):** Dedicated prominent GitHub Card featuring `github.com/<owner>/<repo>` in bold monospace font with an animated star button, bouncing pointing finger/arrow, and star chime sound effect, explicitly directing viewers to star the repo.
  * *Helper Module:* Use `draw_github_repo_header_pill` and `draw_github_cta_card` from `safe_render_tools.py`.

---

## 2. Creative Storytelling & Directorial SOP (No Rigid Templates!)

> [!NOTE]
> As Creative Director, Mr. Flow engineers original, repo-specific storylines that build tension, expose real developer pain points, and resolve dramatically through expressive stickman cartoon action, expressive developer comedy, and dynamic visual metaphors. Never use static slides or robotic monologues.

### Autonomous Production Pipeline (5 Phases)

1. **Phase 1: Repository Discovery & Research Dossier**
   * Select candidate from instruction or database:
     ```bash
     python3 /opt/floworkos/skills/githubtoyoutube/scripts/githubtoyoutube.py --harvest "<keyword>"
     ```
   * Extract: Exact GitHub URL (`github.com/owner/repo`), star count, core architectural problem solved, and standout features.

2. **Phase 2: English Storyboard Scriptwriting (4-Act Structure)**
   * Target duration: 55–58 seconds (approx. 130–145 spoken English words).
   * **Act 0 (0–3s) — The Center Hook Title:** Provocative, punchy title card centered at safe coordinates ($Y \approx 500–600$), e.g. *"AI JUST HIJACKED YOUR BROWSER!"*.
   * **Act 1 (3–18s) — The Nightmare Pain Point:** Frustrated stickman developer suffering manual repetition, bugs, or crashes.
   * **Act 2 (18–38s) — The GitHub Revelation & Mechanics:** Stickman discovers the repo (displaying `github.com/owner/repo` pill); vector animation illustrates the underlying magic (DevTools protocol, LLM brain, automated pipeline).
   * **Act 3 (38–58s) — The Supercharged Triumph & Dual CTA:** Triumphant celebration, code running at lightning speed, followed by the dedicated Outro CTA Card featuring `github.com/owner/repo` and Star button.

3. **Phase 3: English Audio Synthesis & Timestamp Extraction**
   * Generate broadcast-ready English audio via `edge-tts`:
     ```bash
     edge-tts --voice "en-US-ChristopherNeural" --text "<script_text>" --write-media voiceover.mp3 --write-subtitles timestamps.vtt
     ```
   * Parse word/sentence boundary timestamps to synchronize cartoon gestures, SFX, and captions.

4. **Phase 4: Vector Cartoon Animation & Hardware NVENC Pipeline**
   * Script animations in Python with PyCairo using rubber-hose kinematics, dynamic camera zooms, expressive stick figures, and procedural sound effects.
   * Enforce zero-overflow safe boundaries via `safe_render_tools.py`.
   * Render directly through FFmpeg NVENC pipe (30/60 FPS, finishes in 15–30 seconds):
     ```bash
     ffmpeg -y -f rawvideo -vcodec rawvideo -s 1080x1920 -pix_fmt bgra -r 30 -i - \
       -i voiceover.mp3 -c:v h264_nvenc -preset p4 -cq 22 -pix_fmt yuv420p output.mp4
     ```

5. **Phase 5: Archival, Verification & Ledger Logging**
   * Save deliverables to:
     * System Vault: `/opt/floworkos/documents/videos/<repo-name>-short/<repo-name>_short_58s.mp4`
     * User Vault: `~/Documents/videos/<repo-name>-short/`
   * Generate 3x2 contact sheet (`contact_sheet.png`) for instant visual verification of text framing and GitHub URL placement.
   * Append production entry to `/opt/floworkos/skills/githubtoyoutube/PRODUCTION_LEDGER.jsonl`.

---

## 3. Core Visual & Animation Doctrines

Supported production modes:
1. **Vertical Shorts (9:16, 1080x1920, 55–60s):** High-retention short-form cartoon animations reverse-engineered from `@RicksClips3000`.
2. **Long-Form Documentaries (16:9, 1920x1080, 8–15 mins):** In-depth technical architecture visual documentaries.

### The 8 Visual Laws:
1. **Pure Cartoon Action (No Presentation Slide Templates!):**
   * Characters are expressive stickmen with rubber-hose bending limbs, animated eyes, mouth phonemes, and props. No corporate bullet lists.
2. **Non-White Bright & Vibrant Canvases:**
   * Reject sterile `#FFFFFF` and flat boring black.
   * Preferred palettes: Dark Obsidian (`#0F111A`), Deep Cyber Indigo (`#131424`), Warm Ochre (`#F4EEDD`), or Retro Amber.
3. **Subtle Stacked Watermark:**
   * Two-line glowing monospace watermark (`FLOWORK` / `OS.COM`) anchored at top-right or bottom-right inside safe zone.
4. **Cinematic Camera Moves & Smooth Interpolations:**
   * Smooth ease-in-out (`smoothstep`) pans, dynamic zooms on key moments, and camera shakes on explosions or bugs.
5. **Broadcast Vocal Mastering & Sound Design:**
   * Cartoon SFX (wooshes, pops, typewriter clicks, error buzzers, success chimes).
   * Master Loudness: ITU-R BS.1770-4 / EBU R128 `loudnorm=I=-14.0:TP=-1.0:LRA=4.0`.
   * Automatic Sidechain Vocal Ducking: BGM ducks by -7 dB whenever voice speaks.
6. **Zero-Clipping Safe Area Framing:**
   * Characters, props, and subtitles stay strictly inside the 900px safe width ($X: 90..990$) and 1500px safe height ($Y: 180..1680$).
   * Kinetic captions: 2–4 words per line, 48–56px bold font, white fill with heavy 12px black outline.
7. **First 1–3 Seconds Center Hook Title (Detik Pertama Wajib Judul Nendang):**
   * $t = 0.0\text{s}$ through $t = 3.0\text{s}$ must render a high-impact, centered cartoon title card with contrasting glowing fill and black outline.
8. **Mandatory GitHub URL Visibility & Dual CTA:**
   * Prominently display `github.com/<owner>/<repo>` in header pill during technical explanation and full-card CTA at outro.

---

## 4. Self-Contained Skill Scripts Directory

All scripts and reusable tools reside within `/opt/floworkos/skills/githubtoyoutube/scripts/`:
* `safe_render_tools.py`: Safe frame text measurement, auto-wrapping, auto-scaling, and GitHub URL card renderers.
* `githubtoyoutube.py`: Central harvesting CLI and production coordinator.
* `stickman_engine_v2.py`: PyCairo rubber-hose procedural kinematic animation library.
* `audio_pipeline.py`: Edge-TTS audio synthesis and FFmpeg vocal ducking master.

---

## 5. Dedicated Theme Vault Storage Rule

Every render outputs deliverables directly to:
* System Vault: `/opt/floworkos/documents/videos/<theme_folder>/`
* User Vault: `~/Documents/videos/<theme_folder>/`
