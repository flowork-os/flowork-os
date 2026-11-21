<!--
  Flowork OS: The Sovereign Autonomous AI Linux Operating System (Linux 7.3.0 Rust).
  Features built-in Mr. Flow autonomous AI agent, native Android APK runner, Blender 3D AI automation,
  60s video shorts creation foundry, 320+ reverse engineering tools, anti-detect browser, and Windows apps compatibility.
  100% Free, Private, Telemetry-Free, and Open Source.
-->

<div align="center">

<img src="assets/flowork-hero-cover.jpg" width="100%" alt="Flowork OS: The Autonomous AI Operating System. Sovereign desktop running native Android APK mobile apps, AI-driven Blender 3D viewport, and translucent glass terminal HUD with Exit Code 0." />

<h1 align="center">Autonomous AI Operating System (AI OS)</h1>
<p align="center"><b>The Open-Source Desktop AI Co-Pilot That Controls Your PC, Runs Android APKs, Automates Blender 3D, and Boots from USB</b></p>
<p align="center"><i>Powered by Flowork OS · 100% Free, Private, and Telemetry-Free Sovereign Desktop</i></p>

<p align="center">
  <a href="#-quick-test-drive-live-usb-in-5-minutes"><b>⚡ Try Live USB</b></a> ·
  <a href="#-why-flowork-os-the-real-problems-we-solve"><b>🎯 Why Flowork OS?</b></a> ·
  <a href="#-killer-superpowers-you-wont-find-in-any-other-os"><b>🚀 7 Superpowers</b></a> ·
  <a href="#-download-official-live-iso-v110"><b>📥 Download ISO</b></a> ·
  <a href="#%EF%B8%8F-productivity-shortcuts"><b>⌨️ Shortcuts</b></a> ·
  <a href="#-frequently-asked-questions-faq"><b>❓ FAQ</b></a>
</p>

