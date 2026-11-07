# 📸 Flowork OS — Screenshot Repository & Visual Capture Hub

Welcome to the canonical screenshot storage vault for **Flowork OS**.

This directory serves as the unified output destination for all visual captures, desktop snapshots, browser viewport recordings, and agent-driven inspection dumps generated across the operating system.

---

## 1. Purpose & Architecture

In the sovereign Flowork OS ecosystem, visual observation is an autonomous sensory feedback loop for both human operators and autonomous agents. Whenever an agent tool, headless browser runner, or desktop hotkey triggers a screen capture, the resulting image file is deterministically routed and persisted here.

### Core Objectives
1. **Unified Storage**: Eliminate scattered screenshot files across arbitrary temporary paths (`/tmp`, workspace roots, or downloads).
2. **Deterministic Agent Access**: Provide a predictable directory for subagents and forensic investigators to inspect system state and visual artifacts.
3. **Clipboard & Gallery Integration**: Interface seamlessly with the system clipboard, Nemo file manager bookmarks (`📸 Screenshots`), and native image viewers.

---

## 2. Directory Routing & Integration Matrix

All screenshot-capable utilities and agent tools must adhere to the following routing rules:

| Utility / Tool | Execution Path | Target Destination | Format |
| :--- | :--- | :--- | :--- |
| **Interactive Snipping GUI** | `/usr/local/bin/flowork-screenshot-gui` | `$SCREENSHOT_DIR/Screenshot_YYYY-MM-DD_at_HH.MM.SS.png` | PNG (24-bit RGB) |
| **Headless CLI Screenshot** | `/usr/local/bin/flowork-screenshot` | `$SCREENSHOT_DIR/screenshot_YYYYMMDD_HHMMSS.png` | PNG |
| **Browser CDP Tool** | `/opt/floworkos/tools/browser_take_screenshot` | `$SCREENSHOT_DIR/<filename>.png` | PNG / WEBP / JPEG |
| **Native Fallback (CLI)** | `maim`, `gnome-screenshot`, `import` | `$SCREENSHOT_DIR/<target>.png` | PNG |

---

## 3. Tool Authoring Standards for Agents

When creating or configuring an agent tool that captures visual outputs, follow these strict directives:

### A. Environment Path Resolution
Never hardcode raw user home paths in agent code. Resolve the destination path dynamically:
```javascript
// Node.js Tool Pattern
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs');

function getScreenshotDir() {
  const customPath = process.env.FLOWORK_SCREENSHOT_DIR;
  if (customPath && fs.existsSync(customPath)) {
    return customPath;
  }
  const defaultDir = path.join(os.homedir(), 'Pictures', 'Screenshots');
  if (!fs.existsSync(defaultDir)) {
    fs.mkdirSync(defaultDir, { recursive: true });
  }
  return defaultDir;
}
```

```bash
# Bash Tool Pattern
SCREENSHOT_DIR="${FLOWORK_SCREENSHOT_DIR:-${XDG_PICTURES_DIR:-$HOME/Pictures}/Screenshots}"
mkdir -p "$SCREENSHOT_DIR"
```

### B. File Naming Conventions
Files must be uniquely named to prevent accidental overwrites:
- **Timestamped standard**: `Screenshot_YYYY-MM-DD_at_HH.MM.SS.png`
- **Agent task standard**: `task_<taskId>_<epoch>.png`
- **Browser DOM dump**: `browser_page_<viewport>_<timestamp>.png`

### C. Permissions & Cleanliness
- Ensure generated screenshot files have read-write permissions (`0644` or `0664`) so both the operator and inspection subagents can view and process them without privilege escalation.
- Ephemeral test captures created during internal agent test loops should either be recorded with a clear test prefix (`test_capture_*.png`) or cleaned up post-verification.

---

## 4. UI & Shell Quick Access

- **File Manager (Nemo)**: Accessible directly from the sidebar under the **📸 Screenshots** bookmark.
- **Shortcuts & Hotkeys**:
  - `PrintScreen`: Captures full screen directly into this folder.
  - `Shift + PrintScreen`: Interactive selection box (snipping tool) with macOS-style instant preview popup.
- **Terminal Quick Jump**:
  ```bash
  cd ~/Pictures/Screenshots
  ```

---

*Flowork OS Sovereign Workspace — Autonomous Sensory & Visual Vault.*
