# PER-APP KERNEL LANDLOCK CAPABILITY JAIL

## 1. Context & Activation Scope
Activate when creating, packaging, auditing, or modifying `/opt/floworkos/bin/flowork-sandbox-exec`, `crates/flowork-core-rs/src/sandbox.rs`, `flowpkg`, `flowork-launch`, `flow-app`, or application `manifest.json` `"permissions"` capability blocks.

## 2. Mandatory Behavioral Invariants
- Enforce kernel Landlock FS+Net confinement (`LandlockRulesetAttrV4` on ABI `>= 4`) via `/opt/floworkos/bin/flowork-sandbox-exec`; keep newly synthesized apps defaulting to `profile = "strict"` and `allow_network = false`.
- Resolve and pass `--foreground` in `flowork-launch` when wrapping shell launchers under `flowork-sandbox-exec --detach` so health probes track the foreground GUI PID.
- Preserve WebKit2GTK + NVIDIA EGL runtime allowances (`/run/udev`, `/dev/dri`, `/dev/nvidia*`, `~/.nv`, `~/.local/share/webkitgtk`) and canonicalize declared paths before adding rules.
- Validate permission changes with `flowpkg audit-permissions --strict`, `flowork-sandbox-exec --check`, and `flowpkg run <app> --check-health`.

## 3. Strict Prohibitions
- Never grant `/opt`, `/opt/floworkos`, or `$HOME` roots wholesale, and never permit `vault.json`, `/opt/floworkos/connector/data`, `~/.ssh`, `~/.gnupg`, or `~/.aws` in allowlists.
- Never replace `/opt/floworkos/bin/flowpkg` with a non-Python script (preserves `qc_evolution_suite.py` AST integrity checks).
