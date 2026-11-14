# FLOWOS MOBILE ARCHITECTURE & RUNTIME INVARIANTS

## 1. Context & Activation Scope
Applies when porting, compiling, deploying, or troubleshooting Flowork OS components (Mr. Flow, Flowork Connector, Launcher) on Android mobile devices (e.g., POCO C75 `lake` or AOSP sandboxes).

## 2. Mandatory Behavioral Invariants
- **Zygote SECCOMP Isolation:** Android app processes cannot execute `su 0` directly (`SIGSYS`). Route agent turns through root daemon `flowork-connector` via `POST /api/mrflow/stream` on loopback `127.0.0.1:9099`.
- **Zero Pipe Buffer Deadlock:** Never leave spawned child process stdout/stderr unconsumed. Piping without draining deadlocks processes after 64KB of tracing logs. Route child output to `Stdio::inherit()` or append to `/data/floworkos/connector.log`.
- **AOSP Runtimes & Pure Tools:** Stock AOSP lacks `/usr/bin/python3` and `/system/bin/curl`. Never place Python tools (`run.py`) on mobile. Deploy pure POSIX shell actuators (`android_actuator`, `take_screenshot`) and static musl binaries (`mrflow`, `flowork-connector`, `curl`).
- **Dynamic Temp Resolution:** Android lacks `/tmp`. Always resolve temporary directories hierarchically: `/data/local/tmp` -> `/data/floworkos/tmp` -> `/tmp`.
- **Static Musl Compilation:** Build ARM64 release binaries via `aarch64-unknown-linux-musl` using `clang`, `rust-lld`, and `rustls` with `ring`.
- **Data Sanctuary:** Maintain 13 Pillars under `/data/floworkos` (mode 0777). Symlink `/data/floworkos/history/chats` to `.flowork/history/chats`.

## 3. Strict Prohibitions
- Never touch desktop `/opt/floworkos` binaries or source code during mobile builds.
- Never flash physical devices without explicit confirmation and passing sandbox emulation tests.
