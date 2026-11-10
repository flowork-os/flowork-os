---
title: Mr. Flow Header Companion Tray Applet Persistence and OTA Activation
description: Architectural documentation on resolving the missing Mr. Flow header tray icon on newly installed systems, integrating display handshakes, single-instance file locks, systemd user defaults, and automated OTA activation.
keywords:
  - mrflow_tray_applet
  - desktop_header_indicator
  - xfce4_panel_systray
  - systemd_user_services
  - xdg_autostart_integration
  - display_handshake_wait
  - single_instance_file_lock
  - flowork_update_ota
  - delta_manifest_synchronization
  - sovereign_companion_icon
---

# Mr. Flow Header Companion Tray Applet Persistence & OTA Activation

## 1. Issue Overview
On systems freshly installed from the Live ISO, the Mr. Flow companion button in the desktop header panel (systray, next to the Sovereign Connector) failed to appear.

## 2. Root Cause Analysis
1. **Missing System-Wide User Unit**: `flowork-mrflow-tray-applet.service` was initially deployed in developer home `~/.config/systemd/user/` with a hardcoded user path and was never linked in `/etc/systemd/user/default.target.wants/` nor in `/etc/skel/.config/systemd/user/default.target.wants/`.
2. **Missing XDG Autostart Backup**: There was no `.desktop` launcher in `/etc/xdg/autostart/` for non-systemd desktop session fallbacks.
3. **Display Race Condition**: The applet lacked a wait loop for X11/XFCE4 panel availability, leading to premature exit when launched during early graphical target initialization.

## 3. Engineering Remediation
1. **Hardened Applet Core (`mrflow-tray-applet.py`)**:
   - Added `wait_for_display_and_panel()` to poll X11 and `xfce4-panel` availability before binding `Gtk.StatusIcon`.
   - Added non-blocking kernel file lock via `fcntl.flock` to guarantee single-instance execution.
2. **System-Wide Multi-Session Deployment**:
   - Deployed unit to `/etc/systemd/user/flowork-mrflow-tray-applet.service`.
   - Linked to `/etc/systemd/user/default.target.wants/flowork-mrflow-tray-applet.service`.
   - Mirrored into `/etc/skel/.config/systemd/user/` for newly created installer accounts.
   - Installed `/etc/xdg/autostart/mrflow-tray-applet.desktop`.
   - Created `/usr/local/bin/mrflow-tray-applet` executable wrapper.
3. **Auto-Updater Integration (`flowork-update`)**:
   - Updated path mappings in `flowork-manifest-gen` for `system/autostart/` and `system/systemd-user/`.
   - Injected automatic user-session reload hook into `flowork-update` to immediately start and link the service across all active user sessions post-OTA update.
