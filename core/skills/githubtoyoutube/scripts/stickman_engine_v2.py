#!/usr/bin/env python3
"""
🎬 SOVEREIGN STICKMAN 2.0 CINEMATIC ENGINE
Flowork OS Universal Video Production Core.
Features:
- High-Contrast Inversion: Non-white bright backgrounds + Dark matte stickman & UI cards.
- Mandatory Permanent Branding: High-luminance Matrix Green (#00ff66) 'FLOWORKOS.COM' on chest.
- Comedic Kinematics:
  * 'hanging': Dangles and swings from card/window top edge with swinging legs & cheeky wink.
  * 'walking': Paces across the frame with natural arm swings & foot turnover.
  * 'shocked': Clutching head in disbelief, wide 'O_O' eyes, dynamic spine lean.
  * 'thinking': Hand-on-chin with floating holographic optimization card.
  * 'celebrating': Mid-air victory jump with '^ _ ^' cheerful eyes.
  * 'laser_pointer': Grounded power stance with glowing laser rod.
  * 'explaining': Natural outward gestural presentation.
- NVENC Hardware accelerated rendering (1080p @ 30 FPS CFR).
"""

import os
import sys
import math
import subprocess
import cairo

WIDTH = 1920
HEIGHT = 1080
FPS = 30
REPO_URL = "https://github.com/ranxianglei/billion-context"

# ==============================================================================
# 1. MODULAR BACKGROUND ENGINE (NON-WHITE BRIGHT TONES WITH DRIFT)
# ==============================================================================

def draw_modular_background(ctx, t, bg_surface=None, fallback_color=(0.94, 0.91, 0.86)):
    """
    Renders modular background with subtle cinematic Ken-Burns parallax pan/zoom.
    Ensures high contrast against dark foreground elements.
    """
    if bg_surface is not None:
        ctx.save()
        scale = 1.04 + 0.015 * math.sin(t * 0.08)
        pan_x = math.cos(t * 0.05) * 20.0
        pan_y = math.sin(t * 0.07) * 12.0
        img_w = bg_surface.get_width()
        img_h = bg_surface.get_height()
        ctx.translate(WIDTH / 2.0 + pan_x, HEIGHT / 2.0 + pan_y)
        ctx.scale(scale * (WIDTH / float(img_w)), scale * (HEIGHT / float(img_h)))
        ctx.translate(-img_w / 2.0, -img_h / 2.0)
        ctx.set_source_surface(bg_surface, 0, 0)
        ctx.paint()
        ctx.restore()
    else:
        ctx.save()
        ctx.set_source_rgb(*fallback_color)
        ctx.rectangle(0, 0, WIDTH, HEIGHT)
        ctx.fill()
        ctx.restore()


# ==============================================================================
# 2. DARK FROSTED CARDS & GITHUB WINDOWS (HIGH CONTRAST ON BRIGHT BG)
# ==============================================================================

def draw_dark_card(ctx, x, y, w, h, title=""):
    """Dark sleek frosted card with glowing neon rim and soft shadow."""
    ctx.save()
    # Soft drop shadow on bright background
    ctx.set_source_rgba(0.08, 0.12, 0.18, 0.20)
    ctx.rectangle(x + 12, y + 16, w, h); ctx.fill()

    # Deep obsidian glass body (#0c1117)
    ctx.set_source_rgba(0.05, 0.07, 0.10, 0.96)
    rad = 12.0
    ctx.new_sub_path()
    ctx.arc(x + w - rad, y + rad, rad, -math.pi/2, 0)
    ctx.arc(x + w - rad, y + h - rad, rad, 0, math.pi/2)
    ctx.arc(x + rad, y + h - rad, rad, math.pi/2, math.pi)
    ctx.arc(x + rad, y + rad, rad, math.pi, 3*math.pi/2)
    ctx.close_path()
    ctx.fill_preserve()

    # Border rim (#00ff66 neon green accent)
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.90)
    ctx.set_line_width(2.0)
    ctx.stroke()

    # Window titlebar dots
    for i, col in enumerate([(1.0, 0.35, 0.35), (1.0, 0.75, 0.2), (0.2, 0.9, 0.4)]):
        ctx.set_source_rgb(*col)
        ctx.arc(x + 24 + i * 20, y + 24, 5.0, 0, 2 * math.pi); ctx.fill()

    if title:
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(15)
        ctx.set_source_rgba(0.9, 0.95, 1.0, 0.90)
        ctx.move_to(x + 95, y + 29)
        ctx.show_text(title)

    ctx.restore()


def draw_link_callout_banner(ctx, repo_url, t):
    """Glowing repository link banner pinned to top of screen."""
    ctx.save()
    bx, by, bw, bh = 480, 24, 960, 48
    ctx.set_source_rgba(0.05, 0.07, 0.10, 0.95)
    ctx.rectangle(bx, by, bw, bh); ctx.fill()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.85); ctx.set_line_width(1.8)
    ctx.rectangle(bx, by, bw, bh); ctx.stroke()

    # Badge icon
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(13); ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(bx + 20, by + 30); ctx.show_text("★ OFFICIAL REPO:")

    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(14); ctx.set_source_rgb(0.3, 0.9, 1.0)
    ctx.move_to(bx + 160, by + 30); ctx.show_text(repo_url)

    # Action pill
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.25)
    ctx.rectangle(bx + bw - 145, by + 10, 130, 28); ctx.fill()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.9); ctx.set_line_width(1.2)
    ctx.rectangle(bx + bw - 145, by + 10, 130, 28); ctx.stroke()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(12); ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(bx + bw - 130, by + 29); ctx.show_text("CLONE & STAR ↗")
    ctx.restore()


def draw_subtitles(ctx, sub_text):
    """Draws high-visibility subtitle box pinned to bottom."""
    if not sub_text:
        return
    ctx.save()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    font_size = 22
    ctx.set_font_size(font_size)
    ext = ctx.text_extents(sub_text)

    pad_x, pad_y = 28, 14
    box_w = ext.width + pad_x * 2
    box_h = ext.height + pad_y * 2
    box_x = (WIDTH - box_w) / 2.0
    box_y = HEIGHT - 85 - box_h / 2.0

    # Deep dark backing for maximum contrast against bright BG
    ctx.set_source_rgba(0.02, 0.04, 0.07, 0.96)
    ctx.rectangle(box_x, box_y, box_w, box_h); ctx.fill()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.90); ctx.set_line_width(1.6)
    ctx.rectangle(box_x, box_y, box_w, box_h); ctx.stroke()

    # Crisp white text
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(box_x + pad_x, box_y + box_h - pad_y - 2)
    ctx.show_text(sub_text)
    ctx.restore()


