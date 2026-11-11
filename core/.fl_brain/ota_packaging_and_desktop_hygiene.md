---
title: OTA Manifest Symlinks, Desktop Validation, and Python Stdlib Protection
date: 2026-11-12
keywords:
  - ota_updater
  - manifest_symlinks
  - desktop_file_validate
  - crlf_script_guard
  - audacity_symlink_loop
  - remix_resolution
  - xdg_document_portal
  - python_stdlib_shadow
  - dist_packages_repair
  - fuse_condition_guard
  - live_iso_preflight
---

# OTA Manifest Symlinks, Desktop Validation, and Python Stdlib Protection

## Root Causes Addressed (`BUG-01`..`BUG-08` & OTA Pipeline)
1. **CRLF Runner Script (`BUG-01`)**: `/opt/floworkos/apps/craft-anything/bin/craft-anything` had CRLF line endings causing `bash\r` launch failures, and `upload-flowork-os.sh` omitted syncing it into `/opt/flowork-os-repo/core/apps/craft-anything/bin/craft-anything`. Converted to LF, chmod `0755`, synced in `upload-flowork-os.sh`, and added CRLF pre-flight guard in `build-live-iso.sh` & `flowork-update`.
2. **Self-Loop Symlink & App Permissions (`BUG-02`)**: `/opt/floworkos/apps/audacity/runtime/usr -> .` caused `ELOOP` (`Errno 40`), and `audacity/runtime` + `recordly/squashfs-root` had `0700` blocking live user `flowork`. Removed loop symlink, applied `a+rX` (preserving suid `chrome-sandbox`), and added runtime permission repair inside `flowork-update` and `build-live-iso.sh check`.
3. **XDG Desktop & Remix Failures (`BUG-03`, `BUG-05`)**: Unregistered categories (`Flowork`, `Design`), empty `;`/`;;` tokens, and stray `Actions=Remix;` under `[Desktop Action ...]` failed `desktop-file-validate`. Normalized to `X-Flowork;`/`X-Design;`, updated `flow-app` + `flowpkg` + `flowork-launch`, added `REMIX_APP_ALIASES`, `SOVEREIGN_REMIX_COMPONENTS`, and XDG `.desktop` / `PATH` resolution so all dock/launchpad apps remix cleanly.
4. **Skills Path Drift & Portal Crash (`BUG-04`, `BUG-07`)**: Updated `promps/triggers/skills.md` + `triggers.json` to `/opt/floworkos/skills` (13 skills), and guarded `xdg-document-portal.service` with `[Unit]\nConditionPathExists=/dev/fuse` in `/etc/systemd/user/` and `/etc/skel/.config/systemd/user/` while kernel lacks `CONFIG_FUSE_FS`.
5. **Python Stdlib Shadowing & Dist-Packages (`BUG-08`)**: Purged custom `tokenize.py`/`token.py` under `/opt/floworkos/mcp/earshot` and `/opt/floworkos/lib/python3` plus `sys.path.insert` in `mrflow-sidebar.py`, and reinstalled 12 Ubuntu Python packages (`python3-yaml`, `python3-certifi`, `python3-packaging`, `python3-pygments`, `python3-pip`, `python3-setuptools`, etc.) damaged by prior `*token*`/`*.pem` sweeps.
6. **OTA Manifest & Symlink Gaps**: Fixed `flowork-manifest-gen` exact path component exclusions (`EXCLUDE_DIR_NAMES` instead of substring match so `default.target.wants` isn't skipped, and `ROOT_EXCLUDE_RELPATHS` so 88 sub-manifests stay indexed), added `symlinks` delta syncing + `apply_post_update_os_sync()` in `flowork-update` (never restarting sidebar while UNIX socket `is_busy: true`).
