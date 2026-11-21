# Third-Party Software Notices & Open Source Attribution

Flowork OS deeply values, respects, and attributes all open-source software, upstream authors, libraries, and kernel engineers who make our sovereign operating system possible.

All collected upstream **LICENSE**, **COPYING**, **NOTICE**, **COPYRIGHT**, and **ATTRIBUTION** texts have been consolidated into [`licenses/`](licenses/) so every open-source notice remains permanently public, inspectable, and verifiable in this repository.

---

## Linux Kernel & Core Infrastructure

### Linux Kernel (Rust-for-Linux Subsystem)
- **Upstream Repository:** [https://github.com/Rust-for-Linux/linux](https://github.com/Rust-for-Linux/linux)
- **Original Authors & Maintainers:** Linus Torvalds, Greg Kroah-Hartman, Miguel Ojeda, Wedson Almeida Filho, and thousands of Linux & Rust-for-Linux kernel contributors.
- **Primary License:** **GNU General Public License v2.0 only with Linux Syscall Note (`GPL-2.0 WITH Linux-syscall-note`)**
- **Rust Bindings License:** Dual-licensed under **`GPL-2.0 OR Apache-2.0 OR MIT`** for core Rust infrastructure.
- **Tribute:** Flowork OS builds upon the work of the Rust-for-Linux community, integrating memory-safe drivers, Landlock LSM security sandboxing, and `PREEMPT_DYNAMIC`.

### Zstandard (`zstd` v1.5.5) & Calamares Installer
- **Zstandard (`zstd`):** Copyright Yann Collet / Meta Platforms — dual-licensed under **`BSD-3-Clause OR GPL-2.0`** ([`licenses/audacity/runtime-debian-copyrights/libzstd1/copyright`](licenses/audacity/runtime-debian-copyrights/libzstd1/copyright)).
- **Calamares Installer Configuration:** Upstream Calamares distribution installer framework licensed under **GNU GPL-3.0-or-later**.
- **Debian Base OS Packages:** Full Debian/Ubuntu package inventory recorded in [`packages/installed-packages.list`](packages/installed-packages.list).

---

## Native Rust & CLI Agent Binaries

| Package | Version | Authors / Upstream | License | Archived License Path |
| :--- | :--- | :--- | :--- | :--- |
| **`agent-browser`** (Native Rust CLI) | 0.27.0 | Vercel Labs ([vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser)) | Apache-2.0 | [`licenses/agent-browser/LICENSE`](licenses/agent-browser/LICENSE) |
| **`agent-desktop`** (Native Rust CLI) | 1.2.0 | Vercel Labs ([vercel-labs/agent-desktop](https://github.com/vercel-labs/agent-desktop)) | Apache-2.0 | [`licenses/agent-desktop/LICENSE`](licenses/agent-desktop/LICENSE) |

---

## Storytold & Tangency Labs Pure Rust Creative Suite

Dual licensed under **Apache License 2.0** and **MIT License** (embedded fonts under **SIL Open Font License 1.1**). Archived notices preserved under [`licenses/creative-suite/`](licenses/creative-suite/):

1. **PhotoCraft (`photocraft`):** [storytold/photocraft](https://github.com/storytold/photocraft) — [`licenses/creative-suite/photocraft/`](licenses/creative-suite/photocraft/)
2. **VectorCraft (`vectorcraft`):** [storytold/vectorcraft](https://github.com/storytold/vectorcraft) (includes `hayro-*` PDF backend licenses) — [`licenses/creative-suite/vectorcraft/`](licenses/creative-suite/vectorcraft/)
3. **FilmCraft (`filmcraft`):** [storytold/filmcraft](https://github.com/storytold/filmcraft) — [`licenses/creative-suite/filmcraft/`](licenses/creative-suite/filmcraft/)
4. **LightCraft (`lightcraft`):** [storytold/lightcraft](https://github.com/storytold/lightcraft) — [`licenses/creative-suite/lightcraft/`](licenses/creative-suite/lightcraft/)
5. **PdfCraft (`pdfcraft`):** [storytold/pdfcraft](https://github.com/storytold/pdfcraft) (includes ONNX model licenses in `pdfcraft-models/`) — [`licenses/creative-suite/pdfcraft/`](licenses/creative-suite/pdfcraft/)
6. **EffectCraft (`effectcraft`):** [storytold/effectcraft](https://github.com/storytold/effectcraft) — [`licenses/creative-suite/effectcraft/`](licenses/creative-suite/effectcraft/)
7. **DesignCraft (`designcraft`):** [storytold/designcraft](https://github.com/storytold/designcraft) — [`licenses/creative-suite/designcraft/`](licenses/creative-suite/designcraft/)
8. **FigCraft (`figcraft`):** [storytold/figcraft](https://github.com/storytold/figcraft) — [`licenses/creative-suite/figcraft/`](licenses/creative-suite/figcraft/)
9. **WordCraft (`wordcraft`):** [storytold/wordcraft](https://github.com/storytold/wordcraft) — [`licenses/creative-suite/wordcraft/`](licenses/creative-suite/wordcraft/)
10. **SoundCraft (`soundcraft`):** [storytold/soundcraft](https://github.com/storytold/soundcraft) — [`licenses/creative-suite/soundcraft/`](licenses/creative-suite/soundcraft/)
11. **DeckCraft (`deckcraft`):** [storytold/deckcraft](https://github.com/storytold/deckcraft) — [`licenses/creative-suite/deckcraft/`](licenses/creative-suite/deckcraft/)
12. **CadCraft (`cadcraft`):** [storytold/cadcraft](https://github.com/storytold/cadcraft) — [`licenses/creative-suite/cadcraft/`](licenses/creative-suite/cadcraft/)
13. **GridCraft (`gridcraft`):** [storytold/gridcraft](https://github.com/storytold/gridcraft) — [`licenses/creative-suite/gridcraft/`](licenses/creative-suite/gridcraft/)
14. **TextureCraft (`texturecraft`):** [storytold/texturecraft](https://github.com/storytold/texturecraft) — [`licenses/creative-suite/texturecraft/`](licenses/creative-suite/texturecraft/)
15. **SolidCraft (`solidcraft`):** [tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft) (includes `THIRD-PARTY-LICENSES.txt`) — [`licenses/creative-suite/solidcraft/`](licenses/creative-suite/solidcraft/)

---

## Upstream Applications, Browser Layers & Extensions

### 1. DownFlow (`flowork-downflow`) — Superseded & Replaced (Sovereign Clean-Room)
- **Status:** **REPLACED & PURGED**. Fully rewritten from clean-room specifications into a pure native Rust crate (`crates/flowork-downflow`) under the **Apache-2.0** Flowork Sovereign License.
- **Original Upstream:** Formerly Mister Download Manager (Ahmed Nefzaoui, `GPL-3.0`). All legacy GPL binaries (`misterdownloadmanager`, `misterdownloadmanager-cli`, `misterdownloadmanager-mcp`, `misterdownloadmanager-nmhost`), bundled archives (`mdm-firefox.xpi`), and GPL notices have been purged.
- **Current License:** Apache License 2.0 (Flowork Sovereign Core Team). Full backwards-compatibility maintained with Chromium Native Messaging protocol and MCP server.

### 2. Audacity 4 Portable (`v4.0.2`)
- **Authors:** Muse Group / The Audacity Team and contributors ([audacity/audacity](https://github.com/audacity/audacity)).
- **License:** GNU General Public License v3.0 (`GPL-3.0-only`, individual source modules `GPL-2.0+`, docs `CC-BY-3.0`).
- **Bundled Libraries:** 22 audio/UI libraries (`crashpad_handler`, `expat`, `flac`, `freetype`, `harfbuzz`, `lame`, `libid3tag`, `libpng`, `libsndfile`, `mpg123`, `ogg`, `opus`, `opusfile`, `portaudio`, `sbsms`, `soundtouch`, `soxr`, `twolame`, `vorbis`, `wavpack`, `wxwidgets`, `zlib`) + Debian runtime shared library copyrights.
- **Archived License Files:** [`licenses/audacity/`](licenses/audacity/)

### 3. uBlock Origin (`uBlock0.chromium`)
- **Author:** Raymond Hill (`gorhill`) and contributors ([gorhill/uBlock](https://github.com/gorhill/uBlock)).
- **License:** GNU General Public License v3.0 (`GPL-3.0`), plus bundled `Inter` (OFL-1.1), `Metropolis` (Unlicense), `FontAwesome`, `CodeMirror` (MIT), `csstree` (MIT), `hsluv` (MIT), `js-beautify` (MIT), `urlhaus-filter`.
- **Archived License Files:** [`licenses/uBlock0.chromium/`](licenses/uBlock0.chromium/)

### 4. Camoufox Anti-Detect Browser Engine (`v0.5.9`)
- **Author:** Daijro and contributors ([daijro/camoufox](https://github.com/daijro/camoufox)).
- **License:** `MIT` & Mozilla Public License 2.0 (`MPL-2.0`), plus bundled Python runtime dependencies (`playwright`, `fpgen`, `numpy`, `orjson`, `httpx`, `aiohttp`, `geoip2`, `maxminddb`, `requests`, `rich`, `certifi`, `zstandard`, etc.).
- **Archived License Files:** [`licenses/camoufox/`](licenses/camoufox/)

### 5. CutVii & Bundled FFmpeg + Fonts
- **Author:** Zidni Ryi & CutVii Contributors (`cutvii`), plus FFmpeg 9.0.2 (`ffmpeg.org`, BtbN / Martin Riedl static builds).
- **Licenses:** `MIT` (CutVii), **GNU GPL-3.0-or-later** (FFmpeg), and 38 embedded Google Fonts (`OFL-1.1` / `Apache-2.0`).
- **Archived License Files:** [`licenses/cutvii/`](licenses/cutvii/) & [`licenses/ffmpeg/copyright`](licenses/ffmpeg/copyright)

### 6. Craft Anything (`craft-anything-cli`)
- **License:** Dual Licensed under **Apache License 2.0** and **MIT License**.
- **Archived License Files:** [`licenses/craft-anything/`](licenses/craft-anything/)

### 7. Chromium & Electron Runtime Layers
- **Authors:** The Chromium Authors, Google LLC, and OpenJS Foundation.
- **Licenses:** BSD 3-Clause, MIT, LGPL 2.1, and Apache 2.0.
- **Archived License Files:** [`licenses/chromium-electron/`](licenses/chromium-electron/) (`LICENSE.electron.txt` verbatim, plus lossless `gzip -9` archives of full `LICENSES.chromium.*.html` notices for `agent` and `openscreen`, verified by `CHECKSUMS.sha256`).

### 8. GPUTaskMan (Superseded & Replaced by First-Party Native Rust `flowork-taskman`)
- **Status:** **Superseded & Replaced (Sovereign Clean-Room)**.
- **Original Reference:** Scott Hanselman ([shanselman/gputaskman](https://github.com/shanselman/gputaskman)).
- **Current Runtime:** 100% native Rust clean-room implementation under `/opt/floworkos/crates/flowork-taskman/` (Licensed under **Apache-2.0**). All legacy Python runtimes, PSF licenses, and PyInstaller binaries have been purged from the active distribution.
- **Archived Upstream Notices (Historical Reference):** [`licenses/gputaskman/`](licenses/gputaskman/)

### 9. OpenScreen (`v2.2.2`)
- **Authors:** Etienne Lescot, Siddharth Vaddem, and OpenScreen Contributors ([getopenscreen/openscreen](https://github.com/getopenscreen/openscreen)).
- **License:** **MIT License** (`openscreen`), bundling BtbN FFmpeg n8.1.2 LGPL-shared (`LGPL-2.1-or-later`), PipeWire 1.0.5 capture headers (`MIT`), `web-demuxer` WASM (`MIT` + `LGPL-2.1-or-later`), `whisper.cpp` / `ggml` (`MIT`), MediaPipe Selfie Segmentation models (`Apache-2.0`), Kenney UI Audio (`CC0-1.0`), fonts Inter / Lora / Oswald / Caveat / IBM Plex Mono (`OFL-1.1`), and bundled Vite/npm + Rust compositor crate notices (`THIRD-PARTY-LICENSES.txt.gz`).
- **Archived License Files:** [`licenses/openscreen/`](licenses/openscreen/) & [`licenses/chromium-electron/LICENSES.chromium.openscreen.html.gz`](licenses/chromium-electron/LICENSES.chromium.openscreen.html.gz)

---

## CLI Utilities, Agent Skills & Desktop Themes

| Component | Upstream Project / Author | License | Archived License Path |
| :--- | :--- | :--- | :--- |
| **OpenCodeReview (`ocr` v1.13.7)** | Alibaba OpenCodeReview ([alibaba/open-code-review](https://github.com/alibaba/open-code-review)) | Apache-2.0 | [`licenses/open-code-review/LICENSE`](licenses/open-code-review/LICENSE) |
| **`yt-dlp` (v2026.10.26)** | yt-dlp Contributors ([yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)) | The Unlicense | [`licenses/yt-dlp/LICENSE`](licenses/yt-dlp/LICENSE) |
| **`uv`** | Astral Software Inc. ([astral-sh/uv](https://github.com/astral-sh/uv)) | MIT OR Apache-2.0 | [`licenses/uv/LICENSE-MIT`](licenses/uv/LICENSE-MIT) |
| **`edge-tts` (7.3.1), `tabulate` (0.10.0) & async HTTP deps** | `rany2/edge-tts`, `astanin/python-tabulate`, `aio-libs` | LGPL-3.0, MIT, Apache-2.0, PSF-2.0 | [`licenses/python-dist-packages/`](licenses/python-dist-packages/) |
| **Founder Suite Skill** | Jake Schincariol ([Jakeschincariol/founder-skill](https://github.com/Jakeschincariol/founder-skill)) | MIT | [`licenses/skills-founder-suite/NOTICE.md`](licenses/skills-founder-suite/NOTICE.md) |
| **Last30Days Skill** | `mvanhorn` ([mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)) with pure-Python `bird_x.py` X client | MIT | [`licenses/skills-last30days/`](licenses/skills-last30days/) |
| **WhiteSur Icon Theme, Cursors & GTK Theme** | Vince Liuice ([vinceliuice/WhiteSur-icon-theme](https://github.com/vinceliuice/WhiteSur-icon-theme)) | GPL-3.0 | [`licenses/whitesur-theme/COPYING`](licenses/whitesur-theme/COPYING) |

---

## Compliance & Freedom to Inspect

In compliance with **GPL-2.0**, **GPL-3.0**, **AGPL-3.0**, **LGPL-2.1/3.0**, **Apache-2.0**, **MPL-2.0**, **BSD-3-Clause**, **MIT**, **OFL-1.1**, and **The Unlicense**, all users can freely inspect and verify the full verbatim third-party license texts archived in [`licenses/`](licenses/).
