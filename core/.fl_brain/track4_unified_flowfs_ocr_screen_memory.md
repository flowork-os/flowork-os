---
id: track4-unified-flowfs-ocr-screen-memory
keywords:
  - flowfs
  - screen_memory
  - visual_ocr
  - libtesseract
  - libleptonica
  - libwebp
  - fts5_bm25
  - dhash_dedup
  - privacy_exclusion
  - flowork_orbit
  - episodic_jit
  - drm_shm
---

# Track 4: Unified FlowFS Pure Rust & Visual OCR Screen Memory

## Problem Solved
Legacy `/opt/floworkos/bin/flowfs-search` and `/opt/floworkos/bin/flowfs-indexer-daemon` ran on Python + NumPy without FTS5 lexical indexing or automatic OCR text extraction on desktop captures (`flowfs_core.index_screen_capture(..., text="")`).

## Architecture Implemented
- **Pure Rust Core (`/opt/floworkos/crates/flowork-core-rs/src/flowfs.rs`):**
  - SQLite WAL + non-destructive FTS5 virtual tables (`flow_documents_fts`, `flow_screen_fts`, `porter unicode61`) with automatic backfill from existing `~/.local/share/flowork/flowfs.vec.db` rows.
  - Hybrid scoring combining SQLite `bm25()` + 128-dim L2-normalized sub-word trigram cosine similarity + title/filename/OCR boosts (`2.75ms` live screen search latency).
  - Native `libc::dlopen` FFI to `libtesseract.so.5`, `liblept.so.5`, and `libwebp.so.7` using `/opt/floworkos/system/tessdata/eng.traineddata`:
    - Single-pass image decode, downsampling (`<= 1280px`), automatic dark-mode luminance inversion (`mean < 110`) for HUD readability, strict `1500ms` OCR worker timeout, and `320px` WebP thumbnail emission (`/opt/floworkos/screenshots/thumbs/<hash>.webp`).
  - Perceptual `64-bit dHash` keyframe gate (skips OCR when Hamming diff `<= 3/64`, `<5%`), `app_class`/`window_title` privacy exclusion list, secret scrubbing, retention pruning (`FLOWORK_SCREEN_RETENTION_DAYS`), and Neural Bus `flowfs.screen.indexed` emission over `/tmp/flowork-neural-bus.sock` newline JSON.
- **Native Rust Binaries:**
  - `/opt/floworkos/bin/flowfs-search` & `/opt/floworkos/bin/flowfs-indexer-daemon` (`setpriority` Nice +19, `SYS_ioprio_set` Idle, `/proc/stat` >70% CPU pause, DRM SHM `/dev/shm/flowork_drm_latest.bgra` keyframe polling).
- **Integrations:**
  - `/opt/floworkos/bin/flowork-ambient-eye` (`--no-gui` support, active `WM_CLASS` extraction, native `flowfs-search --index-screen`).
  - `/opt/floworkos/connector/flowfs_core.py` delegates default DB operations to `/opt/floworkos/bin/flowfs-search` ELF while keeping Python AST/API compatibility.
  - `/opt/floworkos/theme/flowork-orbit.py` (`📸 SCREEN` tab, debounced async `?` / `??` queries, WebP `GdkPixbuf` cards, `Enter` Lightbox/Photocraft viewer, `Ctrl+C` path / `Ctrl+Shift+C` OCR clipboard copy).
  - `/opt/floworkos/mrflow-rs/src/memory/episodic.rs` bridges `flow_screen_fts` into `recall_jit` as bounded `<SCREEN_MEMORY_JIT source="flowfs_ocr">`.

## Empirical Verification
- `cargo test -p flowork-core-rs` (11/11), `cargo test -p mrflow` (30/30) PASSED.
- Live `flowfs-search --screen "Flowork" --json`: `2.75 ms`, OCR extracted `403 chars` from dark-mode `2560x1080` capture in `537 ms`.
- `qc_evolution_suite.py`: `8 PASSED, 0 FAILED`.
