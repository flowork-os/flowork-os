---
name: spatial-ui-fusion
description: Master procedural playbook for operating native Linux desktop applications via the Spatial UI Scene Graph Engine fusing AT-SPI2 accessibility trees and DRM framebuffer captures.
domain: os_doctrine
keywords:
  - flowork
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
author: Flowork Architecture Board & Dr. Flow
version: 1.0.0
---

# ⚡ Spatial UI Scene Graph & Vision Fusion Playbook

## 1. Objective
Establish deterministic, sub-10ms desktop application automation in Flowork OS by coupling the D-Bus AT-SPI2 accessibility bus with Direct Rendering Manager (DRM) framebuffer telemetry, eliminating slow high-token vision LLMs during native GUI operations.

## 2. Prerequisites
1. Running instance of `flowork-sysd` on port 18090 (`systemctl --user is-active flowork-sysd`).
2. AT-SPI2 accessibility daemon active on D-Bus session (`org.a11y.Bus`).
3. Hardware DRM/KMS or X11 screen capture access with valid `/dev/shm` shared memory write permissions.
4. Compiled native binaries:
   - `/opt/floworkos/bin/flowork-spatial-graph`
   - `/usr/local/bin/agent-desktop`
5. Virtual input device access via `/dev/uinput` or X11 XTest extension.

## 3. Standard Operating Procedure

### Step 1: Query Desktop Spatial Scene Graph
Query the active desktop environment to build an aggregated tree of interactive widgets, screen coordinates, and occlusion status:
```bash
flowork-spatial-graph --app <application_name>
```

### Step 2: Target Identification & Filtering
Locate target interaction components using fuzzy label search or semantic role filters:
```bash
# Locate button by text label
flowork-spatial-graph --find "Save" --role button

# Query full raw JSON for programmatic inspection
flowork-spatial-graph --app <application_name> --json
```

### Step 3: Dispatch Deterministic Actions
Execute atomic actions against the target widget:
```bash
# Semantic click with automatic window lifting
flowork-spatial-graph --click "Save" --app <application_name>

# Text injection into focused input target
flowork-spatial-graph --type-into "Search" --text "build-live-iso"

# Physical hardware click fallback for non-accessible canvas surfaces
flowork-spatial-graph --click "Render" --hardware
```

## 4. Verification
Execute the following verification steps to ensure Exit Code 0 across the Spatial UI subsystem:

```bash
# 1. Verify sysd spatial-graph endpoint health
curl -s -f http://127.0.0.1:18090/api/system/display/spatial-graph | grep -q '"status":"ok"'

# 2. Verify CLI query execution with Exit Code 0
flowork-spatial-graph --json | grep -q '"nodes"'

# 3. Verify tool hardlink integrity
test -x /opt/floworkos/tools/spatial_graph/run
```

## 5. Failure Modes
1. **D-Bus AT-SPI Unreachable:** Accessibility bus disconnected (`org.a11y.Bus` inactive). Remediation: verify user session environment variable `AT_SPI_BUS_ADDRESS` or restart `at-spi-bus-launcher`.
2. **Widget Occluded by Overlapping Window:** Target widget is obscured by another application on top. Remediation: the spatial engine automatically lifts and focuses the parent window via `_NET_ACTIVE_WINDOW` before dispatching input.
3. **Non-Accessible Canvas Surfaces:** Application (e.g. pure SDL game or WebGL) does not expose AT-SPI nodes. Remediation: supply `--hardware` flag to fall back to direct DRM pixel coordinate mapping and uinput HID injection.
