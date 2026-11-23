---
name: take_screenshot
description: Standard operational procedure for capturing, compressing, and dispatching desktop screenshots to chat
keywords: [screenshot, capture, desktop, screen, maim, image, visual, display, compression, png, jpeg, inspection, proof, verification, telemetry, stream, socket, notification, audit, sovereign]
---

# ⚡ FLOWORK OS SOVEREIGN TOOL SKILL: SCREENSHOT CAPTURE SOP

Saat menggunakan tool `take_screenshot`, patuhi SOP kedaulatan Flowork OS:

1. **Penyimpanan Terpadu:**
   - Seluruh tangkapan layar wajib disimpan di direktori canonical `$HOME/Pictures/Screenshots/` (atau `/dev/shm/` untuk mode ultra-fast RAM).

2. **Kompresi & Proteksi Token (Anti-Bloat):**
   - Resolusi dan kualitas gambar wajib dikompresi agar hemat token jika diinspeksi oleh model.

3. **Kirim Otomatis ke Chat:**
   - Runner mengirimkan notifikasi instan ke socket companion `/tmp/mrflow-sidebar-*.sock` agar tangkapan layar langsung muncul di chat UI.
   - Respon agen wajib menyertakan path absolut berkas markdown: `![Screenshot](file:///path/to/screenshot.png)`.
