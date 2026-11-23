#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU UNLOCK (Zagitta/gpu-unlock) - High-Retention Cartoon Short (56.83s, 9:16 Vertical, 60fps)
Engineered for Flowork OS / githubtoyoutube skill.
Full NVENC Hardware Accelerated PyCairo procedural animation.
"""

import os
import sys
import math
import time
import subprocess
import cairo
import numpy as np
import wave

# Resolution & Timing
W, H = 1080, 1920
FPS = 30
DURATION = 56.832
TOTAL_FRAMES = int(DURATION * FPS)

FLOWORK_GREEN = (0.0, 1.0, 0.4)
FLOWORK_DARK = (0.07, 0.08, 0.11)
FLOWORK_TEXT = (0.95, 0.96, 0.98)

# Output Paths
OUT_DIR = "/opt/floworkos/documents/videos/gpu-unlock-short"
USER_OUT_DIR = os.path.expanduser("~/Documents/videos/gpu-unlock-short")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(USER_OUT_DIR, exist_ok=True)

OUT_MP4 = os.path.join(OUT_DIR, "GPU_UNLOCK_CARTOON_SHORT_58S.mp4")
CONTACT_SHEET_PNG = os.path.join(OUT_DIR, "GPU_UNLOCK_CARTOON_SHORT_58S_contact_sheet.png")
AUDIO_WAV = os.path.join(OUT_DIR, "gpu_unlock_audio_mastered.wav")
REPO_PAGE_IMG = os.path.join(OUT_DIR, "gpu_unlock_repo_page.png")

# Load Assets
REPO_SURF = None
if os.path.exists(REPO_PAGE_IMG):
    try:
        REPO_SURF = cairo.ImageSurface.create_from_png(REPO_PAGE_IMG)
        print(f"Loaded repo screenshot: {REPO_SURF.get_width()}x{REPO_SURF.get_height()}")
    except Exception as e:
        print(f"Warning loading repo screenshot: {e}")

print(f"Animation Target: {TOTAL_FRAMES} frames ({DURATION:.2f}s) @ {FPS}fps")

# -------------------------------------------------------------
# GEOMETRY & VISUAL HELPERS
# -------------------------------------------------------------
def draw_rounded_rect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()

def draw_star(ctx, cx, cy, r_outer, r_inner, points=5):
    for i in range(points * 2):
        ang = -math.pi/2 + i * (math.pi / points)
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(ang)
        y = cy + r * math.sin(ang)
        if i == 0:
            ctx.move_to(x, y)
        else:
            ctx.line_to(x, y)
    ctx.close_path()

def draw_comic_sparks(ctx, cx, cy, scale=1.0, color=(1.0, 0.85, 0.0)):
    ctx.save()
    ctx.set_source_rgb(*color)
    ctx.set_line_width(4 * scale)
    for i in range(8):
        ang = i * (math.pi / 4)
        x1 = cx + math.cos(ang) * (20 * scale)
        y1 = cy + math.sin(ang) * (20 * scale)
        x2 = cx + math.cos(ang) * (45 * scale)
        y2 = cy + math.sin(ang) * (45 * scale)
        ctx.move_to(x1, y1)
        ctx.line_to(x2, y2)
        ctx.stroke()
        draw_star(ctx, x2, y2, 8 * scale, 3 * scale, 4)
        ctx.fill()
    ctx.restore()

def draw_branding_badge(ctx):
    """Mandatory stacked FLOWORKOS over .COM in Matrix green on black pill badge."""
    ctx.save()
    bx, by, bw, bh = 60, 60, 220, 78
    draw_rounded_rect(ctx, bx, by, bw, bh, 20)
    ctx.set_source_rgba(0.05, 0.06, 0.08, 0.92)
    ctx.fill_preserve()
    ctx.set_line_width(2.5)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.stroke()
    
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(bx + 26, by + 34)
    ctx.show_text("FLOWORKOS")
    
    ctx.set_font_size(18)
    ctx.set_source_rgb(0.85, 0.90, 0.95)
    ctx.move_to(bx + 76, by + 62)
    ctx.show_text(".COM")
    ctx.restore()

def draw_wall_and_floor(ctx, t, theme="warm_kraft"):
    """Non-white high retention procedural backgrounds."""
    ctx.save()
    if theme == "warm_kraft":
        ctx.set_source_rgb(0.937, 0.910, 0.863) # #EFE8DC
        ctx.paint()
        # Floor line
        ctx.set_source_rgb(0.88, 0.84, 0.78)
        ctx.rectangle(0, 1380, W, H - 1380)
        ctx.fill()
        ctx.set_source_rgb(0.40, 0.35, 0.30)
        ctx.set_line_width(4)
        ctx.move_to(0, 1380)
        ctx.line_to(W, 1380)
        ctx.stroke()
        # Subtle technical dots
        ctx.set_source_rgba(0.5, 0.45, 0.40, 0.15)
        for gx in range(40, W, 80):
            for gy in range(40, 1350, 80):
                ctx.arc(gx, gy, 2, 0, 2*math.pi)
                ctx.fill()
    elif theme == "corporate_dark":
        # Corporate slate with gold tint
        ctx.set_source_rgb(0.12, 0.14, 0.18)
        ctx.paint()
        ctx.set_source_rgb(0.08, 0.09, 0.12)
        ctx.rectangle(0, 1380, W, H - 1380)
        ctx.fill()
        ctx.set_source_rgb(0.85, 0.70, 0.20) # Gold floor beam
        ctx.set_line_width(4)
        ctx.move_to(0, 1380)
        ctx.line_to(W, 1380)
        ctx.stroke()
    elif theme == "sage_mint":
        # Sage Mint #D8E8E0
        ctx.set_source_rgb(0.847, 0.910, 0.878)
        ctx.paint()
        ctx.set_source_rgb(0.76, 0.84, 0.80)
        ctx.rectangle(0, 1380, W, H - 1380)
        ctx.fill()
        ctx.set_source_rgb(0.20, 0.35, 0.28)
        ctx.set_line_width(4)
        ctx.move_to(0, 1380)
        ctx.line_to(W, 1380)
        ctx.stroke()
    elif theme == "cyber_slate":
        # Cyber Dark Slate #151820
        ctx.set_source_rgb(0.09, 0.10, 0.14)
        ctx.paint()
        ctx.set_source_rgb(0.06, 0.07, 0.10)
        ctx.rectangle(0, 1380, W, H - 1380)
        ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4) # Matrix green floor beam
        ctx.set_line_width(4)
        ctx.move_to(0, 1380)
        ctx.line_to(W, 1380)
        ctx.stroke()
        # Matrix grid perspective lines
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.08)
        ctx.set_line_width(1.5)
        for gx in range(0, W + 100, 120):
            ctx.move_to(gx, 1380)
            ctx.line_to(W/2 + (gx - W/2)*2.2, H)
            ctx.stroke()
    ctx.restore()

# -------------------------------------------------------------
# SPECIALIZED VISUAL COMPONENTS (GPU UNLOCK PIPELINE)
# -------------------------------------------------------------
def draw_rtx_gpu(ctx, cx, cy, scale=1.0, is_locked=True, is_spinning=True, t=0.0, speed_mult=1.0):
    """Draws a detailed NVIDIA GeForce RTX graphics card with dual spinning fans and chains."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    
    gw, gh = 520, 260
    gx, gy = -gw/2, -gh/2
    
    # 1. Backplate / Shroud
    draw_rounded_rect(ctx, gx, gy, gw, gh, 24)
    ctx.set_source_rgb(0.12, 0.13, 0.16) # Matte carbon body
    ctx.fill_preserve()
    ctx.set_line_width(6)
    ctx.set_source_rgb(0.24, 0.26, 0.32)
    ctx.stroke()
    
    # Brushed aluminum decorative bevels
    ctx.set_source_rgb(0.28, 0.30, 0.38)
    draw_rounded_rect(ctx, gx + 15, gy + 15, gw - 30, gh - 30, 16)
    ctx.set_line_width(3)
    ctx.stroke()
    
    # Heatsink fin slats (visible on sides)
    ctx.set_source_rgba(0.4, 0.45, 0.5, 0.35)
    ctx.set_line_width(2)
    for fx in range(int(gx + 40), int(gx + gw - 40), 12):
        ctx.move_to(fx, gy + 22)
        ctx.line_to(fx, gy + 50)
        ctx.stroke()
        ctx.move_to(fx, gy + gh - 50)
        ctx.line_to(fx, gy + gh - 22)
        ctx.stroke()
    
    # 2. Dual Axial Fans
    fan_radius = 85
    fan_centers = [(-130, 0), (130, 0)]
    rot_speed = t * 25.0 * speed_mult if is_spinning else 0.0
    
    for fx, fy in fan_centers:
        # Fan outer ring
        ctx.set_source_rgb(0.06, 0.07, 0.09)
        ctx.arc(fx, fy, fan_radius + 6, 0, 2*math.pi)
        ctx.fill()
        
        # Fan glowing intake ring
        if not is_locked:
            ctx.set_source_rgba(0.0, 1.0, 0.4, 0.35) # Cyan/green power glow
            ctx.set_line_width(6)
            ctx.arc(fx, fy, fan_radius + 3, 0, 2*math.pi)
            ctx.stroke()
        
        # Fan blades
        num_blades = 9
        for b in range(num_blades):
            ang = rot_speed + b * (2 * math.pi / num_blades)
            ctx.save()
            ctx.translate(fx, fy)
            ctx.rotate(ang)
            ctx.set_source_rgb(0.18, 0.20, 0.25)
            ctx.new_sub_path()
            ctx.move_to(18, 0)
            ctx.curve_to(45, -12, 70, -6, fan_radius, 0)
            ctx.curve_to(70, 18, 45, 12, 18, 6)
            ctx.close_path()
            ctx.fill_preserve()
            ctx.set_line_width(1.5)
            ctx.set_source_rgb(0.28, 0.32, 0.40)
            ctx.stroke()
            ctx.restore()
            
        # Center metallic motor hub
        ctx.set_source_rgb(0.10, 0.11, 0.14)
        ctx.arc(fx, fy, 26, 0, 2*math.pi)
        ctx.fill()
        ctx.set_source_rgb(0.76, 0.72, 0.0) if is_locked else ctx.set_source_rgb(0.0, 1.0, 0.4)
        ctx.arc(fx, fy, 14, 0, 2*math.pi)
        ctx.fill()
    
    # 3. Top GeForce RTX Illuminated Badge
    ctx.save()
    draw_rounded_rect(ctx, -140, gy - 20, 280, 36, 8)
    ctx.set_source_rgb(0.08, 0.09, 0.11)
    ctx.fill_preserve()
    ctx.set_line_width(2)
    ctx.set_source_rgb(0.46, 0.72, 0.0) # NVIDIA Green #76b900
    ctx.stroke()
    
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(18)
    ctx.set_source_rgb(0.46, 0.72, 0.0)
    ctx.move_to(-120, gy + 5)
    ctx.show_text("GEFORCE RTX™")
    
    ctx.set_font_size(14)
    ctx.set_source_rgb(0.9, 0.9, 0.9)
    ctx.move_to(35, gy + 4)
    ctx.show_text("AI TENSOR")
    ctx.restore()
    
    # 4. Golden PCIe Connector
    ctx.set_source_rgb(0.85, 0.70, 0.15)
    ctx.rectangle(-180, gh/2 - 4, 360, 12)
    ctx.fill()
    ctx.set_source_rgb(0.08, 0.08, 0.08)
    for px in range(-175, 175, 8):
        ctx.rectangle(px, gh/2 - 4, 4, 12)
        ctx.fill()
    
    # 5. LOCK OVERLAY (If is_locked)
    if is_locked:
        # Cross Chains
        ctx.save()
        ctx.set_source_rgba(0.20, 0.22, 0.26, 0.95)
        ctx.set_line_width(24)
        ctx.move_to(gx + 10, gy + 10)
        ctx.line_to(gx + gw - 10, gy + gh - 10)
        ctx.stroke()
        ctx.move_to(gx + 10, gy + gh - 10)
        ctx.line_to(gx + gw - 10, gy + 10)
        ctx.stroke()
        
        # Chain highlight rings
        ctx.set_source_rgb(0.45, 0.48, 0.55)
        ctx.set_line_width(4)
        for i in range(-5, 6):
            ctx.arc(i * 45, i * 22, 14, 0, 2*math.pi)
            ctx.stroke()
            ctx.arc(i * 45, -i * 22, 14, 0, 2*math.pi)
            ctx.stroke()
        
        # Heavy Padlock in Center
        lock_shake = math.sin(t * 35.0) * 4.0
        ctx.translate(lock_shake, 0)
        
        # Shackle
        ctx.set_source_rgb(0.55, 0.60, 0.68)
        ctx.set_line_width(18)
        ctx.arc(0, -45, 42, math.pi, 2*math.pi)
        ctx.stroke()
        
        # Lock Body
        draw_rounded_rect(ctx, -75, -45, 150, 120, 18)
        ctx.set_source_rgb(0.82, 0.65, 0.15) # Heavy brass
        ctx.fill_preserve()
        ctx.set_line_width(6)
        ctx.set_source_rgb(0.45, 0.35, 0.08)
        ctx.stroke()
        
        # Red Warning Banner on Lock
        draw_rounded_rect(ctx, -70, -20, 140, 42, 8)
        ctx.set_source_rgb(0.85, 0.15, 0.15)
        ctx.fill()
        
        ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(20)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.move_to(-60, 9)
        ctx.show_text("50% LOCKED")
        
        # Keyhole
        ctx.arc(0, 42, 9, 0, 2*math.pi)
        ctx.set_source_rgb(0.1, 0.1, 0.1)
        ctx.fill()
        ctx.rectangle(-4, 42, 8, 16)
        ctx.fill()
        ctx.restore()
    else:
        # UNLOCKED POWER AURA
        ctx.save()
        pulse = 0.8 + 0.2 * math.sin(t * 12.0)
        draw_comic_sparks(ctx, -gw/2 - 20, 0, scale=1.2 * pulse, color=(0.0, 1.0, 0.5))
        draw_comic_sparks(ctx, gw/2 + 20, 0, scale=1.2 * pulse, color=(0.0, 1.0, 0.5))
        draw_comic_sparks(ctx, 0, -gh/2 - 30, scale=1.4 * pulse, color=(1.0, 0.85, 0.0))
        
        # 100% UNLEASHED Green Stamp
        ctx.save()
        ctx.rotate(-0.12)
        draw_rounded_rect(ctx, -160, -35, 320, 70, 14)
        ctx.set_source_rgba(0.0, 0.8, 0.3, 0.90)
        ctx.fill_preserve()
        ctx.set_line_width(5)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.stroke()
        
        ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(26)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.move_to(-140, 10)
        ctx.show_text("⚡ 2X FULL SPEED ⚡")
        ctx.restore()
        ctx.restore()

    ctx.restore()

