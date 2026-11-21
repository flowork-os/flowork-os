# 🖥️ PASSIVE TRIGGER: SOVEREIGN DESKTOP ORCHESTRATION

## 1. Context & Activation Scope
Triggered when automating Linux desktop applications, inspecting graphical user interfaces, manipulating windows, or triggering virtual hardware input events.

## 2. Mandatory Behavioral Invariants
- **Semantic First:** Prioritize semantic accessibility tree introspection via `agent_desktop` (`snapshot`, `find`, `get`, `set_value`) for deterministic UI interaction over blind coordinate clicking.
- **Hardware Fallback & Precision Input:** Use `desktop_actuator` (evdev/uinput virtual hardware injection and zero-copy DRM capture) strictly when targeting custom canvas, games, headless renderers, or elements unmapped in AT-SPI.
- **State Transition Verification:** After executing an interactive action (click, toggle, type), verify the resulting state change via a subsequent snapshot or telemetry check before proceeding.
- **Detached GUI Spawning:** Standalone GUI apps must be launched detached via `flowork-launch <app>` or `nohup ... &` (`is_background: true`) to return control instantly (<0.3s) without blocking the agent.

## 3. Strict Prohibitions
- NEVER spam rapid blind mouse clicks without allowing UI animation and event loops to settle.
- NEVER leave modal blocker dialogs or hanging child processes unhandled.
- NEVER execute blocking foreground graphical commands that freeze the active agent turn.
