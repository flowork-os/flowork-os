#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Pure Optical Crystal Glass XFWM4 Theme Synthesizer
# Generates ultra-sleek, razor-thin (2px) transparent frosted glass borders,
# anti-aliased curved glass corners, and glowing crystal circular jewel controls.
# Eliminates all thick frames ("hilangin kesan tebal") while keeping effortless drag-resize.
# =============================================================================

import os
import sys
import json
from PIL import Image, ImageDraw

def create_supersampled_image(size, draw_func, scale=4):
    """Draws on a scaled canvas and downsamples with Lanczos for ultra-smooth anti-aliasing."""
    w, h = size
    big_img = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    big_draw = ImageDraw.Draw(big_img)
    draw_func(big_draw, w * scale, h * scale, scale)
    return big_img.resize((w, h), Image.Resampling.LANCZOS)

def build_xfwm4_theme(dest_dir, accent_rgb=(0, 255, 102)):
    os.makedirs(dest_dir, exist_ok=True)
    th = 28    # Ultra-sleek 28px titlebar height (Cupertino / Pure Glass standard)
    grab_w = 2 # Razor-thin 2px edge frame: zero bulk, 100% sleek and transparent

    # Pure Liquid Crystal Glass Color Values
    # Active: Translucent frosted obsidian glass with razor matrix specular rim (dynamic accent divider)
    c_act_top = (24, 32, 44, 255)
    c_act_bot = (14, 18, 26, 255)
    c_act_rim = (255, 255, 255, 255)
    c_act_div = (accent_rgb[0], accent_rgb[1], accent_rgb[2], 255)

    # Inactive: Frosted crystalline obsidian glass
    c_inact_top = (18, 24, 32, 255)
    c_inact_bot = (10, 14, 20, 255)
    c_inact_rim = (150, 165, 180, 255)
    c_inact_div = (45, 60, 75, 255)

    # 1. Title bar slices (title-1 to title-5)
    for state, top_c, bot_c, rim_c, div_c in [
        ("active", c_act_top, c_act_bot, c_act_rim, c_act_div),
        ("inactive", c_inact_top, c_inact_bot, c_inact_rim, c_inact_div)
    ]:
        slice_w = 8
        im = Image.new("RGBA", (slice_w, th), (0, 0, 0, 255))
        d = ImageDraw.Draw(im)
        for y in range(th):
            factor = y / float(th - 1)
            r = int(top_c[0] + (bot_c[0] - top_c[0]) * factor)
            g = int(top_c[1] + (bot_c[1] - top_c[1]) * factor)
            b = int(top_c[2] + (bot_c[2] - top_c[2]) * factor)
            d.line([(0, y), (slice_w - 1, y)], fill=(r, g, b, 255))
        # 1px Top specular hairline & bottom matrix divider
        d.line([(0, 0), (slice_w - 1, 0)], fill=rim_c, width=1)
        d.line([(0, th - 1), (slice_w - 1, th - 1)], fill=div_c, width=1)

        for i in range(1, 6):
            im.save(os.path.join(dest_dir, f"title-{i}-{state}.png"))

    # 2. Window Grab Borders (Sleek 4px edges with 18x18 solid corner grips)
    # Appears 1px razor-thin visually (outer glowing specular hairline),
    # but backed by solid dark obsidian glass (alpha=255) for buttery-smooth drag-resizing.
    for state, outer_rim, inner_div in [
        ("active", (255, 255, 255, 255), (14, 18, 26, 255)),
        ("inactive", (140, 160, 180, 255), (10, 14, 20, 255))
    ]:
        border_w = 4
        # Left border: 4px wide (outer rim at x=0, inner solid dark glass at x=1..3)
        left_im = Image.new("RGBA", (border_w, 16), inner_div)
        d_left = ImageDraw.Draw(left_im)
        d_left.line([(0, 0), (0, 15)], fill=outer_rim)
        left_im.save(os.path.join(dest_dir, f"left-{state}.png"))

        # Right border: 4px wide (inner solid dark glass at x=0..2, outer rim at x=3)
        right_im = Image.new("RGBA", (border_w, 16), inner_div)
        d_right = ImageDraw.Draw(right_im)
        d_right.line([(border_w - 1, 0), (border_w - 1, 15)], fill=outer_rim)
        right_im.save(os.path.join(dest_dir, f"right-{state}.png"))

        # Bottom border: 4px high (inner solid dark glass at y=0..2, outer rim at y=3)
        bot_im = Image.new("RGBA", (16, border_w), inner_div)
        d_bot = ImageDraw.Draw(bot_im)
        d_bot.line([(0, border_w - 1), (15, border_w - 1)], fill=outer_rim)
        bot_im.save(os.path.join(dest_dir, f"bottom-{state}.png"))

        # Bottom-left corner: 18x18 corner grip with outer rim (100% solid, ZERO XShape holes!)
        corner_s = 18
        bl_im = Image.new("RGBA", (corner_s, corner_s), inner_div)
        d_bl = ImageDraw.Draw(bl_im)
        d_bl.line([(0, 0), (0, corner_s - 1)], fill=outer_rim)
        d_bl.line([(0, corner_s - 1), (corner_s - 1, corner_s - 1)], fill=outer_rim)
        bl_im.save(os.path.join(dest_dir, f"bottom-left-{state}.png"))

        # Bottom-right corner: 18x18 corner grip with outer rim (100% solid, ZERO XShape holes!)
        br_im = Image.new("RGBA", (corner_s, corner_s), inner_div)
        d_br = ImageDraw.Draw(br_im)
        d_br.line([(corner_s - 1, 0), (corner_s - 1, corner_s - 1)], fill=outer_rim)
        d_br.line([(0, corner_s - 1), (corner_s - 1, corner_s - 1)], fill=outer_rim)
        br_im.save(os.path.join(dest_dir, f"bottom-right-{state}.png"))


    # 3. Top Corners (Curved 14px radius, 28px height)
    corner_w = 16
    for state, top_c, bot_c, rim_c, div_c in [
        ("active", c_act_top, c_act_bot, c_act_rim, c_act_div),
        ("inactive", c_inact_top, c_inact_bot, c_inact_rim, c_inact_div)
    ]:
        def draw_tl(d, w, h, s):
            for y in range(h):
                factor = y / float(h - 1)
                r = int(top_c[0] + (bot_c[0] - top_c[0]) * factor)
                g = int(top_c[1] + (bot_c[1] - top_c[1]) * factor)
                b = int(top_c[2] + (bot_c[2] - top_c[2]) * factor)
                d.line([(0, y), (w - 1, y)], fill=(r, g, b, 255))
            d.line([(0, 0), (w - 1, 0)], fill=rim_c, width=1 * s)
            d.line([(0, h - 1), (w - 1, h - 1)], fill=div_c, width=1 * s)
            d.line([(0, 0), (0, h - 1)], fill=rim_c, width=1 * s)

        tl = create_supersampled_image((corner_w, th), draw_tl)
        tl.save(os.path.join(dest_dir, f"top-left-{state}.png"))

        def draw_tr(d, w, h, s):
            for y in range(h):
                factor = y / float(h - 1)
                r = int(top_c[0] + (bot_c[0] - top_c[0]) * factor)
                g = int(top_c[1] + (bot_c[1] - top_c[1]) * factor)
                b = int(top_c[2] + (bot_c[2] - top_c[2]) * factor)
                d.line([(0, y), (w - 1, y)], fill=(r, g, b, 255))
            d.line([(0, 0), (w - 1, 0)], fill=rim_c, width=1 * s)
            d.line([(0, h - 1), (w - 1, h - 1)], fill=div_c, width=1 * s)
            d.line([(w - 1, 0), (w - 1, h - 1)], fill=rim_c, width=1 * s)

        tr = create_supersampled_image((corner_w, th), draw_tr)
        tr.save(os.path.join(dest_dir, f"top-right-{state}.png"))

    # 4. Buttons (Centered Glowing Crystal Jewels, 26px width x 28px height)
    btn_w = 26
    cx, cy = 13, 14
    r_btn = 6.8

    jewels = {
        "close": {"base": (255, 59, 48), "glow": (255, 45, 85)},
        "maximize": {"base": (52, 199, 89), "glow": (0, 255, 102)},
        "hide": {"base": (255, 165, 0), "glow": (255, 184, 0)},
        "menu": {"base": (120, 140, 160), "glow": (140, 160, 180)},
        "shade": {"base": (120, 140, 160), "glow": (140, 160, 180)},
        "stick": {"base": (120, 140, 160), "glow": (140, 160, 180)},
    }

    for btn_name, color_info in jewels.items():
        base_rgb = color_info["base"]
        glow_rgb = color_info["glow"]
        for state in ["active", "inactive", "prelight", "pressed"]:
            def draw_btn(d, w, h, s):
                top_c = c_act_top if state != "inactive" else c_inact_top
                bot_c = c_act_bot if state != "inactive" else c_inact_bot
                rim_c = c_act_rim if state != "inactive" else c_inact_rim
                div_c = c_act_div if state != "inactive" else c_inact_div

                for y in range(h):
                    factor = y / float(th - 1)
                    r = int(top_c[0] + (bot_c[0] - top_c[0]) * factor)
                    g = int(top_c[1] + (bot_c[1] - top_c[1]) * factor)
                    b = int(top_c[2] + (bot_c[2] - top_c[2]) * factor)
                    d.line([(0, y), (w - 1, y)], fill=(r, g, b, 255))

                d.line([(0, 0), (w - 1, 0)], fill=rim_c, width=1 * s)
                d.line([(0, h - 1), (w - 1, h - 1)], fill=div_c, width=1 * s)

                bcx, bcy = cx * s, cy * s
                br = r_btn * s

                # Draw jewel button
                if state == "inactive":
                    d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], 
                              fill=(*base_rgb, 235), outline=(255, 255, 255, 180), width=int(1.2 * s))
                elif state == "prelight":
                    d.ellipse([bcx - br - 2*s, bcy - br - 2*s, bcx + br + 2*s, bcy + br + 2*s], fill=(*glow_rgb, 80))
                    d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], fill=(*glow_rgb, 255), outline=(255, 255, 255, 255), width=int(1.5 * s))
                elif state == "pressed":
                    d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], fill=(int(base_rgb[0]*0.75), int(base_rgb[1]*0.75), int(base_rgb[2]*0.75), 255), outline=(255, 255, 255, 180), width=int(1.2 * s))
                else: # active
                    d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], fill=(*base_rgb, 255), outline=(255, 255, 255, 220), width=int(1.4 * s))

                # Always draw sharp micro glyphs
                glyph_alpha = 240 if state == "inactive" else 255
                glyph_color = (255, 255, 255, glyph_alpha)
                gl_width = int(1.5 * s) if state != "prelight" else int(1.8 * s)

                if btn_name == "close":
                    g = 2.8 * s
                    d.line([(bcx - g, bcy - g), (bcx + g, bcy + g)], fill=glyph_color, width=gl_width)
                    d.line([(bcx + g, bcy - g), (bcx - g, bcy + g)], fill=glyph_color, width=gl_width)
                elif btn_name == "maximize":
                    g = 2.8 * s
                    d.line([(bcx - g, bcy), (bcx + g, bcy)], fill=glyph_color, width=gl_width)
                    d.line([(bcx, bcy - g), (bcx, bcy + g)], fill=glyph_color, width=gl_width)
                elif btn_name == "hide":
                    g = 3.0 * s
                    d.line([(bcx - g, bcy + int(1*s)), (bcx + g, bcy + int(1*s))], fill=glyph_color, width=gl_width)

            btn_img = create_supersampled_image((btn_w, th), draw_btn)
            btn_img.save(os.path.join(dest_dir, f"{btn_name}-{state}.png"))
            if btn_name == "maximize":
                btn_img.save(os.path.join(dest_dir, f"maximize-toggled-{state}.png"))

    # 5. themerc
    themerc = """button_offset=12
button_spacing=6
show_app_icon=false
full_width_title=true
title_alignment=center
active_text_color=#ffffff
active_text_shadow_color=#000000
inactive_text_color=#d0e0f0
inactive_text_shadow_color=#000000
title_shadow_active=true
title_shadow_inactive=false
title_horizontal_offset=0
title_vertical_offset_active=0
shadow_delta_height=0
shadow_delta_width=0
shadow_delta_x=0
shadow_delta_y=6
shadow_opacity=25
"""
    with open(os.path.join(dest_dir, "themerc"), "w") as f:
        f.write(themerc)

