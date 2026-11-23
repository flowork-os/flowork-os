#!/usr/bin/env python3
"""
🎬 SOVEREIGN YOUTUBE SHORT: PONYTAIL (TRENDING GITHUB REPO)
Repository: DietrichGebert/ponytail (196k+ Stars)
Tagline: "The best code is the code you never wrote."

Format: Vertical 9:16 (1080x1920, 30 FPS, 58.0 Seconds)
Visual Standard:
- Bright Non-White Background (Warm Studio Cream #FDFBF7)
- Matte Dark Characters & Expressive Rubber-Hose Animation
- Junior Dev (Frantic Panic, 50k Lines Spaghetti, Sweat Drops, Smoking PC)
- Senior Dev (Ponytail, Cool Shades, Coffee Mug, Relaxed Smirk)
- Giant [DELETE] Key Press -> Comic Explosion -> Clean 5-Line Code
- Dual CTA: GitHub DietrichGebert/ponytail + FLOWORKOS.COM
"""

import os
import sys
import math
import wave
import subprocess
import cairo
import numpy as np

# Audio Path
AUDIO_WAV = "/tmp/ponytail_final_audio_mastered.wav"

# Dimension Constants
W, H = 1080, 1920
FPS = 30
if os.path.exists(AUDIO_WAV):
    with wave.open(AUDIO_WAV, 'rb') as _wf:
        DURATION = _wf.getnframes() / float(_wf.getframerate())
else:
    DURATION = 56.4
TOTAL_FRAMES = int(DURATION * FPS)
FLOOR_Y = 1420

OUT_DIR = "/opt/floworkos/documents/videos/ponytail-short"
USER_OUT_DIR = os.path.expanduser("~/Documents/videos/ponytail-short")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(USER_OUT_DIR, exist_ok=True)

OUT_MP4 = os.path.join(OUT_DIR, "PONYTAIL_TRENDING_GITHUB_CARTOON_SHORT.mp4")
USER_OUT_MP4 = os.path.join(USER_OUT_DIR, "PONYTAIL_TRENDING_GITHUB_CARTOON_SHORT.mp4")
CONTACT_SHEET_PNG = os.path.join(OUT_DIR, "PONYTAIL_CARTOON_SHORT_contact_sheet.png")
USER_CONTACT_SHEET_PNG = os.path.join(USER_OUT_DIR, "PONYTAIL_CARTOON_SHORT_contact_sheet.png")
AVATAR_PNG = "/tmp/ponytail_avatar.png"

# Load Avatar if present
AVATAR_SURF = None
if os.path.exists(AVATAR_PNG):
    try:
        AVATAR_SURF = cairo.ImageSurface.create_from_png(AVATAR_PNG)
    except Exception:
        AVATAR_SURF = None

# ----------------- DRAWING PRIMITIVES -----------------

def draw_star(ctx, cx, cy, r_outer=18, r_inner=8, color=(1.0, 0.85, 0.0)):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.set_source_rgb(*color)
    ctx.new_path()
    for i in range(10):
        angle = i * math.pi / 5 - math.pi / 2
        r = r_outer if i % 2 == 0 else r_inner
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        if i == 0:
            ctx.move_to(x, y)
        else:
            ctx.line_to(x, y)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(0.2, 0.1, 0.0, 0.5)
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.restore()

def draw_comic_sparks(ctx, cx, cy, scale=1.0, color=(1.0, 0.8, 0.0)):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    ctx.set_source_rgb(*color)
    for i in range(8):
        angle = i * (math.pi / 4)
        ctx.save()
        ctx.rotate(angle)
        ctx.move_to(20, 0)
        ctx.line_to(55, -8)
        ctx.line_to(45, 0)
        ctx.line_to(65, 5)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    ctx.restore()

def draw_speech_bubble(ctx, cx, cy, w, h, text, tail_dir="down"):
    ctx.save()
    ctx.translate(cx - w/2, cy - h/2)
    rad = 20
    ctx.new_sub_path()
    ctx.arc(w - rad, rad, rad, -math.pi/2, 0)
    ctx.arc(w - rad, h - rad, rad, 0, math.pi/2)
    ctx.arc(rad, h - rad, rad, math.pi/2, math.pi)
    ctx.arc(rad, rad, rad, math.pi, 3*math.pi/2)
    ctx.close_path()
    
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.set_line_width(4)
    ctx.stroke()
    
    # Text
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ext = ctx.text_extents(text)
    ctx.set_source_rgb(0.1, 0.1, 0.15)
    ctx.move_to((w - ext.width)/2, (h + ext.height)/2)
    ctx.show_text(text)
    ctx.restore()

def draw_sweat_drop(ctx, x, y, size=15):
    ctx.save()
    ctx.translate(x, y)
    ctx.set_source_rgb(0.2, 0.6, 1.0)
    ctx.move_to(0, -size)
    ctx.curve_to(size, size/2, size/2, size, 0, size)
    ctx.curve_to(-size/2, size, -size, size/2, 0, -size)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0.05, 0.2, 0.5)
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.restore()

# ----------------- ROOM & BACKGROUND -----------------

