---
name: blender-scene-setup
slash_command: /blender-scene-setup
description: "Set up and audit Blender scenes the way studios do - units and real-world scale, collection layout, naming conventions (SM_/SK_/T_/M_), origins, linking vs appending, library overrides, asset libraries and catalogs, collection exporters, orphan/path cleanup. Use when starting a project, organizin..."
domain: code_dev
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "blender"
  - "bpy"
  - "scene-setup"
  - "studio-conventions"
  - "metric-system"
  - "unit-scale"
  - "frame-rate-preset"
  - "view-layer-hierarchy"
  - "collection-structure"
  - "world-environment"
  - "camera-rig"
  - "color-management-agx"
  - "clipping-distances"
  - "grid-spacing"
  - "scene-audit"
  - "production-template"
  - "3d-scene"
  - "code-dev"
  - "layer-masking"
  - "flowork-blender"
---

# 🎨 Blender Sovereign Subsystem: Blender Scene Setup

## 1. Executive Summary & Objective
Set up and audit Blender scenes the way studios do - units and real-world scale, collection layout, naming conventions (SM_/SK_/T_/M_), origins, linking vs appending, library overrides, asset libraries and catalogs, collection exporters, orphan/path cleanup. Use when starting a project, organizin...
This skill provides an authoritative, deterministic procedure for executing blender scene setup within Blender 5.2+ and 5.3+ environments, supporting both headless automated batch execution (`bpy`) and live interactive sessions via Flowork OS MCP / terminal runners.

## 2. Prerequisites & Tool Dependencies
1. **Host Environment**: Blender 5.2+ or 5.3+ installed and accessible in `$PATH` (`blender`).
2. **Python Runtime**: Python 3.11+ with `bpy`, `mathutils`, and `numpy`.
3. **Flowork OS Actuators**:
   - `run_shell_command`: Direct execution of headless verification and scripts (`blender --background --python ...`).
   - `spatial_graph` / `desktop_actuator`: GUI viewport inspection and interactive verification when running in headed mode.

## 3. Standard Operating Procedure (SOP)

### Technical Specifications & Upstream Doctrine
# Scene Setup & Hygiene

The execution model and verification steps are in `blender-core`.

## Procedure
1. Run `scripts/scene_audit.py` (add `--fix purge scale paths` only on files you own). It reports units, unapplied/negative scale, default names, objects in the scene root, missing images, orphans and far-off origins.
2. Set units: Metric, Unit Scale **1.0**, Length meters. Keep 1.0 even for Unreal/Roblox, because exporters handle the conversion (see `blender-export-pipelines`).
3. Build the collection layout (below). Every object must be in a named collection, never the scene root.
4. Name everything with the conventions below. Rename after every duplicate or join so no `.001` suffixes remain.
5. Set origins: props at the bottom-center (they sit on the ground at Z=0), characters at world origin between the feet, doors/hinges at the pivot.
6. Apply rotation and scale on meshes (Ctrl+A). Keep location unless the asset should export at the origin.
7. Re-run the audit. It's done when `issues` is empty or every remaining issue is intentional and explained.

## Collection layout (one asset per .blend, or one collection per asset)
```
ASSET_Crate
├── Crate_high      # sculpt / subdiv source (exclude from export)
├── Crate_low       # game mesh(es) SM_Crate, SM_Crate_LOD1..
├── Crate_bake      # cages, bake helpers
├── Crate_collision # UCX_SM_Crate_00 (UE) / Crate-col (Godot)
└── Crate_ref       # reference images/blockout (hide_render)
```
Use **Collection Exporters** (4.2+) to define the export once per collection, then re-export with one call:
```python
with bpy.context.temp_override(collection=col):
    bpy.ops.collection.exporter_add(name="IO_FH_gltf2")
ex = col.exporters[-1]; ex.export_properties.filepath = "//export/SM_Crate.glb"
with bpy.context.temp_override(collection=col):
    bpy.ops.collection.exporter_export(index=len(col.exporters) - 1)
```
`bpy.ops.wm.collection_export_all()` re-runs every collection exporter. 5.3: glTF exporters set the origin with `collection_center_mode` (`WORLD_ORIGIN`, `CENTER_MASS`, `OBJECT_POSITION`, `INSTANCE_OFFSET`). Collections also get one **importer** (USD only, `collection.importer_add` / `importer_import`) whose settings are saved in the .blend.

