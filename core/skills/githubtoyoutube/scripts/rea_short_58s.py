#!/usr/bin/env python3
"""
🎬 REA (morluto/rea) - 58-SECOND HIGH-RETENTION CARTOON SHORT (VERTICAL 9:16)
Official Repository Showcase: https://github.com/morluto/rea
- 100% Pure Cartoon Action Animation via PyCairo & FFmpeg NVENC
- High-Contrast Inversion: Architectural Cream Loft (#F5EBE1) + Dark Matte Stickman (#18191C)
- Rubber-Hose Kinematics, expressive mouth shapes, eye blinks, bouncy limbs
- Real GitHub Screenshot Integration & Clean-Room Code Recreation Visuals
- High-luminance Matrix Green (#00FF66) FLOWORKOS.COM chest branding & HUD
- Dual Call-To-Action (CTA) Outro: GitHub Star + Flowork OS Sovereign Platform
"""

import os
import sys
import math
import subprocess
import cairo
import numpy as np

# Canvas Setup (Vertical 9:16)
W, H = 1080, 1920
FPS = 30
DURATION = 58.0
TOTAL_FRAMES = int(DURATION * FPS)
FLOOR_Y = 1460

OUT_DIR = "/opt/floworkos/documents/videos/rea-short"
USER_OUT_DIR = os.path.expanduser("~/Documents/videos/rea-short")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(USER_OUT_DIR, exist_ok=True)

OUT_MP4 = os.path.join(OUT_DIR, "REA_CARTOON_SHORT_58S.mp4")
CONTACT_SHEET_PNG = os.path.join(OUT_DIR, "REA_CARTOON_SHORT_58S_contact_sheet.png")
AUDIO_WAV = "/tmp/rea_final_audio.wav"
REPO_PAGE_IMG = os.path.join(OUT_DIR, "github_repo_page.png")

REPO_PAGE_SURF = None
if os.path.exists(REPO_PAGE_IMG):
    try:
        REPO_PAGE_SURF = cairo.ImageSurface.create_from_png(REPO_PAGE_IMG)
    except Exception as e:
        print(f"Warning: Could not load repo image: {e}")

# ==============================================================================
# VECTOR SHAPES & HELPERS
# ==============================================================================

def draw_star(ctx, cx, cy, r_outer=18, r_inner=8, color=(1.0, 0.85, 0.0)):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.set_source_rgb(*color)
    ctx.new_sub_path()
    for i in range(10):
        ang = -math.pi/2 + i * (math.pi / 5)
        r = r_outer if i % 2 == 0 else r_inner
        x = r * math.cos(ang)
        y = r * math.sin(ang)
        if i == 0:
            ctx.move_to(x, y)
        else:
            ctx.line_to(x, y)
    ctx.close_path()
    ctx.fill()
    ctx.restore()

def draw_wall_and_floor(ctx, t, cam_shake_x=0, cam_shake_y=0):
    ctx.save()
    ctx.translate(cam_shake_x, cam_shake_y)
    
    # 1. Non-white Architectural Cream Loft Background (#F5EBE1)
    pat = cairo.LinearGradient(0, 0, 0, H)
    pat.add_color_stop_rgb(0.0, 0.965, 0.925, 0.885)
    pat.add_color_stop_rgb(1.0, 0.915, 0.875, 0.825)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()
    
    # Subtle Blueprint Grid
    ctx.set_source_rgba(0.78, 0.72, 0.65, 0.25)
    ctx.set_line_width(2)
    step = 72
    for x in range(0, W + step, step):
        ctx.move_to(x, 0)
        ctx.line_to(x, FLOOR_Y)
    for y in range(0, FLOOR_Y + step, step):
        ctx.move_to(0, y)
        ctx.line_to(W, y)
    ctx.stroke()
    
    # Floor Base (Warm Hardwood Slate)
    floor_pat = cairo.LinearGradient(0, FLOOR_Y, 0, H)
    floor_pat.add_color_stop_rgb(0.0, 0.22, 0.24, 0.28)
    floor_pat.add_color_stop_rgb(1.0, 0.14, 0.15, 0.18)
    ctx.set_source(floor_pat)
    ctx.rectangle(0, FLOOR_Y, W, H - FLOOR_Y)
    ctx.fill()
    
    # Baseboard Divider Line
    ctx.set_source_rgb(0.10, 0.11, 0.13)
    ctx.set_line_width(8)
    ctx.move_to(0, FLOOR_Y)
    ctx.line_to(W, FLOOR_Y)
    ctx.stroke()
    
    # Subtle floor perspective planks
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.15)
    ctx.set_line_width(3)
    for px in range(-300, W + 600, 160):
        ctx.move_to(px, FLOOR_Y)
        ctx.line_to(px + 120, H)
    ctx.stroke()
    
    ctx.restore()

def draw_hud_header(ctx):
    # Top HUD Bar
    ctx.save()
    ctx.set_source_rgba(0.12, 0.13, 0.16, 0.88)
    ctx.rectangle(40, 40, W - 80, 80)
    ctx.fill()
    
    # Border
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.set_line_width(4)
    ctx.rectangle(40, 40, W - 80, 80)
    ctx.stroke()
    
    # Flowork OS Sovereign HUD Badge
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(32)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(65, 92)
    ctx.show_text("⚡ FLOWORK OS")
    
    # Right-hand Topic tag
    ctx.set_font_size(26)
    ctx.set_source_rgb(0.95, 0.95, 0.95)
    ctx.move_to(W - 460, 92)
    ctx.show_text("AGENT REVERSE ENGINEERING")
    ctx.restore()