def draw_corporate_vault(ctx, cx, cy, scale=1.0, t=0.0):
    """Draws a massive corporate steel bank vault door with 0,000 tax stamp."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    
    # Outer vault frame
    draw_rounded_rect(ctx, -240, -220, 480, 440, 30)
    ctx.set_source_rgb(0.18, 0.20, 0.25)
    ctx.fill_preserve()
    ctx.set_line_width(8)
    ctx.set_source_rgb(0.85, 0.70, 0.20) # Golden vault rim
    ctx.stroke()
    
    # Circular heavy vault door
    ctx.set_source_rgb(0.24, 0.27, 0.34)
    ctx.arc(0, 0, 180, 0, 2*math.pi)
    ctx.fill_preserve()
    ctx.set_line_width(12)
    ctx.set_source_rgb(0.12, 0.14, 0.18)
    ctx.stroke()
    
    # Vault locking spokes
    num_spokes = 8
    rot = t * 0.5
    ctx.set_line_width(14)
    ctx.set_source_rgb(0.75, 0.60, 0.15)
    for s in range(num_spokes):
        ang = rot + s * (2 * math.pi / num_spokes)
        ctx.move_to(0, 0)
        ctx.line_to(math.cos(ang) * 165, math.sin(ang) * 165)
        ctx.stroke()
        draw_star(ctx, math.cos(ang) * 165, math.sin(ang) * 165, 12, 5, 5)
        ctx.fill()
        
    # Central vault lock wheel
    ctx.set_source_rgb(0.85, 0.70, 0.20)
    ctx.arc(0, 0, 70, 0, 2*math.pi)
    ctx.fill_preserve()
    ctx.set_line_width(8)
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.stroke()
    
    # Giant text
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgb(1.0, 0.2, 0.2)
    ctx.move_to(-180, -140)
    ctx.show_text("ENTERPRISE ONLY")
    
    ctx.set_font_size(36)
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.move_to(-145, 15)
    ctx.show_text("0,000")
    
    ctx.set_font_size(20)
    ctx.set_source_rgb(0.9, 0.9, 0.9)
    ctx.move_to(-110, 45)
    ctx.show_text("H100 / A100")
    
    # Subtitle pill
    draw_rounded_rect(ctx, -190, 140, 380, 50, 12)
    ctx.set_source_rgb(0.85, 0.15, 0.15)
    ctx.fill()
    ctx.set_font_size(18)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(-170, 172)
    ctx.show_text("CONSUMER CARDS THROTTLED")
    ctx.restore()

def draw_github_repo_card(ctx, cx, cy, scale=1.0, t=0.0):
    """Draws a modern GitHub repository card with live empirical screenshot."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    
    cw, ch = 720, 480
    draw_rounded_rect(ctx, -cw/2, -ch/2, cw, ch, 24)
    ctx.set_source_rgb(0.08, 0.09, 0.12) # GitHub Dark Canvas #0d1117
    ctx.fill_preserve()
    ctx.set_line_width(6)
    ctx.set_source_rgb(0.0, 1.0, 0.4) # Matrix green glowing border
    ctx.stroke()
    
    # Title bar
    ctx.rectangle(-cw/2, -ch/2, cw, 60)
    ctx.set_source_rgb(0.13, 0.15, 0.19)
    ctx.fill()
    
    # macOS window dots
    colors = [(1.0, 0.38, 0.35), (1.0, 0.75, 0.25), (0.18, 0.80, 0.44)]
    for idx, c in enumerate(colors):
        ctx.set_source_rgb(*c)
        ctx.arc(-cw/2 + 35 + idx * 26, -ch/2 + 30, 8, 0, 2*math.pi)
        ctx.fill()
        
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(22)
    ctx.set_source_rgb(0.9, 0.95, 1.0)
    ctx.move_to(-cw/2 + 130, -ch/2 + 38)
    ctx.show_text("github.com/Zagitta/gpu-unlock")
    
    # Repo screenshot or stylized inner mockup
    global REPO_SURF
    if REPO_SURF is not None:
        ctx.save()
        # Clip to inner rectangle
        draw_rounded_rect(ctx, -cw/2 + 20, -ch/2 + 75, cw - 40, ch - 95, 14)
        ctx.clip()
        
        sw = REPO_SURF.get_width()
        sh = REPO_SURF.get_height()
        target_w = cw - 40
        scale_img = target_w / sw
        ctx.translate(-cw/2 + 20, -ch/2 + 75)
        ctx.scale(scale_img, scale_img)
        ctx.set_source_surface(REPO_SURF, 0, 0)
        ctx.paint()
        ctx.restore()
    else:
        # Fallback stylized terminal card
        ctx.set_source_rgb(0.05, 0.06, 0.08)
        draw_rounded_rect(ctx, -cw/2 + 20, -ch/2 + 75, cw - 40, ch - 95, 14)
        ctx.fill()
        
        ctx.set_font_size(24)
        ctx.set_source_rgb(0.0, 1.0, 0.4)
        ctx.move_to(-cw/2 + 50, -ch/2 + 130)
        ctx.show_text("$ sudo insmod gpu_unlock.ko")
        
        ctx.set_source_rgb(0.8, 0.85, 0.95)
        ctx.move_to(-cw/2 + 50, -ch/2 + 180)
        ctx.show_text("[KERNEL] MMA register throttle bypassed!")
        
        ctx.set_source_rgb(1.0, 0.85, 0.0)
        ctx.move_to(-cw/2 + 50, -ch/2 + 230)
        ctx.show_text("[SUCCESS] 2X Tensor throughput active.")

    ctx.restore()

