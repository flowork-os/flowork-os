# 👑 PASSIVE TRIGGER: APP-ON-DEMAND JIT SOFTWARE SYNTHESIS

## 1. Context & Activation Scope
Triggered when the user asks to build, create, synthesize, generate, or code a new desktop application, tool GUI, or utility (e.g., "bikinin app...", "buatkan aplikasi...", "synthesize application", "create desktop tool", "flow-app", "craft-app").

## 2. Mandatory Behavioral Invariants
- **ZERO INSTALLER HUNTING:** Never instruct the user to download third-party Linux deb/rpm/flatpak packages or compile foreign software if a bespoke sovereign application can be synthesized directly via `flow-app`.
- **SOVEREIGN '*flow' ECOSYSTEM MANDATE:** All synthesized applications MUST end with `flow` (e.g. `notesflow`, `diskflow`, `monitorflow`, `termflow`). `flow-app` automatically enforces this suffix.
- **SOVEREIGN SYNTHESIS PROTOCOL:** Execute the 4-step JIT pipeline:
  1. **Scaffold:** Execute `/opt/floworkos/bin/flow-app create <app_id> --name "<Name>" --desc "<Description>" --icon "<Emoji>" --category "<Category>"`.
  2. **Implement Logic:** Surgically update `/opt/floworkos/apps/<app_id>/ui/index.html` (interactive Quantum Glass UI) and optionally `/opt/floworkos/apps/<app_id>/bin/backend.py` for Python logic.
  3. **Verify:** Run `/opt/floworkos/bin/flow-app test <app_id>` to ensure headless WebKit initialization achieves **Exit Code 0**.
  4. **Register & Launch:** Run `/opt/floworkos/bin/flow-app register <app_id>` followed by `/opt/floworkos/bin/flow-app launch <app_id>`.
- **CLEAN DOCK REGISTRATION:** Register applications exclusively into `/usr/share/applications/` (Start menu / Whisker) and Flowork Launchpad (Orbit Deck). NEVER pin newly synthesized applications to the bottom task dock (Plank).
- **QUANTUM GLASS AESTHETICS:** Strictly enforce the Flowork Sovereign visual style:
  - 0.60 opacity, 0.40 transparent backdrop blur.
  - Obsidian `#000000` neutral background.
  - JetBrains Mono Bold typography.
  - Neon green `#00ff66` and cyan `#00f2fe` accents.

## 3. Strict Prohibitions
- NEVER leave synthesized applications untested without verifying `flow-app test <app_id>` returns Exit Code 0.
- NEVER hardcode user home paths (`/home/awenkaudico`); always use `/opt/floworkos/apps/<app_id>`.
- NEVER pollute system directories outside `/opt/floworkos/apps/` and `/usr/share/applications/`.
- NEVER add `.dockitem` files to `~/.config/plank/dock1/launchers/` or modify Plank's `dock-items` GSettings for newly created apps. The bottom dock is strictly reserved for the 6 core system anchors.
