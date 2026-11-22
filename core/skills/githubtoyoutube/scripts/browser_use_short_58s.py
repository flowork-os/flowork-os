#!/usr/bin/env python3
"""
🎬 SOVEREIGN YOUTUBE SHORT: BROWSER-USE (TRENDING GITHUB REPO)
Repository: browser-use/browser-use (35,000+ Stars)
Specs: 1080x1920 (9:16 Vertical Short), 30 fps, 57.5s, PyCairo Cartoon Rendering
Platform Safe Zone: Bottom 320px clear, top 180px branded banner
Audio: Dual mastered cartoon orchestral BGM + SFX + Edge-TTS (en-US-ChristopherNeural)
"""

import math
import os
import subprocess
import sys
import cairo
import numpy as np

# Resolution & Frame Rate
W, H = 1080, 1920
FPS = 30
DURATION_SEC = 57.5
TOTAL_FRAMES = int(DURATION_SEC * FPS)
FLOOR_Y = 1520

# Safe Area Constants
HEADER_TOP = 140
FOOTER_BOTTOM = 1600

# File Paths
AUDIO_WAV = "/tmp/browser_use_final_audio_mastered.wav"
OUTPUT_MP4 = "/opt/floworkos/documents/videos/browser-use-short/BROWSER_USE_GITHUB_CARTOON_SHORT.mp4"
USER_OUTPUT_MP4 = "/home/mrflow/Documents/videos/browser-use-short/BROWSER_USE_GITHUB_CARTOON_SHORT.mp4"
CONTACT_SHEET_PNG = "/opt/floworkos/documents/videos/browser-use-short/BROWSER_USE_CARTOON_SHORT_contact_sheet.png"
USER_CONTACT_SHEET_PNG = "/home/mrflow/Documents/videos/browser-use-short/BROWSER_USE_CARTOON_SHORT_contact_sheet.png"

# Colors
C_DARK_BG = (0.07, 0.09, 0.14)
C_DEEP_NAVY = (0.11, 0.15, 0.22)
C_ACCENT_CYAN = (0.12, 0.82, 0.95)
C_ACCENT_AMBER = (1.00, 0.72, 0.12)
C_ACCENT_GREEN = (0.18, 0.86, 0.45)
C_ACCENT_RED = (0.95, 0.26, 0.28)
C_WHITE = (0.96, 0.97, 1.00)
C_TEXT_MUTED = (0.60, 0.65, 0.75)


def draw_star(ctx, cx, cy, r_outer=20, r_inner=9, color=C_ACCENT_AMBER):
    ctx.save()
    ctx.set_source_rgb(*color)
    ctx.new_path()
    for i in range(10):
        angle = -math.pi / 2 + i * (math.pi / 5)
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            ctx.move_to(x, y)
        else:
            ctx.line_to(x, y)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(0, 0, 0, 0.5)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()


def draw_comic_sparks(ctx, cx, cy, scale=1.0, color=C_ACCENT_AMBER):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    ctx.set_source_rgb(*color)
    for i in range(8):
        angle = i * (math.pi / 4)
        ctx.save()
        ctx.rotate(angle)
        ctx.new_path()
        ctx.move_to(10, 0)
        ctx.line_to(35, 8)
        ctx.line_to(55, 0)
        ctx.line_to(35, -8)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    ctx.restore()


def draw_comic_bubble(ctx, x, y, w, h, text, tail_dir="down"):
    ctx.save()
    # Bubble shadow
    ctx.set_source_rgba(0, 0, 0, 0.35)
    ctx.new_sub_path()
    ctx.arc(x + w - 24 + 6, y + 24 + 6, 24, -math.pi / 2, 0)
    ctx.arc(x + w - 24 + 6, y + h - 24 + 6, 24, 0, math.pi / 2)
    ctx.arc(x + 24 + 6, y + h - 24 + 6, 24, math.pi / 2, math.pi)
    ctx.arc(x + 24 + 6, y + 24 + 6, 24, math.pi, 3 * math.pi / 2)
    ctx.close_path()
    ctx.fill()

    # Main Bubble Body
    ctx.set_source_rgb(0.98, 0.98, 0.99)
    ctx.new_sub_path()
    ctx.arc(x + w - 24, y + 24, 24, -math.pi / 2, 0)
    ctx.arc(x + w - 24, y + h - 24, 24, 0, math.pi / 2)
    ctx.arc(x + 24, y + h - 24, 24, math.pi / 2, math.pi)
    ctx.arc(x + 24, y + 24, 24, math.pi, 3 * math.pi / 2)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0.08, 0.10, 0.15)
    ctx.set_line_width(5)
    ctx.stroke()

    # Comic Text
    ctx.set_source_rgb(0.08, 0.10, 0.15)
    ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(36)
    ext = ctx.text_extents(text)
    ctx.move_to(x + (w - ext.width) / 2, y + (h + ext.height) / 2 - 2)
    ctx.show_text(text)
    ctx.restore()


