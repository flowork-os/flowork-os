---
title: Closed-Loop Cross-App Neural Pipeline and Headless Orchestration
category: architecture
keywords:
  - flowork-pipe
  - flowork-neural-bus
  - agentic_pipe
  - headless_dispatch
  - payload_chaining
  - placeholder_substitution
date: 2026-11-09
---

# Cross-App Neural Pipeline Architecture

## 1. Overview
The Cross-App Neural Pipeline (`flowork-pipe`) establishes an agentic multimodal execution mesh across Flowork OS Craft Suite applications. Rather than operating in isolated silos, applications can be chained sequentially via a Unix-pipe semantic syntax.

## 2. Technical Implementation
- **Neural Bus Daemon (`/opt/floworkos/bin/flowork-neural-bus.js`):**
  - Upgraded `executePipeline(pipeReq, replyCb)` to execute stages sequentially.
  - Dynamic binary resolver `findHeadlessBinary(appName)` inspecting `/opt/floworkos/apps/<app>/bin/<app>-cli`, `/opt/floworkos/apps/<app>/bin/<app>`, `/opt/floworkos/bin/<app>`, `/usr/local/bin/<app>`, and `PATH`.
  - Stdin payload piping (`input: JSON.stringify(currentPayload)`) and stdout JSON parsing.
  - Dynamic parameter resolution: replaces `{prev}`, `{file}`, and `{input}` placeholders with data from prior stages.
  - Abort-on-error mechanism emitting `pipeline_failed` events with precise stage diagnostics.
- **Agentic Pipe CLI (`/opt/floworkos/bin/flowork-pipe`):**
  - Parses pipe expressions (`app1::action --arg val | app2::action`).
  - Supports `--json` flag for raw programmatic integration.
  - Outputs live stage execution progress and final payload upon completion.
  - Strictly returns Exit Code 0 on complete success, Exit Code 1 on failure.
- **Python SDK (`/opt/floworkos/connector/neural_bus_sdk.py`):**
  - Extended HTTP pipeline timeout to 60 seconds to support compute-heavy rendering stages.

## 3. Empirical Verification
- Verified end-to-end chaining of mock audio synthesis to video stitching with placeholder replacement (`{file}` -> `/tmp/voiceover.wav`).
- Verified zero errors, 2 stages completed, and Exit Code 0.
