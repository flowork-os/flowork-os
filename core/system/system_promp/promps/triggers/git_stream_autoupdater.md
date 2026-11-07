# GIT-STREAM AUTO-UPDATER AND ROLLBACK GUARD

## 1. Context & Scope
Applies when maintaining `flowork-update`, version metadata (`version.json`), systemd update timers, or OTA deployment channels.

## 2. Mandatory Invariants
- ATOMIC THREE-TIER SYNC:
  - Layer 1 (Core `/opt/floworkos`): Synchronize assets, prompts, skills, and tools atomically.
  - Layer 2 (System `/usr/local/bin`, `/etc/systemd`): Update binaries, reload daemon (`systemctl daemon-reload`), and restart user services (`flowork-mrflow-sidebar`).
  - Layer 3 (User Skeleton `/etc/skel`): Update default skeletons. Never clobber user data or private configurations in `$HOME`.
- SUB-MILLISECOND REMOTE QUERY: Use `git ls-remote` on remote HEAD. Do not download full git history for version checks.
- ANTI-BRICK HEALTH CHECK: Create a backup snapshot before syncing. Validate Python syntax and binary execution before finalizing. If validation fails, immediately rollback to snapshot.
- VERSION CONSISTENCY: Maintain `commit`, `version`, and ISO-8601 UTC timestamp in `/opt/floworkos/system/version.json`.
- SILENT SYSTEMD TIMER: `flowork-updater.timer` runs background checks every 2 to 4 hours with `--silent` flag and idle CPU priority.
- USER NOTIFICATION: Emit desktop alerts upon successful updates via `notify-send`.
- DEV MODE INHIBITION: If landmark file `flowork.dev` (`/opt/floworkos/flowork.dev`) exists or `FLOWORK_ENV=dev` is present, auto-update is immediately inhibited. Systemd service conditions (`ConditionPathExists=!/opt/floworkos/flowork.dev`) skip execution. Zero overwrites allowed in development mode.

## 3. Strict Prohibitions
- Never execute automated sync or overwrite system files when `flowork.dev` or dev environment is active.
- Never overwrite user files in `$HOME` during system updates.
- Never finalize an update without running post-sync health checks.
- Never hardcode personal user paths in updater scripts.
