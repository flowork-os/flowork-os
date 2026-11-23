# ⚡ CALAMARES EFI SIZING & SILENT PLYMOUTH BOOT/SHUTDOWN MANDATE

When configuring, modifying, or auditing the Calamares installer, system bootloaders, GRUB, initramfs, or Plymouth splash themes in Flowork OS, strictly enforce the following invariants:

1. **Calamares EFI Partition Sizing (Minimum 1024–2048 MiB):**
   - In `/etc/calamares/modules/partition.conf`, ALWAYS declare the explicit `efi:` block with `recommendedSize: 2048MiB`, `minimumSize: 1024MiB`, and `mountPoint: "/boot/efi"`.
   - NEVER permit default ESP sizing (300–500 MiB). Modern kernels (7.x+), dual initrds (host + fallback), and discrete GPU DKMS modules require >400 MB, causing "Erase disk" automated installs to fail fatally with `grub-install exit code 1 (No space left on device)`.
   - Ensure `bootloader.conf` specifies `installEFIFallback: true`, `grubProbe: "grub-probe"`, and `efiBootMgr: "efibootmgr"`.

2. **Professional Silent Boot & Fast Shutdown (Zero Terminal Spam):**
   - Eliminate terminal codes, dmesg traces, and systemd service logs during boot, reboot, and shutdown by setting kernel parameters:
     `quiet splash loglevel=3 systemd.show_status=auto rd.udev.log_level=3 vt.global_cursor_default=0`
   - In ISO boot skeletons (`boot-skeleton/boot/grub/grub.cfg`, `EFI/BOOT/grub.cfg`, `isolinux/isolinux.cfg`), NEVER use `plymouth.enable=0` or `nosplash`.
   - In Calamares `/etc/calamares/modules/grubcfg.conf`, persist `kernel_params` and `GRUB_CMDLINE_LINUX_DEFAULT` with these silent flags into the installed target system.
   - Enforce systemd shutdown silence via `/etc/systemd/system.conf.d/10-flowork-silent.conf` using `ShowStatus=auto` and `DefaultTimeoutStopSec=10s`.
   - Plymouth theme must default to `/usr/share/plymouth/themes/flowork-cyber/flowork-cyber.plymouth` powered by `two-step.so` (`plymouth-theme-spinner`).