# ==============================================================================
# 3. DARK STICKMAN WITH GLOWING 'FLOWORKOS.COM' LOGO
# ==============================================================================

def draw_dark_head(ctx, cx, cy, scale, mood="confident", t=0.0):
    ctx.save()
    r = 32.0 * scale
    
    # 1. Dark Head Base (Matte Obsidian Black)
    head_pat = cairo.RadialGradient(cx - r*0.35, cy - r*0.35, r*0.1, cx, cy, r)
    head_pat.add_color_stop_rgb(0.0, 0.22, 0.25, 0.28)
    head_pat.add_color_stop_rgb(1.0, 0.05, 0.06, 0.07)
    ctx.set_source(head_pat)
    ctx.arc(cx, cy, r, 0, 2 * math.pi); ctx.fill()
    
    # Matrix Green Helm Rim (#00ff66)
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.92)
    ctx.set_line_width(2.6 * scale)
    ctx.arc(cx, cy, r, 0, 2 * math.pi); ctx.stroke()

    # Earpad headphones
    for side in (-1, 1):
        ep_x = cx + side * (r + 1.2 * scale)
        ep_y = cy + 2.0 * scale
        ctx.save()
        ctx.translate(ep_x, ep_y)
        ctx.set_source_rgb(0.04, 0.05, 0.06)
        ctx.rectangle(-4 * scale, -10 * scale, 8 * scale, 20 * scale); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.8 * scale)
        ctx.rectangle(-4 * scale, -10 * scale, 8 * scale, 20 * scale); ctx.stroke()
        ctx.restore()

    # Dark Visor Screen
    vw = r * 1.45; vh = r * 1.0
    vx = cx - vw / 2.0; vy = cy - vh / 2.0 + 2.0 * scale
    v_rad = 10.0 * scale
    ctx.new_sub_path()
    ctx.arc(vx + vw - v_rad, vy + v_rad, v_rad, -math.pi/2, 0)
    ctx.arc(vx + vw - v_rad, vy + vh - v_rad, v_rad, 0, math.pi/2)
    ctx.arc(vx + v_rad, vy + vh - v_rad, v_rad, math.pi/2, math.pi)
    ctx.arc(vx + v_rad, vy + v_rad, v_rad, math.pi, 3*math.pi/2)
    ctx.close_path()
    ctx.set_source_rgb(0.02, 0.03, 0.04); ctx.fill_preserve()
    ctx.set_source_rgba(0.0, 1.0, 0.5, 0.85); ctx.set_line_width(1.6 * scale); ctx.stroke()

    # Expressive Animated Visor Face (Blinking + Pupil Glancing + Speech Lip-Sync)
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    eye_y = vy + vh * 0.45
    left_x = cx - vw * 0.25
    right_x = cx + vw * 0.25
    mouth_y = vy + vh * 0.76

    # 1. Natural Blinking (blinks for 0.22s every 3.8 seconds)
    is_blinking = (t * 2.2) % 3.8 > 3.58

    # 2. Pupil Glancing / Eye Tracking
    glance_x = math.sin(t * 1.6) * (2.2 * scale)
    glance_y = math.cos(t * 1.2) * (1.2 * scale)

    # 3. Dynamic Speech Mouth (articulates continuously with narration)
    talk_cycle = t * 13.0
    mouth_open = max(0.0, math.sin(talk_cycle)) * (3.8 * scale)
    mouth_w = (6.0 + math.sin(talk_cycle * 0.7) * 2.0) * scale

    if mood == "cheeky":
        # Winking eye + cheeky talking grin
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(3.0 * scale)
        ctx.move_to(left_x - 6 * scale, eye_y)
        ctx.curve_to(left_x, eye_y + 4 * scale, left_x, eye_y + 4 * scale, left_x + 6 * scale, eye_y); ctx.stroke()
        ctx.arc(right_x + glance_x * 0.5, eye_y - 2 * scale + glance_y * 0.5, 5.0 * scale, 0, 2 * math.pi); ctx.fill()
        # Animated cheeky mouth
        ctx.move_to(cx - 6 * scale, mouth_y)
        ctx.curve_to(cx - 2 * scale, mouth_y + 4 * scale + mouth_open * 0.4, cx + 2 * scale, mouth_y + 4 * scale + mouth_open * 0.4, cx + 6 * scale, mouth_y); ctx.stroke()

    elif mood == "shocked":
        # Terrified wide eyes shaking + quivering open mouth
        quiv = math.sin(t * 30.0) * (1.5 * scale)
        ctx.set_source_rgb(0.0, 1.0, 0.85); ctx.set_line_width(3.0 * scale)
        ctx.arc(left_x + quiv, eye_y, (7.5 + math.sin(t * 22.0) * 1.0) * scale, 0, 2 * math.pi); ctx.stroke()
        ctx.arc(right_x + quiv, eye_y, (7.5 + math.sin(t * 22.0) * 1.0) * scale, 0, 2 * math.pi); ctx.stroke()
        ctx.arc(left_x + quiv, eye_y, 2.5 * scale, 0, 2 * math.pi); ctx.fill()
        ctx.arc(right_x + quiv, eye_y, 2.5 * scale, 0, 2 * math.pi); ctx.fill()
        # Trembling O mouth
        ctx.arc(cx + quiv, mouth_y + 2 * scale, (4.5 + math.sin(t * 18.0) * 1.8) * scale, 0, 2 * math.pi); ctx.stroke()

    elif mood == "celebrating":
        # Cheerful laughing curved eyes ^_^ + wide open laughing mouth
        ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_line_width(3.4 * scale)
        ctx.move_to(left_x - 7 * scale, eye_y + 3 * scale)
        ctx.curve_to(left_x - 3 * scale, eye_y - 6 * scale, left_x + 3 * scale, eye_y - 6 * scale, left_x + 7 * scale, eye_y + 3 * scale); ctx.stroke()
        ctx.move_to(right_x - 7 * scale, eye_y + 3 * scale)
        ctx.curve_to(right_x - 3 * scale, eye_y - 6 * scale, right_x + 3 * scale, eye_y - 6 * scale, right_x + 7 * scale, eye_y + 3 * scale); ctx.stroke()
        # Animated singing / cheering mouth
        cheer_open = (5.0 + math.sin(t * 10.0) * 3.0) * scale
        ctx.arc(cx, mouth_y + 2 * scale, cheer_open, 0, math.pi); ctx.stroke()

    elif mood == "thinking":
        # Glancing up to the corner + small thoughtful mouth
        ctx.set_source_rgb(0.2, 0.9, 1.0); ctx.set_line_width(2.8 * scale)
        ctx.arc(left_x - 2 * scale, eye_y - 3 * scale, 5.0 * scale, 0, 2 * math.pi); ctx.stroke()
        ctx.move_to(right_x - 6 * scale, eye_y); ctx.line_to(right_x + 6 * scale, eye_y); ctx.stroke()
        ctx.move_to(cx - 5 * scale, mouth_y); ctx.line_to(cx + 5 * scale, mouth_y - 2 * scale + math.sin(t * 6.0) * scale); ctx.stroke()

    elif mood == "laser":
        # Laser targeting reticle eyes + focused speaking mouth
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(2.2 * scale)
        for ex in (left_x, right_x):
            ctx.arc(ex, eye_y, 6.0 * scale, 0, 2 * math.pi); ctx.stroke()
            ctx.move_to(ex - 7 * scale, eye_y); ctx.line_to(ex + 7 * scale, eye_y); ctx.stroke()
            ctx.move_to(ex, eye_y - 7 * scale); ctx.line_to(ex, eye_y + 7 * scale); ctx.stroke()
            ctx.arc(ex, eye_y, 1.8 * scale, 0, 2 * math.pi); ctx.fill()
        if mouth_open > 1.2 * scale:
            ctx.arc(cx, mouth_y, mouth_open, 0, 2 * math.pi); ctx.stroke()
        else:
            ctx.move_to(cx - 5 * scale, mouth_y); ctx.line_to(cx + 6 * scale, mouth_y + 1 * scale); ctx.stroke()

    else: # "confident" (default)
        ctx.set_source_rgb(0.0, 1.0, 0.5)
        if is_blinking:
            # Closed happy curved eye blink
            ctx.set_line_width(3.2 * scale)
            ctx.move_to(left_x - 6 * scale, eye_y + 2 * scale)
            ctx.curve_to(left_x, eye_y + 5 * scale, left_x, eye_y + 5 * scale, left_x + 6 * scale, eye_y + 2 * scale); ctx.stroke()
            ctx.move_to(right_x - 6 * scale, eye_y + 2 * scale)
            ctx.curve_to(right_x, eye_y + 5 * scale, right_x, eye_y + 5 * scale, right_x + 6 * scale, eye_y + 2 * scale); ctx.stroke()
        else:
            # Open eyes with tracking pupils and catchlights
            ctx.set_line_width(3.0 * scale)
            for ex in (left_x, right_x):
                ctx.arc(ex + glance_x, eye_y + glance_y, 4.6 * scale, 0, 2 * math.pi); ctx.fill()
                # Specular white catchlight
                ctx.save()
                ctx.set_source_rgb(1.0, 1.0, 1.0)
                ctx.arc(ex + glance_x - 1.5 * scale, eye_y + glance_y - 1.5 * scale, 1.6 * scale, 0, 2 * math.pi); ctx.fill()
                ctx.restore()

        # Dynamic Speech Talking Mouth
        if mouth_open > 1.2 * scale:
            # Open talking articulation
            ctx.set_line_width(2.0 * scale)
            ctx.arc(cx, mouth_y + mouth_open * 0.2, mouth_open, 0, 2 * math.pi); ctx.stroke()
        else:
            # Articulated smile curve
            ctx.set_line_width(3.0 * scale)
            ctx.move_to(cx - mouth_w, mouth_y)
            ctx.curve_to(cx - 2 * scale, mouth_y + 3.5 * scale, cx + 2 * scale, mouth_y + 3.5 * scale, cx + mouth_w, mouth_y); ctx.stroke()

    ctx.restore()
    ctx.restore()