def draw_center_hook_title(ctx, t):
    if t > 5.5:
        return
    ctx.save()
    scale = 1.0 + 0.06 * math.sin(t * 12)
    if t < 0.4:
        scale *= max(0.05, t / 0.4)
    
    cy = 430
    cx = W / 2
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    
    # Comic Banner Backdrop
    w_box, h_box = 960, 260
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.rectangle(-w_box/2 + 12, -h_box/2 + 12, w_box, h_box)
    ctx.fill()
    
    # Neon Amber Box
    ctx.set_source_rgb(1.0, 0.82, 0.0)
    ctx.rectangle(-w_box/2, -h_box/2, w_box, h_box)
    ctx.fill()
    
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.set_line_width(10)
    ctx.rectangle(-w_box/2, -h_box/2, w_box, h_box)
    ctx.stroke()
    
    # Red badge inside
    ctx.set_source_rgb(0.95, 0.2, 0.2)
    ctx.rectangle(-w_box/2 + 20, -h_box/2 + 20, w_box - 40, 70)
    ctx.fill()
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(44)
    ctx.set_source_rgb(1, 1, 1)
    ext = ctx.text_extents("NO SOURCE CODE? NO PROBLEM!")
    ctx.move_to(-ext.width/2, -h_box/2 + 70)
    ctx.show_text("NO SOURCE CODE? NO PROBLEM!")
    
    # Giant Hook Text
    ctx.set_font_size(58)
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    t1 = "REVERSE ENGINEER"
    t2 = "ANY APP IN SECONDS?! 🤯"
    ext1 = ctx.text_extents(t1)
    ext2 = ctx.text_extents(t2)
    ctx.move_to(-ext1.width/2, 40)
    ctx.show_text(t1)
    ctx.move_to(-ext2.width/2, 105)
    ctx.show_text(t2)
    
    # Comic burst stars
    draw_star(ctx, -w_box/2 - 15, -h_box/2, 28, 12, (1, 0.3, 0.1))
    draw_star(ctx, w_box/2 + 15, -h_box/2, 28, 12, (1, 0.3, 0.1))
    draw_star(ctx, 0, h_box/2 + 20, 24, 10, (1, 0.8, 0.0))
    ctx.restore()

def draw_subtitle_pill(ctx, text, y=1720):
    if not text:
        return
    ctx.save()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    font_size = 52
    ctx.set_font_size(font_size)
    ext = ctx.text_extents(text)
    
    pw = ext.width + 90
    ph = ext.height + 45
    px = (W - pw) / 2
    py = y - ext.height / 2 - 20
    
    # Outer dark shadow
    ctx.set_source_rgba(0, 0, 0, 0.85)
    ctx.rectangle(px - 6, py - 4, pw + 12, ph + 8)
    ctx.fill()
    
    # Neon Pill Background
    ctx.set_source_rgb(0.12, 0.13, 0.16)
    ctx.rectangle(px, py, pw, ph)
    ctx.fill()
    
    # Accent border
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.set_line_width(6)
    ctx.rectangle(px, py, pw, ph)
    ctx.stroke()
    
    # Punchy subtitle text (pure white with 14px black outline)
    tx = (W - ext.width) / 2
    ty = y + ext.height / 2 - 4
    
    # Outline stroke
    ctx.set_line_width(14)
    ctx.set_source_rgb(0, 0, 0)
    ctx.move_to(tx, ty)
    ctx.text_path(text)
    ctx.stroke()
    
    # Inner fill
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(tx, ty)
    ctx.show_text(text)
    ctx.restore()

# ==============================================================================
# MR. FLOW SOVEREIGN RUBBER-HOSE STICKMAN
# ==============================================================================

