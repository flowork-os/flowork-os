---
title: Track 1 Root Cargo Workspace Unification, Systemd Hygiene & Glass HUD Parity
category: architecture
keywords:
  - cargo_workspace
  - rust_toolchain
  - flowork_connector
  - systemd_hygiene
  - glass_hud_spec
  - alacritty_toml
  - mrflow_tray_flock
  - live_iso_pseudo_files
  - spotlight_rasi
  - zero_drift_track1
date: 2026-11-12
---

# Track 1: Root Cargo Workspace, Systemd Hygiene & Glass HUD Parity

## 1. Root Cargo Workspace & Toolchain Pinning
- Created unified `/opt/floworkos/Cargo.toml` (`resolver = "2"`, unified `[profile.release]`) spanning `crates/flowork-core-rs`, `mrflow-rs`, `connector-rs`, `sysd`, and `wm` while explicitly excluding `apps/cutvii/src-tauri` (Tauri GUI build).
- Pinned toolchain via `/opt/floworkos/rust-toolchain.toml` (`1.99.1`) installed under `$HOME/.cargo` and `$HOME/.rustup`; non-interactive bash shells require `export PATH="$HOME/.cargo/bin:$PATH"`.
- Added early CLI flag handling (`--help`, `--version`, `--check`) in `/opt/floworkos/connector-rs/src/main.rs` prior to TCP `:9099` bind and exposed canonical symlink `/opt/floworkos/bin/flowork-connector -> /opt/floworkos/connector/bin/flowork-connector`.

## 2. Systemd & Single-Instance Tray Hygiene
- Eliminated dead legacy units (`flowork-core.service`, `flowork-visiond.service`, `flowork-window-manager.service`) from user units, kernel setup scripts, OTA updater, ISO SquashFS excludes, and GitHub staging sync. Keep `flowork-wm.service` (`xfwm4`) intact.
- Created canonical `/opt/floworkos/system/systemd/{mrflow-tray,flowork-sysd}.service` (`Restart=on-failure` on `mrflow-tray.service`, `WorkingDirectory=/opt/floworkos` on `flowork-sysd.service`), injected via `$PSEUDO_FILE` in `build-live-iso.sh` and synced in `upload-flowork-os.sh`.
- Protected both `/opt/floworkos/connector/bin/mrflow-tray-menu.py` and `/opt/floworkos/apps/connector/bin/mrflow-tray-menu.py` with non-blocking `fcntl.flock` (`/tmp/mrflow-router-tray-{user}.lock`) to prevent dual tray icons alongside XDG autostart.

## 3. Glass HUD & Dead Asset Cleanup
- Aligned `EOF_ALACRITTY` in `/opt/floworkos/session/flowork-session.sh` with `/opt/floworkos/system/glass_hud_spec.md` (`opacity = 0.60`, `#000000`, `JetBrains Mono` Bold `12.0`, `transparent_background_colors = true`) and removed dead `x-flow` / `flowork-window-daemon` launch blocks.
- Removed unreferenced `theme/launchpad.rasi` and `theme/flowork-launchpad.py`; retained `theme/spotlight.rasi` because `/usr/local/bin/flowork-power-menu` actively invokes `rofi -dmenu -theme /opt/floworkos/theme/spotlight.rasi`.
- Hardened `/opt/floworkos/iso-builder/build-live-iso.sh` polkit check (`EUID` / readable / `sudo -n`) so unprivileged `check` and `dry-run` execute without blocking on a `sudo` password prompt.
