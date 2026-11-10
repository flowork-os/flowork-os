---
name: blender-mastering
description: Comprehensive 3D asset pipeline playbook for Blender: modeling, rigging, texturing, animation, geometry nodes, and QA verification via headless bpy execution.
domain: code_dev
keywords:
  - blender
  - bpy
  - 3d_modeling
  - hardsurface
  - sculpting
  - retopology
  - uv_unwrapping
  - pbr_materials
  - texture_baking
  - geometry_nodes
  - character_rigging
  - blendshapes
  - animation_actions
  - game_optimization
  - asset_export
  - cycles_rendering
  - eevee_rendering
  - lighting_lookdev
  - asset_qa
  - headless_pipeline
author: Flowork Architecture Board
version: 1.0.0
---

# 🎨 FLOWORK OS SOVEREIGN SKILL: BLENDER 3D PIPELINE MASTERING

## 1. Executive Summary & Objective
Equip Mr. Flow and Flowork OS agents with enterprise-grade 3D production capabilities driven through Blender Python API (`bpy`). Cover full-stack 3D workflows: scene organization, hard-surface/organic modeling, UV unwrapping, PBR texturing, map baking, procedural geometry nodes, character rigging, animation, game engine export, photo-real rendering, and empirical asset QA verification.

## 2. Prerequisites & Tool Dependencies
1. **Blender Engine**:
   - Host Blender installation (`/usr/bin/blender` or `/usr/local/bin/blender`).
   - Python 3 environment with NumPy and mathutils.
2. **System Tool Dependencies**:
   - `run_shell_command` (Flowork OS host terminal executor).
   - Headless script runner at `/opt/floworkos/skills/blender-mastering/scripts/run_in_blender.py`.
   - Pipeline modules library at `/opt/floworkos/skills/blender-mastering/modules/`.
3. **Display & Headless Modes**:
   - Operates 100% headlessly (`-b --factory-startup`) or in desktop session with `DISPLAY=:0`.

## 3. Standard Operating Procedure (SOP)

### Phase 1: Environment Inspection & Scene Telemetry
Before executing any 3D operation, inspect the host Blender runtime and scene state:
```bash
python3 /opt/floworkos/skills/blender-mastering/scripts/run_in_blender.py /opt/floworkos/skills/blender-mastering/scripts/env_report.py
```
Outputs GPU compute devices, rendering engines (`CYCLES`, `BLENDER_EEVEE`), scene units (metric, 1.0 scale), and installed extensions in JSON.

### Phase 2: Pipeline Domain Routing
Identify the user's objective and mobilize the appropriate sub-module from `/opt/floworkos/skills/blender-mastering/modules/`:

| Mission | Specialized Module Directory | Key Action Script / Method |
|---|---|---|
| Scene Setup & Units | `modules/blender-scene-setup` | Metric units, collections, asset libraries |
| Hard-Surface Modeling | `modules/blender-hardsurface-modeling` | Bevel modifiers, booleans, weighted normals |
| Organic Sculpting | `modules/blender-sculpting` | Multiresolution, remeshing, sculpt brushes |
| Retopology & UVs | `modules/blender-retopology-uv` | Texel density, seams, conformal unwrap |
| PBR Materials & Shaders | `modules/blender-pbr-materials` | Principled BSDF node tree assembly |
| Layered Texturing | `modules/blender-texturing` | Grime, edge wear, decals, curvature masks |
| High-to-Low Map Baking | `modules/blender-texture-baking` | Normal, AO, roughness, ORM packed textures |
| Procedural Geometry Nodes | `modules/blender-geometry-nodes` | JSON-driven node tree construction |
| Character & Body Rigging | `modules/blender-character-rigging` | Armature generation, bone hierarchy, weights |
| Facial Blendshapes | `modules/blender-facial-shapekeys` | ARKit 52 shape keys, visemes |
| Skeletal Animation | `modules/blender-animation` | Actions, NLA tracks, mocap retargeting |
| Clothing & Garments | `modules/blender-clothing` | Surface deform, collision, poke prevention |
| Hair & Fur Grooming | `modules/blender-hair-grooming` | Hair curves, particle systems, hair cards |
| Game Poly Optimization | `modules/blender-game-optimization` | LODs, draw call reduction, batch merge |
| Multi-Engine Export | `modules/blender-export-pipelines` | glTF / FBX / USD for Unreal, Unity, Web |
| Cycles & EEVEE Rendering | `modules/blender-rendering` | Denoiser, light paths, batch camera frames |
| Studio Lookdev Lighting | `modules/blender-lighting-lookdev` | 3-point studio lighting, HDRIs, turntables |
| Asset QA & Validation | `modules/blender-asset-qa` | Automated manifold, normal, scale check |

