---
name: run_shell_command
description: Master procedural doctrine for shell commands execution, process sandboxing, and Exit Code 0 verification
keywords: [shell, bash, command, linux, process, terminal, execution, exitcode, pipeline, stdout, stderr, sandbox, sovereign, audit, safety, background, daemon, timeout, flowork, doctrine]
---

# ⚡ FLOWORK OS SOVEREIGN TOOL SKILL: SHELL EXECUTION SOP

Saat menggunakan tool `run_shell_command`, wajib mematuhi doktrin inti Flowork OS:

1. **Prinsip Bukti Empiris (Exit Code 0):**
   - Setiap klaim keberhasilan WAJIB didasarkan pada output perintah terminal yang berakhir dengan kode keluar `Exit Code 0`.
   - Jika perintah mengembalikan kode keluar selain 0, analisis pesan kesalahan pada `stderr` dan lakukan perbaikan secara mandiri.

2. **Perlindungan Proses Panjang (No Blocking):**
   - Perintah yang membutuhkan waktu lama (misal instalasi paket berat, build kernel/ISO) WAJIB dijalankan dengan mekanisme non-blocking atau background task.
   - Jangan pernah menjalankan `sleep` tanpa batas di foreground.

3. **Integritas Teritori:**
   - Seluruh modifikasi skrip OS wajib berada di bawah `/opt/floworkos` atau workspace target `$HOME`.
   - Dilarang keras merusak konfigurasi inti `/opt/floworkos/connector/` (port 9099).