def draw_dyno_speedometer(ctx, cx, cy, label, val_now, val_max, unit, progress, boost_pct, t=0.0):
    """Draws an automotive dyno tachometer with sweeping needle and flame boost."""
    ctx.save()
    ctx.translate(cx, cy)
    
    # Outer gauge rim
    gr = 175
    draw_rounded_rect(ctx, -gr - 25, -gr - 25, (gr + 25)*2, (gr + 25)*2 + 60, 28)
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.fill_preserve()
    ctx.set_line_width(6)
    ctx.set_source_rgb(0.25, 0.30, 0.38)
    ctx.stroke()
    
    # Gauge arc background (-210 to +30 deg)
    start_ang = math.radians(150)
    end_ang = math.radians(390)
    
    ctx.set_line_width(26)
    ctx.set_source_rgb(0.16, 0.18, 0.22)
    ctx.arc(0, 0, gr - 20, start_ang, end_ang)
    ctx.stroke()
    
    # Active power arc
    cur_ang = start_ang + progress * (end_ang - start_ang)
    if progress > 0.01:
        # Green to fiery orange gradient arc
        ctx.set_source_rgb(0.0, 0.95, 0.45) if progress < 0.7 else ctx.set_source_rgb(1.0, 0.55, 0.0)
        ctx.arc(0, 0, gr - 20, start_ang, cur_ang)
        ctx.stroke()
        
    # Tick marks
    for i in range(11):
        tick_prog = i / 10.0
        tick_ang = start_ang + tick_prog * (end_ang - start_ang)
        x1 = math.cos(tick_ang) * (gr - 38)
        y1 = math.sin(tick_ang) * (gr - 38)
        x2 = math.cos(tick_ang) * (gr - 10)
        y2 = math.sin(tick_ang) * (gr - 10)
        ctx.set_line_width(4 if i % 2 == 0 else 2)
        ctx.set_source_rgb(0.8, 0.85, 0.9)
        ctx.move_to(x1, y1)
        ctx.line_to(x2, y2)
        ctx.stroke()
        
    # Needle
    needle_vib = math.sin(t * 40.0) * (0.03 * progress)
    eff_ang = cur_ang + needle_vib
    nx = math.cos(eff_ang) * (gr - 15)
    ny = math.sin(eff_ang) * (gr - 15)
    
    ctx.set_line_width(7)
    ctx.set_source_rgb(1.0, 0.25, 0.20) # Bright red needle
    ctx.move_to(0, 0)
    ctx.line_to(nx, ny)
    ctx.stroke()
    
    # Center hub
    ctx.set_source_rgb(0.3, 0.35, 0.42)
    ctx.arc(0, 0, 24, 0, 2*math.pi)
    ctx.fill_preserve()
    ctx.set_line_width(3)
    ctx.set_source_rgb(0.9, 0.95, 1.0)
    ctx.stroke()
    
    # Digital display
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgb(0.7, 0.75, 0.85)
    ctx.move_to(-gr + 15, -gr + 5)
    ctx.show_text(label)
    
    # Current value display
    ctx.set_font_size(38)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    val_str = f"{val_now:.0f} {unit}"
    ctx.move_to(-75, 110)
    ctx.show_text(val_str)
    
    # Giant comic boost badge
    if boost_pct:
        draw_rounded_rect(ctx, -110, 135, 220, 52, 14)
        ctx.set_source_rgb(0.0, 0.85, 0.35)
        ctx.fill_preserve()
        ctx.set_line_width(3)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.stroke()
        
        ctx.set_font_size(26)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.move_to(-95, 172)
        ctx.show_text(boost_pct)
        
    ctx.restore()

