# 📸 Flowork OS — Sovereign Screenshot Vault

Welcome to the centralized screenshot storage hub for **Flowork OS** (`/opt/floworkos/screenshots`).

This directory serves as the unified system-wide capture vault for all visual artifacts, desktop snapshots, browser viewport recordings, and agent-driven inspection dumps across the entire operating system.

---

## 1. Architectural Philosophy

In Flowork OS, visual perception is a first-class operational input for both human operators and autonomous agents. By centralizing all screenshot operations in `/opt/floworkos/screenshots`:

1. **User-Agnostic Portability**: Captured artifacts are decoupled from individual user home directories (`/home/<username>`). When building ISO installers or deploying across multi-user environments, paths never break.
2. **Deterministic Agent Feedback**: Any autonomous agent, background daemon, or CLI tool has a single canonical location to store and read inspection screenshots.
3. **Nemo File Manager Quick Access**: Integrated directly into the file manager sidebar via the `📸 Screenshots` bookmark (`file:///opt/floworkos/screenshots`).

---

## 2. Directory Routing & Integration Matrix

All screenshot-capable tools and utilities are configured to persist visual artifacts directly into this vault:

| Utility / Tool | Path | Invocation / Trigger | File Pattern |
| :--- | :--- | :--- | :--- |
| **Interactive Snipping GUI** | `/usr/local/bin/flowork-screenshot-gui` | `Shift + PrintScreen` (macOS-style popup) | `Screenshot_YYYY-MM-DD_at_HH.MM.SS.png` |
| **Headless CLI Capture** | `/usr/local/bin/flowork-screenshot` | `PrintScreen` or CLI scripts | `screenshot_YYYYMMDD_HHMMSS.png` |
| **Browser CDP Tool** | `/opt/floworkos/tools/browser_take_screenshot` | Agent browser automation | `<custom_name>.png` |
| **Native Fallback Tools** | `maim`, `gnome-screenshot`, `import` | CLI one-liners | `<filename>.png` |

---

## 3. Developer & Agent Integration Standards

When authoring new agent tools or scripts that produce visual artifacts:

### A. Environment Path Resolution
All tools must target this directory as the primary default:
```javascript
// Node.js Tool Pattern
const path = require('node:path');
const fs = require('node:fs');

function getScreenshotDir() {
  const dir = process.env.FLOWORK_SCREENSHOT_DIR || '/opt/floworkos/screenshots';
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
}
```

```bash
# Bash Tool Pattern
SCREENSHOT_DIR="${FLOWORK_SCREENSHOT_DIR:-/opt/floworkos/screenshots}"
mkdir -p "$SCREENSHOT_DIR"
```

### B. File Permissions
Files generated inside this directory should be readable by all users and agents (`0666` or `0644`) to allow frictionless inspection by forensics agents without privilege elevation.

### C. Naming & Hygiene
- **Timestamped Standard**: `Screenshot_YYYY-MM-DD_at_HH.MM.SS.png`
- **Agent Task Standard**: `task_<taskId>_<epoch>.png`
- Automated test runs must clean up transient screenshots post-verification or label them with `test_` prefixes.

---

## 4. UI & Shell Quick Access

- **File Manager (Nemo)**: Pinned under `📸 Screenshots` in the sidebar (`file:///opt/floworkos/screenshots`).
- **Shortcuts**:
  - `PrintScreen`: Instant full-screen capture saved directly here.
  - `Shift + PrintScreen`: Interactive area selection with instant preview and copy-to-clipboard popup.
- **Terminal Navigation**:
  ```bash
  cd /opt/floworkos/screenshots
  ```

---

*Flowork OS Sovereign Workspace — Canonical Visual Vault.*
