#!/usr/bin/env python3
"""
Flowork OS - Sovereign Plymouth Splash Theme Generator
Generates high-fidelity cybernetic boot splash frames with animated quantum pulse,
rotating perimeter plasma arcs, orbital energy nodes, and sovereign watermark.
"""

import os
import math
import cairo

THEME_DIR = "/opt/floworkos/theme/plymouth/flowork-cyber"
os.makedirs(THEME_DIR, exist_ok=True)

SIZE = 160
TOTAL_FRAMES = 36

def get_hex_vertices(cx, cy, r):
    vertices = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        vertices.append((px, py))
    return vertices

def get_hex_point_at_t(vertices, t):
    """Interpolate point along hexagon perimeter: t in [0.0, 1.0)"""
    t = t % 1.0
    seg_float = t * 6.0
    seg_idx = int(seg_float) % 6
    seg_frac = seg_float - int(seg_float)
    x1, y1 = vertices[seg_idx]
    x2, y2 = vertices[(seg_idx + 1) % 6]
    return x1 + (x2 - x1) * seg_frac, y1 + (y2 - y1) * seg_frac

def draw_frame(frame_idx, filename):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surface)
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()
    ctx.set_operator(cairo.OPERATOR_OVER)

    cx, cy = SIZE / 2.0, SIZE / 2.0
    r_outer = 68.0
    r_inner = 58.0
    outer_verts = get_hex_vertices(cx, cy, r_outer)
    inner_verts = get_hex_vertices(cx, cy, r_inner)

    progress = frame_idx / float(TOTAL_FRAMES)
    pulse = 0.85 + 0.15 * math.sin(2.0 * math.pi * progress)

    # 1. Outer Dark Hex Plate with subtle Cyber Core Glow
    ctx.new_path()
    for i, (vx, vy) in enumerate(outer_verts):
        if i == 0: ctx.move_to(vx, vy)
        else: ctx.line_to(vx, vy)
    ctx.close_path()
    ctx.set_source_rgba(0.035, 0.043, 0.063, 0.94)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.0, 0.95, 1.0, 0.22)
    ctx.set_line_width(2.5)
    ctx.stroke()

    # 2. Inner Circuit Hexagon Outline
    ctx.new_path()
    for i, (vx, vy) in enumerate(inner_verts):
        if i == 0: ctx.move_to(vx, vy)
        else: ctx.line_to(vx, vy)
    ctx.close_path()
    ctx.set_source_rgba(0.47, 0.16, 0.79, 0.35)
    ctx.set_line_width(1.5)
    ctx.stroke()

    # 3. Rotating Perimeter Plasma Arc (Electric Surge)
    # The head of the surge is at progress, with a trailing comet tail of 12 points
    trail_len = 16
    for step in range(trail_len):
        trail_t = (progress - (step * 0.015)) % 1.0
        tx, ty = get_hex_point_at_t(outer_verts, trail_t)
        alpha = (1.0 - (step / float(trail_len))) ** 1.8
        r_spark = 4.5 * (1.0 - (step / float(trail_len))) + 1.2
        
        ctx.arc(tx, ty, r_spark, 0, 2 * math.pi)
        if step == 0:
            ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95)
        elif step < 4:
            ctx.set_source_rgba(0.0, 0.95, 1.0, alpha * 0.9)
        else:
            ctx.set_source_rgba(0.47, 0.16, 0.79, alpha * 0.75)
        ctx.fill()

    # Opposite Counter-Arc (harmonic resonance)
    for step in range(10):
        trail_t = (progress + 0.5 - (step * 0.012)) % 1.0
        tx, ty = get_hex_point_at_t(inner_verts, trail_t)
        alpha = (1.0 - (step / 10.0)) ** 2.0
        ctx.arc(tx, ty, 3.0 * (1.0 - step / 10.0) + 1.0, 0, 2 * math.pi)
        ctx.set_source_rgba(0.22, 0.74, 0.97, alpha * 0.8)
        ctx.fill()

    # 4. Central Sovereign 'F' Pulse Engine
    scale = 0.28
    ctx.save()
    ctx.translate(cx - 256.0 * scale, cy - 256.0 * scale)
    ctx.scale(scale, scale)

    # Core Breathing Glow Gradient
    grad = cairo.LinearGradient(170, 140, 360, 380)
    c1 = (0.0 * pulse, 0.95 * pulse, 1.0 * pulse)
    c2 = (0.22 * pulse, 0.74 * pulse, 0.97 * pulse)
    c3 = (0.47 * pulse, 0.16 * pulse, 0.79 * pulse)
    grad.add_color_stop_rgb(0.0, *c1)
    grad.add_color_stop_rgb(0.5, *c2)
    grad.add_color_stop_rgb(1.0, *c3)

    ctx.set_source(grad)
    # Vertical Pillar
    ctx.rectangle(170, 140, 60, 240)
    ctx.fill()
    # Top Bar
    ctx.rectangle(230, 140, 130, 55)
    ctx.fill()
    # Mid Bar
    ctx.rectangle(230, 240, 95, 55)
    ctx.fill()

    # Orbital Nodes with Quantum Glow
    ctx.arc(360, 167, 14 * pulse, 0, 2 * math.pi)
    ctx.set_source_rgba(0.0, 0.95, 1.0, 0.95)
    ctx.fill()

    ctx.arc(325, 267, 12 * pulse, 0, 2 * math.pi)
    ctx.set_source_rgba(0.65, 0.25, 0.95, 0.95)
    ctx.fill()

    ctx.arc(200, 380, 10 * pulse, 0, 2 * math.pi)
    ctx.set_source_rgba(0.0, 0.95, 1.0, 0.9)
    ctx.fill()

    ctx.restore()

    # 5. Dual Nano Orbital Sparks
    orbit_r1 = 44.0
    orbit_angle1 = 2.0 * math.pi * progress * 2.0
    ox1 = cx + orbit_r1 * math.cos(orbit_angle1)
    oy1 = cy + orbit_r1 * math.sin(orbit_angle1)
    ctx.arc(ox1, oy1, 2.5, 0, 2 * math.pi)
    ctx.set_source_rgba(0.0, 0.95, 1.0, 0.85)
    ctx.fill()

    surface.write_to_png(filename)

