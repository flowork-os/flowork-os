---
description: Flowork OS Living Desktop Motion Canvas, Mr. Flow Oceanic Holographic Reactor & Real-Time Voice Cadence
keywords:
  - wallpaper
  - ambient
  - motion
  - reactor
  - synaptic
  - cadence
  - amplitude
  - holographic
  - oceanic
  - pulse
  - morphology
  - oscilloscope
  - canvas
  - shm
  - cairo
  - x11
  - desktop
  - visualizer
  - rhythm
  - mrflow
---

# 🌊 Mr. Flow Sovereign Oceanic Holographic Reactor & Dynamic Audio Pulse

### Context
Flowork OS transforms the X11 root desktop into a living spatial canvas. The wallpaper operates as the primary environmental feedback loop for Mr. Flow's intelligence, voice cadence, and tool morphology, paving the way toward a dockless, sidebarless computing paradigm.

### Mandatory Architecture & Runtime Invariants
1. **Zero-IO RAM Bridge (`/dev/shm`):**
   - Inter-process state (`state`, `morphology`, `tool_name`, `action`, `amplitude`) routes exclusively via `/dev/shm/flowork-neural-state.json`.
   - Never write high-frequency animation telemetry to persistent disk to protect SSD lifespan and ensure zero-latency IPC.
2. **Real-Time RMS Speech Cadence Synchronization:**
   - In `voice_daemon.py`, pre-extract normalized RMS audio energy in 40ms slices (25 FPS) using in-memory decoding.
   - Stream amplitude synchronously with audio playback to reflect syllable accents, speech cadence, and pauses between words.
3. **Dynamic Arc Reactor Pulsation (Acoustic Follower):**
   - In `flowork-motion-ambient.py`, evaluate amplitude via a Fast-Attack (0.65) and Smooth-Decay (0.30) follower at 30 FPS.
   - Dynamically scale ring radii (up to +22%), inner iris (up to +35%), and core glow (up to +50%) in rhythm with vocal syllables.
   - During natural pauses, the core must smoothly contract into a serene resting state.
4. **Tool Morphology Mutation:**
   - The central core must morph its inner iris depending on active tool categories:
     - `morph-terminal`: Cybernetic matrix phosphor data streams (`#00ff66`).
     - `morph-circle`: 360° rotating radar sonar scan cone (`#00e5ff`).
     - `morph-frameless`: Holographic vertical laser scanner line.
     - `morph-chamfer`: Crystalline interlocking hexagonal lattices.
     - `morph-swarm`: Gravitational satellite constellation energy web.
5. **Strict Sovereign Branding:**
   - Universal white-label: strictly identity-protected as **Mr. Flow Sovereign Core** with zero external naming references.
