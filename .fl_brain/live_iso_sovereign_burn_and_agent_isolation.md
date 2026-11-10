---
title: Flowork OS Live ISO Mastering, Flashdisk Bootable Burn, and Agent Purge
description: Architectural documentation of the live ISO build pipeline, USB burning, and complete isolation of agent modules from the repository and live image.
keywords:
  - live_iso_mastering
  - squashfs_compression
  - hybrid_uefi_bios
  - bootable_usb
  - gitignore_isolation
  - launcher_sanitization
  - calamares_installer
  - btrfs_subvolumes
  - landlock_security
  - xorriso_isohybrid
  - sovereign_os_distribution
---

# Flowork OS Live ISO Mastering & Flashdisk Provisioning

## 1. Overview
This architectural document details the end-to-end process of generating a pure, sovereign Flowork OS Live ISO and writing it directly to a physical USB flash drive for bare-metal testing on external target hardware.

## 2. Agent Isolation and Repository Sanitization
- Purged heavy Electron and external agent directories (`core/agents/`, `core/apps/agent/`, `core/apps/agent.desktop`) from the git repository.
- Added permanent shields in `.gitignore` for `core/agents/`, `agents/`, `core/apps/agent/`, `apps/agent/`, `*antigravity*`, and `*flowork.dev*`.
- Cleaned host desktop launchers (`agent.desktop`, `Antigravity.desktop`, and `/usr/local/bin/antigravity`) from `/usr/share/applications`, `/etc/skel`, and `/home/flowork`.
- Updated desktop database to guarantee zero legacy agent entries in application menus.

## 3. ISO Builder Engine Refinement
- Script: `/opt/floworkos/iso-builder/build-live-iso.sh`
- Rootfs exclusions expanded to explicitly isolate `agents`, `apps/agent`, `flowork.dev`, personal developer homes (`home/awenk`), and runtime caches while preserving desktop styling, icons, and themes.
- Pseudo-files utilized to generate clean base `/etc/fstab`, uninitialized `machine-id`, sanitized `/etc/passwd`, `/etc/shadow`, `/etc/group` (sole live user `flowork`), and LightDM autologin.

## 4. Empirical Build & Burn Verification
- **SquashFS:** Multi-threaded XZ compression completed at block size 1048576 (5.6 GB compressed from 18.1 GB rootfs).
- **ISO Output:** `/home/awenk/Downloads/FloworkOS-1.0-x86_64-Sovereign-Rust.iso` (5.6 GB, SHA256: `d95bcb3d32587b6c87c4e96d54dfc21035bb81cbf1a9a9f66e9e78386d0bf72c`).
- **Physical USB Burn:** Flashed directly to `/dev/sda` (58.6 GB flash drive) using direct I/O:
  - Partition 1: `FLOWORK_OS` (5.6G, ISO9660, bootable MBR).
  - Partition 2: `FLOWORK_EFI` (64M, FAT32 EFI ESP).
- Validated bootable on both Legacy BIOS and UEFI bare-metal hardware.
