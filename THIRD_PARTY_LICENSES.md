# ⚖️ Third-Party Software Notices & Open Source Attribution

Flowork OS deeply values, respects, and attributes all open-source software, upstream authors, libraries, and kernel engineers who make our sovereign operating system possible.

All original upstream **LICENSE**, **COPYING**, and **README** files are strictly preserved alongside their respective applications and runtime binaries.

---

## 🐧 The Upstream Foundation: Linux Kernel & Rust-for-Linux

### 👑 Linux Kernel (Rust-for-Linux Subsystem)
- **Upstream Repository:** [https://github.com/Rust-for-Linux/linux](https://github.com/Rust-for-Linux/linux)
- **Original Authors & Maintainers:** Linus Torvalds, Greg Kroah-Hartman, Miguel Ojeda, Wedson Almeida Filho, and thousands of Linux & Rust-for-Linux kernel contributors.
- **Primary License:** **GNU General Public License v2.0 only with Linux Syscall Note (`GPL-2.0 WITH Linux-syscall-note`)**
- **Rust Bindings License:** Dual-licensed under **`GPL-2.0 OR Apache-2.0 OR MIT`** for core Rust infrastructure.
- **Local Kernel Packages:** Built and packaged into `/opt/floworkos/kernel/` (`linux-image-7.3.0-flowork-rust_amd64.deb`, `linux-headers-7.3.0-flowork-rust_amd64.deb`).
- **Our Tribute:** Flowork OS builds upon the pioneering work of the Rust-for-Linux community, integrating memory-safe drivers, Landlock LSM security sandboxing, and ultra-low latency preemption (`PREEMPT_DYNAMIC`).

---

## 🎨 Storytold & Tangency Labs Pure Rust Creative Suite

The complete next-generation creative workbench built from scratch in pure, memory-safe Rust with GPU hardware acceleration.
- **Original Authors & Maintainers:** Storytold, Tangency Labs, and open-source contributors.
- **Licenses:** Dual Licensed under **Apache License 2.0** and **MIT License**.
- **Embedded Fonts:** SIL Open Font License 1.1 (OFL-1.1).
- **Installed Native Applications:**
  1. **PhotoCraft (`photocraft`):** Photo & raster image editing studio ([storytold/photocraft](https://github.com/storytold/photocraft))
  2. **VectorCraft (`vectorcraft`):** Vector illustration & SVG studio ([storytold/vectorcraft](https://github.com/storytold/vectorcraft))
  3. **FilmCraft (`filmcraft`):** Non-linear video editing & timeline compositor ([storytold/filmcraft](https://github.com/storytold/filmcraft))
  4. **LightCraft (`lightcraft`):** RAW photo developer & color grading darkroom ([storytold/lightcraft](https://github.com/storytold/lightcraft))
  5. **PdfCraft (`pdfcraft`):** High-speed PDF document editor & publisher ([storytold/pdfcraft](https://github.com/storytold/pdfcraft))
  6. **EffectCraft (`effectcraft`):** Visual effects & motion graphics compositor ([storytold/effectcraft](https://github.com/storytold/effectcraft))
  7. **DesignCraft (`designcraft`):** Graphic design, layout, & brand asset studio ([storytold/designcraft](https://github.com/storytold/designcraft))
  8. **FigCraft (`figcraft`):** UI/UX interface design & component prototyping ([storytold/figcraft](https://github.com/storytold/figcraft))
  9. **WordCraft (`wordcraft`):** Document word processor & typography studio ([storytold/wordcraft](https://github.com/storytold/wordcraft))
  10. **SoundCraft (`soundcraft`):** Multi-track digital audio workstation (DAW) ([storytold/soundcraft](https://github.com/storytold/soundcraft))
  11. **DeckCraft (`deckcraft`):** Presentation slide architect & deck designer ([storytold/deckcraft](https://github.com/storytold/deckcraft))
  12. **CadCraft (`cadcraft`):** Parametric 2D/3D CAD & engineering modeler ([storytold/cadcraft](https://github.com/storytold/cadcraft))
  13. **GridCraft (`gridcraft`):** Reactive spreadsheet & data calculation studio ([storytold/gridcraft](https://github.com/storytold/gridcraft))
  14. **TextureCraft (`texturecraft`):** Procedural PBR material synthesizer ([storytold/texturecraft](https://github.com/storytold/texturecraft))
  15. **SolidCraft (`solidcraft`):** Solid B-Rep mechanical CAD modeler ([tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft))
- **Documentation & License Paths:** Preserved within each application under `/opt/floworkos/apps/<app_name>/share/doc/<app_name>/`.

---

## 📦 Upstream Applications & Tools

### 1. 🛡️ uBlock Origin (`uBlock0.chromium`)
- **Author:** Raymond Hill (gorhill) and contributors.
- **License:** GNU General Public License v3.0 (GPL-3.0)
- **Upstream Repository:** [https://github.com/gorhill/uBlock](https://github.com/gorhill/uBlock)
- **Local Documentation:** `/opt/floworkos/apps/uBlock0.chromium/LICENSE.txt`

### 2. 🦊 Camoufox Anti-Detect Browser Engine
- **Author:** Daijro and contributors.
- **License:** Mozilla Public License 2.0 (MPL-2.0) & MIT License
- **Upstream Repository:** [https://github.com/daijro/camoufox](https://github.com/daijro/camoufox)
- **Local Documentation:** `/opt/floworkos/apps/camoufox/venv/lib/python3.12/site-packages/camoufox-0.5.9.dist-info/licenses/LICENSE`

### 3. 🔬 Craft Anything (`craft-anything-cli`)
- **License:** Dual Licensed under **Apache License 2.0** and **MIT License**.
- **Local Documentation:** `/opt/floworkos/apps/craft-anything/share/doc/craft-anything/`

### 4. 🎬 Cutvii
- **Author:** Cutvii Open Source Contributors.
- **License:** MIT License
- **Local Documentation:** `/opt/floworkos/apps/cutvii/LICENSE` & `/opt/floworkos/apps/cutvii/README.md`

### 5. 🌐 Chromium & Electron Runtime Layers
- **Authors:** The Chromium Authors, Google LLC, and OpenJS Foundation.
- **Licenses:** BSD 3-Clause, MIT, LGPL 2.1, and Apache 2.0.
- **Local Documentation:** `/opt/floworkos/apps/agent/LICENSES.chromium.html`

---

## 🤝 Compliance & Freedom to Inspect

In compliance with the **GPL-2.0**, **GPL-3.0**, **LGPL**, **Apache 2.0**, **MPL-2.0**, and **MIT** licenses, all users are free to inspect, study, modify, and redistribute these components in accordance with their respective open-source licensing terms.
