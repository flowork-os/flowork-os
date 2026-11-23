# LINUX 7.3+ KERNEL REBUILD & UNIVERSAL HARDWARE INVARIANTS

## 1. Context & Activation Scope
Activate only when configuring, building, or auditing the `Linux 7.3+` Flowork kernel (`build-flowork-kernel.sh`, `flowork-universal.config`), enabling `Landlock LSM`/`USER_NS`/`FUSE`/`UINPUT`, or debugging multi-vendor Intel/AMD hardware support (`i915`, `xe`, `VMD`, `iwlwifi`, `I2C_HID`, `SOF`).

## 2. Mandatory Behavioral Invariants
- Keep `/opt/floworkos/system/kernel/flowork-universal.config` declarative and merge via `scripts/kconfig/merge_config.sh -m` + `make olddefconfig` inside `build-flowork-kernel.sh`, then assert required `CONFIG_*` lines exist in `.config` (parent toggles such as `POWERCAP`, `USB_USBNET`, `VIRT_DRIVERS`, and `X86_PLATFORM_DRIVERS_{DELL,HP}` prevent silent Kconfig drops).
- Never pass `LOCALVERSION=""` to `make bindeb-pkg`; bump `CONFIG_LOCALVERSION` (e.g., `-flowork-rust-v2`) so `sort -V` selects the new kernel while preserving rollback and rebuilding DKMS (`TARGET_KVER=<new_kver> /opt/floworkos/system/kernel/enable-landlock-and-nvidia.sh`).
- Ensure `rustup component add rust-src` and `make rustavailable` succeed before building `CONFIG_RUST=y`.

## 3. Strict Prohibitions
- Never hardcode host usernames in `/opt/floworkos/system/kernel/` or ISO configs, and keep kernel source builds out of `/opt/floworkos/`.
- Never claim Landlock or Intel/AMD driver support is active without verifying `.deb` contents (`dpkg-deb -c`), running `uname -r`, and checking `/sys/kernel/security/lsm`.