## Naming conventions (Unreal-style, accepted by all engines)
| Type | Pattern | Example |
|---|---|---|
| Static mesh | `SM_<Name>[_LOD#]` | `SM_Crate_LOD1` |
| Skeletal mesh / rig | `SK_<Name>` / `RIG_<Name>` (armature object `Armature` or `root`) | `SK_Hero` |
| Material | `M_<Name>` / instance `MI_<Name>` | `M_Wood_Oak` |
| Texture | `T_<Name>_<Suffix>`: `_BC` base color, `_N` normal, `_ORM` (R=AO G=Rough B=Metal), `_E` emissive, `_M` mask | `T_Crate_ORM` |
| Collision | UE `UCX_<Mesh>_##`, Godot suffix `-col`/`-colonly`/`-convcolonly` | `UCX_SM_Crate_00` |
| Bones/sides | `.L`/`.R` suffix (Blender mirror tools depend on it) | `upper_arm.L` |
| Actions | `<Rig>_<Clip>` | `Hero_Run` |
Use ASCII only, no spaces, and PascalCase or snake_case consistently across the project.

## Real-world scale reference (meters)
Door 2.0–2.1 × 0.9 · ceiling 2.4–2.7 · table 0.75 · chair seat 0.45 · counter 0.9 · stair rise 0.18 / tread 0.28 · adult human 1.7–1.8 (eyes 1.6) · car 4.5 × 1.8 × 1.5. Roblox: 1 stud ≈ 0.28 m; default character ≈ 5 studs tall. Wrong scale breaks physics, lighting falloff, DOF and texel density, so check `ob.dimensions` first.

## Linking, appending, overrides
- **Append** (`libraries.load(link=False)`) makes a local copy. Use it for one-off reuse.
- **Link** (`link=True`) is read-only, updates from the source and is what pipelines use. To edit a linked collection, add a library override: `ob.override_hierarchy_create(scene, view_layer, do_fully_editable=False)`. Only overridable properties (transforms, pose, and anything marked overridable) can change.
- Keep library paths relative (`//`). Check `bpy.data.libraries` for broken paths.

## Asset libraries
- Mark: `ob.asset_mark(); ob.asset_generate_preview()`. Metadata goes in `ob.asset_data` (`author`, `description`, `license`, `tags.new("wood")`, `catalog_id`).
- Catalogs live in `blender_assets.cats.txt` at the library root, one line per catalog: `UUID:Path/Sub:Simple Name`.
- Register a library with `prefs.filepaths.asset_libraries.new(name=..., directory=...)`. 5.2+: remote libraries via `use_remote_url` + `remote_url`. In 5.2 `active_asset_library` indices are offset by 2 ("All", "Essentials").
- Import method per library: `LINK`, `APPEND`, `APPEND_REUSE` (default; reuses already-appended data).

## Hygiene rules
- Purge orphans before shipping (`bpy.data.orphans_purge(do_recursive=True)`). Use fake users only on purpose.
- Image paths: relative (`file.make_paths_relative`), or pack for single-file delivery (`file.pack_all`).
- Never ship multi-user mesh data that has an unapplied per-object scale. Instances are fine, but bake scale before export.
- Hide helpers with `hide_render=True` **and** exclude them from export collections; viewport hiding alone isn't enough.
- One active scene per file for delivery. Extra scenes confuse exporters (`use_active_scene`).

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