[![Release](https://img.shields.io/badge/Release-v1.1.0%20Official%20ISO-00f2fe.svg?style=for-the-badge&logo=github&logoColor=black)](https://github.com/flowork-os/flowork-os/releases)
[![Live USB](https://img.shields.io/badge/Live%20USB-Plug%20%26%20Play-00ff66.svg?style=for-the-badge&logo=linux&logoColor=black)](https://github.com/flowork-os/flowork-os/releases)
[![Android APK](https://img.shields.io/badge/Android%20Subsystem-Native%20APK-34d399.svg?style=for-the-badge&logo=android&logoColor=white)](https://github.com/flowork-os/flowork-os)
[![Blender 3D](https://img.shields.io/badge/Blender%203D-AI%20Automated-ea580c.svg?style=for-the-badge&logo=blender&logoColor=white)](https://github.com/flowork-os/flowork-os)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Telemetry%20Free-ff0080.svg?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-GPL--3.0-yellow.svg?style=for-the-badge&logo=gnu)]()

</div>

---

> **“A Chatbot only gives you advice. Flowork OS actually does the work.”**  
> Instead of spending hours juggling terminal commands, broken Python environments, expensive AI subscriptions, bloated emulators, and heavy operating systems, Flowork OS fuses an autonomous AI agent directly into your desktop environment.

---

## 🎯 Why Flowork OS? (The Real Problems We Solve)

| The Old, Frustrating Way | The Flowork OS Way |
| :--- | :--- |
| ❌ **Chatbots That Only Talk:** You ask a chatbot for code, copy it to your editor, get an error, paste it back, repeat 20 times. | ✅ **Autonomous Hands-On Execution:** Tell Mr. Flow *"Build this app"* or *"Fix my Wi-Fi"*. The AI creates files, executes terminal commands, inspects outputs, and self-corrects until it works. |
| ❌ **Android Emulators Are Slow & Full of Ads:** Running Android apps on PC means installing 5GB emulators (BlueStacks, Nox) that lag your CPU and spam notifications. | ✅ **Native Android APK Subsystem & AI Control:** Run `.apk` files directly on your desktop with zero bloat. Plus, Mr. Flow can automate, tap, and control Android apps programmatically. |
| ❌ **3D Modeling & Animation Learning Curve:** Using Blender requires months of learning complex nodes, keyframes, and python scripts. | ✅ **AI-Driven 3D Studio (Blender Live):** Instruct Mr. Flow in plain language to model 3D assets, generate procedural geometry nodes, set up PBR materials, and render photo-real scenes. |
| ❌ **Expensive AI Subscriptions & Rate Limits:** Paying $20–$100/month for cloud AI tools that cut you off mid-task when you hit a rate limit. | ✅ **Smart Multi-Account Failover:** Connect your free or developer keys once into a local encrypted vault. Flowork automatically rotates accounts on the fly so your tasks never stall. |
| ❌ **Manual Video & Content Production:** Creating animated educational videos or YouTube Shorts takes 3–4 hours of scripting, voiceover, keyframing, and rendering. | ✅ **1-Click Video Foundry:** Feed it any GitHub repository link or topic. In 60 seconds, Flowork generates the script, voiceover, animated stickman visuals, subtitles, and renders a 1080p video ready to upload. |
| ❌ **Windows App Lock-In:** Stuck on Windows because of specific `.exe` software (like FL Studio or specialized tools). | ✅ **Seamless Windows Apps & Drive Access:** Run Windows applications out of the box with pre-configured wine environments, and access all your existing Windows drives without formatting. |

---

## 🚀 Killer Superpowers You Won't Find in Any Other OS

### 1. 🤖 The Truly Autonomous Co-Pilot (Hands-On Execution & Self-Healing)
* **The Pain:** Web-based AI chatbots (ChatGPT, Claude, Gemini Web) are confined inside a browser tab. They cannot create files on your hard drive, run tests, or touch your desktop applications. When code fails, you are stuck manually copying logs back and forth.
* **The Flowork Solution:** Mr. Flow has direct system and GUI actuation authority (`desktop_actuator`, `run_command`, `write_to_file`):
  * **Self-Healing Sentinel:** If a build command or script throws an error, Mr. Flow automatically inspects the terminal traceback, edits the file, and retries recursively until it passes with Exit Code 0.
  * **Dynamic Tool Foundry:** When confronted with a novel problem, Mr. Flow can synthesize, compile, and execute brand-new tools on the fly.
  * **Desktop Automation:** Interacts directly with windows, clicks buttons, and automates repetitive administrative desktop workflows.

### 2. 📱 Native Android Subsystem & AI App Control (`flowork-apk` & `apk-actuator`)
* **The Pain:** Running mobile apps on a PC usually requires installing heavy third-party emulators (BlueStacks, Nox, LDPlayer) that consume 6GB+ RAM, install unwanted sponsored apps, and run sluggishly. Moreover, there is no way for an AI agent to interact with them.
* **The Flowork Solution:**
  * **Run APKs Directly on Desktop:** Install, launch, and manage Android `.apk` packages natively via `flowork-apk` without virtualized emulator bloatware.
  * **AI App Automation (`apk-actuator`):** Mr. Flow can directly navigate and automate Android applications (TikTok, CapCut, Shopee, Instagram, etc.). He can tap UI elements, swipe, type inputs, extract mobile data, and execute mobile automation sequences completely hands-free.

### 3. 🎨 AI-Driven 3D Studio via Blender Live (`blender-live` & `blender-mastering`)
* **The Pain:** Creating 3D scenes, procedural meshes, character rigs, and photorealistic renders in Blender takes years of technical expertise. Doing it programmatically requires complex `bpy` Python scripting.
* **The Flowork Solution:**
  * **Live Blender IPC Bridge (`blender-live`):** Mr. Flow connects directly to Blender's runtime engine via a real-time command socket.
  * **Automated 3D Generation:** Simply ask Mr. Flow to build 3D environments, configure procedural geometry nodes, set up PBR materials, rig models, and trigger high-speed EEVEE or Cycles GPU hardware renders automatically.

### 4. 🎬 Automated 60-Second Video Creation Foundry (`githubtoyoutube`)
* **The Pain:** Turning open-source projects or educational topics into engaging short-form video content (YouTube Shorts, TikTok, Reels) normally takes 3 to 5 hours of scriptwriting, voice recording, asset sourcing, subtitle alignment, and rendering.
* **The Flowork Solution:**
  * Provide a single GitHub repository URL or topic name.
  * In under **60 seconds**, Flowork OS autonomously:
    1. Analyzes the codebase and crafts a viral, high-retention narration script.
    2. Synthesizes natural, human-quality voice narration.
    3. Procedurally animates stickman cartoon characters and explanatory UI cards frame-by-frame.
    4. Burns precise, word-by-word synchronized color subtitles.
    5. Masters and mixes background audio (`kamidi-mastering`).
    6. Hardware-encodes a vertical 1080x1920 MP4 via GPU NVENC acceleration.
    7. Produces an algorithmic SEO package (clickable titles, descriptions, hashtags, and a 12-tile contact sheet thumbnail).

### 5. 🪟 Windows Apps & Zero-Risk Drive Integration (`wine-staging` & NTFS Access)
* **The Pain:** Switching to a new OS often means losing access to your favorite Windows software or worrying about losing your existing Windows files.
* **The Flowork Solution:**
  * **Built-in Windows App Runtime:** Pre-tuned `wine-staging` environment ready to run `.exe` software and digital audio workstations (like FL Studio) out of the box with low-latency audio.
  * **Passwordless Windows Drive Access:** When running in Live USB mode, Flowork OS automatically detects and mounts your existing Windows NTFS and exFAT partitions. You can edit your Windows documents, copy files, and work on your projects without modifying your Windows installation.

### 6. ⚡ Zero-Setup & Unlimited Multi-Account AI (Free from Subscriptions & Limits)
* **The Pain:** Setting up open-source AI agents on Windows or Ubuntu requires hours of dependency debugging (conflicting Python wheels, CUDA version hell, Docker overhead). Meanwhile, paid SaaS subscriptions enforce strict hourly caps.
* **The Flowork Solution:**
  * **Instant Zero-Setup:** Boots ready to roll. Zero virtualenv creation, zero CUDA driver debugging.
  * **Multi-Account Failover Vault (`flowork-connector`):** Securely stores multiple free or developer API accounts in a local encrypted vault. Flowork monitors latency and rate limits, continuously prioritizing healthy accounts. When an account enters a cooldown window, it silently rotates to the next account, delivering uninterrupted, high-speed AI assistance without recurring monthly bills.

### 7. 🔬 320+ Tool Reverse Engineering & Anti-Detect Stealth Browser
* **The Pain:** Analyzing an Android application, inspecting a binary, or managing multiple web identities usually requires expensive anti-detect browsers ($50–$200/mo) and dozens of shady tools. Everyday browsing is constantly interrupted by unskippable video ads.
* **The Flowork Solution:**
  * **320+ Clean-Room Inspection Tools (`craft-anything`):** Instantly decompile APKs, inspect ELF/PE binaries, unpack Electron ASAR, and extract Unity/Unreal game assets.
  * **Hardware Fingerprint Spoofing (`flowork-stealth`):** Camoufox-powered engine spoofs WebGL, Canvas, system audio, and fonts at the OS level.
  * **100% Video Ad Eradication:** System-wide kernel DNS filter and browser blocker wipe out video ads on YouTube and Twitch completely.

---

## ⚡ Quick Test Drive (Live USB in 5 Minutes)

> [!TIP]
> **You do NOT need to wipe your hard drive or delete Windows/macOS!**  
> Flowork OS runs directly from a USB flash drive in **Live Mode**. Your existing files, Windows installation, and personal documents remain 100% untouched.

```mermaid
graph LR
    A[1. Download ISO Parts] --> B[2. Run 1-Click Reassembly]
    B --> C[3. Flash to USB Stick]
    C --> D[4. Boot & Enjoy Sovereign AI]
```

### 📥 3-Step Quick Start:

1. **Download the ISO Release Parts:**  
   👉 **[Download Flowork OS v1.1.0 ISO](https://github.com/flowork-os/flowork-os/releases)**

2. **Reassemble the ISO (1-Click):**
   * **Windows:** Put all parts in one folder and double-click `join-iso.bat`.
   * **Linux / Mac:** Run `bash join-iso.sh` in the terminal.

3. **Flash to USB Flashdrive (min 8 GB):**
   * Open **[Rufus](https://rufus.ie)** (Windows) or **[BalenaEtcher](https://etcher.balena.io)** (Mac/Linux).
   * Select your USB drive and the reassembled `.iso` file, then click **Start**.
   * Restart your computer, press your boot key (`F12`, `F11`, or `Esc`), select your USB drive, and boot straight into Flowork OS!

---

## ⌨️ Productivity Shortcuts

| Shortcut | Action | Description |
| :--- | :--- | :--- |
| **`Super + Space`** | **Spotlight Search** | Instant application launcher and system command finder |
| **`Super + A` / `F4`** | **Sovereign Launchpad** | Visual card drawer showcasing all installed tools & creative apps |
| **`Super + Return`** | **Glass Terminal** | Ultra-low latency translucent terminal HUD |
| **`Super` / `Alt + F1`**| **Start Menu** | Clean, searchable application menu |
| **Hover Right Edge** | **Mr. Flow AI Drawer** | Instant sidebar to give natural language instructions to your AI co-pilot |

---

## 💻 System Requirements

* **Processor:** 64-bit x86_64 CPU (Intel Core i3/i5/i7/i9 or AMD Ryzen).
* **RAM:** 4 GB minimum (8 GB+ recommended for heavy multitasking and local pipelines).
* **Storage:** 16 GB free space (only if you choose to install permanently; 0 GB needed for Live USB mode).
* **Boot Compatibility:** Compatible with **Legacy BIOS (MBR)** and **Modern UEFI (Secure Boot supported)**.

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>Will booting Flowork OS erase my Windows files or personal photos?</b></summary>
<br>
<b>No.</b> When you boot from the USB flash drive, Flowork OS runs entirely in RAM (Live Mode). It does not touch, modify, or format your internal hard drive unless you explicitly open the Calamares Installer and choose to install it.
</details>

<details>
<summary><b>Can I run my Android apps and Windows software on Flowork OS?</b></summary>
<br>
<b>Yes.</b> Flowork OS features a native Android Subsystem (<code>flowork-apk</code>) to run and automate APKs without heavy emulators, as well as built-in Wine compatibility to run Windows <code>.exe</code> software directly.
</details>

<details>
<summary><b>Do I need an expensive high-end NVIDIA GPU to run Mr. Flow?</b></summary>
<br>
<b>No.</b> Flowork OS is engineered with ultra-lightweight native binaries. The system AI co-pilot connects seamlessly to lightweight endpoints or free API tiers without requiring a $2,000 graphics card.
</details>

<details>
<summary><b>Is Flowork OS really 100% free and open source?</b></summary>
<br>
<b>Yes.</b> Flowork OS is built entirely under open-source licenses (GPL-3.0 / MIT / Apache-2.0). There are zero paywalls, zero subscription tiers, and zero locked features.
</details>

---

<div align="center">

**Flowork OS — The Autonomous Future of Personal Computing.**  
*Freedom, Privacy, and Built-In Intelligence.*

[**⭐ Star this repo on GitHub**](https://github.com/flowork-os/flowork-os) • [**💬 Join the Community**](https://github.com/flowork-os/flowork-os/discussions)

</div>