def draw_studio_environment(ctx, t, theme="navy"):
    ctx.save()
    # High-contrast non-white background gradient
    pat = cairo.LinearGradient(0, 0, 0, H)
    if theme == "navy":
        pat.add_color_stop_rgb(0.0, 0.08, 0.11, 0.17)
        pat.add_color_stop_rgb(0.7, 0.05, 0.07, 0.12)
        pat.add_color_stop_rgb(1.0, 0.03, 0.04, 0.08)
    elif theme == "crimson":
        pat.add_color_stop_rgb(0.0, 0.20, 0.06, 0.08)
        pat.add_color_stop_rgb(0.7, 0.12, 0.04, 0.05)
        pat.add_color_stop_rgb(1.0, 0.05, 0.02, 0.03)
    elif theme == "cyan":
        pat.add_color_stop_rgb(0.0, 0.04, 0.16, 0.22)
        pat.add_color_stop_rgb(0.7, 0.03, 0.09, 0.14)
        pat.add_color_stop_rgb(1.0, 0.02, 0.05, 0.08)
    else:
        pat.add_color_stop_rgb(0.0, 0.08, 0.11, 0.17)
        pat.add_color_stop_rgb(1.0, 0.03, 0.04, 0.08)

    ctx.rectangle(0, 0, W, H)
    ctx.set_source(pat)
    ctx.fill()

    # Subtle Perspective Studio Floor
    f_pat = cairo.LinearGradient(0, FLOOR_Y, 0, H)
    f_pat.add_color_stop_rgb(0.0, 0.02, 0.03, 0.06)
    f_pat.add_color_stop_rgb(1.0, 0.01, 0.01, 0.03)
    ctx.rectangle(0, FLOOR_Y, W, H - FLOOR_Y)
    ctx.set_source(f_pat)
    ctx.fill()

    # Glowing floor rim line
    ctx.move_to(0, FLOOR_Y)
    ctx.line_to(W, FLOOR_Y)
    ctx.set_source_rgba(0.2, 0.6, 0.9, 0.45)
    ctx.set_line_width(4)
    ctx.stroke()

    # Subtle animated studio grid in ceiling/background
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.03)
    ctx.set_line_width(1.5)
    for gx in range(60, W, 120):
        ctx.move_to(gx, 0)
        ctx.line_to(gx, FLOOR_Y)
        ctx.stroke()

    ctx.restore()


def draw_master_brand_header(ctx, t):
    ctx.save()
    # Stacked Header Pill
    ctx.set_source_rgba(0.05, 0.08, 0.13, 0.88)
    ctx.new_sub_path()
    ctx.arc(W - 80 - 24, 60 + 24, 24, -math.pi / 2, 0)
    ctx.arc(W - 80 - 24, 60 + 85 - 24, 24, 0, math.pi / 2)
    ctx.arc(80 + 24, 60 + 85 - 24, 24, math.pi / 2, math.pi)
    ctx.arc(80 + 24, 60 + 24, 24, math.pi, 3 * math.pi / 2)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(0.2, 0.7, 0.9, 0.6)
    ctx.set_line_width(2.5)
    ctx.stroke()

    # Left Badge: GITHUB TRENDING
    ctx.set_source_rgb(0.18, 0.86, 0.45)
    ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.move_to(110, 114)
    ctx.show_text("⭐ GITHUB: BROWSER-USE")

    # Right Badge: FLOWORKOS.COM
    ctx.set_source_rgb(0.12, 0.82, 0.95)
    ctx.move_to(W - 400, 114)
    ctx.show_text("POWERED BY FLOWORKOS.COM")

    ctx.restore()