def draw_dark_hoodie_torso(ctx, cx, cy, scale, torso_lean=0.0):
    """Deep charcoal/matte black hoodie with prominent glowing FLOWORKOS.COM logo."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(torso_lean)

    hw_shoulder = 36.0 * scale
    hw_waist = 28.0 * scale
    torso_h = 82.0 * scale

    # Dark Matte Hoodie Body
    hoodie_pat = cairo.LinearGradient(0, 0, 0, torso_h)
    hoodie_pat.add_color_stop_rgb(0.0, 0.12, 0.15, 0.18)
    hoodie_pat.add_color_stop_rgb(1.0, 0.05, 0.06, 0.08)
    ctx.set_source(hoodie_pat)

    ctx.move_to(-14 * scale, 0)
    ctx.line_to(-hw_shoulder, 12 * scale)
    ctx.line_to(-hw_waist - 3 * scale, torso_h - 10 * scale)
    ctx.line_to(-hw_waist, torso_h)
    ctx.line_to(hw_waist, torso_h)
    ctx.line_to(hw_waist + 3 * scale, torso_h - 10 * scale)
    ctx.line_to(hw_shoulder, 12 * scale)
    ctx.line_to(14 * scale, 0)
    ctx.close_path()
    ctx.fill_preserve()

    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.9)
    ctx.set_line_width(2.0 * scale)
    ctx.stroke()

    # Kangaroo front pocket
    py = torso_h * 0.62; pw = hw_waist * 0.88; ph = torso_h * 0.32
    ctx.set_source_rgba(0.04, 0.05, 0.07, 0.95)
    ctx.rectangle(-pw, py, pw * 2, ph); ctx.fill_preserve()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6); ctx.set_line_width(1.5 * scale); ctx.stroke()

    # ⭐ ULTRA-BRIGHT 'FLOWORKOS.COM' LOGO
    badge_y = 18.0 * scale
    badge_w = 68.0 * scale
    badge_h = 20.0 * scale
    bx = -badge_w / 2.0
    by = badge_y

    ctx.set_source_rgb(0.02, 0.03, 0.04)
    ctx.rectangle(bx, by, badge_w, badge_h); ctx.fill_preserve()
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.8 * scale); ctx.stroke()

    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(7.5 * scale)
    ext = ctx.text_extents("FLOWORKOS.COM")

    # Neon bloom glow
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.45)
    ctx.move_to(-ext.width / 2.0, by + badge_h * 0.68 + 0.5 * scale)
    ctx.show_text("FLOWORKOS.COM")

    # Pure Matrix Green text
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(-ext.width / 2.0, by + badge_h * 0.68)
    ctx.show_text("FLOWORKOS.COM")

    # Drawstrings routed cleanly above badge
    ctx.set_source_rgba(0.85, 0.95, 1.0, 0.9)
    ctx.set_line_width(1.8 * scale)
    for side in (-1, 1):
        ctx.move_to(side * 8 * scale, 6 * scale)
        ctx.curve_to(side * 10 * scale, 12 * scale, side * 13 * scale, 14 * scale, side * 15 * scale, 16 * scale); ctx.stroke()
        ctx.set_source_rgb(0.0, 1.0, 0.4)
        ctx.arc(side * 15 * scale, 17 * scale, 1.6 * scale, 0, 2*math.pi); ctx.fill()

    ctx.restore()
    return torso_h


def draw_dark_leg(ctx, hip_x, hip_y, foot_x, foot_y, scale, is_left=True):
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    mid_x = (hip_x + foot_x) / 2.0 + (3.0 * scale if is_left else -3.0 * scale)
    mid_y = (hip_y + foot_y) / 2.0
    # Dark pants
    ctx.set_source_rgb(0.06, 0.08, 0.10)
    ctx.set_line_width(11.0 * scale)
    ctx.move_to(hip_x, hip_y); ctx.line_to(mid_x, mid_y); ctx.line_to(foot_x, foot_y - 6 * scale); ctx.stroke()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.7)
    ctx.set_line_width(1.6 * scale)
    ctx.move_to(hip_x, hip_y); ctx.line_to(mid_x, mid_y); ctx.line_to(foot_x, foot_y - 6 * scale); ctx.stroke()

    # Sneaker with bright green sole
    ctx.save()
    ctx.translate(foot_x, foot_y)
    flip = 1 if is_left else -1
    ctx.scale(flip, 1)
    ctx.set_source_rgb(0.1, 0.12, 0.15)
    ctx.rectangle(-12 * scale, -10 * scale, 30 * scale, 10 * scale); ctx.fill_preserve()
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.5 * scale); ctx.stroke()
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.rectangle(-13 * scale, 0, 32 * scale, 4.0 * scale); ctx.fill()
    ctx.restore()
    ctx.restore()


def draw_arm_and_hand(ctx, sh_x, sh_y, hand_x, hand_y, scale, gesture="open", item=None):
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    dx = hand_x - sh_x; dy = hand_y - sh_y
    bend_dir = 1.0 if dx > 0 else -1.0
    elbow_x = (sh_x + hand_x) / 2.0 + (dy * 0.18 * bend_dir)
    elbow_y = (sh_y + hand_y) / 2.0 - (abs(dx) * 0.15)

    ctx.set_source_rgb(0.08, 0.11, 0.15)
    ctx.set_line_width(10.5 * scale)
    ctx.move_to(sh_x, sh_y); ctx.line_to(elbow_x, elbow_y); ctx.line_to(hand_x, hand_y); ctx.stroke()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.75)
    ctx.set_line_width(1.6 * scale)
    ctx.move_to(sh_x, sh_y); ctx.line_to(elbow_x, elbow_y); ctx.line_to(hand_x, hand_y); ctx.stroke()

    ctx.save()
    ctx.translate(hand_x, hand_y)
    ctx.set_source_rgb(0.9, 0.95, 1.0)
    if gesture == "point":
        ang = math.atan2(dy, dx)
        ctx.rotate(ang)
        ctx.arc(0, 0, 5.0 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(3.2 * scale)
        ctx.move_to(0, 0); ctx.line_to(12 * scale, 0); ctx.stroke()
        if item == "laser_pointer":
            ctx.set_source_rgb(0.2, 0.25, 0.3); ctx.set_line_width(2.2 * scale)
            ctx.move_to(2 * scale, 0); ctx.line_to(50 * scale, 0); ctx.stroke()
            ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.arc(50 * scale, 0, 3.8 * scale, 0, 2*math.pi); ctx.fill()
            ctx.set_source_rgba(0.0, 1.0, 0.4, 0.5); ctx.set_line_width(1.2 * scale)
            ctx.move_to(50 * scale, 0); ctx.line_to(125 * scale, -5 * scale); ctx.stroke()
    elif gesture == "clutch":
        ctx.arc(0, 0, 6.0 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(2.2 * scale)
        for f_ang in (-0.6, -0.2, 0.2, 0.6):
            ctx.move_to(0, 0); ctx.line_to(math.cos(f_ang) * 10 * scale, math.sin(f_ang) * 10 * scale); ctx.stroke()
    elif gesture == "chin":
        ctx.arc(0, 0, 5.5 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(2.6 * scale)
        ctx.move_to(0, 0); ctx.line_to(5 * scale, -8 * scale); ctx.stroke()
        ctx.move_to(0, 0); ctx.line_to(-5 * scale, -5 * scale); ctx.stroke()
    elif gesture == "fist":
        ctx.arc(0, 0, 6.5 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.85); ctx.arc(0, 0, 2.5 * scale, 0, 2*math.pi); ctx.fill()
    else: # open
        ctx.arc(0, 0, 5.5 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(2.4 * scale)
        for f_ang in (-0.5, -0.15, 0.2, 0.55):
            ctx.move_to(0, 0); ctx.line_to(math.cos(f_ang) * 9.5 * scale, math.sin(f_ang) * 9.5 * scale); ctx.stroke()
    ctx.restore()
    ctx.restore()


# ==============================================================================
# 4. MASTER COMEDIC ACTIONS & STAGING
# ==============================================================================

def draw_hanging_stickman(ctx, anchor_x, anchor_y, scale=1.35, t=0.0):
    """Stickman dangles humorously from top edge of card/window."""
    ctx.save()
    swing = math.sin(t * 3.5) * 0.10
    ctx.translate(anchor_x, anchor_y)
    ctx.rotate(swing)

    hand_spacing = 38.0 * scale
    for side in (-1, 1):
        hx = side * hand_spacing / 2.0
        ctx.set_source_rgb(0.05, 0.08, 0.12)
        ctx.arc(hx, 0, 5.5 * scale, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.8 * scale)
        ctx.arc(hx, 0, 5.5 * scale, 0, 2 * math.pi); ctx.stroke()

    head_cy = 38.0 * scale
    draw_dark_head(ctx, 0, head_cy, scale, mood="cheeky", t=t)

    torso_cy = head_cy + 34.0 * scale
    draw_dark_hoodie_torso(ctx, 0, torso_cy, scale, torso_lean=0.0)

    sh_y = torso_cy + 12.0 * scale
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgb(0.08, 0.10, 0.14); ctx.set_line_width(10.0 * scale)
    ctx.move_to(-28 * scale, sh_y); ctx.line_to(-hand_spacing/2.0, 0); ctx.stroke()
    ctx.move_to(28 * scale, sh_y); ctx.line_to(hand_spacing/2.0, 0); ctx.stroke()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.8); ctx.set_line_width(1.6 * scale)
    ctx.move_to(-28 * scale, sh_y); ctx.line_to(-hand_spacing/2.0, 0); ctx.stroke()
    ctx.move_to(28 * scale, sh_y); ctx.line_to(hand_spacing/2.0, 0); ctx.stroke()

    hip_y = torso_cy + 82.0 * scale
    kick_l = math.sin(t * 5.0) * 18.0 * scale
    kick_r = math.cos(t * 5.0) * 18.0 * scale
    draw_dark_leg(ctx, -14 * scale, hip_y, -24 * scale + kick_l, hip_y + 80 * scale, scale, is_left=True)
    draw_dark_leg(ctx, 14 * scale, hip_y, 24 * scale + kick_r, hip_y + 80 * scale, scale, is_left=False)
    ctx.restore()


def draw_walking_stickman(ctx, x, y, scale=1.35, t=0.0):
    """Stickman paces / walks across the frame with natural arm & leg swings."""
    ctx.save()
    walk_cycle = t * 6.0
    step_l = math.sin(walk_cycle)
    step_r = math.sin(walk_cycle + math.pi)
    bob = abs(math.sin(walk_cycle * 2.0)) * 5.0 * scale

    base_y = y - bob
    head_y = base_y - 75 * scale
    torso_y = head_y + 36 * scale
    hip_y = torso_y + 82 * scale
    ground_y = y + 105 * scale

    ctx.save()
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.18)
    ctx.scale(1.0, 0.22)
    ctx.arc(x, ground_y * 4.54, 65 * scale, 0, 2 * math.pi); ctx.fill()
    ctx.restore()

    draw_dark_hoodie_torso(ctx, x, torso_y, scale, torso_lean=0.08)
    draw_dark_head(ctx, x + 4 * scale, head_y, scale, mood="confident", t=t)

    foot_l_x = x + step_l * 32.0 * scale
    foot_r_x = x + step_r * 32.0 * scale
    foot_l_y = ground_y - max(0, -step_l * 14.0 * scale)
    foot_r_y = ground_y - max(0, -step_r * 14.0 * scale)
    draw_dark_leg(ctx, x - 14 * scale, hip_y, foot_l_x, foot_l_y, scale, is_left=True)
    draw_dark_leg(ctx, x + 14 * scale, hip_y, foot_r_x, foot_r_y, scale, is_left=False)

    sh_l_x = x - 34 * scale; sh_y = torso_y + 14 * scale
    sh_r_x = x + 34 * scale
    hand_l_x = x + step_r * 28.0 * scale
    hand_r_x = x + step_l * 28.0 * scale
    hand_y = torso_y + 45 * scale
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgb(0.08, 0.10, 0.14); ctx.set_line_width(10.0 * scale)
    ctx.move_to(sh_l_x, sh_y); ctx.line_to(hand_l_x, hand_y); ctx.stroke()
    ctx.move_to(sh_r_x, sh_y); ctx.line_to(hand_r_x, hand_y); ctx.stroke()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.8); ctx.set_line_width(1.6 * scale)
    ctx.move_to(sh_l_x, sh_y); ctx.line_to(hand_l_x, hand_y); ctx.stroke()
    ctx.move_to(sh_r_x, sh_y); ctx.line_to(hand_r_x, hand_y); ctx.stroke()

    for hx in (hand_l_x, hand_r_x):
        ctx.set_source_rgb(0.05, 0.08, 0.12); ctx.arc(hx, hand_y, 5.0 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.arc(hx, hand_y, 2.0 * scale, 0, 2*math.pi); ctx.fill()
    ctx.restore()


def draw_stylized_stickman(ctx, x, y, scale=1.35, mood="confident", t=0.0, action="explaining"):
    """Master character dispatcher supporting hanging, walking, clutching, thinking, and celebrating."""
    if action == "hanging":
        draw_hanging_stickman(ctx, x, y, scale=scale, t=t)
        return
    if action == "walking":
        draw_walking_stickman(ctx, x, y, scale=scale, t=t)
        return

    ctx.save()
    breathe = math.sin(t * 3.0) * (2.0 * scale)
    base_y = y + breathe
    head_y = base_y - 75 * scale
    torso_y = head_y + 36 * scale
    hip_y = torso_y + 82 * scale
    ground_y = base_y + 105 * scale

    # Floor shadow
    ctx.save()
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.20)
    ctx.scale(1.0, 0.22)
    ctx.arc(x, ground_y * 4.54, 70 * scale, 0, 2 * math.pi); ctx.fill()
    ctx.restore()

    if action == "shocked" or mood == "shocked":
        # Quivering arms & head in alarm
        quiv = math.sin(t * 32.0) * (3.0 * scale)
        torso_lean = -0.16 + math.sin(t * 25.0) * 0.03
        draw_dark_hoodie_torso(ctx, x - 10 * scale + quiv, torso_y, scale, torso_lean=torso_lean)
        draw_dark_head(ctx, x - 20 * scale + quiv, head_y - 2 * scale, scale, mood="shocked", t=t)
        draw_dark_leg(ctx, x - 26 * scale, hip_y, x - 48 * scale, ground_y, scale, is_left=True)
        draw_dark_leg(ctx, x - 2 * scale, hip_y, x + 30 * scale, ground_y - 2 * scale, scale, is_left=False)
        sh_l = x - 42 * scale; sh_r = x + 18 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y + 14 * scale, x - 42 * scale + quiv, head_y - 8 * scale + quiv, scale, gesture="clutch")
        draw_arm_and_hand(ctx, sh_r, torso_y + 10 * scale, x + 6 * scale + quiv, head_y - 10 * scale - quiv, scale, gesture="clutch")

    elif action == "thinking" or mood == "thinking":
        # Tapping chin & thoughtful head tilt
        tap = math.sin(t * 8.0) * (3.5 * scale)
        head_tilt = math.sin(t * 1.5) * 0.04
        draw_dark_hoodie_torso(ctx, x, torso_y, scale, torso_lean=0.04)
        draw_dark_head(ctx, x + 4 * scale, head_y + head_tilt * 10.0, scale, mood="thinking", t=t)
        draw_dark_leg(ctx, x - 14 * scale, hip_y, x - 22 * scale, ground_y, scale, is_left=True)
        draw_dark_leg(ctx, x + 14 * scale, hip_y, x + 20 * scale, ground_y, scale, is_left=False)
        sh_l = x - 36 * scale; sh_r = x + 36 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y + 14 * scale, x - 42 * scale, hip_y - 12 * scale + math.sin(t * 3.0) * 4.0, scale, gesture="fist")
        draw_arm_and_hand(ctx, sh_r, torso_y + 14 * scale, x + 14 * scale, head_y + 24 * scale + tap, scale, gesture="chin")

    elif action == "bouncing":
        # Continuous energetic bouncing on feet
        jump_y = -abs(math.sin(t * 8.0)) * 32.0 * scale
        arm_pump = math.sin(t * 8.0) * (14.0 * scale)
        draw_dark_hoodie_torso(ctx, x, torso_y + jump_y, scale, torso_lean=0.0)
        draw_dark_head(ctx, x, head_y + jump_y, scale, mood="celebrating", t=t)
        draw_dark_leg(ctx, x - 14 * scale, hip_y + jump_y, x - 18 * scale, ground_y - 25 * scale, scale, is_left=True)
        draw_dark_leg(ctx, x + 14 * scale, hip_y + jump_y, x + 18 * scale, ground_y - 25 * scale, scale, is_left=False)
        sh_l = x - 34 * scale; sh_r = x + 34 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y + 12 * scale + jump_y, x - 45 * scale, torso_y - 10 * scale + jump_y + arm_pump, scale, gesture="open")
        draw_arm_and_hand(ctx, sh_r, torso_y + 12 * scale + jump_y, x + 45 * scale, torso_y - 10 * scale + jump_y + arm_pump, scale, gesture="open")
        # Spring bounce ripple
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.7); ctx.set_line_width(1.8 * scale)
        ctx.arc(x, ground_y + 5, 20 * scale, math.pi * 0.2, math.pi * 0.8); ctx.stroke()

    elif action == "celebrating" or mood == "celebrating":
        # Joyful victory jump with waving arms
        jump_y = -abs(math.sin(t * 6.0)) * 26.0 * scale
        arm_wave = math.sin(t * 7.0) * (16.0 * scale)
        draw_dark_hoodie_torso(ctx, x, torso_y + jump_y, scale, torso_lean=0.0)
        draw_dark_head(ctx, x, head_y + jump_y, scale, mood="celebrating", t=t)
        draw_dark_leg(ctx, x - 16 * scale, hip_y + jump_y, x - 30 * scale, ground_y - 20 * scale, scale, is_left=True)
        draw_dark_leg(ctx, x + 16 * scale, hip_y + jump_y, x + 30 * scale, ground_y - 20 * scale, scale, is_left=False)
        sh_l = x - 36 * scale; sh_r = x + 36 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y + 12 * scale + jump_y, x - (64 + arm_wave) * scale, head_y - 38 * scale + jump_y, scale, gesture="open")
        draw_arm_and_hand(ctx, sh_r, torso_y + 12 * scale + jump_y, x + (64 + arm_wave) * scale, head_y - 38 * scale + jump_y, scale, gesture="open")

    elif action == "salto":
        # Mid-air 360 flip
        flip_angle = (t * 7.0) % (2 * math.pi) - math.pi
        ctx.save()
        ctx.translate(x, y - 40 * scale)
        ctx.rotate(flip_angle)
        draw_dark_hoodie_torso(ctx, 0, -8 * scale, scale * 0.95, torso_lean=0.2)
        draw_dark_head(ctx, 0, -38 * scale, scale * 0.95, mood="celebrating", t=t)
        draw_dark_leg(ctx, -10 * scale, 22 * scale, -24 * scale, -2 * scale, scale * 0.88, is_left=True)
        draw_dark_leg(ctx, 10 * scale, 22 * scale, 24 * scale, -2 * scale, scale * 0.88, is_left=False)
        draw_arm_and_hand(ctx, -24 * scale, 5 * scale, -24 * scale, 12 * scale, scale * 0.88, gesture="clutch")
        draw_arm_and_hand(ctx, 24 * scale, 5 * scale, 24 * scale, 12 * scale, scale * 0.88, gesture="clutch")
        ctx.restore()

    elif action == "sprint":
        # Turbo high-speed sprint with pumping arms and churning legs
        sprint_cycle = t * 14.0
        sprint_arm_l = math.sin(sprint_cycle) * (35.0 * scale)
        sprint_arm_r = math.cos(sprint_cycle) * (35.0 * scale)
        draw_dark_hoodie_torso(ctx, x, torso_y, scale, torso_lean=0.32)
        draw_dark_head(ctx, x + 16 * scale, head_y + 5 * scale, scale, mood="laser", t=t)
        draw_dark_leg(ctx, x - 12 * scale, hip_y, x - 44 * scale + sprint_arm_l * 0.5, ground_y, scale, is_left=True)
        draw_dark_leg(ctx, x + 12 * scale, hip_y, x + 46 * scale - sprint_arm_l * 0.5, ground_y - 18 * scale, scale, is_left=False)
        sh_l = x - 30 * scale; sh_r = x + 30 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y + 14 * scale, x + 38 * scale + sprint_arm_r, torso_y + 45 * scale, scale, gesture="open")
        draw_arm_and_hand(ctx, sh_r, torso_y + 14 * scale, x - 38 * scale - sprint_arm_r, torso_y + 20 * scale, scale, gesture="open")
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6); ctx.set_line_width(1.5 * scale)
        for wy in range(int(torso_y), int(ground_y), 15):
            ctx.move_to(x - 95 * scale, wy); ctx.line_to(x - 50 * scale, wy); ctx.stroke()

    elif action == "splat":
        # Cartoon flat splat on ground with quivering
        dizzy_quiv = math.sin(t * 15.0) * (2.0 * scale)
        ctx.save(); ctx.translate(x, ground_y - 10 * scale); ctx.scale(1.2, 0.4)
        draw_dark_hoodie_torso(ctx, 0, 0, scale, torso_lean=0.0)
        ctx.restore()
        draw_dark_head(ctx, x - 55 * scale + dizzy_quiv, ground_y - 24 * scale, scale * 0.88, mood="shocked", t=t)
        draw_dark_leg(ctx, x + 25 * scale, ground_y - 6 * scale, x + 80 * scale, ground_y - 4 * scale, scale * 0.85, is_left=True)
        for st_x in (-70, -55, -40):
            star_rot = t * 5.0 + st_x
            ctx.set_source_rgb(1.0, 0.85, 0.2)
            ctx.arc(x + st_x * scale + math.sin(star_rot) * 4.0, ground_y - 45 * scale + math.cos(star_rot) * 4.0, 3.5, 0, 2*math.pi); ctx.fill()

    elif action == "hover":
        # Jetpack thruster hover with vertical oscillation & arm balancing
        hover_bob = math.sin(t * 4.0) * (10.0 * scale)
        arm_bal = math.sin(t * 5.0) * (8.0 * scale)
        feet_y = hip_y + 70 * scale + hover_bob
        draw_dark_hoodie_torso(ctx, x, torso_y - 30 * scale + hover_bob, scale, torso_lean=0.0)
        draw_dark_head(ctx, x, head_y - 30 * scale + hover_bob, scale, mood="laser", t=t)
        draw_dark_leg(ctx, x - 12 * scale, hip_y - 30 * scale + hover_bob, x - 16 * scale, feet_y - 30 * scale, scale, is_left=True)
        draw_dark_leg(ctx, x + 12 * scale, hip_y - 30 * scale + hover_bob, x + 16 * scale, feet_y - 30 * scale, scale, is_left=False)
        sh_l = x - 30 * scale; sh_r = x + 30 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y - 16 * scale + hover_bob, x - 50 * scale, torso_y + 10 * scale + hover_bob + arm_bal, scale, gesture="open")
        draw_arm_and_hand(ctx, sh_r, torso_y - 16 * scale + hover_bob, x + 50 * scale, torso_y + 10 * scale + hover_bob - arm_bal, scale, gesture="open")
        for fx in (x - 16 * scale, x + 16 * scale):
            ctx.save(); ctx.translate(fx, feet_y - 24 * scale)
            flame_len = (25.0 + math.sin(t * 20.0) * 6.0) * scale
            pat = cairo.LinearGradient(0, 0, 0, flame_len)
            pat.add_color_stop_rgba(0.0, 0.0, 1.0, 0.5, 0.95)
            pat.add_color_stop_rgba(1.0, 0.0, 0.8, 1.0, 0.0)
            ctx.set_source(pat)
            ctx.move_to(-6 * scale, 0); ctx.line_to(6 * scale, 0); ctx.line_to(0, flame_len); ctx.close_path(); ctx.fill()
            ctx.restore()

    elif action == "sitting_laptop":
        # Rapid typing clatter on laptop
        lap_x, lap_y = x + 20 * scale, torso_y + 48 * scale
        lap_l_y = lap_y + math.sin(t * 22.0) * (4.0 * scale)
        lap_r_y = lap_y + math.sin(t * 22.0 + math.pi) * (4.0 * scale)
        draw_dark_hoodie_torso(ctx, x, torso_y, scale, torso_lean=0.05 + math.sin(t * 4.0) * 0.02)
        draw_dark_head(ctx, x + 2 * scale, head_y, scale, mood="confident", t=t)
        draw_dark_leg(ctx, x - 12 * scale, hip_y, x - 16 * scale, hip_y + 65 * scale, scale, is_left=True)
        draw_dark_leg(ctx, x + 12 * scale, hip_y, x + 16 * scale, hip_y + 65 * scale, scale, is_left=False)
        draw_arm_and_hand(ctx, x - 30 * scale, torso_y + 14 * scale, lap_x - 8 * scale, lap_l_y, scale, gesture="point")
        draw_arm_and_hand(ctx, x + 30 * scale, torso_y + 14 * scale, lap_x + 8 * scale, lap_r_y, scale, gesture="point")
        ctx.save(); ctx.translate(lap_x, lap_y)
        ctx.set_source_rgb(0.08, 0.12, 0.18); ctx.rectangle(-18 * scale, 0, 36 * scale, 7 * scale); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.0); ctx.rectangle(-18 * scale, 0, 36 * scale, 7 * scale); ctx.stroke()
        ctx.set_source_rgba(0.02, 0.05, 0.09, 0.95); ctx.rectangle(10 * scale, -22 * scale, 5 * scale, 22 * scale); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_line_width(1.0); ctx.rectangle(10 * scale, -22 * scale, 5 * scale, 22 * scale); ctx.stroke()
        ctx.restore()

    elif action == "confused":
        # Hand actively scratching head & head tilting
        scratch_y = math.sin(t * 12.0) * (5.0 * scale)
        head_tilt = math.sin(t * 2.0) * 0.06
        draw_dark_hoodie_torso(ctx, x, torso_y, scale, torso_lean=-0.06 + head_tilt)
        draw_dark_head(ctx, x - 2 * scale, head_y, scale, mood="confused", t=t)
        draw_dark_leg(ctx, x - 12 * scale, hip_y, x - 20 * scale, ground_y, scale, is_left=True)
        draw_dark_leg(ctx, x + 12 * scale, hip_y, x + 14 * scale, ground_y, scale, is_left=False)
        sh_l = x - 28 * scale; sh_r = x + 28 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y + 14 * scale, x - 35 * scale, hip_y - 5 * scale + math.sin(t * 3.0) * 3.0, scale, gesture="open")
        draw_arm_and_hand(ctx, sh_r, torso_y + 14 * scale, x + 6 * scale, head_y - 20 * scale + scratch_y, scale, gesture="scratch")
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size((24.0 + math.sin(t * 4.0) * 3.0) * scale); ctx.set_source_rgb(0.2, 0.9, 1.0)
        ctx.move_to(x + 40 * scale, head_y - 10 * scale); ctx.show_text("???")

    elif action == "heavy_lifting":
        # Straining and trembling under weight
        tremble = math.sin(t * 28.0) * (2.0 * scale)
        squat_y = 18 * scale + math.sin(t * 3.0) * 3.0
        draw_dark_hoodie_torso(ctx, x + tremble, torso_y + squat_y, scale, torso_lean=0.0)
        draw_dark_head(ctx, x + tremble, head_y + squat_y + 2 * scale, scale, mood="strained", t=t)
        draw_dark_leg(ctx, x - 16 * scale, hip_y + squat_y, x - 40 * scale, ground_y, scale, is_left=True)
        draw_dark_leg(ctx, x + 16 * scale, hip_y + squat_y, x + 40 * scale, ground_y, scale, is_left=False)
        sh_l = x - 28 * scale; sh_r = x + 28 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y + squat_y + 12 * scale, x - 42 * scale + tremble, head_y + squat_y - 25 * scale, scale, gesture="lifting")
        draw_arm_and_hand(ctx, sh_r, torso_y + squat_y + 12 * scale, x + 42 * scale + tremble, head_y + squat_y - 25 * scale, scale, gesture="lifting")

    elif action == "laser_pointer":
        # Pointing laser with subtle natural breath & target wobble
        laser_wobble = math.sin(t * 2.0) * (4.0 * scale)
        draw_dark_hoodie_torso(ctx, x, torso_y, scale, torso_lean=-0.04)
        draw_dark_head(ctx, x, head_y, scale, mood="laser", t=t)
        draw_dark_leg(ctx, x - 16 * scale, hip_y, x - 32 * scale, ground_y, scale, is_left=True)
        draw_dark_leg(ctx, x + 16 * scale, hip_y, x + 28 * scale, ground_y, scale, is_left=False)
        sh_l = x - 36 * scale; sh_r = x + 36 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y + 14 * scale, x - 42 * scale, hip_y - 12 * scale + math.sin(t * 2.5) * 3.0, scale, gesture="fist")
        draw_arm_and_hand(ctx, sh_r, torso_y + 14 * scale, x + 72 * scale, torso_y - 6 * scale + laser_wobble, scale, gesture="point", item="laser_pointer")

    else: # "explaining" (default)
        # 🌟 VIVID SPEAKING GESTICULATION (Arms move continuously with speech!)
        arm_wave_r_x = x + (62.0 + math.sin(t * 4.2) * 22.0) * scale
        arm_wave_r_y = (torso_y + 18.0 * scale) + math.cos(t * 3.5) * 26.0 * scale
        arm_wave_l_x = x - (38.0 + math.sin(t * 2.8) * 12.0) * scale
        arm_wave_l_y = (hip_y - 4.0 * scale) + math.cos(t * 2.5) * 14.0 * scale
        torso_sway = math.sin(t * 2.5) * 0.05
        draw_dark_hoodie_torso(ctx, x, torso_y, scale, torso_lean=0.04 + torso_sway)
        draw_dark_head(ctx, x + 2 * scale + math.sin(t * 2.5) * 3.0 * scale, head_y, scale, mood=mood, t=t)
        draw_dark_leg(ctx, x - 14 * scale, hip_y, x - 22 * scale, ground_y, scale, is_left=True)
        draw_dark_leg(ctx, x + 14 * scale, hip_y, x + 22 * scale, ground_y, scale, is_left=False)
        sh_l = x - 36 * scale; sh_r = x + 36 * scale
        draw_arm_and_hand(ctx, sh_l, torso_y + 14 * scale, arm_wave_l_x, arm_wave_l_y, scale, gesture="open")
        draw_arm_and_hand(ctx, sh_r, torso_y + 14 * scale, arm_wave_r_x, arm_wave_r_y, scale, gesture="point" if math.sin(t * 3.0) > 0.2 else "open")

    ctx.restore()


# ==============================================================================
# 5. SUBTITLE PARSER & MASTER NVENC HARDWARE RENDERER
# ==============================================================================

def parse_srt(srt_path):
    cues = []
    if not os.path.exists(srt_path):
        return cues
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    blocks = content.split("\n\n")
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) >= 3:
            time_line = lines[1]
            text = " ".join(lines[2:]).strip()
            if "-->" in time_line:
                start_str, end_str = time_line.split("-->")
                def to_sec(ts):
                    ts = ts.strip().replace(",", ".")
                    parts = ts.split(":")
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                cues.append((to_sec(start_str), to_sec(end_str), text))
    return cues


def render_chapter_pipeline(chapter_num, title, audio_file, srt_file, output_file, render_frame_func):
    """Encodes full 1080p chapter using PyCairo raw video to FFmpeg NVENC pipe."""
    print(f"\n[*] Rendering Chapter {chapter_num}: '{title}' via NVENC Hardware Pipe...")
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_file
    ]
    duration = float(subprocess.check_output(probe_cmd).decode().strip())
    total_frames = int(duration * FPS)
    print(f"[+] Audio Duration: {duration:.2f}s | Target Frames: {total_frames} @ {FPS} FPS")

    cues = parse_srt(srt_file)
    print(f"[+] Loaded {len(cues)} sentence subtitle cues")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "bgra",
        "-r", str(FPS),
        "-i", "-",
        "-i", audio_file,
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-cq", "21",
        "-c:a", "aac",
        "-b:a", "320k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_file
    ]

    pipe = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    for frame in range(total_frames):
        t = frame / float(FPS)
        active_sub = ""
        for start, end, text in cues:
            if start <= t <= end:
                active_sub = text
                break

        render_frame_func(ctx, t, active_sub)
        surface.flush()
        pipe.stdin.write(surface.get_data())

        if frame % (FPS * 10) == 0:
            pct = (frame / float(total_frames)) * 100
            print(f"  • Progress: {frame}/{total_frames} frames ({pct:.1f}%) | Time: {t:.1f}s / {duration:.1f}s")

    pipe.stdin.close()
    pipe.wait()
    print(f"[✓] Chapter {chapter_num} Complete: {output_file} (Exit Code: {pipe.returncode})")
    return output_file
