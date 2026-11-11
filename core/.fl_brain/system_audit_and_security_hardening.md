---
title: Flowork OS Security Hardening & Bug Remediation
date: 2026-11-11
keywords:
  - security_hardening
  - vault_permissions
  - umask_override
  - flowpkg_deduplication
  - webextension_filter
  - gecko_stale_lock
  - r8169_firmware
  - zstd_decompression
  - systemd_timer_unit
  - tool_foundry_chmod
  - zero_node_audit
---

# Flowork OS Security Hardening & Bug Remediation

## True Root Causes Fixed
1. **Vault Permissions (`0664` -> `0600`)**: `VaultManager::save_vault_unlocked()` in `/opt/floworkos/connector-rs/src/vault.rs` used `fs::write` inheriting default umask. Hardened temp file creation via `OpenOptionsExt::mode(0o600)` + `fs::set_permissions` on load/save, enforced `0600` in `/opt/floworkos/session/flowork-session.sh` (`chmod 600`), and updated `/opt/floworkos/iso-builder/build-live-iso.sh` pseudo-file (`f 600 1000 1000`).
2. **App Registry Contamination & Symlink Duplicates**: `list_packages()`/`run_package()` in `/opt/floworkos/bin/flowpkg` and `list_apps()` in `/opt/floworkos/bin/flow-app` now exclude unpacked browser extensions (`manifest_version` without `app.json`) and deduplicate by `os.path.realpath()` (real directories prioritized); orphan `/opt/floworkos/apps/crypto-radarflow` symlink was purged.
3. **Stealth Stale Gecko Locks**: Added `cleanup_stale_gecko_locks()` in `/opt/floworkos/apps/flowork-stealth/bin/stealth_runner.py` inspecting symlink `+PID`, `/proc/{pid}`, and POSIX `flock`/`lockf` before unlinking stale `lock`/`.parentlock`.
4. **Realtek `r8169` Missing Firmware**: Kernel lacks `CONFIG_FW_LOADER_COMPRESS`, preventing `.fw.zst` loading. Decompressed `/lib/firmware/rtl_nic/rtl8168h-2.fw.zst` -> `/lib/firmware/rtl_nic/rtl8168h-2.fw` preserving `.fw.zst`.
5. **Systemd Timer & Foundry Script Modes**: Removed invalid `[Unit]` `Persistent=true` in `/etc/systemd/system/flowork-adshield-update.timer`; enforced `755` on `/opt/floworkos/tools/tool_foundry/run.py` and in `upload-flowork-os.sh`; registered `anti_zombie.md`, `sovereign_branding_invariants.md`, and `system_audit_hardening.md` in `promps/triggers.json`; removed orphan `~/.npm`.

## False Positives Preserved Intentionally
- Zero-Node Pure Rust architecture (no Node/npm restoration), `02_operational_guidelines.md` `@lock`, `GNOME Shell` CSS files (distinct from GTK3), and `CutVii` `OWNER/REPO` placeholder guard (`UpdateStatus::Placeholder`).
- Kernel config items (`CONFIG_FUSE_FS`, built-in `CONFIG_INTEL_MEI_ME=y`) require a future kernel rebuild.
