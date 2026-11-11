---
title: Smart HTTP Commit-Pinned Delta OTA, Surgical Reloads, and Host-Repo Parity
date: 2026-11-12
keywords:
  - smart_http_head_resolution
  - commit_pinned_cdn
  - fastly_cache_skew_fix
  - delta_ota_convergence
  - surgical_daemon_restart
  - to_delete_collision_guard
  - dir_symlink_rollback
  - offline_auto_graceful_exit
  - etxtbsy_atomic_replace
  - host_repo_parity
  - runtime_artifact_exclusion
  - flowork_update
  - flowork_manifest_gen
  - networkmanager_dispatcher
  - github_update_watch
---

# Smart HTTP Commit-Pinned Delta OTA, Surgical Reloads, and Host-Repo Parity

## 1. Root Causes Resolved
1. **Fastly Raw CDN Cache Skew (up to 5 minutes post-push):**
   - Fetching `raw.githubusercontent.com/{repo}/main/manifest.json.gz` returned stale cached manifests immediately after `git push`, while `watcher.py` used uncached branch API / fallback and risked mismatched commit states.
2. **Unsafe Rollback, Target Collision & Over-Broad Restarts:**
   - Old `to_delete` logic checked only `remote_symlink_targets`, risking deletion if a repo key relocated to another key sharing the same OS `target` (`remote_file_targets`).
   - Rollback `shutil.rmtree` vs `os.unlink` treated symlinks-to-directories improperly when checking `os.path.isdir(p)` without `os.path.islink(p)`.
   - Background `--auto` reloaded all user units unconditionally even when unrelated files changed.
3. **Host-vs-Repo Parity Drift & Transient File Churn:**
   - Old `upload-flowork-os.sh` omitted `/etc/skel` theme/config files, swapped outdated Big Sur wallpaper & `.face`, tracked live `.pid`/`.last_alert`/`test_config.json`/`foundry_test_result.json`, left dangling `core/bin/flowork-iso-master -> ../../iso-builder/build-live-iso.sh`, and copied `ubersuggest`/`flowork-screenshot` instead of preserving canonical symlinks.

## 2. Definitive Architectural Fixes
1. **Git Smart HTTP HEAD + Commit-Pinned Raw CDN:**
   - Both `flowork-update` and `watcher.py` resolve live `refs/heads/{branch}` via `https://github.com/{repo}.git/info/refs?service=git-upload-pack` (Git Smart HTTP pkt-line parser — zero Fastly skew, zero GitHub REST quota) with REST API fallback.
   - `manifest.json.gz` and all changed payloads download strictly from `https://raw.githubusercontent.com/{repo}/{head_sha}/...`, eliminating stale branch CDN reads.
   - `flowork-update --json`, `--repair`, and `--auto` (offline exits 0 gracefully) support `--root` sandbox testing, self-update re-exec forwarding `--sync-flags`, and immediate sidebar/trigger clearance via `_clear_github_trigger_and_badge`.
2. **Atomic, Collision-Safe & Surgical Post-Sync:**
   - `compute_delta` protects `abs_t` in `to_delete` when `abs_t in remote_file_targets or abs_t in remote_symlink_targets`.
   - Rollback unlinks symlinks cleanly via `(os.path.islink(p) or not os.path.isdir(p))`.
   - `derive_sync_flags(updated_rel_paths, symlinks_rel_paths)` restricts systemd/daemon reloads strictly to subsystems whose files changed (`tray`, `sidebar`, `triggers`, `edits`, `bus`, `systemd_sys`, `updater_timer`, `systemd_user`, `desktop`), while `/etc/NetworkManager/dispatcher.d/99-flowork-updater` and `flowork-updater.timer` trigger rate-limited online checks automatically.
3. **Host-Repo Parity & Transient Exclusion Hygiene:**
   - `flowork-manifest-gen` excludes `.last_alert`, `.state.json`, `foundry_test_result.json`, `test_config.json` alongside `*.pid`; `upload-flowork-os.sh` untracks them (`git rm --cached`), adds them to `.gitignore`, syncs full `/etc/skel` + boot-skeleton configs + `flowork-profile/bin/app.py`, preserves valid symlinks (`flowork-iso-master`, `prompts`, `ubersuggest`, `flowork-screenshot`), and purges legacy `flowork-autoupdate.*` / `core/nyquist-plug-ins`.
