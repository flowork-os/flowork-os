---
name: blender-game-optimization
slash_command: /blender-game-optimization
description: "Optimize Blender assets for real-time engines - triangle/material/texture/bone budgets per platform (mobile, Roblox, web, VR, console, PC), LOD chains, decimation modes, mesh cleanup, draw-call reduction (material merging, atlases, trim sheets), instancing, vertex-split costs, collision proxies, ..."
domain: code_dev
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "blender"
  - "bpy"
  - "game-optimization"
  - "triangle-budget"
  - "draw-call-reduction"
  - "lod-generation"
  - "decimate-modifier"
  - "material-merging"
  - "texture-atlas"
  - "occlusion-culling"
  - "convex-collision"
  - "vertex-cache"
  - "mobile-budget"
  - "pc-console-targets"
  - "perf-audit"
  - "engine-readiness"
  - "3d-optimization"
  - "code-dev"
  - "headroom-check"
  - "flowork-blender"
---

# 🎨 Blender Sovereign Subsystem: Blender Game Optimization

## 1. Executive Summary & Objective
Optimize Blender assets for real-time engines - triangle/material/texture/bone budgets per platform (mobile, Roblox, web, VR, console, PC), LOD chains, decimation modes, mesh cleanup, draw-call reduction (material merging, atlases, trim sheets), instancing, vertex-split costs, collision proxies, ...
This skill provides an authoritative, deterministic procedure for executing blender game optimization within Blender 5.2+ and 5.3+ environments, supporting both headless automated batch execution (`bpy`) and live interactive sessions via Flowork OS MCP / terminal runners.

## 2. Prerequisites & Tool Dependencies
1. **Host Environment**: Blender 5.2+ or 5.3+ installed and accessible in `$PATH` (`blender`).
2. **Python Runtime**: Python 3.11+ with `bpy`, `mathutils`, and `numpy`.
3. **Flowork OS Actuators**:
   - `run_shell_command`: Direct execution of headless verification and scripts (`blender --background --python ...`).
   - `spatial_graph` / `desktop_actuator`: GUI viewport inspection and interactive verification when running in headed mode.

## 3. Standard Operating Procedure (SOP)

### Technical Specifications & Upstream Doctrine
# Game Optimization

The execution model is in `blender-core`. Always re-run `blender-asset-qa` after optimizing.

## Procedure
1. **Measure**: `scripts/mesh_stats.py -- --objects ... --budget mobile|roblox|web|vr|console|pc`. It returns tris, estimated draw calls, materials, texture VRAM, bones, and the over-budget items.
2. **Clean**: `make_lods.py --cleanup` (merge by distance 0.1 mm, dissolve degenerate, delete loose). Remove hidden faces: back-to-back faces and faces under other parts (`qa_check` → `back_to_back`, plus manual xray).
3. **Reduce in this order** (cheapest visual loss first): hidden/interior geometry → unnecessary edge loops on flat areas (Limited Dissolve 1–5°) → over-segmented cylinders → Decimate → bake detail to normals (`blender-texture-baking`).
4. **Materials**: merge to 1–2 per asset (atlas / trim sheet / shared tiling material). Each material slot per mesh is roughly one draw call.
5. **LODs**: `scripts/make_lods.py -- --objects SM_X --rename` creates `_LOD1.._LOD3` at 50/25/12.5%. Check every LOD silhouette with `look`/`review_shots`.
6. **Re-measure**, then QA, then export (`blender-export-pipelines`).

## Budgets (guidance per asset, 2026)
| Platform | Hero char tris | Prop tris | Mats/asset | Max texture | Bones |
|---|---|---|---|---|---|
| Mobile | 5–15k | 0.3–3k | 1–2 | 1024 | ≤75 |
| Roblox | body ≤10,742 (head 4k, torso 1.75k, limb 1,248); accessory/clothing 4k | ≤20k per MeshPart | 1 (SurfaceAppearance) | 1024 (PBR), 4k max | R15 + optional |
| Web (three.js/Babylon) | 10–30k | 1–10k | 1–2 | 2048 | ≤100 |
| Standalone VR (Quest) | 10–40k | 1–10k | 1–3 | 2048 | ≤100 |
| Console / PC | 50–150k | 5–50k | 2–6 | 4096 | 150–300 |
| UE5 Nanite (static) | — | millions OK | few | 4096+ | n/a |
Whole-scene limits matter more than single assets: mobile ≈ 100–300k tris visible and < 100–200 draw calls; PC ≈ millions of tris and < 2–5k draw calls.

