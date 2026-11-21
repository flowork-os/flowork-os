# 🛡️ PASSIVE TRIGGER: SOVEREIGN BRANDING & ASSET INVARIANTS

## 1. Context & Activation Scope
Triggered when modifying system branding, desktop themes, user profile pictures, avatars (`~/.face`), greeters, neofetch, icons, or distribution packaging.

## 2. Mandatory Behavioral Invariants
- **UNIFIED SOVEREIGN LOGO:** All user profile avatars (`~/.face`, `~/.face.icon`) must strictly use the official Flowork Cyber Hexagon icon (`/opt/floworkos/assets/flowork-icon.png` 256x256 RGBA).
- **SKEL SYNCHRONIZATION:** Mirror `.face` and symlink `.face.icon -> .face` into `/etc/skel` and repository `skel/` so newly generated ISO users inherit Flowork branding.
- **DEBIAN ASSET OVERRIDES:** Ensure all legacy Debian icon aliases (`debian-logo`, `debian-swirl`, `distributor-logo-debian`, `start-here-debian`, `emblem-debian`, `softwarecenter-debian`) are mapped to the Flowork Cyber Shield SVG (`/usr/share/icons/flowork/flowork-logo.svg`) and multi-resolution PNGs (16px to 256px).
- **TERMINAL BRANDING:** Maintain the Flowork Sovereign Cyber Hex ASCII art in `/opt/floworkos/theme/flowork-ascii.txt` and configure `neofetch` to render Flowork identity by default.

## 3. Strict Prohibitions
- NEVER reintroduce Debian swirl SVGs (`#a80030`, `#d70751`) or default distribution placeholders.
- NEVER leave `.face.icon` broken; it must always resolve to the Flowork PNG avatar.
- NEVER hardcode user-specific paths when packaging branding assets for ISO builds.
