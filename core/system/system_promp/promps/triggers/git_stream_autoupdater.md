# CONTENT-ADDRESSABLE DELTA OTA & SMART HTTP UPDATER

## 1. Context & Activation Scope
Applies when maintaining `flowork-update`, `flowork-manifest-gen`, `github_update_watch`, `version.json`, systemd update units, or `upload-flowork-os.sh` OTA channels.

## 2. Mandatory Behavioral Invariants
- COMMIT-PINNED CDN FETCH: Resolve live upstream `HEAD` via Git Smart HTTP (`info/refs?service=git-upload-pack`) first to eliminate Fastly CDN skew, then fetch `manifest.json.gz` and delta payloads strictly from `raw.githubusercontent.com/{repo}/{head_sha}/...`.
- ATOMIC & COLLISION-SAFE INSTALL: Verify SHA-256 checksums, stage atomically via sibling temp files and `os.replace` (`ETXTBSY`-safe for active daemons), guard `to_delete` against `remote_file_targets | remote_symlink_targets`, and run AST/binary health checks with directory-symlink-safe rollback.
- SURGICAL RELOAD & OFFLINE DEFERRAL: Derive minimal subsystem restart flags (`derive_sync_flags`) so only modified daemons reload; exit with code 0 gracefully on offline `--auto` timers.
- PASSWORDLESS & DEV-MODE GUARD: Enforce `/etc/sudoers.d/flowork-updater`, polkit rules, and immediate Exit Code 0 inhibition whenever `flowork.dev` exists or `FLOWORK_ENV=dev`.
- HOST-REPO PARITY: Keep `/etc/skel`, `/opt/floworkos`, `/usr/local/bin`, and `upload-flowork-os.sh` aligned; exclude transient runtime files (`.pid`, `.last_alert`, `.state.json`, `foundry_test_result.json`, `test_config.json`).

## 3. Strict Prohibitions
- Never fetch mutable `raw/.../main` URLs when an exact commit SHA is resolved.
- Never overwrite files in `flowork.dev` environments or prompt for passwords on background timers.
- Never restart unrelated daemons or active busy AI turns during background `--auto`.