def draw_studio_environment(ctx, t, theme="cream", cam_x=0, cam_y=0):
    ctx.save()
    ctx.translate(cam_x, cam_y)
    
    # Base Wall
    if theme == "cream":
        base_col = (0.99, 0.98, 0.96) # #FDFBF7 Warm cream
    elif theme == "emergency":
        pulse = 0.5 + 0.5 * math.sin(t * 12)
        base_col = (0.98 + 0.02 * pulse, 0.88 - 0.15 * pulse, 0.88 - 0.15 * pulse)
    elif theme == "emerald":
        base_col = (0.94, 0.99, 0.96)
    else:
        base_col = (0.95, 0.97, 1.0)
        
    ctx.set_source_rgb(*base_col)
    ctx.rectangle(-50, -50, W + 100, H + 100)
    ctx.fill()
    
    # Subtle geometric grid pattern
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.025)
    ctx.set_line_width(1.5)
    for x in range(0, W, 80):
        ctx.move_to(x, 0)
        ctx.line_to(x, FLOOR_Y)
    for y in range(0, FLOOR_Y, 80):
        ctx.move_to(0, y)
        ctx.line_to(W, y)
    ctx.stroke()
    
    # Floor (Warm dark parquet / studio plank)
    floor_grad = cairo.LinearGradient(0, FLOOR_Y, 0, H)
    floor_grad.add_color_stop_rgb(0.0, 0.82, 0.78, 0.72)
    floor_grad.add_color_stop_rgb(1.0, 0.72, 0.67, 0.60)
    ctx.set_source(floor_grad)
    ctx.rectangle(0, FLOOR_Y, W, H - FLOOR_Y)
    ctx.fill()
    
    # Floor separator border line
    ctx.set_source_rgb(0.35, 0.30, 0.25)
    ctx.set_line_width(6)
    ctx.move_to(0, FLOOR_Y)
    ctx.line_to(W, FLOOR_Y)
    ctx.stroke()
    
    # Emergency Siren Light if in emergency mode
    if theme == "emergency":
        siren_x = W - 140
        siren_y = 120
        flash = 0.5 + 0.5 * math.sin(t * 16)
        # Red beam
        ctx.save()
        beam_grad = cairo.RadialGradient(siren_x, siren_y, 10, siren_x, siren_y, 350)
        beam_grad.add_color_stop_rgba(0.0, 1.0, 0.1, 0.1, 0.7 * flash)
        beam_grad.add_color_stop_rgba(1.0, 1.0, 0.0, 0.0, 0.0)
        ctx.set_source(beam_grad)
        ctx.rectangle(0, 0, W, FLOOR_Y)
        ctx.fill()
        ctx.restore()
        
        # Siren lamp body
        ctx.set_source_rgb(0.2, 0.2, 0.2)
        ctx.rectangle(siren_x - 30, siren_y, 60, 25)
        ctx.fill()
        ctx.set_source_rgb(1.0, 0.15, 0.15)
        ctx.arc(siren_x, siren_y, 25, math.pi, 0)
        ctx.fill()
    
    ctx.restore()

# ----------------- PROPS & STICKMEN -----------------

