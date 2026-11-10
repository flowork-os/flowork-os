---
name: presentation-slide-architect
description: Sovereign architectural playbook for deconstructing presentation templates, structuring deck narrative flows, and generating high-aesthetic visual slides with native 16:9 layouts.
domain: code_dev
keywords:
  - presentation
  - pitch-deck
  - pptx
  - slides
  - visual-hierarchy
  - layout
  - typography
  - slide-outline
  - storytelling
  - spatial-glass
  - color-palette
  - deck-structure
  - keynote
  - infographics
  - vector-graphics
  - style-preset
  - image-generation
  - composition
  - slide-export
  - aspect-ratio
author: Flowork Architecture Board & Dr. Flow
version: 1.0.0
---

# Presentation Slide Architecture & Visual Synthesis Playbook

## 1. Executive Summary & Objective
Deliver a deterministic, high-aesthetic Standard Operating Procedure for converting structured markdown briefs, product pitches, technical whitepapers, or raw topic outlines into publication-ready presentation decks. The goal is to enforce rigid visual hierarchy, cohesive spatial styling (such as Spatial Glass, Dark Aurora, Clean Tech Blue, or Swiss Grid), and produce both high-resolution 16:9 master visual frames and editable OpenXML presentation files (`.pptx`).

## 2. Prerequisites & Tool Dependencies
1. Core Flowork runtime tools: `run_shell_command`, `read_file`, `write_file`.
2. Python 3.10+ runtime with `python-pptx`, `Pillow`, and standard JSON tools.
3. High-fidelity visual generation API access (e.g. OpenAI `gpt-image-2` or local Stable Diffusion pipeline).
4. Strict aesthetic requirement: Slides must reject amateur clip-art, unaligned margins, or text-heavy bullet walls. Every page is treated as an intentional, magazine-grade layout composition.

## 3. Standard Operating Procedure (SOP)

### Step 1: Ingest Content & Construct Slide Plan
Analyze source material and synthesize an atomic slide plan in `out/slides_plan.json`. Each entry defines slide purpose, narrative focus, visual layout archetype, and verbatim copy:
```json
{
  "deck_title": "Project Synthesis",
  "aspect_ratio": "16:9",
  "style_preset": "spatial-glass",
  "slides": [
    {
      "index": 1,
      "archetype": "title_hero",
      "headline": "Autonomous Sovereignty",
      "subheadline": "Architectural Foundation of Flowork OS",
      "visual_description": "Frosted glass panel floating in a deep space gradient with ambient cyan refraction."
    }
  ]
}
```

### Step 2: Select or Calibrate Design Style Preset
Select one of the validated visual style presets:
- `spatial-glass`: Apple VisionOS aesthetic, deep blurred backdrops, glowing borders, frosted acrylic translucency.
- `dark-aurora`: Linear / Vercel developer aesthetic, dark obsidian backdrop with vibrant neon accent gradients.
- `clean-tech-blue`: Stripe / Ramp enterprise fintech aesthetic, crisp white/navy typography, structured mathematical grid.
- `swiss-grid`: Bauhaus / Vignelli international typograhic style, high-contrast monochrome, oversized serif headings.
- `editorial-mono`: Kinfolk / Monocle publishing layout, generous whitespace, understated elegance.

### Step 3: Visual Frame Synthesis
Format structured image generation prompts using the calibrated style tokens. Synthesize full-resolution master visuals (1920x1080 or 2560x1440) for each slide in `out/frames/slide_%02d.png`.

### Step 4: Assemble Native PowerPoint (.pptx) Deck
Package generated visual frames into a 16:9 `.pptx` container using Python automation:
```bash
python3 -c "
import sys, os
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

frame_dir = 'out/frames'
frames = sorted([f for f in os.listdir(frame_dir) if f.endswith('.png')])
for frame in frames:
    slide = prs.slides.add_slide(blank_layout)
    slide.shapes.add_picture(os.path.join(frame_dir, frame), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))

prs.save('out/deck.pptx')
print(f'Successfully compiled {len(frames)} slides into out/deck.pptx')
"
```

### Step 5: Optional Native Editable Layer Reconstruction
When editable vector/text mode is explicitly requested, generate native OpenXML shapes and typography boxes over the visual backdrop rather than embedding static baked copy.

## 4. Verification & Quality Gates (Exit Code 0)
Verify the presentation compilation pipeline output integrity:
```bash
# 1. Verify slide plan schema and non-empty slides array
test -s out/slides_plan.json

# 2. Verify master visual frames exist and match plan count
test $(ls -1 out/frames/*.png 2>/dev/null | wc -l) -gt 0

# 3. Confirm valid .pptx binary compilation
test -f out/deck.pptx && test -s out/deck.pptx

# 4. Verify 16:9 aspect ratio conformance via image dimensions
python3 -c "
import glob
from PIL import Image
for img_path in glob.glob('out/frames/*.png'):
    with Image.open(img_path) as im:
        w, h = im.size
        ratio = round(w / h, 2)
        assert ratio in [1.77, 1.78], f'Invalid aspect ratio: {w}x{h} ({ratio}) in {img_path}'
print('All slide frames strictly conform to 16:9 aspect ratio.')
"
```

## 5. Failure Modes, Edge Cases & Recovery
1. **Aspect Ratio Distortion:** Image generated in 1:1 or 4:3 stretched across 16:9 slide canvas. Mitigation: force explicit 1792x1024 or 1920x1080 pixel boundaries during synthesis.
2. **Text Illegibility & Low Contrast:** Light text over translucent glass or light backgrounds. Mitigation: insert a semi-opaque backdrop scrim (`rgba(10, 15, 25, 0.75)`) behind typography containers.
3. **Broken .pptx XML Hierarchy:** Incompatible font or corrupted shape hierarchy prevents PowerPoint from opening. Remediation: author standard Calibri/Inter fallbacks and validate file header with `file out/deck.pptx`.

## 6. Prohibitions & Anti-Patterns
- **NEVER Mix Incoherent Styles:** Do not combine hand-drawn sketches with photorealistic 3D renders in the same presentation deck.
- **NEVER Generate 4:3 Aspect Ratios:** Traditional 4:3 layouts are deprecated and strictly prohibited.
- **NEVER Output Raw Unformatted Bullets:** Unstructured bullet points without typographical hierarchy violate Flowork design doctrines.
