---
title: Linux 7.3+ Landlock LSM, Sandbox & Universal Intel/AMD Hardware Kernel Rebuild
category: kernel
date: 2026-11-11
keywords:
  - linux_7_3
  - landlock_lsm
  - flowork_universal_config
  - build_flowork_kernel
  - config_user_ns
  - config_fuse_fs
  - config_input_uinput
  - intel_i915_xe_vmd
  - iwlwifi_sof_i2c_hid
  - nvidia_dkms_v2
  - bindeb_pkg
  - flowork_rust_kernel
---

# Linux 7.3+ Landlock LSM, Sandbox & Universal Intel/AMD Hardware Kernel Rebuild

## Problem Addressed
The initial `7.3.0-flowork-rust-gd89e1d186ec9` build (`#7`) shipped with a minimal hardware and security config (`1731 =y`, `15 =m`), leaving critical subsystems disabled:
- Security/sandbox flags: `CONFIG_SECURITY_LANDLOCK`, `CONFIG_SECURITYFS`, `CONFIG_USER_NS`, `CONFIG_PSI`, `CONFIG_FUSE_FS`, `CONFIG_BTRFS_FS`, `CONFIG_INPUT_UINPUT`, `CONFIG_FW_LOADER_COMPRESS_ZSTD`.
- Universal Intel/AMD hardware: `CONFIG_VMD=y` (Intel NVMe VMD storage), `CONFIG_DRM_XE=m` (Intel Arc / Core Ultra), `CONFIG_IWLWIFI=m`, `CONFIG_I2C_HID_ACPI=m` + Intel Pinctrl/LPSS/DesignWare I2C (laptop touchpads), `CONFIG_SND_SOC_SOF_*` (Intel/AMD laptop DSP audio), `CONFIG_USB_VIDEO_CLASS=m` (UVC webcams), `CONFIG_BT_HCIBTUSB=m` (`BT_INTEL`/`RTL`/MTK/QCOM), `CONFIG_IGB`/`CONFIG_IGC`/`CONFIG_IXGBE=m` (2.5Gb+ Intel LAN), `CONFIG_DRM_AMDGPU=m` + `CONFIG_DRM_RADEON=m`, and `CONFIG_DRM_NOUVEAU=m` (legacy discrete fallback when `nvidia-open` is inapplicable).

## Root Solution & Architecture
- **Declarative Config Fragment:** `/opt/floworkos/system/kernel/flowork-universal.config` enforces `CONFIG_LOCALVERSION="-flowork-rust-v2"` along with Landlock, BPF/PSI, UINPUT, FUSE, Btrfs/exFAT/NTFS3, Intel `i915`+`xe`+`VMD`, `AMDGPU`/`Nouveau`, laptop OEM/touchpad/SOF/Wi-Fi/Bluetooth/USB4/LAN, and `KVM` drivers.
- **Reproducible Packaging Pipeline:** `/opt/floworkos/system/kernel/build-flowork-kernel.sh` validates `make rustavailable` (with Rust `rust-src` installed), merges base `/boot/config-$(uname -r)` with `flowork-universal.config`, runs `make olddefconfig`, asserts every critical flag is enabled (preventing silent Kconfig drops from missing parent dependencies such as `USB_USBNET`, `POWERCAP`, `VIRT_DRIVERS`, `X86_PLATFORM_DRIVERS_*`), and compiles `make bindeb-pkg`.
- **Target Kernel Versioning & Provisioning:** Bumping `-flowork-rust-v2` places `7.3.0-flowork-rust-v2-gd89e1d186ec9` cleanly above `#7` under `sort -V` in `/opt/floworkos/iso-builder/build-live-iso.sh` while keeping `#7` as a GRUB rollback entry. `TARGET_KVER=7.3.0-flowork-rust-v2-gd89e1d186ec9 /opt/floworkos/system/kernel/enable-landlock-and-nvidia.sh` compiles NVIDIA 595.99.02 DKMS against the new kernel headers before reboot.

## Multi-Hardware Caveat (Pre-Turing NVIDIA)
- `/usr/share/X11/xorg.conf.d/10-nvidia.conf` uses `MatchDriver "nvidia-drm"`, so Intel (`i915`/`xe`) and AMD (`amdgpu`) systems use native DRM/Xorg `modesetting` cleanly without conflict.
- Systems carrying older pre-Turing NVIDIA GPUs (GTX 10xx / GTX 9xx) cannot bind `nvidia-driver-595-open` and are affected by `/lib/modprobe.d/nvidia-graphics-drivers.conf` blacklisting `nouveau`; installing non-open `nvidia` or booting with Intel/AMD/safe graphics (`nomodeset`) resolves display initialization on legacy hardware.