def draw_senior_dev(ctx, x, y, scale=1.0, state=None):
    if state is None:
        state = {}
    pose = state.get("pose", "idle")
    t = state.get("t", 0.0)

    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)

    # Elastic breathing bounce
    squash = 1.0 + 0.03 * math.sin(t * 8)
    stretch = 1.0 - 0.03 * math.sin(t * 8)
    ctx.scale(squash, stretch)

    # Shadow on floor
    ctx.save()
    ctx.scale(1.0, 0.3)
    ctx.set_source_rgba(0, 0, 0, 0.4)
    ctx.arc(0, 360, 95, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()

    # Pants & Shoes (Rubber hose legs)
    ctx.set_source_rgb(0.15, 0.20, 0.30)
    ctx.set_line_width(24)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    # Left leg
    ctx.move_to(-35, 120)
    ctx.curve_to(-40, 180, -45, 230, -35, 270)
    ctx.stroke()
    # Right leg
    ctx.move_to(35, 120)
    ctx.curve_to(40, 180, 45, 230, 35, 270)
    ctx.stroke()

    # Shoes (Cyan sneakers)
    ctx.set_source_rgb(0.12, 0.82, 0.95)
    ctx.arc(-42, 275, 24, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(42, 275, 24, 0, 2 * math.pi)
    ctx.fill()

    # Torso (Hoodie)
    ctx.set_source_rgb(0.18, 0.24, 0.36)
    ctx.new_sub_path()
    ctx.arc(55, 30, 25, -math.pi / 2, 0)
    ctx.arc(55, 120, 25, 0, math.pi / 2)
    ctx.arc(-55, 120, 25, math.pi / 2, math.pi)
    ctx.arc(-55, 30, 25, math.pi, 3 * math.pi / 2)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0.08, 0.11, 0.18)
    ctx.set_line_width(6)
    ctx.stroke()

    # Hoodie Logo (Terminal Prompt >_)
    ctx.set_source_rgb(0.18, 0.86, 0.45)
    ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(32)
    ctx.move_to(-24, 85)
    ctx.show_text(">_")

    # Head (Cartoon Oval)
    head_y = -35 + 4 * math.sin(t * 8)
    ctx.set_source_rgb(0.98, 0.82, 0.68)
    ctx.arc(0, head_y, 60, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.set_line_width(6)
    ctx.stroke()

    # Cool Glasses
    ctx.set_source_rgb(0.12, 0.14, 0.20)
    ctx.rectangle(-45, head_y - 18, 38, 28)
    ctx.rectangle(7, head_y - 18, 38, 28)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.12, 0.82, 0.95)
    ctx.set_line_width(4)
    ctx.stroke()
    # Glass bridge
    ctx.move_to(-7, head_y - 4)
    ctx.line_to(7, head_y - 4)
    ctx.stroke()

    # Beanie / Hair
    ctx.set_source_rgb(0.85, 0.35, 0.15)
    ctx.new_sub_path()
    ctx.arc(0, head_y - 30, 62, math.pi, 2 * math.pi)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.set_line_width(6)
    ctx.stroke()

    # Arms & Poses
    ctx.set_line_width(22)
    ctx.set_source_rgb(0.18, 0.24, 0.36)
    if pose == "panic":
        # Hands on head pulling hair!
        ctx.move_to(-55, 30)
        ctx.curve_to(-95, -20, -75, -80, -25, head_y - 50)
        ctx.stroke()
        ctx.move_to(55, 30)
        ctx.curve_to(95, -20, 75, -80, 25, head_y - 50)
        ctx.stroke()
    elif pose == "point_right":
        # Right arm pointing forward
        ctx.move_to(-55, 30)
        ctx.curve_to(-75, 70, -70, 90, -45, 95)
        ctx.stroke()
        ctx.move_to(55, 30)
        ctx.curve_to(110, 20, 160, 20, 210, 25)
        ctx.stroke()
        # Pointing hand
        ctx.set_source_rgb(0.98, 0.82, 0.68)
        ctx.arc(220, 25, 18, 0, 2 * math.pi)
        ctx.fill()
    else:
        # Relaxed coffee sipping pose
        ctx.move_to(-55, 30)
        ctx.curve_to(-85, 60, -75, 95, -45, 95)
        ctx.stroke()
        ctx.move_to(55, 30)
        ctx.curve_to(95, 60, 70, 85, 45, 75)
        ctx.stroke()
        # Coffee Mug
        ctx.set_source_rgb(0.95, 0.95, 0.98)
        ctx.rectangle(35, 60, 32, 40)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.1, 0.1, 0.1)
        ctx.set_line_width(3)
        ctx.stroke()

    ctx.restore()


