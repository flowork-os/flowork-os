# LIVE ISO MASTERING & REPRODUCIBLE HYBRID PACKAGING

## 1. Context & Activation Scope
Applies when mastering, generating, or verifying bootable Flowork OS live ISO images (`.iso`), squashfs filesystems, or hybrid UEFI/BIOS bootloaders.

## 2. Mandatory Behavioral Invariants
- Exclude personal homes (`/home/*`), root credentials (`/root/*`), private tokens (`*token*`), SSH/GPG keys, and `/var/lib/lightdm` cache (`.config/google-chrome`, `.config/plank`).
- Purge host users (`awenkaudico`, `mrflow`) from `/etc/passwd`, `/etc/shadow`, `/etc/group`. Enforce sole live user `flowork` (UID 1000) with passwordless sudo.
- Synchronize LightDM autologin: set `autologin-user=flowork` and `user-session=flowork` in `lightdm.conf` to prevent broken greeter fallback screens.
- In `grub.cfg`, enforce dynamic partition search (`search --no-floppy --set=root --file /live/vmlinuz`) so UEFI transitions from partition 2 (EFI) to rootfs partition 1.
- Suppress initramfs warnings with `plymouth.enable=0 selinux=0 quiet splash` in kernel cmdline.
- Dual-master hybrid boot: Embed Microsoft-signed `shimx64.efi.signed` as `BOOTX64.EFI`, Canonical-signed `grubx64.efi.signed`, and `mmx64.efi` inside FAT EFI partition.
- Compress rootfs via multi-threaded XZ (`mksquashfs -comp xz -b 1048576`). Validate bootability and SHA256 checksum with Exit Code 0.

## 3. Strict Prohibitions
- Never leak browser profiles, Telegram sessions, or auth tokens into `/var/lib/lightdm` or rootfs.
- Never hardcode host user paths in boot session scripts or live configurations.
- Never boot UEFI without dynamic root search (`search --file /live/vmlinuz`).
