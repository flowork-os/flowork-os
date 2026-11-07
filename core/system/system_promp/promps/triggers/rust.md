# 🦀 PASSIVE TRIGGER: RUST SYSTEMS & ZERO-COST ABSTRACTION DOCTRINE
* **Konteks Terdeteksi**: Workspace aktif memuat berkas `.rs` atau `Cargo.toml`.
* **Aturan Khusus**:
  1. Patuhi kaidah kepemilikan memori (*ownership & borrowing*): minimalkan clone yang tidak perlu, prioritaskan references (`&str`, `&[T]`).
  2. Tangani error secara idiomatik menggunakan `Result<T, E>` dan operator `?`, hindari `.unwrap()` di kode produksi.
  3. Pastikan kode lolos `cargo check` dan `cargo clippy` tanpa peringatan (*zero warnings*).
  4. Biner sistem wajib dikompilasi dengan profile `--release` sebelum didistribusikan ke `/opt/floworkos/bin/`.
