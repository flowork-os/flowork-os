#!/usr/bin/env python3
"""
MR. FLOW 10-SECOND HIGH-RETENTION CARTOON SHORT (VERTICAL 9:16)
Reverse-Engineered from @RicksClips3000 Animation Language:
- 100% Pure Action Cartoon (moving every second, NO static slide templates!)
- Rubber-Hose Bezier Limbs, Squash & Stretch Physics, Cartoon Anticipation & Overshoot
- Dynamic Face Rig: Eyebrow tilts, animated mouth phonemes, eye glance & wink
- Interactive Cartoon Props: Giant hammer, pesky red memory bug, comic impact explosion
- Zero-Clipping Safe Area Framing (Vertical 1080x1920)
- High-Energy Broadcast Audio with Vocal Compression & Procedural SFX
"""

import os, sys, math, subprocess
import cairo
import numpy as np

W, H = 1080, 1920
FPS = 60
DURATION = 10.0
TOTAL_FRAMES = int(DURATION * FPS)
FLOOR_Y = 1460

OUT_DIR = "/opt/floworkos/documents/videos/cartoon-short-10s"
USER_OUT_DIR = os.path.expanduser("~/Documents/videos/cartoon-short-10s")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(USER_OUT_DIR, exist_ok=True)

OUT_MP4 = os.path.join(OUT_DIR, "MR_FLOW_CARTOON_SHORT_10S.mp4")
CONTACT_SHEET_PNG = os.path.join(OUT_DIR, "MR_FLOW_CARTOON_SHORT_10S_contact_sheet.png")
AUDIO_WAV = "/tmp/short_final_audio.wav"

def ease_out_bounce(x):
    n1 = 7.5625
    d1 = 2.75
    if x < 1 / d1:
        return n1 * x * x
    elif x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    elif x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    else:
        x -= 2.625 / d1
        return n1 * x * x + 0.984375

def draw_background(ctx, t, cam_shake_x=0, cam_shake_y=0):
    ctx.save()
    ctx.translate(cam_shake_x, cam_shake_y)
    
    # 1. Warm Cartoon Wall (Kraft/Clay gradient - strictly non-white)
    pat = cairo.LinearGradient(0, 0, 0, H)
    pat.add_color_stop_rgb(0.0, 0.94, 0.91, 0.86) # #efe8dc
    pat.add_color_stop_rgb(1.0, 0.86, 0.82, 0.75) # #dcd1c0
    ctx.set_source(pat)
    ctx.paint()
    
    # 2. Floor Line & Baseboard
    ctx.set_source_rgb(0.48, 0.44, 0.38)
    ctx.rectangle(0, FLOOR_Y - 25, W, 25) # Baseboard
    ctx.fill()
    ctx.set_source_rgb(0.28, 0.25, 0.22)
    ctx.set_line_width(4)
    ctx.move_to(0, FLOOR_Y - 25)
    ctx.line_to(W, FLOOR_Y - 25)
    ctx.stroke()
    
    # Floor surface
    ctx.set_source_rgb(0.79, 0.74, 0.66)
    ctx.rectangle(0, FLOOR_Y, W, H - FLOOR_Y)
    ctx.fill()
    
    # Perspective Floor Planks
    ctx.set_source_rgba(0.62, 0.58, 0.50, 0.4)
    ctx.set_line_width(4)
    for px in range(-200, W + 400, 220):
        ctx.move_to(px, FLOOR_Y)
        ctx.line_to(px - 180, H)
        ctx.stroke()
        
    # Volumetric Sunlight Ray (Rick's Clips Style Frame 01)
    ctx.save()
    ray = cairo.LinearGradient(W, 0, 0, FLOOR_Y + 100)
    ray.add_color_stop_rgba(0.0, 1.0, 1.0, 1.0, 0.38)
    ray.add_color_stop_rgba(0.7, 1.0, 1.0, 1.0, 0.08)
    ray.add_color_stop_rgba(1.0, 1.0, 1.0, 1.0, 0.0)
    ctx.set_source(ray)
    ctx.move_to(W - 80, 0)
    ctx.line_to(W, 0)
    ctx.line_to(W, 260)
    ctx.line_to(180, FLOOR_Y + 120)
    ctx.line_to(30, FLOOR_Y + 120)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    
    # Cartoon background prop: Server Cabinet in the corner
    ctx.save()
    ctx.set_source_rgb(0.20, 0.22, 0.27)
    ctx.rectangle(70, FLOOR_Y - 480, 200, 480)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.12, 0.13, 0.16)
    ctx.set_line_width(6)
    ctx.stroke()
    # Rack vents & blinking LEDs
    for row in range(5):
        ry = FLOOR_Y - 440 + row * 85
        ctx.set_source_rgb(0.15, 0.16, 0.20)
        ctx.rectangle(85, ry, 170, 70)
        ctx.fill()
        # Blinking LEDs
        led_color = (0.0, 1.0, 0.4) if math.sin(t * 8.0 + row) > 0 else (0.2, 0.4, 0.2)
        ctx.set_source_rgb(*led_color)
        ctx.arc(105, ry + 35, 6, 0, 2*math.pi)
        ctx.fill()
    ctx.restore()
    
    ctx.restore()