def draw_mr_flow(ctx, cx, cy, scale=1.0, state=None):
    if state is None:
        state = {}
    
    bounce = state.get("bounce", 0.0)
    eye_state = state.get("eyes", "normal") # normal, shocked, happy, wink
    mouth_state = state.get("mouth", "talk")  # talk, smile, ooh, frown
    blink = state.get("blink", False)
    left_arm = state.get("left_arm", "down")
    right_arm = state.get("right_arm", "down")
    has_cape = state.get("cape", False)
    t = state.get("t", 0.0)
    
    ctx.save()
    ctx.translate(cx, cy + bounce)
    ctx.scale(scale, scale)
    
    # Cape
    if has_cape:
        ctx.save()
        ctx.set_source_rgb(0.85, 0.15, 0.15)
        ctx.move_to(-40, -180)
        c_wave = math.sin(t * 12) * 25
        ctx.curve_to(-120 + c_wave, -100, -140 + c_wave, 20, -90 + c_wave, 120)
        ctx.line_to(-30, 80)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    
    # Shadow on floor
    shadow_w = 110 * scale
    shadow_h = 24 * scale
    ctx.save()
    ctx.set_source_rgba(0, 0, 0, 0.35)
    ctx.scale(1.0, shadow_h / shadow_w)
    ctx.arc(0, (230 - bounce) * (shadow_w / shadow_h), shadow_w, 0, 2*math.pi)
    ctx.fill()
    ctx.restore()
    
    # Dark Matte Body & Limbs Color (#18191C)
    body_col = (0.09, 0.10, 0.11)
    
    # Legs (Rubber-hose curved paths)
    ctx.set_source_rgb(*body_col)
    ctx.set_line_width(18)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    
    # Left Leg
    ctx.move_to(-28, 40)
    leg_l_curl = math.sin(t * 8) * 15
    ctx.curve_to(-40, 100, -50 + leg_l_curl, 160, -35, 210)
    ctx.stroke()
    # Left shoe
    ctx.set_source_rgb(0.08, 0.08, 0.08)
    ctx.rectangle(-55, 202, 38, 18); ctx.fill()
    
    # Right Leg
    ctx.set_source_rgb(*body_col)
    ctx.move_to(28, 40)
    leg_r_curl = -math.sin(t * 8) * 15
    ctx.curve_to(40, 100, 50 + leg_r_curl, 160, 35, 210)
    ctx.stroke()
    # Right shoe
    ctx.set_source_rgb(0.08, 0.08, 0.08)
    ctx.rectangle(18, 202, 38, 18); ctx.fill()
    
    # Torso (Pill Shape)
    ctx.set_source_rgb(*body_col)
    ctx.set_line_width(1)
    torso_y1 = -160
    torso_h = 190
    ctx.rectangle(-46, torso_y1, 92, torso_h)
    ctx.fill()
    ctx.arc(0, torso_y1, 46, math.pi, 0); ctx.fill()
    ctx.arc(0, torso_y1 + torso_h, 46, 0, math.pi); ctx.fill()
    
    # High-Luminance Matrix Green Chest Badge: "FLOWORKOS.COM"
    ctx.save()
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.set_line_width(4)
    ctx.rectangle(-40, -110, 80, 50)
    ctx.stroke()
    ctx.set_source_rgb(0.02, 0.20, 0.08)
    ctx.rectangle(-38, -108, 76, 46)
    ctx.fill()
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(11)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(-35, -88)
    ctx.show_text("FLOWORK")
    ctx.move_to(-28, -72)
    ctx.show_text("OS.COM")
    ctx.restore()
    
    # Left Arm
    ctx.set_source_rgb(*body_col)
    ctx.set_line_width(16)
    ctx.move_to(-42, -130)
    if left_arm == "shocked":
        ctx.curve_to(-120, -170, -130, -220, -90, -240)
    elif left_arm == "point_up":
        ctx.curve_to(-90, -160, -110, -240, -80, -290)
    elif left_arm == "cross":
        ctx.curve_to(-30, -100, 20, -90, 45, -110)
    elif left_arm == "wave":
        w_ang = math.sin(t * 14) * 35
        ctx.curve_to(-100, -170, -120 + w_ang, -220, -80 + w_ang, -260)
    else: # down / rest
        ctx.curve_to(-80, -70, -75, 0, -55, 30)
    ctx.stroke()
    # Left hand white glove
    ctx.set_source_rgb(1, 1, 1)
    ctx.arc(ctx.get_current_point()[0], ctx.get_current_point()[1], 15, 0, 2*math.pi)
    ctx.fill()
    ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(3); ctx.stroke()
    
    # Right Arm
    ctx.set_source_rgb(*body_col)
    ctx.set_line_width(16)
    ctx.move_to(42, -130)
    if right_arm == "point_right":
        ctx.curve_to(110, -140, 160, -150, 230, -140)
    elif right_arm == "point_up_right":
        ctx.curve_to(110, -170, 160, -240, 210, -290)
    elif right_arm == "hammer":
        h_ang = math.sin(t * 18) * 40
        ctx.curve_to(90, -160, 140 + h_ang, -210, 180 + h_ang, -180)
    elif right_arm == "shocked":
        ctx.curve_to(120, -170, 130, -220, 90, -240)
    elif right_arm == "wave":
        w_ang = -math.sin(t * 14) * 35
        ctx.curve_to(100, -170, 120 + w_ang, -220, 80 + w_ang, -260)
    else: # down / rest
        ctx.curve_to(80, -70, 75, 0, 55, 30)
    ctx.stroke()
    # Right hand glove
    ctx.set_source_rgb(1, 1, 1)
    hand_pt = ctx.get_current_point()
    ctx.arc(hand_pt[0], hand_pt[1], 15, 0, 2*math.pi)
    ctx.fill()
    ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(3); ctx.stroke()
    
    # Head (Dark Matte Circle)
    head_cy = -230
    head_r = 74
    ctx.set_source_rgb(*body_col)
    ctx.arc(0, head_cy, head_r, 0, 2*math.pi)
    ctx.fill()
    
    # Eyes & Pupils
    eye_dx = 24
    eye_cy = head_cy - 8
    eye_r = 20
    
    if blink:
        # Closed eyes lines
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_line_width(6)
        ctx.move_to(-eye_dx - 12, eye_cy)
        ctx.line_to(-eye_dx + 12, eye_cy)
        ctx.move_to(eye_dx - 12, eye_cy)
        ctx.line_to(eye_dx + 12, eye_cy)
        ctx.stroke()
    elif eye_state == "shocked":
        # Huge cartoon eyeballs
        for side in (-eye_dx, eye_dx):
            ctx.set_source_rgb(1, 1, 1)
            ctx.arc(side, eye_cy, eye_r * 1.35, 0, 2*math.pi)
            ctx.fill()
            ctx.set_source_rgb(0, 0, 0)
            ctx.arc(side, eye_cy, 6, 0, 2*math.pi)
            ctx.fill()
    else:
        # Normal expressive eyes
        for side in (-eye_dx, eye_dx):
            ctx.set_source_rgb(1, 1, 1)
            ctx.arc(side, eye_cy, eye_r, 0, 2*math.pi)
            ctx.fill()
            ctx.set_source_rgb(0.08, 0.08, 0.1)
            # Pupil tracks rightwards slightly
            ctx.arc(side + 3, eye_cy, 8, 0, 2*math.pi)
            ctx.fill()
            # Glint
            ctx.set_source_rgb(1, 1, 1)
            ctx.arc(side + 6, eye_cy - 3, 3, 0, 2*math.pi)
            ctx.fill()
            
    # Mouth
    ctx.save()
    ctx.set_source_rgb(1, 1, 1)
    if mouth_state == "talk":
        m_open = 8 + 6 * abs(math.sin(t * 16))
        ctx.arc(0, head_cy + 34, 18, 0, math.pi)
        ctx.set_line_width(m_open)
        ctx.stroke()
    elif mouth_state == "ooh":
        ctx.arc(0, head_cy + 35, 12, 0, 2*math.pi)
        ctx.fill()
        ctx.set_source_rgb(0.1, 0.1, 0.1)
        ctx.arc(0, head_cy + 35, 7, 0, 2*math.pi)
        ctx.fill()
    elif mouth_state == "frown":
        ctx.set_line_width(6)
        ctx.arc(0, head_cy + 45, 18, math.pi, 2*math.pi)
        ctx.stroke()
    else: # smile
        ctx.set_line_width(6)
        ctx.arc(0, head_cy + 30, 20, 0.15*math.pi, 0.85*math.pi)
        ctx.stroke()
    ctx.restore()
    
    ctx.restore()

