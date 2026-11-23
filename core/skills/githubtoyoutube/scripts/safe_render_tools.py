#!/usr/bin/env python3
"""
🛡️ SAFE RENDER TOOLS — GITHUB TO YOUTUBE SOVEREIGN ANIMATION ENGINE
Provides zero-overflow text rendering, auto-wrapping, dynamic font scaling,
prominent GitHub repository URL banners, kinetic subtitles, and Outro Dual-CTA cards.
"""

import math
import cairo

# -------------------------------------------------------------
# SAFE FRAME CONSTANTS (9:16 VERTICAL 1080x1920)
# -------------------------------------------------------------
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920

SAFE_MIN_X = 90
SAFE_MAX_X = 990
MAX_SAFE_WIDTH = SAFE_MAX_X - SAFE_MIN_X  # 900px usable width

SAFE_MIN_Y = 180  # Top UI margin
SAFE_MAX_Y = 1680 # Bottom YouTube Shorts UI margin
USABLE_HEIGHT = SAFE_MAX_Y - SAFE_MIN_Y

KINETIC_CAPTION_Y = 1500  # Safe anchored zone for dynamic subtitles


def wrap_text_to_width(ctx, text: str, max_width: float) -> list:
    """
    Splits text into lines that strictly do not exceed max_width (in pixels).
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
                # Word itself exceeds max_width; keep it on its own line
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def draw_safe_text_centered(
    ctx,
    text: str,
    cx: float = CANVAS_WIDTH / 2.0,
    cy: float = None,
    max_width: float = MAX_SAFE_WIDTH,
    base_font_size: float = 52.0,
    font_face: str = "Sans",
    font_weight: int = cairo.FONT_WEIGHT_BOLD,
    text_color=(1.0, 1.0, 1.0),
    outline_color=(0.0, 0.0, 0.0),
    outline_width: float = 12.0,
    line_spacing: float = 1.25,
    center_x: float = None,
    baseline_y: float = None,
    y_pos: float = None,
    font_size: float = None,
    color=None,
    bold: bool = True,
    bg_box: bool = False,
    bg_color=(0.0, 0.0, 0.0, 0.7),
    font_family: str = None,
    **kwargs,
):
    """
    Draws text guaranteed to fit within [SAFE_MIN_X, SAFE_MAX_X].
    Supports both legacy and modern calling conventions smoothly.
    """
    if font_family is not None:
        font_face = font_family
    if center_x is not None:
        cx = center_x
    if baseline_y is not None:
        cy = baseline_y
    elif y_pos is not None:
        cy = y_pos
    elif cy is None:
        cy = 500.0

    if font_size is not None:
        base_font_size = font_size
    if color is not None:
        text_color = color
    if not bold:
        font_weight = cairo.FONT_WEIGHT_NORMAL

    ctx.save()
    ctx.select_font_face(font_face, cairo.FONT_SLANT_NORMAL, font_weight)

    # First attempt at base_font_size
    ctx.set_font_size(base_font_size)
    lines = wrap_text_to_width(ctx, text, max_width)

    # Check if lines still exceed bounds; if so, scale down font dynamically
    current_font_size = base_font_size
    for _ in range(5):
        too_wide = False
        for line in lines:
            ext = ctx.text_extents(line)
            if ext.width > max_width:
                too_wide = True
                scale = max_width / max(1.0, ext.width)
                current_font_size = max(24.0, current_font_size * scale * 0.96)
                ctx.set_font_size(current_font_size)
                lines = wrap_text_to_width(ctx, text, max_width)
                break
        if not too_wide:
            break

    # Calculate vertical spacing
    line_height = current_font_size * line_spacing
    total_height = len(lines) * line_height
    start_y = cy - (total_height / 2.0) + (current_font_size * 0.8)

    for i, line in enumerate(lines):
        ext = ctx.text_extents(line)
        line_x = cx - (ext.width / 2.0)
        line_y = start_y + (i * line_height)

        # Background box if requested
        if bg_box:
            pad_x = 16.0
            pad_y = 8.0
            ctx.set_source_rgba(*bg_color)
            _rounded_rect(ctx, line_x - pad_x, line_y - ext.height - pad_y, ext.width + pad_x * 2, ext.height + pad_y * 2, 12.0)
            ctx.fill()

        # Draw black contrast outline
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
    repo_slug: str,  # e.g. "browser-use/browser-use" or "unclecode/crawl4ai"
    stars_str: str = "55k ★",
    y_pos: float = 230.0,
    alpha: float = 1.0,
    stars_count: str = None,
    t: float = None,
):
    """
    Draws a prominent, sleek GitHub repository pill at the top safe zone:
    [ GitHub Icon | github.com/owner/repo | ★ 55k ]
    Strictly constrained within the horizontal safe boundary (X: 90..990).
    """
    if stars_count is not None:
        stars_str = str(stars_count)
    if t is not None:
        alpha = min(1.0, max(0.0, t * 2.0))

    ctx.save()
    full_url = f"github.com/{repo_slug}"

    pill_max_w = min(MAX_SAFE_WIDTH, 880.0)
    pill_h = 76.0
    pill_cx = CANVAS_WIDTH / 2.0

    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    font_size = 32.0
    ctx.set_font_size(font_size)
    ext_url = ctx.text_extents(full_url)

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

    # 3. Cyan-teal neon border
    ctx.set_source_rgba(0.2, 0.8, 1.0, 0.85 * alpha)
    ctx.set_line_width(3.0)
    ctx.stroke()

    # 4. GitHub Octocat/Badge Icon (stylized mark)
    icon_cx = pill_x + 42.0
    icon_cy = y_pos
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95 * alpha)
    ctx.arc(icon_cx, icon_cy, 18.0, 0, 2 * math.pi)
    ctx.fill()

    ctx.set_source_rgba(0.08, 0.10, 0.15, alpha)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(18.0)
    octo_txt = "GH"
    ext_octo = ctx.text_extents(octo_txt)
    ctx.move_to(icon_cx - ext_octo.width / 2.0, icon_cy + ext_octo.height / 2.0)
    ctx.show_text(octo_txt)

    # 5. Centered Monospace URL
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(font_size)
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.98 * alpha)
    url_x = pill_x + 72.0
    ctx.move_to(url_x, y_pos + (ext_url.height / 2.0) - 2.0)
    ctx.show_text(full_url)

    # 6. Star badge on the right
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24.0)
    ext_stars = ctx.text_extents(stars_str)
    star_pill_w = ext_stars.width + 26.0
    star_pill_h = 38.0
    star_pill_x = pill_x + pill_w - star_pill_w - 14.0
    star_pill_y = y_pos - (star_pill_h / 2.0)

    ctx.set_source_rgba(0.95, 0.75, 0.1, 0.95 * alpha)
    _rounded_rect(ctx, star_pill_x, star_pill_y, star_pill_w, star_pill_h, 12.0)
    ctx.fill()

    ctx.set_source_rgba(0.08, 0.08, 0.08, alpha)
    ctx.move_to(star_pill_x + 13.0, y_pos + (ext_stars.height / 2.0) - 2.0)
    ctx.show_text(stars_str)

    ctx.restore()


def draw_github_cta_card(
    ctx,
    repo_slug: str = None,
    stars_str: str = "55,000+ Stars",
    y_center: float = 1250.0,
    scale: float = 1.0,
    stars_count: str = None,
    t: float = None,
    repo_owner: str = None,
    repo_name: str = None,
    **kwargs,
):
    """
    Dedicated Outro CTA Card featuring the repository URL and Star call-to-action.
    """
    if repo_slug is None:
        if repo_owner and repo_name:
            repo_slug = f"{repo_owner}/{repo_name}"
        else:
            repo_slug = "owner/repo"

    if stars_count is not None:
        stars_str = str(stars_count)

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
    ctx.set_source_rgba(0.08, 0.11, 0.18, 0.98)
    _rounded_rect(ctx, card_x, card_y, card_w, card_h, 32.0 * scale)
    ctx.fill_preserve()

    # Neon border
    ctx.set_source_rgb(0.1, 0.9, 0.5)
    ctx.set_line_width(4.0 * scale)
    ctx.stroke()

    # Top CTA Header: "STAR THIS REPOSITORY ON GITHUB"
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(32.0 * scale)
    ctx.set_source_rgb(0.95, 0.95, 0.95)
    header_txt = "★ STAR THIS REPOSITORY ON GITHUB ★"
    ext_hdr = ctx.text_extents(header_txt)
    ctx.move_to(CANVAS_WIDTH / 2.0 - ext_hdr.width / 2.0, card_y + 60.0 * scale)
    ctx.show_text(header_txt)

    # Full GitHub URL in bold monospace
    full_url = f"github.com/{repo_slug}"
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    url_font_size = 42.0 * scale
    ctx.set_font_size(url_font_size)
    ext_url = ctx.text_extents(full_url)

    # Scale down if needed
    avail_w = card_w - 60.0 * scale
    if ext_url.width > avail_w:
        url_font_size = url_font_size * (avail_w / ext_url.width)
        ctx.set_font_size(url_font_size)
        ext_url = ctx.text_extents(full_url)

    url_bg_w = ext_url.width + 48.0 * scale
    url_bg_h = 68.0 * scale
    url_bg_x = CANVAS_WIDTH / 2.0 - (url_bg_w / 2.0)
    url_bg_y = card_y + 105.0 * scale

    ctx.set_source_rgba(0.02, 0.05, 0.10, 0.6)
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


def draw_safe_kinetic_caption(
    ctx,
    text: str,
    t: float = 0.0,
    y_pos: float = KINETIC_CAPTION_Y,
    font_size: float = 46.0,
    color=(1.0, 1.0, 1.0),
    accent_color=(1.0, 0.85, 0.1),
):
    """
    Draws a responsive, animated kinetic caption pill at bottom safe area.
    """
    ctx.save()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(font_size)

    lines = wrap_text_to_width(ctx, text, MAX_SAFE_WIDTH - 60.0)
    if not lines:
        ctx.restore()
        return

    line_h = font_size * 1.25
    total_h = len(lines) * line_h + 30.0

    # Draw dark semi-translucent pill container
    max_line_w = max([ctx.text_extents(l).width for l in lines])
    pill_w = min(MAX_SAFE_WIDTH, max_line_w + 60.0)
    pill_x = (CANVAS_WIDTH - pill_w) / 2.0
    pill_y = y_pos - (total_h / 2.0)

    # Outer shadow
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.6)
    _rounded_rect(ctx, pill_x + 3, pill_y + 4, pill_w, total_h, 20.0)
    ctx.fill()

    # Dark background box
    ctx.set_source_rgba(0.06, 0.07, 0.12, 0.88)
    _rounded_rect(ctx, pill_x, pill_y, pill_w, total_h, 20.0)
    ctx.fill_preserve()

    # Subtle accent border
    ctx.set_source_rgba(0.3, 0.7, 1.0, 0.5)
    ctx.set_line_width(2.5)
    ctx.stroke()

    # Text lines
    start_y = pill_y + 22.0 + font_size * 0.8
    for i, line in enumerate(lines):
        ext = ctx.text_extents(line)
        line_x = (CANVAS_WIDTH - ext.width) / 2.0
        line_y = start_y + (i * line_h)

        # Black stroke
        ctx.set_source_rgba(0.0, 0.0, 0.0, 0.95)
        ctx.set_line_width(8.0)
        ctx.move_to(line_x, line_y)
        ctx.text_path(line)
        ctx.stroke()

        # Fill text
        ctx.set_source_rgb(*color)
        ctx.move_to(line_x, line_y)
        ctx.show_text(line)

    ctx.restore()


def _rounded_rect(ctx, x, y, w, h, r):
    r = min(r, w / 2.0, h / 2.0)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()
