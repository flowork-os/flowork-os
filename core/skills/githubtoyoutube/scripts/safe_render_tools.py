#!/usr/bin/env python3
"""
🛡️ SAFE RENDER TOOLS — GITHUB TO YOUTUBE SOVEREIGN ANIMATION ENGINE
Provides zero-overflow text rendering, auto-wrapping, dynamic font scaling,
and prominent GitHub repository URL overlays conforming to the 9:16 vertical safe zone.
"""

import math
import cairo

# 9:16 VERTICAL SHORT BOUNDS & SAFE MARGIN CONSTANTS
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920

SAFE_MARGIN_X = 90  # Min 90px left/right margin (Safe X: 90 .. 990, width: 900px)
SAFE_TOP_Y = 180    # Min 180px top margin (Safe Y: 180 .. 1680)
SAFE_BOTTOM_Y = 1680
MAX_SAFE_WIDTH = CANVAS_WIDTH - (SAFE_MARGIN_X * 2)  # 900px


def wrap_text_to_width(ctx, text: str, max_width: float) -> list:
    """
    Splits text into multiple lines such that no line exceeds max_width.
    """
    words = text.split()
    if not words:
        return []

    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        ext = ctx.text_extents(test_line)
        if ext.width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # Word itself is wider than max_width, force it
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def draw_safe_text_centered(
    ctx,
    text: str,
    cx: float,
    cy: float,
    max_width: float = MAX_SAFE_WIDTH,
    base_font_size: float = 52.0,
    font_face: str = "Sans",
    font_weight: int = cairo.FONT_WEIGHT_BOLD,
    text_color=(1.0, 1.0, 1.0),
    outline_color=(0.0, 0.0, 0.0),
    outline_width: float = 12.0,
    line_spacing: float = 1.25,
):
    """
    Draws text perfectly centered at (cx, cy) wrapped and scaled so it NEVER
    exceeds max_width or clips screen margins.
    """
    ctx.save()
    ctx.select_font_face(font_face, cairo.FONT_SLANT_NORMAL, font_weight)

    # First attempt at base_font_size
    ctx.set_font_size(base_font_size)
    lines = wrap_text_to_width(ctx, text, max_width)

    # If any single line still exceeds max_width, scale font size down
    max_measured_line = 0.0
    for line in lines:
        ext = ctx.text_extents(line)
        if ext.width > max_measured_line:
            max_measured_line = ext.width

    effective_font_size = base_font_size
    if max_measured_line > max_width and max_measured_line > 0:
        scale = max_width / max_measured_line
        effective_font_size = max(24.0, base_font_size * scale)
        ctx.set_font_size(effective_font_size)
        lines = wrap_text_to_width(ctx, text, max_width)

    total_height = len(lines) * effective_font_size * line_spacing
    start_y = cy - (total_height / 2.0) + (effective_font_size * 0.8)

    for i, line in enumerate(lines):
        line_y = start_y + (i * effective_font_size * line_spacing)
        ext = ctx.text_extents(line)
        line_x = cx - (ext.width / 2.0)

        # Draw heavy stroke outline if requested
        if outline_width > 0 and outline_color is not None:
            ctx.set_source_rgba(*outline_color)
            ctx.set_line_width(outline_width)
            ctx.move_to(line_x, line_y)
            ctx.text_path(line)
            ctx.stroke()

        # Draw fill text
        ctx.set_source_rgba(*text_color)
        ctx.move_to(line_x, line_y)
        ctx.show_text(line)

    ctx.restore()
    return total_height


def draw_github_repo_header_pill(
    ctx,
    repo_slug: str,  # e.g. "browser-use/browser-use"
    stars_str: str = "55k ★",
    y_pos: float = 230.0,
    alpha: float = 1.0,
):
    """
    Draws a prominent, sleek GitHub repository pill at the top safe zone:
    [ GitHub Icon | github.com/owner/repo | ★ 55k ]
    Strictly constrained within the horizontal safe boundary (X: 90..990).
    """
    ctx.save()
    full_url = f"github.com/{repo_slug}"

    # Target maximum pill width
    pill_max_w = min(MAX_SAFE_WIDTH, 880.0)
    pill_h = 76.0
    pill_cx = CANVAS_WIDTH / 2.0

    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    font_size = 32.0
    ctx.set_font_size(font_size)
    ext_url = ctx.text_extents(full_url)

    # Scale font if URL is long
    available_url_w = pill_max_w - 260.0
    if ext_url.width > available_url_w:
        font_size = max(20.0, font_size * (available_url_w / ext_url.width))
        ctx.set_font_size(font_size)
        ext_url = ctx.text_extents(full_url)

    pill_w = min(pill_max_w, ext_url.width + 240.0)
    pill_x = pill_cx - (pill_w / 2.0)
    pill_y = y_pos - (pill_h / 2.0)

    # 1. Outer glow / shadow
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.45 * alpha)
    _rounded_rect(ctx, pill_x + 3, pill_y + 4, pill_w, pill_h, 24.0)
    ctx.fill()

    # 2. Glass dark background
    ctx.set_source_rgba(0.08, 0.10, 0.15, 0.95 * alpha)
    _rounded_rect(ctx, pill_x, pill_y, pill_w, pill_h, 24.0)
    ctx.fill_preserve()

    # 3. Glowing border (Neon Cyan / Electric Blue)
    ctx.set_source_rgba(0.2, 0.7, 1.0, 0.85 * alpha)
    ctx.set_line_width(3.0)
    ctx.stroke()

    # 4. GitHub Octocat circle icon on left
    icon_cx = pill_x + 42.0
    icon_cy = pill_y + (pill_h / 2.0)
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95 * alpha)
    ctx.arc(icon_cx, icon_cy, 18.0, 0, 2 * math.pi)
    ctx.fill()

    # Inner cat cutout
    ctx.set_source_rgba(0.08, 0.10, 0.15, 0.95 * alpha)
    ctx.arc(icon_cx, icon_cy, 10.0, 0, 2 * math.pi)
    ctx.fill()

    # 5. GitHub URL text (White / Bright Cyan)
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(font_size)
    ctx.set_source_rgba(0.95, 0.98, 1.0, 1.0 * alpha)
    url_x = icon_cx + 28.0
    url_y = pill_y + (pill_h / 2.0) + (ext_url.height / 2.5)
    ctx.move_to(url_x, url_y)
    ctx.show_text(full_url)

    # 6. Star count badge on right
    if stars_str:
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(24.0)
        ext_stars = ctx.text_extents(stars_str)
        star_pill_w = ext_stars.width + 26.0
        star_pill_h = 42.0
        star_pill_x = pill_x + pill_w - star_pill_w - 16.0
        star_pill_y = pill_y + (pill_h - star_pill_h) / 2.0

        ctx.set_source_rgba(1.0, 0.8, 0.1, 0.22 * alpha)
        _rounded_rect(ctx, star_pill_x, star_pill_y, star_pill_w, star_pill_h, 14.0)
        ctx.fill_preserve()
        ctx.set_source_rgba(1.0, 0.85, 0.2, 0.9 * alpha)
        ctx.set_line_width(1.8)
        ctx.stroke()

        ctx.set_source_rgba(1.0, 0.88, 0.25, 1.0 * alpha)
        ctx.move_to(star_pill_x + 13.0, star_pill_y + star_pill_h * 0.7)
        ctx.show_text(stars_str)

    ctx.restore()