# ==============================================================================
# PROPS & SCENE GRAPHICS
# ==============================================================================

def draw_locked_app_window(ctx, x, y, w, h, t):
    """Draws a target closed-source commercial app with big padlock"""
    ctx.save()
    ctx.translate(x, y)
    
    # Shadow
    ctx.set_source_rgba(0, 0, 0, 0.3)
    ctx.rectangle(12, 12, w, h); ctx.fill()
    
    # Window Frame
    ctx.set_source_rgb(0.15, 0.16, 0.20)
    ctx.rectangle(0, 0, w, h); ctx.fill()
    ctx.set_source_rgb(0.28, 0.30, 0.36)
    ctx.set_line_width(4); ctx.rectangle(0, 0, w, h); ctx.stroke()
    
    # Title Bar
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    ctx.rectangle(0, 0, w, 48); ctx.fill()
    
    # Window Dots
    for i, col in enumerate([(0.95, 0.3, 0.3), (0.95, 0.75, 0.2), (0.2, 0.85, 0.3)]):
        ctx.set_source_rgb(*col)
        ctx.arc(28 + i * 26, 24, 7, 0, 2*math.pi); ctx.fill()
        
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(20)
    ctx.set_source_rgb(0.9, 0.9, 0.9)
    ctx.move_to(130, 32)
    ctx.show_text("TARGET_PROPRIETARY_APP (CLOSED SOURCE)")
    
    # Content Area: UI wireframe
    ctx.set_source_rgb(0.20, 0.22, 0.26)
    ctx.rectangle(30, 75, 180, h - 110); ctx.fill()
    ctx.rectangle(230, 75, w - 260, 100); ctx.fill()
    ctx.rectangle(230, 195, w - 260, h - 230); ctx.fill()
    
    # Giant Locked Padlock
    lock_cx, lock_cy = w/2 + 40, h/2 + 20
    ctx.save()
    ctx.translate(lock_cx, lock_cy)
    
    # Padlock Shackle
    ctx.set_source_rgb(0.85, 0.75, 0.2)
    ctx.set_line_width(18)
    ctx.arc(0, -45, 45, math.pi, 0); ctx.stroke()
    
    # Padlock Body
    ctx.set_source_rgb(0.95, 0.75, 0.1)
    ctx.rectangle(-55, -45, 110, 95); ctx.fill()
    ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(6); ctx.rectangle(-55, -45, 110, 95); ctx.stroke()
    
    # Keyhole
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.arc(0, -10, 14, 0, 2*math.pi); ctx.fill()
    ctx.move_to(-8, -5); ctx.line_to(-12, 25); ctx.line_to(12, 25); ctx.line_to(8, -5); ctx.close_path(); ctx.fill()
    
    ctx.restore()
    ctx.restore()