def draw_benchmark_bars(ctx, cx, cy, t=0.0):
    """Draws full benchmark comparison bars for RTX 3080, RTX 4090, and SDXL."""
    ctx.save()
    ctx.translate(cx, cy)
    
    bw, bh = 760, 480
    draw_rounded_rect(ctx, -bw/2, -bh/2, bw, bh, 24)
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.fill_preserve()
    ctx.set_line_width(6)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.stroke()
    
    # Title
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.move_to(-bw/2 + 40, -bh/2 + 50)
    ctx.show_text("EMPIRICAL BENCHMARK GAINS")
    
    # Metric 1: RTX 3080 FP16 TFLOPS
    y1 = -bh/2 + 115
    ctx.set_font_size(20)
    ctx.set_source_rgb(0.85, 0.90, 0.98)
    ctx.move_to(-bw/2 + 40, y1)
    ctx.show_text("RTX 3080 Tensor FP16: 65 -> 113 TFLOPS (+74%)")
    
    # Base Bar
    draw_rounded_rect(ctx, -bw/2 + 40, y1 + 12, 280, 32, 8)
    ctx.set_source_rgb(0.25, 0.28, 0.35)
    ctx.fill()
    # Unlocked Bar
    draw_rounded_rect(ctx, -bw/2 + 40, y1 + 12, 485, 32, 8)
    ctx.set_source_rgb(0.0, 0.85, 0.4)
    ctx.fill()
    
    # Metric 2: RTX 4090 FP16 TFLOPS
    y2 = -bh/2 + 220
    ctx.set_source_rgb(0.85, 0.90, 0.98)
    ctx.move_to(-bw/2 + 40, y2)
    ctx.show_text("RTX 4090 Tensor FP16: 165 -> 329 TFLOPS (+99% / 2X)")
    
    draw_rounded_rect(ctx, -bw/2 + 40, y2 + 12, 330, 32, 8)
    ctx.set_source_rgb(0.25, 0.28, 0.35)
    ctx.fill()
    draw_rounded_rect(ctx, -bw/2 + 40, y2 + 12, 660, 32, 8)
    ctx.set_source_rgb(0.0, 0.85, 0.4)
    ctx.fill()
    
    # Metric 3: SDXL Image Gen Time (Lower is better)
    y3 = -bh/2 + 325
    ctx.set_source_rgb(0.85, 0.90, 0.98)
    ctx.move_to(-bw/2 + 40, y3)
    ctx.show_text("SDXL 1024x1024: 8.2s -> 4.1s (50% Faster)")
    
    draw_rounded_rect(ctx, -bw/2 + 40, y3 + 12, 540, 32, 8)
    ctx.set_source_rgb(0.75, 0.25, 0.25) # Slow stock time
    ctx.fill()
    draw_rounded_rect(ctx, -bw/2 + 40, y3 + 12, 270, 32, 8)
    ctx.set_source_rgb(0.0, 0.85, 0.4) # Fast unlocked time
    ctx.fill()
    
    # Green Verification Stamp
    ctx.save()
    ctx.translate(bw/2 - 190, bh/2 - 55)
    draw_rounded_rect(ctx, -140, -25, 280, 50, 12)
    ctx.set_source_rgb(0.0, 0.65, 0.25)
    ctx.fill_preserve()
    ctx.set_line_width(3)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.stroke()
    ctx.set_font_size(18)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(-125, 8)
    ctx.show_text("✔ 100% BIT-IDENTICAL")
    ctx.restore()
    
    ctx.restore()

