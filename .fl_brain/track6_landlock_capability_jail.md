---
id: track6-landlock-capability-jail
title: Per-App Landlock Capability Manifest and Kernel Sandbox Execution
track: 6
keywords:
  - landlock
  - flowork-sandbox-exec
  - capability
  - manifest
  - flowpkg
  - flowork-launch
  - flow-app
  - network-isolation
  - webkit2gtk
  - nvidia-egl
  - security-violation
  - audit-permissions
---

# Track 6: Per-App Landlock Capability Jail

- **Shared Rust Module:** `/opt/floworkos/crates/flowork-core-rs/src/sandbox.rs` implements Linux kernel Landlock FS+Net confinement (`probe_landlock_abi`, `LandlockRulesetAttrV4` supporting TCP/UDP isolation on ABI >= 4/10, and `LandlockRulesetAttrV1` fallback).
- **Wrapper Binary:** `/opt/floworkos/bin/flowork-sandbox-exec` (`--app-id`, `--manifest`, `--profile`, `--detach`, `--sandbox-trace`, `--check`) strips sensitive tokens, blocks hard-deny invariants (`/opt/floworkos/connector/data`, `vault.json`, `~/.ssh`, `~/.gnupg`, `~/.aws`, `~/Downloads/token`, `~/.git-credentials`) via canonical symlink checks, grants subtree/GPU/WebKit2GTK runtime nodes (`/run/udev`, `/dev/dri`, `/dev/nvidia*`, `~/.nv`, `~/.local/share/webkitgtk`), and publishes `security.sandbox.denied` over `/run/flowork/bus.sock` with desktop toast feedback.
- **Wiring & Schemas:** Standardized `"permissions"` blocks added across `/opt/floworkos/apps/*/manifest.json` and `craft-anything/templates/quantum-glass/manifest.json` (`strict` default). `flowpkg run`, `flowpkg build`, `flowpkg audit-permissions`, `flow-app create`, and `flowork-launch` (with automatic `--foreground` forwarding for shell wrappers) enforce kernel confinement.