def draw_junior_dev(ctx, cx, cy, scale=1.0, state=None):
    """Junior Dev: frantic, sweating, panicked typing or screaming."""
    if state is None: state = {}
    pose = state.get("pose", "panic_type")
    t = state.get("t", 0.0)
    
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    
    body_col = (0.12, 0.14, 0.18) # Dark matte obsidian
    
    # Desk and Computer
    ctx.save()
    # Desk top
    ctx.set_source_rgb(0.25, 0.22, 0.20)
    ctx.rectangle(-180, 20, 360, 25)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.1, 0.08, 0.06)
    ctx.set_line_width(4)
    ctx.stroke()
    
    # Desk legs
    ctx.rectangle(-160, 45, 20, 160)
    ctx.rectangle(140, 45, 20, 160)
    ctx.fill()
    
    # Smoking PC Monitor
    ctx.set_source_rgb(0.15, 0.16, 0.20)
    ctx.rectangle(-140, -180, 280, 190)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.05, 0.05, 0.08)
    ctx.set_line_width(5)
    ctx.stroke()
    
    # Monitor Screen (Red Error / Glitch)
    if pose in ["panic_type", "screaming"]:
        scr_grad = cairo.LinearGradient(-130, -170, 130, 0)
        pulse = 0.5 + 0.5 * math.sin(t * 14)
        scr_grad.add_color_stop_rgb(0.0, 0.6 + 0.2 * pulse, 0.05, 0.05)
        scr_grad.add_color_stop_rgb(1.0, 0.3 + 0.1 * pulse, 0.02, 0.02)
        ctx.set_source(scr_grad)
    else:
        ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.rectangle(-130, -170, 260, 170)
    ctx.fill()
    
    # Error text on screen
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(15)
    ctx.set_source_rgb(1.0, 0.3, 0.3)
    ctx.move_to(-120, -140); ctx.show_text("ERROR: OUT OF MEMORY!")
    ctx.move_to(-120, -115); ctx.show_text("CPU: 100% | THREADS: 50k")
    ctx.move_to(-120, -90); ctx.show_text("STACK OVERFLOW EXCEPTION")
    ctx.move_to(-120, -65); ctx.show_text("DEPENDENCY CONFLICT x1429")
    ctx.set_source_rgb(1.0, 0.8, 0.0)
    ctx.move_to(-120, -35); ctx.show_text("SERVER IS BURNING... 🔥")
    
    # Smoke rising from monitor
    smoke_y = -190 - (t * 80) % 120
    ctx.set_source_rgba(0.5, 0.5, 0.5, 0.45 * (1.0 - ((t * 80) % 120) / 120))
    ctx.arc(math.sin(t*8)*20, smoke_y, 25, 0, 2*math.pi)
    ctx.fill()
    
    # Keyboard
    ctx.set_source_rgb(0.3, 0.32, 0.38)
    ctx.rectangle(-110, 5, 220, 16)
    ctx.fill()
    ctx.restore()
    
    # Junior Stickman Body (sitting behind/beside desk)
    chair_x = -220
    chair_y = -30
    
    # Body jitter when panicking
    jitter = math.sin(t * 35) * 6 if pose in ["panic_type", "screaming"] else 0
    
    ctx.save()
    ctx.translate(chair_x + jitter, chair_y)
    
    # Torso
    ctx.set_source_rgb(*body_col)
    ctx.set_line_width(12)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(0, -60)
    ctx.line_to(10, 60)
    ctx.stroke()
    
    # Head
    head_y = -120
    ctx.set_source_rgb(*body_col)
    ctx.arc(0, head_y, 45, 0, 2*math.pi)
    ctx.fill()
    
    # Disheveled Hair spikes
    ctx.set_source_rgb(*body_col)
    ctx.set_line_width(6)
    ctx.move_to(-25, head_y - 35); ctx.line_to(-40, head_y - 65); ctx.stroke()
    ctx.move_to(0, head_y - 45); ctx.line_to(5, head_y - 75); ctx.stroke()
    ctx.move_to(25, head_y - 35); ctx.line_to(45, head_y - 60); ctx.stroke()
    
    # Face (Horrified Eyes)
    if pose in ["panic_type", "screaming", "shocked"]:
        # White sclera
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.arc(-15, head_y - 5, 16, 0, 2*math.pi); ctx.fill()
        ctx.arc(18, head_y - 5, 16, 0, 2*math.pi); ctx.fill()
        # Tiny vibrating pupils
        p_jit = math.sin(t * 40) * 3
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.arc(-15 + p_jit, head_y - 5, 5, 0, 2*math.pi); ctx.fill()
        ctx.arc(18 + p_jit, head_y - 5, 5, 0, 2*math.pi); ctx.fill()
        # Mouth open screaming
        ctx.set_source_rgb(0.8, 0.1, 0.1)
        ctx.arc(2, head_y + 22, 16, 0, math.pi); ctx.fill()
        # Flying sweat droplets
        draw_sweat_drop(ctx, -55, head_y - 20 + math.sin(t*10)*15, 14)
        draw_sweat_drop(ctx, 55, head_y - 30 + math.cos(t*12)*15, 16)
    else:
        # Happy / relieved
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.arc(-15, head_y - 5, 12, 0, 2*math.pi); ctx.fill()
        ctx.arc(15, head_y - 5, 12, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.arc(-15, head_y - 5, 4, 0, 2*math.pi); ctx.fill()
        ctx.arc(15, head_y - 5, 4, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgb(0.9, 0.2, 0.2)
        ctx.arc(0, head_y + 15, 14, 0, math.pi); ctx.fill()
    
    # Arms frantically typing
    ctx.set_source_rgb(*body_col)
    ctx.set_line_width(10)
    type_cycle = math.sin(t * 30)
    # Left arm
    ctx.move_to(-5, -30)
    ctx.line_to(40, -10 + type_cycle * 15)
    ctx.line_to(95, 35 - type_cycle * 12)
    ctx.stroke()
    # Right arm
    ctx.move_to(5, -30)
    ctx.line_to(55, -5 - type_cycle * 15)
    ctx.line_to(115, 35 + type_cycle * 12)
    ctx.stroke()
    
    # Legs (seated)
    ctx.move_to(10, 60); ctx.line_to(60, 110); ctx.line_to(65, 175); ctx.stroke()
    
    ctx.restore()
    ctx.restore()

def draw_senior_dev(ctx, cx, cy, scale=1.0, state=None):
    """Senior Dev: Ponytail, cool sunglasses, coffee mug, relaxed swagger."""
    if state is None: state = {}
    pose = state.get("pose", "stand_coffee")
    t = state.get("t", 0.0)
    
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    
    body_col = (0.10, 0.11, 0.14) # Obsidian matte
    
    # Bobbing bounce
    bob = math.sin(t * 4) * 6
    torso_y = -40 + bob
    head_y = torso_y - 95
    
    # Torso (Hoodie shape)
    ctx.save()
    ctx.set_source_rgb(*body_col)
    # Hoodie trapezoid
    ctx.move_to(-38, torso_y - 25)
    ctx.line_to(38, torso_y - 25)
    ctx.line_to(32, torso_y + 65)
    ctx.line_to(-32, torso_y + 65)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0.04, 0.05, 0.06)
    ctx.set_line_width(4)
    ctx.stroke()
    
    # Sovereign Flowork OS Stacked Chest Branding
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(11)
    ctx.set_source_rgb(0.0, 1.0, 0.4) # Matrix green #00ff66
    ext1 = ctx.text_extents("FLOWORKOS")
    ctx.move_to(-ext1.width/2, torso_y + 8)
    ctx.show_text("FLOWORKOS")
    ctx.set_font_size(10)
    ext2 = ctx.text_extents(".COM")
    ctx.move_to(-ext2.width/2, torso_y + 24)
    ctx.show_text(".COM")
    ctx.restore()
    
    # Head
    ctx.save()
    ctx.set_source_rgb(*body_col)
    ctx.arc(0, head_y, 42, 0, 2*math.pi)
    ctx.fill()
    
    # THE ICONIC PONYTAIL (tied at back of head)
    ctx.save()
    ponytail_sway = math.sin(t * 6) * 0.15
    ctx.translate(-38, head_y - 5)
    ctx.rotate(ponytail_sway)
    # Hairband (Cyan/Green)
    ctx.set_source_rgb(0.0, 0.95, 0.8)
    ctx.rectangle(-4, -6, 8, 12)
    ctx.fill()
    # Hair clump curves down gracefully
    ctx.set_source_rgb(*body_col)
    ctx.set_line_width(14)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-4, 0)
    ctx.curve_to(-40, 10, -50, 45, -35, 75)
    ctx.stroke()
    ctx.set_line_width(8)
    ctx.move_to(-4, 2)
    ctx.curve_to(-35, 20, -42, 55, -28, 85)
    ctx.stroke()
    ctx.restore()
    
    # Cool Jet-Black Sunglasses (Retro Wayfarer shades)
    ctx.save()
    ctx.set_source_rgb(0.02, 0.02, 0.04)
    # Left lens
    ctx.rectangle(-28, head_y - 10, 24, 18)
    ctx.fill()
    # Right lens
    ctx.rectangle(4, head_y - 10, 24, 18)
    ctx.fill()
    # Bridge
    ctx.set_line_width(4)
    ctx.move_to(-6, head_y - 4); ctx.line_to(6, head_y - 4); ctx.stroke()
    # Specular White Reflection Glare on shades
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.75)
    ctx.set_line_width(2.5)
    ctx.move_to(-24, head_y - 8); ctx.line_to(-12, head_y + 4); ctx.stroke()
    ctx.move_to(8, head_y - 8); ctx.line_to(20, head_y + 4); ctx.stroke()
    ctx.restore()
    
    # Smug confident smile / smirk
    ctx.set_source_rgb(0.9, 0.8, 0.7)
    ctx.set_line_width(3.5)
    ctx.arc(0, head_y + 16, 12, 0.1 * math.pi, 0.85 * math.pi)
    ctx.stroke()
    ctx.restore()
    
    # Arms and Coffee Mug
    ctx.set_source_rgb(*body_col)
    ctx.set_line_width(12)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    
    if pose == "point_forward":
        # Pointing arm
        ctx.move_to(25, torso_y - 10)
        ctx.line_to(110, torso_y - 25)
        ctx.line_to(165, torso_y - 30)
        ctx.stroke()
        # Pointing finger
        ctx.set_line_width(6)
        ctx.move_to(165, torso_y - 30); ctx.line_to(185, torso_y - 30); ctx.stroke()
        # Left arm holding coffee
        ctx.set_line_width(12)
        ctx.move_to(-25, torso_y - 10)
        ctx.line_to(-60, torso_y + 15)
        ctx.line_to(-40, torso_y + 35)
        ctx.stroke()
        draw_coffee_mug(ctx, -40, torso_y + 35, t)
    elif pose == "press_button":
        # Right arm pressing big key down
        press_y = torso_y + 45
        ctx.move_to(25, torso_y - 10)
        ctx.line_to(80, torso_y + 20)
        ctx.line_to(110, press_y)
        ctx.stroke()
        # Left arm on hip
        ctx.move_to(-25, torso_y - 10)
        ctx.line_to(-65, torso_y + 15)
        ctx.line_to(-40, torso_y + 45)
        ctx.stroke()
    else: # "stand_coffee"
        # Holding coffee mug with both hands comfortably
        ctx.move_to(-25, torso_y - 10)
        ctx.line_to(-50, torso_y + 15)
        ctx.line_to(-10, torso_y + 25)
        ctx.stroke()
        ctx.move_to(25, torso_y - 10)
        ctx.line_to(45, torso_y + 15)
        ctx.line_to(10, torso_y + 25)
        ctx.stroke()
        draw_coffee_mug(ctx, 0, torso_y + 25, t)
        
    # Legs (Standing cool)
    ctx.set_line_width(12)
    leg_bob = math.sin(t * 4) * 3
    # Left leg
    ctx.move_to(-18, torso_y + 65)
    ctx.line_to(-24, torso_y + 140)
    ctx.line_to(-26, torso_y + 215 + leg_bob)
    ctx.stroke()
    # Right leg (slightly crossed / relaxed)
    ctx.move_to(18, torso_y + 65)
    ctx.line_to(28, torso_y + 140)
    ctx.line_to(32, torso_y + 215 + leg_bob)
    ctx.stroke()
    
    ctx.restore()