def draw_safe_kernel_shield(ctx, cx, cy, t=0.0):
    """Draws a heraldic Linux kernel safety shield with automated fallback badge."""
    ctx.save()
    ctx.translate(cx, cy)
    
    # Heraldic Shield Path
    ctx.new_sub_path()
    ctx.move_to(-140, -160)
    ctx.line_to(140, -160)
    ctx.curve_to(140, 40, 70, 140, 0, 180)
    ctx.curve_to(-70, 140, -140, 40, -140, -160)
    ctx.close_path()
    
    ctx.set_source_rgb(0.12, 0.14, 0.18)
    ctx.fill_preserve()
    ctx.set_line_width(10)
    ctx.set_source_rgb(0.85, 0.70, 0.20) # Gold heraldic border
    ctx.stroke()
    
    # Inner Linux Tux Penguin silhouette / emblem
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.arc(0, -50, 45, 0, 2*math.pi)
    ctx.fill()
    
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(-75, 40)
    ctx.show_text("LINUX KERNEL")
    
    ctx.set_font_size(18)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(-65, 80)
    ctx.show_text("AUTO FALLBACK")
    
    ctx.set_font_size(16)
    ctx.set_source_rgb(0.85, 0.85, 0.85)
    ctx.move_to(-60, 115)
    ctx.show_text("GPL-3.0 SAFE")
    
    # Radiating sparks
    pulse = 1.0 + 0.15 * math.sin(t * 10.0)
    draw_comic_sparks(ctx, 0, 0, scale=1.4 * pulse, color=(0.85, 0.70, 0.20))
    ctx.restore()

