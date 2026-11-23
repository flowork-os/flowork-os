---
name: suno-music-producer
description: End-to-end procedural playbook for neural vocal stem isolation, acoustic copyright filter bypass, Latin PinYin lyric adaptation, Suno AI synthesis, and YouTube compilation mastering.
domain: shell_system
keywords:
  - suno
  - vocal_isolation
  - stem_separation
  - demucs
  - copyright_bypass
  - pitch_modulation
  - atempo
  - timestretch
  - pinyin_translation
  - mandarin_lyrics
  - xianxia_ost
  - ffmpeg
  - ffprobe
  - audio_mastering
  - android_vm
  - flowork_suno_prep
  - vocal_to_piano
  - compilation_builder
  - youtube_shorts
  - generative_audio
---

# Objective
The `suno-music-producer` skill provides a unified, end-to-end production workflow for transforming copyrighted source songs into original, monetizable Suno AI compositions. It unifies neural vocal separation via Demucs, acoustic fingerprint evasion (speed/pitch modulation & vocal-to-piano MIDI conversion), rhythmic Latin PinYin translation, Android Micro-VM media synchronization, and multi-track 1-hour YouTube compilation mastering.

# Prerequisites
1. **Neural Audio Separator:** Demucs AI Hybrid Transformer (`/opt/floworkos/apps/suno-demucs/venv/bin/demucs`).
2. **Audio/Video Transcoder:** FFmpeg and FFprobe with standard codecs and filter chains (`asetrate`, `aresample`, `atempo`, `pan`).
3. **Hardware & Subsystem Bridge:** Flowork Micro-VM with ADB (`/opt/floworkos/android-sdk/platform-tools/adb`).
4. **CLI Utilities:** `yt-dlp` (`/usr/local/bin/yt-dlp`), `flowork-suno-prep` (`/opt/floworkos/bin/flowork-suno-prep`), `flowork-vocal-to-piano`, `flowork-channel-compiler`.
5. **Output Directories:**
   - Scratchpad: `/opt/floworkos/documents/suno_experiment/`
   - User Deliverables: `/home/awenkaudico/Music/suno_ready/` and `/home/awenkaudico/Documents/suno_experiment/`.

# Standard Operating Procedure

## Stage 1: Song Acquisition & Neural Vocal Isolation
1. Download reference audio using `yt-dlp`:
   ```bash
   yt-dlp -x --audio-format wav --audio-quality 0 -o "source_song.%(ext)s" "$TARGET_URL"
   ```
2. Isolate acapella vocals using Demucs AI Hybrid Transformer:
   ```bash
   /opt/floworkos/apps/suno-demucs/venv/bin/demucs --two-stems vocals -n htdemucs -o stems source_song.wav
   ```

## Stage 2: Acoustic Fingerprint Evasion (Copyright Bypass)
Select one of two proven bypass strategies:
1. **Method A — 5x Robot Voice Modulation (Vocal Cadence Preserved):**
   - Compresses 4-minute audio into ~45–54 seconds (strictly under Suno 60-second upload threshold):
   ```bash
   flowork-suno-prep "$SOURCE_URL" --speed 5.0 --mode pitch --launch
   ```
   - Alternatively, apply chained `atempo` and `asetrate` filters:
   ```bash
   ffmpeg -y -i stems/htdemucs/source_song/vocals.wav \
     -af "asetrate=44100*5,aresample=44100" -t 59 -map_metadata -1 output_robot_5x.mp3
   ```
2. **Method B — Vocal-to-Piano Instrumentalization (Zero-Lyrics Bypass):**
   - Tracks fundamental frequency ($F_0$) via YIN algorithm and converts to MIDI piano guide:
   ```bash
   flowork-vocal-to-piano input_vocal.wav output_piano
   ```

## Stage 3: Android Micro-VM Ingestion
1. Mirror modulated audio into host and Android guest storage:
   - Host: `~/Music/suno_ready/<song_title>_suno_robot_5.0x.mp3`
   - Android: `/sdcard/Music/suno_ready/<song_title>_suno_robot_5.0x.mp3`
2. Broadcast Android media scanner intent to index the file in Suno APK's picker:
   ```bash
   adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file:///sdcard/Music/suno_ready/<song_title>_suno_robot_5.0x.mp3"
   ```

## Stage 4: Mandarin Lyrical Translation & Style Prompting
1. Translate verses into rhythmic Latin PinYin without Chinese Hanzi to prevent character encoding boxes and ensure pure phonetic cadence parsing in Suno.
2. Structure Suno prompts with atmospheric style tags:
   - **Cinematic Drachin Style:** `Epic Xianxia Costume Drama OST, traditional Guzheng, emotional Erhu solo, atmospheric cinematic pads, melancholic acoustic piano, powerful male Mandopop ballad, dramatic orchestral crescendo, 75 bpm, high fidelity studio recording.`

## Stage 5: Long-Form Compilation & YouTube Mastering
1. Combine 15–20 generated songs into a 1-hour master compilation:
   ```bash
   flowork-channel-compiler https://www.youtube.com/@ChannelHandle 15
   ```
2. Automatically render 1080p 30fps Full HD master MP4 with normalized loudness (-14 LUFS) and chapter tracklist (`DESKRIPSI_YOUTUBE_TRACKLIST.txt`).

# Verification
1. **Duration Verification:** Check that audio upload candidate is strictly $\le 59.5$ seconds:
   ```bash
   ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 output_robot_5x.mp3
   ```
2. **Subsystem Sync Verification:** Verify file exists and is indexed in Android VM:
   ```bash
   adb shell ls -la /sdcard/Music/suno_ready/
   ```
3. **Phonetic Encoding Check:** Ensure lyric files contain 100% standard ASCII Latin alphabet characters (`[A-Za-z\s.,!?'-]`).

# Failure Modes
1. **Audio Clip Exceeds 60 Seconds:** Suno upload rejects files longer than 60s. Mitigated by applying explicit `-t 59` duration clamp in FFmpeg.
2. **Android Media Scanner Stall:** Audio does not appear in file picker. Mitigated by re-broadcasting `MEDIA_SCANNER_SCAN_FILE` intent via ADB.
3. **Demucs VRAM Exhaustion:** PyTorch CUDA OOM during separation. Mitigated by setting `--shifts 1` or falling back to CPU mode.