def generate_watermark(filename):
    w, h = 420, 100
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surface)
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()
    ctx.set_operator(cairo.OPERATOR_OVER)

    # Title: FLOWORK OS
    ctx.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(32.0)
    title = "FLOWORK OS"
    extents = ctx.text_extents(title)
    tx = (w - extents.width) / 2.0 - extents.x_bearing
    ty = 45.0

    # Glow Gradient
    grad = cairo.LinearGradient(tx, 0, tx + extents.width, 0)
    grad.add_color_stop_rgb(0.0, 0.0, 0.95, 1.0)
    grad.add_color_stop_rgb(0.5, 0.22, 0.74, 0.97)
    grad.add_color_stop_rgb(1.0, 0.65, 0.25, 0.95)
    ctx.set_source(grad)
    ctx.move_to(tx, ty)
    ctx.show_text(title)

    # Subtitle: SOVEREIGN NEURAL DESKTOP
    ctx.select_font_face("Cantarell", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(12.5)
    sub = "SOVEREIGN SYSTEM ARCHITECTURE"
    sub_extents = ctx.text_extents(sub)
    sx = (w - sub_extents.width) / 2.0 - sub_extents.x_bearing
    sy = 72.0
    ctx.set_source_rgba(0.22, 0.74, 0.97, 0.75)
    ctx.move_to(sx, sy)
    ctx.show_text(sub)

    # Micro Line Accents
    ctx.set_line_width(1.0)
    ctx.set_source_rgba(0.0, 0.95, 1.0, 0.3)
    line_y = 84.0
    ctx.move_to(w / 2.0 - 80, line_y)
    ctx.line_to(w / 2.0 + 80, line_y)
    ctx.stroke()

    surface.write_to_png(filename)

def main():
    print(f"Generating {TOTAL_FRAMES} boot splash animation frames in {THEME_DIR}...")
    for i in range(1, TOTAL_FRAMES + 1):
        num_str = f"{i:04d}"
        anim_path = os.path.join(THEME_DIR, f"animation-{num_str}.png")
        throb_path = os.path.join(THEME_DIR, f"throbber-{num_str}.png")
        draw_frame(i - 1, anim_path)
        # Link or copy for throbber (Plymouth two-step uses throbber or animation)
        if os.path.exists(throb_path):
            os.remove(throb_path)
        os.link(anim_path, throb_path)

    # Generate static fallback
    draw_frame(0, os.path.join(THEME_DIR, "bgrt-fallback.png"))

    # Generate watermark
    generate_watermark(os.path.join(THEME_DIR, "watermark.png"))

    print("All frames and watermark successfully generated!")

if __name__ == "__main__":
    main()