def draw_memory_bug(ctx, x, y, state="alive", t=0):
    """Goofy red cartoon memory leak bug creature"""
    ctx.save()
    ctx.translate(x, y)
    
    if state == "alive":
        # Wiggling legs & body
        wiggle = math.sin(t * 16.0) * 4.0
        squish = 1.0 + math.sin(t * 12.0) * 0.08
        ctx.scale(squish, 1.0 / squish)
        
        # Legs
        ctx.set_source_rgb(0.15, 0.15, 0.15)
        ctx.set_line_width(5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for side in [-1, 1]:
            for i in range(3):
                lx = side * (25 + i * 8)
                ly = -5 + i * 8 + (wiggle if i % 2 == 0 else -wiggle) * side
                ctx.move_to(0, ly)
                ctx.curve_to(side * 20, ly - 10, side * 35, ly + 5, lx, ly + 14)
                ctx.stroke()
                
        # Red round bug body
        ctx.set_source_rgb(0.92, 0.22, 0.24)
        ctx.arc(0, 0, 28, 0, 2*math.pi)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.15, 0.15, 0.15)
        ctx.set_line_width(4)
        ctx.stroke()
        
        # Big silly cartoon bug eyes
        for ex in [-12, 12]:
            ctx.set_source_rgb(1, 1, 1)
            ctx.arc(ex, -12, 9, 0, 2*math.pi)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.1, 0.1, 0.1)
            ctx.stroke()
            # Pupil looking up nervously at Mr. Flow
            ctx.arc(ex - 2, -15, 4.5, 0, 2*math.pi)
            ctx.fill()
            
        # Antennae
        ctx.set_line_width(3)
        ctx.move_to(-8, -25)
        ctx.curve_to(-18, -45 + wiggle, -25, -40, -22, -48)
        ctx.stroke()
        ctx.move_to(8, -25)
        ctx.curve_to(18, -45 - wiggle, 25, -40, 22, -48)
        ctx.stroke()
        
    elif state == "squashed":
        # Completely flattened like a comic pancake
        ctx.scale(2.2, 0.15)
        ctx.set_source_rgb(0.92, 0.22, 0.24)
        ctx.arc(0, 0, 30, 0, 2*math.pi)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.1, 0.1, 0.1)
        ctx.set_line_width(6)
        ctx.stroke()
        # Crossed X eyes
        ctx.restore()
        ctx.save()
        ctx.translate(x, y - 5)
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_line_width(4)
        for ex in [-22, 22]:
            ctx.move_to(ex - 6, -6); ctx.line_to(ex + 6, 6); ctx.stroke()
            ctx.move_to(ex + 6, -6); ctx.line_to(ex - 6, 6); ctx.stroke()
            
    ctx.restore()

