# 👑 PASSIVE TRIGGER: SOVEREIGN STEALTH & ANTI-DETECT BROWSER

## 1. Scope & Activation
Triggered when configuring, launching, or debugging anti-detect browser profiles, synthetic hardware personas, or stealth browser sessions (`flowork-stealth`, `camoufox`, `anti-detect`, `iphey`, `stealth browser`).

## 2. Core Invariants & Hybrid Dual-Engine
1. **Instant Chrome Stealth Fallback (< 0.3s)**: When Camoufox binary is absent or network-stalled, instantly spawn Google Chrome with `--user-data-dir`, `--load-extension` (Manifest V3 hardware spoofing), `--new-window`, and atomic canvas/audio seeds.
2. **Native Camoufox C++ Engine**: When official binaries exist, activate persistent C++ browser context with OS spoofing, humanized input, and WebRTC leak protection.
3. **Strict Profile Sandboxing**: Each profile maintains an isolated directory under `/opt/floworkos/apps/flowork-stealth/profiles/<slug>/`. Never leak storage, cookies, or sessions across profiles.
4. **Non-Blocking Execution & Observability**: Detach browser processes cleanly via `setpgrp`. Stream logs to `/tmp/flowork_stealth_launch.log`, dispatch desktop notifications via `notify-send`, and ensure immediate window foregrounding.
