# CONTENT-ADDRESSABLE DELTA OTA UPDATER & PASSWORDLESS GUARD

## 1. Context & Scope
Applies when maintaining `flowork-update`, `flowork-manifest-gen`, version metadata (`version.json`), systemd timers, or OTA deployment channels.

## 2. Mandatory Invariants
- CRYPTOGRAPHIC DELTA OTA: Download only `manifest.json.gz` (~1.2 MB). Compute in-memory SHA-256 diffs across system files. Download only modified/added files from raw GitHub CDN. Never clone or pull the full multi-gigabyte git repository.
- PASSWORDLESS BYPASS: Enforce `ALL ALL=(ALL) NOPASSWD: /opt/floworkos/bin/flowork-update` in `/etc/sudoers.d/flowork-updater` and polkit rule in `/etc/polkit-1/rules.d/99-flowork-updater.rules`. Even if user configures a password, background and manual updates must bypass prompts and execute cleanly.
- DEVELOPER MODE EXCLUSION: If landmark `flowork.dev` (`/opt/floworkos/flowork.dev`, `/etc/flowork.dev`, `~/flowork.dev`) exists or `FLOWORK_ENV=dev`, auto-update is strictly inhibited. Both systemd unit conditions (`ConditionPathExists=!/opt/floworkos/flowork.dev`) and script fast-path must immediately exit with code 0.
- ATOMIC THREE-TIER SYNC: Core `/opt/floworkos`, system `/usr/local/bin` & `/etc/systemd`, user skeleton `/etc/skel`. Never clobber existing user data in `$HOME`.
- POST-UPDATE HEALTH CHECK: Validate syntax and core binaries (`mrflow`, `flowork-profile`, dock scripts) before finalizing. Roll back immediately from backup if health checks fail.
- SINGLE-BUILD REPRODUCIBILITY: The ISO is built once. All subsequent system improvements, bugfixes, and packages flow via delta OTA updates.

## 3. Strict Prohibitions
- Never execute automated sync or overwrite files when `flowork.dev` is present.
- Never prompt the user for a password during background or scheduled updates.
- Never download full git trees for rolling updates.
