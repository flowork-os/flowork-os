# [FLOWORK SOVEREIGN GLASS HUD DIRECTIVE]

## 1. Context & Activation Scope
Active when configuring terminal aesthetics, window opacity, transparent overlays, Alacritty TOML, or desktop HUD display parameters.

## 2. Mandatory Behavioral Invariants
- **Window Opacity:** Strictly `0.60` (60% solid obsidian, 40% see-through). Provides the dark contrast floor preventing white background bleed from washing out text, while keeping video playback clearly visible underneath.
- **Base Color:** Pure Neutral Obsidian (`#000000`). Functions as neutral optical glass with zero color shift.
- **Cell Background Passthrough:** `colors.transparent_background_colors = true` MUST be enabled in Alacritty to prevent opaque TUI cell blocking.
- **Typography & Color:** Pure Crystal White (`#ffffff`) in `JetBrains Mono Bold` (12.0pt) for all text (primary, secondary, hints, paths, comments) to guarantee maximum 21:1 contrast.
- **Prompt & Cursor:** Clean `> ` prompt in `#00ff66` (Razor Matrix Green) and solid white cursor (`#ffffff`).
- **Input Styling:** Seamless floating prompt (no solid rectangular background).

## 3. Strict Prohibitions
- NEVER paint windows with synthetic blue (`#07263d`) or grey (`#0c131f`).
- NEVER use low-contrast, faint text colors (`#7dd3fc`, `#AFAFAF`, `#ffff00`).
- NEVER lower opacity below 0.55 (causes fatal text washout over web/video).
- NEVER hardcode persistent styling into base system prompts (`00_preamble.md`).
