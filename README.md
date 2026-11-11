<div align="center">

# 👑 Flowork OS
### The Sovereign AI-Native Linux Operating System
**Powered by Linux 7.3.0 Rust Kernel (Eust Kernel) • Autonomous Desktop AI Agent • 320+ Clean-Room Reverse Engineering Tools • Sovereign Quantum Glass HUD**

[![Kernel](https://img.shields.io/badge/Kernel-Linux%207.3.0%20Rust-00ff66.svg?style=for-the-badge&logo=linux&logoColor=black)](https://github.com/flowork-os/flowork-os/releases/tag/v1.0.1)
[![Release](https://img.shields.io/badge/Release-v1.0.1%20Official%20ISO-00f2fe.svg?style=for-the-badge&logo=github&logoColor=black)](https://github.com/flowork-os/flowork-os/releases/tag/v1.0.1)
[![Architecture](https://img.shields.io/badge/Arch-x86__64%20Preempt%20Dynamic-7928ca.svg?style=for-the-badge&logo=rust&logoColor=white)]()
[![Security](https://img.shields.io/badge/Security-Landlock%20LSM%20Pure-ff0080.svg?style=for-the-badge)]()
[![Kernel License](https://img.shields.io/badge/Kernel%20License-GPL--2.0-blue.svg?style=for-the-badge&logo=gnu)](https://github.com/Rust-for-Linux/linux)
[![OS License](https://img.shields.io/badge/OS%20License-GPL--3.0-yellow.svg?style=for-the-badge&logo=gnu)]()

[**🌐 Official Website**](https://floworkos.com) • [**📥 Download Official ISO (v1.0.1)**](https://github.com/flowork-os/flowork-os/releases/tag/v1.0.1) • [**📖 Architecture Spec**](core/ARCHITECT.md) • [**⚡ All Releases (v1.0.1 / v1.0.0)**](https://github.com/flowork-os/flowork-os/releases)

---
</div>

> **“FLOWORK IS NOT AN APPLICATION ON LINUX; FLOWORK IS LINUX ITSELF.”**  
> Flowork OS is an open-source, sovereign, AI-native operating system where autonomous AI reasoning is directly fused into the Linux kernel and userspace runtime. It eliminates SaaS dependencies, protects privacy via Landlock LSM sandboxing, and provides automated self-evolving agent loops.

---

## ⚡ Quick Download & Flash Guide (Official ISO v1.0.1)

Flowork OS `v1.0.1` is a **hardened, physically USB boot-verified hybrid live image** compatible with both **Legacy BIOS** and **Modern UEFI (Secure Boot Supported)** across 64-bit Intel and AMD systems (previous [`v1.0.0` archive](https://github.com/flowork-os/flowork-os/releases/tag/v1.0.0) remains preserved intact).

📦 **Download the Official ISO Parts (5.8 GiB / 6.24 GB Total):**  
👉 **[Download Flowork OS v1.0.1 Release Assets](https://github.com/flowork-os/flowork-os/releases/tag/v1.0.1)**

| File Asset | Size | Description |
| :--- | :---: | :--- |
| **`flowork-os-v1.0.1-amd64.iso.00.part`** | 1.76 GiB | Hybrid ISO Archive Part 1 |
| **`flowork-os-v1.0.1-amd64.iso.01.part`** | 1.76 GiB | Hybrid ISO Archive Part 2 |
| **`flowork-os-v1.0.1-amd64.iso.02.part`** | 1.76 GiB | Hybrid ISO Archive Part 3 |
| **`flowork-os-v1.0.1-amd64.iso.03.part`** | 548 MiB | Hybrid ISO Archive Part 4 |
| **`flowork-os-v1.0.1-amd64.iso.sha256`** | 94 B | Authoritative SHA-256 Checksum |
| **`join-iso.bat`** | 598 B | Windows 1-Click Reassembly Script |
| **`join-iso.sh`** | 465 B | Linux / macOS 1-Click Reassembly Script |
| **`README.txt`** | 663 B | Quick flashing cheat sheet |

### 🔨 1-Click Reassembly & Verification

#### Windows:
1. Download all parts into the same folder.
2. Double-click **`join-iso.bat`**. It will instantly produce `flowork-os-v1.0.1-amd64.iso`.
3. Open **[Rufus](https://rufus.ie)**, select your USB drive (min 8 GB), choose `flowork-os-v1.0.1-amd64.iso`, set Partition Scheme to **MBR**, and click **START**.

#### Linux / macOS:
```bash
# 1. Reassemble and verify checksum
bash join-iso.sh

# 2. Flash to USB flash drive (replace /dev/sdX with your USB drive)
sudo dd if=flowork-os-v1.0.1-amd64.iso of=/dev/sdX bs=4M oflag=direct conv=fsync status=progress
```

🔒 **Official SHA-256 Integrity Hash:**  
`501771af269db261d6afe9c9c4a25a3e859e2d1e3a6f825b7a159145adbac0c5`

---

## 🌟 Core Pillars & Key Features

### ��� 1. Linux 7.3.0 Rust Kernel (Eust Kernel)
- **Ring-0 Memory Safety:** Critical kernel abstractions, drivers, and scheduler modules authored in 100% Safe Rust.
- **Landlock LSM Hardened:** Kernel-level sandbox confining agent tool executions to strict territorial bounds without root escalation.
- **Dynamic Preemption (`PREEMPT_DYNAMIC`):** Ultra-low desktop latency tailored for real-time AI inference and 120Hz display refresh rates.

### 🧠 2. Mr. Flow: Autonomous Sovereign AI Agent
- **Full Operational Authority:** Autonomously self-evolves, synthesizes tools via Dynamic Tool Foundry, authors subagents, and repairs system components.
- **Direct Vision-Action Actuation:** Zero-copy DRM framebuffer perception and native `uinput` virtual HID events for instant GUI control without fragile cloud vision models.
- **Zero Token Bloat Invariant:** Uses just-in-time passive triggers and native compiled Rust rule sensors (`rules/.bin/*`) to ensure prompts remain razor-sharp (0 token waste on quiescent turns).

### 🔬 3. Built-in Clean-Room Reverse Engineering (`craft-anything-cli`)
- **320+ Inspection Tools:** Complete native suite for inspecting binaries (ELF, PE, Mach-O), Android APK/DEX, Electron ASAR, JavaScript Webpack bundles, and game archives (Unity, Unreal).
- **Zero Prompt Bloat:** CLI-driven engine executing on-demand without spamming AI context with hundreds of static tool schemas.

### 🌐 4. Google Agent Skills Sovereign Navigator
- **100+ On-Demand Skills:** Instant lookup and execution for official Google Cloud, Gemini API, GKE AI inference, BigQuery, and Safe Rust migration workflows.
- **Air-Gapped & Resilient:** Cached offline catalog with automatic multi-tier fallback (local cache -> curl -> unverified SSL).

### 🛡️ 5. Flowork Stealth Anti-Detect Browser
- **Native C++ Camoufox Engine:** Built-in hardware fingerprint spoofing (WebGL, Canvas, audio, fonts) replacing commercial paid tools like AdsPower or Multilogin.
- **Dual-Shield Ad Eradication:** System-wide DNS blackhole (77,700+ domains) combined with in-DOM uBlock Origin for 100% video ad eradication (YouTube, Twitch).

### 🔄 6. Autonomous Git-Stream Rolling OTA Updates
- **One-Command Updating:** Built-in background timer (`flowork-updater.timer`) checks remote git HEAD in sub-milliseconds.
- **Anti-Brick Health Checks:** Automatically validates Python syntax and binary integrity before applying updates, with instant rollback if validation fails.
```bash
flowork-update --check    # Check for available OTA updates
sudo flowork-update --force  # Force instant sync
```

---

## 📊 Comparison Matrix

| Capability | Traditional Linux (Ubuntu/Debian) | Commercial OS (Windows/macOS) | Flowork OS |
| :--- | :---: | :---: | :---: |
| **Kernel Core** | Standard C Monolithic | Proprietary Closed Kernel | **Linux 7.3.0 Safe Rust (Eust)** |
| **Native AI Agent** | ❌ None (Third-party app) | ⚠️ Cloud Copilot (Telemetry) | **👑 Sovereign Local/Remote Mr. Flow** |
| **Prompt Overhead** | ❌ N/A | ❌ Rigid Cloud Prompts | **⚡ Anti-Bloat Law (0 Token Waste)** |
| **Reverse Engineering** | Requires manual installs | Proprietary Paid Tools | **🔬 320+ Built-in Tools (`craft-anything`)** |
| **Ad & Tracker Shield** | Browser extension only | Built-in OS Telemetry & Ads | **🛡️ Dual-Shield (DNS + DOM Eradication)** |
| **OTA System Updating** | APT package managers | Forcible Reboot Updates | **🔄 Git-Stream Three-Tier Atomic Sync** |
| **Desktop Aesthetics** | Standard Themes | Static Windows UI | **🪟 Obsidian Quantum Glass (0.60 HUD)** |

---


---

## 🎨 Built-in Pure Rust Creative Suite (15 Native Apps)

Flowork OS bundles a comprehensive, professional creative suite built from scratch in **pure, memory-safe Rust with GPU hardware acceleration** (powered by Storytold & Tangency Labs). All applications are fully integrated into the desktop shell, Start Menu, and Launchpad:

| Application | Category | Description | Upstream |
| :--- | :--- | :--- | :--- |
| **PhotoCraft** | Raster Graphics | Professional photo editor & raster manipulation studio | [storytold/photocraft](https://github.com/storytold/photocraft) |
| **VectorCraft** | Vector Graphics | SVG design & high-precision vector illustration | [storytold/vectorcraft](https://github.com/storytold/vectorcraft) |
| **FilmCraft** | Video Editing | Non-linear video editor & multi-track timeline compositor | [storytold/filmcraft](https://github.com/storytold/filmcraft) |
| **LightCraft** | Photography | RAW photo developer & non-destructive color darkroom | [storytold/lightcraft](https://github.com/storytold/lightcraft) |
| **PdfCraft** | Publishing | Ultra-fast PDF document editor, annotator, & reader | [storytold/pdfcraft](https://github.com/storytold/pdfcraft) |
| **EffectCraft** | VFX & Motion | Visual effects, particle systems, & motion graphics studio | [storytold/effectcraft](https://github.com/storytold/effectcraft) |
| **DesignCraft** | Graphic Design | Layout, brand asset creator, & desktop publishing studio | [storytold/designcraft](https://github.com/storytold/designcraft) |
| **FigCraft** | UI/UX Prototyping | Vector interface designer & interactive prototype builder | [storytold/figcraft](https://github.com/storytold/figcraft) |
| **WordCraft** | Word Processing | Typography workbench & document publishing editor | [storytold/wordcraft](https://github.com/storytold/wordcraft) |
| **SoundCraft** | Digital Audio (DAW)| Multi-track audio workstation, sound design, & synthesizer | [storytold/soundcraft](https://github.com/storytold/soundcraft) |
| **DeckCraft** | Presentations | Interactive pitch deck & presentation slide architect | [storytold/deckcraft](https://github.com/storytold/deckcraft) |
| **CadCraft** | Parametric CAD | 2D/3D Computer-Aided Design & engineering modeler | [storytold/cadcraft](https://github.com/storytold/cadcraft) |
| **GridCraft** | Spreadsheets | Reactive computation spreadsheet & data analytics suite | [storytold/gridcraft](https://github.com/storytold/gridcraft) |
| **TextureCraft** | PBR Materials | Procedural PBR material generator & 3D texture synthesizer | [storytold/texturecraft](https://github.com/storytold/texturecraft) |
| **SolidCraft** | Mechanical CAD | Precision boundary representation (B-Rep) solid CAD | [tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft) |

## 🏛️ System Architecture Layers

The repository is structured into atomic layers reflecting the live OS layout:

```
flowork-os/
├── core/                     # /opt/floworkos (Core AI agent, tools, skills, session)
│   ├── apps/                 # Sovereign applications (craft-anything, flowork-stealth)
│   ├── bin/                  # Core executable binaries (mrflow, flowork-update)
│   ├── skills/               # Sovereign skills (google-skills-navigator, clean-room)
│   ├── system_promp/         # Prompts engine, passive triggers, and Rust rules
│   └── tools/                # Dynamic Tool Foundry and native system tools
├── skel/                     # /etc/skel (Canonical user configuration skeleton)
│   ├── .config/              # Alacritty obsidian HUD, Plank dock, XFCE4 glass panel
│   └── Desktop/              # Sovereign desktop launchers
├── system/                   # Host overlays (systemd services, LightDM autologin, bin)
├── kernel/                   # Linux 7.3.0 Rust Kernel packages and initramfs builder
├── packages/                 # Authoritative installed-packages.list manifest
└── iso-builder/              # Bootable ISO generation recipe and boot-skeleton
    └── boot-skeleton/        # Tested UEFI (BOOTX64.EFI) and BIOS (isolinux) tree
```

---

## ⌨️ Desktop Shortcuts & Productivity Cheat Sheet

| Shortcut | Action | Subsystem |
| :--- | :--- | :--- |
| `Super + A` / `F4` | Open Sovereign Launchpad (Card Drawer) | `flowork-launchpad.py` |
| `Super + Space` | Spotlight Application & Command Search | `spotlight.rasi` / Rofi |
| `Alt + F1` / `Super` | Open Start Menu (Whisker Glass Menu) | `xfce4-popup-whiskermenu` |
| `Super + Return` | Open Alacritty Obsidian Glass Terminal (0.60) | Alacritty HUD |
| Hover Right Edge | Open Mr. Flow AI Autonomous Assistant | `mrflow-sidebar.py` |

---

## 💻 System Requirements

- **Processor:** 64-bit x86_64 CPU (Intel Core i3/i5/i7/i9 or AMD Ryzen).
- **Memory (RAM):** 4 GB minimum (8 GB+ recommended for large AI agent pipelines).
- **Storage:** 16 GB free space (SSD recommended).
- **Boot Firmware:** Compatible with both **Legacy BIOS (MBR)** and **UEFI (64-bit)** with Secure Boot ON or OFF.
- **Installation Media:** USB Flash Drive (8 GB or larger).

---


---

## ⚖️ Open Source Licenses & Upstream Attribution

Flowork OS stands on the shoulders of giants. We deeply respect and honor the work of open-source authors and maintainers.  
All collected upstream licenses, notices, and attributions are consolidated publicly in the repository under [**`licenses/`**](licenses/) and indexed in [**`THIRD_PARTY_LICENSES.md`**](THIRD_PARTY_LICENSES.md):
- **Linux Kernel (`Rust-for-Linux`) & Zstandard:** `GPL-2.0 WITH Linux-syscall-note`, `BSD-3-Clause OR GPL-2.0`
- **Storytold / Tangency Pure Rust Creative Suite & `craft-anything`:** Dual `Apache-2.0 OR MIT`
- **Audacity 4 Portable & DownFlow:** `GPL-3.0` (`+ bundled audio/UI notices`)
- **Recordly:** `AGPL-3.0` (`webadderallorg/Recordly`)
- **uBlock Origin & WhiteSur Theme:** `GPL-3.0`
- **Camoufox Engine:** `MPL-2.0` / `MIT`
- **CutVii & Bundled FFmpeg:** `MIT` (CutVii) / `GPL-3.0-or-later` (FFmpeg)
- **CLI & Agent Toolchain:** `Mr. Flow` (Native Sovereign Rust Engine, `MIT`), `agent-browser` (`Apache-2.0`), `agent-desktop` (`Apache-2.0`), `open-code-review` (`Apache-2.0`), `Node.js` (`MIT`), `npm` (`Artistic-2.0`), `corepack` (`MIT`), `yt-dlp` (`Unlicense`), `uv` (`MIT OR Apache-2.0`), `edge-tts` (`LGPL-3.0`)
- **Chromium & Electron Core:** `BSD-3-Clause`, `LGPL-2.1`, `Apache-2.0`, and `MIT`

👉 **Detailed Attribution Table:** [**`THIRD_PARTY_LICENSES.md`**](THIRD_PARTY_LICENSES.md) • [**`licenses/` Archive**](licenses/)

## 🤝 Community & Contributing

Flowork OS is developed autonomously under the direction of **Architect AWENKAUDICO** and sovereign agent **Mr. Flow**.  
We welcome pull requests, custom tools, and kernel enhancements!

1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/SovereignEnhancement`).
3. Commit your Changes (`git commit -m "feat: Add sovereign enhancement"`).
4. Push to the Branch (`git push origin feature/SovereignEnhancement`).
5. Open a Pull Request.

---

<div align="center">

**Flowork OS — The Autonomous Future of Personal Computing.**  
*Crafted with 100% Safe Rust, Sovereign Intelligence, and Zero Prompt Bloat.*

</div>