def draw_ai_agent_bot(ctx, x, y, scale=1.0, t=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)

    # Hover bobbing
    bob_y = 12 * math.sin(t * 6)
    ctx.translate(0, bob_y)

    # Drop shadow
    ctx.save()
    ctx.scale(1.0, 0.3)
    ctx.set_source_rgba(0, 0, 0, 0.3)
    ctx.arc(0, 320, 85, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()

    # Antenna
    ctx.set_source_rgb(0.12, 0.82, 0.95)
    ctx.set_line_width(6)
    ctx.move_to(0, -90)
    ctx.line_to(0, -135)
    ctx.stroke()
    # Antenna bulb (blinking)
    bulb_alpha = 0.6 + 0.4 * math.sin(t * 12)
    ctx.set_source_rgba(1.0, 0.72, 0.12, bulb_alpha)
    ctx.arc(0, -145, 16, 0, 2 * math.pi)
    ctx.fill()

    # Bot Head / Body (Smooth Capsule)
    ctx.set_source_rgb(0.92, 0.95, 1.0)
    ctx.arc(0, -10, 85, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.12, 0.15, 0.22)
    ctx.set_line_width(7)
    ctx.stroke()

    # Dark Visor Screen
    ctx.set_source_rgb(0.08, 0.11, 0.18)
    ctx.arc(0, -12, 60, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.12, 0.82, 0.95)
    ctx.set_line_width(4)
    ctx.stroke()

    # Glowing Cyan AI Eyes (Cybernetic Expressive)
    ctx.set_source_rgb(0.12, 0.82, 0.95)
    ctx.arc(-24, -14, 14, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(24, -14, 14, 0, 2 * math.pi)
    ctx.fill()

    # Little Jet Thruster Flame
    flame_h = 35 + 15 * math.sin(t * 24)
    ctx.set_source_rgba(0.12, 0.82, 0.95, 0.8)
    ctx.new_path()
    ctx.move_to(-25, 75)
    ctx.line_to(0, 75 + flame_h)
    ctx.line_to(25, 75)
    ctx.close_path()
    ctx.fill()

    # Robotic Pointer Arm / Cursor
    hand_angle = math.sin(t * 5) * 0.3
    ctx.save()
    ctx.translate(65, 20)
    ctx.rotate(hand_angle)
    ctx.set_source_rgb(0.12, 0.82, 0.95)
    ctx.set_line_width(12)
    ctx.move_to(0, 0)
    ctx.line_to(70, -20)
    ctx.stroke()
    # Robotic Finger/Cursor
    ctx.new_path()
    ctx.move_to(70, -20)
    ctx.line_to(100, -35)
    ctx.line_to(95, -15)
    ctx.close_path()
    ctx.fill()
    ctx.restore()

    ctx.restore()


def draw_browser_simulator(ctx, x, y, w, h, t, url="https://booking.com/flights"):
    ctx.save()
    # Browser Window Shadow
    ctx.set_source_rgba(0, 0, 0, 0.45)
    ctx.rectangle(x + 12, y + 12, w, h)
    ctx.fill()

    # Main Browser Shell
    ctx.set_source_rgb(0.12, 0.15, 0.22)
    ctx.rectangle(x, y, w, h)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.25, 0.30, 0.42)
    ctx.set_line_width(4)
    ctx.stroke()

    # Browser Top Chrome / Title Bar
    ctx.set_source_rgb(0.08, 0.10, 0.15)
    ctx.rectangle(x, y, w, 70)
    ctx.fill()

    # Window Controls (Red, Yellow, Green)
    ctx.set_source_rgb(0.95, 0.26, 0.28)
    ctx.arc(x + 28, y + 35, 9, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(1.0, 0.72, 0.12)
    ctx.arc(x + 56, y + 35, 9, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(0.18, 0.86, 0.45)
    ctx.arc(x + 84, y + 35, 9, 0, 2 * math.pi)
    ctx.fill()

    # Omnibar / URL Bar
    ctx.set_source_rgb(0.16, 0.20, 0.28)
    ctx.rectangle(x + 120, y + 15, w - 145, 40)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.25, 0.32, 0.45)
    ctx.set_line_width(2)
    ctx.stroke()

    # URL Text
    ctx.set_source_rgb(0.7, 0.8, 0.9)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(20)
    ctx.move_to(x + 140, y + 42)
    ctx.show_text("🔒 " + url)

    # Web Page Body (Clean White/Gray)
    ctx.set_source_rgb(0.96, 0.97, 0.99)
    ctx.rectangle(x + 4, y + 72, w - 8, h - 76)
    ctx.fill()

    # Webpage mock elements
    # Header banner
    ctx.set_source_rgb(0.05, 0.25, 0.65)
    ctx.rectangle(x + 15, y + 85, w - 30, 70)
    ctx.fill()
    ctx.set_source_rgb(1, 1, 1)
    ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ctx.move_to(x + 35, y + 130)
    ctx.show_text("FLIGHT SEARCH & BOOKING AUTOPILOT")

    # Form Fields with Bounding Boxes
    fields = [
        ("From: Tokyo (HND)", 180, 220),
        ("To: San Francisco (SFO)", 420, 220),
        ("Date: Nov 25, 2026", 180, 330),
        ("Passengers: 1 Adult", 420, 330)
    ]
    for idx, (label, fx, fy) in enumerate(fields, 1):
        ctx.set_source_rgb(0.90, 0.92, 0.96)
        ctx.rectangle(x + fx - 150, y + fy - 35, 220, 55)
        ctx.fill_preserve()
        # Bounding box tag (AI agent view)
        ctx.set_source_rgb(0.95, 0.26, 0.28)
        ctx.set_line_width(2.5)
        ctx.stroke()

        # Numeric index badge [1], [2], etc.
        ctx.set_source_rgb(0.95, 0.26, 0.28)
        ctx.rectangle(x + fx - 150, y + fy - 52, 28, 20)
        ctx.fill()
        ctx.set_source_rgb(1, 1, 1)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(14)
        ctx.move_to(x + fx - 145, y + fy - 37)
        ctx.show_text(str(idx))

        # Field Label
        ctx.set_source_rgb(0.15, 0.18, 0.25)
        ctx.set_font_size(16)
        ctx.move_to(x + fx - 140, y + fy)
        ctx.show_text(label)

    # Search Button (Clicked by Agent)
    btn_x = x + (w - 260) / 2
    btn_y = y + 430
    ctx.set_source_rgb(0.18, 0.75, 0.35)
    ctx.rectangle(btn_x, btn_y, 260, 60)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.1, 0.4, 0.15)
    ctx.set_line_width(3)
    ctx.stroke()

    # Bounding Box [5] on button
    ctx.set_source_rgb(0.95, 0.26, 0.28)
    ctx.rectangle(btn_x - 5, btn_y - 20, 32, 22)
    ctx.fill()
    ctx.set_source_rgb(1, 1, 1)
    ctx.set_font_size(14)
    ctx.move_to(btn_x + 6, btn_y - 5)
    ctx.show_text("5")

    ctx.set_source_rgb(1, 1, 1)
    ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26)
    ctx.move_to(btn_x + 35, btn_y + 40)
    ctx.show_text("SEARCH FLIGHTS ✈️")

    # Animated Cursor clicking button!
    cx_t = btn_x + 180 + 30 * math.cos(t * 4)
    cy_t = btn_y + 35 + 15 * math.sin(t * 4)
    ctx.set_source_rgb(0.12, 0.82, 0.95)
    ctx.new_path()
    ctx.move_to(cx_t, cy_t)
    ctx.line_to(cx_t + 25, cy_t + 35)
    ctx.line_to(cx_t + 12, cy_t + 35)
    ctx.line_to(cx_t + 20, cy_t + 55)
    ctx.line_to(cx_t + 8, cy_t + 58)
    ctx.line_to(cx_t, cy_t + 40)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0, 0, 0)
    ctx.set_line_width(3)
    ctx.stroke()

    # Click ripple wave
    ripple = (t * 4) % 1.0
    ctx.arc(cx_t, cy_t, 45 * ripple, 0, 2 * math.pi)
    ctx.set_source_rgba(0.12, 0.82, 0.95, 1.0 - ripple)
    ctx.set_line_width(4)
    ctx.stroke()

    ctx.restore()


