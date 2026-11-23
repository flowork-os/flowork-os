# FLOWOS MOBILE ARCHITECTURE & RUNTIME INVARIANTS

## 1. Context & Activation Scope
Applies when porting, compiling, deploying, or testing FlowOS on Android (POCO C75 `lake` or AOSP sandboxes).

## 2. Mandatory Behavioral Invariants
- **Zygote SECCOMP Isolation:** Apps cannot execute `su 0` (`SIGSYS`). Route agent turns through root daemon `flowork-connector` via `POST /api/mrflow/stream` on loopback `127.0.0.1:9099`.
- **Zero Pipe Deadlock:** Never leave spawned process stdout/stderr unconsumed; drain or route to inherit/log to prevent 64KB pipe stall.
- **AOSP Pure Runtimes:** Stock AOSP lacks Python/curl. Use POSIX shell actuators (`android_actuator`, `take_screenshot`) and static musl binaries (`mrflow`, `flowork-connector`, `curl`).
- **Dynamic Temp:** Resolve temp hierarchically: `/data/local/tmp` -> `/data/floworkos/tmp` -> `/tmp`.
- **Static Musl Build:** Build ARM64 release binaries via `aarch64-unknown-linux-musl` using `clang`, `rust-lld`, `rustls` (`ring`).
- **Data Sanctuary & SELinux:** Keep 13 Pillars under `/data/floworkos` (0777). Enforce `umask 000` and `setenforce 0` in init services so Launcher priv-app can index/resume `.flowork/history/chats`.
- **App Drawer & Base64 Icons:** In `LauncherActivity.java`, extract icons as PNG Base64 (`iconBase64`) scaled 72x72; populate `name`/`label` and `package`/`packageName`. Include ComponentName fallback.
- **SingleTask Navigation:** Home (`keyevent 3`) calls `onNewIntent` (`window.onHomePressed`). Back (`keyevent 4`) calls `window.onBackPressed`. Manifest: `singleTask`, `resumeWhilePausing="true"`.
- **De-Googled Stores:** Deploy Aurora Store and F-Droid via `./tools/install_app_stores.sh`.

## 3. Strict Prohibitions
- Never touch desktop `/opt/floworkos` binaries during mobile builds.
- Never flash physical devices without explicit confirmation and passing sandbox tests.
