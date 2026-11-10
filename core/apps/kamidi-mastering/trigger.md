---
id: kamidi-mastering
name: Kamidi Mastering Console Pro
version: 1.0.0
category_id: CAT-016
scopes:
  - default_solo
  - canvas_active
conditions:
  app_mode:
    - audio_mastering
    - audio_dsp
keywords:
  - audio mastering
  - mastering console
  - parametric eq
  - multiband compressor
  - brickwall limiter
  - lufs metering
  - true peak
  - dynamic eq
  - sub bass 808
  - transient shaper
  - audio processing
  - ebu r128
  - dsp engine
  - sound engineering
  - studio master
  - wav export
  - music production
  - audio limiter
  - audio clipper
  - mastering presets
exclude_keywords:
  - crypto trading
  - blockchain bot
  - video editor
  - chess engine
---

# Dynamic Plugin Trigger: Kamidi Mastering Console Pro (`kamidi-mastering`)
<!-- Co-authored-by: Flowork OS <agent@floworkos.com> -->

## 1. Trigger Specification & Activation Lifecycle

When this plugin is mounted on the Flowork Canvas stage or referenced in user conversations, this trigger is evaluated:
1. **Activation Scope**: `default_solo`, `canvas_active`.
2. **Category Jurisdiction**: `CAT-016` (Media, Arts & Audio Production).
3. **Primary Roles**: Audio Mastering DSP Engineering, Multiband Dynamic Control, Brickwall Limiting, LUFS EBU R128 Loudness Normalization, and Studio WAV Export.
4. **Mandatory Runbook Inspection**:
   When receiving dispatched events via `/api/prompt-dispatch` or interacting with the backend microservice, the active agent MUST inspect `SKILL.md` via `view_file` to review REST endpoints, parameter keys, and schema contracts before executing actions.

## 2. Dynamic Port & REST IPC Contract

- **Target Dynamic Port**: Injected via `$FLOWORK_APP_PORT` (Default fallback: `17860`).
- **REST Endpoints**:
  - `GET /api/status`: Health check, active audio track metadata, DSP parameters, and LUFS telemetry.
  - `POST /api/master/parameters`: Update parametric EQ, multiband compressor, limiter threshold, and transient shaper.
  - `POST /api/presets/apply`: Apply one of 23 calibrated studio mastering presets.
  - `POST /api/prompt-dispatch`: Dispatches Canvas user events directly to the active Flowork Agent.
