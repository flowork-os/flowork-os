# UPSTREAM APPIMAGE, ELECTRON & EXTERNAL CLI INTEGRATION

## 1. Context & Activation Scope
Activate only when cloning, building, wrapping, or packaging external upstream desktop/TUI applications (`openscreen`, `gputaskman`, `AppImage`, `app.asar`, `pyinstaller`, `third_party_licenses`) into `/opt/floworkos/apps/`.

## 2. Mandatory Behavioral Invariants
- **Runtime Extraction & Permissions:** Extract `.AppImage` runtimes directly into `squashfs-root/`, delete the raw `.AppImage` to prevent bloat, preserve `4755 root:root` on `chrome-sandbox`, and enforce `o+rx` checks in `build-live-iso.sh` and `flowork-update`.
- **Chromium/GTK Flag Safety:** Never forward CLI flags like `--display <index>` raw to Electron/Chromium binaries before GTK initializes; map them cleanly to env variables (`OPENSCREEN_DISPLAY_INDEX`) inside `/opt/floworkos/bin/<app>` and preserve `DISPLAY`.
- **Zero-Node Scratch Discipline:** When an upstream Electron/Vite build requires `node`/`npm`, isolate portable binaries inside `scratch/`, rebuild `app.asar` + `THIRD-PARTY-LICENSES.txt`, then delete `scratch/` before finishing.
- **Neural Bus & Repo Guard:** Provide a single-object JSON `<app>-cli` wrapper supporting `{file}`/`stdin` chaining, exclude heavy runtimes from Git (`<50MB` limit) in `upload-flowork-os.sh`, archive license texts under `licenses/`, and register `/usr/local/bin` + `/usr/share/applications` pseudo-files in `build-live-iso.sh`.

## 3. Strict Prohibitions
- Never push binaries `>=50MB`, `.AppImage` archives, or personal `$HOME` build paths to `flowork-os-repo`.
- Never guess X11 `StartupWMClass` without empirical `wmctrl -lx` + `desktop-file-validate` checks.
