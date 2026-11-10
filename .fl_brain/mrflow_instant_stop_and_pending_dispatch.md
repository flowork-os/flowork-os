---
title: Mr. Flow Instant Stop, Pending Queue Immediate Dispatch & End-to-End Screenshot Fix
category: architecture
keywords:
  - mrflow_sidebar
  - instant_stop_abort
  - pending_queue_dispatch
  - screenshot_preview
  - user_attached_preview
  - python3_tokenize_stdlib_fix
  - gtk_clipboard_thread_safety
  - instant_local_preview_filereader
  - xclip_clipboard_sync
  - multi_directory_screen_search
date: 2026-11-10
---

# Mr. Flow Instant Stop, Pending Queue Immediate Dispatch & End-to-End Screenshot Fix

## 1. Issue Analysis & Root Cause
1. **Screenshot Failure & Missing Preview ("screenshoot masih ngak bisa"):**
   - **Critical Python 3.12 Standard Library Missing Inode:** Python 3.12 minimal installation was missing `/usr/lib/python3.12/tokenize.py` and `token.py`. When PIL (`from PIL import Image`) was imported during image processing, it failed with `ModuleNotFoundError: No module named 'tokenize'` (from `PIL.Image -> logging -> traceback -> linecache -> tokenize`), silently aborting all screenshot captures and clipboard processing.
   - **GTK Clipboard Thread Safety:** `Gtk.Clipboard.wait_is_image_available()` and `wait_for_image()` were called inside a background `threading.Thread` upon receiving `paste_from_system_clipboard`, where GTK X11 selection events cannot be processed, returning `False`.
   - **Preview Latency:** UI previously waited for Python to save and return a data payload before showing the thumbnail. In Antigravity-grade UX, local file reading via `FileReader` should display the preview card immediately in 0ms.
2. **Stop Delay & Inability to Send Pending Messages Immediately:**
   - The UI Stop button (`#btnStopExecution`) was hidden during tool transitions in `hideSovereignTaskHud` and `updateSovereignTaskHudFinished`.
   - Python backend previously executed blocking `proc.wait(1.0)` and `err_thread.join(0.5)`.
   - Pending queue items lacked an instant dispatch button, forcing users to wait for turns to finish.

## 2. Implemented Solutions
1. **Python Standard Library Inode Restoration & Canonical Fallback:**
   - Restored authentic `tokenize.py` and `token.py` from Ubuntu noble-updates `libpython3.12-minimal`.
   - Installed canonical system assets in `/opt/floworkos/lib/python3/` and `/home/awenk/.local/lib/python3.12/site-packages/`.
   - Added early `sys.path.insert(0, "/opt/floworkos/lib/python3")` in `mrflow-sidebar.py` to permanently protect against environment drift.
2. **GTK Main-Thread Clipboard Execution:**
   - Dispatched `paste_from_system_clipboard` on `GLib.idle_add(self._check_and_paste_system_clipboard)` to guarantee 100% thread-safe GTK clipboard interrogation.
   - Preserved fallback sequence: `Gtk.Clipboard` -> URI check -> `xclip` direct extraction -> 5-minute newest screenshot lookup in `~/Pictures/Screenshots`, `/opt/floworkos/screenshots`, and `/tmp`.
3. **Instant 0ms UI Preview & Dual Event Binding:**
   - Updated `filePickerInput`, `drop`, and `paste` handlers in `ui/index.html` to generate an instant base64 data URI preview via `FileReader` and immediately display `#attachmentPreview` above `#userInput`.
   - Attached paste listeners to both `window` and `#userInput` to prevent textarea event swallowing.
   - Added `attachedImageB64` fallback in `send_agent_message` to eliminate async file saving race conditions.
4. **Permanent Stop Button & "⚡ Kirim Sekarang" Pending Queue:**
   - Enforced `btnStopInput.style.display = isGenerating ? "flex" : "none"` throughout generation.
   - Reduced abort timeout to 0.1s with non-blocking SIGKILL.
   - Added `sendPendingMessageNow(index)` with button `⚡ Kirim Sekarang` on every pending queue card, plus `Ctrl+Enter` immediate interruption shortcut.

## 3. Empirical Verification
- Tested end-to-end clipboard paste via Unix domain socket `/tmp/mrflow-sidebar-awenk.sock`:
  `[08:51:16 AM] Clipboard pixbuf saved successfully: /home/awenk/Pictures/Screenshots/User_Pasted_20261110_085116.jpg (0.6 KB)`
  `[08:51:51 AM] PREVIEW_STATUS_REPORT: {"action": "log_preview_status", "scope_attachedUserImage": true, "path": "/home/awenk/Pictures/Screenshots/User_Pasted_20261110_085116.jpg"}`
- `flowork-mrflow-sidebar.service` is active and running cleanly (Main PID 253527).
- Full QC Evolution Suite verified: 8 passed, 0 failed (Exit Code 0).
