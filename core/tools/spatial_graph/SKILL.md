---
name: spatial_graph
description: Sovereign procedural doctrine for native Linux desktop Spatial UI Scene Graph inspection, AT-SPI2 accessibility and DRM framebuffer fusion, and sub-10ms deterministic widget interaction.
keywords:
  - spatial
  - scene
  - graph
  - atspi
  - accessibility
  - drm
  - framebuffer
  - uinput
  - desktop
  - automation
  - widget
  - click
  - interaction
  - occlusion
  - coordinates
  - deterministic
  - latency
  - fusion
  - sovereign
  - flowork
---

# ⚡ FLOWORK OS SOVEREIGN TOOL SKILL: SPATIAL_GRAPH

## 1. Executive Summary
The `spatial_graph` tool provides sub-10ms native Linux desktop scene graph inspection and deterministic widget manipulation by fusing D-Bus AT-SPI2 accessibility trees with raw hardware DRM/KMS framebuffer captures (`/dev/shm/flowork_drm_latest.bgra`). It bypasses slow, high-token Vision LLMs entirely for desktop app operations.

## 2. Core Operational Loop
1. **Inspect Scene Graph (`inspect`):**
   Execute an inspection query to retrieve all interactive widgets, coordinates, and occlusion status across active desktop windows:
   ```json
   {
     "action": "inspect",
     "app": "flowork-studio"
   }
   ```
2. **Find Target Widget (`find`):**
   Locate specific widgets by text label, title, or semantic role:
   ```json
   {
     "action": "find",
     "app": "flowork-studio",
     "target": "Save"
   }
   ```
3. **Execute Deterministic Click (`click`):**
   Dispatch instantaneous click targeting either the AT-SPI press action or physical uinput hardware event:
   ```json
   {
     "action": "click",
     "target": "Close",
     "app": "flowork-studio"
   }
   ```
4. **Direct Text Injection (`type`):**
   Focus and inject text into target input fields without manual typing delays:
   ```json
   {
     "action": "type",
     "target": "Search",
     "text": "build-live-iso"
   }
   ```

## 3. Invariants & Best Practices
- Prefer AT-SPI semantic actions by default; toggle `"hardware": true` only when operating custom canvas, SDL, or OpenGL surfaces.
- Always check `is_occluded` flag in the returned node payload; occluded widgets will automatically receive focused window lifting before click dispatch.
- Ensure all operational assertions achieve verifiable Exit Code 0.
