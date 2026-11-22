# SOVEREIGN ANDROID MICRO-VM AND MULTI-APK CONCURRENCY

## 1. Context & Activation Scope
Triggered when running, configuring, automating, or packaging Android APK applications, Scrcpy displays, Direct Hardware Windowing, and the Flowork Micro-VM subsystem.

## 2. Mandatory Behavioral Invariants
- **Always-On Standby Daemon:** The Android Micro-VM (`flowork-android-subsystem.service`) MUST start automatically on desktop login and remain warm in headless standby mode, enabling instantaneous zero-wait APK launches.
- **Isolated Virtual Displays for Concurrency:** Non-DRM Android apps (CapCut, Shopee, TikTok) MUST run on dedicated virtual displays (`--new-display=720x1280/240` or `1280x800/240`) with dynamic ports. This prevents concurrent applications from colliding, mirroring each other, or interrupting playback.
- **Pure X11 Direct Hardware Windowing for DRM & Play Store:** Apps requiring `FLAG_SECURE` (Melolo, DramaBox) and Google Play Store (`com.android.vending`) MUST run on the direct QEMU hardware display wrapped in a Pure X11 container window (`flowork-apk-direct`). NEVER route Google Play Store through virtual displays, as Android security blocks untrusted virtual surfaces.
- **Clean Detachment Lifecycle:** On `WM_DELETE_WINDOW` or application close, the direct controller MUST reparent the QEMU window back to root at off-screen coordinates `(5000, 5000)` and unmap it BEFORE container destruction. This guarantees QEMU stays alive and subsequent app launches never open with blank windows.
- **Subsystem Window Protection:** `hide_emulator_windows()` MUST detect active `flowork-apk-direct` processes and NEVER unmap or reposition QEMU while a direct hardware windowing session is active.
- **Eradication of Phone DNA:** Scrcpy MUST pass `--no-vd-system-decorations` to eliminate mobile status and navigation bars. Mouse bindings MUST suppress home and notifications (`--mouse-bind=b---`). All windows MUST open directly to the target app with standard Linux window titlebar decorations.
- **Universal Graphics & SwiftShader Resilience:** The Android emulator MUST dynamically audit host graphics (`detect_system_graphics()`). On systems lacking discrete GPUs or utilizing legacy Intel iGPUs (e.g. Core i3/i5 Ivy Bridge HD 2500/4000), it MUST enforce Google SwiftShader CPU rendering (`-gpu swiftshader_indirect`) to prevent crashes. Instant crashes MUST auto-fallback to `swiftshader_indirect` then `auto`.
- **Dynamic Hardware Sizing:** The AVD configuration MUST dynamically harmonize with host resources (`get_hardware_profile()`). Systems with <=4.5GB RAM MUST scale emulator memory to 1536MB and limit vCPUs to 2 cores to prevent host starvation and Linux kernel OOM kills.
- **Self-Healing KVM Virtualization:** The subsystem MUST automatically verify and repair `/dev/kvm` permissions (`chmod 666 /dev/kvm`) and kernel modules (`kvm_intel`/`kvm_amd`) before falling back or diagnosing BIOS VT-x state.
- **Decoupled On-Demand Hydration:** The Android Micro-VM emulator and system images are decoupled from the live ISO. The runtime MUST check `is_android_hydrated()` before launching or daemonizing, prompting or running `flowork-hydrate --app android` with graceful standby rather than crashing with unhandled file errors.

## 3. Strict Prohibitions
- NEVER allow concurrent Android apps to share Display 0 and mirror each other's viewports.
- NEVER embed the QEMU hardware display into `Gtk.Socket` or any framework widget that invokes `XDestroyWindow` on child windows.
- NEVER permit `hide_emulator_windows()` to unmap the active direct display while Melolo or DRM apps are running.
- NEVER allow phone homescreens, mobile status bars, or virtual navigation bars to render in desktop windows.
- NEVER execute `pkill qemu-system` or kill the emulator when an individual application window is closed.
- NEVER pass invalid `-gpu swiftshader` to Google Android emulator CLI; MUST pass `-gpu swiftshader_indirect`.
- NEVER crash or crash-loop daemon services when decoupled emulator payloads are unhydrated.
- NEVER allocate >=3GB RAM or >=4 cores to the emulator on dual-core or <=4GB physical memory systems.
- NEVER omit `/opt/floworkos/apk/` archiver or `flowork-android-subsystem.service` from `/etc/skel` and live ISO manifests.
