# 👑 DiskCraft — Sovereign Storage & Disk Hygiene Suite for Flowork OS

## 1. Background & Motivation
Modern operating systems accumulate immense amounts of temporary caches, dangling container layers, package manager cache, build artifacts, browser data, and duplicate files. Traditional Linux cleanup tools (like BleachBit or manual shell scripts) are often risky, lack modern visual feedback (like interactive Treemap disk visualizations), or execute destructive commands without preview.
Inspired by the core architecture of **MangoDisk** (`harry0703/MangoDisk`), **DiskCraft** (`diskcraft`) is a native, sovereign disk hygiene utility engineered for **Flowork OS**. It implements a safety-first architecture, declarative rule scanning, fast hashing deduplication, interactive storage exploration, and real-time disk telemetry.

---

## 2. Scope & Key Features

### A. Deep Cleanup Engine (`cleanup`)
* **System & OS Caches:** `/var/cache/apt`, `/var/log`, systemd journal logs (`journalctl --vacuum-size`), `/tmp` stale sessions.
* **User & Application Caches:** `~/.cache` (thumbnails, fontconfig, IPC buffers), Trash (`~/.local/share/Trash`).
* **Browser Caches:** Google Chrome & Flowork Stealth (Camoufox profiles) cache, media caches, code caches.
* **Developer Build Artifacts:** `node_modules` (in selected workspaces), Rust `target/`, Python `__pycache__` & `.pyc`, Godot, CMake cache.
* **Strict Blacklist & Safety Guardrails:** Hard-coded protection preventing modification to `/boot`, `/lib`, `/usr/bin`, `/etc`, `/opt/floworkos/kernel*`, active process files, and active session locks.
* **Simulation Mode (Dry-Run):** Calculate reclaimable space and file list before any deletion.

### B. Storage Visualizer & Large Files Treemap (`treemap`)
* Recursive filesystem capacity mapping.
* Visual interactive Treemap / bar distribution showing partitions, top folders, and huge files (>100MB).
* Direct drill-down navigation and selective inspect/reveal.

### C. Smart Duplicate File Finder (`duplicates`)
* Multi-stage hash comparison (Size match -> Header 4KB fast hash -> Full BLAKE3 / SHA-256 hash).
* Safe smart selection: guarantees that at least one original file remains strictly untouched.
* Side-by-side duplicate preview.

### D. Real-Time Telemetry & Disk Health (`telemetry`)
* Live I/O throughput (read/write MB/s).
* Partition mount table, total/used/free space, and inode consumption.

---

## 3. Architecture & Tech Stack

* **Platform Root:** `/opt/floworkos/apps/diskcraft/`
* **Desktop Engine:** WebKit2GTK Quantum Glass micro-webview (`bin/app.py`).
* **Backend Controller:** Python 3 asynchronous backend (`bin/backend.py`) executing safe multi-threaded filesystem traversals, hashing, and system telemetry.
* **Frontend UI:** Interactive Quantum Glass interface (`ui/index.html`) styled in Obsidian dark mode (`#000000`, 0.40 backdrop blur, neon green `#00ff66` and cyan `#00f2fe` accents) with high-density visual components and zero external CDN dependencies.
* **Launcher Binary:** `/opt/floworkos/bin/diskcraft` and `/usr/local/bin/diskcraft`.
* **Desktop Entry:** `/opt/floworkos/apps/diskcraft.desktop` synced to `/usr/share/applications/` and Launchpad.
* **System Icon:** SVG/PNG high-resolution icon in `/opt/floworkos/icons/diskcraft.png`.

---

## 4. Phased Implementation Plan

### Phase 1: Application Scaffolding & Manifest
* Scaffold app directory `/opt/floworkos/apps/diskcraft/` using `craft-app`.
* Generate app manifest `app.json` and freedesktop launcher `diskcraft.desktop`.
* Create system launcher `/opt/floworkos/bin/diskcraft` and symlink to `/usr/local/bin/diskcraft`.
* Synthesize high-resolution DiskCraft icon in `/opt/floworkos/icons/diskcraft.png`.

### Phase 2: High-Performance Backend Engine (`bin/backend.py`)
* Implement `SystemMetrics`: reads `/proc/diskstats`, `statvfs`, and mount points.
* Implement `CleanupScanner`: declarative rule engine scanning apt cache, user cache, logs, browser cache, dev artifacts, and trash with strict root safety checks.
* Implement `DiskAnalyzer`: recursive directory walker calculating folder weights and identifying top files.
* Implement `DuplicateFinder`: multi-tiered size and fast-hash matcher with automatic original preservation.
* Implement `SafeCleaner`: deletion executor supporting dry-run simulation and atomic batch unlinking.

### Phase 3: Quantum Glass Interactive Interface (`ui/index.html`)
* Header with live disk gauge, partition selector, and quick stats.
* **Tab 1: Deep Cleanup** (Categorized scan results with toggle switches, reclaimable size badges, dry-run toggle, and one-click clean button).
* **Tab 2: Space Analyzer & Treemap** (Interactive visual bar/treemap breakdown of directories and top large files).
* **Tab 3: Duplicate Finder** (Search path selector, group results, auto-select duplicates, and bulk purge).
* **Tab 4: Disk Telemetry** (Real-time mount points, inode status, and I/O metrics).
* Responsive notifications, progress spinners, and confirmation modals.

### Phase 4: Verification & Integration
* Run `/opt/floworkos/bin/craft-app test diskcraft` to ensure headless WebKit initialization achieves **Exit Code 0**.
* Verify standalone execution via `flowork-launch diskcraft` or `/opt/floworkos/bin/diskcraft --foreground`.
* Verify desktop integration: sync `diskcraft.desktop` to `/usr/share/applications/` and `~/.local/share/applications/`.
* Verify app registry in `/opt/floworkos/apps/apps.json`.
* Perform dry-run and scan tests to verify safety invariants.

---

## 5. Verification & Testing Strategy
1. **Headless WebKit Health Check:** `python3 /opt/floworkos/apps/diskcraft/bin/app.py --check-health` must return `Exit Code 0`.
2. **Backend API Validation:** Test scan commands (`scan_cleanup`, `scan_storage`, `scan_duplicates`, `get_metrics`) via backend unit test returning valid JSON payloads.
3. **Safety Blacklist Verification:** Assert that attempting to clean blacklisted directories (`/boot`, `/lib`, `/usr`, `/etc`) is strictly rejected by the backend guardrails.
4. **Desktop Launch Verification:** Launch the application detached and confirm window presence and UI responsiveness.
