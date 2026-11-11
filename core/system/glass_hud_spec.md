# 💎 Flowork Sovereign Glass HUD Specification (`glass_hud_spec.md`)

> **Authoritative Specification:** Flowork OS Transparent Overlay Working Standard  
> **Status:** Canonical Rule (`@lock`)  
> **Target Runtimes:** Alacritty Terminal, MrFlow CLI, WhiteSur Dark Desktop Shell  
> **Design Objective:** Multitasking transparent overlay enabling users to work, chat with agents, and execute CLI commands seamlessly while viewing media (e.g. YouTube videos, documentation, IDEs) directly through the terminal window without visual occlusion.

---

## 1. Transparency & Alpha Channel Invariants

| Parameter | Canonical Value | Description & Technical Rationale |
| :--- | :---: | :--- |
| **Window Opacity (`window.opacity`)** | **`0.60` (60%)** | Configured in Alacritty TOML and launcher flags. Optimal balance providing a dark obsidian contrast floor so background light doesn't wash out text, while maintaining high transparency. |
| **Glass Passthrough (See-Through)** | **`40%` (0.40)** | Calibrated see-through capability allowing active video playback, browser windows, and IDE code behind the terminal to remain clearly visible. |
| **32-Bit ARGB Alpha Channel** | **`153 / 255` (`0x99`)** | Native X11 Composite 32-bit ARGB TrueColor visual value. |
| **Cell Background Transparency** | **`true` (Wajib Aktif)** | `colors.transparent_background_colors = true` MUST be enabled. Prevents ANSI codes, React-Ink components, or shell resets from painting opaque cell rectangles. |

---

## 2. Polar-Opposite Contrast & High-Visibility Color Doctrine

To prevent text from disappearing against bright white YouTube webpages or dynamic video scenes, Flowork OS enforces a **Polar-Opposite Chromatic Contrast** standard:

* **Background Base Paint:** **`#000000` (Pure Neutral Obsidian Black)**
  * *Strict Prohibition:* Haram using synthetic blue (`#07263d`), muddy grey (`#1c2128`), or tinted backdrops.
  * *Effect:* The glass surface acts as pure optical glass. Background media shines through with 100% natural color accuracy.
* **Typography Weight (Anti-Washout):** **`JetBrains Mono Bold (Size 12.0)`**
  * Normal and bold text use thick **Bold** glyph weights so letter strokes never fade or blur over background motion.
* **Primary & Secondary Text:** **`#ffffff` (Pure Crystal Luminescent White)**
  * Polar-opposite contrast ratio (21:1) against the dark obsidian base. Zero faint grey (`#AFAFAF`), zero washed-out pastels.
* **Prompt & Focus Accent:** **`#00ff66` (Razor Matrix Green)**
  * Clean, razor-sharp `> ` prompt and active focus indicators.
* **Active Cursor:** **`#ffffff` (Solid White)**
* **Selection Highlight:** **`#00ffff`** with black text.
* **Specular Borders & Dividers:** **`#94a3b8` / `#475569`**.
* **Input Box Styling:** **Seamless Floating** (Eliminated solid grey rectangular half-box background; prompt floats natively over the glass).

---

## 3. Terminal & Geometry Configuration (`alacritty.toml`)

```toml
[window]
startup_mode = "Windowed"
opacity = 0.60
blur = true
padding = { x = 20, y = 16 }
decorations = "full"

[font]
size = 12.0

[font.normal]
family = "JetBrains Mono"
style = "Bold"

[font.bold]
family = "JetBrains Mono"
style = "Bold"

[font.italic]
family = "JetBrains Mono"
style = "Italic"

[colors]
transparent_background_colors = true

[colors.primary]
background = "#000000"
foreground = "#ffffff"

[colors.cursor]
text = "#000000"
cursor = "#ffffff"

[colors.selection]
text = "#000000"
background = "#00ffff"

[colors.normal]
black = "#000000"
red = "#ff5555"
green = "#00ff66"
yellow = "#ffff00"
blue = "#00d4ff"
magenta = "#ff00ff"
cyan = "#00ffff"
white = "#ffffff"

[colors.bright]
black = "#475569"
red = "#ff6666"
green = "#33ff88"
yellow = "#ffff33"
blue = "#33ddff"
magenta = "#ff33ff"
cyan = "#33ffff"
white = "#ffffff"
```

---

## 4. Canonical Enforcement Paths

Any build or rebuild of Flowork OS must enforce these exact values across:
1. `/home/awenkaudico/.config/alacritty/alacritty.toml`
2. `/home/mrflow/.config/alacritty/alacritty.toml`
3. `/etc/skel/.config/alacritty/alacritty.toml`
4. `/usr/local/bin/mrflow-terminal` (`--option window.opacity=0.60`)
5. `/opt/floworkos/bin/mrflow-terminal` (`--option window.opacity=0.60`)
6. `/home/mrflow/floworkos/bin/mrflow-terminal` (`--option window.opacity=0.60`)
7. Native Rust HUD Engine (`/opt/floworkos/mrflow-rs/src/tui/` & `/opt/floworkos/bin/mrflow`)