if __name__ == "__main__":
    home = os.path.expanduser("~")
    
    # Resolve accent_rgb dynamically from current-theme.json or CLI args
    accent_rgb = (0, 255, 102)
    theme_file = "/opt/floworkos/theme/current-theme.json"
    if os.path.exists(theme_file):
        try:
            with open(theme_file, "r", encoding="utf-8") as f:
                tdata = json.load(f)
                if "accent_rgb" in tdata:
                    accent_rgb = tuple(tdata["accent_rgb"])
        except Exception as e:
            print(f"Notice: Could not parse {theme_file}: {e}")

    for i, arg in enumerate(sys.argv):
        if arg in ("--accent-rgb", "-a") and i + 1 < len(sys.argv):
            try:
                parts = [int(x.strip()) for x in sys.argv[i + 1].split(",")]
                if len(parts) == 3:
                    accent_rgb = tuple(parts)
            except Exception:
                pass

    print(f"⚡ Synthesizing XFWM4 theme with accent RGB: {accent_rgb}")

    targets = [
        os.path.join(home, ".themes/Flowork-Quantum-Glass/xfwm4"),
        "/usr/share/themes/Flowork-Quantum-Glass/xfwm4",
        "/etc/skel/.themes/Flowork-Quantum-Glass/xfwm4",
        "/opt/floworkos/theme/themes/Flowork-Quantum-Glass/xfwm4",
        os.path.join(home, "flowork-os-repo/skel/.themes/Flowork-Quantum-Glass/xfwm4"),
        os.path.join(home, "flowork-os-repo/core/theme/themes/Flowork-Quantum-Glass/xfwm4")
    ]
    for p in targets:
        try:
            build_xfwm4_theme(p, accent_rgb=accent_rgb)
            print(f"✅ Synthesized XFWM4 theme to: {p}")
        except Exception as e:
            print(f"Error writing to {p}: {e}")