def draw_coffee_mug(ctx, cx, cy, t):
    """Draws warm ceramic coffee mug with rising steam."""
    ctx.save()
    ctx.translate(cx, cy)
    
    # Mug body
    ctx.set_source_rgb(0.95, 0.95, 0.95)
    ctx.rectangle(-14, -18, 28, 30)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.set_line_width(3)
    ctx.stroke()
    
    # Handle
    ctx.arc(14, -3, 8, -math.pi/2, math.pi/2)
    ctx.stroke()
    
    # Hot coffee inside
    ctx.set_source_rgb(0.35, 0.18, 0.05)
    ctx.arc(0, -18, 12, 0, 2*math.pi)
    ctx.fill()
    
    # Steaming curls
    ctx.set_source_rgba(0.7, 0.7, 0.7, 0.6)
    ctx.set_line_width(2.5)
    for i, offset_x in enumerate([-6, 6]):
        steam_y = -24 - (t * 25 + i * 15) % 45
        ctx.move_to(offset_x, -22)
        ctx.curve_to(offset_x + math.sin(t*8 + i)*8, steam_y + 15,
                     offset_x - math.sin(t*8 + i)*8, steam_y + 8,
                     offset_x + math.sin(t*8)*6, steam_y)
        ctx.stroke()
    ctx.restore()

# ----------------- UI HERO CARDS & PROPS -----------------

def draw_hook_title_card(ctx, t):
    """Babak 0: Giant High-Impact Center Hook Card."""
    pulse = 1.0 + 0.04 * math.sin(t * 12)
    ctx.save()
    ctx.translate(W/2, 420)
    ctx.scale(pulse, pulse)
    
    card_w, card_h = 940, 360
    
    # Glowing shadow
    glow = cairo.RadialGradient(0, 0, 100, 0, 0, 520)
    glow.add_color_stop_rgba(0.0, 1.0, 0.8, 0.0, 0.45)
    glow.add_color_stop_rgba(1.0, 1.0, 0.5, 0.0, 0.0)
    ctx.set_source(glow)
    ctx.rectangle(-card_w/2 - 60, -card_h/2 - 60, card_w + 120, card_h + 120)
    ctx.fill()
    
    # Dark card container
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.rectangle(-card_w/2, -card_h/2, card_w, card_h)
    ctx.fill_preserve()
    ctx.set_source_rgb(1.0, 0.82, 0.0)
    ctx.set_line_width(8)
    ctx.stroke()
    
    # Comic corner sparks
    draw_comic_sparks(ctx, -card_w/2, -card_h/2, 1.1, (1.0, 0.85, 0.0))
    draw_comic_sparks(ctx, card_w/2, -card_h/2, 1.1, (1.0, 0.85, 0.0))
    
    # Top Tag
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    t1 = "★ VIRAL OPEN SOURCE SHOWCASE ★"
    ext1 = ctx.text_extents(t1)
    ctx.move_to(-ext1.width/2, -100)
    ctx.show_text(t1)
    
    # Main Hook Text
    ctx.set_font_size(52)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    t2 = "CODING 50.000 BARIS"
    ext2 = ctx.text_extents(t2)
    ctx.move_to(-ext2.width/2, -20)
    ctx.show_text(t2)
    
    ctx.set_font_size(44)
    ctx.set_source_rgb(1.0, 0.3, 0.3)
    t3 = "vs SENIOR DEV MALAS?!"
    ext3 = ctx.text_extents(t3)
    ctx.move_to(-ext3.width/2, 45)
    ctx.show_text(t3)
    
    # Sub badge
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.rectangle(-260, 85, 520, 52)
    ctx.fill()
    ctx.set_source_rgb(0.08, 0.08, 0.08)
    ctx.set_font_size(24)
    t4 = "THE BEST CODE = ZERO CODE!"
    ext4 = ctx.text_extents(t4)
    ctx.move_to(-ext4.width/2, 120)
    ctx.show_text(t4)
    
    ctx.restore()

