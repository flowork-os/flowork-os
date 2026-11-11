# 👑 PASSIVE TRIGGER: APP-ON-DEMAND JIT SOFTWARE SYNTHESIS

## 1. Context & Activation Scope
Triggered when the user asks to synthesize, generate, or build a bespoke desktop application or utility (`bikinin app`, `buatkan aplikasi`, `synthesize application`, `create desktop tool`, `flow-app`, `craft-app`).

## 2. Mandatory Behavioral Invariants
- **ZERO INSTALLER HUNTING:** Never tell the user to install external deb/rpm/flatpak packages when a sovereign `*flow` app can be synthesized directly via `flow-app`.
- **SOVEREIGN '*flow' SUFFIX:** App IDs MUST end with `flow` (e.g., `notesflow`, `diskflow`, `monitorflow`, `termflow`); `flow-app` enforces this suffix.
- **SOVEREIGN 4-STEP PIPELINE:**
  1. **Scaffold:** `/opt/floworkos/bin/flow-app create <app_id> --name "<Name>" --desc "<Description>" --icon "<Emoji>" --category "<Category>"`.
  2. **Implement:** Update `/opt/floworkos/apps/<app_id>/ui/index.html` (Quantum Glass UI) and optional `/opt/floworkos/apps/<app_id>/bin/backend.py`.
  3. **Verify:** Run `/opt/floworkos/bin/flow-app test <app_id>` and achieve **Exit Code 0**.
  4. **Register & Launch:** Run `flow-app register <app_id>` then `flow-app launch <app_id>`.
- **CLEAN REGISTRATION:** Register only in `/usr/share/applications/` and Flowork Launchpad; never pin new apps to Plank dock.
- **QUANTUM GLASS STYLE:** Enforce `0.60` opacity, `0.40` backdrop blur, `#000000` obsidian base, JetBrains Mono Bold, `#00ff66` / `#00f2fe` accents.

## 3. Strict Prohibitions
- NEVER leave apps unverified (`flow-app test <app_id>` MUST return Exit Code 0).
- NEVER hardcode personal `/home/<username>` paths; store apps in `/opt/floworkos/apps/<app_id>`.
- NEVER add `.dockitem` entries to `~/.config/plank/dock1/launchers/` or alter Plank's `dock-items`; keep the 6 core dock anchors untouched.
