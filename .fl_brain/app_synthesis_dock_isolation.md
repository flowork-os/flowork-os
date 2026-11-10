---
title: Application Synthesis Desktop Menu Registration & Clean Dock Invariant
category: architecture
keywords:
  - application_synthesis
  - craft_app
  - desktop_registration
  - clean_dock
  - launchpad
  - whisker_menu
  - plank_dock
  - start_menu
  - taskbar_isolation
  - sovereign_apps
  - dockitem_prohibition
  - orbit_deck
---
# Application Synthesis Desktop Menu Registration & Clean Dock Invariant

## Problem Statement
When synthesizing, generating, or registering bespoke desktop applications in Flowork OS (via `craft-app` or manual packaging), applications must never be automatically or permanently pinned to the bottom dock (`Plank`). Doing so clutters the taskbar, breaks symmetrical centering, and creates visual noise.

## Authoritative Doctrine
1. **Target Destinations:**
   - **Start Menu (Whisker):** Register the `.desktop` file into `/usr/share/applications/` (and `/opt/floworkos/apps/`).
   - **Launchpad (Orbit Deck):** Register the app into `/opt/floworkos/theme/flowork-orbit.py` favorites or allow it to be indexed via `/usr/share/applications/`.
2. **Bottom Dock (Plank) Isolation:**
   - The bottom dock is strictly reserved for the 6 core sovereign anchors (`flowork-launchpad`, `Alacritty`, `code`, `nemo`, `mrflow-agent`, `trash`).
   - Newly synthesized apps appear dynamically in the dock ONLY while their window process is running, and disappear immediately upon closing.
   - Never create `.dockitem` files in `~/.config/plank/dock1/launchers/` or `/etc/skel/.config/plank/dock1/launchers/`.
   - Never append the app ID to `net.launchpad.plank.dock.settings dock-items`.
   - Keep `auto-pinning` set to `false`.