def draw_high_retention_subtitle(ctx, text, y_pos=1680):
    """Draws massive bold subtitles with black outline and neon yellow/white text."""
    if not text:
        return
    ctx.save()
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(36)
    
    # Measure text for background pill
    ext = ctx.text_extents(text)
    pw = ext.width + 60
    ph = ext.height + 34
    px = (W - pw) / 2
    py = y_pos - ext.height - 15
    
    # Background Pill
    draw_rounded_rect(ctx, px, py, pw, ph, 18)
    ctx.set_source_rgba(0.05, 0.06, 0.08, 0.92)
    ctx.fill_preserve()
    ctx.set_line_width(3.5)
    ctx.set_source_rgb(0.0, 1.0, 0.4) # Matrix green border
    ctx.stroke()
    
    # Text Outline
    tx = (W - ext.width) / 2
    ty = y_pos - 2
    ctx.move_to(tx, ty)
    ctx.text_path(text)
    ctx.set_line_width(8)
    ctx.set_source_rgb(0.0, 0.0, 0.0)
    ctx.stroke()
    
    # Text Fill (Bright Golden Yellow)
    ctx.move_to(tx, ty)
    ctx.set_source_rgb(1.0, 0.92, 0.15)
    ctx.show_text(text)
    ctx.restore()

# -------------------------------------------------------------
# HIGH-RETENTION CUES & SUBTITLE TIMINGS
# -------------------------------------------------------------
SUBTITLES = [
    (0.0, 3.8, "NVIDIA has been locking half your GPU's AI speed..."),
    (3.8, 7.5, "and an open-source tool just unlocked it completely!"),
    (7.5, 12.0, "If you run local LLMs or Stable Diffusion on RTX,"),
    (12.0, 16.5, "your tensor cores are throttled at half-speed."),
    (16.5, 21.5, "Why? So companies buy thirty-thousand dollar enterprise cards!"),
    (21.5, 25.5, "Meet GPU-Unlock on GitHub:"),
    (25.5, 30.5, "A lightweight Linux kernel module bypassing hardware limits."),
    (30.5, 35.5, "It removes MMA instruction caps with zero hardware risk."),
    (35.5, 40.5, "RTX 3080 jumps from 65 to 113 TFLOPS!"),
    (40.5, 45.5, "RTX 4090 reaches an insane 329 TFLOPS!"),
    (45.5, 50.5, "Image generation cut in half, bit-identical precision."),
    (50.5, 56.8, "GPL-3.0 open source. Link in comments below!"),
]

def get_subtitle_for_time(t):
    for start, end, text in SUBTITLES:
        if start <= t < end:
            return text
    return ""

# -------------------------------------------------------------
# SCENE ORCHESTRATION & FRAME RENDERING
# -------------------------------------------------------------

def fill_bright_background(ctx, width, height, theme='kraft', t=0.0):
    theme_map = {
        'kraft': 'warm_kraft',
        'cream': 'corporate_dark',
        'mint': 'sage_mint',
        'gray': 'cyber_slate'
    }
    mapped = theme_map.get(theme, 'warm_kraft')
    draw_wall_and_floor(ctx, t=t, theme=mapped)

def draw_branding_header(ctx, t=0.0):
    draw_branding_badge(ctx)

