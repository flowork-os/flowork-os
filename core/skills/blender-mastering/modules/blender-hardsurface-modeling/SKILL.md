---
name: blender-hardsurface-modeling
slash_command: /blender-hardsurface-modeling
description: "Hard-surface and prop modeling in Blender 5.3 - blockout-to-detail flow, non-destructive modifier stacks (Mirror, Boolean Exact/Manifold, Bevel, Weighted Normal, Smooth by Angle), mid-poly vs subdivision vs high-to-low workflows, shading/custom normals, cylinder segment budgets, edge attributes f..."
domain: code_dev
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "blender"
  - "bpy"
  - "hardsurface-modeling"
  - "blockout-pipeline"
  - "boolean-cleanup"
  - "weighted-normals"
  - "bevel-modifier"
  - "subdivision-surface"
  - "edge-loops"
  - "crease-weight"
  - "cutter-collections"
  - "poly-quads"
  - "mechanical-props"
  - "inset-extrude"
  - "kitbashing"
  - "hard-surface-cad"
  - "3d-props"
  - "code-dev"
  - "curved-paneling"
  - "flowork-blender"
---

# 🎨 Blender Sovereign Subsystem: Blender Hardsurface Modeling

## 1. Executive Summary & Objective
Hard-surface and prop modeling in Blender 5.3 - blockout-to-detail flow, non-destructive modifier stacks (Mirror, Boolean Exact/Manifold, Bevel, Weighted Normal, Smooth by Angle), mid-poly vs subdivision vs high-to-low workflows, shading/custom normals, cylinder segment budgets, edge attributes f...
This skill provides an authoritative, deterministic procedure for executing blender hardsurface modeling within Blender 5.2+ and 5.3+ environments, supporting both headless automated batch execution (`bpy`) and live interactive sessions via Flowork OS MCP / terminal runners.

## 2. Prerequisites & Tool Dependencies
1. **Host Environment**: Blender 5.2+ or 5.3+ installed and accessible in `$PATH` (`blender`).
2. **Python Runtime**: Python 3.11+ with `bpy`, `mathutils`, and `numpy`.
3. **Flowork OS Actuators**:
   - `run_shell_command`: Direct execution of headless verification and scripts (`blender --background --python ...`).
   - `spatial_graph` / `desktop_actuator`: GUI viewport inspection and interactive verification when running in headed mode.

## 3. Standard Operating Procedure (SOP)

### Technical Specifications & Upstream Doctrine
# Hard-Surface Modeling

The execution model is in `blender-core`. Run `blender-asset-qa` after every modeling pass.

## Pick the workflow first
| Workflow | When | Output |
|---|---|---|
| **Mid-poly** (bevel + weighted normals, no bake) | modern games, props seen up close, fast iteration | game mesh directly; tiling materials/trim sheets |
| **High → low** (high via booleans+bevel or subd, low baked) | hero assets, unique textures, tight tri budgets | `_high` + `_low` → `blender-texture-baking` |
| **Subdivision** (support loops/creases + Subsurf) | renders, product viz, film | smooth surfaces, edges held by loops/creases |

## Procedure
1. **Blockout** at real scale (`ob.dimensions`) from primitives. Settle the silhouette and proportions before any detail. Check against references.
2. **Apply scale** (`transform_apply(scale=True)`) before bevels, booleans or solidify, because modifier distances use object space.
3. **Primary → secondary → tertiary** forms. Booleans for cuts and panels, then bevels. Small tertiary details go in normal maps/decals, or into the high-poly as "floaters" for baking.
4. **UV the base mesh now** (mid-poly). Bevel/Boolean modifiers propagate UVs, but after bevels no edge is sharp enough to auto-seam. Then **build the stack** with `scripts/apply_stack.py -- --objects Body --preset midpoly --cutters Cut1 Cut2`. Order: Mirror → Booleans → Bevel → Weighted Normal → (Triangulate at export).
5. **Shading check**: smooth shading + Weighted Normal (keep sharp). There must be no gradients across flat faces. View with a matcap or `look` in `solid` shading.
6. **QA** with `blender-asset-qa`, then apply the stack only on an export copy (`--apply`), keeping the editable source.

