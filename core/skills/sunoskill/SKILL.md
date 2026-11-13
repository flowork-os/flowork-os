---
name: sunoskill
description: End-to-end procedural playbook for downloading songs, isolating center vocal tracks, time-stretching audio to exactly 59 seconds for YouTube Shorts Uno bypass, and translating lyrics into rhythmic Latin PinYin for Suno AI re-arrangement.
domain: shell_system
keywords:
  - suno
  - audio
  - vocal
  - isolation
  - timestretch
  - atempo
  - ffmpeg
  - ffprobe
  - ytdlp
  - youtube
  - shorts
  - copyright
  - bypass
  - mandarin
  - pinyin
  - translation
  - lyrics
  - arrangement
  - generative
  - workflow
author: Awenk Audico & Mr. Flow Architecture Board
version: 1.0.0
---

# 🎵 Suno AI Vocal Transformation & Shorts Engineering (sunoskill)

## 1. Executive Summary & Objective
The `sunoskill` playbook establishes an automated, end-to-end production workflow to transform copyrighted long-form songs into 100% copyright-free, monetizable YouTube Shorts audio. The pipeline downloads source audio from YouTube or local media, extracts the center vocal track while suppressing side instruments, compresses the full song duration into exactly 59 seconds via extreme time-stretch (`atempo`) to evade automated Content ID (Uno/Audiam) matching, translates the original lyrics into metrically aligned phonetic Latin Mandarin (PinYin), and structures the prompt for generative Suno AI re-arrangement.

## 2. Prerequisites & Tool Dependencies
- **CLI Utilities:** `yt-dlp` (`/usr/local/bin/yt-dlp`), `ffmpeg` (`/usr/bin/ffmpeg`), `ffprobe` (`/usr/bin/ffprobe`).
- **Flowork Tools:** `run_shell_command`, `read_file`, `write_file`.
- **Target Directories:**
  - Processing scratchpad: `/opt/floworkos/documents/suno_experiment/`
  - User deliverables: `/home/awenkaudico/Documents/suno_experiment/`
- **Audio Output Constraints:**
  - Sped-up duration must be $\le 59.02$ seconds to guarantee compliance with the 60-second YouTube Shorts threshold.
  - Channels: Mono center extraction (`pan=mono|c0=0.5*c0+0.5*c1`).
  - Frequency vocal bandpass: Highpass 180 Hz, Lowpass 4200 Hz.

## 3. Standard Operating Procedure (SOP)

### Step 1: Song Acquisition via `yt-dlp`
Acquire the highest-quality audio stream from YouTube without downloading video bloat:
```bash
TARGET_URL="https://www.youtube.com/watch?v=..."
WORK_DIR="/opt/floworkos/documents/suno_experiment"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

yt-dlp -x --audio-format wav --audio-quality 0 -o "source_song.%(ext)s" "$TARGET_URL"
```

### Step 2: Center Vocal Isolation and 59-Second Time-Stretch
1. Isolate the lead vocal sitting in the stereo center channel while cancelling panned side instruments, applying voice frequency bandpass and dynamic normalization:
```bash
ffmpeg -y -i source_song.wav \
  -af "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=180,lowpass=f=4200,dynaudnorm" \
  vocal_isolated.wav
```

2. Probe the exact duration of the isolated vocal:
```bash
ORIG_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 vocal_isolated.wav)
```

3. Calculate the time-stretch speedup factor. The operator can choose either:
- **Mode A (Exact 59s Shorts Limit):** $S = \text{ORIG\_DUR} / 59.0$
- **Mode B (Natural Upbeat +30% Speedup):** $S = 1.30$ (`atempo=1.30`) to retain clear vocal articulation while evading Content ID hash algorithms.

Chain multiple `atempo` filters (max 2.0 per filter stage) to reach the exact target ratio:
```python
# Compute chained atempo stages
speed = float(orig_dur) / 59.0
factors = []
rem = speed
while rem > 2.0:
    factors.append(2.0)
    rem /= 2.0
factors.append(rem)
atempo_str = ",".join([f"atempo={f:.8f}" for f in factors])
```

4. Render the 59-second time-stretched vocal artifact:
```bash
ffmpeg -y -i vocal_isolated.wav -af "$ATEMPO_STR" -t 59 output_vocal_59s.mp3
ffmpeg -y -i vocal_isolated.wav -af "$ATEMPO_STR" -t 59 output_vocal_59s.wav
cp -f output_vocal_59s.* /home/awenkaudico/Documents/suno_experiment/
```

### Step 3: Lyrical Translation into Phonetic Latin Mandarin (PinYin)
Translate the song's verse, chorus, and bridge from Indonesian into rhythmic Mandarin written strictly in **standard Latin alphabet (PinYin)** without Chinese Hanzi characters, ensuring:
1. Syllable count matches the vocal melody cadence of the original Indonesian verses.
2. Emotional meaning is preserved (longing, heartbreak, romantic nostalgia).
3. Plain ASCII letters A-Z avoid tofu rendering boxes or clipboard encoding corruption across all operating systems.

## 4. Verification & Quality Gates (Exit Code 0)
Every execution of `sunoskill` must pass the following empirical quality checks:
1. **Duration Compliance:**
   ```bash
   ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 output_vocal_59s.mp3
   ```
   *Gate:* Must return a duration between 58.50 and 59.02 seconds with Exit Code 0.
2. **File Integrity:**
   Both `.mp3` and `.wav` output files must exist and be non-empty ($> 100\text{ KB}$).
3. **Phonetic Latin Script:**
   The generated Mandarin lyrics must contain 100% Latin characters (`[A-Za-z\s.,!?'-]`) and zero unmapped unicode blocks.

## 5. Failure Modes, Edge Cases & Recovery
- **Issue: `yt-dlp` JS runtime warning or throttling:**
  - *Remedy:* Pass `--force-ipv4` and fallback to standard m4a/opus extraction before WAV transcode.
- **Issue: Mono source recording (no stereo panning):**
  - *Remedy:* Center cancellation cannot extract side instruments on mono files. Fallback to frequency vocal bandpass (`highpass=f=200,lowpass=f=3800,afftdn=nf=-20`) directly.
- **Issue: `atempo` speedup factor exceeds 100x:**
  - *Remedy:* Reject files exceeding 90 minutes. Normal songs ($\le 10$ minutes) will yield a speed factor $\le 10.2\text{x}$.

## 6. Prohibitions & Anti-Patterns
- **NEVER** crop or trim the song to 59 seconds; it MUST be time-stretched so the entire musical journey is compressed into 59 seconds.
- **NEVER** use Chinese Hanzi characters in the primary prompt block unless explicitly requested, as Latin PinYin prevents display boxes and is fully parsed by Suno AI.
- **NEVER** leave untracked temporary WAV files in `/tmp` without mirroring final deliverable artifacts to `/home/awenkaudico/Documents/suno_experiment/`.