def draw_speech_bubble(ctx, x, y, w, h, text, tail_pos="bl"):
    """Draw comic speech bubble with pointer tail"""
    ctx.save()
    # Shadow
    draw_rounded_rect(ctx, x + 6, y + 6, w, h, 20)
    ctx.set_source_rgba(0, 0, 0, 0.15)
    ctx.fill()
    
    # Bubble Body
    draw_rounded_rect(ctx, x, y, w, h, 20)
    ctx.set_source_rgb(0.98, 0.98, 0.95)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.1, 0.1, 0.15)
    ctx.set_line_width(4)
    ctx.stroke()
    
    # Pointer tail
    ctx.new_path()
    if 'b' in tail_pos:
        tail_x = x + w * (0.25 if 'l' in tail_pos else 0.75)
        ctx.move_to(tail_x - 18, y + h - 2)
        ctx.line_to(tail_x, y + h + 24)
        ctx.line_to(tail_x + 18, y + h - 2)
    elif 't' in tail_pos:
        tail_x = x + w * (0.25 if 'l' in tail_pos else 0.75)
        ctx.move_to(tail_x - 18, y + 2)
        ctx.line_to(tail_x, y - 24)
        ctx.line_to(tail_x + 18, y + 2)
    ctx.close_path()
    ctx.set_source_rgb(0.98, 0.98, 0.95)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.1, 0.1, 0.15)
    ctx.set_line_width(4)
    ctx.stroke()
    
    # Text
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ext = ctx.text_extents(text)
    ctx.move_to(x + (w - ext.width) / 2 - ext.x_bearing, y + (h + ext.height) / 2)
    ctx.set_source_rgb(0.1, 0.1, 0.15)
    ctx.show_text(text)
    ctx.restore()


def render_frame_to_surface(ctx, frame_idx, total_frames, t):
    # Determine Current Scene and Background Palette
    # Palette 0: Warm Kraft (#EFE8DC) - Act 1 (0 to 10s)
    # Palette 1: Architectural Cream (#F5EBE1) - Act 2 (10 to 22s)
    # Palette 2: Sage Mint (#D8E8E0) - Act 3 (22 to 36s)
    # Palette 3: High-Tech Cyber Gray (#E5E9F0) - Act 4 (36 to 48s)
    # Palette 4: Sage Mint (#D8E8E0) - Act 5 (48 to 57s)
    
    if t < 10.0:
        theme = 'kraft'
        scene = 1
    elif t < 22.0:
        theme = 'cream'
        scene = 2
    elif t < 36.0:
        theme = 'mint'
        scene = 3
    elif t < 48.0:
        theme = 'gray'
        scene = 4
    else:
        theme = 'mint'
        scene = 5
        
    # 1. Fill Dynamic Bright Non-White Canvas
    fill_bright_background(ctx, W, H, theme=theme, t=t)
    
    # 2. Draw Top Branding Header (FLOWORKOS.COM)
    draw_branding_header(ctx, t=t)
    
    # 3. Scene Content Dispatch
    stickman = Stickman(W/2, 1380)
    
    if scene == 1:
        # ACT 1: The Great GPU Throttle (0 - 10s)
        # Giant Locked RTX GPU floating in upper area
        gpu_y = 520 + math.sin(t * 3.0) * 15.0
        draw_rtx_gpu(ctx, W/2, gpu_y, scale=1.35, is_locked=True, is_spinning=True, t=t, speed_mult=0.5)
        
        # Stickman pointing up in shock / investigating
        arm_wave = math.sin(t * 8.0) * 0.25
        stickman.draw(ctx, pose="shock", t=t, eye_look="up")
        draw_speech_bubble(ctx, W/2 + 230, 1150, 260, 95, "50% THROTTLED?!", tail_pos="bl")
        
    elif scene == 2:
        # ACT 2: The 0,000 Corporate Paywall (10 - 22s)
        # Corporate Vault Door with 0,000 Stamp
        vault_y = 520
        draw_corporate_vault(ctx, W/2, vault_y, scale=1.15, t=t)
        
        # Stickman scratching head / holding money
        stickman.draw(ctx, pose="thinking", t=t, eye_look="up")
        draw_speech_bubble(ctx, W/2 - 250, 1120, 280, 95, "0K FOR FULL SPEED?", tail_pos="br")
        
    elif scene == 3:
        # ACT 3: The Open-Source Bypass (22 - 36s)
        # GitHub Repo Card with Live Screenshot
        card_y = 540 + math.sin(t * 2.5) * 10.0
        draw_github_repo_card(ctx, W/2, card_y, scale=1.18, t=t)
        
        # Stickman typing on keyboard / celebrating with thumbs up
        stickman.draw(ctx, pose="typing", t=t, eye_look="up")
        draw_speech_bubble(ctx, W/2 + 240, 1150, 260, 95, "GPU-UNLOCK FOUND!", tail_pos="bl")
        
    elif scene == 4:
        # ACT 4: Empirical Benchmarks & 2X Dyno Boost (36 - 48s)
        if t < 42.5:
            # Dyno Speedometers side by side
            prog = min(1.0, (t - 36.0) / 4.0)
            val = 65.0 + prog * 48.0
            draw_dyno_speedometer(ctx, W/2, 530, "RTX 3080 TENSOR SPEED", val, 120, "TFLOPS", prog, "+74% BOOST", t=t)
        else:
            # Comprehensive Benchmark Comparison Bars
            draw_benchmark_bars(ctx, W/2, 540, t=t)
            
        # Stickman running / flexing with 2x power
        stickman.draw(ctx, pose="flex", t=t, eye_look="straight")
        draw_comic_sparks(ctx, W/2 - 200, 1300, scale=1.2, color=(0.0, 1.0, 0.4))
        draw_comic_sparks(ctx, W/2 + 200, 1300, scale=1.2, color=(0.0, 1.0, 0.4))
        
    else:
        # ACT 5: Linux Kernel Module & Call to Action (48 - 57s)
        # Unlocked glowing RTX GPU floating proudly
        gpu_y = 480
        draw_rtx_gpu(ctx, W/2, gpu_y, scale=1.25, is_locked=False, is_spinning=True, t=t, speed_mult=2.2)
        
        # Heraldic Kernel Shield
        draw_safe_kernel_shield(ctx, W/2 + 240, 850, t=t)
        
        # Stickman pointing down to comments / call to action
        stickman.draw(ctx, pose="point_down", t=t, eye_look="down")
        draw_speech_bubble(ctx, W/2 - 240, 1140, 290, 100, "STAR THE REPO! ⭐", tail_pos="br")
        
    # 4. Render Dynamic Subtitle Pill
    sub_text = get_subtitle_for_time(t)
    draw_high_retention_subtitle(ctx, sub_text, y_pos=1720)

