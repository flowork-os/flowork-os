#!/usr/bin/env python3
"""
🎬 MASTER STICKMAN (MR. FLOW) SCENE TEMPLATE CATALOG & GENERATOR
Universal Flowork OS Stickman 2.0 Template Suite.

Renders 16 Distinct, High-Energy, Acrobatic & Comedic Storytelling Scenes:
 1. Walking / Pacing Presentation (Jalan Santai Sambil Menerangkan)
 2. Bouncing / Double Hopping (Lompat-Lompat Heboh Antusias)
 3. Salto / Backflip 360° over Bug (Salto Akrobatik Melompati Error)
 4. Hanging from Card Top Edge (Bergelantungan Santai di Kusen Card)
 5. Sitting on Card Ledge + Laptop (Duduk Coding Santai + Kopi)
 6. Turbo Sprint (Lari Kencang Dikejar Bug / OOM)
 7. Slapstick Flat Splat (Terpeleset Jatuh Gepeng + Bintang Dizzy)
 8. Hover Jetpack Thrusters (Melayang di Udara dengan Api Sneaker)
 9. Peeking from Screen Border (Mengintip Lucu Muncul dari Bawah)
10. Confused Head Scratch (Bingung Garuk Kepala + Tanda Tanya '???')
11. Detective Deep Thinking (Tangan di Dagu + Hologram Formula ACP)
12. Cool Leaning on Card Side (Bersandar Keren Sambil Pegang Kopi)
13. Heavy Lifting Database (Beban Berat Mengangkat Blok 2M Token)
14. Panic Clutching Cheeks (Panik Histeris Tagihan $1,450 API Bill)
15. Victory Leap + Confetti (Lompat Selebrasi Sukses + Hujan Confetti)
16. Macro Camera Zoom Punch-In (Extreme 2.5x Close-Up Wajah & Badge)

Rules:
- High-Contrast Inversion: Warm non-white bright backgrounds (Kraft, Cream, Mint, Amber, Slate).
- Dark matte obsidian stickman & dark frosted glass cards.
- Mandatory high-luminance Matrix Green (#00ff66) 'FLOWORKOS.COM' chest badge.
"""

import math
import os
import sys
import cairo

# ==============================================================================
# COLOR PALETTES & CANVAS CONSTANTS
# ==============================================================================

BG_PALETTES = {
    "kraft": ((0.94, 0.91, 0.86), (0.88, 0.84, 0.78)),
    "cream": ((0.96, 0.93, 0.89), (0.91, 0.88, 0.83)),
    "sage":  ((0.86, 0.91, 0.88), (0.80, 0.86, 0.83)),
    "amber": ((0.93, 0.89, 0.82), (0.86, 0.82, 0.74)),
    "slate": ((0.88, 0.90, 0.91), (0.83, 0.85, 0.87)),
}

def draw_nonwhite_bg(ctx, w, h, bg_type="cream"):
    """Draws warm non-white bright background with soft architectural grid."""
    ctx.save()
    top_c, bot_c = BG_PALETTES.get(bg_type, BG_PALETTES["cream"])
    pat = cairo.LinearGradient(0, 0, w, h)
    pat.add_color_stop_rgb(0.0, *top_c)
    pat.add_color_stop_rgb(1.0, *bot_c)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, w, h)
    ctx.fill()

    # Subtle grid lines for high-tech architectural feel
    ctx.set_source_rgba(0.25, 0.30, 0.35, 0.05)
    ctx.set_line_width(1.0)
    step = 40
    for x in range(0, int(w), step):
        ctx.move_to(x, 0); ctx.line_to(x, h); ctx.stroke()
    for y in range(0, int(h), step):
        ctx.move_to(0, y); ctx.line_to(w, y); ctx.stroke()
    ctx.restore()


def draw_dark_card(ctx, x, y, w, h, title=""):
    """Dark sleek frosted obsidian glass card with glowing neon rim and soft shadow."""
    ctx.save()
    # Drop shadow
    ctx.set_source_rgba(0.08, 0.12, 0.18, 0.22)
    ctx.rectangle(x + 10, y + 14, w, h); ctx.fill()

    # Deep obsidian glass body (#0c1117)
    ctx.set_source_rgba(0.05, 0.07, 0.10, 0.96)
    rad = 10.0
    ctx.new_sub_path()
    ctx.arc(x + w - rad, y + rad, rad, -math.pi/2, 0)
    ctx.arc(x + w - rad, y + h - rad, rad, 0, math.pi/2)
    ctx.arc(x + rad, y + h - rad, rad, math.pi/2, math.pi)
    ctx.arc(x + rad, y + rad, rad, math.pi, 3*math.pi/2)
    ctx.close_path()
    ctx.fill_preserve()

    # Border rim (#00ff66)
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.90)
    ctx.set_line_width(1.8)
    ctx.stroke()

    # Window dots
    for i, col in enumerate([(1.0, 0.35, 0.35), (1.0, 0.75, 0.2), (0.2, 0.9, 0.4)]):
        ctx.set_source_rgb(*col)
        ctx.arc(x + 18 + i * 16, y + 18, 4.0, 0, 2 * math.pi); ctx.fill()

    if title:
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(12.5)
        ctx.set_source_rgba(0.9, 0.95, 1.0, 0.92)
        ctx.move_to(x + 75, y + 23)
        ctx.show_text(title)

    ctx.restore()


# ==============================================================================
# CHARACTER ANATOMY PRIMITIVES (HEAD, HOODIE, LEGS, ARMS)
# ==============================================================================