def draw_github_ponytail_hero(ctx, t):
    """Babak 2: GitHub Repository Showcase Card."""
    ctx.save()
    ctx.translate(W/2, 450)
    
    card_w, card_h = 960, 480
    
    # Card Background
    ctx.set_source_rgb(0.08, 0.09, 0.13)
    ctx.rectangle(-card_w/2, -card_h/2, card_w, card_h)
    ctx.fill_preserve()
    # Glowing emerald/cyan border
    ctx.set_source_rgb(0.0, 0.9, 0.7)
    ctx.set_line_width(6)
    ctx.stroke()
    
    # Window Top Bar
    ctx.set_source_rgb(0.14, 0.16, 0.22)
    ctx.rectangle(-card_w/2, -card_h/2, card_w, 65)
    ctx.fill()
    
    # Traffic light window dots
    for i, col in enumerate([(1.0, 0.35, 0.35), (1.0, 0.78, 0.25), (0.2, 0.85, 0.4)]):
        ctx.set_source_rgb(*col)
        ctx.arc(-card_w/2 + 45 + i*35, -card_h/2 + 32, 11, 0, 2*math.pi)
        ctx.fill()
        
    # URL Pill
    ctx.set_source_rgb(0.06, 0.07, 0.10)
    ctx.rectangle(-card_w/2 + 180, -card_h/2 + 15, 620, 36)
    ctx.fill()
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(20)
    ctx.set_source_rgb(0.7, 0.75, 0.85)
    ctx.move_to(-card_w/2 + 200, -card_h/2 + 40)
    ctx.show_text("github.com/DietrichGebert/ponytail")
    
    # Repo Header Content
    # Avatar icon
    if AVATAR_SURF:
        ctx.save()
        ctx.translate(-card_w/2 + 55, -card_h/2 + 105)
        scale_av = 110.0 / AVATAR_SURF.get_width()
        ctx.scale(scale_av, scale_av)
        ctx.set_source_surface(AVATAR_SURF, 0, 0)
        ctx.paint()
        ctx.restore()
    else:
        ctx.set_source_rgb(0.2, 0.25, 0.35)
        ctx.arc(-card_w/2 + 110, -card_h/2 + 160, 55, 0, 2*math.pi)
        ctx.fill()
    
    # Repo Title
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(44)
    ctx.set_source_rgb(0.35, 0.75, 1.0)
    ctx.move_to(-card_w/2 + 190, -card_h/2 + 140)
    ctx.show_text("DietrichGebert / ponytail")
    
    # Star Badge (Pulsing Gold)
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.rectangle(-card_w/2 + 190, -card_h/2 + 165, 320, 48)
    ctx.fill()
    ctx.set_source_rgb(0.08, 0.08, 0.08)
    ctx.set_font_size(26)
    draw_star(ctx, -card_w/2 + 220, -card_h/2 + 189, 14, 6, (0.1, 0.1, 0.1))
    ctx.move_to(-card_w/2 + 245, -card_h/2 + 198)
    ctx.show_text("196,084 STARS ★")
    
    # Trending Tag
    ctx.set_source_rgb(0.9, 0.2, 0.4)
    ctx.rectangle(-card_w/2 + 530, -card_h/2 + 165, 230, 48)
    ctx.fill()
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.set_font_size(22)
    ctx.move_to(-card_w/2 + 550, -card_h/2 + 198)
    ctx.show_text("🔥 #1 TRENDING")
    
    # Tagline Box
    ctx.set_source_rgb(0.12, 0.14, 0.19)
    ctx.rectangle(-card_w/2 + 45, -card_h/2 + 245, card_w - 90, 190)
    ctx.fill()
    
    ctx.set_source_rgb(1.0, 0.95, 0.7)
    ctx.set_font_size(28)
    ctx.move_to(-card_w/2 + 75, -card_h/2 + 295)
    ctx.show_text('"Makes your AI agent think like the laziest')
    ctx.move_to(-card_w/2 + 75, -card_h/2 + 335)
    ctx.show_text(' senior dev in the room."')
    
    # Golden Quote
    ctx.set_source_rgb(0.0, 1.0, 0.5)
    ctx.set_font_size(29)
    ctx.move_to(-card_w/2 + 75, -card_h/2 + 395)
    ctx.show_text('💡 "The best code is the code you never wrote!"')
    
    ctx.restore()

def draw_delete_button_vfx(ctx, t, is_pressed=False):
    """Babak 3: Giant 3D Mechanical [DELETE] Key."""
    ctx.save()
    ctx.translate(W/2, 600)
    
    btn_w, btn_h = 580, 220
    press_offset = 35 if is_pressed else 0
    
    # Shadow
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.35)
    ctx.rectangle(-btn_w/2, -btn_h/2 + 50, btn_w, btn_h)
    ctx.fill()
    
    # 3D Base
    ctx.set_source_rgb(0.65, 0.1, 0.15)
    ctx.rectangle(-btn_w/2, -btn_h/2 + press_offset, btn_w, btn_h)
    ctx.fill()
    
    # Key Face (Red Hot Neon)
    face_grad = cairo.LinearGradient(0, -btn_h/2 + press_offset, 0, btn_h/2 + press_offset)
    face_grad.add_color_stop_rgb(0.0, 1.0, 0.25, 0.25)
    face_grad.add_color_stop_rgb(1.0, 0.85, 0.15, 0.15)
    ctx.set_source(face_grad)
    ctx.rectangle(-btn_w/2 + 15, -btn_h/2 + press_offset + 10, btn_w - 30, btn_h - 40)
    ctx.fill_preserve()
    ctx.set_source_rgb(1.0, 0.8, 0.8)
    ctx.set_line_width(5)
    ctx.stroke()
    
    # Key Label
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(68)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    txt = "[ DELETE ]"
    ext = ctx.text_extents(txt)
    ctx.move_to(-ext.width/2, press_offset + 25)
    ctx.show_text(txt)
    
    ctx.restore()

