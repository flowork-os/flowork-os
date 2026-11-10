---
title: Content-Addressable Cryptographic Delta OTA Updater and Passwordless Bypass
category: architecture
keywords:
  - delta_ota_updater
  - content_addressable
  - cryptographic_manifest
  - sha256_signatures
  - manifest_generator
  - passwordless_bypass
  - sudoers_nopasswd
  - polkit_rules
  - developer_mode_exclusion
  - flowork_dev_landmark
  - atomic_staging
  - rollback_guard
  - post_update_health_check
  - single_build_iso
  - raw_github_cdn
  - bandwidth_optimization
  - zero_hardcoded_paths
  - systemd_timer
  - white_label
  - empirical_verification
---
# Content-Addressable Cryptographic Delta OTA Updater and Passwordless Bypass

## 1. Problem Statements & Root Causes
1. **Multi-Gigabyte Git Clone in Auto-Update:**
   - *Symptom:* The previous updater attempted `git clone` or full git pulls of the entire 3.5+ GB repository on user machines, exhausting bandwidth and failing on slow connections.
   - *Root Cause:* Absence of a Content-Addressable Delta layer. Entire git histories and large binary blobs were fetched instead of targeted changed files.
2. **Password Prompts Blocking Background & Non-Interactive Updates:**
   - *Symptom:* If an end user installed Flowork OS and set an account password, background update timers and GUI update actions prompted for sudo passwords, causing updates to fail or hang indefinitely.
   - *Root Cause:* Sudoers lacked `NOPASSWD:` authorization for `flowork-update`, and `flowork-update` lacked automated, passwordless privilege escalation and Polkit service triggers.
3. **Overwriting Developer Environments:**
   - *Symptom:* Developers editing Flowork OS code locally risked having their in-progress files overwritten by automated update cycles.
   - *Root Cause:* Lack of strict developer landmark file checks (`flowork.dev`) across both systemd units and application runners.

## 2. Definitive Architectural Solutions
1. **Cryptographic Manifest Generator (`flowork-manifest-gen`):**
   - Scans system trees (`core`, `skel`, `system`, `iso-builder`), ignores files > 50MB and volatile dirs (`.git`, `node_modules`, `venv`, `user_data`), and computes SHA-256 signatures and octal file modes in sub-4 seconds.
   - Computes a deterministic Merkle `manifest_id` across all signatures.
   - Emits uncompressed `manifest.json` and gzip-compressed `manifest.json.gz` (~1.2 MB).
2. **Content-Addressable Delta OTA Updater (`flowork-update`):**
   - Fetches only `manifest.json.gz` from GitHub raw CDN.
   - Fast-path verification: If `remote_manifest["manifest_id"] == local_manifest["manifest_id"]`, exits in <50ms with code 0.
   - Computes file-by-file delta diff in <10ms, downloading ONLY modified or new files directly from GitHub CDN.
   - Verifies SHA-256 signatures prior to atomic application into `/opt/floworkos`, `/etc/skel`, `/usr/local/bin`, and `/etc/systemd/system`.
   - Runs post-update health checks (`mrflow`, `flowork-profile`, dock syntax) and provides automated rollback from `/tmp` backups on failure.
3. **Passwordless Escalation & Polkit Bypass:**
   - Added `/etc/sudoers.d/flowork-updater` specifying `ALL ALL=(ALL) NOPASSWD: /opt/floworkos/bin/flowork-update, /opt/floworkos/bin/flowork-manifest-gen`.
   - Added Polkit rule `/etc/polkit-1/rules.d/99-flowork-updater.rules` allowing passwordless control of `flowork-updater.service`.
   - In `flowork-update`: If `os.geteuid() != 0`, cleanly self-escalates via `sudo -n /opt/floworkos/bin/flowork-update` with zero password prompt.
4. **Developer Mode Protection (`flowork.dev`):**
   - Systemd unit `/etc/systemd/system/flowork-updater.service` enforces `ConditionPathExists=!/opt/floworkos/flowork.dev`.
   - `flowork-update` checks `DEV_LANDMARKS` (`/opt/floworkos/flowork.dev`, `/etc/flowork.dev`, `~/flowork.dev`) and immediately halts with Exit Code 0 unless `--force` is passed.
5. **Universal ISO Single-Build Doctrine:**
   - The Flowork OS ISO is built once. All subsequent improvements, craft applications, and system patches stream exclusively through Delta OTA.