def draw_cryptic_assembly_hell(ctx, x, y, w, h, t):
    """Draws mountains of unreadable assembly hex and decompile errors"""
    ctx.save()
    ctx.translate(x, y)
    
    # Dark Hacker Box
    ctx.set_source_rgb(0.08, 0.08, 0.10)
    ctx.rectangle(0, 0, w, h); ctx.fill()
    ctx.set_source_rgb(0.85, 0.2, 0.2); ctx.set_line_width(5); ctx.rectangle(0, 0, w, h); ctx.stroke()
    
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    
    hex_lines = [
        "0x7F 0x45 0x4C 0x46 0x02 0x01 0x01 0x00 ... [ELF64]",
        "00401020: 48 83 ec 28          sub    $0x28,%rsp",
        "00401024: 48 8d 05 d5 0f 00 00 lea    0xfd5(%rip),%rax",
        "0040102b: 48 89 05 0e 20 00 00 mov    %rax,0x200e(%rip)",
        "00401032: e8 c9 00 00 00       callq  <SUB_401100_OBFUSCATED>",
        "00401037: 85 c0                test   %eax,%eax",
        "00401039: 74 12                je     0x40104d <CRASH_FAIL>",
        "0040103b: b8 01 00 00 00       mov    $0x1,%eax",
        "00401040: 48 83 c4 28          add    $0x28,%rsp",
        "00401044: c3                   retq   ; CONTROL FLOW GRAPH CORRUPTED"
    ]
    
    # Hex lines scrolling / flickering
    ctx.set_source_rgb(0.9, 0.3, 0.3)
    for idx, line in enumerate(hex_lines):
        line_y = 50 + idx * 36
        if line_y < h - 40:
            ctx.move_to(25, line_y)
            ctx.show_text(line)
            
    # Huge Red Alert Banner across
    alert_flash = math.sin(t * 14) > 0
    if alert_flash:
        ctx.set_source_rgb(0.95, 0.1, 0.1)
        ctx.rectangle(20, h/2 - 60, w - 40, 110); ctx.fill()
        ctx.set_source_rgb(1, 1, 1)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(36)
        ctx.move_to(50, h/2 + 8)
        ctx.show_text("⚠️ GHIDRA: 40,000 OBFUSCATED STRINGS!")
    
    ctx.restore()

def draw_github_rea_card(ctx, x, y, w, h, t):
    """Draws the official morluto/rea GitHub showcase card with real screenshot & star burst"""
    ctx.save()
    ctx.translate(x, y)
    
    # Golden glow
    glow_pulse = 0.5 + 0.5 * math.sin(t * 10)
    ctx.set_source_rgba(1.0, 0.85, 0.0, 0.25 * glow_pulse)
    ctx.rectangle(-15, -15, w + 30, h + 30); ctx.fill()
    
    # Outer Card
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    ctx.rectangle(0, 0, w, h); ctx.fill()
    ctx.set_source_rgb(1.0, 0.80, 0.0); ctx.set_line_width(8); ctx.rectangle(0, 0, w, h); ctx.stroke()
    
    # Header bar
    ctx.set_source_rgb(0.16, 0.18, 0.22)
    ctx.rectangle(0, 0, w, 80); ctx.fill()
    
    # GitHub Octocat Logo icon
    ctx.set_source_rgb(1, 1, 1)
    ctx.arc(45, 40, 22, 0, 2*math.pi); ctx.fill()
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(36)
    ctx.set_source_rgb(0.35, 0.75, 1.0)
    ctx.move_to(85, 52)
    ctx.show_text("morluto / rea")
    
    # 470K Stars Golden Badge
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.rectangle(w - 280, 16, 255, 48); ctx.fill()
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.set_font_size(26)
    ctx.move_to(w - 265, 50)
    ctx.show_text("⭐ 470,296 STARS")
    
    # Embed real GitHub screenshot if available
    if REPO_PAGE_SURF:
        ctx.save()
        ctx.translate(20, 100)
        scale_img = (w - 40) / REPO_PAGE_SURF.get_width()
        ctx.scale(scale_img, scale_img)
        ctx.set_source_surface(REPO_PAGE_SURF, 0, 0)
        ctx.paint()
        ctx.restore()
    else:
        # Fallback card description
        ctx.set_source_rgb(0.9, 0.9, 0.9)
        ctx.set_font_size(28)
        ctx.move_to(30, 150)
        ctx.show_text("Reverse engineer anything with agents,")
        ctx.move_to(30, 190)
        ctx.show_text("from app behavior down to native binaries.")
        
    ctx.restore()

def draw_mcp_agent_bridge(ctx, x, y, w, h, t):
    """Draws AI Agent connecting to target binary via REA MCP server"""
    ctx.save()
    ctx.translate(x, y)
    
    # Terminal Frame
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.rectangle(0, 0, w, h); ctx.fill()
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(5); ctx.rectangle(0, 0, w, h); ctx.stroke()
    
    # Header
    ctx.set_source_rgb(0.14, 0.16, 0.20)
    ctx.rectangle(0, 0, w, 50); ctx.fill()
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(22)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(30, 34)
    ctx.show_text("$ npx rea-agents inspect --target ./app_binary")
    
    # Live MCP Inspection Feed
    lines = [
        "[+] REA MCP Server: Protocol v2 Connected to Claude Code & Flowork OS",
        "[*] Probing binary architecture: x86_64 ELF + Dynamic Linker",
        "[✓] Extracted 42 API Endpoints & Protobuf Schemas",
        "[✓] Recovered State Machine & Auth Handshake: SUCCESS",
        "[⚡] Generating Clean-Room TypeScript Implementation..."
    ]
    
    ctx.set_font_size(24)
    for idx, l in enumerate(lines):
        ctx.move_to(30, 100 + idx * 45)
        if "[✓]" in l or "[⚡]" in l:
            ctx.set_source_rgb(0.0, 1.0, 0.4)
        else:
            ctx.set_source_rgb(0.9, 0.9, 0.9)
        ctx.show_text(l)
        
    # Laser Scanning Line
    scan_y = 80 + int((t * 220) % (h - 100))
    ctx.set_source_rgba(0.0, 1.0, 0.8, 0.7)
    ctx.set_line_width(6)
    ctx.move_to(20, scan_y); ctx.line_to(w - 20, scan_y); ctx.stroke()
    
    ctx.restore()

