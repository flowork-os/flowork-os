---
title: Desktop Reboot Persistence, Dock Centering Offset, and Anti-Leak Vault Ignorance
category: architecture
keywords:
  - reboot_persistence
  - session_runner
  - xfce4_panel
  - whiskermenu
  - command_profile
  - mugshot_spawner
  - plank_dock
  - center_alignment
  - responsive_dock
  - zero_offset
  - vault_exclusion
  - episodic_memory
  - remote_sync
  - landlock_security
  - triple_lock
  - systemd_path
  - gitignore_anti_leak
  - white_label
  - empirical_verification
  - sovereign_desktop
---
# Desktop Reboot Persistence, Dock Centering Offset, and Anti-Leak Vault Ignorance

## 1. Problem Statements & Root Causes
1. **Whisker Menu Profile Mugshot Error on Restart:**
   - *Symptom:* Clicking the profile button in Whisker Menu displayed `Failed to edit profile. Failed to execute child process "mugshot" (No such file or directory)`.
   - *Root Cause:* `/opt/floworkos/session/flowork-session.sh` executed on startup and generated `~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml` and `~/.config/xfce4/panel/whiskermenu-1.rc` via hardcoded heredocs missing `command-profile` and `show-command-profile`. Additionally, `flowork-panel.service` systemd unit lacked `/opt/floworkos/bin` and `%h/.local/bin` in its PATH environment.
2. **Plank Bottom Dock Not Centering:**
   - *Symptom:* Plank task dock shifted far to the right and expanded unevenly when apps were opened.
   - *Root Cause:* `/opt/floworkos/theme/flowork-dock-responsive.py` attempted to adjust Plank's `offset` based on `_NET_WORKAREA` width (subtracting the 762px Companion sidebar strut). Setting `offset = 21%` pushed Plank's full-screen 2560px window 537px to the right instead of centering it.
3. **Connector Remote Logout upon Pull/Update:**
   - *Symptom:* If dummy `vault.json` or `episodic_memory.db` were tracked or committed to GitHub, pulling or cloning updates on a secondary PC wiped active session credentials and logged the user out.

## 2. Definitive Architectural Fixes
1. **Triple-Lock Reboot Persistence (`flowork-session.sh` & systemd):**
   - In both `/opt/floworkos/session/flowork-session.sh` and repo `core/session/flowork-session.sh`, explicitly added:
     - `command-profile=/opt/floworkos/bin/flowork-profile`
     - `show-command-profile=true`
     - `systemctl --user import-environment PATH DISPLAY XDG_CURRENT_DESKTOP FLOWORK_OS_ROOT`
     - Symlink fallbacks for `mugshot` pointing to `/opt/floworkos/bin/flowork-profile`.
   - In `flowork-panel.service` (user config and skel), injected:
     `Environment=PATH=/opt/floworkos/bin:%h/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
2. **Plank Dock Physical Center Invariant (Zero Offset):**
   - Plank window natively spans full physical display geometry and centers items with `alignment='center'` and `items-alignment='center'`.
   - Removed offset percentage calculations from `calculate_responsive_dock_geometry()` in `/opt/floworkos/theme/flowork-dock-responsive.py` and locked `offset = 0`.
3. **Permanent Vault & Session Exclusion:**
   - Added explicit patterns to `.gitignore` preventing `vault.json` and `episodic_memory.db` from being tracked.
   - Executed `git rm --cached` and removed local repo disk copies to prevent dummy overwrites across PC clusters.
