---
name: kamidi-mastering
description: Professional audio mastering suite with 32-bit float DSP, Parametric EQ, Multiband Compressor, Brickwall Limiter, and EBU R128 LUFS Metering.
domain: shell_system
keywords:
  - audio_mastering
  - mastering_console
  - parametric_eq
  - multiband_compressor
  - brickwall_limiter
  - lufs_metering
  - true_peak
  - dynamic_eq
  - sub_bass_808
  - transient_shaper
  - audio_processing
  - ebu_r128
  - dsp_engine
  - sound_engineering
  - studio_master
  - wav_export
  - music_production
  - audio_limiter
  - audio_clipper
  - mastering_presets
author: Flowork Architecture Board
version: 5.0.10
---

# 🎛️ FLOWORK OS SOVEREIGN SKILL: KAMIDI MASTERING CONSOLE PRO (v5.0.10)

## 1. Objective
Equip Mr. Flow and Flowork OS with professional studio-grade audio mastering capabilities. Enable real-time 32-bit float DSP processing, 8-band parametric equalization, 3-band multiband dynamics compression, transparent brickwall limiting, and ITU-R BS.1770 / EBU R128 compliance metering.

## 2. Prerequisites
1. **Host Audio & Display Subsystem**:
   - PulseAudio / PipeWire audio server active (`pactl info` operational).
   - X11 display session initialized (`DISPLAY=:0`).
   - Native system FFmpeg binary at `/usr/bin/ffmpeg`.
2. **Native Runtime**:
   - Compiled native Rust binary at `/opt/floworkos/apps/kamidi-mastering/bin/kamidi-mastering-bin`.
   - Linked to `libgtk-3.so.0` and `libwebkit2gtk-4.1.so.0`.
3. **Application Assets**:
   - Web GUI and authentic DSP suite at `/opt/floworkos/apps/kamidi-mastering/gui/`.
   - Desktop launcher at `/opt/floworkos/bin/kamidi-mastering`.

## 3. Standard Operating Procedure (SOP)

### Phase 1: Engine Initialization & Verification
1. Verify executable and health status:
   ```bash
   /opt/floworkos/bin/kamidi-mastering --check-health
   ```
2. Confirm Exit Code 0 and message `HEALTH_OK: Kamidi Mastering Pro v5.0.10 native Rust engine & UI operational.`.

### Phase 2: Launching Mastering Console
1. Launch from application menu or terminal detached:
   ```bash
   flowork-launch kamidi-mastering
   ```
2. The native Rust runner starts the embedded HTTP loopback daemon (port `17860`) and renders the WebKit view with software compositor fallbacks disabled (`WEBKIT_DISABLE_COMPOSITING_MODE=1`).

### Phase 3: Audio Mastering Workflow
1. **Load Source Audio**:
   - Click `LOAD TRACK` or drag & drop audio files (WAV, MP3, FLAC, OGG, AAC) into the workspace.
2. **Gain Staging & Tonal Balance**:
   - Adjust input gain to achieve -18 dBFS RMS headroom.
   - Configure the 8-band parametric EQ (High-Pass, Low Shelf, Peaking, High Shelf).
3. **Multiband Dynamics**:
   - Tune crossover frequencies (Low/Mid/High).
   - Apply gentle compression to stabilize bass and control harsh high frequencies.
4. **Loudness & Limiting**:
   - Target streaming standards (-14 LUFS integrated for Spotify/YouTube, -9 LUFS for Club).
   - Set ceiling to -0.3 dB True Peak to prevent inter-sample clipping on DAC playback.
5. **Export Master**:
   - Click `EXPORT` to render offline 32-bit float audio and perform 2-pass LUFS normalization via native FFmpeg sidecar.

## 4. Verification
1. **Engine Health Check**: Run `/opt/floworkos/bin/kamidi-mastering --check-health` -> Returns Exit Code 0.
2. **Window Detection**: Run `DISPLAY=:0 wmctrl -l | grep -i "Kamidi Mastering"` -> Window title detected.