### Phase 3: Headless Execution Protocol
Execute pipeline scripts headlessly via the sovereign runner:
```bash
python3 /opt/floworkos/skills/blender-mastering/scripts/run_in_blender.py \
  --blend /path/to/project.blend \
  /opt/floworkos/skills/blender-mastering/modules/blender-asset-qa/scripts/qa_check.py \
  --save /path/to/output.blend \
  -- --objects TargetMesh
```
For inline procedural generation, invoke expression mode:
```bash
python3 /opt/floworkos/skills/blender-mastering/scripts/run_in_blender.py \
  --expr "import bpy; bpy.ops.mesh.primitive_cube_add(size=2); bpy.ops.wm.save_as_mainfile(filepath='cube.blend')"
```

### Phase 4: API Rules & Invariant Practices
1. **Data API over Operators:** Prioritize direct data mutation (`bpy.data`, `bmesh`, `mesh.attributes`, `foreach_get/set`) over `bpy.ops` because operators fail in background execution lacking a 3D viewport context.
2. **Context Overrides:** If `bpy.ops` is unavoidable, wrap with `temp_override`:
   ```python
   with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
       bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
   ```
3. **Locale-Safe Node Lookups:** Search shader nodes strictly by `node.type == 'BSDF_PRINCIPLED'` rather than `node.name` to avoid localized translation collisions.
4. **Transform Normalization:** Always apply rotation and scale before rigging, modifier execution, physics simulation, or game engine export.

## 4. Verification & Quality Gates (Exit Code 0)
Every completed 3D task MUST undergo empirical verification:
1. **Script Execution Return Code:**
   Terminal execution must exit with code 0:
   ```bash
   python3 /opt/floworkos/skills/blender-mastering/scripts/run_in_blender.py --expr "import bpy; print('OK')"
   ```
2. **Asset QA Verification:**
   Run the automated QA check module against all synthesized meshes:
   ```bash
   python3 /opt/floworkos/skills/blender-mastering/scripts/run_in_blender.py \
     --blend output.blend \
     /opt/floworkos/skills/blender-mastering/modules/blender-asset-qa/scripts/qa_check.py
   ```
   Check for zero non-manifold edges, zero flipped face normals, normalized `[1.0, 1.0, 1.0]` scale, and valid UV coordinates.
3. **Export Artifact Existence:**
   Confirm exported `.glb`, `.fbx`, or `.blend` files exist with non-zero byte size (`ls -lh <file>`).

## 5. Failure Modes, Edge Cases & Recovery
1. **Missing 3D Viewport Context in Headless Mode:**
   - *Error:* `RuntimeError: Operator bpy.ops.X.poll() failed, context is incorrect`.
   - *Fix:* Replace operator with direct `bmesh` operations or use `bpy.context.temp_override(window=..., screen=..., area=...)`.
2. **Theme or Transform Warning in GTK/WebKit:**
   - *Symptom:* Harmless stderr warnings regarding CSS properties.
   - *Fix:* Filter stderr or ensure `--python-exit-code 1` is evaluated directly.
3. **Missing Cycles GPU Compute Device:**
   - *Cause:* Headless server or container lacks NVIDIA CUDA / AMD ROCm drivers.
   - *Recovery:* Set `scene.cycles.device = 'CPU'` and fallback gracefully to Workbench or CPU Cycles.
4. **Freed Memory Pointer Crash (SIGSEGV):**
   - *Cause:* Accessing a Python reference after applying or removing a modifier / object.
   - *Recovery:* Query object names as strings first (`names = [o.name for o in bpy.data.objects]`), perform operations, then re-acquire fresh object handles via `bpy.data.objects[name]`.

## 6. Prohibitions & Anti-Patterns
1. NEVER run per-vertex loops using `bpy.ops`. Use `bmesh` or NumPy vectorization (`foreach_get`/`foreach_set`).
2. NEVER use localized node names like `"Principled BSDF"` or `"Shader Node Tree"`. Always match against RNA `type` identifiers.
3. NEVER export models with unapplied scales or negative transform matrices.
4. NEVER leave temporary `.blend1` or `.blend@` backup files scattered in workspace roots upon mission completion.