# -------------------------------------------------------------
# STICKMAN ACTOR WRAPPER
# -------------------------------------------------------------
import sys
sys.path.insert(0, '/opt/floworkos/skills/githubtoyoutube/scripts')
from stickman_engine_v2 import draw_stylized_stickman

class Stickman:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def draw(self, ctx, pose="explaining", t=0.0, eye_look="straight"):
        if pose == "shock":
            draw_stylized_stickman(ctx, self.x, self.y, scale=1.38, mood="shocked", t=t, action="shocked")
        elif pose == "thinking":
            draw_stylized_stickman(ctx, self.x, self.y, scale=1.38, mood="thinking", t=t, action="thinking")
        elif pose == "typing":
            # High energy celebration / keyboard action
            draw_stylized_stickman(ctx, self.x, self.y, scale=1.38, mood="confident", t=t, action="celebrating")
        elif pose == "flex":
            draw_stylized_stickman(ctx, self.x, self.y, scale=1.38, mood="confident", t=t, action="celebrating")
        elif pose == "point_down":
            draw_stylized_stickman(ctx, self.x, self.y, scale=1.38, mood="confident", t=t, action="pointing")
        else:
            draw_stylized_stickman(ctx, self.x, self.y, scale=1.38, mood="confident", t=t, action="explaining")

# -------------------------------------------------------------
# MASTER RENDER PIPELINE & CLI
# -------------------------------------------------------------
def render_test_frames(output_dir="/tmp/gpu_unlock_previews"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    test_times = [3.0, 15.0, 28.0, 40.0, 52.0]
    for idx, t in enumerate(test_times):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surface)
        render_frame_to_surface(ctx, int(t * FPS), int(DURATION * FPS), t)
        out_png = f"{output_dir}/preview_scene_{idx+1}_{int(t)}s.png"
        surface.write_to_png(out_png)
        print(f"[PREVIEW] Rendered test frame at {t:.1f}s -> {out_png}")

def render_full_video(output_mp4, audio_wav):
    import subprocess
    import time
    
    total_frames = int(DURATION * FPS)
    print(f"=== STARTING MASTER NVENC RENDER: {total_frames} frames ({DURATION:.2f}s) @ {FPS} FPS ===")
    print(f"Output: {output_mp4}")
    print(f"Audio:  {audio_wav}")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "bgra",
        "-s", f"{W}x{H}",
        "-r", str(FPS),
        "-i", "-",
        "-i", audio_wav,
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-tune", "hq",
        "-cq", "19",
        "-b:v", "12M",
        "-maxrate", "18M",
        "-bufsize", "24M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4
    ]
    
    start_time = time.time()
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    
    stride = surface.get_stride()
    
    for f_idx in range(total_frames):
        t = f_idx / float(FPS)
        render_frame_to_surface(ctx, f_idx, total_frames, t)
        surface.flush()
        raw_data = surface.get_data()
        proc.stdin.write(raw_data)
        
        if (f_idx + 1) % 90 == 0 or (f_idx + 1) == total_frames:
            elapsed = time.time() - start_time
            fps_eff = (f_idx + 1) / elapsed if elapsed > 0 else 0
            eta = (total_frames - (f_idx + 1)) / fps_eff if fps_eff > 0 else 0
            pct = ((f_idx + 1) / total_frames) * 100
            print(f"[RENDER] Frame {f_idx+1}/{total_frames} ({pct:.1f}%) | Speed: {fps_eff:.1f} fps | ETA: {eta:.1f}s")
            
    proc.stdin.close()
    stderr_out = proc.stderr.read().decode('utf-8', errors='ignore')
    proc.wait()
    
    if proc.returncode != 0:
        print(f"[ERROR] FFmpeg failed with exit code {proc.returncode}:")
        print(stderr_out[-1000:])
        raise RuntimeError(f"FFmpeg encoding failed with exit code {proc.returncode}")
        
    total_elapsed = time.time() - start_time
    print(f"=== RENDER COMPLETE! Finished in {total_elapsed:.1f}s ({total_frames/total_elapsed:.1f} fps average) ===")
    print(f"Empirical video saved to: {output_mp4}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render 60s GPU Unlock Cartoon Short")
    parser.add_argument("--test", action="store_true", help="Render 5 test preview frames")
    parser.add_argument("--output", default="/opt/floworkos/documents/videos/gpu-unlock-short/gpu_unlock_short_master.mp4")
    parser.add_argument("--audio", default="/tmp/gpu_unlock_final_audio_mastered.wav")
    args = parser.parse_args()
    
    if args.test:
        render_test_frames()
    else:
        render_full_video(args.output, args.audio)
