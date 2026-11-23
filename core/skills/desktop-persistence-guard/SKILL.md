---
name: desktop-persistence-guard
description: Comprehensive procedural playbook for guaranteeing that desktop applications, systemd services, bookmarks, and autostart configurations persist across reboot in Flowork OS via the Triple-Lock protocol.
domain: os_doctrine
keywords:
  - flowork
  - persistence
  - reboot
  - restart
  - systemd
  - autostart
  - skeleton
  - session
  - desktop
  - bookmarks
  - config
  - services
  - sidebar
  - fallback
  - symlink
  - gtk
  - xdg
  - daemon
  - target
  - immutable
author: Flowork Architecture Board & Dr. Flow
version: 1.0.0
---

# ⚡ Desktop & Application Reboot Persistence Guard

## 1. Objective
Provide a deterministic standard operating procedure for configuring, installing, or modifying desktop user applications, systemd user daemons, panel applets, file manager bookmarks, and autostart entries in Flowork OS such that no configuration reverts, resets, or disappears upon system reboot.

## 2. Prerequisites
1. Sovereign root access (`sudo` or Flowork OS admin session).
2. Physical access to system session controllers:
   - `/opt/floworkos/session/flowork-session.sh`
   - `/etc/skel/` and `/etc/xdg/`
   - `/etc/systemd/user/` and `$HOME/.config/systemd/user/`
3. Zero hardcoded usernames: all paths MUST dynamically resolve `$HOME` or use canonical `/opt/floworkos/` root.

## 3. Standard Operating Procedure

### Lock 1: Anchor the Session Boot Script
Desktop environments in Flowork OS re-execute `/opt/floworkos/session/flowork-session.sh` on every display manager login.
1. Inspect `flowork-session.sh` before editing user dotfiles to ensure no hardcoded legacy overwrite rules exist.
2. If modifying GTK bookmarks (e.g. `~/.config/gtk-3.0/bookmarks`), update the generation logic in `flowork-session.sh` directly.
3. Establish canonical backward-compatibility symlinks under `/opt/floworkos/` if scripts reference legacy directory structures.

### Lock 2: Mirror into System Skeletons (`/etc/skel/` & `/etc/xdg/`)
User sessions in immutable or live ISO configurations regenerate default directories from system skeleton templates.
1. Place system-wide autostart desktop entries in `/etc/xdg/autostart/<app>.desktop`.
2. Mirror all user autostart files to `/etc/skel/.config/autostart/<app>.desktop`.
3. If introducing application settings (e.g. `sidebar_config.json`), ensure a pristine default copy resides in `/etc/skel/.flowork/` or `/etc/skel/.config/`.

### Lock 3: Bind Systemd Services to `default.target`
User background services (such as Mr. Flow Sidebar daemon) frequently fail to resurrect when bound to `graphical-session.target` because modular X11 compositors do not reliably report this target.
1. Edit the service unit file (`/etc/systemd/user/<service>.service` or `~/.config/systemd/user/<service>.service`).
2. Set the install target:
   ```ini
   [Install]
   WantedBy=default.target
   ```
3. Enable and start the service:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable <service>.service
   systemctl --user restart <service>.service
   ```
4. Verify that the unit is linked into `$HOME/.config/systemd/user/default.target.wants/<service>.service`.

## 4. Verification
Execute the following verification commands to ensure Exit Code 0 across all 3 locks:

```bash
# 1. Verify systemd user service status & default.target link
systemctl --user is-enabled <service>.service
test -L "$HOME/.config/systemd/user/default.target.wants/<service>.service"

# 2. Verify XDG autostart symmetry
test -f "/etc/xdg/autostart/<app>.desktop"
test -f "$HOME/.config/autostart/<app>.desktop"

# 3. Verify session script syntax
bash -n /opt/floworkos/session/flowork-session.sh
```

## 5. Failure Modes
1. **Isolated Dotfile Edits:** Editing only `~/.config/` files without updating `/etc/skel/` or `flowork-session.sh` will cause settings to revert on next login.
2. **Graphical Session Hang:** Services bound to `graphical-session.target` remain dormant after reboot. Remediation: immediately re-target unit to `default.target`.
3. **Hardcoded User Paths:** Using `/home/username/` in `.desktop` Exec or systemd Unit files breaks portability across different users or live ISO boots. Remediation: use environment variables or absolute canonical paths (`/opt/floworkos/`).
