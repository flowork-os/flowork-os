#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Quantum Glass Wallpaper Synthesizer
# Generates a bespoke, 2560x1080 deep obsidian glass wallpaper with
# cybernetic neural topologies, the Flowork Sovereign crest, and www.floworkos.com.
# 100% Standalone White-Label — Zero Apple, Zero Windows.
# =============================================================================

import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_quantum_wallpaper(output_path="/opt/floworkos/theme/flowork-quantum-wallpaper.png", width=2560, height=1080):
    # 1. Base Deep Void Radial Gradient (from dark obsidian #070b16 to deep void #020307)
    base = Image.new("RGBA", (width, height), (3, 5, 10, 255))
    draw = ImageDraw.Draw(base)

    center_x, center_y = width // 2, height // 2
    max_radius = math.hypot(center_x, center_y)

    # Multi-stop subtle glow in center
    for r in range(int(max_radius), 0, -4):
        ratio = r / max_radius
        # Interpolate from center (14, 22, 38) to edge (2, 3, 7)
        cr = int(2 + (14 - 2) * (1.0 - ratio) ** 1.8)
        cg = int(3 + (26 - 3) * (1.0 - ratio) ** 1.8)
        cb = int(7 + (48 - 7) * (1.0 - ratio) ** 1.8)
        draw.ellipse(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            fill=(cr, cg, cb, 255)
        )

    # 2. Cybernetic Vector Layer (Neural Mesh & Perspective Lattice)
    grid_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid_layer)

    # Horizontal guideline mesh (spaced widely for elegance)
    for y in range(0, height, 72):
        dist_y = abs(y - center_y) / (height / 2)
        alpha = int(14 * (1.0 - dist_y * 0.6))
        grid_draw.line([(0, y), (width, y)], fill=(0, 242, 254, alpha), width=1)

    # Vertical guideline mesh
    for x in range(0, width, 128):
        dist_x = abs(x - center_x) / (width / 2)
        alpha = int(12 * (1.0 - dist_x * 0.7))
        grid_draw.line([(x, 0), (x, height)], fill=(0, 242, 254, alpha), width=1)

    # Hexagonal Central Ring
    hex_radius = 210
    hex_points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = center_x + hex_radius * math.cos(angle)
        py = center_y + hex_radius * math.sin(angle)
        hex_points.append((px, py))
    hex_points.append(hex_points[0])

    for i in range(len(hex_points) - 1):
        grid_draw.line([hex_points[i], hex_points[i+1]], fill=(0, 242, 254, 70), width=2)

    # Outer Hex Ring (segmented)
    outer_hex = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = center_x + (hex_radius + 40) * math.cos(angle)
        py = center_y + (hex_radius + 40) * math.sin(angle)
        outer_hex.append((px, py))
    for i in range(6):
        p1 = outer_hex[i]
        p2 = outer_hex[(i + 1) % 6]
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2
        grid_draw.line([p1, (mid_x - 10, mid_y)], fill=(0, 255, 136, 45), width=1)
        grid_draw.line([(mid_x + 10, mid_y), p2], fill=(0, 255, 136, 45), width=1)

    # 3. Center Sovereign Emblem: [ F _ ]
    emblem_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    emblem_draw = ImageDraw.Draw(emblem_layer)

    # Inner Frosted Glass Plate
    plate_w, plate_h = 380, 170
    p_x0 = center_x - plate_w // 2
    p_y0 = center_y - plate_h // 2
    p_x1 = p_x0 + plate_w
    p_y1 = p_y0 + plate_h

    # Rounded frosted glass plate with specular cyan border
    emblem_draw.rounded_rectangle(
        [p_x0, p_y0, p_x1, p_y1],
        radius=24,
        fill=(8, 14, 25, 150),
        outline=(0, 242, 254, 110),
        width=1
    )

    # Fonts
    font_paths = [
        "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"
    ]
    font_large = None
    font_medium = None
    font_url = None

    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_large = ImageFont.truetype(fp, 46)
                font_medium = ImageFont.truetype(fp, 12)
                font_url = ImageFont.truetype(fp, 14)
                break
            except Exception:
                pass
    if font_large is None:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_url = ImageFont.load_default()

    # 1. Main Title: FLOWORK OS
    title_text = "FLOWORK OS"
    bbox = emblem_draw.textbbox((0, 0), title_text, font=font_large)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = center_x - tw // 2
    ty = center_y - 54

    emblem_draw.text((tx, ty), title_text, font=font_large, fill=(0, 242, 254, 245))

    # 2. Subtitle: SOVEREIGN AGENT-NATIVE LINUX 7.3.0 RUST
    sub_text = "SOVEREIGN AGENT-NATIVE LINUX 7.3.0 RUST"
    s_bbox = emblem_draw.textbbox((0, 0), sub_text, font=font_medium)
    sw = s_bbox[2] - s_bbox[0]
    sx = center_x - sw // 2
    sy = ty + th + 14
    emblem_draw.text((sx, sy), sub_text, font=font_medium, fill=(0, 255, 136, 210))

    # 3. Canonical Sovereign Domain: www.floworkos.com
    url_text = "www.floworkos.com"
    u_bbox = emblem_draw.textbbox((0, 0), url_text, font=font_url)
    uw = u_bbox[2] - u_bbox[0]
    uh = u_bbox[3] - u_bbox[1]
    ux = center_x - uw // 2
    uy = sy + 24

    # Pill badge backing for URL
    pill_pad_x = 14
    pill_pad_y = 5
    emblem_draw.rounded_rectangle(
        [ux - pill_pad_x, uy - pill_pad_y, ux + uw + pill_pad_x, uy + uh + pill_pad_y + 1],
        radius=10,
        fill=(0, 242, 254, 22),
        outline=(0, 242, 254, 75),
        width=1
    )
    emblem_draw.text((ux, uy), url_text, font=font_url, fill=(0, 242, 254, 230))

    # Merge layers
    composed = Image.alpha_composite(base, grid_layer)
    composed = Image.alpha_composite(composed, emblem_layer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    composed.convert("RGB").save(output_path, "PNG", optimize=True)
    print(f"✅ Flowork Quantum Wallpaper with www.floworkos.com synthesized: {output_path} ({width}x{height})")

if __name__ == "__main__":
    create_quantum_wallpaper()
