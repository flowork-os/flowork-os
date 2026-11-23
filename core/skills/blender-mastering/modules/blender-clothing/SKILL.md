---
name: blender-clothing
slash_command: /blender-clothing
description: "Game clothing in Blender 5.3 - garments from body regions (ease offset, thickness), skin-weight transfer, hiding covered body faces, cloth-sim draping for folds, body-morph shape keys on garments, layered clothing, pose-aware poke-through checks, sim-to-game-mesh cleanup. Use for shirts, pants, a..."
domain: code_dev
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "blender"
  - "bpy"
  - "clothing-generation"
  - "garment-modeling"
  - "body-region-extraction"
  - "solidify-modifier"
  - "cloth-simulation"
  - "collision-physics"
  - "surface-deform"
  - "weight-transfer"
  - "crease-brush"
  - "wrinkle-sculpting"
  - "real-time-garments"
  - "uv-unwrapping"
  - "fabric-materials"
  - "game-ready-cloth"
  - "3d-fashion"
  - "code-dev"
  - "pinned-vertices"
  - "flowork-blender"
---

# 🎨 Blender Sovereign Subsystem: Blender Clothing

## 1. Executive Summary & Objective
Game clothing in Blender 5.3 - garments from body regions (ease offset, thickness), skin-weight transfer, hiding covered body faces, cloth-sim draping for folds, body-morph shape keys on garments, layered clothing, pose-aware poke-through checks, sim-to-game-mesh cleanup. Use for shirts, pants, a...
This skill provides an authoritative, deterministic procedure for executing blender clothing within Blender 5.2+ and 5.3+ environments, supporting both headless automated batch execution (`bpy`) and live interactive sessions via Flowork OS MCP / terminal runners.

## 2. Prerequisites & Tool Dependencies
1. **Host Environment**: Blender 5.2+ or 5.3+ installed and accessible in `$PATH` (`blender`).
2. **Python Runtime**: Python 3.11+ with `bpy`, `mathutils`, and `numpy`.
3. **Flowork OS Actuators**:
   - `run_shell_command`: Direct execution of headless verification and scripts (`blender --background --python ...`).
   - `spatial_graph` / `desktop_actuator`: GUI viewport inspection and interactive verification when running in headed mode.

## 3. Standard Operating Procedure (SOP)

### Technical Specifications & Upstream Doctrine
# Clothing

The execution model is in `blender-core`. The rig and weights are in `blender-character-rigging`, classic cloth settings in `blender-simulation`, and Roblox layered clothing cages in `blender-export-pipelines` (references/roblox.md).

## One call each
```
scripts/garment.py -- --body Body --group Torso --name Shirt --hide-body
scripts/garment.py -- --body Body --zmin 0.45 --zmax 1.05 --name Pants --offset 0.01 --drape 40 --morphs
scripts/garment.py -- --body Body --group Torso --name Armor --offset 0.02 --thickness 0.008
scripts/garment.py -- --check Shirt --body Body          # pose the rig first: checks the current pose
```

## How pros build game clothing
1. **Shape**: start from the body (extract + offset) for fitted clothes, or from flat patterns sewn by cloth sim (Marvelous Designer or Blender cloth with sewing springs) for loose ones. Simulate on the body in its **rest pose** (A/T).
2. **Game mesh**: retopo the high/sim result to clean, even quads with loops at the joints (elbows, knees, shoulders get 3 loops), then UV it. Bake folds into normal maps (`blender-texture-baking`) so the low mesh stays light.
3. **Skin**: copy weights from the body (same bones, same influences), clean them (limit 4, normalize, drop < 0.001), then blend toward smoother weights only on loose parts (skirts, coats) and add extra bones for those.
4. **Hide what's covered**: delete body faces under the garment (save tris, stop poke-through) or mask them per outfit. Keep one ring of skin under cuffs and collars.
5. **Verify in motion**: stress poses (`blender-character-rigging` `stress_poses.py`), then `--check` in each. Fix by easing (offset), smoothing the body there, weight tweaks, or hiding.

## garment.py
- Region: `--group` (body vertex group, weight > 0.5) or a world `--zmin/--zmax` band. The faces are copied in world space and pushed out along the vertex normals by `--offset` (ease: 5–10 mm fitted cotton, 10–20 mm jackets, 15–30 mm armor). Then `Solidify` adds `--thickness` (2–4 mm fabric, 5–10 mm leather/armor), growing outward. UVs carry over from the body.
- Weights: Data Transfer (`POLYINTERP_NEAREST`, all groups by name), applied, limited to `--max-influences`, normalized and cleaned. The body's Armature modifier is added and parented to the rig.
- `--hide-body`: `Hidden_<name>` vertex group (the region shrunk by one ring) + an inverted Mask modifier on the body. Swappable outfits toggle masks. For export, delete those faces on a body copy instead.
- `--drape N`: classic cloth (cotton-ish: mass 0.15, tension 15, bending 0.5, quality 8). The top 8% is pinned, the body collides at 3 mm, it settles N frames, then the result is applied. That gives gravity folds on loose areas. Use 30–60 frames.
- `--morphs`: for each body shape key, a same-named garment shape key, via Surface Deform bound in the rest pose and applied as a shape key per morph. Engines drive body and garment keys together (fat/thin, muscle, breathing). Measured: a 30% body morph pokes through 346 verts. With the matching garment key, 0.
- **Poke check** (also run at the end of every build): casts along each body vertex normal. If the garment is hit inward before outward (or sits < 0.5 mm away), it's poke-through. Verts that hit no garment within 0.1 m aren't covered and are ignored. It reports `covered_verts`, `poke_verts` and `poke_max_m`, uses the **evaluated** pose, and respects the body masks.

## Layered clothing
- Order from the skin out: underwear/base → shirt → vest → jacket → armor. Each layer offsets from the one below (run `garment.py --body Shirt` for a vest over the shirt) and copies weights from the body, not from the layer below.
- Interpenetration between layers in motion usually comes from mismatched weights. Copying all layers from the same body keeps them moving together.
- Roblox layered clothing needs `<Name>_InnerCage` + `<Name>_OuterCage` built from Roblox's template cages (same vert order/UVs). Other engines (UE Mutable/Unity) blend shape keys or use body-hiding masks. Same principle.

## Gotchas
- `shape_key_add()` creates keys at value 1.0 (measured). Set `.value = 0` when authoring morphs from Python.
- Surface Deform for **morphs only**: if left live together with an Armature modifier, the pose is applied twice. `--morphs` removes it after baking the keys.
- Apply the body's scale before building. Offsets and thickness are in meters.
- Cloth sims need the body's collision mesh at a modest resolution. Decimate a proxy for the collision if the body is > 50k verts.
- Run `blender-asset-qa` on the final garment (z-fighting with the body, floating parts, normals) and check its tris against `blender-game-optimization` budgets.

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