def draw_github_cta_card(
    ctx,
    repo_slug: str,
    stars_str: str = "55,000+ Stars",
    y_center: float = 1250.0,
    scale: float = 1.0,
):
    """
    Dedicated Outro CTA Card featuring the repository URL and Star call-to-action.
    """
    ctx.save()
    card_w = min(MAX_SAFE_WIDTH, 880.0) * scale
    card_h = 320.0 * scale
    card_x = (CANVAS_WIDTH - card_w) / 2.0
    card_y = y_center - (card_h / 2.0)

    # Shadow
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.5)
    _rounded_rect(ctx, card_x + 6, card_y + 8, card_w, card_h, 32.0 * scale)
    ctx.fill()

    # Background gradient
    pat = cairo.LinearGradient(card_x, card_y, card_x + card_w, card_y + card_h)
    pat.add_color_stop_rgb(0.0, 0.10, 0.12, 0.18)
    pat.add_color_stop_rgb(1.0, 0.05, 0.07, 0.10)
    ctx.set_source(pat)
    _rounded_rect(ctx, card_x, card_y, card_w, card_h, 32.0 * scale)
    ctx.fill_preserve()

    # Neon border
    ctx.set_source_rgb(0.1, 0.9, 0.5)
    ctx.set_line_width(4.0 * scale)
    ctx.stroke()

    # Top CTA Header: "STAR THIS REPOSITORY ON GITHUB"
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28.0 * scale)
    ctx.set_source_rgb(0.1, 0.9, 0.5)
    ext_hdr = ctx.text_extents("★ STAR THIS REPO ON GITHUB ★")
    ctx.move_to(CANVAS_WIDTH / 2.0 - ext_hdr.width / 2.0, card_y + 60.0 * scale)
    ctx.show_text("★ STAR THIS REPO ON GITHUB ★")

    # Full GitHub URL in bold monospace
    full_url = f"github.com/{repo_slug}"
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    url_font_size = 42.0 * scale
    ctx.set_font_size(url_font_size)
    ext_url = ctx.text_extents(full_url)

    # Scale URL if it exceeds card inner width
    avail_w = card_w - (60.0 * scale)
    if ext_url.width > avail_w:
        url_font_size = max(24.0 * scale, url_font_size * (avail_w / ext_url.width))
        ctx.set_font_size(url_font_size)
        ext_url = ctx.text_extents(full_url)

    url_bg_w = ext_url.width + (40.0 * scale)
    url_bg_h = 72.0 * scale
    url_bg_x = CANVAS_WIDTH / 2.0 - (url_bg_w / 2.0)
    url_bg_y = card_y + 105.0 * scale

    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.6)
    _rounded_rect(ctx, url_bg_x, url_bg_y, url_bg_w, url_bg_h, 16.0 * scale)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.2, 0.7, 1.0, 0.7)
    ctx.set_line_width(2.0 * scale)
    ctx.stroke()

    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(CANVAS_WIDTH / 2.0 - ext_url.width / 2.0, url_bg_y + url_bg_h * 0.68)
    ctx.show_text(full_url)

    # Star count & Live button
    btn_w = 340.0 * scale
    btn_h = 60.0 * scale
    btn_x = CANVAS_WIDTH / 2.0 - (btn_w / 2.0)
    btn_y = card_y + 215.0 * scale

    ctx.set_source_rgb(0.95, 0.75, 0.1)
    _rounded_rect(ctx, btn_x, btn_y, btn_w, btn_h, 20.0 * scale)
    ctx.fill()

    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26.0 * scale)
    ctx.set_source_rgb(0.05, 0.05, 0.05)
    btn_text = f"★ STAR ({stars_str})"
    ext_btn = ctx.text_extents(btn_text)
    ctx.move_to(CANVAS_WIDTH / 2.0 - ext_btn.width / 2.0, btn_y + btn_h * 0.68)
    ctx.show_text(btn_text)

    ctx.restore()


def _rounded_rect(ctx, x, y, w, h, r):
    r = min(r, w / 2.0, h / 2.0)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()
