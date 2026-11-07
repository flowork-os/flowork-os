# 👑 Flowork OS — Sovereign AI-Native Operating System

[![Kernel](https://img.shields.io/badge/Kernel-Linux%207.3.0%20Rust-00ff66.svg?style=flat-square)](file:///home/awenkaudico/kernel-dev)
[![Architecture](https://img.shields.io/badge/Architecture-x86__64%20Preempt%20Dynamic-00f2fe.svg?style=flat-square)]()
[![GUI](https://img.shields.io/badge/GUI-Sovereign%20Glass%20HUD%20(0.60)-7928ca.svg?style=flat-square)]()
[![Security](https://img.shields.io/badge/Security-Landlock%20LSM%20Pure-ff0080.svg?style=flat-square)]()

Flowork OS is an autonomous, AI-native Linux distribution featuring the custom **Linux 7.3.0 Rust Kernel**, Landlock LSM kernel policies, native ELF AI reasoning runtime (**Mr. Flow**), and the **Sovereign Quantum Glass** desktop shell.

---

## 🏛️ System Architecture Layers

1. **`core/` (`/opt/floworkos`)**
   - Universal 13-pillar system root.
   - Native compiled AI engine (`/opt/floworkos/bin/mrflow`).
   - Pure Rust sub-millisecond environmental sensors (`system_promp/rules/.bin/`).
   - Desktop applications, Quantum Glass theme, and system session supervisor.

2. **`skel/` (`/etc/skel`)**
   - Canonical user configuration skeleton.
   - 100% reproducible XFCE4 glass panel layout, Plank dock, GTK-3.0 styling, and Alacritty terminal geometry.

3. **`system/`**
   - Systemd units, LightDM slick-greeter glass configurations, Xsessions entries, and `/usr/local/bin/` wrappers.

4. **`kernel/`**
   - Custom Linux 7.3.0 Rust Kernel binary packages (`linux-image`, `linux-headers`, `linux-libc-dev`).
   - Autonomous initramfs builder (`build_initramfs.sh`) and QEMU test harness.

5. **`packages/`**
   - Authoritative package selection manifest (`installed-packages.list`) containing exact system package dependencies.

6. **`iso-builder/`**
   - Automated bootable ISO generation scripts.

---

## 🚀 Building the Bootable ISO

To produce the identical bootable `flowork-os-7.3.0-amd64.iso`:

```bash
cd iso-builder
sudo ./build-iso.sh
```

---

*Architected by Dr. Flow under Architect AWENKAUDICO.*
