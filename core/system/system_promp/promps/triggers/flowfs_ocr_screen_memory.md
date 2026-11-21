# FLOWFS PURE RUST & VISUAL OCR SCREEN MEMORY INVARIANTS

## 1. Context & Activation Scope
Activate only when maintaining `/opt/floworkos/crates/flowork-core-rs/src/flowfs.rs`, `flowfs-search`, `flowfs-indexer-daemon`, `flowork-ambient-eye`, Orbit Screen Memory (`flowork-orbit.py`), or `flow_screen_fts` recall in `mrflow-rs/src/memory/episodic.rs`.

## 2. Hard Invariants
- Preserve dual-table compatibility in `$HOME/.local/share/flowork/flowfs.vec.db`: keep legacy columns on `flow_documents` and `flow_screen_memory` intact alongside FTS5 virtual tables (`flow_documents_fts`, `flow_screen_fts`) so Python callers (`flowfs_core.py`) and QC checks never break.
- Load OCR and WebP libraries dynamically via `dlopen` (`libtesseract.so.5`, `liblept.so.5`, `libwebp.so.7`) using `/opt/floworkos/system/tessdata/eng.traineddata`; never link Python/NumPy or spawn heavy runtimes inside `flowfs-search` or `flowfs-indexer-daemon`.
- Enforce the `<= 1500ms` OCR timeout budget, dark-mode luminance inversion (`mean < 110`), `dHash` keyframe diff (`> 3/64` bits), and the `app_class`/`window_title` privacy exclusion filter before writing screen captures.
- Speak newline-delimited JSON on `/tmp/flowork-neural-bus.sock` (not HTTP) when publishing `flowfs.screen.indexed`.

## 3. Empirical Proof Gate
- Validate `cargo test -p flowork-core-rs`, `cargo test -p mrflow`, `python3 /opt/floworkos/qc_evolution_suite.py` (8/8 PASSED), `< 30ms` screen search latency, and zero Python processes for `flowfs-indexer-daemon`.