def draw_clean_code_terminal(ctx, t):
    """Babak 4: Clean 5-Line Terminal Screen + Max Speedometer."""
    ctx.save()
    ctx.translate(W/2, 480)
    
    term_w, term_h = 940, 520
    
    # Terminal Container
    ctx.set_source_rgb(0.05, 0.06, 0.08)
    ctx.rectangle(-term_w/2, -term_h/2, term_w, term_h)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.set_line_width(6)
    ctx.stroke()
    
    # Titlebar
    ctx.set_source_rgb(0.12, 0.14, 0.18)
    ctx.rectangle(-term_w/2, -term_h/2, term_w, 55)
    ctx.fill()
    
    # Badge
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(22)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(-term_w/2 + 35, -term_h/2 + 36)
    ctx.show_text("⚡ PONYTAIL AI COMPILER: OPTIMIZED!")
    
    # Code Lines (Neon Matrix Green & Cyan)
    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26)
    
    lines = [
        ("// 49,995 SPAGHETTI LINES PURGED! [OK]", (1.0, 0.35, 0.35)),
        ("// PONYTAIL STANDARD SUITE - 5 LINES LEFT:", (1.0, 0.85, 0.0)),
        ("import { auth } from 'std/auth';", (0.3, 0.85, 1.0)),
        ("export const login = () => auth.verify();", (0.3, 0.85, 1.0)),
        ("// ZERO DEPENDENCIES | RAM: 0.1MB | EXEC: 0.001ms", (0.0, 1.0, 0.4)),
    ]
    
    for i, (line_txt, col) in enumerate(lines):
        ctx.set_source_rgb(*col)
        ctx.move_to(-term_w/2 + 45, -term_h/2 + 115 + i * 50)
        ctx.show_text(line_txt)
        
    # Big Turbo Speedometer Box
    ctx.set_source_rgb(0.09, 0.12, 0.16)
    ctx.rectangle(-term_w/2 + 40, term_h/2 - 130, term_w - 80, 95)
    ctx.fill()
    
    ctx.set_source_rgb(0.0, 1.0, 0.5)
    ctx.set_font_size(32)
    ctx.move_to(-term_w/2 + 75, term_h/2 - 75)
    ctx.show_text("PERFORMANCE GAIN: +10,000% 🚀 [MAX SPEED]")
    
    ctx.restore()

def draw_dual_outro_card(ctx, t):
    """Babak 5: Dual Call-To-Action (Outro)."""
    ctx.save()
    ctx.translate(W/2, 480)
    
    card_w, card_h = 960, 560
    
    # Outer Glow
    glow = cairo.RadialGradient(0, 0, 120, 0, 0, 560)
    glow.add_color_stop_rgba(0.0, 0.0, 1.0, 0.4, 0.4)
    glow.add_color_stop_rgba(1.0, 0.0, 0.5, 0.2, 0.0)
    ctx.set_source(glow)
    ctx.rectangle(-card_w/2 - 40, -card_h/2 - 40, card_w + 80, card_h + 80)
    ctx.fill()
    
    # Container
    ctx.set_source_rgb(0.07, 0.08, 0.11)
    ctx.rectangle(-card_w/2, -card_h/2, card_w, card_h)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.set_line_width(8)
    ctx.stroke()
    
    # Top Section: GitHub Repo CTA
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(32)
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    t1 = "★ STAR THE REPOSITORY ON GITHUB! ★"
    ext1 = ctx.text_extents(t1)
    ctx.move_to(-ext1.width/2, -190)
    ctx.show_text(t1)
    
    ctx.set_font_size(44)
    ctx.set_source_rgb(0.35, 0.75, 1.0)
    t2 = "DietrichGebert / ponytail"
    ext2 = ctx.text_extents(t2)
    ctx.move_to(-ext2.width/2, -125)
    ctx.show_text(t2)
    
    ctx.set_font_size(26)
    ctx.set_source_rgb(0.8, 0.85, 0.9)
    t3 = "196,084+ STARS ★ FREE & OPEN SOURCE"
    ext3 = ctx.text_extents(t3)
    ctx.move_to(-ext3.width/2, -75)
    ctx.show_text(t3)
    
    # Dividing Line
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.15)
    ctx.set_line_width(3)
    ctx.move_to(-card_w/2 + 50, -25); ctx.line_to(card_w/2 - 50, -25); ctx.stroke()
    
    # Bottom Section: Flowork OS Sovereign Platform
    ctx.set_font_size(28)
    ctx.set_source_rgb(0.9, 0.9, 0.9)
    t4 = "BOOST YOUR SOVEREIGN AGENT PRODUCTIVITY:"
    ext4 = ctx.text_extents(t4)
    ctx.move_to(-ext4.width/2, 35)
    ctx.show_text(t4)
    
    # Giant Pulsing FLOWORKOS.COM Banner
    pulse = 1.0 + 0.03 * math.sin(t * 10)
    ctx.save()
    ctx.scale(pulse, pulse)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.rectangle(-380, 75, 760, 95)
    ctx.fill()
    
    ctx.set_source_rgb(0.04, 0.05, 0.06)
    ctx.set_font_size(54)
    t5 = "FLOWORKOS.COM"
    ext5 = ctx.text_extents(t5)
    ctx.move_to(-ext5.width/2, 142)
    ctx.show_text(t5)
    ctx.restore()
    
    # Bottom Tag
    ctx.set_font_size(22)
    ctx.set_source_rgb(0.7, 0.75, 0.8)
    t6 = "Linux 7.3 Eust Kernel • Native AI Desktop Subsystem"
    ext6 = ctx.text_extents(t6)
    ctx.move_to(-ext6.width/2, 235)
    ctx.show_text(t6)
    
    ctx.restore()

def draw_subtitle_pill(ctx, text, y=1720):
    """Draws crisp high-contrast subtitle pill."""
    if not text: return
    ctx.save()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(32)
    ext = ctx.text_extents(text)
    
    pill_w = ext.width + 80
    pill_h = 75
    pill_x = (W - pill_w) / 2
    pill_y = y - pill_h / 2
    
    # Pill background
    ctx.set_source_rgba(0.05, 0.06, 0.08, 0.92)
    rad = 22
    ctx.new_sub_path()
    ctx.arc(pill_x + pill_w - rad, pill_y + rad, rad, -math.pi/2, 0)
    ctx.arc(pill_x + pill_w - rad, pill_y + pill_h - rad, rad, 0, math.pi/2)
    ctx.arc(pill_x + rad, pill_y + pill_h - rad, rad, math.pi/2, math.pi)
    ctx.arc(pill_x + rad, pill_y + rad, rad, math.pi, 3*math.pi/2)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.set_line_width(3.5)
    ctx.stroke()
    
    # Subtitle Text
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(pill_x + (pill_w - ext.width)/2, pill_y + (pill_h + ext.height)/2 - 4)
    ctx.show_text(text)
    ctx.restore()