def draw_clean_room_code_box(ctx, x, y, w, h, t):
    """Draws synthesized clean-room code with 100% test pass badge"""
    ctx.save()
    ctx.translate(x, y)
    
    # Modern Editor Box
    ctx.set_source_rgb(0.12, 0.13, 0.17)
    ctx.rectangle(0, 0, w, h); ctx.fill()
    ctx.set_source_rgb(0.4, 0.7, 1.0); ctx.set_line_width(6); ctx.rectangle(0, 0, w, h); ctx.stroke()
    
    # Header
    ctx.set_source_rgb(0.18, 0.20, 0.26)
    ctx.rectangle(0, 0, w, 55); ctx.fill()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(30, 38)
    ctx.show_text("recreated_feature.ts (100% Clean-Room)")
    
    # Synthesized Code Lines
    code_lines = [
        ("export class FeaturePipeline {", (0.9, 0.6, 1.0)),
        ("  async executeReplication(payload: SchemaPayload) {", (0.4, 0.8, 1.0)),
        ("    const handshake = await this.mcp.connect();", (0.9, 0.9, 0.9)),
        ("    return handshake.reconstructGraph(payload);", (0.9, 0.9, 0.9)),
        ("  }", (0.4, 0.8, 1.0)),
        ("}", (0.9, 0.6, 1.0)),
    ]
    
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26)
    for idx, (code_t, col) in enumerate(code_lines):
        ctx.set_source_rgb(*col)
        ctx.move_to(35, 110 + idx * 42)
        ctx.show_text(code_t)
        
    # Big Green Test Pass Stamp
    ctx.save()
    ctx.translate(w - 270, h - 90)
    ctx.set_source_rgb(0.0, 0.9, 0.3)
    ctx.rectangle(0, 0, 240, 60); ctx.fill()
    ctx.set_source_rgb(0.05, 0.2, 0.08)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.move_to(20, 40)
    ctx.show_text("✓ 42 TESTS PASS")
    ctx.restore()
    
    ctx.restore()

def draw_dual_cta_outro(ctx, t):
    """Draws mandatory prominent Dual Call-To-Action outro cards"""
    ctx.save()
    
    # Card 1: Top Card - GitHub Repo
    c1_w, c1_h = 920, 260
    c1_x = (W - c1_w) / 2
    c1_y = 380
    
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.rectangle(c1_x + 10, c1_y + 10, c1_w, c1_h); ctx.fill()
    
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.rectangle(c1_x, c1_y, c1_w, c1_h); ctx.fill()
    ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(8); ctx.rectangle(c1_x, c1_y, c1_w, c1_h); ctx.stroke()
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.set_font_size(44)
    t_c1 = "⭐ STAR ON GITHUB!"
    ext1 = ctx.text_extents(t_c1)
    ctx.move_to(c1_x + (c1_w - ext1.width)/2, c1_y + 75)
    ctx.show_text(t_c1)
    
    ctx.set_font_size(40)
    ctx.set_source_rgb(0.05, 0.1, 0.3)
    t_url1 = "github.com/morluto/rea"
    ext_url1 = ctx.text_extents(t_url1)
    ctx.move_to(c1_x + (c1_w - ext_url1.width)/2, c1_y + 145)
    ctx.show_text(t_url1)
    
    ctx.set_font_size(28)
    ctx.set_source_rgb(0.25, 0.25, 0.25)
    t_sub1 = "Over 470,000 Developers Already Starred!"
    ext_sub1 = ctx.text_extents(t_sub1)
    ctx.move_to(c1_x + (c1_w - ext_sub1.width)/2, c1_y + 205)
    ctx.show_text(t_sub1)
    
    # Card 2: Lower Card - Flowork OS
    c2_w, c2_h = 920, 260
    c2_x = (W - c2_w) / 2
    c2_y = 700
    
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.rectangle(c2_x + 10, c2_y + 10, c2_w, c2_h); ctx.fill()
    
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.rectangle(c2_x, c2_y, c2_w, c2_h); ctx.fill()
    ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(8); ctx.rectangle(c2_x, c2_y, c2_w, c2_h); ctx.stroke()
    
    ctx.set_source_rgb(0.02, 0.15, 0.05)
    ctx.set_font_size(44)
    t_c2 = "⚡ RUN SOVEREIGN AI AGENTS"
    ext2 = ctx.text_extents(t_c2)
    ctx.move_to(c2_x + (c2_w - ext2.width)/2, c2_y + 75)
    ctx.show_text(t_c2)
    
    ctx.set_font_size(48)
    ctx.set_source_rgb(0.0, 0.25, 0.08)
    t_url2 = "FLOWORKOS.COM"
    ext_url2 = ctx.text_extents(t_url2)
    ctx.move_to(c2_x + (c2_w - ext_url2.width)/2, c2_y + 148)
    ctx.show_text(t_url2)
    
    ctx.set_font_size(28)
    ctx.set_source_rgb(0.08, 0.25, 0.12)
    t_sub2 = "Linux Kernel + Direct Hardware AI Automation"
    ext_sub2 = ctx.text_extents(t_sub2)
    ctx.move_to(c2_x + (c2_w - ext_sub2.width)/2, c2_y + 205)
    ctx.show_text(t_sub2)
    
    ctx.restore()

