---
name: blender-asset-qa
slash_command: /blender-asset-qa
description: "Mandatory review gate for any mesh or asset created or edited in Blender. Detects z-fighting, floating/detached parts, inverted or inconsistent normals, non-manifold/open geometry, degenerate faces, duplicate verts, n-gons, unapplied scale, UV problems, bad skin weights, material/texture errors, ..."
domain: code_dev
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "blender"
  - "bpy"
  - "asset-qa"
  - "mesh-inspection"
  - "non-manifold"
  - "isolated-vertices"
  - "z-fighting"
  - "ngon-detection"
  - "normal-orientation"
  - "transform-applied"
  - "texture-paths"
  - "naming-conventions"
  - "polycount-budget"
  - "uv-overlap"
  - "material-slots"
  - "headless-lint"
  - "quality-gate"
  - "code-dev"
  - "3d-verification"
  - "flowork-blender"
---

# 🎨 Blender Sovereign Subsystem: Blender Asset Qa

## 1. Executive Summary & Objective
Mandatory review gate for any mesh or asset created or edited in Blender. Detects z-fighting, floating/detached parts, inverted or inconsistent normals, non-manifold/open geometry, degenerate faces, duplicate verts, n-gons, unapplied scale, UV problems, bad skin weights, material/texture errors, ...
This skill provides an authoritative, deterministic procedure for executing blender asset qa within Blender 5.2+ and 5.3+ environments, supporting both headless automated batch execution (`bpy`) and live interactive sessions via Flowork OS MCP / terminal runners.

## 2. Prerequisites & Tool Dependencies
1. **Host Environment**: Blender 5.2+ or 5.3+ installed and accessible in `$PATH` (`blender`).
2. **Python Runtime**: Python 3.11+ with `bpy`, `mathutils`, and `numpy`.
3. **Flowork OS Actuators**:
   - `run_shell_command`: Direct execution of headless verification and scripts (`blender --background --python ...`).
   - `spatial_graph` / `desktop_actuator`: GUI viewport inspection and interactive verification when running in headed mode.

## 3. Standard Operating Procedure (SOP)

### Technical Specifications & Upstream Doctrine
# Asset QA (review gate)

Never assume a generated or edited mesh is correct. Check it with numbers, then look at it.

## Procedure
1. **Automated check**, passing one asset's objects together:
   `scripts/qa_check.py -- --objects Body Head Hat --profile game`
   Profiles: `game` (default), `render` (lenient), `print` (watertight required), `roblox` (20k tris/mesh, watertight, no n-gons, ≤4 influences).
2. **Fix every `errors` entry** (table below), then re-run until `"pass": true`. Each warning must be either fixed or explicitly accepted, with the reason reported to the user.
3. **Visual check, always**:
   - Live: MCP `look` with `mode="angles"` on the targets, once in `material`/`solid` shading and once in `wireframe`. Use `xray` for internals.
   - Headless: `scripts/review_shots.py -- --objects ... --mode random` (one color per object, which makes detached pieces obvious), then `--mode wire` for topology. Open the returned PNG.
4. Report: tris per object, issues fixed, and remaining accepted warnings.

## What each finding means → fix
| Finding | Cause | Fix |
|---|---|---|
| `zfighting` A<->B | two surfaces facing the same way within `--eps` (1 mm) that overlap | delete the hidden duplicate, or offset ≥ 2–5 mm along the normal, or boolean/merge them |
| `back_to_back` | faces touching with opposite normals (boxes glued face-to-face) | delete the hidden faces (wasted tris, bake artifacts) |
| `floating` | island/object not touching any other part within `--tol` | move it to make contact (snap), bridge it, or join and merge. If floating is intended (sparks, UI), check it separately |
| `enclosed` | part fully inside another, not touching (eyes, internal mechanics) | usually fine. Confirm it's intended |
| `inside_out_islands` | closed part with normals pointing in | `mesh.normals_make_consistent(inside=False)` on that part |
| `inconsistent_normals_edges` | neighbouring faces wound in opposite directions | recalc normals; if it persists, look for non-manifold seams |
| `nonmanifold_edges` / `wire_edges` | >2 faces per edge, or stray edges | dissolve/delete the extra faces; `delete_loose` |
| `boundary_edges` | open holes (bad for print/Roblox/bakes) | fill (`fill_holes`/`edge_face_add`) or cap |
| `degenerate_faces` / `zero_length_edges` | collapsed geometry | `dissolve_degenerate(threshold=1e-4)` |
| `duplicate_verts` | unwelded seams | `remove_doubles(threshold=1e-4)` (Merge by Distance); check UV seams after |
| `ngons` | faces with >4 sides | triangulate/quadrangulate locally; n-gons are fine only on flat hard-surface faces that never deform |
| unapplied/negative scale | object transform | `transform_apply(rotation=True, scale=True)`; negative scale flips normals on export |
| `uv_maps: 0` / zero-area UV / overlap | missing or bad unwrap | `blender-retopology-uv` |
| unweighted / >4 influences | skinning | `blender-character-rigging` (`rig_check.py`) |
| `ground_z` ≠ 0 | asset floats or sinks | move the origin to the bottom and set z = 0 (props) |
| faces on empty/missing slot | material removed or index out of range | assign a material; engines show grey/magenta |
| `feeds [...] but is sRGB` | normal/roughness/metal/AO map tagged as color | `image.colorspace_settings.is_data = True` (Non-Color) |
| missing texture file | broken path, unpacked | relink (`blender-scene-setup` path cleanup) or pack |
| unused slot / Non-Color base color | leftovers, wrong tag | remove the slot; base color and emission are sRGB |

## Manual checks the script can't fully judge
- **Silhouette and proportions** at the target camera distance. Compare with references and real-world size (`ob.dimensions`).
- **Shading artifacts**: smoothing on hard edges (needs sharp edges/weighted normals), and pinching at poles on curved surfaces.
- **Intersections that look wrong** (a leg clipping a seat), even though they're "attached".
- **Interior/hidden geometry** that wastes tris (use `xray`).
- **Deformation**: pose the rig at extremes (elbow 140°, knee 150°, shoulder raised) and look for collapsing volume.
- **Material assignment**: slots and color spaces are checked automatically. Still look at whether each part got the *intended* material.

## Tuning
- `--eps` is the z-fight distance. Raise it to 0.005 for large environment scenes, and lower it to 0.0002 for tiny jewelry.
- `--tol` is the contact tolerance for detached parts. Raise it for chunky kitbash.
- `--no-modifiers` checks the base mesh. By default the evaluated (modifier) result is checked, which is what gets exported.
- Above `--max-tris` (300k), the z-fight and floating checks are skipped. Check high-poly sources per part instead.

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
