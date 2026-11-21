# 🎬 Flowork Edits — Sovereign Desktop Video Editor (Architecture & Implementation Plan)

## 1. Executive Summary & Objective
**Flowork Edits** is a native, sovereign video editor application for Flowork OS, designed as a pixel-perfect, feature-compatible clean-room implementation of Meta's macOS Edits (Basel) application. It empowers creators to cut, trim, arrange multi-track video and audio, generate on-device AI captions, apply real-time filters and color LUTs, and seamlessly import/export projects compatible with Instagram Reels on mobile via the **.bsleditsx** archive format and **BSLHandoff** protocol.

---

## 2. Technology Stack & Architectural Pillars
- **Desktop Shell & Framework:** Node.js + Native Desktop Canvas / Lightweight Webview GUI with dark glass macOS aesthetic, running directly on Flowork OS X11/GLX.
- **Styling & Aesthetics:** Pure Vanilla CSS (macOS Sonoma/Sequoia dark glass theme, translucent acrylic panels, crisp typography, custom scrollbars, SVG icons matching Apple SF Symbols).
- **Core Media & Video Engine:** FFmpeg & FFprobe backend combined with HTML5 Video + WebGL Canvas for hardware-accelerated preview rendering and video scrubbing.
- **Audio Processing Graph:** Web Audio API with real-time waveform visualizer, volume envelopes, and ducking nodes.
- **Speech & Auto-Captions Engine:** Integrated local Python Whisper AI daemon (`faster-whisper` / `whisper-timestamped`) producing timed subtitle tokens for the text track.
- **File Format & Interchange:** 100% compliant `.bsleditsx` project archive handler reading and generating `manifest.json` + `composition.json`.
- **System Integration:** Registered desktop entry in `/opt/floworkos/apps/flowork-edits.desktop` with launcher shortcut, mime-type handler for `.bsleditsx`, and persistence lock.

---

## 3. UI/UX Layout Specification (Pixel-Perfect Clone)
1. **Top Bar (Window Controls & Actions):**
   - Left: Basel Mac App icon, Project Title editable, Undo / Redo buttons.
   - Center: Aspect ratio switcher (`9:16` Reels/Shorts, `16:9` Landscape, `1:1` Square, `4:5` Feed).
   - Right: Zoom controls, "Import Media", "Transfer from Phone", and bright primary "Export" button.
2. **Main Canvas / Preview Monitor:**
   - Centered video monitor with real-time aspect framing, safe zone overlay guides, overlay text anchors, and playback timecode (e.g. `00:00:14:12 / 00:00:30:00`).
   - Transport controls: Play / Pause (Spacebar), Step Forward / Backward (J-K-L navigation), Split Tool (`Cmd+B` / `Ctrl+B`), Delete Clip (`Delete` / `Backspace`).
3. **Left Sidebar / Media & Effect Library:**
   - Tabs: `Media` (imported videos/photos/audio), `Captions` (AI generated subtitles), `Effects & Filters` (LUT color grading, glitch, zoom blur, camera shake), `Audio` (voiceover narration, sound effects, beat detection).
4. **Bottom Multi-Track Stacked Timeline:**
   - Playhead with millisecond-precision scrub bar and ruler.
   - Track 1 (Text / Captions Overlay Track).
   - Track 2 (Sticker / Picture-in-Picture Video Track).
   - Track 3 (Primary Video Track with thumbnail strip).
   - Track 4 (Audio Track with interactive waveform rendering).
   - Interactive handles for clip trim (head & tail drag), clip splitting, and volume slider.

---

## 4. Phase-by-Phase Implementation Roadmap

### Phase 1: Application Skeleton & Desktop Integration
- Scaffold `/opt/floworkos/apps/flowork-edits/` with clean modular structure (`frontend/`, `backend/`, `assets/`, `bin/`).
- Create launcher wrapper `/opt/floworkos/bin/flowork-edits` and desktop entry `/opt/floworkos/apps/flowork-edits.desktop`.
- Extract original app icons from the DMG (`BaselMacAppIcon.icns`) and convert to high-res PNG for Flowork OS theme.

### Phase 2: Core Video Player & Timeline Canvas
- Build the responsive, GPU-accelerated video preview canvas with multi-aspect ratios.
- Implement the interactive multi-track timeline (draggable playhead, clip slices, trimming handles, zoom level).
- Implement keyboard navigation: `Space` (play/pause), `Split (S/B)`, `Delete`, `Arrows` (frame stepping).

### Phase 3: Project Engine (.bsleditsx)
- Build the archive manager capable of packaging and unpacking `.bsleditsx` ZIP bundles containing `manifest.json` and `composition.json`.
- Provide sample Instagram Reels template project so the user can test editing immediately.

### Phase 4: Local Auto-Captions & Subtitle Generation
- Implement subtitle transcription pipeline using local speech recognition.
- Generate timed caption tokens and place them automatically into the Captions timeline track.

### Phase 5: Verification & Quality Gate
- Verify application launches smoothly from terminal and application menu.
- Verify video playback, splitting, trimming, and export to MP4 via FFmpeg with Exit Code 0.