def draw_comic_sparks(ctx, x, y, radius, t_progress):
    """Cartoon starburst explosion impact"""
    if t_progress < 0 or t_progress > 1.0:
        return
    ctx.save()
    ctx.translate(x, y)
    scale = max(0.001, (1.0 - (1.0 - t_progress)**3) * 1.5)
    ctx.scale(scale, scale)
    alpha = max(0.0, min(1.0, 1.0 - t_progress * 1.2))
    
    # Yellow / Orange starburst
    ctx.set_source_rgba(1.0, 0.85, 0.1, alpha * 0.9)
    num_points = 12
    ctx.new_path()
    for i in range(num_points * 2):
        ang = i * math.pi / num_points
        r = radius * 1.1 if i % 2 == 0 else radius * 0.45
        px = math.cos(ang) * r
        py = math.sin(ang) * r
        if i == 0: ctx.move_to(px, py)
        else: ctx.line_to(px, py)
    ctx.close_path()
    ctx.fill()
    
    # Matrix Green inner core
    ctx.set_source_rgba(0.0, 1.0, 0.4, alpha)
    ctx.arc(0, 0, radius * 0.35, 0, 2*math.pi)
    ctx.fill()
    
    # Electric lightning bolts shooting out
    ctx.set_source_rgba(0.2, 1.0, 0.5, alpha)
    ctx.set_line_width(6)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for ang in [0.3, 1.2, 2.1, 3.4, 4.5, 5.3]:
        r1 = radius * 0.5
        r2 = radius * 1.4
        mx = (r1 + r2) / 2 + (math.sin(ang * 5) * 25)
        ctx.move_to(math.cos(ang) * r1, math.sin(ang) * r1)
        ctx.line_to(math.cos(ang + 0.1) * mx, math.sin(ang + 0.1) * mx)
        ctx.line_to(math.cos(ang) * r2, math.sin(ang) * r2)
        ctx.stroke()
        
    ctx.restore()