def draw_subtitle_banner(ctx, text):
    ctx.save()
    sub_y = 1630
    sub_h = 130

    # Gradient Subtitle Box
    pat = cairo.LinearGradient(0, sub_y, 0, sub_y + sub_h)
    pat.add_color_stop_rgba(0.0, 0.05, 0.08, 0.14, 0.94)
    pat.add_color_stop_rgba(1.0, 0.02, 0.04, 0.08, 0.98)

    ctx.set_source(pat)
    ctx.rectangle(40, sub_y, W - 80, sub_h)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.18, 0.86, 0.45, 0.8)
    ctx.set_line_width(3.5)
    ctx.stroke()

    # Multi-line word-wrap text
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(36)

    words = text.split(" ")
    lines = []
    curr = []
    for w in words:
        curr.append(w)
        line_str = " ".join(curr)
        if ctx.text_extents(line_str).width > (W - 140):
            curr.pop()
            lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))

    total_text_h = len(lines) * 44
    start_y = sub_y + (sub_h - total_text_h) / 2 + 32
    for i, line in enumerate(lines):
        ext = ctx.text_extents(line)
        ctx.move_to(W / 2 - ext.width / 2, start_y + i * 44)
        ctx.show_text(line)

    ctx.restore()


def render_scene(ctx, t):
    # Scene 0: 0.0 - 4.2s (The Hook)
    if t < 4.2:
        draw_studio_environment(ctx, t, theme="navy")
        draw_master_brand_header(ctx, t)

        # Giant Comic Title Card
        title_y = 380 + 15 * math.sin(t * 8)
        draw_comic_bubble(ctx, 80, title_y, W - 160, 220, "STOP CLICKING MANUALLY!")

        draw_comic_sparks(ctx, 160, title_y - 20, scale=1.3, color=C_ACCENT_AMBER)
        draw_comic_sparks(ctx, W - 160, title_y + 200, scale=1.3, color=C_ACCENT_CYAN)

        # Dev pointing shock, AI agent bot appearing
        draw_senior_dev(ctx, 320, FLOOR_Y - 140, scale=1.05, state={"pose": "point_right", "t": t})
        draw_ai_agent_bot(ctx, 740, FLOOR_Y - 260, scale=1.1, t=t)

        draw_subtitle_banner(ctx, "Stop clicking buttons like 1999! What if AI browsed the web for you?")

    # Scene 1: 4.2 - 14.5s (The Nightmare: Broken Scrapers & Captchas)
    elif t < 14.5:
        draw_studio_environment(ctx, t, theme="crimson")
        draw_master_brand_header(ctx, t)

        # Big Alert Header
        ctx.save()
        ctx.set_source_rgb(0.95, 0.26, 0.28)
        ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(68)
        ext = ctx.text_extents("WEB SCRAPING NIGHTMARE!")
        ctx.move_to(W / 2 - ext.width / 2, 280)
        ctx.show_text("WEB SCRAPING NIGHTMARE!")
        ctx.restore()

        # Captcha & Broken Code Wall Card
        card_w, card_h = 760, 520
        card_x, card_y = (W - card_w) / 2, 340
        ctx.set_source_rgb(0.12, 0.08, 0.10)
        ctx.rectangle(card_x, card_y, card_w, card_h)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.95, 0.26, 0.28)
        ctx.set_line_width(5)
        ctx.stroke()

        # Huge 403 Forbidden Stamp
        ctx.save()
        ctx.translate(W / 2, card_y + 160)
        ctx.rotate(-0.12)
        ctx.set_source_rgb(0.95, 0.26, 0.28)
        ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(72)
        ext = ctx.text_extents("🚫 403 FORBIDDEN")
        ctx.move_to(-ext.width / 2, 0)
        ctx.show_text("🚫 403 FORBIDDEN")
        ctx.restore()

        # Captcha Puzzle Mockup
        ctx.set_source_rgb(0.9, 0.92, 0.96)
        ctx.rectangle(card_x + 60, card_y + 240, card_w - 120, 220)
        ctx.fill()
        ctx.set_source_rgb(0.2, 0.2, 0.25)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(24)
        ctx.move_to(card_x + 90, card_y + 290)
        ctx.show_text("CAPTCHA: Select all traffic lights...")
        ctx.move_to(card_x + 90, card_y + 350)
        ctx.set_source_rgb(0.8, 0.1, 0.1)
        ctx.show_text("💥 ERROR: DOM Selector '#btn-submit' changed!")

        # Dev Panic
        draw_senior_dev(ctx, W / 2, FLOOR_Y - 140, scale=1.1, state={"pose": "panic", "t": t})

        draw_subtitle_banner(ctx, "Captchas block you, DOM layouts break, and scrapers turn into spaghetti code!")

    # Scene 2: 14.5 - 28.0s (The Breakthrough: browser-use 35k Stars)
    elif t < 28.0:
        draw_studio_environment(ctx, t, theme="cyan")
        draw_master_brand_header(ctx, t)

        # Huge Breakthrough Card
        ctx.save()
        ctx.set_source_rgb(0.12, 0.82, 0.95)
        ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(64)
        ext = ctx.text_extents("ENTER: BROWSER-USE")
        ctx.move_to(W / 2 - ext.width / 2, 280)
        ctx.show_text("ENTER: BROWSER-USE")
        ctx.restore()

        # GitHub Repo Card
        card_w, card_h = 820, 560
        card_x, card_y = (W - card_w) / 2, 330
        ctx.set_source_rgb(0.08, 0.12, 0.18)
        ctx.rectangle(card_x, card_y, card_w, card_h)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.12, 0.82, 0.95)
        ctx.set_line_width(4)
        ctx.stroke()

        # GitHub Stats inside card
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(44)
        ctx.move_to(card_x + 50, card_y + 80)
        ctx.show_text("📦 browser-use / browser-use")

        ctx.set_font_size(28)
        ctx.set_source_rgb(0.7, 0.8, 0.9)
        ctx.move_to(card_x + 50, card_y + 140)
        ctx.show_text("Make websites accessible for AI agents.")

        # Star Badge
        draw_star(ctx, card_x + 90, card_y + 240, r_outer=32, r_inner=14, color=C_ACCENT_AMBER)
        ctx.set_source_rgb(1.0, 0.85, 0.15)
        ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(52)
        ctx.move_to(card_x + 145, card_y + 258)
        ctx.show_text("35,800+ STARS ON GITHUB")

        # Feature Badges
        pills = ["⚡ Chromium Control", "👁️ Vision + DOM Loop", "🤖 LLM Autonomous"]
        for p_i, pill in enumerate(pills):
            p_y = card_y + 340 + p_i * 65
            ctx.set_source_rgb(0.15, 0.22, 0.32)
            ctx.rectangle(card_x + 50, p_y - 30, 480, 50)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.18, 0.86, 0.45)
            ctx.set_line_width(2.5)
            ctx.stroke()

            ctx.set_source_rgb(1, 1, 1)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(24)
            ctx.move_to(card_x + 75, p_y + 6)
            ctx.show_text(pill)

        # Characters
        draw_senior_dev(ctx, 240, FLOOR_Y - 140, scale=0.95, state={"pose": "idle", "t": t})
        draw_ai_agent_bot(ctx, 800, FLOOR_Y - 260, scale=1.1, t=t)

        draw_subtitle_banner(ctx, "Enter browser-use: 35,000+ stars! Connects LLMs directly to Chromium.")

    # Scene 3: 28.0 - 42.0s (How It Works: Autonomous Autopilot)
    elif t < 42.0:
        draw_studio_environment(ctx, t, theme="navy")
        draw_master_brand_header(ctx, t)

        # Active Browser Simulator in action!
        draw_browser_simulator(ctx, 100, 240, W - 200, 720, t)

        # Bot pointing and acting
        draw_ai_agent_bot(ctx, 920, 540, scale=0.85, t=t)
        draw_senior_dev(ctx, 160, FLOOR_Y - 140, scale=0.9, state={"pose": "point_right", "t": t})

        draw_subtitle_banner(ctx, "No fragile CSS selectors! Extracts clickable coordinates & browses like a human.")

    # Scene 4: 42.0 - 51.5s (Flowork OS Integration & Superpower)
    elif t < 51.5:
        draw_studio_environment(ctx, t, theme="cyan")
        draw_master_brand_header(ctx, t)

        # Flowork OS Superpower Header
        ctx.save()
        ctx.set_source_rgb(0.18, 0.86, 0.45)
        ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(60)
        ext = ctx.text_extents("FLOWORK OS: RING-0 ACCELERATION")
        ctx.move_to(W / 2 - ext.width / 2, 280)
        ctx.show_text("FLOWORK OS: RING-0 ACCELERATION")
        ctx.restore()

        # Architecture Comparison Card
        card_w, card_h = 860, 600
        card_x, card_y = (W - card_w) / 2, 330
        ctx.set_source_rgb(0.06, 0.10, 0.16)
        ctx.rectangle(card_x, card_y, card_w, card_h)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.18, 0.86, 0.45)
        ctx.set_line_width(4)
        ctx.stroke()

        # Features list
        pillars = [
            ("🛡️ Landlock Ring-0 Sandbox", "Zero chance of malicious prompt injection escaping"),
            ("🚀 Direct DRM Framebuffer Capture", "Microsecond visual loop at hardware GPU speed"),
            ("⌨️ Virtual UInput Hardware HID", "Bypasses bot detection with true kernel HID events"),
            ("⚡ Sovereign Local Inference", "Runs alongside Ollama and zero-cloud LLM gateways")
        ]
        for p_idx, (p_title, p_desc) in enumerate(pillars):
            py = card_y + 60 + p_idx * 130
            ctx.set_source_rgb(0.12, 0.82, 0.95)
            ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(32)
            ctx.move_to(card_x + 40, py)
            ctx.show_text(p_title)

            ctx.set_source_rgb(0.8, 0.85, 0.95)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(22)
            ctx.move_to(card_x + 40, py + 36)
            ctx.show_text(p_desc)

        # Character
        draw_senior_dev(ctx, 540, FLOOR_Y - 140, scale=1.05, state={"pose": "idle", "t": t})

        draw_subtitle_banner(ctx, "Pair with Flowork OS for ring-zero sandbox isolation and hardware speed!")

    # Scene 5: 51.5 - 57.5s (Dual Call-to-Action & Outro)
    else:
        draw_studio_environment(ctx, t, theme="navy")
        draw_master_brand_header(ctx, t)

        # Giant Glowing Star Button
        btn_w, btn_h = 760, 160
        btn_x, btn_y = (W - btn_w) / 2, 340
        ctx.set_source_rgb(1.0, 0.72, 0.12)
        ctx.rectangle(btn_x, btn_y, btn_w, btn_h)
        ctx.fill_preserve()
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_line_width(5)
        ctx.stroke()

        draw_star(ctx, btn_x + 90, btn_y + btn_h / 2, r_outer=45, r_inner=20, color=(1, 1, 1))
        ctx.set_source_rgb(0.08, 0.10, 0.15)
        ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(52)
        ctx.move_to(btn_x + 160, btn_y + 100)
        ctx.show_text("STAR ON GITHUB NOW!")

        # Lower Box: Flowork OS Callout
        box2_y = 560
        ctx.set_source_rgb(0.08, 0.14, 0.22)
        ctx.rectangle(btn_x, box2_y, btn_w, 240)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.12, 0.82, 0.95)
        ctx.set_line_width(4)
        ctx.stroke()

        ctx.set_source_rgb(0.12, 0.82, 0.95)
        ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(38)
        ctx.move_to(btn_x + 50, box2_y + 70)
        ctx.show_text("CLONE & RUN ON FLOWORK OS")

        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.set_font_size(48)
        ctx.move_to(btn_x + 50, box2_y + 145)
        ctx.show_text("FLOWORKOS.COM")

        ctx.set_source_rgb(0.18, 0.86, 0.45)
        ctx.set_font_size(24)
        ctx.move_to(btn_x + 50, box2_y + 195)
        ctx.show_text("SOVEREIGN LINUX OS BUILT FOR AUTONOMOUS AI AGENTS")

        # Falling Confetti & Stars
        for idx in range(12):
            star_t = (t * 2 + idx * 0.4) % 3.0
            sx = 100 + (idx * 85) % (W - 200)
            sy = 200 + star_t * 300
            draw_star(ctx, sx, sy, r_outer=16, r_inner=7, color=C_ACCENT_AMBER)

        # Characters celebrating
        draw_senior_dev(ctx, 320, FLOOR_Y - 140, scale=1.05, state={"pose": "idle", "t": t})
        draw_ai_agent_bot(ctx, 760, FLOOR_Y - 260, scale=1.1, t=t)

        draw_subtitle_banner(ctx, "Star browser-use on GitHub right now, and visit floworkos.com!")


