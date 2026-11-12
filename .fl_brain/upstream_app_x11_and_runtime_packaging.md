---
title: Upstream Electron AppImage X11 Capture & PyInstaller App Integration
date: 2026-11-12
keywords:
  - upstream_appimage
  - electron_asar
  - openscreen_x11
  - gputaskman_nvml
  - display_flag_collision
  - pipewire_x11_helper
  - zero_node_scratch
  - neural_bus_adapter
  - github_size_limit
  - squashfs_pseudofile
  - license_vault_archive
  - startup_wmclass
---

# Upstream Electron AppImage X11 Capture & PyInstaller App Integration

## Summary of Solutions Integrated (`gputaskman` v0.4.0 & `openscreen` v2.2.2)
1. **Electron AppImage Unpacking & Zero-Duplicate Storage**: Extracted `OpenScreen-Linux-x86_64.AppImage` into `/opt/floworkos/apps/openscreen/squashfs-root/` and purged the `.AppImage` binary (`827M` vs `1GB+`), preserving `4755 root:root` on `chrome-sandbox` and setting `a+rX` across runtimes for live user `flowork`.
2. **X11 MIT-SHM Capture & GTK `--display` Collision Fix**: `openscreen` v2.2.2 lacked upstream X11 capture (`bc11fc4`) and passing `--display 0` caused Chromium/GTK to abort (exit `133`) before JS could call `app.commandLine.removeSwitch("display")`. Compiled `openscreen-pipewire-helper` in Rust (`~/.cargo/bin/cargo` + `LIBCLANG_PATH=/usr/lib/llvm-18/lib` + BtbN FFmpeg n8.1.2 LGPL-shared SDK), patched `electron/cli/args.ts` to read `OPENSCREEN_DISPLAY_INDEX`, rebuilt `app.asar` (`@electron/asar`) and `THIRD-PARTY-LICENSES.txt` via an ephemeral scratch Node.js toolchain, then deleted scratch to maintain Zero-Node OS. Mapped `record --display <n>` in `/opt/floworkos/bin/openscreen` while keeping `DISPLAY=:0` intact.
3. **Alacritty Geometry & Exact `StartupWMClass` Matching**: Wrapped Textual TUI `gputaskman` (`--window`) in Alacritty (`--class "gputaskman,gputaskman"`, `148x42`) and verified actual X11 `WM_CLASS` (`wmctrl -lx` -> lowercase `openscreen.openscreen`) to guarantee dock/panel grouping and zero duplicate menu categories (`desktop-file-validate` 0 errors/hints).
4. **Neural Bus NDJSON-to-JSON Bridge**: Wrapped `openscreen-cli` (collapsing NDJSON stream events to a single JSON envelope with `file`/`output`/`project`/`--output` alias) and `gputaskman-cli` (`snapshot`/`list-gpus`/`diff`/`record`) so `/opt/floworkos/bin/flowork-pipe` pipelines execute seamlessly.
5. **Repo Size Guard (`<50MB`) & Live ISO Parity**: Excluded heavy `runtime/` & `squashfs-root/` binaries from `~/flowork-os-repo` via `.gitignore` and `upload-flowork-os.sh` sync blocks while archiving verbatim/gzipped notices in `licenses/`, mirroring symlinks in `system/bin/`, and injecting `/usr/local/bin/*` + `/usr/share/applications/*.desktop` in `build-live-iso.sh` pseudo-files.