## Stack rules
- **Booleans**: put cutters in a `Cutters` collection with display `WIRE` and `hide_render=True`. Solver: `EXACT` (robust default), `MANIFOLD` (much faster, but inputs must be closed manifold), `FLOAT` (legacy fast, fragile with coplanar faces). With many cutters, use `operand_type="COLLECTION"`.
- Avoid coplanar boolean faces: extend cutters slightly past the surface. They also cause z-fighting.
- **Bevel**: `limit_method="ANGLE"` (30°), or `"WEIGHT"` with a `bevel_weight_edge` attribute for hand-picked edges. Turn on `use_clamp_overlap`, `harden_normals=True`, `miter_outer="MITER_ARC"`. Width ≈ 0.5–2% of the part's size, kept consistent across the asset.
- **Weighted Normal** after Bevel: `mode="FACE_AREA"`, `keep_sharp=True`, weight 50. Needs smooth faces (remove the `sharp_face` attribute or call `shade_smooth`).
- **Smooth by Angle** (4.1+, replaces auto smooth): `bpy.ops.object.shade_auto_smooth(angle=rad)` adds a GN modifier, or `shade_smooth_by_angle` sets `sharp_edge` destructively.
- **Mirror**: `use_clip=True`, `use_mirror_merge=True`. Model one half only at x ≥ 0.
- **Subdivision**: hold edges with support loops (a loop 1–5% of the face width from the edge) or `crease_edge` (0–1). Turn on `use_limit_surface`. Don't use creases if the asset goes to an engine.
- **Triangulate** only for export/baking (`keep_custom_normals=True`, `BEAUTY`). Triangulating the bake mesh and the export mesh identically keeps normal maps synced.

## Topology rules
- **N-gons**: fine on flat, non-deforming faces in mid-poly/game meshes. Never use them on curved surfaces or anything that subdivides or deforms.
- **Poles** (5+ edges) should sit on flat areas, never on a curvature peak or bevel.
- **Cylinder segments by on-screen size**: small (bolts) 6–8, medium (handles) 12–16, large (barrels) 24–32, hero/close-up 48+. Use multiples of 4 or 8 so booleans/mirrors line up with existing loops.
- **No long, thin triangles** across visible curved areas (shading and LOD artifacts).
- **Panel lines**: inset + extrude in (mid-poly) or a boolean groove on the high-poly, then bake.
- Spend density where the silhouette needs it, not on flat faces.

## Edge/face attributes from Python (4.0+ names)
```python
me = ob.data
bw = me.attributes.get("bevel_weight_edge") or me.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
cr = me.attributes.get("crease_edge") or me.attributes.new("crease_edge", "FLOAT", "EDGE")
sh = me.attributes.get("sharp_edge") or me.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
bw.data[edge_index].value = 1.0; sh.data[edge_index].value = True
me.edges[edge_index].use_seam = True          # seams are still an edge property
```
Select sharp edges by angle in bmesh: `e.calc_face_angle(0) > math.radians(30)`.

## Gotchas
- A bevel that looks blobby or flips usually means unapplied/non-uniform scale or overlapping geometry (turn on clamp).
- A Boolean that returns nothing or garbage: the cutter isn't closed/manifold (Exact copes, Manifold fails), or its normals are inverted.
- Weighted Normal has no effect: faces are flat-shaded, or an earlier modifier destroyed the custom normals.
- 5.2: the GN `Mesh Bevel` node exists for procedural bevels inside node trees (`blender-geometry-nodes`).
- 5.3: LoopTools is built in (`mesh.relax_edge_loops`, `curve_edge_loops_between_selected`, `fit_edge_loops_to_annotation`, `space_edge_loops_evenly`). `mesh.primitive_quad_sphere_add(segments=4)` gives an all-quad cube-sphere: no pinched poles, so it subdivides and bevels cleanly.
- Trim-sheet/mid-poly assets: UVs go to the trim strips (`blender-retopology-uv`) and materials tile (`blender-pbr-materials`).

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