def render_all():
    print(f"🎬 Starting render of browser-use short ({TOTAL_FRAMES} frames, {DURATION_SEC}s)...")
    temp_mp4 = OUTPUT_MP4 + ".tmp.mp4"

    # FFmpeg command streaming raw video from pipe
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "bgra",
        "-r", str(FPS),
        "-i", "-",
        "-i", AUDIO_WAV,
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-b:v", "8M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        temp_mp4
    ]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        # Fallback to libx264
        cmd[cmd.index("h264_nvenc")] = "libx264"
        cmd[cmd.index("-preset") + 1] = "veryfast"
        cmd.remove("-b:v")
        cmd.remove("8M")
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)

    # Sample frame indexes for contact sheet
    sample_indices = [
        int(TOTAL_FRAMES * 0.05),  # Hook
        int(TOTAL_FRAMES * 0.15),  # Nightmare
        int(TOTAL_FRAMES * 0.35),  # Breakthrough
        int(TOTAL_FRAMES * 0.55),  # Browser Sim
        int(TOTAL_FRAMES * 0.75),  # Flowork OS
        int(TOTAL_FRAMES * 0.95),  # Outro CTA
    ]
    sampled_surfaces = []

    for frame in range(TOTAL_FRAMES):
        t = frame / FPS
        render_scene(ctx, t)
        surface.flush()

        data = surface.get_data()
        proc.stdin.write(data)

        if frame in sample_indices:
            # Capture snapshot for contact sheet
            snap = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            s_ctx = cairo.Context(snap)
            s_ctx.set_source_surface(surface, 0, 0)
            s_ctx.paint()
            sampled_surfaces.append(snap)

        if frame % 150 == 0:
            print(f"Render progress: {frame}/{TOTAL_FRAMES} frames ({t:.1f}s)...")

    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        err = proc.stderr.read().decode()
        print(f"❌ FFmpeg failed: {err}")
        sys.exit(1)

    # Atomic move
    os.rename(temp_mp4, OUTPUT_MP4)
    subprocess.run(["cp", OUTPUT_MP4, USER_OUTPUT_MP4], check=True)
    print(f"✅ Video rendered successfully: {OUTPUT_MP4}")
    print(f"✅ Mirrored to: {USER_OUTPUT_MP4}")

    # Build Contact Sheet (2x3 grid)
    cs_w, cs_h = 1080, 1140
    cs_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, cs_w, cs_h)
    cs_ctx = cairo.Context(cs_surf)

    # Dark background
    cs_ctx.set_source_rgb(0.05, 0.07, 0.11)
    cs_ctx.rectangle(0, 0, cs_w, cs_h)
    cs_ctx.fill()

    # Title
    cs_ctx.set_source_rgb(0.12, 0.82, 0.95)
    cs_ctx.select_font_face("Impact", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cs_ctx.set_font_size(36)
    cs_ctx.move_to(40, 50)
    cs_ctx.show_text("BROWSER-USE (35K+ STARS) - CARTOON SHORT CONTACT SHEET")

    grid_cols = 3
    thumb_w = 320
    thumb_h = int(thumb_w * (1920 / 1080))  # 568 px
    scale = thumb_w / W

    for idx, snap in enumerate(sampled_surfaces[:6]):
        col = idx % grid_cols
        row = idx // grid_cols
        gx = 40 + col * (thumb_w + 20)
        gy = 80 + row * (thumb_h + 30)

        cs_ctx.save()
        cs_ctx.translate(gx, gy)
        cs_ctx.scale(scale, scale)
        cs_ctx.set_source_surface(snap, 0, 0)
        cs_ctx.paint()
        cs_ctx.restore()

        # Border
        cs_ctx.set_source_rgb(0.18, 0.86, 0.45)
        cs_ctx.set_line_width(3)
        cs_ctx.rectangle(gx, gy, thumb_w, thumb_h)
        cs_ctx.stroke()

    cs_surf.write_to_png(CONTACT_SHEET_PNG)
    subprocess.run(["cp", CONTACT_SHEET_PNG, USER_CONTACT_SHEET_PNG], check=True)
    print(f"✅ Contact sheet written to: {CONTACT_SHEET_PNG}")
    print(f"✅ Mirrored contact sheet to: {USER_CONTACT_SHEET_PNG}")


if __name__ == "__main__":
    render_all()
