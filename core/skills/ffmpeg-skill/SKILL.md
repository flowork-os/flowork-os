---
name: ffmpeg-skill
description: Autonomous 42-tool modular video and audio editor for AI agents with lossless GOP cutting, auto-subtitles, loudness normalization, and RTX 4060 GPU NVENC acceleration.
domain: shell_system
keywords:
  - ffmpeg
  - video
  - audio
  - smartcut
  - losslesstrim
  - subtitles
  - captioning
  - loudness
  - ebur128
  - reframe
  - crop
  - broll
  - multicam
  - audiomastering
  - nvenc
  - hardwareaccel
  - silence
  - scenechange
  - videoproduction
  - mcp
author: kajisho5 / Flowork Architecture Board
version: 3.12.1
---

# ⚡ FLOWORK OS SOVEREIGN SKILL: FFMPEG MODULAR MEDIA ENGINE

## 1. Objective
Equip Mr. Flow with an autonomous, 42-tool modular video and audio processing pipeline for sovereign media creation and delivery.
- Execute frame-accurate lossless cuts, auto-subtitling, loudness mastering, aspect reframing, and multi-track audio sync.
- Maximize performance using native RTX 4060 GPU NVENC hardware acceleration with zero external cloud dependencies.
- Deliver production-ready media complying strictly with target platform constraints (TikTok, Reels, YouTube, X, Broadcast).
- Enforce the Universal Document Output Law by routing all generated deliverables to `/opt/floworkos/documents/videos/`.

## 2. Prerequisites & Tool Dependencies
1. **System & Hardware Requirements**:
   - `ffmpeg` and `ffprobe` installed and accessible in `$PATH`.
   - Python 3 stdlib runtime (`python3 /opt/floworkos/skills/ffmpeg-skill/scripts/<tool>.py`).
   - Hardware acceleration via NVIDIA NVENC (`FFMPEG_SKILL_HW=1` or `--hw`).
2. **Flowork Sovereign Execution Instruments**:
   - `flowork-ffmpeg <command> [flags]` native CLI launcher.
   - MCP endpoint: `python3 /opt/floworkos/mcp/ffmpeg_server/server.py` (JSON-RPC stdio).
   - `run_shell_command`: Execute python/ffmpeg pipeline scripts.
   - Output destination directory: `/opt/floworkos/documents/videos/` (mirrored to `$HOME/Documents/videos/`).

## 3. Standard Operating Procedure (SOP)

### Execution Pipeline & Invariants
Run tools in this exact order:
0. **Environment Check (Failure only)**: If `kind: missing_tool`, run `scripts/_contract.py doctor`.
1. **Probe**: Inspect input metadata via `probe.py input.mp4` to plan with empirical numbers.
2. **Prefer Lossless**: Keep `-c copy` whenever a keyframe snap, remux, or audio swap suffices.
3. **Plan First**: Run `--dry-run --json` to inspect parameters before rendering heavy files.
4. **Processing Chain**: `colour` → `cut` → `join` → `silence` → `fit` → `caption/overlay` → `sync` → `audio` → `loudness` → `export`.
5. **Pre-Delivery Check**: Validate compliance using `check.py OUTPUT --platform <target>`.
6. **Empirical Look**: Extract visual contact sheets via `look.py OUTPUT --tiles 3x2` to verify placement and safe zones.

### Core Command Dispatch Matrix
| User Intent | Execution Command |
|---|---|
| Cut lossless / trim segment | `cut.py input.mp4 --start 1:20 --end 2:05` |
| Keyframe-accurate smart cut | `cut.py input.mp4 --start 1:20.4 --end 2:05.1 --smart` |
| Remove dead air / pause jump cut | `silence.py input.mp4 --speech-aware` |
| Reframe / aspect ratio conversion | `fit.py input.mp4 --aspect 9:16 --fit pad` (or `crop`, `blur`) |
| Burn in captions / subtitles | `caption.py input.mp4 --srt subs.srt --animate pop --karaoke` |
| Audio loudness mastering | `loudness.py input.mp4 --lufs -14 --tp -1` |
| Clean voice / remove hiss | `audio.py input.mp4 --voice --denoise` |
| Background music auto-ducking | `audio.py input.mp4 --music bgm.mp3 --duck --fade-out 3` |
| Delivery export preset | `export.py input.mp4 --preset youtube` (or `reels`, `tiktok`, `prores`) |

## 4. Verification & Quality Gates
Every media pipeline operation must satisfy the following automated verification checks:
1. **Exit Code 0**: Ensure `ffmpeg` and wrapper scripts terminate cleanly without errors.
2. **Output Stream Probe**: Verify output container, video bitrate, audio codec, and sample rate match the target specification via `probe.py <output>`.
3. **Loudness Compliance**: Ensure integrated LUFS (-14 LUFS for web/streaming, -23 LUFS for broadcast) and True Peak (≤ -1.0 dBTP) via `loudness.py --measure-only`.
4. **Visual Safe-Zone Verification**: Extract reference frames via `look.py <output> --guides title,action` to guarantee burned captions and overlays do not collide with UI chrome.

## 5. Failure Modes & Recovery Strategies
- **HDR Washout**: If SDR output looks washed out from an HDR source, re-run with `color.py input.mov --to-sdr`.
- **Alpha Loss**: Standard re-encodes drop alpha channels. Pass `--keep-alpha` with `--alpha-codec prores4444` to preserve transparency.
- **Audio Drift on VFR**: Phone/screen recordings often use Variable Frame Rate. Conform to constant frame rate first using `fit.py input.mp4 --fps 30` or `sync.py --fix-drift`.
- **Cut Point Artifacts**: If a lossless cut creates frozen frames at start, switch to `--smart` GOP-aware re-encoding or `--accurate`.
- **Subtitle Safe-Area Overflow**: If captions are covered by TikTok/Reels UI buttons, specify `--platform reels` or increase `--margin`.
