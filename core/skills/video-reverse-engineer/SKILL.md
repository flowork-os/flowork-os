---
name: video-reverse-engineer
description: Comprehensive procedural playbook for reverse-engineering videos shot-by-shot, classifying visual generation techniques, isolating audio stems, and producing replication blueprints.
domain: shell_system
keywords:
  - video
  - reverse-engineering
  - storyboard
  - shot
  - ffmpeg
  - audio-stems
  - subtitles
  - keyframes
  - transcription
  - recreation
  - breakdown
  - multimodal
  - cut-detection
  - b-roll
  - typography
  - color-grading
  - motion-graphics
  - cinematography
  - demucs
  - synthesis
author: Flowork Architecture Board & Dr. Flow
version: 1.0.0
---

# Video Reverse-Engineering & Replication Playbook

## 1. Executive Summary & Objective
Establish a deterministic, empirical Standard Operating Procedure for deconstructing any video asset (live-action, AI-generated, 3D CGI, 2D motion graphics, screencast, or hybrid) frame-by-frame. The objective is to identify source modalities, isolate auditory stems (speech, music, SFX), trace typography/motion overlays, and deliver an exact, actionable replication blueprint without hallucination.

## 2. Prerequisites & Tool Dependencies
1. Core Flowork runtime tools: `run_shell_command`, `read_file`, `write_file`.
2. System CLI binaries:
   - `ffmpeg` & `ffprobe` (video decapsulation, audio extraction, keyframe sampling).
   - Python 3.10+ runtime (`python3`) with standard library support.
3. Multimodal vision-language model access or local visual inspection tools (`agent_browser` / `take_screenshot`).
4. Strict evidence requirement: Any attribution claim (AI model vs live camera vs 3D) must reference explicit timestamped frame evidence. Ambiguous elements must be classified as "unconfirmed" with an empirical confidence score.

## 3. Standard Operating Procedure (SOP)

### Step 1: Probe Video Container & Extract Metadata
Execute container-level metadata inspection to retrieve resolution, frame rate, color space, codec, and audio channels:
```bash
ffprobe -v quiet -print_format json -show_format -show_streams input_video.mp4 > out/metadata.json
```

### Step 2: Shot Boundary & Cut Detection
Detect scene changes and temporal transitions to segment the video into distinct visual shots:
```bash
mkdir -p out/shots out/keyframes
ffmpeg -i input_video.mp4 -filter:v "select='gt(scene,0.3)',showinfo" -vsync vfr out/keyframes/shot_%03d.jpg 2> out/scene_cuts.log
```

### Step 3: Audio Stem Separation & Spectral Analysis
Extract audio track and split channels to isolate dialog/TTS speech, background music (BGM), and sound effects (SFX):
```bash
mkdir -p out/audio
ffmpeg -i input_video.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 2 out/audio/master_audio.wav
# Generate waveform spectrum visualization for rhythmic sync auditing
ffmpeg -i out/audio/master_audio.wav -filter_complex "showwavespic=s=1280x360:colors=0x00FF88" -frames:v 1 out/audio/waveform.png
```

### Step 4: Visual Shot Modality Classification
Evaluate each isolated keyframe across the standard 10 visual modality taxonomies:
1. `live_action`: Natural focal blur, organic camera shake, physical sensor noise.
2. `ai_generated`: Temporal warping, prompt artifacting, hyper-smooth skin textures, inconsistent hand anatomy.
3. `digital_avatar`: Fixed neck boundaries, 2D/3D head anchor, synthetic lip sync over static portrait.
4. `cgi_3d`: Polygonal mesh precision, shader raytracing, synthetic physics simulation.
5. `motion_graphics_2d`: Vector animation, parametric keyframing, SVG/After Effects transforms.
6. `stop_motion`: Discrete frame-stepped physical movement, clay/puppet tactile texture.
7. `screencast`: Native UI pixels, cursor paths, window boundaries.
8. `static_camera_pan_zoom`: Ken Burns effect applied over high-resolution still image.
9. `still_frame`: Zero pixel delta over temporal duration.
10. `hybrid_composite`: Real footage with overlaid AI inpainting, deepfake face swap, or style transfer.

### Step 5: Overlay, Typography, and Motion Graphics Audit
Identify all secondary layers superimposed onto the base footage:
- Subtitle tracks: font style, outline width, bounding box, active karaoke-style keyword highlights.
- Motion stickers, call-to-action badges, and corporate watermark positioning.
- Synchronized SFX trigger points aligned with on-screen graphical pops.

### Step 6: Replication Blueprint Generation
Compile the complete deconstruction report into `out/replication_blueprint.md` containing:
- Timeline breakdown with millisecond timestamps.
- Shot-by-shot generation route (prompt engineering recipe for AI shots, lighting/lens setup for live footage).
- Exact asset requirements (reference logos, audio tempo/BPM, typography weights).

## 4. Verification & Quality Gates (Exit Code 0)
Verify the deconstruction pipeline output integrity:
```bash
# 1. Ensure metadata extraction was generated
test -s out/metadata.json

# 2. Verify keyframe generation count matches cut logs
test $(ls -1 out/keyframes/*.jpg 2>/dev/null | wc -l) -gt 0

# 3. Verify audio waveform extraction
test -s out/audio/waveform.png

# 4. Confirm zero orphan temporary files remained unorganized
test -d out/shots && test -d out/audio
```

## 5. Failure Modes, Edge Cases & Recovery
1. **Low Scene Detection Sensitivity:** Dark or low-contrast transitions fail `scene > 0.3` threshold. Mitigation: re-run scene detection with lowered threshold (`scene > 0.15`) or enforce periodic frame sampling (`fps=1`).
2. **Variable Frame Rate (VFR) Audio Drift:** Audio track becomes out of sync with visual cut points. Mitigation: remux to constant frame rate (`ffmpeg -i input.mp4 -vsync cfr -r 30 out_cfr.mp4`) before cutting.
3. **Hallucinated Origin Attribution:** Agent guessing camera model or AI model without concrete artifact evidence. Remediation: tag classification as `unconfirmed (confidence: X%)` and list missing discriminative markers.

## 6. Prohibitions & Anti-Patterns
- **NEVER Guess Unverifiable Data:** Do not fabricate specific generative seed numbers, lens models, or exact camera sensors unless verifiable via container EXIF metadata.
- **NEVER Skip Audio Analysis:** A video deconstruction without BGM and SFX event mapping is strictly prohibited.
- **NEVER Output Pure Text Dumps:** Always deliver structured markdown tables with timestamps, shot numbers, and replication parameters.
