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
version: 1.0.0
---

# 🎛️ FLOWORK OS SOVEREIGN SKILL: KAMIDI MASTERING CONSOLE PRO

## 1. Objective
Equip Mr. Flow and Flowork OS with professional studio-grade audio mastering capabilities. Enable real-time 32-bit float DSP processing, 8-band parametric equalization, 3-band multiband dynamics compression, transparent brickwall limiting, and ITU-R BS.1770 / EBU R128 compliance metering.

## 2. Prerequisites
1. **Host Audio & Display Subsystem**:
   - PulseAudio / PipeWire audio server active (`pactl info` operational).
   - X11 display session initialized (`DISPLAY=:0`).
   - Node.js runtime installed (`/usr/bin/node` or `/usr/local/bin/node`).
2. **WebKit2GTK Runtime**:
   - Python 3 with `PyGObject` (`gi.repository.WebKit2` and `Gtk 3.0`).
3. **Application Assets**:
   - Engine server at `/opt/floworkos/apps/kamidi-mastering/engine/server.mjs`.
   - Web GUI at `/opt/floworkos/apps/kamidi-mastering/gui/index.html`.
   - Desktop launcher at `/opt/floworkos/bin/kamidi-mastering`.

## 3. Standard Operating Procedure (SOP)

### Phase 1: Engine Initialization & Verification
1. Verify Node.js DSP server port availability (default port: `17860`).
2. Execute headless health check:
   ```bash
   /opt/floworkos/bin/kamidi-mastering --check-health
   ```
3. Confirm Exit Code 0 and message `HEALTH_OK: Kamidi Mastering Console Pro engine & UI operational.`.

### Phase 2: Launching Mastering Console
1. Launch from application menu or terminal:
   ```bash
   kamidi-mastering
   ```
2. The sovereign runner starts `engine/server.mjs` as a background DSP daemon if not already running.
3. WebKit2GTK renders the GUI at `http://127.0.0.1:17860/` with hardware acceleration enabled.

### Phase 3: Audio Mastering Workflow
1. **Load Source Audio**:
   - Drag & drop or select WAV/FLAC/MP3 files into the audio loader.
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
   - Render offline 32-bit float or 24-bit PCM master WAV.

## 4. Verification
1. **Engine Health Check**: Run `/opt/floworkos/bin/kamidi-mastering --check-health` -> Must return Exit Code 0.
2. **HTTP Server Response**: Run `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:17860/` -> Must return 200.
3. **GUI Window Registration**: Run `wmctrl -l | grep -i "Kamidi Mastering"` -> Window title must be detected.

## 5. Failure Modes & Recovery
1. **Port 17860 Already Bound**:
   - *Cause*: Previous instance or orphan node process holding port.
   - *Recovery*: Check process using `lsof -i :17860` or kill existing instance via `pkill -f "engine/server.mjs"`, then relaunch.
2. **Web Audio Context Suspended**:
   - *Cause*: Browser autoplay policy blocks AudioContext before user interaction.
   - *Recovery*: Click any knob or transport play button to resume Web Audio context.
3. **Missing Audio Drivers**:
   - *Cause*: PulseAudio daemon not responding.
   - *Recovery*: Restart user audio daemon with `systemctl --user restart pulseaudio` or verify ALSA devices.