# ==============================================================================
# MASTER RENDER ENGINE
# ==============================================================================

def render_58s_rea_cartoon():
    print(f"🎬 Starting REA 58-second master render: {TOTAL_FRAMES} frames @ {FPS} FPS...")
    
    ffmpeg_cmd = [
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
        "-cq", "19",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUT_MP4
    ]
    
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    
    contact_surfaces = []
    contact_interval = TOTAL_FRAMES // 12
    
    for f in range(TOTAL_FRAMES):
        t = f / FPS
        
        # Camera shake trigger on beat hits
        cam_shake_x, cam_shake_y = 0, 0
        if (39.5 <= t <= 40.5) or (0.0 <= t <= 0.4):
            shake_amp = 8 * math.exp(-(t % 0.5) * 6)
            cam_shake_x = math.sin(t * 80) * shake_amp
            cam_shake_y = math.cos(t * 90) * shake_amp
            
        draw_wall_and_floor(ctx, t, cam_shake_x, cam_shake_y)
        draw_hud_header(ctx)
        
        # Subtitle selection
        sub_text = ""
        if 0.0 <= t < 2.8:
            sub_text = "REVERSE ENGINEER ANY APP IN SECONDS?!"
        elif 2.8 <= t < 5.5:
            sub_text = "IN UNDER 30 SECONDS!"
        elif 5.5 <= t < 8.8:
            sub_text = "NORMALLY: DAYS OF CRYPTIC ASSEMBLY!"
        elif 8.8 <= t < 12.0:
            sub_text = "WEEPING INSIDE GHIDRA & HEX CODE!"
        elif 12.0 <= t < 16.5:
            sub_text = "ENTER REA: THE TRENDING MONSTER!"
        elif 16.5 <= t < 21.0:
            sub_text = "⭐ 470,000+ GITHUB STARS!"
        elif 21.0 <= t < 26.5:
            sub_text = "CONNECTS AI AGENTS VIA MCP!"
        elif 26.5 <= t < 33.0:
            sub_text = "INSPECTS APPS & DECOMPILES BINARIES!"
        elif 33.0 <= t < 40.0:
            sub_text = "EXTRACTS SCHEMAS & FULL ARCHITECTURE!"
        elif 40.0 <= t < 44.0:
            sub_text = "NO LEAKED SOURCE CODE NEEDED!"
        elif 44.0 <= t < 48.0:
            sub_text = "CLEAN-ROOM CODE WITH TESTS IN MINUTES!"
        elif 48.0 <= t < 53.0:
            sub_text = "⭐ STAR REPO: github.com/morluto/rea"
        elif 53.0 <= t <= 58.0:
            sub_text = "⚡ BUILD AGENTS ON FLOWORKOS.COM"

        # Scene Sequencing
        if t < 5.5:
            # SCENE 1: Impossible Hook
            draw_center_hook_title(ctx, t)
            draw_locked_app_window(ctx, 80, 520, 920, 680, t)
            
            stick_state = {
                "bounce": math.sin(t * 12) * 18,
                "eyes": "shocked",
                "mouth": "ooh",
                "left_arm": "shocked",
                "right_arm": "point_up_right",
                "t": t
            }
            draw_mr_flow(ctx, 320, FLOOR_Y - 140, scale=1.1, state=stick_state)
            
        elif 5.5 <= t < 12.0:
            # SCENE 2: The Agony of Ghidra & Assembly Hell
            draw_cryptic_assembly_hell(ctx, 80, 240, 920, 780, t)
            
            stick_state = {
                "bounce": math.sin(t * 10) * 14,
                "eyes": "shocked",
                "mouth": "frown",
                "left_arm": "shocked",
                "right_arm": "shocked",
                "t": t
            }
            draw_mr_flow(ctx, 540, FLOOR_Y - 160, scale=1.15, state=stick_state)
            
        elif 12.0 <= t < 21.0:
            # SCENE 3: The Massive Viral Reveal (morluto/rea 470k stars)
            draw_github_rea_card(ctx, 70, 220, 940, 800, t)
            
            # Star burst around
            for i in range(8):
                ang = i * (math.pi / 4) + t * 2
                dist = 420 + 40 * math.sin(t * 6 + i)
                sx = 540 + dist * math.cos(ang)
                sy = 620 + dist * math.sin(ang)
                if 40 < sx < W - 40 and 40 < sy < FLOOR_Y:
                    draw_star(ctx, sx, sy, 22, 10, (1.0, 0.85, 0.0))
                    
            stick_state = {
                "bounce": math.sin(t * 14) * 20,
                "eyes": "happy",
                "mouth": "smile",
                "left_arm": "point_up",
                "right_arm": "point_up_right",
                "cape": True,
                "t": t
            }
            draw_mr_flow(ctx, 860, FLOOR_Y - 150, scale=1.1, state=stick_state)
            
        elif 21.0 <= t < 33.0:
            # SCENE 4: Core Agentic Mechanism (MCP Inspection)
            draw_mcp_agent_bridge(ctx, 80, 260, 920, 740, t)
            
            stick_state = {
                "bounce": math.sin(t * 10) * 12,
                "eyes": "normal",
                "mouth": "talk",
                "left_arm": "cross",
                "right_arm": "point_right",
                "t": t
            }
            draw_mr_flow(ctx, 280, FLOOR_Y - 150, scale=1.1, state=stick_state)
            
        elif 33.0 <= t < 48.0:
            # SCENE 5: Clean-Room Code Recreation & Tests Pass
            draw_clean_room_code_box(ctx, 80, 260, 920, 760, t)
            
            # Comic sparks & anvil strike at t=39.5
            if 39.5 <= t <= 43.0:
                for sp in range(6):
                    sp_x = 760 + math.sin(t * 20 + sp) * 90
                    sp_y = 700 + math.cos(t * 20 + sp) * 90
                    draw_star(ctx, sp_x, sp_y, 16, 7, (1, 0.9, 0.2))
                    
            stick_state = {
                "bounce": math.sin(t * 16) * 24,
                "eyes": "happy",
                "mouth": "smile",
                "left_arm": "wave",
                "right_arm": "wave",
                "t": t
            }
            draw_mr_flow(ctx, 840, FLOOR_Y - 150, scale=1.15, state=stick_state)
            
        else:
            # SCENE 6: Dual Outro Call-To-Action (t >= 48.0)
            draw_dual_cta_outro(ctx, t)
            
            stick_state = {
                "bounce": math.sin(t * 12) * 16,
                "eyes": "normal",
                "mouth": "smile",
                "left_arm": "wave",
                "right_arm": "point_up_right",
                "cape": True,
                "t": t
            }
            draw_mr_flow(ctx, 540, FLOOR_Y - 150, scale=1.15, state=stick_state)

        # Subtitle Pill Overlay
        draw_subtitle_pill(ctx, sub_text, y=1720)
        
        # Flush surface to pipe
        surface.flush()
        raw_data = surface.get_data()
        proc.stdin.write(raw_data)
        
        # Save snapshot for contact sheet
        if f % contact_interval == 0 and len(contact_surfaces) < 12:
            snap_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            s_ctx = cairo.Context(snap_surf)
            s_ctx.set_source_surface(surface, 0, 0)
            s_ctx.paint()
            contact_surfaces.append(snap_surf)
            
        if f % 150 == 0:
            print(f"Frame {f}/{TOTAL_FRAMES} rendered ({t:.1f}s / {DURATION:.1f}s)")
            
    proc.stdin.close()
    proc.wait()
    print("✓ Video stream successfully written via h264_nvenc!")
    
    # Generate 12-tile Contact Sheet
    print("🎨 Generating 12-tile contact sheet...")
    cs_w, cs_h = 1920, 1080
    cs_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, cs_w, cs_h)
    cs_ctx = cairo.Context(cs_surface)
    cs_ctx.set_source_rgb(0.12, 0.13, 0.16); cs_ctx.paint()
    
    thumb_w, thumb_h = int(cs_w / 4), int(cs_h / 3)
    for idx, snap in enumerate(contact_surfaces[:12]):
        col = idx % 4
        row = idx // 4
        x = col * thumb_w
        y = row * thumb_h
        
        cs_ctx.save()
        cs_ctx.translate(x, y)
        cs_ctx.scale(thumb_w / W, thumb_h / H)
        cs_ctx.set_source_surface(snap, 0, 0)
        cs_ctx.paint()
        cs_ctx.restore()
        
        cs_ctx.set_source_rgb(0.0, 1.0, 0.4)
        cs_ctx.set_line_width(4)
        cs_ctx.rectangle(x, y, thumb_w, thumb_h); cs_ctx.stroke()
        
        cs_ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cs_ctx.set_font_size(36)
        cs_ctx.set_source_rgb(1, 1, 1)
        cs_ctx.move_to(x + 25, y + 50)
        cs_ctx.show_text(f"t = {idx * (DURATION / 12):.1f}s")
        
    cs_surface.write_to_png(CONTACT_SHEET_PNG)
    print(f"✓ Contact sheet saved to {CONTACT_SHEET_PNG}!")
    
    # Dual Mirroring
    subprocess.run(["cp", "-f", OUT_MP4, USER_OUT_DIR], check=True)
    subprocess.run(["cp", "-f", CONTACT_SHEET_PNG, USER_OUT_DIR], check=True)
    print(f"✓ Mirrored deliverables to {USER_OUT_DIR}!")

if __name__ == "__main__":
    render_58s_rea_cartoon()