def draw_mr_flow_cartoon(ctx, x, y, scale=1.0, state=None):
    """
    Mr. Flow Full Cartoon Actor Rig:
    - Rubber-hose limbs
    - Squash & Stretch body scaling
    - Expressive face rig (eyebrows, eyes, dynamic talking mouth)
    - Dark Obsidian capsule hoodie with permanent MATRIX GREEN FLOWORKOS.COM
    """
    if state is None:
        state = {}
        
    pose = state.get("pose", "idle")
    t = state.get("t", 0.0)
    squash_x = state.get("squash_x", 1.0)
    squash_y = state.get("squash_y", 1.0)
    brow_state = state.get("brow", "normal")
    eye_state = state.get("eye", "normal")
    mouth_state = state.get("mouth", "smile")
    is_talking = state.get("talk", False)
    has_hammer = state.get("hammer", False)
    hammer_angle = state.get("hammer_angle", 0.0)
    hoodie_glow = state.get("glow", 0.0)
    
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale * squash_x, scale * squash_y)
    
    # Drop shadow on floor
    shadow_w = 110 * squash_x
    ctx.save()
    ctx.set_source_rgba(0.18, 0.16, 0.14, 0.28)
    ctx.scale(1.0, 0.28)
    shadow_y_rel = (FLOOR_Y - y) / (scale * squash_y * 0.28)
    ctx.arc(0, shadow_y_rel, shadow_w, 0, 2*math.pi)
    ctx.fill()
    ctx.restore()
    
    # Kinetic parameters per pose
    hip_y = 0
    torso_y = hip_y - 80
    head_y = torso_y - 120
    
    # 1. LEGS & FEET (Rubber Hose)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(16)
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    
    floor_rel = (FLOOR_Y - y) / (scale * squash_y)
    
    if pose == "walk":
        # Dynamic cartoon walk cycle
        stride = math.sin(t * 12.0)
        l_foot_y = floor_rel - max(0, -stride * 35.0)
        r_foot_y = floor_rel - max(0, stride * 35.0)
        l_foot_x = -stride * 55.0
        r_foot_x = stride * 55.0
        
        # Left leg
        ctx.move_to(-25, hip_y)
        ctx.curve_to(-35, hip_y + 60, l_foot_x - 10, l_foot_y - 40, l_foot_x, l_foot_y)
        ctx.stroke()
        # Left foot
        ctx.move_to(l_foot_x, l_foot_y); ctx.line_to(l_foot_x - 30, l_foot_y); ctx.stroke()
        
        # Right leg
        ctx.move_to(25, hip_y)
        ctx.curve_to(35, hip_y + 60, r_foot_x + 10, r_foot_y - 40, r_foot_x, r_foot_y)
        ctx.stroke()
        # Right foot
        ctx.move_to(r_foot_x, r_foot_y); ctx.line_to(r_foot_x + 30, r_foot_y); ctx.stroke()
        
    elif pose in ["jump_swing", "crouch"]:
        # Tucked or crouched legs
        ctx.move_to(-28, hip_y)
        ctx.curve_to(-65, hip_y + 40, -50, floor_rel - 10, -35, floor_rel)
        ctx.stroke()
        ctx.move_to(28, hip_y)
        ctx.curve_to(65, hip_y + 40, 50, floor_rel - 10, 35, floor_rel)
        ctx.stroke()
        # Feet flat
        ctx.move_to(-35, floor_rel); ctx.line_to(-65, floor_rel); ctx.stroke()
        ctx.move_to(35, floor_rel); ctx.line_to(65, floor_rel); ctx.stroke()
        
    else: # idle, lean_point, shrug, triumphant
        # Standing firm with slight hip breathing
        ctx.move_to(-25, hip_y)
        ctx.curve_to(-40, hip_y + 70, -45, floor_rel - 30, -50, floor_rel)
        ctx.stroke()
        ctx.move_to(-50, floor_rel); ctx.line_to(-80, floor_rel); ctx.stroke()
        
        ctx.move_to(25, hip_y)
        ctx.curve_to(40, hip_y + 70, 45, floor_rel - 30, 50, floor_rel)
        ctx.stroke()
        ctx.move_to(50, floor_rel); ctx.line_to(80, floor_rel); ctx.stroke()
        
    # 2. TORSO: Obsidian Pill Hoodie
    rw, rh, rrad = 140, 170, 50
    rx = -rw / 2
    ry = torso_y - rh / 2 + 10
    
    ctx.save()
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    ctx.new_sub_path()
    ctx.arc(rx + rw - rrad, ry + rrad, rrad, -math.pi/2, 0)
    ctx.arc(rx + rw - rrad, ry + rh - rrad, rrad, 0, math.pi/2)
    ctx.arc(rx + rrad, ry + rh - rrad, rrad, math.pi/2, math.pi)
    ctx.arc(rx + rrad, ry + rrad, rrad, math.pi, 3*math.pi/2)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0.04, 0.04, 0.06)
    ctx.set_line_width(6)
    ctx.stroke()
    
    # Kangaroo Pocket
    ctx.set_source_rgb(0.13, 0.14, 0.18)
    ctx.arc(0, ry + rh - 22, 42, 0.2, math.pi - 0.2)
    ctx.stroke()
    
    # CHEST BRANDING: Permanent High-Luminance Matrix Green Stacked (FLOWORKOS / .COM)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    
    # Line 1: FLOWORKOS
    ctx.set_font_size(15.0)
    ext1 = ctx.text_extents("FLOWORKOS")
    bx1 = -ext1.width / 2
    by1 = ry + 52
    
    # Line 2: .COM (Slightly smaller, centered underneath)
    ctx.set_font_size(12.5)
    ext2 = ctx.text_extents(".COM")
    bx2 = -ext2.width / 2
    by2 = ry + 70
    
    # Pulsating glow
    glow_val = 0.35 + 0.35 * math.sin(t * 10.0) + hoodie_glow * 0.6
    ctx.set_source_rgba(0.0, 1.0, 0.4, min(1.0, glow_val))
    for ox, oy in [(-1.5,0),(1.5,0),(0,-1.5),(0,1.5)]:
        ctx.move_to(bx1 + ox, by1 + oy)
        ctx.show_text("FLOWORKOS")
        ctx.move_to(bx2 + ox, by2 + oy)
        ctx.show_text(".COM")
        
    ctx.set_source_rgb(0.0, 1.0, 0.4) # Matrix green
    ctx.move_to(bx1, by1)
    ctx.show_text("FLOWORKOS")
    ctx.move_to(bx2, by2)
    ctx.show_text(".COM")
    ctx.restore()
    
    # 3. RUBBER-HOSE ARMS & PROPS
    ctx.set_line_width(15)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    
    if pose == "walk":
        arm_swing = math.cos(t * 12.0) * 45.0
        # Left arm
        ctx.move_to(-55, torso_y - 40)
        ctx.curve_to(-80, torso_y, -90 - arm_swing, torso_y + 40, -75 - arm_swing, torso_y + 80)
        ctx.stroke()
        ctx.arc(-75 - arm_swing, torso_y + 80, 14, 0, 2*math.pi); ctx.fill()
        # Right arm
        ctx.move_to(55, torso_y - 40)
        ctx.curve_to(80, torso_y, 90 + arm_swing, torso_y + 40, 75 + arm_swing, torso_y + 80)
        ctx.stroke()
        ctx.arc(75 + arm_swing, torso_y + 80, 14, 0, 2*math.pi); ctx.fill()
        
    elif pose == "lean_point":
        # Left arm on hip
        ctx.move_to(-55, torso_y - 40)
        ctx.curve_to(-105, torso_y - 20, -115, torso_y + 20, -75, torso_y + 35)
        ctx.stroke()
        ctx.arc(-75, torso_y + 35, 14, 0, 2*math.pi); ctx.fill()
        
        # Right arm pointing forward aggressively at viewer
        ctx.move_to(55, torso_y - 40)
        ctx.curve_to(110, torso_y - 50, 150, torso_y - 20, 175, torso_y + 10)
        ctx.stroke()
        # Pointing hand
        ctx.arc(175, torso_y + 10, 16, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(10)
        ctx.move_to(175, torso_y + 10); ctx.line_to(205, torso_y + 10); ctx.stroke()
        ctx.set_line_width(15)
        
    elif pose == "shrug_question":
        # Both hands raised up in comical disbelief
        shrug_wave = math.sin(t * 14.0) * 8.0
        ctx.move_to(-55, torso_y - 30)
        ctx.curve_to(-110, torso_y - 60, -130, torso_y - 120 + shrug_wave, -115, torso_y - 150 + shrug_wave)
        ctx.stroke()
        ctx.arc(-115, torso_y - 150 + shrug_wave, 16, 0, 2*math.pi); ctx.fill()
        
        ctx.move_to(55, torso_y - 30)
        ctx.curve_to(110, torso_y - 60, 130, torso_y - 120 - shrug_wave, 115, torso_y - 150 - shrug_wave)
        ctx.stroke()
        ctx.arc(115, torso_y - 150 - shrug_wave, 16, 0, 2*math.pi); ctx.fill()
        
    elif pose in ["crouch", "jump_swing", "smash_down"]:
        # Giant Comic Hammer Interaction
        if has_hammer:
            ctx.save()
            hx = 45 if pose != "smash_down" else 85
            hy = torso_y - 140 if pose == "jump_swing" else (torso_y + 20 if pose == "smash_down" else torso_y - 20)
            ctx.translate(hx, hy)
            ctx.rotate(hammer_angle)
            
            # Wooden handle
            ctx.set_source_rgb(0.55, 0.35, 0.18)
            ctx.set_line_width(16)
            ctx.move_to(0, 100); ctx.line_to(0, -160); ctx.stroke()
            # Giant Iron Sledge Block
            ctx.set_source_rgb(0.22, 0.25, 0.32)
            ctx.rectangle(-75, -230, 150, 90)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.10, 0.11, 0.14)
            ctx.set_line_width(8)
            ctx.stroke()
            # Matrix Green Lightning Core on Hammer
            ctx.set_source_rgb(0.0, 1.0, 0.4)
            ctx.rectangle(-60, -195, 120, 20)
            ctx.fill()
            ctx.restore()
            
        # Arms holding hammer
        if pose == "jump_swing":
            ctx.move_to(-55, torso_y - 40)
            ctx.curve_to(-30, torso_y - 120, 20, torso_y - 160, 45, torso_y - 140)
            ctx.stroke()
            ctx.move_to(55, torso_y - 40)
            ctx.curve_to(65, torso_y - 100, 55, torso_y - 130, 45, torso_y - 140)
            ctx.stroke()
            ctx.arc(45, torso_y - 140, 16, 0, 2*math.pi); ctx.fill()
        elif pose == "smash_down":
            ctx.move_to(-55, torso_y - 20)
            ctx.curve_to(-20, torso_y + 20, 50, torso_y + 40, 85, torso_y + 20)
            ctx.stroke()
            ctx.move_to(55, torso_y - 20)
            ctx.curve_to(70, torso_y, 80, torso_y + 10, 85, torso_y + 20)
            ctx.stroke()
            ctx.arc(85, torso_y + 20, 16, 0, 2*math.pi); ctx.fill()
            
    elif pose == "triumphant":
        # Double Thumbs-Up
        for side in [-1, 1]:
            ctx.move_to(side * 55, torso_y - 30)
            ctx.curve_to(side * 95, torso_y - 60, side * 115, torso_y - 70, side * 95, torso_y - 110)
            ctx.stroke()
            ctx.arc(side * 95, torso_y - 110, 16, 0, 2*math.pi); ctx.fill()
            ctx.set_line_width(10)
            ctx.move_to(side * 95, torso_y - 110); ctx.line_to(side * 95, torso_y - 135); ctx.stroke()
            ctx.set_line_width(15)
            
    # 4. HEAD (Cream Cartoon Oval with Thick Outline)
    ctx.save()
    ctx.set_source_rgb(0.98, 0.98, 0.98)
    ctx.scale(1.0, 1.08)
    ctx.arc(0, head_y / 1.08, 68, 0, 2*math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    ctx.set_line_width(7)
    ctx.stroke()
    ctx.restore()
    
    # 5. DYNAMIC CARTOON FACE RIG
    ctx.set_line_width(6.5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    
    if brow_state == "skeptical":
        ctx.move_to(-46, head_y - 42); ctx.curve_to(-30, head_y - 58, -15, head_y - 52, -5, head_y - 44); ctx.stroke()
        ctx.move_to(10, head_y - 36); ctx.curve_to(25, head_y - 42, 40, head_y - 34, 48, head_y - 26); ctx.stroke()
    elif brow_state == "incredulous":
        ctx.move_to(-45, head_y - 50); ctx.curve_to(-30, head_y - 64, -15, head_y - 64, -5, head_y - 50); ctx.stroke()
        ctx.move_to(5, head_y - 50); ctx.curve_to(15, head_y - 64, 30, head_y - 64, 45, head_y - 50); ctx.stroke()
    elif brow_state == "intense_smash":
        ctx.move_to(-45, head_y - 45); ctx.curve_to(-30, head_y - 38, -15, head_y - 28, -5, head_y - 24); ctx.stroke()
        ctx.move_to(5, head_y - 24); ctx.curve_to(15, head_y - 28, 30, head_y - 38, 45, head_y - 45); ctx.stroke()
    else:
        ctx.move_to(-42, head_y - 40); ctx.curve_to(-28, head_y - 50, -15, head_y - 48, -6, head_y - 38); ctx.stroke()
        ctx.move_to(6, head_y - 38); ctx.curve_to(15, head_y - 48, 28, head_y - 50, 42, head_y - 40); ctx.stroke()
        
    blink = ((t * 2.5) % 3.6 > 3.42)
    if eye_state == "wink":
        ctx.move_to(-35, head_y - 18); ctx.curve_to(-24, head_y - 26, -15, head_y - 26, -5, head_y - 18); ctx.stroke()
        ctx.arc(25, head_y - 16, 12, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgb(1, 1, 1); ctx.arc(28, head_y - 19, 4, 0, 2*math.pi); ctx.fill()
    elif blink:
        ctx.move_to(-34, head_y - 18); ctx.line_to(-14, head_y - 18); ctx.stroke()
        ctx.move_to(14, head_y - 18); ctx.line_to(34, head_y - 18); ctx.stroke()
    else:
        ctx.arc(-24, head_y - 18, 11, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgb(1, 1, 1); ctx.arc(-21, head_y - 21, 3.5, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgb(0.10, 0.11, 0.14)
        ctx.arc(24, head_y - 18, 11, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgb(1, 1, 1); ctx.arc(27, head_y - 21, 3.5, 0, 2*math.pi); ctx.fill()
        
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    if is_talking:
        talk_cycle = abs(math.sin(t * 14.0))
        m_h = 16 + talk_cycle * 26
        ctx.save()
        ctx.move_to(-24, head_y + 16)
        ctx.line_to(24, head_y + 16)
        ctx.curve_to(24, head_y + 16 + m_h, -24, head_y + 16 + m_h, -24, head_y + 16)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.stroke()
        ctx.clip()
        ctx.set_source_rgb(0.95, 0.35, 0.45)
        ctx.arc(0, head_y + 16 + m_h, 18, 0, 2*math.pi); ctx.fill()
        ctx.restore()
    elif mouth_state == "grit_teeth":
        ctx.save()
        ctx.rectangle(-28, head_y + 16, 56, 22)
        ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve()
        ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(4); ctx.stroke()
        for tx in [-14, 0, 14]:
            ctx.move_to(tx, head_y + 16); ctx.line_to(tx, head_y + 38); ctx.stroke()
        ctx.move_to(-28, head_y + 27); ctx.line_to(28, head_y + 27); ctx.stroke()
        ctx.restore()
    elif mouth_state == "gasp_o":
        ctx.save()
        ctx.arc(0, head_y + 28, 16, 0, 2*math.pi)
        ctx.fill()
        ctx.restore()
    else:
        ctx.save()
        ctx.move_to(-24, head_y + 18)
        ctx.curve_to(-12, head_y + 36, 12, head_y + 36, 24, head_y + 18)
        ctx.set_line_width(5); ctx.stroke()
        ctx.restore()
        
    ctx.restore()

def draw_subtitle_pill(ctx, text, y=1700):
    if not text:
        return
    ctx.save()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(60)
    ext = ctx.text_extents(text)
    sx = (W - ext.width) / 2
    sy = y
    
    ctx.set_source_rgb(0.04, 0.04, 0.06)
    ctx.set_line_width(14)
    ctx.move_to(sx, sy)
    ctx.text_path(text)
    ctx.stroke()
    
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(sx, sy)
    ctx.show_text(text)
    ctx.restore()

def render_cartoon_short():
    print(f"🎬 Starting Render: 10-Second Cartoon Short @ {FPS} FPS ({TOTAL_FRAMES} frames)...")
    
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
        "-cq", "19",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUT_MP4
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    
    contact_frame_indices = [int(TOTAL_FRAMES * i / 8) for i in range(8)]
    contact_surfaces = []
    
    for f in range(TOTAL_FRAMES):
        t = f / FPS
        
        cam_shake_x = 0
        cam_shake_y = 0
        bug_state = "alive"
        bug_x, bug_y = 760, FLOOR_Y - 14
        sparks_t = -1.0
        subtitle = ""
        
        if t < 2.0:
            p = min(1.0, t / 1.6)
            char_x = -150 + p * (540 - (-150))
            char_y = FLOOR_Y - 260
            pose = "walk" if t < 1.6 else "lean_point"
            brow = "skeptical"
            eye = "normal"
            mouth = "talk_open"
            talk = True
            squash_x, squash_y = 1.0, 1.0
            hammer = False
            hammer_angle = 0
            glow = 0.0
            subtitle = "STOP RIGHT THERE!" if t > 0.4 else ""
            
        elif t < 4.4:
            char_x = 540
            char_y = FLOOR_Y - 260
            pose = "shrug_question"
            brow = "incredulous"
            eye = "glance_side"
            mouth = "talk_open"
            talk = True
            squash_x = 1.0 + math.sin(t * 8.0) * 0.04
            squash_y = 1.0 - math.sin(t * 8.0) * 0.04
            hammer = False
            hammer_angle = 0
            glow = 0.0
            subtitle = "BLOATED CODE?"
            
        elif t < 5.4:
            char_x = 540
            c_p = min(1.0, (t - 4.4) / 0.8)
            squash_y = 1.0 - c_p * 0.32
            squash_x = 1.0 + c_p * 0.35
            char_y = FLOOR_Y - 260 + c_p * 80
            pose = "crouch"
            brow = "intense_smash"
            eye = "normal"
            mouth = "grit_teeth"
            talk = False
            hammer = True
            hammer_angle = -0.4 - c_p * 0.8
            glow = 0.4
            subtitle = "WATCH THIS!"
            
        elif t < 6.2:
            jump_p = (t - 5.4) / 0.8
            squash_y = 1.38
            squash_x = 0.74
            char_x = 540 + jump_p * 160
            char_y = FLOOR_Y - 260 - math.sin(jump_p * math.pi) * 360
            pose = "jump_swing"
            brow = "intense_smash"
            eye = "normal"
            mouth = "grit_teeth"
            talk = False
            hammer = True
            hammer_angle = -1.2 + jump_p * 2.8
            glow = 0.8
            subtitle = "WATCH THIS!"
            
        elif t < 7.4:
            dt_smash = t - 6.2
            char_x = 700
            char_y = FLOOR_Y - 260
            pose = "smash_down"
            brow = "intense_smash"
            eye = "normal"
            mouth = "grit_teeth"
            talk = False
            hammer = True
            hammer_angle = 1.6
            glow = 1.0
            bug_state = "squashed"
            
            cam_shake_x = math.sin(dt_smash * 75.0) * 32.0 * math.exp(-dt_smash * 6.0)
            cam_shake_y = math.cos(dt_smash * 85.0) * 28.0 * math.exp(-dt_smash * 6.0)
            sparks_t = dt_smash / 0.9
            subtitle = "MR. FLOW SMASHES!"
            
        else:
            dt_outro = t - 7.4
            char_x = 640
            char_y = FLOOR_Y - 260
            pose = "triumphant"
            brow = "happy"
            eye = "wink" if dt_outro > 0.8 else "normal"
            mouth = "smile"
            talk = (dt_outro < 1.2)
            bounce = math.sin(dt_outro * 14.0) * math.exp(-dt_outro * 4.0) * 0.12
            squash_x = 1.0 - bounce
            squash_y = 1.0 + bounce
            hammer = False
            hammer_angle = 0
            glow = 1.0
            bug_state = "squashed"
            subtitle = "PURE LIGHTNING!"
            
        draw_background(ctx, t, cam_shake_x, cam_shake_y)
        draw_memory_bug(ctx, bug_x + cam_shake_x, bug_y + cam_shake_y, state=bug_state, t=t)
        
        if sparks_t >= 0:
            draw_comic_sparks(ctx, bug_x + cam_shake_x, bug_y - 20 + cam_shake_y, 220, sparks_t)
            
        actor_state = {
            "pose": pose, "t": t,
            "squash_x": squash_x, "squash_y": squash_y,
            "brow": brow, "eye": eye, "mouth": mouth,
            "talk": talk, "hammer": hammer, "hammer_angle": hammer_angle,
            "glow": glow
        }
        draw_mr_flow_cartoon(ctx, char_x + cam_shake_x, char_y + cam_shake_y, scale=1.55, state=actor_state)
        draw_subtitle_pill(ctx, subtitle, y=1720)
        
        surface.flush()
        raw_data = surface.get_data()
        proc.stdin.write(raw_data)
        
        if f in contact_frame_indices:
            snapshot = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            s_ctx = cairo.Context(snapshot)
            s_ctx.set_source_surface(surface, 0, 0)
            s_ctx.paint()
            contact_surfaces.append(snapshot)
            
        if (f + 1) % 60 == 0:
            print(f"  Frame {f+1}/{TOTAL_FRAMES} ({(f+1)/TOTAL_FRAMES*100:.0f}%) rendered...")
            
    proc.stdin.close()
    proc.wait()
    print("✅ Video encoded successfully with NVENC!")
    
    print("📸 Creating 8-frame contact sheet...")
    cs_w, cs_h = 2160, 1920
    cs_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, cs_w, cs_h)
    cs_ctx = cairo.Context(cs_surface)
    cs_ctx.set_source_rgb(0.12, 0.13, 0.16)
    cs_ctx.paint()
    
    thumb_w, thumb_h = int(cs_w / 4), int(cs_h / 2)
    for idx, snap in enumerate(contact_surfaces[:8]):
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
        cs_ctx.rectangle(x, y, thumb_w, thumb_h)
        cs_ctx.stroke()
        
        cs_ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cs_ctx.set_font_size(32)
        cs_ctx.set_source_rgb(1, 1, 1)
        cs_ctx.move_to(x + 20, y + 45)
        cs_ctx.show_text(f"t = {idx * 1.25:.1f}s")
        
    cs_surface.write_to_png(CONTACT_SHEET_PNG)
    print(f"📸 Contact sheet saved to {CONTACT_SHEET_PNG}!")
    
    subprocess.run(["cp", "-f", OUT_MP4, USER_OUT_DIR], check=True)
    subprocess.run(["cp", "-f", CONTACT_SHEET_PNG, USER_OUT_DIR], check=True)
    print(f"📁 Video & Contact Sheet copied to {USER_OUT_DIR}!")

if __name__ == "__main__":
    render_cartoon_short()
