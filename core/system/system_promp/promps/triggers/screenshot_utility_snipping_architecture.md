# SCREENSHOT & SNIPPING UTILITY ARCHITECTURE

## 1. Context & Scope
Applies when developing, diagnosing, or invoking Flowork OS desktop snipping and screenshot capture (`flowork-screenshot`, `slop`, `maim`, or screenshot keybindings).

## 2. Mandatory Architectural Invariants
- DIRECT INTERACTIVE SNIPPING: Default execution mode MUST BE interactive area selection (`mode = "area"` via `slop --noopengl` and `maim -u -g`). Never impose modal toolbar barriers or multi-click workflows before selection.
- CHAT SIDEBAR COMPATIBILITY: The standalone snipping utility must behave identically to the Mr. Flow chat sidebar capture (`-a` snippet).
- ACTION PREVIEW POPUP: Every capture MUST materialize the bottom-right Pure Optical Crystal Glass preview popup featuring:
  1. `Tersalin ✓`: Re-copy image to X11 clipboard (`xclip -selection clipboard -t image/png`).
  2. `Buka`: Open image in default viewer (`xdg-open <file>`).
  3. `Buka Folder`: Open containing directory (`$HOME/Pictures/Screenshots`) in file manager (`xdg-open <dir>`).
- AUTOMATIC TELEMETRY: Every successful capture is automatically copied to clipboard, saved with timestamped ISO filename, and mirrored to `/opt/floworkos/screenshots/`.
