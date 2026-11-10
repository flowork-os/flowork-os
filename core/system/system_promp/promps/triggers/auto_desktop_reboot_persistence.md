# ⚡ DESKTOP & APP CONFIGURATION REBOOT PERSISTENCE MANDATE
When configuring, modifying, or repairing user desktop apps, bookmarks, panels, autostart programs, or system services in Flowork OS, you MUST enforce the **Triple-Lock Persistence Protocol** to prevent configurations from reverting upon PC restart:

1. **Session Script Anchor (`/opt/floworkos/session/flowork-session.sh`):**
   - Inspect and update the boot generator script so login sessions do NOT overwrite user configs with legacy defaults.
   - Ensure canonical symlinks exist in `/opt/floworkos/` for any legacy paths.

2. **System Skeleton Anchor (`/etc/skel/` and `/etc/xdg/`):**
   - Synchronize all `.desktop` autostart files to `/etc/xdg/autostart/` and `/etc/skel/.config/autostart/`.
   - Mirror critical dotfile defaults into `/etc/skel/.config/` so user resets do not erase active configurations.

3. **Systemd Target Anchor (`default.target`):**
   - User services (`~/.config/systemd/user/*.service` & `/etc/systemd/user/*.service`) MUST specify `WantedBy=default.target`.
   - NEVER rely exclusively on `graphical-session.target` as it may fail to trigger under modular X11/XFCE sessions.
   - Enable via `systemctl --user enable <service>` and verify symlink presence in `default.target.wants/`.

**Prohibition:** Never modify `~/.config/` in isolation; changes without the Triple-Lock will be eradicated upon next desktop login.
