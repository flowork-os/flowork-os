#!/usr/bin/env python3
# =============================================================================
# 🚀 Flowork Sovereign OS — Native X11 Root Wallpaper Renderer
# Renders Flowork OS Sovereign Wallpaper directly onto X11 Root Window
# Chunks line-by-line to respect X11 protocol max request size
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================

import sys
import os
from PIL import Image
from Xlib import X, display, Xatom

def set_root_wallpaper(image_path, display_name=None):
    if not os.path.isfile(image_path):
        print(f"Error: image not found: {image_path}", file=sys.stderr)
        return False

    d = display.Display(display_name or os.environ.get("DISPLAY", ":0"))
    screen = d.screen()
    root = screen.root
    width = screen.width_in_pixels
    height = screen.height_in_pixels

    img = Image.open(image_path).convert("RGB")
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    rgb_bytes = img.tobytes()

    pixmap = root.create_pixmap(width, height, screen.root_depth)
    gc = root.create_gc(foreground=screen.white_pixel, background=screen.black_pixel)

    # Send line by line to stay well under X11 request length limit
    # (width * 4 bytes per line = 1280 * 4 = 5120 bytes << 65535)
    row_stride_rgb = width * 3
    for y in range(height):
        row_bgrx = bytearray(width * 4)
        offset_rgb = y * row_stride_rgb
        for x in range(width):
            r = rgb_bytes[offset_rgb + x * 3]
            g = rgb_bytes[offset_rgb + x * 3 + 1]
            b = rgb_bytes[offset_rgb + x * 3 + 2]
            row_bgrx[x * 4] = b
            row_bgrx[x * 4 + 1] = g
            row_bgrx[x * 4 + 2] = r
            row_bgrx[x * 4 + 3] = 0
        pixmap.put_image(gc, 0, y, width, 1, X.ZPixmap, screen.root_depth, 0, bytes(row_bgrx))

    root.change_attributes(background_pixmap=pixmap)

    atom_xroot = d.intern_atom("_XROOTPMAP_ID")
    atom_eset = d.intern_atom("ESETROOT_PMAP_ID")
    root.change_property(atom_xroot, Xatom.PIXMAP, 32, [pixmap.id])
    root.change_property(atom_eset, Xatom.PIXMAP, 32, [pixmap.id])

    root.clear_area(0, 0, width, height, False)
    d.sync()
    d.close()
    print(f"✅ Flowork OS Sovereign Wallpaper painted ({width}x{height}) on {d.get_display_name()}")
    return True

if __name__ == "__main__":
    target_img = sys.argv[1] if len(sys.argv) > 1 else "/opt/floworkos/theme/wallpaper-flowork.png"
    target_disp = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("DISPLAY", ":0")
    set_root_wallpaper(target_img, target_disp)
