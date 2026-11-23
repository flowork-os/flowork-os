# Implementation Plan: Detached GUI App Launch & Zero-Hang Handshake

## 1. Objective
Eliminate synchronous blocking and hanging when launching GUI desktop applications in Flowork OS, ensuring instant fallback (< 0.5s) to Mr. Flow and calling environments with verified PID status while keeping GUI apps actively running on the desktop.

## 2. Key Files & Context
- `/opt/floworkos/bin/crypto-radar`: Currently uses blocking `exec python3 ...` foreground call.
- `/opt/floworkos/bin/craft-anything`: Currently uses blocking `exec "$CACHE_BIN" "$@"` foreground call.
- `/opt/floworkos/bin/craft-app`: Synthesizes and registers apps; must generate detached launcher binaries.
- `/opt/floworkos/bin/flowork-launch`: Universal sovereign CLI runner with instant handshake and crash sentinel.
- `/opt/floworkos/system/system_promp/promps/triggers.json`: Needs trigger keywords (`jalankan`, `buka`, `launch`, `run app`, `aplikasi`).
- `/opt/floworkos/system/system_promp/promps/triggers/process_lifecycle_and_audio.md`: Prompts agent with detached launch doctrine.

## 3. Implementation Steps

### Step 1: Create Universal Sovereign Detacher `/opt/floworkos/bin/flowork-launch`
- Create executable bash script `/opt/floworkos/bin/flowork-launch` (and symlink `/usr/local/bin/flowork-launch`).
- Logic:
  1. Accepts target command or app ID.
  2. Spawns process using `setsid <command> >/dev/null 2>&1 &` or logs to `/tmp/flowork_app_launch.log`.
  3. Checks `kill -0 $PID` after 0.3s.
  4. Returns Exit Code 0 immediately with JSON output `{"status": "running", "pid": PID, "app": APP}`.

### Step 2: Fix Non-Detaching Launchers in `/opt/floworkos/bin/`
- Update `/opt/floworkos/bin/crypto-radar` to launch detached with `nohup python3 ... >/dev/null 2>&1 &` and `exit 0`.
- Update `/opt/floworkos/bin/craft-anything` to launch detached with `nohup "$CACHE_BIN" "$@" >/dev/null 2>&1 &` and `exit 0`.

### Step 3: Update `craft-app` Template and Launcher Generator
- Ensure newly synthesized and registered applications generate detached runners with `setsid`/`nohup`.

### Step 4: Expand Trigger Keywords & System Prompts
- Update `triggers.json` for `process_lifecycle_and_audio` to include Indonesian & English launch keywords (`"launch"`, `"buka"`, `"jalankan"`, `"run app"`, `"open app"`, `"aplikasi"`).
- Ensure `process_lifecycle_and_audio.md` reinforces the mandatory detached launch invariant for all GUI applications.

## 4. Verification & Testing
1. Test `/opt/floworkos/bin/flowork-launch crypto-radar` and ensure it exits with Code 0 in < 0.5s while the GUI window appears.
2. Test `/opt/floworkos/bin/crypto-radar` directly and verify it returns Exit Code 0 immediately.
3. Test `/opt/floworkos/bin/craft-anything` directly and verify it returns Exit Code 0 immediately.
4. Verify window detection via `wmctrl -l` or `xdotool` confirming processes remain healthy.
