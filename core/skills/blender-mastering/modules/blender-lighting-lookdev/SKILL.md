---
name: blender-lighting-lookdev
slash_command: /blender-lighting-lookdev
description: "Lighting, cameras and look-dev in Blender 5.3 - studio 3-point and product lighting, HDRI environments, sun/sky exteriors, interiors, light linking, physically based light units, camera focal lengths/composition/DOF, cyclorama backdrops, looping turntables for asset presentation. Use when present..."
domain: code_dev
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "blender"
  - "bpy"
  - "lighting-lookdev"
  - "three-point-lighting"
  - "key-light"
  - "fill-light"
  - "rim-light"
  - "hdri-environment"
  - "color-temperature"
  - "light-intensity-lux"
  - "camera-focal-length"
  - "depth-of-field"
  - "macbeth-chart"
  - "exposure-calibration"
  - "cycles-samples"
  - "cinematic-lighting"
  - "3d-rendering"
  - "code-dev"
  - "aces-color-management"
  - "flowork-blender"
---

# 🎨 Blender Sovereign Subsystem: Blender Lighting Lookdev

## 1. Executive Summary & Objective
Lighting, cameras and look-dev in Blender 5.3 - studio 3-point and product lighting, HDRI environments, sun/sky exteriors, interiors, light linking, physically based light units, camera focal lengths/composition/DOF, cyclorama backdrops, looping turntables for asset presentation. Use when present...
This skill provides an authoritative, deterministic procedure for executing blender lighting lookdev within Blender 5.2+ and 5.3+ environments, supporting both headless automated batch execution (`bpy`) and live interactive sessions via Flowork OS MCP / terminal runners.

## 2. Prerequisites & Tool Dependencies
1. **Host Environment**: Blender 5.2+ or 5.3+ installed and accessible in `$PATH` (`blender`).
2. **Python Runtime**: Python 3.11+ with `bpy`, `mathutils`, and `numpy`.
3. **Flowork OS Actuators**:
   - `run_shell_command`: Direct execution of headless verification and scripts (`blender --background --python ...`).
   - `spatial_graph` / `desktop_actuator`: GUI viewport inspection and interactive verification when running in headed mode.

## 3. Standard Operating Procedure (SOP)

### Technical Specifications & Upstream Doctrine
# Lighting & Look-dev

The execution model is in `blender-core`. Render settings are in `blender-rendering`. Full time-of-day, night and fog environments are in `blender-time-of-day`.

## One call: presentation scene
```
scripts/turntable.py -- --objects Hero --rig studio --backdrop --frames 120 --lens 85
scripts/turntable.py -- --objects Hero --rig both --hdri //hdri/studio_small_09_2k.exr --hdri-strength 0.8
```
This builds a camera framed to the bounding sphere (on the narrower frame axis), a key/fill/rim area-light rig scaled to the asset, an optional 18%-grey cyclorama, and a pivot that orbits camera + lights + backdrop in a seamless loop. **The asset itself isn't modified.** Everything lives in the `LD_Lookdev` collection, and re-running replaces it. Set the render resolution **before** running, because framing depends on the aspect ratio.

## Lighting recipes
| Situation | Setup |
|---|---|
| Asset / product review | 3-point: key 45° side, 30–40° up; fill opposite at ⅓ power and lower; rim behind for silhouette. Large soft area lights (size ≈ object), neutral grey backdrop, Khronos PBR Neutral view |
| Reflective product (metal, glass, car paint) | large softboxes/strip lights *reflected* in the surface, plus a black/white gradient environment. Shape the reflections, not the illumination |
| Exterior day | Sun light (angle 0.5° for sharp, 2–5° for softer) + sky (`ShaderNodeTexSky`, `sky_type` `MULTIPLE_SCATTERING`/`SINGLE_SCATTERING`; 5.x replaced "Nishita"; `PREETHAM`/`HOSEK_WILKIE` legacy) with `sun_elevation`/`sun_rotation` matching the Sun light (5.3: `sun_disc` now emits light, so turn it off when a Sun lamp is the sun), or an HDRI of the matching time of day |
| Interior | HDRI/sky through the windows + portal area lights in the openings, bounces ≥ 4, then practical lights (lamps) at real wattage |
| Character / portrait | soft key from above-front, a reflector-like fill, rim or hair light, an eye catchlight. 85–135 mm lens |
| Stylized / game screenshot | match the engine: one directional + ambient/HDRI, no fancy GI, so it looks like it will in-game |
- **HDRI**: Poly Haven (CC0) via the blender-mcp `search_assets`/`import_asset`, or `ShaderNodeTexEnvironment` + Mapping (Z rotation aligns the sun). Strength 0.5–1.5. Clamp sun hotspots if they cause fireflies.
- **Light linking** (4.0+, Cycles + EEVEE): set `light_obj.light_linking.receiver_collection` / `blocker_collection` (on the light **object**) to light only what you choose, like a hero rim that doesn't touch the backdrop. Portals: `light.cycles.is_portal = True` on area lights in window openings.
- **Units**: point/spot/area in Watts (a 60 W bulb ≈ point light 40–60 W in Blender), sun in W/m² (irradiance; 1000 ≈ physical midday, but use 3–10 with AgX for natural results), emission strength ≈ W/m². Keep lights physically plausible and control the overall image with exposure.
- **Shadows**: light size controls softness. A bigger, closer light is softer. Contact shadows should exist where objects touch, so check that nothing floats (`blender-asset-qa` `ground_z`).

