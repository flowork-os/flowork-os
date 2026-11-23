#!/usr/bin/env python3
"""
🎨 NON-WHITE BRIGHT BACKGROUND VAULT GENERATOR
Generates 5 distinct high-key non-white backgrounds for anti-duplicate video syndication:
1. Warm Kraft Paper / Vintage Parchment (#EFE8DC)
2. Soft Architectural Cream Loft (#F5EBE1)
3. Sage Mint Daylight Studio (#D8E8E0)
4. Sunlit Amber Loft Wood (#EAE3D2)
5. Soft Industrial Warm Slate (#DFE3E6)
STRICT CONSTRAINT: Pure sterile white (#FFFFFF) is strictly avoided to prevent eye fatigue.
"""

import os
import math
import cairo

WIDTH = 1920
HEIGHT = 1080

def render_warm_kraft_paper(ctx):
    # Warm Kraft / Parchment
    pat = cairo.LinearGradient(0, 0, WIDTH, HEIGHT)
    pat.add_color_stop_rgb(0.0, 0.94, 0.91, 0.86) # #efe8dc
    pat.add_color_stop_rgb(1.0, 0.88, 0.84, 0.78) # #e0d6c7
    ctx.set_source(pat)
    ctx.rectangle(0, 0, WIDTH, HEIGHT); ctx.fill()

    # Subtle organic paper grain
    ctx.set_source_rgba(0.4, 0.3, 0.2, 0.04)
    ctx.set_line_width(1.0)
    for i in range(0, WIDTH, 40):
        ctx.move_to(i, 0); ctx.line_to(i, HEIGHT); ctx.stroke()
    for j in range(0, HEIGHT, 40):
        ctx.move_to(0, j); ctx.line_to(WIDTH, j); ctx.stroke()

    # Soft warm vignette
    vig = cairo.RadialGradient(WIDTH/2, HEIGHT/2, 400, WIDTH/2, HEIGHT/2, 1100)
    vig.add_color_stop_rgba(0.0, 1.0, 1.0, 1.0, 0.0)
    vig.add_color_stop_rgba(1.0, 0.7, 0.6, 0.5, 0.25)
    ctx.set_source(vig); ctx.rectangle(0, 0, WIDTH, HEIGHT); ctx.fill()

def render_architectural_cream(ctx):
    # Architectural Cream / Loft
    pat = cairo.LinearGradient(0, 0, 0, HEIGHT)
    pat.add_color_stop_rgb(0.0, 0.96, 0.92, 0.88) # #f5ebe1
    pat.add_color_stop_rgb(1.0, 0.91, 0.87, 0.82)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, WIDTH, HEIGHT); ctx.fill()

    # Minimalist blueprint dot grid
    ctx.set_source_rgba(0.5, 0.4, 0.35, 0.12)
    for x in range(40, WIDTH, 60):
        for y in range(40, HEIGHT, 60):
            ctx.arc(x, y, 1.2, 0, 2*math.pi); ctx.fill()

    # Soft ambient daylight wash
    wash = cairo.LinearGradient(0, 0, WIDTH, 0)
    wash.add_color_stop_rgba(0.0, 1.0, 0.95, 0.9, 0.15)
    wash.add_color_stop_rgba(1.0, 0.85, 0.8, 0.75, 0.20)
    ctx.set_source(wash); ctx.rectangle(0, 0, WIDTH, HEIGHT); ctx.fill()

def render_sage_mint_studio(ctx):
    # Sage Mint Daylight
    pat = cairo.LinearGradient(0, 0, WIDTH, HEIGHT)
    pat.add_color_stop_rgb(0.0, 0.85, 0.91, 0.88) # #d8e8e0
    pat.add_color_stop_rgb(1.0, 0.79, 0.86, 0.83)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, WIDTH, HEIGHT); ctx.fill()

    # Isometric subtle lines
    ctx.set_source_rgba(0.2, 0.4, 0.35, 0.05)
    ctx.set_line_width(1.0)
    for x in range(-HEIGHT, WIDTH + HEIGHT, 70):
        ctx.move_to(x, 0); ctx.line_to(x + HEIGHT, HEIGHT); ctx.stroke()

    # Soft radial focus
    vig = cairo.RadialGradient(WIDTH/2, HEIGHT/2, 300, WIDTH/2, HEIGHT/2, 1000)
    vig.add_color_stop_rgba(0.0, 1.0, 1.0, 1.0, 0.1)
    vig.add_color_stop_rgba(1.0, 0.2, 0.3, 0.25, 0.18)
    ctx.set_source(vig); ctx.rectangle(0, 0, WIDTH, HEIGHT); ctx.fill()

def render_loft_daylight_amber(ctx):
    # Loft Amber Wood
    pat = cairo.LinearGradient(0, 0, 0, HEIGHT)
    pat.add_color_stop_rgb(0.0, 0.92, 0.89, 0.82) # #eae3d2
    pat.add_color_stop_rgb(1.0, 0.86, 0.82, 0.74)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, WIDTH, HEIGHT); ctx.fill()

    # Horizontal architectural slats
    ctx.set_source_rgba(0.4, 0.35, 0.25, 0.05)
    ctx.set_line_width(2.0)
    for y in range(0, HEIGHT, 45):
        ctx.move_to(0, y); ctx.line_to(WIDTH, y); ctx.stroke()

def render_warm_slate_concrete(ctx):
    # Warm Slate Light
    pat = cairo.LinearGradient(0, 0, WIDTH, HEIGHT)
    pat.add_color_stop_rgb(0.0, 0.87, 0.89, 0.90) # #dfe3e6
    pat.add_color_stop_rgb(1.0, 0.82, 0.84, 0.86)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, WIDTH, HEIGHT); ctx.fill()

    # Minimal crosshair grid
    ctx.set_source_rgba(0.3, 0.35, 0.4, 0.08)
    ctx.set_line_width(1.0)
    for x in range(0, WIDTH, 80):
        ctx.move_to(x, 0); ctx.line_to(x, HEIGHT); ctx.stroke()
    for y in range(0, HEIGHT, 80):
        ctx.move_to(0, y); ctx.line_to(WIDTH, y); ctx.stroke()


BACKGROUND_CATALOG = {
    "warm_kraft_paper": ("warm_kraft_paper.png", render_warm_kraft_paper),
    "architectural_cream": ("architectural_cream.png", render_architectural_cream),
    "sage_mint_studio": ("sage_mint_studio.png", render_sage_mint_studio),
    "loft_daylight_amber": ("loft_daylight_amber.png", render_loft_daylight_amber),
    "warm_slate_concrete": ("warm_slate_concrete.png", render_warm_slate_concrete),
}

def generate_all_backgrounds(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    generated = []
    for key, (filename, render_fn) in BACKGROUND_CATALOG.items():
        filepath = os.path.join(output_dir, filename)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
        ctx = cairo.Context(surf)
        render_fn(ctx)
        surf.write_to_png(filepath)
        print(f"[✓] Non-White Bright BG Created: {filepath}")
        generated.append(filepath)
    return generated

if __name__ == "__main__":
    out_path = "/opt/floworkos/pipelines/stickman_billion_context_documentary/assets/backgrounds"
    generate_all_backgrounds(out_path)