def draw_head(ctx, cx, cy, scale, mood="confident"):
    """Renders dark matte cyber helm with expressive neon visor."""
    ctx.save()
    r = 30.0 * scale

    # Base helm (dark radial gradient)
    head_pat = cairo.RadialGradient(cx - r*0.35, cy - r*0.35, r*0.1, cx, cy, r)
    head_pat.add_color_stop_rgb(0.0, 0.22, 0.25, 0.28)
    head_pat.add_color_stop_rgb(1.0, 0.05, 0.06, 0.07)
    ctx.set_source(head_pat)
    ctx.arc(cx, cy, r, 0, 2 * math.pi); ctx.fill()

    # Neon outer rim
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.92)
    ctx.set_line_width(2.4 * scale)
    ctx.arc(cx, cy, r, 0, 2 * math.pi); ctx.stroke()

    # Ear pads / Headphones
    for side in (-1, 1):
        ep_x = cx + side * (r + 1.0 * scale)
        ep_y = cy + 2.0 * scale
        ctx.save()
        ctx.translate(ep_x, ep_y)
        ctx.set_source_rgb(0.04, 0.05, 0.06)
        ctx.rectangle(-4 * scale, -9 * scale, 8 * scale, 18 * scale); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4)
        ctx.set_line_width(1.6 * scale)
        ctx.rectangle(-4 * scale, -9 * scale, 8 * scale, 18 * scale); ctx.stroke()
        ctx.restore()

    # Visor screen
    vw = r * 1.45
    vh = r * 1.0
    vx = cx - vw / 2.0
    vy = cy - vh / 2.0 + 2.0 * scale
    v_rad = 9.0 * scale
    ctx.new_sub_path()
    ctx.arc(vx + vw - v_rad, vy + v_rad, v_rad, -math.pi/2, 0)
    ctx.arc(vx + vw - v_rad, vy + vh - v_rad, v_rad, 0, math.pi/2)
    ctx.arc(vx + v_rad, vy + vh - v_rad, v_rad, math.pi/2, math.pi)
    ctx.arc(vx + v_rad, vy + v_rad, v_rad, math.pi, 3*math.pi/2)
    ctx.close_path()
    ctx.set_source_rgb(0.02, 0.03, 0.04); ctx.fill_preserve()
    ctx.set_source_rgba(0.0, 1.0, 0.5, 0.85); ctx.set_line_width(1.5 * scale); ctx.stroke()

    # Visor Expressions
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    eye_y = vy + vh * 0.45
    left_x = cx - vw * 0.25
    right_x = cx + vw * 0.25
    mouth_y = vy + vh * 0.76

    if mood == "cheeky":
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(2.8 * scale)
        ctx.move_to(left_x - 5 * scale, eye_y)
        ctx.curve_to(left_x, eye_y + 4 * scale, left_x, eye_y + 4 * scale, left_x + 5 * scale, eye_y); ctx.stroke()
        ctx.arc(right_x, eye_y - 2 * scale, 4.5 * scale, 0, 2 * math.pi); ctx.fill()
        ctx.move_to(cx - 5 * scale, mouth_y)
        ctx.curve_to(cx - 2 * scale, mouth_y + 4 * scale, cx + 2 * scale, mouth_y + 4 * scale, cx + 5 * scale, mouth_y); ctx.stroke()
    elif mood == "shocked":
        ctx.set_source_rgb(0.0, 1.0, 0.85); ctx.set_line_width(2.8 * scale)
        ctx.arc(left_x, eye_y, 7.0 * scale, 0, 2 * math.pi); ctx.stroke()
        ctx.arc(right_x, eye_y, 7.0 * scale, 0, 2 * math.pi); ctx.stroke()
        ctx.arc(left_x, eye_y, 2.2 * scale, 0, 2 * math.pi); ctx.fill()
        ctx.arc(right_x, eye_y, 2.2 * scale, 0, 2 * math.pi); ctx.fill()
        ctx.arc(cx, mouth_y, 4.0 * scale, 0, 2 * math.pi); ctx.stroke()
    elif mood == "celebrating":
        ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_line_width(3.2 * scale)
        ctx.move_to(left_x - 6 * scale, eye_y + 2 * scale)
        ctx.curve_to(left_x - 3 * scale, eye_y - 5 * scale, left_x + 3 * scale, eye_y - 5 * scale, left_x + 6 * scale, eye_y + 2 * scale); ctx.stroke()
        ctx.move_to(right_x - 6 * scale, eye_y + 2 * scale)
        ctx.curve_to(right_x - 3 * scale, eye_y - 5 * scale, right_x + 3 * scale, eye_y - 5 * scale, right_x + 6 * scale, eye_y + 2 * scale); ctx.stroke()
        ctx.move_to(cx - 7 * scale, mouth_y - 2 * scale)
        ctx.curve_to(cx - 3 * scale, mouth_y + 4 * scale, cx + 3 * scale, mouth_y + 4 * scale, cx + 7 * scale, mouth_y - 2 * scale); ctx.stroke()
    elif mood == "confused":
        ctx.set_source_rgb(0.2, 0.9, 1.0); ctx.set_line_width(2.8 * scale)
        # Left eye wide, right eye squinted
        ctx.arc(left_x, eye_y, 5.0 * scale, 0, 2 * math.pi); ctx.stroke()
        ctx.arc(left_x, eye_y, 2.0 * scale, 0, 2 * math.pi); ctx.fill()
        ctx.move_to(right_x - 5 * scale, eye_y); ctx.line_to(right_x + 5 * scale, eye_y); ctx.stroke()
        # Wavy mouth
        ctx.move_to(cx - 6 * scale, mouth_y + 2 * scale)
        ctx.curve_to(cx - 2 * scale, mouth_y - 3 * scale, cx + 2 * scale, mouth_y + 3 * scale, cx + 6 * scale, mouth_y - 2 * scale); ctx.stroke()
    elif mood == "strained": # Heavy lifting
        ctx.set_source_rgb(1.0, 0.4, 0.2); ctx.set_line_width(2.8 * scale)
        # Tightly shut grimace eyes
        ctx.move_to(left_x - 5 * scale, eye_y - 3 * scale); ctx.line_to(left_x + 5 * scale, eye_y + 3 * scale); ctx.stroke()
        ctx.move_to(left_x - 5 * scale, eye_y + 3 * scale); ctx.line_to(left_x + 5 * scale, eye_y - 3 * scale); ctx.stroke()
        ctx.move_to(right_x - 5 * scale, eye_y - 3 * scale); ctx.line_to(right_x + 5 * scale, eye_y + 3 * scale); ctx.stroke()
        ctx.move_to(right_x - 5 * scale, eye_y + 3 * scale); ctx.line_to(right_x + 5 * scale, eye_y - 3 * scale); ctx.stroke()
        ctx.move_to(cx - 7 * scale, mouth_y); ctx.line_to(cx + 7 * scale, mouth_y); ctx.stroke()
    elif mood == "laser":
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(2.0 * scale)
        for ex in (left_x, right_x):
            ctx.arc(ex, eye_y, 5.5 * scale, 0, 2 * math.pi); ctx.stroke()
            ctx.move_to(ex - 7 * scale, eye_y); ctx.line_to(ex + 7 * scale, eye_y); ctx.stroke()
            ctx.move_to(ex, eye_y - 7 * scale); ctx.line_to(ex, eye_y + 7 * scale); ctx.stroke()
            ctx.arc(ex, eye_y, 1.6 * scale, 0, 2 * math.pi); ctx.fill()
        ctx.move_to(cx - 5 * scale, mouth_y); ctx.line_to(cx + 6 * scale, mouth_y + 1 * scale); ctx.stroke()
    elif mood == "thinking":
        ctx.set_source_rgb(0.2, 0.9, 1.0); ctx.set_line_width(2.6 * scale)
        ctx.arc(left_x, eye_y - 2 * scale, 4.8 * scale, 0, 2 * math.pi); ctx.stroke()
        ctx.move_to(right_x - 5 * scale, eye_y + 1 * scale); ctx.line_to(right_x + 5 * scale, eye_y + 1 * scale); ctx.stroke()
        ctx.move_to(cx - 5 * scale, mouth_y); ctx.line_to(cx + 4 * scale, mouth_y - 2 * scale); ctx.stroke()
    else: # confident
        ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_line_width(2.8 * scale)
        for ex in (left_x, right_x):
            ctx.arc(ex, eye_y, 4.2 * scale, 0, 2 * math.pi); ctx.fill()
        ctx.move_to(cx - 5 * scale, mouth_y)
        ctx.curve_to(cx - 2 * scale, mouth_y + 3.0 * scale, cx + 2 * scale, mouth_y + 3.0 * scale, cx + 5 * scale, mouth_y); ctx.stroke()

    ctx.restore()
    ctx.restore()


