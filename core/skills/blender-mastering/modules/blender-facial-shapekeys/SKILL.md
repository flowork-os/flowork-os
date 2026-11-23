---
name: blender-facial-shapekeys
slash_command: /blender-facial-shapekeys
description: "Facial rigs and shape keys in Blender 5.3 - ARKit 52 blendshapes, visemes for lip-sync, sculpting expressions, splitting symmetric shapes into Left/Right, mirroring, corrective and combination shapes, drivers and control rigs, bone+blendshape hybrids, export to engines (Unity, Unreal, Roblox dyna..."
domain: code_dev
author: Flowork Architecture Board
version: 1.0.0
keywords:
  - "blender"
  - "bpy"
  - "facial-shapekeys"
  - "arkit-blendshapes"
  - "52-shapekeys"
  - "viseme-lip-sync"
  - "jaw-open"
  - "eye-blink"
  - "expression-library"
  - "blendshape-transfer"
  - "topology-mirror"
  - "sculpt-wrinkles"
  - "face-rigging"
  - "bone-drivers"
  - "speech-animation"
  - "real-time-faces"
  - "3d-avatar"
  - "code-dev"
  - "corrective-shapes"
  - "flowork-blender"
---

# 🎨 Blender Sovereign Subsystem: Blender Facial Shapekeys

## 1. Executive Summary & Objective
Facial rigs and shape keys in Blender 5.3 - ARKit 52 blendshapes, visemes for lip-sync, sculpting expressions, splitting symmetric shapes into Left/Right, mirroring, corrective and combination shapes, drivers and control rigs, bone+blendshape hybrids, export to engines (Unity, Unreal, Roblox dyna...
This skill provides an authoritative, deterministic procedure for executing blender facial shapekeys within Blender 5.2+ and 5.3+ environments, supporting both headless automated batch execution (`bpy`) and live interactive sessions via Flowork OS MCP / terminal runners.

## 2. Prerequisites & Tool Dependencies
1. **Host Environment**: Blender 5.2+ or 5.3+ installed and accessible in `$PATH` (`blender`).
2. **Python Runtime**: Python 3.11+ with `bpy`, `mathutils`, and `numpy`.
3. **Flowork OS Actuators**:
   - `run_shell_command`: Direct execution of headless verification and scripts (`blender --background --python ...`).
   - `spatial_graph` / `desktop_actuator`: GUI viewport inspection and interactive verification when running in headed mode.

## 3. Standard Operating Procedure (SOP)

### Technical Specifications & Upstream Doctrine
# Facial Rig & Shape Keys

The execution model is in `blender-core`. The body rig is in `blender-character-rigging`.

## Choose the approach
| Approach | Use | Notes |
|---|---|---|
| **Blendshapes (ARKit 52)** | games, VTubers, mocap (iPhone/Live Link Face), web/VRM | the industry interchange set; each shape is sculpted |
| **Bones** (jaw, eyes, lids, brows, lips) | stylized, low memory, mobile | jaw + eyes as bones are almost always right |
| **Hybrid** | most production game heads | jaw/eye/tongue bones + blendshapes for everything soft |
| **Rigify face** (`human` metarig) | film-style keyframe animation inside Blender | 100+ face bones, heavy for engines |

## Procedure (blendshapes)
1. The head mesh needs clean loops around the eyes and mouth (`blender-retopology-uv`), with eyes, teeth and tongue as separate objects parented or weighted to bones.
2. `scripts/shapekeys.py -- --mesh Head --create arkit` (or `--create visemes` for the 15 Oculus visemes) creates empty, correctly named keys.
3. Sculpt each key (live: sculpt mode on the active key, `use_shape_key_edit_mode`). Symmetric expressions can be sculpted once, then `--split eyeBlink` gives `eyeBlinkLeft/Right` with a soft blend across X=0 (`--falloff` m).
4. `--mirror browDownLeft` builds `browDownRight` (topology-independent mirror).
5. `--report` lists unsculpted keys, the max offset per key, and missing ARKit names. A shape is done only when every key moves and nothing is left over.
6. Optional: `--drivers FaceCtrl` adds a controller with 0–1 custom properties driving each key, for keyframing in Blender.
7. Check the extremes and **combinations** (jawOpen + mouthSmile, eyeBlink + eyeSquint) with `look`. Fix them with corrective combination keys driven by the product of two keys.

## Shape key rules
- Shapes are **deltas from Basis**. Never change the Basis topology after creating keys (adding or removing verts destroys every key).
- One action per key. No head or neck movement inside face keys (bones do that). Keep eyelids sliding over the eye surface, not through it (check with `blender-asset-qa` zfighting on lid/eye).
- Range 0–1. `slider_max` can be raised for exaggeration, but engines clamp to 0–1.
- Relative keys (`use_relative=True`, the default) are the only kind that exports.
- Name exactly per spec (case-sensitive): `eyeBlinkLeft`, not `EyeBlink_L`. Engines map by name.
- Keys on meshes with Subdivision: sculpt at level 0, and keep the subdivision modifier **after** the shape keys (they're evaluated first anyway).
- Applying modifiers on a mesh with shape keys fails. Use `modifier_apply_as_shapekey` for deform modifiers, or apply them before creating keys.

## Correctives and combination shapes
- Corrective for a bone pose: sculpt in the posed state, then drive with a `TRANSFORMS` variable (`ROT_X`, `LOCAL_SPACE`, mapped to 0–1).
- Combination: key `jawOpen_mouthSmile` with driver `SCRIPTED` expression `a*b`, from the two key values (`SINGLE_PROP` `key_blocks["jawOpen"].value`). Simple expressions don't need Python auto-run.

## Engine notes
- **Unity**: FBX blendshapes. In the Model importer, set Blend Shape Normals = Calculate (or Import if smoothing was exported). ARKit names map to the AR Foundation face-tracking samples.
- **Unreal**: morph targets ("Import Morph Targets"). Live Link Face / MetaHuman Animator use ARKit names, and the Pose Asset maps the curves. No leaf bones.
- **Roblox dynamic heads**: FACS-based poses with Roblox-specific names, authored as animation frames on a head rig (Creator Hub "Dynamic heads" spec). Build from the official Blender template. ARKit sculpts can be reused by renaming/mapping. Head ≤ 4,000 tris.
- **VRM / web (three-vrm, ReadyPlayerMe-style)**: ARKit 52 + visemes as glTF morph targets (`export_morph=True`). Keep the morph-normal export on only if shading needs it (it doubles the size).
- Drop unused keys before export. Every key costs memory per vertex (glTF sparse accessors help).

## Gotchas
- `ob.shape_key_add(from_mix=False)` copies the Basis. `from_mix=True` bakes the current mix (useful for combos, dangerous by accident).
- `shape_key_mirror(use_topology=False)` needs a mesh symmetric on X. Run it on the **active** key (the script handles this).
- Driver variables on shape keys use the Key ID (`ob.data.shape_keys`), not the mesh: `fc = kb.driver_add("value")`.

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