## Decimate modes
| Mode | Use | Notes |
|---|---|---|
| `COLLAPSE` (ratio) | organic, scans, LODs | `use_symmetry`, vertex group factor to protect faces/hands; triangulates |
| `UNSUBDIV` (iterations) | meshes made by subdividing quads | restores the quad grid cleanly |
| `DISSOLVE` (planar, angle) | hard-surface / CAD | delimit `{"SEAM","SHARP","MATERIAL","UV"}`; keeps the silhouette, makes n-gons → triangulate on export |
Protect UV seams and silhouette: decimate a copy, then compare. If UVs tear at LOD1, the ratio is too aggressive for that topology, so re-unwrap or use a manual LOD.

## The hidden cost: vertex splits
GPU vertex count = unique (position, normal, UV, color) combinations. Every UV seam and hard edge **duplicates** vertices, so engine vertex counts are often 1.5–3× Blender's. Minimize seams where they aren't needed, keep hard edges = seams (so the split happens once), and don't add vertex colors or extra UV sets you don't use.

## LOD rules
- Halve the tris per level. Switch at screen size ~0.5 / 0.25 / 0.125 (UE "Screen Size", Unity LOD Group %, Godot `lod_bias` auto).
- LODs keep the same materials (or fewer: merge them at LOD2+), same pivot, same bounds.
- Skeletal LODs: remove finger/face bones at LOD2+ (the engine bone-reduction tools handle this). Keep the skinning on the same skeleton.
- Far LOD / foliage: impostor/billboard. Unreal Nanite (static, opaque/masked) and Godot's auto mesh LOD can replace a hand-made chain.
- Roblox: no manual LODs. `RenderFidelity=Automatic` does it. Keep each MeshPart ≤ 20k tris and use a simple `CollisionFidelity` (Box/Hull) for non-walkable parts.

## Draw calls and batching
- **Merge** static meshes that share a material and are always seen together (join objects). **Don't merge** across large areas, because that defeats frustum/occlusion culling.
- **Instancing**: repeated objects as linked duplicates (Alt+D, shared mesh) or collection instances. They export as instances (glTF `EXT_mesh_gpu_instancing` with `export_gpu_instances`) or as one mesh + transforms in the engine.
- **Atlases/trim sheets**: put many props on one texture set. Trim sheets let walls, panels and pipes share one 2k material.
- **Texture memory** (upper bound, uncompressed RGBA8 + mips): 1k = 5.3 MB, 2k = 21 MB, 4k = 85 MB. Engines compress (BC7/ASTC ≈ 4–8×). Pack grayscale maps into ORM channels to cut it 3×.

## Collision
Keep collision separate and simple: boxes/convex hulls of ≤ 32–255 verts. UE `UCX_<Mesh>_##`, Godot `-colonly`/`-convcolonly` suffix, Unity MeshCollider on a simplified mesh, Roblox `CollisionFidelity`. Never use the render mesh as a physics mesh for anything that moves.

## Rig and animation cost
Limit to 4 influences per vertex (`vertex_group_limit_total(limit=4)` + normalize). Remove non-deforming bones from the export (`use_armature_deform_only`). Bake constraints and drivers to keys. Shape keys cost memory per vertex, so drop unused ones and keep only deltas (glTF sparse accessors handle this).

## Gotchas
- Decimate on meshes with unapplied modifiers: `make_lods.py` evaluates them first. Other paths need you to apply them.
- Join (`Ctrl+J`) merges materials and UV maps by **name**. Rename the UV maps identically first, or the UVs get lost.
- The `Weld` modifier is the non-destructive merge by distance. Use `mode="CONNECTED"` to avoid welding separate parts.
- Triangulate before measuring if the engine will. Quads already count as 2 tris in the stats.

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