def draw_dark_hoodie(ctx, cx, cy, scale, torso_lean=0.0):
    """Renders dark matte hoodie with kangaroo pocket and mandatory FLOWORKOS.COM chest badge."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(torso_lean)

    hw_shoulder = 34.0 * scale
    hw_waist = 26.0 * scale
    torso_h = 78.0 * scale

    hoodie_pat = cairo.LinearGradient(0, 0, 0, torso_h)
    hoodie_pat.add_color_stop_rgb(0.0, 0.12, 0.15, 0.18)
    hoodie_pat.add_color_stop_rgb(1.0, 0.05, 0.06, 0.08)
    ctx.set_source(hoodie_pat)

    ctx.move_to(-12 * scale, 0)
    ctx.line_to(-hw_shoulder, 12 * scale)
    ctx.line_to(-hw_waist - 3 * scale, torso_h - 10 * scale)
    ctx.line_to(-hw_waist, torso_h)
    ctx.line_to(hw_waist, torso_h)
    ctx.line_to(hw_waist + 3 * scale, torso_h - 10 * scale)
    ctx.line_to(hw_shoulder, 12 * scale)
    ctx.line_to(12 * scale, 0)
    ctx.close_path()
    ctx.fill_preserve()

    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.9)
    ctx.set_line_width(1.8 * scale)
    ctx.stroke()

    # Kangaroo pocket
    py = torso_h * 0.62
    pw = hw_waist * 0.88
    ph = torso_h * 0.32
    ctx.set_source_rgba(0.04, 0.05, 0.07, 0.95)
    ctx.rectangle(-pw, py, pw * 2, ph); ctx.fill_preserve()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6); ctx.set_line_width(1.4 * scale); ctx.stroke()

    # ⭐ ULTRA-BRIGHT 'FLOWORKOS.COM' LOGO BADGE
    badge_y = 17.0 * scale
    badge_w = 64.0 * scale
    badge_h = 19.0 * scale
    bx = -badge_w / 2.0
    by = badge_y

    ctx.set_source_rgb(0.02, 0.03, 0.04)
    ctx.rectangle(bx, by, badge_w, badge_h); ctx.fill_preserve()
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.6 * scale); ctx.stroke()

    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(7.0 * scale)
    ext = ctx.text_extents("FLOWORKOS.COM")

    # Double pass for maximum neon glow & legibility
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.4)
    ctx.move_to(-ext.width / 2.0, by + badge_h * 0.68 + 0.5 * scale); ctx.show_text("FLOWORKOS.COM")
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(-ext.width / 2.0, by + badge_h * 0.68); ctx.show_text("FLOWORKOS.COM")

    # Short drawstrings (non-occluding)
    ctx.set_source_rgba(0.85, 0.95, 1.0, 0.9)
    ctx.set_line_width(1.8 * scale)
    for side in (-1, 1):
        ctx.move_to(side * 8 * scale, 6 * scale)
        ctx.curve_to(side * 10 * scale, 11 * scale, side * 13 * scale, 13 * scale, side * 14 * scale, 15 * scale); ctx.stroke()
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.arc(side * 14 * scale, 16 * scale, 1.5 * scale, 0, 2*math.pi); ctx.fill()

    ctx.restore()
    return torso_h


def draw_dark_leg(ctx, hip_x, hip_y, foot_x, foot_y, scale, is_left=True):
    """Draws sleek dark leg with cyber sneaker."""
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    mid_x = (hip_x + foot_x) / 2.0 + (3.0 * scale if is_left else -3.0 * scale)
    mid_y = (hip_y + foot_y) / 2.0
    ctx.set_source_rgb(0.06, 0.08, 0.10)
    ctx.set_line_width(10.0 * scale)
    ctx.move_to(hip_x, hip_y); ctx.line_to(mid_x, mid_y); ctx.line_to(foot_x, foot_y - 6 * scale); ctx.stroke()

    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.7)
    ctx.set_line_width(1.5 * scale)
    ctx.move_to(hip_x, hip_y); ctx.line_to(mid_x, mid_y); ctx.line_to(foot_x, foot_y - 6 * scale); ctx.stroke()

    # Sneaker with matrix green sole
    ctx.save()
    ctx.translate(foot_x, foot_y)
    flip = 1 if is_left else -1
    ctx.scale(flip, 1)
    ctx.set_source_rgb(0.1, 0.12, 0.15)
    ctx.rectangle(-11 * scale, -9 * scale, 28 * scale, 9 * scale); ctx.fill_preserve()
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.4 * scale); ctx.stroke()
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.rectangle(-12 * scale, 0, 30 * scale, 3.8 * scale); ctx.fill()
    ctx.restore()
    ctx.restore()


def draw_arm_and_hand(ctx, sh_x, sh_y, hand_x, hand_y, scale, gesture="open", item=None):
    """Draws posable arm with hands & props."""
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    dx = hand_x - sh_x
    dy = hand_y - sh_y
    bend_dir = 1.0 if dx > 0 else -1.0
    elbow_x = (sh_x + hand_x) / 2.0 + (dy * 0.18 * bend_dir)
    elbow_y = (sh_y + hand_y) / 2.0 - (abs(dx) * 0.15)

    ctx.set_source_rgb(0.08, 0.11, 0.15); ctx.set_line_width(9.5 * scale)
    ctx.move_to(sh_x, sh_y); ctx.line_to(elbow_x, elbow_y); ctx.line_to(hand_x, hand_y); ctx.stroke()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.75); ctx.set_line_width(1.5 * scale)
    ctx.move_to(sh_x, sh_y); ctx.line_to(elbow_x, elbow_y); ctx.line_to(hand_x, hand_y); ctx.stroke()

    ctx.save()
    ctx.translate(hand_x, hand_y)
    ctx.set_source_rgb(0.9, 0.95, 1.0)

    if gesture == "point":
        ang = math.atan2(dy, dx); ctx.rotate(ang)
        ctx.arc(0, 0, 4.8 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(3.0 * scale); ctx.move_to(0, 0); ctx.line_to(11 * scale, 0); ctx.stroke()
        if item == "laser_pointer":
            ctx.set_source_rgb(0.2, 0.25, 0.3); ctx.set_line_width(2.0 * scale)
            ctx.move_to(2 * scale, 0); ctx.line_to(45 * scale, 0); ctx.stroke()
            ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.arc(45 * scale, 0, 3.5 * scale, 0, 2*math.pi); ctx.fill()
            ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6); ctx.set_line_width(1.2 * scale)
            ctx.move_to(45 * scale, 0); ctx.line_to(120 * scale, -5 * scale); ctx.stroke()
    elif gesture == "clutch":
        ctx.arc(0, 0, 5.5 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(2.0 * scale)
        for f_ang in (-0.6, -0.2, 0.2, 0.6):
            ctx.move_to(0, 0); ctx.line_to(math.cos(f_ang) * 9 * scale, math.sin(f_ang) * 9 * scale); ctx.stroke()
    elif gesture == "chin":
        ctx.arc(0, 0, 5.0 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(2.4 * scale)
        ctx.move_to(0, 0); ctx.line_to(4 * scale, -7 * scale); ctx.stroke()
    elif gesture == "scratch":
        # Scratching head
        ctx.arc(0, 0, 5.0 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(2.0 * scale)
        ctx.move_to(0, 0); ctx.line_to(-4 * scale, -8 * scale); ctx.stroke()
        ctx.move_to(2 * scale, 0); ctx.line_to(0 * scale, -9 * scale); ctx.stroke()
    elif gesture == "mug":
        ctx.arc(0, 0, 5.0 * scale, 0, 2*math.pi); ctx.fill()
        ctx.save()
        ctx.set_source_rgb(0.12, 0.18, 0.25); ctx.rectangle(2 * scale, -12 * scale, 14 * scale, 16 * scale); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.2 * scale); ctx.rectangle(2 * scale, -12 * scale, 14 * scale, 16 * scale); ctx.stroke()
        ctx.arc(16 * scale, -4 * scale, 4 * scale, -math.pi/2, math.pi/2); ctx.stroke()
        ctx.set_source_rgba(0.0, 1.0, 0.5, 0.7)
        ctx.move_to(6 * scale, -15 * scale); ctx.line_to(7 * scale, -22 * scale); ctx.stroke()
        ctx.move_to(11 * scale, -15 * scale); ctx.line_to(12 * scale, -24 * scale); ctx.stroke()
        ctx.restore()
    elif gesture == "lifting":
        # Hands palm up under heavy load
        ctx.arc(0, 0, 5.0 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(2.5 * scale)
        ctx.move_to(-7 * scale, -2 * scale); ctx.line_to(7 * scale, -2 * scale); ctx.stroke()
    else: # open
        ctx.arc(0, 0, 5.0 * scale, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(2.2 * scale)
        for f_ang in (-0.5, -0.15, 0.2, 0.55):
            ctx.move_to(0, 0); ctx.line_to(math.cos(f_ang) * 8.5 * scale, math.sin(f_ang) * 8.5 * scale); ctx.stroke()
    ctx.restore()
    ctx.restore()


# ==============================================================================
# 16 DISTINCT SCENE TEMPLATES IMPLEMENTATION
# ==============================================================================

def render_scene_template(ctx, px, py, pw, ph, scene_num, title, action_key, bg_color):
    """Renders one self-contained, fully decorated adegan / scene template."""
    ctx.save()
    ctx.rectangle(px, py, pw, ph); ctx.clip()

    # 1. Background
    draw_nonwhite_bg(ctx, pw, ph, bg_type=bg_color)

    # 2. Card Container / Stage Frame
    card_x, card_y, card_w, card_h = px + 20, py + 16, pw - 40, ph - 32
    draw_dark_card(ctx, card_x, card_y, card_w, card_h, f"{scene_num}. {title}")

    cx = card_x + card_w / 2.0
    cy = card_y + card_h / 2.0 + 30
    sc = 1.05

    # 3. Kinematic Scene Realization
    if action_key == "walking":
        # 1. Pacing / Walking presentation across stage
        ground_y = cy + 60
        torso_y = ground_y - 110 * sc
        head_y = torso_y - 36 * sc
        hip_y = torso_y + 78 * sc
        draw_dark_hoodie(ctx, cx, torso_y, sc, torso_lean=0.08)
        draw_head(ctx, cx + 4 * sc, head_y, sc, mood="confident")
        # Walking leg stride
        draw_dark_leg(ctx, cx - 12 * sc, hip_y, cx - 35 * sc, ground_y, sc, is_left=True)
        draw_dark_leg(ctx, cx + 12 * sc, hip_y, cx + 28 * sc, ground_y - 8 * sc, sc, is_left=False)
        sh_y = torso_y + 14 * sc
        draw_arm_and_hand(ctx, cx - 28 * sc, sh_y, cx - 40 * sc, torso_y + 40 * sc, sc, gesture="open")
        draw_arm_and_hand(ctx, cx + 28 * sc, sh_y, cx + 48 * sc, torso_y + 15 * sc, sc, gesture="point")
        # Motion arrows on ground
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6); ctx.set_line_width(1.5)
        ctx.move_to(cx - 70, ground_y + 10); ctx.line_to(cx + 70, ground_y + 10); ctx.stroke()
        ctx.move_to(cx + 60, ground_y + 6); ctx.line_to(cx + 70, ground_y + 10); ctx.line_to(cx + 60, ground_y + 14); ctx.stroke()

    elif action_key == "bouncing":
        # 2. Enthusiastic bouncing / double hop
        ground_y = cy + 60
        hop_y = -35 * sc
        torso_y = ground_y - 110 * sc + hop_y
        head_y = torso_y - 36 * sc
        hip_y = torso_y + 78 * sc
        draw_dark_hoodie(ctx, cx, torso_y, sc, torso_lean=0.0)
        draw_head(ctx, cx, head_y, sc, mood="celebrating")
        # Bent knees hopping in mid-air
        draw_dark_leg(ctx, cx - 14 * sc, hip_y, cx - 18 * sc, ground_y - 25 * sc, sc, is_left=True)
        draw_dark_leg(ctx, cx + 14 * sc, hip_y, cx + 18 * sc, ground_y - 25 * sc, sc, is_left=False)
        sh_y = torso_y + 12 * sc
        draw_arm_and_hand(ctx, cx - 28 * sc, sh_y, cx - 45 * sc, torso_y - 10 * sc, sc, gesture="open")
        draw_arm_and_hand(ctx, cx + 28 * sc, sh_y, cx + 45 * sc, torso_y - 10 * sc, sc, gesture="open")
        # Spring bounce lines
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.7); ctx.set_line_width(1.8)
        ctx.arc(cx, ground_y + 5, 20, math.pi * 0.2, math.pi * 0.8); ctx.stroke()
        ctx.arc(cx, ground_y + 12, 12, math.pi * 0.2, math.pi * 0.8); ctx.stroke()

    elif action_key == "salto":
        # 3. Mid-air 360 flip over red bug block
        bug_x, bug_y, bug_w, bug_h = cx - 55, cy + 38, 110, 40
        ctx.set_source_rgba(0.2, 0.04, 0.06, 0.95); ctx.rectangle(bug_x, bug_y, bug_w, bug_h); ctx.fill()
        ctx.set_source_rgb(1.0, 0.25, 0.35); ctx.set_line_width(1.5); ctx.rectangle(bug_x, bug_y, bug_w, bug_h); ctx.stroke()
        ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(10); ctx.move_to(bug_x + 8, bug_y + 24); ctx.show_text("⚠️ BUG: O(N²)")

        ctx.save()
        ctx.translate(cx, cy - 30)
        ctx.rotate(-0.85) # Mid-flip inversion
        draw_dark_hoodie(ctx, 0, -8 * sc, sc * 0.92, torso_lean=0.2)
        draw_head(ctx, 0, -38 * sc, sc * 0.92, mood="celebrating")
        draw_dark_leg(ctx, -10 * sc, 22 * sc, -24 * sc, -2 * sc, sc * 0.85, is_left=True)
        draw_dark_leg(ctx, 10 * sc, 22 * sc, 24 * sc, -2 * sc, sc * 0.85, is_left=False)
        draw_arm_and_hand(ctx, -24 * sc, 5 * sc, -24 * sc, 12 * sc, sc * 0.85, gesture="clutch")
        draw_arm_and_hand(ctx, 24 * sc, 5 * sc, 24 * sc, 12 * sc, sc * 0.85, gesture="clutch")
        ctx.restore()

    elif action_key == "hanging":
        # 4. Playful card edge hanging
        anchor_x = card_x + card_w - 85
        anchor_y = card_y
        ctx.save()
        ctx.translate(anchor_x, anchor_y)
        ctx.rotate(0.08)
        for side in (-1, 1):
            ctx.set_source_rgb(0.05, 0.08, 0.12); ctx.arc(side * 18 * sc, 0, 5 * sc, 0, 2*math.pi); ctx.fill()
            ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.arc(side * 18 * sc, 0, 5 * sc, 0, 2*math.pi); ctx.stroke()
        draw_head(ctx, 0, 36 * sc, sc, mood="cheeky")
        draw_dark_hoodie(ctx, 0, 70 * sc, sc, torso_lean=0.0)
        draw_arm_and_hand(ctx, -26 * sc, 82 * sc, -18 * sc, 0, sc, gesture="clutch")
        draw_arm_and_hand(ctx, 26 * sc, 82 * sc, 18 * sc, 0, sc, gesture="clutch")
        draw_dark_leg(ctx, -12 * sc, 148 * sc, -22 * sc, 215 * sc, sc, is_left=True)
        draw_dark_leg(ctx, 12 * sc, 148 * sc, 28 * sc, 205 * sc, sc, is_left=False)
        ctx.restore()
        ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_font_size(13)
        ctx.move_to(card_x + 25, card_y + 75); ctx.show_text("2,000,000 TOKEN ILLUSION")
        ctx.set_source_rgb(0.8, 0.9, 1.0); ctx.set_font_size(11)
        ctx.move_to(card_x + 25, card_y + 105); ctx.show_text("Swinging playfully from upper card rim!")

    elif action_key == "sitting_laptop":
        # 5. Seated on ledge with coffee & laptop
        ledge_y = cy + 40
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(2.5)
        ctx.move_to(cx - 130, ledge_y); ctx.line_to(cx + 130, ledge_y); ctx.stroke()

        head_y = ledge_y - 120 * sc
        torso_y = head_y + 36 * sc
        hip_y = torso_y + 75 * sc
        draw_dark_hoodie(ctx, cx, torso_y, sc, torso_lean=0.05)
        draw_head(ctx, cx + 2 * sc, head_y, sc, mood="confident")
        draw_dark_leg(ctx, cx - 12 * sc, hip_y, cx - 16 * sc, hip_y + 65 * sc, sc, is_left=True)
        draw_dark_leg(ctx, cx + 12 * sc, hip_y, cx + 16 * sc, hip_y + 65 * sc, sc, is_left=False)

        lap_x, lap_y = cx + 20 * sc, torso_y + 48 * sc
        draw_arm_and_hand(ctx, cx - 30 * sc, torso_y + 14 * sc, lap_x - 8 * sc, lap_y, sc, gesture="point")
        draw_arm_and_hand(ctx, cx + 30 * sc, torso_y + 14 * sc, lap_x + 8 * sc, lap_y, sc, gesture="point")

        # Laptop
        ctx.save(); ctx.translate(lap_x, lap_y)
        ctx.set_source_rgb(0.08, 0.12, 0.18); ctx.rectangle(-18 * sc, 0, 36 * sc, 7 * sc); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.0); ctx.rectangle(-18 * sc, 0, 36 * sc, 7 * sc); ctx.stroke()
        ctx.set_source_rgba(0.02, 0.05, 0.09, 0.95); ctx.rectangle(10 * sc, -22 * sc, 5 * sc, 22 * sc); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_line_width(1.0); ctx.rectangle(10 * sc, -22 * sc, 5 * sc, 22 * sc); ctx.stroke()
        ctx.restore()

    elif action_key == "sprint":
        # 6. Turbo sprint with speed lines
        ground_y = cy + 60
        torso_y = ground_y - 110 * sc
        head_y = torso_y - 36 * sc
        hip_y = torso_y + 78 * sc
        draw_dark_hoodie(ctx, cx, torso_y, sc, torso_lean=0.32)
        draw_head(ctx, cx + 16 * sc, head_y + 5 * sc, sc, mood="laser")
        draw_dark_leg(ctx, cx - 12 * sc, hip_y, cx - 44 * sc, ground_y, sc, is_left=True)
        draw_dark_leg(ctx, cx + 12 * sc, hip_y, cx + 46 * sc, ground_y - 18 * sc, sc, is_left=False)
        sh_y = torso_y + 14 * sc
        draw_arm_and_hand(ctx, cx - 30 * sc, sh_y, cx + 38 * sc, torso_y + 45 * sc, sc, gesture="open")
        draw_arm_and_hand(ctx, cx + 30 * sc, sh_y, cx - 38 * sc, torso_y + 20 * sc, sc, gesture="open")
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6); ctx.set_line_width(1.5)
        for wy in range(int(torso_y), int(ground_y), 15):
            ctx.move_to(cx - 95 * sc, wy); ctx.line_to(cx - 50 * sc, wy); ctx.stroke()

    elif action_key == "splat":
        # 7. Flat cartoon splat on floor
        ground_y = cy + 55
        ctx.set_source_rgba(0.0, 0.0, 0.0, 0.25); ctx.rectangle(cx - 85 * sc, ground_y - 5 * sc, 170 * sc, 10 * sc); ctx.fill()
        ctx.save(); ctx.translate(cx, ground_y - 10 * sc); ctx.scale(1.2, 0.4)
        draw_dark_hoodie(ctx, 0, 0, sc, torso_lean=0.0)
        ctx.restore()
        draw_head(ctx, cx - 55 * sc, ground_y - 24 * sc, sc * 0.88, mood="shocked")
        draw_dark_leg(ctx, cx + 25 * sc, ground_y - 6 * sc, cx + 80 * sc, ground_y - 4 * sc, sc * 0.85, is_left=True)
        for st_x in (-70, -55, -40):
            ctx.set_source_rgb(1.0, 0.85, 0.2); ctx.arc(cx + st_x * sc, ground_y - 45 * sc, 3.2, 0, 2*math.pi); ctx.fill()
        ctx.set_font_size(12); ctx.set_source_rgb(1.0, 0.3, 0.4)
        ctx.move_to(cx - 15, ground_y - 35); ctx.show_text("💥 CRASH: TTL TIMEOUT")

    elif action_key == "hover":
        # 8. Sci-Fi jetpack hover
        head_y = cy - 75 * sc
        torso_y = head_y + 36 * sc
        hip_y = torso_y + 78 * sc
        feet_y = hip_y + 70 * sc
        draw_dark_hoodie(ctx, cx, torso_y, sc, torso_lean=0.0)
        draw_head(ctx, cx, head_y, sc, mood="laser")
        draw_dark_leg(ctx, cx - 12 * sc, hip_y, cx - 16 * sc, feet_y, sc, is_left=True)
        draw_dark_leg(ctx, cx + 12 * sc, hip_y, cx + 16 * sc, feet_y, sc, is_left=False)
        sh_y = torso_y + 14 * sc
        draw_arm_and_hand(ctx, cx - 30 * sc, sh_y, cx - 50 * sc, torso_y + 35 * sc, sc, gesture="open")
        draw_arm_and_hand(ctx, cx + 30 * sc, sh_y, cx + 50 * sc, torso_y + 35 * sc, sc, gesture="open")
        for fx in (cx - 16 * sc, cx + 16 * sc):
            ctx.save(); ctx.translate(fx, feet_y + 6 * sc)
            pat = cairo.LinearGradient(0, 0, 0, 25 * sc)
            pat.add_color_stop_rgba(0.0, 0.0, 1.0, 0.5, 0.95)
            pat.add_color_stop_rgba(1.0, 0.0, 0.8, 1.0, 0.0)
            ctx.set_source(pat)
            ctx.move_to(-6 * sc, 0); ctx.line_to(6 * sc, 0); ctx.line_to(0, 25 * sc); ctx.close_path(); ctx.fill()
            ctx.restore()

    elif action_key == "peeking":
        # 9. Peeking curiously from bottom screen border
        peek_y = card_y + card_h
        draw_head(ctx, cx, peek_y - 20 * sc, sc * 1.1, mood="cheeky")
        for h_side in (-1, 1):
            ctx.set_source_rgb(0.05, 0.08, 0.12); ctx.arc(cx + h_side * 28 * sc, peek_y, 5 * sc, 0, 2*math.pi); ctx.fill()
            ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.arc(cx + h_side * 28 * sc, peek_y, 5 * sc, 0, 2*math.pi); ctx.stroke()
        ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_font_size(13)
        ctx.move_to(card_x + 30, card_y + 75); ctx.show_text("PEEKING AT CRITICAL LOGS...")
        ctx.set_source_rgb(0.8, 0.9, 1.0); ctx.set_font_size(11)
        ctx.move_to(card_x + 30, card_y + 100); ctx.show_text("Peekaboo comedic pop-up from border!")

    elif action_key == "confused":
        # 10. Confused scratching head
        ground_y = cy + 60
        torso_y = ground_y - 110 * sc
        head_y = torso_y - 36 * sc
        hip_y = torso_y + 78 * sc
        draw_dark_hoodie(ctx, cx, torso_y, sc, torso_lean=-0.06)
        draw_head(ctx, cx - 2 * sc, head_y, sc, mood="confused")
        draw_dark_leg(ctx, cx - 12 * sc, hip_y, cx - 20 * sc, ground_y, sc, is_left=True)
        draw_dark_leg(ctx, cx + 12 * sc, hip_y, cx + 14 * sc, ground_y, sc, is_left=False)
        sh_y = torso_y + 14 * sc
        # Left hand on hip, right hand scratching top of head
        draw_arm_and_hand(ctx, cx - 28 * sc, sh_y, cx - 35 * sc, hip_y - 5 * sc, sc, gesture="open")
        draw_arm_and_hand(ctx, cx + 28 * sc, sh_y, cx + 6 * sc, head_y - 20 * sc, sc, gesture="scratch")
        # Floating question marks '???'
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(24); ctx.set_source_rgb(0.2, 0.9, 1.0)
        ctx.move_to(cx + 40, head_y - 10); ctx.show_text("???")

    elif action_key == "thinking":
        # 11. Detective deep thinking + HUD formula
        ground_y = cy + 60
        torso_y = ground_y - 110 * sc
        head_y = torso_y - 36 * sc
        hip_y = torso_y + 78 * sc
        draw_dark_hoodie(ctx, cx - 22, torso_y, sc, torso_lean=0.04)
        draw_head(ctx, cx - 18, head_y, sc, mood="thinking")
        draw_dark_leg(ctx, cx - 34, hip_y, cx - 42, ground_y, sc, is_left=True)
        draw_dark_leg(ctx, cx - 10, hip_y, cx - 2, ground_y, sc, is_left=False)
        sh_y = torso_y + 14 * sc
        draw_arm_and_hand(ctx, cx - 50, sh_y, cx - 60, hip_y - 8 * sc, sc, gesture="open")
        draw_arm_and_hand(ctx, cx + 8, sh_y, cx - 8, head_y + 20 * sc, sc, gesture="chin")
        # Floating formula HUD
        ctx.set_source_rgba(0.01, 0.04, 0.08, 0.92); ctx.rectangle(cx + 25, head_y - 25, 105, 45); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_line_width(1.2); ctx.rectangle(cx + 25, head_y - 25, 105, 45); ctx.stroke()
        ctx.set_font_size(9.5); ctx.move_to(cx + 33, head_y - 8); ctx.show_text("// ACP-KERNEL")
        ctx.move_to(cx + 33, head_y + 11); ctx.show_text("O(N²) -> O(1)")

    elif action_key == "leaning":
        # 12. Cool leaning on card frame with coffee mug
        ground_y = cy + 60
        torso_y = ground_y - 110 * sc
        head_y = torso_y - 36 * sc
        hip_y = torso_y + 78 * sc
        draw_dark_hoodie(ctx, cx - 15, torso_y, sc, torso_lean=0.10)
        draw_head(ctx, cx - 10, head_y, sc, mood="confident")
        # Crossed ankles
        draw_dark_leg(ctx, cx - 26, hip_y, cx - 10, ground_y, sc, is_left=True)
        draw_dark_leg(ctx, cx - 4, hip_y, cx - 20, ground_y, sc, is_left=False)
        sh_y = torso_y + 14 * sc
        # Arm 1 leaning on vertical beam, arm 2 holding coffee
        draw_arm_and_hand(ctx, cx - 40, sh_y, cx - 75, torso_y + 35 * sc, sc, gesture="open")
        draw_arm_and_hand(ctx, cx + 15, sh_y, cx + 38, torso_y + 15 * sc, sc, gesture="mug")
        # Vertical neon pillar
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(2.5)
        ctx.move_to(cx - 75, card_y + 40); ctx.line_to(cx - 75, ground_y + 5); ctx.stroke()

    elif action_key == "heavy_lifting":
        # 13. Straining to lift 2M token database block
        ground_y = cy + 60
        squat_y = 18 * sc
        torso_y = ground_y - 110 * sc + squat_y
        head_y = torso_y - 34 * sc
        hip_y = torso_y + 78 * sc
        draw_dark_hoodie(ctx, cx, torso_y, sc, torso_lean=0.0)
        draw_head(ctx, cx, head_y, sc, mood="strained")
        # Wide squat legs
        draw_dark_leg(ctx, cx - 16 * sc, hip_y, cx - 40 * sc, ground_y, sc, is_left=True)
        draw_dark_leg(ctx, cx + 16 * sc, hip_y, cx + 40 * sc, ground_y, sc, is_left=False)
        sh_y = torso_y + 12 * sc
        # Arms raised overhead holding colossal block
        draw_arm_and_hand(ctx, cx - 28 * sc, sh_y, cx - 42 * sc, head_y - 25 * sc, sc, gesture="lifting")
        draw_arm_and_hand(ctx, cx + 28 * sc, sh_y, cx + 42 * sc, head_y - 25 * sc, sc, gesture="lifting")
        # Giant database block
        db_x, db_y, db_w, db_h = cx - 75, head_y - 70 * sc, 150, 42
        ctx.set_source_rgba(0.08, 0.12, 0.18, 0.95); ctx.rectangle(db_x, db_y, db_w, db_h); ctx.fill()
        ctx.set_source_rgb(1.0, 0.5, 0.2); ctx.set_line_width(1.8); ctx.rectangle(db_x, db_y, db_w, db_h); ctx.stroke()
        ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(10); ctx.move_to(db_x + 12, db_y + 26); ctx.show_text("📦 2,000,000 TOKENS")

    elif action_key == "shocked":
        # 14. Panic clutching cheeks ($1,450 API Bill crisis)
        ground_y = cy + 60
        torso_y = ground_y - 110 * sc
        head_y = torso_y - 36 * sc
        hip_y = torso_y + 78 * sc
        draw_dark_hoodie(ctx, cx, torso_y, sc, torso_lean=-0.16)
        draw_head(ctx, cx - 18 * sc, head_y - 2 * sc, sc, mood="shocked")
        draw_dark_leg(ctx, cx - 24 * sc, hip_y, cx - 44 * sc, ground_y, sc, is_left=True)
        draw_dark_leg(ctx, cx - 2 * sc, hip_y, cx + 28 * sc, ground_y, sc, is_left=False)
        sh_y = torso_y + 14 * sc
        draw_arm_and_hand(ctx, cx - 38 * sc, sh_y, cx - 38 * sc, head_y - 8 * sc, sc, gesture="clutch")
        draw_arm_and_hand(ctx, cx + 16 * sc, sh_y, cx + 5 * sc, head_y - 10 * sc, sc, gesture="clutch")
        ctx.set_source_rgb(1.0, 0.25, 0.35); ctx.set_font_size(16)
        ctx.move_to(card_x + 25, card_y + 75); ctx.show_text("$1,450.00 API BILL!")

    elif action_key == "celebrating":
        # 15. Victory celebration leap + confetti
        ground_y = cy + 60
        jump_y = -24.0 * sc
        torso_y = ground_y - 110 * sc + jump_y
        head_y = torso_y - 36 * sc
        hip_y = torso_y + 78 * sc
        draw_dark_hoodie(ctx, cx, torso_y, sc, torso_lean=0.0)
        draw_head(ctx, cx, head_y, sc, mood="celebrating")
        draw_dark_leg(ctx, cx - 14 * sc, hip_y, cx - 26 * sc, ground_y - 20 * sc, sc, is_left=True)
        draw_dark_leg(ctx, cx + 14 * sc, hip_y, cx + 26 * sc, ground_y - 20 * sc, sc, is_left=False)
        sh_y = torso_y + 12 * sc
        draw_arm_and_hand(ctx, cx - 30 * sc, sh_y, cx - 55 * sc, head_y - 28 * sc, sc, gesture="open")
        draw_arm_and_hand(ctx, cx + 30 * sc, sh_y, cx + 55 * sc, head_y - 28 * sc, sc, gesture="open")
        for cp in range(16):
            c_x = cx - 100 + (cp * 43) % 200
            c_y = card_y + 40 + (cp * 29) % 130
            ctx.set_source_rgba(0.2 + 0.3 * math.sin(cp), 0.8, 0.4, 0.85)
            ctx.rectangle(c_x, c_y, 5, 3); ctx.fill()

    elif action_key == "camera_zoom":
        # 16. Dynamic macro camera zoom (2.5x closeup)
        ctx.save()
        ctx.rectangle(card_x + 2, card_y + 35, card_w - 4, card_h - 37); ctx.clip()
        draw_dark_hoodie(ctx, cx, cy + 90, scale=2.4, torso_lean=0.0)
        draw_head(ctx, cx, cy - 20, scale=2.4, mood="confident")
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.85); ctx.set_line_width(1.5)
        ctx.rectangle(cx - 150, cy - 100, 300, 200); ctx.stroke()
        ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(12); ctx.set_source_rgb(0.0, 1.0, 0.4)
        ctx.move_to(cx - 140, cy - 78); ctx.show_text("[CAMERA PUNCH-IN: 2.5x]")
        ctx.restore()

    ctx.restore()


# ==============================================================================
# MASTER CATALOG & INDIVIDUAL TEMPLATE EXPORTER
# ==============================================================================

def main():
    assets_dir = "/opt/floworkos/skills/githubtoyoutube/assets"
    templates_dir = os.path.join(assets_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)

    catalog = [
        # Row 1
        ("01", "WALKING / PACING", "walking", "kraft"),
        ("02", "BOUNCING / DOUBLE HOP", "bouncing", "cream"),
        ("03", "SALTO 360° OVER BUG", "salto", "sage"),
        ("04", "HANGING FROM CARD TOP", "hanging", "amber"),
        # Row 2
        ("05", "SITTING ON EDGE + LAPTOP", "sitting_laptop", "slate"),
        ("06", "TURBO HIGH-SPEED SPRINT", "sprint", "kraft"),
        ("07", "SLAPSTICK FLAT SPLAT", "splat", "cream"),
        ("08", "HOVER JETPACK THRUSTERS", "hover", "sage"),
        # Row 3
        ("09", "PEEKING FROM BORDER", "peeking", "amber"),
        ("10", "CONFUSED HEAD SCRATCH", "confused", "slate"),
        ("11", "DETECTIVE DEEP THINKING", "thinking", "kraft"),
        ("12", "COOL LEANING ON FRAME", "leaning", "cream"),
        # Row 4
        ("13", "HEAVY LIFTING DATABASE", "heavy_lifting", "sage"),
        ("14", "PANIC CLUTCHING CHEEKS", "shocked", "amber"),
        ("15", "VICTORY LEAP + CONFETTI", "celebrating", "slate"),
        ("16", "MACRO CAMERA ZOOM (2.5x)", "camera_zoom", "cream"),
    ]

    print("[*] Generating 16 Individual High-Resolution Templates (1920x1080)...")
    for s_num, s_title, a_key, bg_col in catalog:
        item_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1920, 1080)
        item_ctx = cairo.Context(item_surf)
        render_scene_template(item_ctx, 0, 0, 1920, 1080, s_num, s_title, a_key, bg_col)
        item_filename = f"{s_num}_{a_key}.png"
        item_path = os.path.join(templates_dir, item_filename)
        item_surf.write_to_png(item_path)

    print("[*] Generating 16-Scene Master Catalog Grid (2560x1600, 4x4)...")
    CATALOG_W = 2560
    CATALOG_H = 1600
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, CATALOG_W, CATALOG_H)
    ctx = cairo.Context(surf)

    draw_nonwhite_bg(ctx, CATALOG_W, CATALOG_H, bg_type="cream")

    # Header Bar
    ctx.save()
    ctx.set_source_rgba(0.04, 0.07, 0.10, 0.96)
    ctx.rectangle(40, 20, CATALOG_W - 80, 80); ctx.fill()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.9); ctx.set_line_width(2.2)
    ctx.rectangle(40, 20, CATALOG_W - 80, 80); ctx.stroke()

    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26); ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(65, 68)
    ctx.show_text("STICKMAN (MR. FLOW) 16 MASTER SCENE TEMPLATES // CINEMATIC KINEMATICS CATALOG")

    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(14); ctx.set_source_rgba(0.9, 0.95, 1.0, 0.95)
    ctx.move_to(CATALOG_W - 740, 68)
    ctx.show_text("BRAND: FLOWORKOS.COM (HIGH-CONTRAST INVERSION)")
    ctx.restore()

    # 4 Columns x 4 Rows
    COLS, ROWS = 4, 4
    PW, PH = 590, 345
    GAP_X, GAP_Y = 25, 20
    START_X = 55
    START_Y = 120

    for idx, (s_num, s_title, a_key, bg_col) in enumerate(catalog):
        c = idx % COLS
        r = idx // COLS
        px = START_X + c * (PW + GAP_X)
        py = START_Y + r * (PH + GAP_Y)
        render_scene_template(ctx, px, py, PW, PH, s_num, s_title, a_key, bg_col)

    master_catalog_path = os.path.join(assets_dir, "sticky_scene_templates_catalog.png")
    surf.write_to_png(master_catalog_path)
    print(f"[✓] MASTER 16-SCENE CATALOG CREATED: {master_catalog_path}")

    # Mirror to Vault & Brain Artifact Directory
    user_vault = os.path.expanduser("~/Documents/videos/billion-context-documentary")
    brain_dir = os.environ.get("FLOWORK_ARTIFACTS_DIR")
    os.makedirs(user_vault, exist_ok=True)
    os.makedirs(theme_vault, exist_ok=True)

    os.system(f"cp {master_catalog_path} {user_vault}/sticky_scene_templates_catalog.png")
    os.system(f"cp {master_catalog_path} {theme_vault}/sticky_scene_templates_catalog.png")
    if brain_dir and os.path.isdir(brain_dir):
        os.system(f"cp {master_catalog_path} {brain_dir}/sticky_scene_templates_catalog.png")
        print(f"[✓] Synced Catalog to Artifact Directory: {brain_dir}/sticky_scene_templates_catalog.png")
    print(f"[✓] Synced Catalog to Vault: {user_vault}/sticky_scene_templates_catalog.png")


if __name__ == "__main__":
    main()
