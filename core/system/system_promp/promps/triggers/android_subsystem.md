# SOVEREIGN ANDROID MICRO-VM & MULTI-APK RUNTIME

## 1. Context & Activation Scope
Applies when running, automating, debugging, or packaging Android APK applications, Google Play Store, Scrcpy displays, Direct Hardware Windowing, and Micro-VM daemons.

## 2. Mandatory Behavioral Invariants
- **Standby Micro-VM Daemon:** `flowork-android-subsystem.service` starts on desktop login and remains warm in headless mode for instant APK execution.
- **Direct Hardware Windowing for Play Store & DRM:** Google Play Store (`com.android.vending`) and DRM apps (`FLAG_SECURE`) MUST route through Direct Hardware Display (`flowork-apk-direct`) via Pure X11 container. On window close, reparent QEMU to root at (5000, 5000) and unmap before destruction.
- **Scrcpy Virtual Displays:** Non-DRM apps MUST run on dedicated virtual displays (`--new-display`) with phone decorations suppressed (`--no-vd-system-decorations`, `--mouse-bind=b---`).
- **Intel i3 / No-GPU Graphics Resilience:** Emulator MUST detect host GPU. On headless or legacy Intel iGPUs, enforce `-gpu swiftshader_indirect`. Never pass raw `-gpu swiftshader`.
- **Dynamic Sizing & Self-Healing KVM:** For host RAM <= 4.5GB, scale AVD to 1536MB RAM and 2 vCPUs. Auto-repair `/dev/kvm` permissions (`chmod 666`).
- **ISO Baked & On-Demand Fallback:** Baked directly into Live ISO v7.3.1+ for offline operation. If unhydrated on minimal builds, auto-trigger `flowork-on-demand android` with Glass HUD progress.

## 3. Strict Prohibitions
- NEVER route Google Play Store through virtual displays or embed QEMU into Gtk.Socket.
- NEVER kill QEMU on individual app window closure.
- NEVER allocate >=3GB RAM or >=4 cores on dual-core or <=4GB RAM hosts.
