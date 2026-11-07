#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Quantum Glass XFWM4 Theme Synthesizer
# Generates 100% bespoke, ultra-modern, frosted obsidian window borders,
# cybernetic geometric control nodes, and glowing active borders.
# Zero Apple, Zero Windows — 100% Flowork Sovereign.
# =============================================================================

import os
from PIL import Image, ImageDraw

def build_xfwm4_theme(dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    th = 28 # Titlebar height
    bw = 2  # Border width

    # Colors
    c_active_bg = (8, 12, 22, 255)         # Deep Obsidian Void
    c_inactive_bg = (5, 8, 14, 255)        # Inactive Dark Void
    c_active_top_border = (0, 242, 254, 180) # Quantum Cyan Highlight
    c_inactive_top_border = (26, 38, 58, 120)
    c_active_bottom_border = (0, 242, 254, 70)
    c_inactive_bottom_border = (18, 26, 40, 100)

    c_cyan = (0, 242, 254, 255)
    c_cyan_hover = (85, 255, 255, 255)
    c_crimson = (255, 45, 85, 255)
    c_crimson_hover = (255, 90, 120, 255)
    c_dim = (80, 95, 120, 220)

    # 1. Title bar slices (title-1 to title-5)
    for state, bg, top_b, bot_b in [("active", c_active_bg, c_active_top_border, c_active_bottom_border),
                                    ("inactive", c_inactive_bg, c_inactive_top_border, c_inactive_bottom_border)]:
        im = Image.new("RGBA", (4, th), bg)
        d = ImageDraw.Draw(im)
        d.line([(0, 0), (3, 0)], fill=top_b, width=1)
        d.line([(0, th - 1), (3, th - 1)], fill=bot_b, width=1)
        for i in range(1, 6):
            im.save(os.path.join(dest_dir, f"title-{i}-{state}.png"))

    # 2. Window Side & Bottom Borders
    # left & right (2px wide)
    for state, border_color in [("active", (0, 242, 254, 140)), ("inactive", (20, 30, 48, 120))]:
        side_im = Image.new("RGBA", (bw, 16), border_color)
        side_im.save(os.path.join(dest_dir, f"left-{state}.png"))
        side_im.save(os.path.join(dest_dir, f"right-{state}.png"))

        bot_im = Image.new("RGBA", (16, bw), border_color)
        bot_im.save(os.path.join(dest_dir, f"bottom-{state}.png"))

        corner_im = Image.new("RGBA", (bw, bw), border_color)
        corner_im.save(os.path.join(dest_dir, f"bottom-left-{state}.png"))
        corner_im.save(os.path.join(dest_dir, f"bottom-right-{state}.png"))

    # 3. Top Corners (rounded top-left and top-right, radius 10px)
    corner_w = 12
    for state, bg, border_col in [("active", c_active_bg, c_cyan), ("inactive", c_inactive_bg, c_dim)]:
        # Top-Left
        tl = Image.new("RGBA", (corner_w, th), (0, 0, 0, 0))
        d_tl = ImageDraw.Draw(tl)
        d_tl.rounded_rectangle([0, 0, corner_w * 2, th * 2], radius=10, fill=bg, outline=border_col, width=1)
        tl.save(os.path.join(dest_dir, f"top-left-{state}.png"))

        # Top-Right
        tr = Image.new("RGBA", (corner_w, th), (0, 0, 0, 0))
        d_tr = ImageDraw.Draw(tr)
        d_tr.rounded_rectangle([-corner_w, 0, corner_w, th * 2], radius=10, fill=bg, outline=border_col, width=1)
        tr.save(os.path.join(dest_dir, f"top-right-{state}.png"))

    # 4. Bespoke Cybernetic Button Nodes (26 x 28 px)
    btn_w = 26
    def create_btn_base(state_bg):
        im = Image.new("RGBA", (btn_w, th), state_bg)
        d = ImageDraw.Draw(im)
        d.line([(0, 0), (btn_w - 1, 0)], fill=c_active_top_border, width=1)
        d.line([(0, th - 1), (btn_w - 1, th - 1)], fill=c_active_bottom_border, width=1)
        return im, d

    # A. Close Button (Cyber Angular Cross ✕)
    close_specs = [
        ("active", c_active_bg, c_crimson),
        ("prelight", (35, 12, 22, 255), c_crimson_hover),
        ("pressed", (22, 6, 14, 255), (180, 20, 50, 255)),
        ("inactive", c_inactive_bg, c_dim)
    ]
    for name, bg, icon_col in close_specs:
        im, d = create_btn_base(bg)
        cx, cy = btn_w // 2, th // 2
        r = 4
        d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=icon_col, width=2)
        d.line([(cx + r, cy - r), (cx - r, cy + r)], fill=icon_col, width=2)
        im.save(os.path.join(dest_dir, f"close-{name}.png"))

    # B. Maximize Button (Cyber Framing Bracket ⌜⌝ / ▢)
    max_specs = [
        ("active", c_active_bg, c_cyan),
        ("prelight", (14, 30, 48, 255), c_cyan_hover),
        ("pressed", (10, 20, 32, 255), (0, 150, 180, 255)),
        ("inactive", c_inactive_bg, c_dim)
    ]
    for name, bg, icon_col in max_specs:
        im, d = create_btn_base(bg)
        cx, cy = btn_w // 2, th // 2
        r = 4
        d.rectangle([cx - r, cy - r, cx + r, cy + r], outline=icon_col, width=1)
        im.save(os.path.join(dest_dir, f"maximize-{name}.png"))
        im.save(os.path.join(dest_dir, f"maximize-toggled-{name}.png"))

    # C. Hide / Minimize Button (Cyber Laser Line ―)
    hide_specs = [
        ("active", c_active_bg, c_cyan),
        ("prelight", (14, 30, 48, 255), c_cyan_hover),
        ("pressed", (10, 20, 32, 255), (0, 150, 180, 255)),
        ("inactive", c_inactive_bg, c_dim)
    ]
    for name, bg, icon_col in hide_specs:
        im, d = create_btn_base(bg)
        cx, cy = btn_w // 2, th // 2
        r = 5
        d.line([(cx - r, cy + 3), (cx + r, cy + 3)], fill=icon_col, width=2)
        im.save(os.path.join(dest_dir, f"hide-{name}.png"))

    # 5. themerc configuration
    themerc_content = """# Flowork Sovereign Quantum Glass Window Manager Theme
button_offset=8
button_spacing=2
show_app_icon=false
full_width_title=true

active_text_color=#00f2fe
active_text_shadow_color=#020408
inactive_text_color=#64748b
inactive_text_shadow_color=#020408

title_shadow_active=false
title_shadow_inactive=false
title_horizontal_offset=0

shadow_delta_height=0
shadow_delta_width=0
shadow_delta_x=0
shadow_delta_y=2
shadow_opacity=60
"""
    with open(os.path.join(dest_dir, "themerc"), "w") as f:
        f.write(themerc_content)

    print(f"✅ Flowork-Quantum-Glass XFWM4 theme synthesized successfully at: {dest_dir}")

if __name__ == "__main__":
    build_xfwm4_theme(os.path.expanduser("~/.themes/Flowork-Quantum-Glass/xfwm4"))
    try:
        build_xfwm4_theme("/usr/share/themes/Flowork-Quantum-Glass/xfwm4")
    except Exception:
        pass
