---
name: blender-geometry-nodes
slash_command: /blender-geometry-nodes
description: "Geometry Nodes in Blender 5.3 - fields, domains, attributes, instancing, zones (simulation/repeat/for-each), closures/bundles, lists, SDF grids, node tools, baking, plus a JSON-to-node-tree builder and socket inspector. Use for scattering, procedural assets/environments, parametric tools and modi..."
domain: code_dev
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "blender"
  - "bpy"
  - "geometry-nodes"
  - "node-fields"
  - "attribute-domains"
  - "procedural-modeling"
  - "raycast-node"
  - "mesh-to-points"
  - "curve-to-mesh"
  - "sample-index"
  - "geometry-proximity"
  - "repeat-zone"
  - "simulation-nodes"
  - "group-inputs"
  - "viewer-debugging"
  - "procedural-assets"
  - "3d-nodes"
  - "code-dev"
  - "named-attributes"
  - "flowork-blender"
---

# 🎨 Blender Sovereign Subsystem: Blender Geometry Nodes

## 1. Executive Summary & Objective
Geometry Nodes in Blender 5.3 - fields, domains, attributes, instancing, zones (simulation/repeat/for-each), closures/bundles, lists, SDF grids, node tools, baking, plus a JSON-to-node-tree builder and socket inspector. Use for scattering, procedural assets/environments, parametric tools and modi...
This skill provides an authoritative, deterministic procedure for executing blender geometry nodes within Blender 5.2+ and 5.3+ environments, supporting both headless automated batch execution (`bpy`) and live interactive sessions via Flowork OS MCP / terminal runners.

## 2. Prerequisites & Tool Dependencies
1. **Host Environment**: Blender 5.2+ or 5.3+ installed and accessible in `$PATH` (`blender`).
2. **Python Runtime**: Python 3.11+ with `bpy`, `mathutils`, and `numpy`.
3. **Flowork OS Actuators**:
   - `run_shell_command`: Direct execution of headless verification and scripts (`blender --background --python ...`).
   - `spatial_graph` / `desktop_actuator`: GUI viewport inspection and interactive verification when running in headed mode.

## 3. Standard Operating Procedure (SOP)

### Technical Specifications & Upstream Doctrine
# Geometry Nodes

The execution model is in `blender-core`. Build trees with `scripts/gn_builder.py`, a compact JSON spec that's far cheaper than raw bpy. Look up exact socket names first, because they change between versions:
```
scripts/gn_builder.py -- --describe GeometryNodeDistributePointsOnFaces GeometryNodeInstanceOnPoints
scripts/gn_builder.py -- --spec scatter.json --apply Ground --set Density=20 Seed=3 Mask=@paint_mask
```
`--set Name=@attr` feeds a modifier input from a named attribute. The result reports evaluated vert/face counts and node warnings. The spec format is in the script docstring; full examples are in [references/recipes.md](references/recipes.md).

## Core concepts (get these right or nothing works)
- **Geometry** flows left→right through sockets with **circle** shapes. **Fields** (diamond sockets) are functions evaluated per element **on the node that consumes them**, in that node's domain/context.
- **Domains**: Point, Edge, Face, Face Corner, Spline, Instance, Layer. `Capture Attribute` freezes a field at a point in the graph (before topology changes), and `Evaluate on Domain` converts between domains.
- **Attributes**: built-ins (`position`, `normal`, `sharp_face`, `material_index`, `UVMap`...) plus named ones via `Store Named Attribute`. Named attributes persist after the modifier. That's how GN data reaches shaders (Attribute node) and exporters (glTF `export_attributes`, which exports names starting with `_`).
- **Instances** are cheap (one mesh, many transforms). **Realize Instances** only when you must edit per-instance geometry or export a single mesh. Realize as late as possible.
- Inputs exposed on the group interface become **modifier inputs** (5.2: `mod.properties.inputs.<identifier>.value`). Panels group them, menu sockets give enums.

