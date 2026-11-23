---
name: line-art-animation
description: Autonomous hand-drawn ink and Japanese line art procedural animation workflow. Uses inverse kinematics, spring-pendulum physics, day-night palettes, and deterministic SVG rendering.
domain: code_dev
keywords:
  - line_art_animation
  - procedural_animation
  - inverse_kinematics
  - gait_solver
  - svg_vector_engine
  - hand_drawn_ink
  - dual_open_stroke
  - spring_physics
  - pendulum_motion
  - day_night_palette
  - deterministic_capture
  - headless_chromium
  - ffmpeg_video_export
  - zero_foot_sliding
  - washi_paper_aesthetic
  - interactive_wind
  - character_rigging
  - minimum_jerk_trajectory
  - ink_wash_rendering
  - faceless_storytelling
author: Flowork Architecture Board
version: 1.0.0
---

# 🖋️ FLOWORK OS SOVEREIGN SKILL: LINE ART PROCEDURAL ANIMATION

## 1. Objective
Equip Mr. Flow with an autonomous, mathematically rigorous procedural line-art animation pipeline to engineer hand-drawn ink animations in pure SVG and TypeScript.
- **Zero Hallucination / Zero Artifacts:** Replace heavy, inconsistent generative video models with lightweight, deterministic procedural mathematics.
- **True Inverse Kinematics Gait:** Eliminate robotic sine-wave bobbing and foot-sliding via contact-phase pinning and minimum-jerk swing trajectories.
- **Ink-on-Paper Aesthetic:** Enforce dual open-contour pen strokes, paper textures, and continuous solar-cycle color palettes.
- **Lossless Deterministic Export:** Capture frames deterministically via headless browser CDP stepping (`window.__step(dt)`) and encode 1080p/4K 60fps video via FFmpeg without dropped frames.

## 2. Prerequisites
1. **Flowork Native Development & Multimedia Tools**:
   - `node` / `npm` or `bun` for TypeScript bundling and Vite dev server.
   - `chromium` or `google-chrome` for headless CDP frame stepping.
   - `ffmpeg` on Linux host for lossless frame stitching into H.264/ProRes video.
2. **Core Animation Math Libraries (`lib/`)**:
   - `gait.ts`: Leg/hip inverse kinematics solver (`gait(phase, cadence, speed)`).
   - `motion.ts`: Second-order damped spring and pendulum physics (`Spring`, `Pendulum`).
   - `ink.ts`: Vector stroke generator (`limb`, `torso`, `head`, `groundRipple`, `inkBleed`).
   - `daynight.ts`: Solar-angle color interpolation engine (`palette(tau)`).

## 3. Standard Operating Procedure (SOP)

### Phase 1: Coordinate Space & Skeletal Rigging
All characters are authored within a standardized local coordinate space:
- **Dimensions**: ~95 units tall, ground level at `y = 120`.
- **Skeleton Layering Order (Back-to-Front)**:
  1. Back arm (shoulder -> elbow -> wrist -> hand)
  2. Back leg (hip -> knee -> ankle -> toe)
  3. Torso & clothing wrapper (kimono, coat, tunic)
  4. Head & facial profile (ear, chin, hat/hood)
  5. Front leg
  6. Front arm
  7. Secondary dynamic attachments (lantern, scarf, bag, sword)

### Phase 2: Inverse Kinematics Gait Formulation
Never animate legs with simple `Math.sin(t)`. Always invoke `gait()`:
1. **Stance Phase (`phase < 0.5`)**:
   - The planted foot is pinned to the ground: `x_foot = -speed * (phase / 0.5) * stride_length`.
   - Heel raises dynamically as the leg transitions toward toe-off.
2. **Swing Phase (`phase >= 0.5`)**:
   - Foot leaves the ground following a minimum-jerk polynomial curve.
   - Foot clears the ground at peak trajectory before descending smoothly.
3. **Hip Dip**:
   - Hip dips downwards during double support (`phase = 0.0` and `phase = 0.5`) and peaks during single support.

### Phase 3: Hand-Drawn Ink Aesthetic (Dual Open Stroke)
1. **Never use closed geometric polygons** for human limbs.
2. Render each limb using two open stroke curves via `limb(start, joint, end, thickness)`:
   - Line A curves along the anterior silhouette.
   - Line B curves along the posterior silhouette with slight endpoint offset.
3. Apply SVG filter `feTurbulence` with subtle displacement to simulate rough mulberry washi paper fiber bleeding.

### Phase 4: Physics-Driven Secondary Motion
1. Attach accessories to skeletal joints using `Pendulum` or `Spring`:
   - Lantern: Damped angular pendulum attached to wrist or staff tip.
   - Hair / Scarf: Chain of 2 to 3 spring links reacting to body acceleration and mouse wind.
2. Add interactive ambient pointer reactivity:
   - Calculate cursor velocity $\vec{v}_{mouse} = (x_{t} - x_{t-1}) / \Delta t$.
   - Inject wind force into fabric and dangling geometry.

### Phase 5: Deterministic Video Capture & Rendering
To render a scene into MP4 video:
1. Launch Vite in headless debug mode:
   `npm run build && npm run preview -- --port 5173`
2. Execute deterministic frame stepping script:
   `npx tsx scripts/capture.ts --url "http://localhost:5173/?debug=1" --frames 360 --fps 60 --out /opt/floworkos/documents/animation.mp4`
3. Verify output video bitrate, resolution, and zero-frame-drop playback.

## 4. Verification
Execute the following verification checklist before delivering any animation:
1. **Zero Foot Sliding Check**: Observe contact point of the planted foot against ground markers; coordinate must remain strictly motionless relative to ground plane during stance.
2. **Silhouette Legibility**: Switch palette to pure black-and-white; character pose and action must remain instantly recognizable without internal detail lines.
3. **Seamless Loop**: Ensure phase $\phi$ wraps smoothly at $2\pi$ without angular discontinuities or spring snap.
4. **Deterministic Step Verification**: Run `window.__step(1/60)` manually in browser console; ensure entire scene advances identically to real-time `requestAnimationFrame`.

## 5. Failure Modes
1. **Floating / Sliding Feet**: Caused by animating world position separately from gait stride frequency. Fix: Lock world translation speed strictly to `stride_length * cadence`.
2. **Rigid "Wireframe" Look**: Caused by closed SVG `<polygon>` or uniform stroke-width. Fix: Replace with `dual_open_stroke` with varying stroke-width taper.
3. **Spring Explosion / Instability**: Occurs when delta time $\Delta t > 0.033$ (frame lag). Fix: Sub-step physics integration (e.g., 4 steps of $\Delta t / 4$) or clamp maximum velocity.
4. **Dropped Frames in Video Export**: Caused by real-time screen recorders. Fix: Always use deterministic CDP frame-stepping with `scripts/capture.ts`.
