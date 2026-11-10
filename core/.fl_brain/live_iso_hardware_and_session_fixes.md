---
title: Live ISO Hardware & Session Sanitization Fixes
date: 2026-11-09
keywords:
  - live_iso
  - volume_applet
  - pulseaudio
  - systray
  - network_manager
  - ntfs_3g
  - udisks2_polkit
  - windows_partitions
  - connector_vault
  - session_logout
---

# Live ISO Hardware, Panel & Session Sanitization Fixes

## Problem Addressed
During Live ISO remastering, four critical defects were identified:
1. Volume control icon and hardware media keys were absent from the panel and desktop session.
2. NetworkManager tray icon (`nm-applet`) was missing and connection autoconnect was unasserted.
3. Windows internal NTFS/exFAT drives (D:, E:, etc.) were hidden in the file manager and prompted for admin passwords when mounting.
4. Flowork Connector was baking active developer credentials (`awenkaudico`) with 7 linked OAuth tokens into the live rootfs instead of a clean logged-out state.

## Root Causes & Solutions Applied
1. **Audio & Volume Control (`xfce4-pulseaudio-plugin`)**:
   - Declared `/plugins/plugin-9` (`pulseaudio`) with `enable-keyboard-shortcuts` and `show-notifications` in Xfconf, `xfce4-panel.xml`, and `flowork-session.sh`.
   - Mapped `XF86AudioRaiseVolume`, `XF86AudioLowerVolume`, `XF86AudioMute`, and `XF86AudioMicMute` directly to `pactl set-sink-volume` and `pactl set-sink-mute` in `xfce4-keyboard-shortcuts.xml`.
2. **Internet & Network Tray (`libsystray.so` + `nm-applet`)**:
   - Declared `/plugins/plugin-8` (`systray`) with `square-icons` in Xfconf, allowing `nm-applet` to dock immediately.
   - Added `/etc/NetworkManager/conf.d/99-flowork-network.conf` enforcing `autoconnect=true` and DNS fallback (`1.1.1.1`, `8.8.8.8`).
3. **Windows Drives (NTFS / exFAT) & Passwordless Mounting**:
   - Installed `ntfs-3g`, `exfat-fuse`, `exfatprogs`, and `cifs-utils`.
   - Created `/etc/polkit-1/rules.d/10-udisks2.rules` allowing active local console users to mount/unmount internal partitions without password popups (`polkit.Result.YES`).
   - Enabled Nemo desktop icons: `volumes-visible=true` and `computer-icon-visible=true`.
   - Created `flowork-computer.desktop` on Desktop and system apps menu (`nemo computer:///`).
4. **Connector Vault Sanitization**:
   - Reset `/opt/floworkos/connector/data/vault.json` to 100% clean logged-out state (`flowork_token: ""`, `flowork_user: null`, `accounts: []`, `is_logged_out: true`, default model `gemini-3.8-flash-high`).
   - Preserved developer workstation backup at `vault.dev.bak` (ignored from git/ISO).
   - Created canonical template `vault.clean.json` enforced at Live boot and ISO build time.