## Camera rules
- Focal length: 24–35 mm environments/interiors (keep verticals straight: camera level, or shift instead of tilting), 50 mm natural, **85–135 mm products and portraits** (no distortion), 200 mm+ compressed telephoto.
- Composition: rule of thirds / centered symmetric for products, horizon off-center, leading lines, headroom. Show the silhouette (3/4 view at slight elevation 10–25°).
- DOF (`cam.data.dof.use_dof`, `focus_object`, `aperture_fstop`): f/2.8–5.6 for products at real scale. DOF depends on scale, so a wrong scene scale ruins it.
- Clip start/end tight around the subject (the script does this), which avoids precision artifacts.
- Sensor fit AUTO uses the larger axis. Portrait renders need framing on the width.

## Look-dev procedure (material approval)
1. Neutral setup: `--rig studio` or a neutral HDRI, grey backdrop, Khronos PBR Neutral or AgX (pick one and keep it).
2. Add a calibration chart object if needed (a grey 18% sphere, a chrome sphere, a Macbeth chart) next to the asset.
3. Turntable at 24–30 fps, 120–240 frames, 85 mm. Render previews with `render_batch.py --preset preview --format MP4`.
4. Check the materials under 2–3 different HDRIs. A good PBR material holds up in all of them (`blender-pbr-materials` sanity checks).

## Gotchas
- World lighting is invisible if `world.node_tree` has no Background → World Output link (the script ensures one).
- EEVEE needs `use_raytracing` for good reflections. Light probes (Volume/Sphere/Plane) still help static GI in interiors.
- Area lights that are too small and bright make fireflies in Cycles. Increase the size, decrease the power.
- A turntable that rotates the **asset** changes its transforms and animation data, which is why this rig orbits the camera instead.

## 4. Verification & Quality Gates (Exit Code 0)
1. **Headless Execution Verification**:
   - All accompanying scripts located in `scripts/` must execute headlessly without exceptions:
     ```bash
     blender --background --python scripts/<script_name>.py -- [args]
     ```
   - Must exit with Exit Code 0 and produce clean JSON or diagnostic output.
2. **Deterministic State Audit**:
   - Verify unapplied transforms (`rotation == 0`, `scale == 1.0`).
   - Confirm asset integrity, zero orphaned data blocks, and valid material slots.

## 5. Failure Modes, Edge Cases & Recovery
- **Context Override Failures**: Blender 5.x strictly requires proper `bpy.context.temp_override(window=..., area=..., region=...)` syntax. Never use obsolete 3.x context dictionaries.
- **Missing GPU / Display In Headless Mode**: Use `--background` and software OpenGL fallback (`LIBGL_ALWAYS_SOFTWARE=1`) if running in compute-only environments.
- **Node Socket Mismatches**: Access sockets by name or type identifier; avoid hardcoded integer indices across Blender minor versions.

## 6. Prohibitions & Anti-Patterns
- **NEVER** leave unapplied scales on meshes prior to physics, rigging, or baking.
- **NEVER** use blocking interactive dialogs in headless automated pipelines.
- **NEVER** modify production `.blend` files without a backup or non-destructive branch.
- **NEVER** hallucinate obsolete Blender 2.7x/2.8x API calls (`bpy.ops.object.select_name`, etc.).