def draw_flowork_watermark(ctx):
    """Top-right subtle sovereign badge."""
    ctx.save()
    ctx.translate(W - 220, 70)
    ctx.set_source_rgba(0.08, 0.09, 0.12, 0.85)
    ctx.rectangle(0, 0, 180, 42)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(16)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(15, 27)
    ctx.show_text("FLOWORK OS")
    ctx.restore()

# ----------------- MAIN RENDER PIPELINE -----------------

def render_ponytail_cartoon():
    print(f"🎬 Starting High-Velocity 58s Ponytail Cartoon Render...")
    print(f"Target: {OUT_MP4}")
    print(f"Hardware: NVENC H.264 (RTX 4060 GPU Accelerated)")
    
    # Test NVENC availability
    encoder = "h264_nvenc"
    try:
        chk = subprocess.run(["ffmpeg", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "h264_nvenc" not in chk.stdout:
            encoder = "libx264"
    except Exception:
        encoder = "libx264"
        
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "bgra",
        "-r", str(FPS),
        "-i", "-",
        "-i", AUDIO_WAV,
        "-c:v", encoder,
    ]
    if encoder == "h264_nvenc":
        cmd += ["-preset", "p4", "-cq", "19", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p"]
        
    cmd += [
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUT_MP4
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    
    # Milestone frames for contact sheet (9 key moments)
    contact_times = [2.0, 8.0, 14.0, 20.0, 27.0, 35.0, 42.0, 48.0, 54.0]
    contact_indices = [int(t * FPS) for t in contact_times]
    contact_surfaces = []
    
    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / float(FPS)
        
        cam_shake_x = 0
        cam_shake_y = 0
        theme = "cream"
        subtitle = ""
        
        # ---------------- SCENE 0: HOOK (0 - 4.5s) ----------------
        if t < 4.5:
            theme = "cream"
            draw_studio_environment(ctx, t, theme)
            draw_hook_title_card(ctx, t)
            
            # Junior Dev frantic typing in lower screen
            draw_junior_dev(ctx, W/2, FLOOR_Y - 140, scale=1.0, state={"pose": "panic_type", "t": t})
            subtitle = "Pernah nggak ngoding 50.000 baris cuma buat fitur login simpel?"
            
        # ---------------- SCENE 1: RELATABLE NIGHTMARE (4.5 - 15.0s) ----------------
        elif t < 15.0:
            theme = "emergency"
            # Camera shake when server explodes
            if 5.0 <= t <= 7.0:
                dt = t - 5.0
                cam_shake_x = math.sin(dt * 60) * 16 * math.exp(-dt * 2)
                cam_shake_y = math.cos(dt * 70) * 14 * math.exp(-dt * 2)
            
            draw_studio_environment(ctx, t, theme, cam_shake_x, cam_shake_y)
            
            # Big Red Alert Banner
            ctx.save()
            ctx.translate(W/2, 280)
            ctx.set_source_rgb(0.85, 0.1, 0.1)
            ctx.rectangle(-460, -70, 920, 140)
            ctx.fill_preserve()
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ctx.set_line_width(6)
            ctx.stroke()
            
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(36)
            ctx.move_to(-420, -15); ctx.show_text("🚨 CRITICAL: SERVER EXPLODING!")
            ctx.set_font_size(24)
            ctx.set_source_rgb(1.0, 0.9, 0.2)
            ctx.move_to(-420, 35); ctx.show_text("CPU 100% | 1,429 DEPENDENCY CONFLICTS DETECTED")
            ctx.restore()
            
            # Junior Dev screaming in horror
            draw_junior_dev(ctx, W/2, FLOOR_Y - 140, scale=1.1, state={"pose": "screaming", "t": t})
            
            # Flying flying angry shoe / sandal from angry boss
            sandal_x = (t - 4.5) * 120 % (W + 200) - 100
            sandal_y = 650 + math.sin(t * 15) * 50
            ctx.save()
            ctx.translate(sandal_x, sandal_y)
            ctx.rotate(t * 12)
            ctx.set_source_rgb(0.6, 0.1, 0.1)
            ctx.rectangle(-40, -18, 80, 36)
            ctx.fill()
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(16)
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ctx.move_to(-30, 6); ctx.show_text("BOSS 👠")
            ctx.restore()
            
            subtitle = "Junior dev panik! CPU 100%, seribu dependency tabrakan!"
            
        # ---------------- SCENE 2: THE TURNAROUND (15.0 - 25.0s) ----------------
        elif t < 25.0:
            theme = "emerald"
            draw_studio_environment(ctx, t, theme)
            draw_github_ponytail_hero(ctx, t)
            
            # Senior Dev walking in smoothly from left, sipping coffee
            walk_progress = min(1.0, (t - 15.0) / 3.0)
            senior_x = 220 + walk_progress * 180
            draw_senior_dev(ctx, senior_x, FLOOR_Y - 140, scale=1.0, state={"pose": "stand_coffee", "t": t})
            
            # Speech Bubble from Senior Dev
            if t > 18.0:
                draw_speech_bubble(ctx, senior_x + 190, FLOOR_Y - 420, 320, 80, "Santai, ngopi dulu ☕")
            
            subtitle = "Senior Dev berkuncir kuda datang santai buka repo: Ponytail!"
            
        # ---------------- SCENE 3: PHILOSOPHY REVEAL (25.0 - 34.0s) ----------------
        elif t < 34.0:
            theme = "cream"
            draw_studio_environment(ctx, t, theme)
            
            # Giant Philosophy Quote Banner
            ctx.save()
            ctx.translate(W/2, 340)
            ctx.set_source_rgb(0.08, 0.09, 0.12)
            ctx.rectangle(-460, -120, 920, 240)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.0, 1.0, 0.4)
            ctx.set_line_width(6)
            ctx.stroke()
            
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(24)
            ctx.set_source_rgb(1.0, 0.85, 0.0)
            ctx.move_to(-420, -65); ctx.show_text("★ THE GOLDEN MANIFESTO ★")
            
            ctx.set_font_size(38)
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ctx.move_to(-420, -10); ctx.show_text('"THE BEST CODE IS')
            ctx.move_to(-420, 40); ctx.show_text(' THE CODE YOU NEVER WROTE!"')
            
            ctx.set_font_size(24)
            ctx.set_source_rgb(0.4, 0.8, 1.0)
            ctx.move_to(-420, 85); ctx.show_text("AI Agent Lazy Senior Dev Architecture")
            ctx.restore()
            
            # Senior Dev pointing forward with authority
            draw_senior_dev(ctx, 420, FLOOR_Y - 140, scale=1.05, state={"pose": "point_forward", "t": t})
            
            subtitle = "Filosofi: 'The best code is the code you never wrote!'"
            
        # ---------------- SCENE 4: SUPERPOWER IN ACTION (34.0 - 46.0s) ----------------
        elif t < 46.0:
            # Button Press and Explosion
            is_pressed = (35.5 <= t <= 37.0)
            
            if 36.5 <= t <= 39.5:
                theme = "emergency"
                dt = t - 36.5
                cam_shake_x = math.sin(dt * 80) * 25 * math.exp(-dt * 3)
                cam_shake_y = math.cos(dt * 90) * 20 * math.exp(-dt * 3)
            else:
                theme = "emerald"
                
            draw_studio_environment(ctx, t, theme, cam_shake_x, cam_shake_y)
            
            if t < 37.0:
                # Show Giant [DELETE] key
                draw_delete_button_vfx(ctx, t, is_pressed=is_pressed)
                draw_senior_dev(ctx, 340, FLOOR_Y - 140, scale=1.0, state={"pose": "press_button", "t": t})
            else:
                # Terminal screen with 5-line clean code
                draw_clean_code_terminal(ctx, t)
                
                # Comic Explosion sparks
                draw_comic_sparks(ctx, W/2 + 280, 420, scale=1.4 * (0.8 + 0.2*math.sin(t*16)), color=(1.0, 0.85, 0.0))
                draw_comic_sparks(ctx, W/2 - 280, 420, scale=1.4 * (0.8 + 0.2*math.sin(t*16)), color=(1.0, 0.35, 0.35))
                
                # Senior Dev calm with coffee, Junior Dev in jaw-drop shock
                draw_senior_dev(ctx, 320, FLOOR_Y - 140, scale=1.0, state={"pose": "stand_coffee", "t": t})
                draw_junior_dev(ctx, 800, FLOOR_Y - 140, scale=0.85, state={"pose": "shocked", "t": t})
                
            subtitle = "BOOM! 49.000 baris dihapus, sisa 5 baris super kencang!"
            
        # ---------------- SCENE 5: OUTRO & DUAL CTA (46.0 - 58.0s) ----------------
        else:
            theme = "emerald"
            draw_studio_environment(ctx, t, theme)
            draw_dual_outro_card(ctx, t)
            
            # Celebration confetti & stars falling
            for i in range(15):
                star_x = (i * 72 + int(t * 40)) % W
                star_y = (i * 130 + int(t * 120)) % H
                draw_star(ctx, star_x, star_y, 14, 6, (1.0, 0.85, 0.2))
                
            # Both characters celebrating
            draw_senior_dev(ctx, 280, FLOOR_Y - 140, scale=0.95, state={"pose": "stand_coffee", "t": t})
            draw_junior_dev(ctx, 800, FLOOR_Y - 140, scale=0.85, state={"pose": "happy", "t": t})
            
            subtitle = "Cek Ponytail di GitHub & boost produktivitas di floworkos.com!"
            
        # Subtitle Pill
        draw_subtitle_pill(ctx, subtitle, y=1740)
        
        # Watermark
        draw_flowork_watermark(ctx)
        
        # Capture contact frames
        if frame_idx in contact_indices:
            frame_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            f_ctx = cairo.Context(frame_surf)
            f_ctx.set_source_surface(surface, 0, 0)
            f_ctx.paint()
            contact_surfaces.append(frame_surf)
            
        # Pipe BGRA frame to FFmpeg
        data = surface.get_data()
        try:
            proc.stdin.write(data)
        except (BrokenPipeError, IOError):
            print(f"⚠️ Video pipe closed at frame {frame_idx}/{TOTAL_FRAMES}. Finalizing cleanly...")
            break
        
        if frame_idx % 90 == 0:
            print(f"Frame {frame_idx}/{TOTAL_FRAMES} ({frame_idx/TOTAL_FRAMES*100:.0f}%) rendered...")
            
    try:
        proc.stdin.close()
    except Exception:
        pass
    proc.wait()
    
    # Mirror video to user home
    subprocess.run(["cp", "-f", OUT_MP4, USER_OUT_MP4], check=True)
    print(f"✅ Video successfully rendered and mirrored to {USER_OUT_MP4}!")
    
    # ----------------- BUILD CONTACT SHEET (3x3 Grid) -----------------
    if contact_surfaces:
        cols, rows = 3, 3
        cell_w, cell_h = 360, 640
        sheet_w, sheet_h = cols * cell_w, rows * cell_h
        sheet_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, sheet_w, sheet_h)
        s_ctx = cairo.Context(sheet_surf)
        
        s_ctx.set_source_rgb(0.08, 0.09, 0.12)
        s_ctx.rectangle(0, 0, sheet_w, sheet_h)
        s_ctx.fill()
        
        for idx, f_surf in enumerate(contact_surfaces[:9]):
            r = idx // cols
            c = idx % cols
            s_ctx.save()
            s_ctx.translate(c * cell_w, r * cell_h)
            s_ctx.scale(cell_w / float(W), cell_h / float(H))
            s_ctx.set_source_surface(f_surf, 0, 0)
            s_ctx.paint()
            s_ctx.restore()
            
            # Frame border
            s_ctx.set_source_rgb(0.0, 1.0, 0.4)
            s_ctx.set_line_width(2)
            s_ctx.rectangle(c * cell_w, r * cell_h, cell_w, cell_h)
            s_ctx.stroke()
            
        sheet_surf.write_to_png(CONTACT_SHEET_PNG)
        subprocess.run(["cp", "-f", CONTACT_SHEET_PNG, USER_CONTACT_SHEET_PNG], check=True)
        print(f"📸 Contact sheet generated at {CONTACT_SHEET_PNG}!")

if __name__ == "__main__":
    render_ponytail_cartoon()