## Zones and advanced types
| Feature | Nodes | Use |
|---|---|---|
| Simulation zone | `GeometryNodeSimulationInput/Output` (paired) | per-frame state: growth, particles, erosion; bake to keep |
| Repeat zone | `GeometryNodeRepeatInput/Output` | iterate N times (L-systems, relaxation, recursive subdivision) |
| For Each Element | `GeometryNodeForeachGeometryElementInput/Output` | run a sub-graph per element (per building lot, per island) |
| Closures / Bundles (5.0+) | `NodeClosureInput/Output`, `NodeCombineBundle`/`NodeSeparateBundle`, Evaluate Closure | pass functions/structured data around; reusable "strategy" node groups |
| Lists (5.2) | `GeometryNodeFieldToList`, `ListGetItem`, `ListLength`, `SortList`, `FilterList` | real arrays, not fields |
| Grids/SDF (4.x–5.x) | `MeshToSDFGrid`, `SDFGridBoolean`, `SDFGridFillet`, `SDFGridOffset`, `GridToMesh` | smooth booleans, remeshing, fillets, voxel effects |
| Grids/lists/curves (5.3) | `GridSolvePoisson`, `RasterizePoints`, `GridTopologyBoolean`, `GridDeactivateVoxels`, `GetGridNames`, `CombineList`, `ConstructCurves`, `GeometryMaterials`, `FunctionNodeGetVectorComponent` | fluid-like/voxel effects, fixed small lists, curves from position lists |
| Physics (5.2, experimental) | `GeometryNodeXPBDSolver` + bundles | node-based cloth/hair, see `blender-simulation` |
| Gizmos | `GizmoLinear/Dial/Transform` | viewport handles for inputs |
Zones need `input.pair_with_output(output)` (spec key `pairs`), plus items on the output node (`repeat_items`, `state_items`, ...; spec 4th node field).

## Procedure
1. Sketch the data flow: source geometry → selection/masks (fields) → generate/instance → transform/randomize → realize/merge → set materials/shading → output.
2. `--describe` every node type you'll use, then write the spec and build. Check `node_warnings` and the evaluated counts.
3. Expose only meaningful inputs (density, seed, scale range, materials), with min/max set.
4. Look at it (`look`), check `blender-asset-qa` if the result will be exported (realized geometry), and check `blender-game-optimization` for instance counts and tris.
5. Ship: either keep it procedural (the .blend/asset library), or apply the modifier / `visual_geometry_to_objects` for exporters.

## Rules
- Randomness: always expose a `Seed`, and use `Random Value` with the ID/Index field so results stay stable when counts change.
- Scale-independent setups use `Object Info` (Relative) and real units. Apply the object scale or read it explicitly.
- Materials: `Set Material` inside the tree. The material must exist in the file, and instances keep their own materials.
- Shading: GN output loses auto-smooth unless you add `Set Shade Smooth` + (5.x) the `Smooth by Angle` essentials group, or store `sharp_edge`.
- UVs: primitives output `UVMap` via their UV output. Store it with `Store Named Attribute` (Face Corner, 2D Vector, name `UVMap`) or it's dropped.
- Performance: avoid realizing millions of instances, prefer Points + instances for scatter, use `Merge by Distance` sparingly, and simulation zones need baking for playback/export (`object.geometry_node_bake_single` or modifier `bakes`).
- Node tools (`ng.is_tool = True`, `is_mode_edit` etc.) turn a group into an operator in the 3D View menus, for editing workflows.

## Gotchas
- 5.2: `mod["Socket_2"]` no longer works. Use `getattr(mod.properties.inputs, ident).value`, and `.type = "ATTRIBUTE"` + `.attribute_name` for attribute inputs. Compare and Random Value **sockets changed**: Random Value now has single dynamic `Min`/`Max`/`Value` sockets typed by `data_type`. Link by name, and `--describe` when unsure.
- 5.3: Import PLY's output is `Geometry` (was `Mesh`) and is a point cloud for Gaussian-splat files. Curve to Mesh adds `Miter Scale`; Realize Instances adds `Preserve Normals` (negative-scale instances).
- Sockets that are disabled for the current mode/data type are still in `node.inputs` with the same name. The builder picks the **enabled** one. Set `data_type`/`mode` props first (the builder sets props before links).
- `nt.interface.new_socket(...)` is the 4.0+ API (`ng.inputs.new` is gone).
- Exporters see the **evaluated** mesh. Instances become glTF instancing (`export_gpu_instances`) or are realized on export.

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
