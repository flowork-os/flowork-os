# LIVE ISO MASTERING & REPRODUCIBLE HYBRID PACKAGING

## 1. Context & Activation Scope
Applies when mastering, generating, or verifying bootable Flowork OS live ISO images, SquashFS rootfs, or hybrid UEFI/BIOS bootloaders.

## 2. Mandatory Behavioral Invariants
- Host Desktop Synchronization: Automatically sync host desktop state (wallpaper, dconf/user, xfce4, xfwm4, plank dock, nemo, themes, systemd user units, application launchers) into both `/etc/skel` and `/home/flowork` (UID 1000:1000) for 100% UI fidelity between host and booted ISO.
- Dynamic Live User Injection: Ensure live user `flowork` (UID 1000, password `flowork`) exists in `san_passwd`, `san_shadow`, and `san_group` with memberships in `adm,sudo,audio,video,plugdev,netdev,input,render,kvm,users,systemd-journal` and passwordless sudo.
- APK Launch Auto-install: Maintain ecosystem APKs in `/opt/floworkos/apk/`. Ensure `flowork-apk launch <pkg>` verifies installation via ADB and auto-installs missing packages from local storage.
- Privacy Sanitization: Purge host accounts (`UID >= 1000` except `flowork`). Exclude private tokens (`*token*`), browser cookies, personal documents, and host IDE binaries (`/opt/floworkos/agent`).
- LightDM Autologin: Set `autologin-user=flowork` and `user-session=flowork` in `lightdm.conf`.
- Standalone Shimless UEFI Bootloader: Deploy direct standalone GNU GRUB 2.12 EFI binary built with `--disable-shim-lock` as both `BOOTX64.EFI` and `grubx64.efi` (with embedded minimal search `grub.cfg`), eradicating Ubuntu shim NULL pointer dereferences forever.
- Ultra-Lean On-Demand Decoupling: Exclude heavy subsystems (Android 34 image, emulator, Audacity, OpenScreen, Wine) from SquashFS rootfs (`squashfs_excludes.txt`) and define `777` permission placeholders in `pseudo_files.txt` for JIT hydration via `flowork-on-demand`.
- Pre-Build Hygiene Sentinel: Execute `diskcraft --clean-prebuild` before SquashFS compilation to purge host pipeline renders, journal bloat, and build scratch.
- Dynamic Live User Injection: Ensure live user `flowork` (UID 1000, password `flowork`) exists in `san_passwd`, `san_shadow`, and `san_group` with memberships in `adm,sudo,audio,video,plugdev,netdev,input,render,kvm,users,systemd-journal` and passwordless sudo.
- Desktop State Synchronization: Sync host wallpaper, xfce4, nemo, themes, systemd user units, and launchers into `/etc/skel` and `/home/flowork` for 100% UI fidelity.
- Multi-threaded XZ Compression: Compile SquashFS using `mksquashfs -comp xz -b 1048576 -Xbcj x86` with relative exclusion lists.

## 3. Strict Prohibitions
- Never embed Canonical/Ubuntu shim binaries (`shimx64.efi`) with active shim-lock inside non-secureboot hybrid boot media.
- Never bundle static gigabyte runtime payloads into rootfs when decoupled `.tar.zst` on-demand provisioners are available.
- Never leak browser sessions, tokens, personal documents, or `/opt/floworkos/agent` into rootfs.
- Never build SquashFS without verifying `san_passwd` contains `flowork:x:1000:1000`.
