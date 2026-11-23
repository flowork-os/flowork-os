# 🖱️ DESKTOP ACTUATOR PROCEDURE: FLOWORK SOVEREIGN HARDWARE INPUT

---
name: desktop_actuator
description: Master procedural doctrine for zero-copy DRM screen capture and evdev/uinput virtual hardware input injection with high-speed macro action sequences and continuous brush drag paths.
keywords: [desktop_actuator, hardware_input, uinput, evdev, screen_capture, drm, macro_sequence, drag_path, vector_action, flowork, doctrine]
---

## 1. Executive Summary
`desktop_actuator` interfaces directly with `flowork-sysd` (running at `:18090`), leveraging pure-Rust kernel evdev/uinput virtual HID injection. It is 100% immune to synthetic bot-detection heuristics and can execute thousands of micro-actions at raw kernel scheduling speed.

## 2. Core Capabilities & Agile Modalities

### A. High-Speed Macro Action Sequences (`sequence`)
Executes an arbitrary chain of micro-actions in a single turn without LLM turn-by-turn roundtrips:
```json
{
  "action": "sequence",
  "sequence": [
    {"action": "mouse_move", "dx": 150, "dy": 80},
    {"action": "click", "button": "left", "clicks": 2},
    {"action": "wait", "ms": 50},
    {"action": "type_text", "text": "Flowork Kernel 7.3"},
    {"action": "key_press", "keycode": 28}
  ]
}
```

### B. Continuous Vector Brush Strokes / Drag Paths (`drag` with `via`)
Executes mouse button press down, traverses continuous coordinate delta waypoints, and releases in one atomic gesture:
```json
{
  "action": "drag",
  "button": "left",
  "via": [
    {"dx": 10, "dy": 10},
    {"dx": 20, "dy": -5},
    {"dx": 15, "dy": 25}
  ],
  "step_delay_ms": 5
}
```

### C. Direct Hardware Hotkeys & Inputs
- `hotkey`: `{ "action": "hotkey", "keycodes": [29, 31] }` (presses Ctrl+S in sequence, releases in reverse order)
- `type_text`: `{ "action": "type_text", "text": "Hello" }` (microsecond character emission)
- `scroll`: `{ "action": "scroll", "delta": -5 }` (relative wheel scroll)
- `telemetry` & `capture`: zero-copy direct DRM display query and screenshot.

## 3. Strict Operational Guidelines
- Batch micro-movements into `sequence` rather than executing individual tool calls across turns.
- Use continuous `via` paths for fluid brush strokes, dragging sliders, or complex canvas gestures.
- Verify status and receipt returns (`steps_executed`, `elapsed_ms`) to ensure Exit Code 0.
