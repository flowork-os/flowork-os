#!/usr/bin/env python3
"""
AI AGENT OFFICE - 58-SECOND HIGH-RETENTION CARTOON SHORT (VERTICAL 9:16)
Official Repository Showcase: https://github.com/flowork-os/ai-agent-office
- 100% Pure Cartoon Action Animation (Active physics every second, NO slide templates!)
- Reverse-engineered from @RicksClips3000: Rubber-hose limbs, squash/stretch, over-the-top gags
- Detik Pertama: Catchy centered Cartoon Hook Title ("STOP CHATTING WITH AI! I HIRED AN ENTIRE AI AGENT OFFICE!")
  visible immediately from t = 0.0s with pulse and elastic entrance.
- Real Screenshots: Embedded GitHub repository screenshot & 3D virtual office cover
- Prominent Dual CTA: Direct links to github.com/flowork-os/ai-agent-office and floworkos.com
- Stacked chest branding: FLOWORKOS on top, .COM underneath in Matrix Green (#00FF66)
- High-energy broadcast voiceover with procedural cartoon soundtrack and sound effects
- Zero Unicode Tofu Boxes: Uses pure procedural vector stars and symbols
"""

import os, sys, math, subprocess, json
import cairo
import numpy as np

W, H = 1080, 1920
FPS = 60
DURATION = 58.0
TOTAL_FRAMES = int(DURATION * FPS)
FLOOR_Y = 1460

OUT_DIR = "/opt/floworkos/documents/videos/ai-agent-office-short"
USER_OUT_DIR = os.path.expanduser("~/Documents/videos/ai-agent-office-short")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(USER_OUT_DIR, exist_ok=True)

OUT_MP4 = os.path.join(OUT_DIR, "AI_AGENT_OFFICE_CARTOON_SHORT_60S.mp4")
CONTACT_SHEET_PNG = os.path.join(OUT_DIR, "AI_AGENT_OFFICE_CARTOON_SHORT_60S_contact_sheet.png")
AUDIO_WAV = "/tmp/office_repo_final_audio.wav"
REPO_IMG_PATH = "/tmp/repo_assets/github_repo_card.png"
COVER_IMG_PATH = "/tmp/repo_assets/cover.png"

# Preload image surfaces
REPO_SURF = None
COVER_SURF = None
if os.path.exists(REPO_IMG_PATH):
    try:
        REPO_SURF = cairo.ImageSurface.create_from_png(REPO_IMG_PATH)
    except Exception as e:
        print(f"Warning: Could not load {REPO_IMG_PATH}: {e}")

if os.path.exists(COVER_IMG_PATH):
    try:
        COVER_SURF = cairo.ImageSurface.create_from_png(COVER_IMG_PATH)
    except Exception as e:
        print(f"Warning: Could not load {COVER_IMG_PATH}: {e}")

def draw_star(ctx, cx, cy, r_outer=18, r_inner=8, color=(1.0, 0.85, 0.0)):
    """Procedural 5-pointed star graphic (Zero font/tofu box dependencies)"""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.set_source_rgb(*color)
    ctx.new_sub_path()
    for i in range(10):
        ang = -math.pi/2 + i * (math.pi / 5)
        r = r_outer if i % 2 == 0 else r_inner
        x = r * math.cos(ang)
        y = r * math.sin(ang)
        if i == 0: ctx.move_to(x, y)
        else: ctx.line_to(x, y)
    ctx.close_path()
    ctx.fill()
    ctx.restore()

def draw_wall_and_floor(ctx, t, bg_type="office", cam_shake_x=0, cam_shake_y=0):
    ctx.save()
    ctx.translate(cam_shake_x, cam_shake_y)
    
    pat = cairo.LinearGradient(0, 0, 0, H)
    if bg_type == "dark_room":
        pat.add_color_stop_rgb(0.0, 0.18, 0.19, 0.24)
        pat.add_color_stop_rgb(1.0, 0.10, 0.11, 0.15)
    else: # architectural warm cream
        pat.add_color_stop_rgb(0.0, 0.95, 0.92, 0.88) # #f5ebe1
        pat.add_color_stop_rgb(1.0, 0.88, 0.84, 0.78)
    ctx.set_source(pat)
    ctx.paint()
    
    # Baseboard
    base_color = (0.12, 0.13, 0.16) if bg_type == "dark_room" else (0.45, 0.40, 0.35)
    ctx.set_source_rgb(*base_color)
    ctx.rectangle(0, FLOOR_Y - 25, W, 25)
    ctx.fill()
    
    # Floor surface
    floor_color = (0.24, 0.22, 0.26) if bg_type == "dark_room" else (0.80, 0.74, 0.65)
    ctx.set_source_rgb(*floor_color)
    ctx.rectangle(0, FLOOR_Y, W, H - FLOOR_Y)
    ctx.fill()
    
    # Perspective Floor Planks
    plank_color = (0.18, 0.16, 0.20, 0.4) if bg_type == "dark_room" else (0.64, 0.58, 0.48, 0.4)
    ctx.set_source_rgba(*plank_color)
    ctx.set_line_width(4)
    for px in range(-200, W + 400, 220):
        ctx.move_to(px, FLOOR_Y)
        ctx.line_to(px - 180, H)
        ctx.stroke()
        
    # Volumetric sunlight ray
    if bg_type != "dark_room":
        ctx.save()
        ray = cairo.LinearGradient(W, 0, 0, FLOOR_Y + 100)
        ray.add_color_stop_rgba(0.0, 1.0, 1.0, 1.0, 0.35)
        ray.add_color_stop_rgba(0.7, 1.0, 1.0, 1.0, 0.08)
        ray.add_color_stop_rgba(1.0, 1.0, 1.0, 1.0, 0.0)
        ctx.set_source(ray)
        ctx.move_to(W - 80, 0); ctx.line_to(W, 0); ctx.line_to(W, 260); ctx.line_to(180, FLOOR_Y + 120); ctx.line_to(30, FLOOR_Y + 120)
        ctx.close_path(); ctx.fill()
        ctx.restore()
        
    ctx.restore()

def draw_comic_sparks(ctx, cx, cy, scale=1.0, color=(1.0, 0.85, 0.0)):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(0.001, scale), max(0.001, scale))
    ctx.set_source_rgb(*color)
    for ang in np.linspace(0, 2*math.pi, 8, endpoint=False):
        ctx.save()
        ctx.rotate(ang)
        ctx.move_to(0, -35)
        ctx.line_to(7, -15)
        ctx.line_to(0, 0)
        ctx.line_to(-7, -15)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    ctx.restore()

def draw_center_hook_title(ctx, t):
    """
    DETIK PERTAMA: Highly Engaging Cartoon Hook Card right in the center.
    Visible immediately at t = 0.0s, with pulsing comic badge and explosive punch!
    """
    if t >= 3.2:
        return
        
    # Visible from t = 0.0s with subtle breathing pulse
    scale = 0.96 + 0.04 * math.sin(t * 8.0)
    alpha = 1.0
    if t > 2.6:
        # Fade out and zoom forward
        alpha = max(0.0, 1.0 - (t - 2.6) / 0.6)
        scale += (t - 2.6) * 0.25

    cx, cy = 540, 780
    w, h, rad = 940, 480, 36
    
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(0.001, scale), max(0.001, scale))
    
    # Drop shadow
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.45 * alpha)
    ctx.save()
    ctx.translate(14, 18)
    ctx.new_sub_path()
    ctx.arc(w/2 - rad, -h/2 + rad, rad, -math.pi/2, 0)
    ctx.arc(w/2 - rad, h/2 - rad, rad, 0, math.pi/2)
    ctx.arc(-w/2 + rad, h/2 - rad, rad, math.pi/2, math.pi)
    ctx.arc(-w/2 + rad, -h/2 + rad, rad, math.pi, 3*math.pi/2)
    ctx.close_path(); ctx.fill()
    ctx.restore()
    
    # Obsidian Glass Card Body
    ctx.new_sub_path()
    ctx.arc(w/2 - rad, -h/2 + rad, rad, -math.pi/2, 0)
    ctx.arc(w/2 - rad, h/2 - rad, rad, 0, math.pi/2)
    ctx.arc(-w/2 + rad, h/2 - rad, rad, math.pi/2, math.pi)
    ctx.arc(-w/2 + rad, -h/2 + rad, rad, math.pi, 3*math.pi/2)
    ctx.close_path()
    ctx.set_source_rgba(0.07, 0.08, 0.12, 0.96 * alpha)
    ctx.fill_preserve()
    
    # Glowing Matrix Green double rim
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.95 * alpha)
    ctx.set_line_width(8)
    ctx.stroke_preserve()
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.6 * alpha)
    ctx.set_line_width(2.5)
    ctx.stroke()
    
    # Top Warning Pill: [!] STOP CHATTING WITH AI! [!]
    pill_w, pill_h = 660, 64
    ctx.save()
    ctx.translate(0, -h/2 + 55)
    ctx.set_source_rgba(0.95, 0.15, 0.25, 0.95 * alpha)
    ctx.new_sub_path()
    ctx.arc(pill_w/2 - 20, -pill_h/2 + 20, 20, -math.pi/2, 0)
    ctx.arc(pill_w/2 - 20, pill_h/2 - 20, 20, 0, math.pi/2)
    ctx.arc(-pill_w/2 + 20, pill_h/2 - 20, 20, math.pi/2, math.pi)
    ctx.arc(-pill_w/2 + 20, -pill_h/2 + 20, 20, math.pi, 3*math.pi/2)
    ctx.close_path(); ctx.fill()
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(32)
    ctx.set_source_rgba(1, 1, 1, alpha)
    hook_str = "STOP CHATTING WITH AI!"
    ext = ctx.text_extents(hook_str)
    ctx.move_to(-ext.width/2, 11)
    ctx.show_text(hook_str)
    
    # Small side warning stars
    draw_star(ctx, -pill_w/2 + 35, 0, 12, 5, (1.0, 1.0, 1.0))
    draw_star(ctx, pill_w/2 - 35, 0, 12, 5, (1.0, 1.0, 1.0))
    ctx.restore()
    
    # Line 1: "I HIRED AN ENTIRE"
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(54)
    line1 = "I HIRED AN ENTIRE"
    ext1 = ctx.text_extents(line1)
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.9 * alpha)
    ctx.set_line_width(10)
    ctx.move_to(-ext1.width/2, 25); ctx.text_path(line1); ctx.stroke()
    ctx.set_source_rgba(1.0, 1.0, 1.0, alpha)
    ctx.move_to(-ext1.width/2, 25); ctx.show_text(line1)
    
    # Line 2: "AI AGENT OFFICE!"
    ctx.set_font_size(68)
    line2 = "AI AGENT OFFICE!"
    ext2 = ctx.text_extents(line2)
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.9 * alpha)
    ctx.set_line_width(12)
    ctx.move_to(-ext2.width/2, 110); ctx.text_path(line2); ctx.stroke()
    ctx.set_source_rgba(0.0, 1.0, 0.4, alpha) # Matrix Green
    ctx.move_to(-ext2.width/2, 110); ctx.show_text(line2)
    
    # Bottom Badge: 100% AUTONOMOUS SWARM • BARE METAL
    bot_w, bot_h = 760, 56
    ctx.save()
    ctx.translate(0, h/2 - 55)
    ctx.set_source_rgba(1.0, 0.84, 0.0, 0.25 * alpha) # Gold translucent
    ctx.new_sub_path()
    ctx.arc(bot_w/2 - 16, -bot_h/2 + 16, 16, -math.pi/2, 0)
    ctx.arc(bot_w/2 - 16, bot_h/2 - 16, 16, 0, math.pi/2)
    ctx.arc(-bot_w/2 + 16, bot_h/2 - 16, 16, math.pi/2, math.pi)
    ctx.arc(-bot_w/2 + 16, -bot_h/2 + 16, 16, math.pi, 3*math.pi/2)
    ctx.close_path(); ctx.fill_preserve()
    ctx.set_source_rgba(1.0, 0.84, 0.0, 0.9 * alpha); ctx.set_line_width(3); ctx.stroke()
    
    ctx.set_font_size(28)
    ctx.set_source_rgba(1.0, 0.95, 0.7, alpha)
    bot_text = "100% AUTONOMOUS SWARM • BARE METAL"
    ext_b = ctx.text_extents(bot_text)
    ctx.move_to(-ext_b.width/2, 10); ctx.show_text(bot_text)
    ctx.restore()
    
    # Corner Comic Sparks
    draw_comic_sparks(ctx, -w/2 + 30, -h/2 + 30, scale=0.8 * (0.8 + 0.2*math.sin(t*12)), color=(1.0, 0.85, 0.0))
    draw_comic_sparks(ctx, w/2 - 30, h/2 - 30, scale=0.8 * (0.8 + 0.2*math.cos(t*12)), color=(0.0, 1.0, 0.4))
    
    ctx.restore()

def draw_github_repo_card(ctx, x, y, w, h, t, show_pointer=False):
    """
    Renders the official GitHub Repository Card embedding real screenshot and clear URL.
    """
    rad = 28
    ctx.save()
    ctx.translate(x, y)
    
    # Outer Glow
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.25 + 0.1 * math.sin(t * 8.0))
    ctx.set_line_width(14)
    ctx.new_sub_path()
    ctx.arc(w - rad, rad, rad, -math.pi/2, 0)
    ctx.arc(w - rad, h - rad, rad, 0, math.pi/2)
    ctx.arc(rad, h - rad, rad, math.pi/2, math.pi)
    ctx.arc(rad, rad, rad, math.pi, 3*math.pi/2)
    ctx.close_path(); ctx.stroke()
    
    # Window Body
    ctx.new_sub_path()
    ctx.arc(w - rad, rad, rad, -math.pi/2, 0)
    ctx.arc(w - rad, h - rad, rad, 0, math.pi/2)
    ctx.arc(rad, h - rad, rad, math.pi/2, math.pi)
    ctx.arc(rad, rad, rad, math.pi, 3*math.pi/2)
    ctx.close_path()
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.set_line_width(5)
    ctx.stroke()
    
    # Top Browser Header Bar
    head_h = 70
    ctx.save()
    ctx.set_source_rgb(0.14, 0.16, 0.22)
    ctx.rectangle(0, 0, w, head_h); ctx.fill()
    
    # Window controls (red, yellow, green)
    colors = [(0.95, 0.35, 0.35), (0.95, 0.80, 0.25), (0.35, 0.85, 0.45)]
    for idx, c in enumerate(colors):
        ctx.set_source_rgb(*c)
        ctx.arc(35 + idx * 30, head_h / 2, 8, 0, 2*math.pi); ctx.fill()
        
    # URL Pill Bar: github.com/flowork-os/ai-agent-office
    bar_x, bar_y, bar_w, bar_h = 145, 12, w - 340, 46
    ctx.set_source_rgb(0.06, 0.07, 0.10)
    ctx.rectangle(bar_x, bar_y, bar_w, bar_h); ctx.fill()
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(2); ctx.stroke()
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(21)
    ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(bar_x + 16, bar_y + 31)
    ctx.show_text("github.com/flowork-os/ai-agent-office")
    
    # Star Button Pill on right
    sbtn_x, sbtn_y, sbtn_w, sbtn_h = w - 175, 12, 160, 46
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.rectangle(sbtn_x, sbtn_y, sbtn_w, sbtn_h); ctx.fill()
    draw_star(ctx, sbtn_x + 22, sbtn_y + 23, 12, 5, (0.1, 0.1, 0.1))
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(20)
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.move_to(sbtn_x + 42, sbtn_y + 31)
    ctx.show_text("STAR REPO")
    ctx.restore()
    
    # Real Screenshot Content Area
    view_x, view_y = 10, head_h + 8
    view_w, view_h = w - 20, h - head_h - 18
    
    ctx.save()
    ctx.rectangle(view_x, view_y, view_w, view_h)
    ctx.clip()
    
    if REPO_SURF is not None:
        img_w = REPO_SURF.get_width()
        img_h = REPO_SURF.get_height()
        sc = view_w / img_w
        ctx.translate(view_x, view_y)
        ctx.scale(sc, sc)
        ctx.set_source_surface(REPO_SURF, 0, 0)
        ctx.paint()
    else:
        ctx.set_source_rgb(0.12, 0.14, 0.18); ctx.paint()
        ctx.set_source_rgb(1, 1, 1)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(36)
        ctx.move_to(view_x + 40, view_y + 100); ctx.show_text("flowork-os / ai-agent-office")
    ctx.restore()
    
    # Animated Pointer Cursor
    if show_pointer:
        p_x = w - 100 + math.sin(t * 15.0) * 8
        p_y = head_h + 35 + math.cos(t * 15.0) * 8
        ctx.save()
        ctx.translate(p_x, p_y)
        # Vector Pointer Arrow
        ctx.set_source_rgb(1.0, 0.85, 0.0)
        ctx.move_to(0, 0); ctx.line_to(-18, -40); ctx.line_to(5, -34); ctx.close_path(); ctx.fill()
        ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(3); ctx.stroke()
        ctx.restore()
        
    ctx.restore()

def draw_3d_office_display(ctx, x, y, w, h, t):
    """
    Renders the ultra-wide curved office monitor showing the real 3D virtual office swarm.
    """
    rad = 24
    ctx.save()
    ctx.translate(x, y)
    
    # Outer frame
    ctx.set_source_rgb(0.12, 0.14, 0.18)
    ctx.rectangle(0, 0, w, h); ctx.fill()
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(4); ctx.stroke()
    
    # Inner viewport
    pad = 8
    ctx.save()
    ctx.rectangle(pad, pad, w - pad*2, h - pad*2)
    ctx.clip()
    
    if COVER_SURF is not None:
        cw = COVER_SURF.get_width()
        ch = COVER_SURF.get_height()
        sc = max((w - pad*2) / cw, (h - pad*2) / ch)
        ctx.translate(pad, pad)
        ctx.scale(sc, sc)
        ctx.set_source_surface(COVER_SURF, 0, 0)
        ctx.paint()
    else:
        ctx.set_source_rgb(0.18, 0.20, 0.25); ctx.paint()
    ctx.restore()
    
    # Top overlay banner
    ctx.set_source_rgba(0.08, 0.09, 0.12, 0.88)
    ctx.rectangle(0, 0, w, 52); ctx.fill()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(22); ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(25, 34); ctx.show_text(">> LIVE 3D SOVEREIGN OFFICE SWARM • BARE METAL <<")
    
    # Bottom Department Badges
    dept_names = ["[ MARKETING AGENT ]", "[ FINANCE AGENT ]", "[ RUST DEV AGENT ]"]
    badge_w = (w - 60) / 3
    for i, name in enumerate(dept_names):
        bx = 20 + i * (badge_w + 10)
        by = h - 50
        ctx.set_source_rgba(0.06, 0.07, 0.10, 0.90)
        ctx.rectangle(bx, by, badge_w, 40); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(2); ctx.stroke()
        ctx.set_font_size(18); ctx.set_source_rgb(1, 1, 1)
        ctx.move_to(bx + 12, by + 26); ctx.show_text(name)
        
    ctx.restore()

def draw_dual_cta_outro(ctx, t):
    """
    High-conversion Call-To-Action Cards in the outro.
    Dual prominent cards:
    Card 1: STAR ON GITHUB (github.com/flowork-os/ai-agent-office)
    Card 2: WATCH LIVE AT FLOWORKOS.COM
    """
    ctx.save()
    
    # 1. GITHUB REPO CTA CARD (y: 200 - 450)
    card1_w, card1_h = 960, 260
    card1_x = (W - card1_w) / 2
    card1_y = 200
    
    pulse1 = 1.0 + 0.02 * math.sin(t * 10.0)
    ctx.save()
    ctx.translate(card1_x + card1_w/2, card1_y + card1_h/2)
    ctx.scale(pulse1, pulse1)
    ctx.translate(-card1_w/2, -card1_h/2)
    
    # Card 1 Body
    ctx.set_source_rgba(0.08, 0.09, 0.12, 0.96)
    ctx.rectangle(0, 0, card1_w, card1_h); ctx.fill()
    ctx.set_source_rgb(1.0, 0.85, 0.0); ctx.set_line_width(6); ctx.stroke()
    
    # Top Header Pill
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.rectangle(0, 0, card1_w, 48); ctx.fill()
    draw_star(ctx, 35, 24, 14, 6, (0.1, 0.1, 0.1))
    draw_star(ctx, card1_w - 35, 24, 14, 6, (0.1, 0.1, 0.1))
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26); ctx.set_source_rgb(0.1, 0.1, 0.1)
    head_txt1 = "OFFICIAL OPEN-SOURCE REPOSITORY"
    ext_h1 = ctx.text_extents(head_txt1)
    ctx.move_to((card1_w - ext_h1.width)/2, 34); ctx.show_text(head_txt1)
    
    # URL Text
    ctx.set_font_size(36); ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(40, 115); ctx.show_text("github.com/flowork-os/ai-agent-office")
    
    # Star Button Graphic
    btn_w, btn_h = 440, 64
    ctx.save(); ctx.translate(40, 155)
    ctx.set_source_rgb(1.0, 0.85, 0.0); ctx.rectangle(0, 0, btn_w, btn_h); ctx.fill()
    draw_star(ctx, 35, 32, 16, 7, (0.1, 0.1, 0.1))
    ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_font_size(28)
    ctx.move_to(65, 43); ctx.show_text("STAR ON GITHUB")
    ctx.restore()
    
    # License tag
    ctx.set_font_size(24); ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(520, 195); ctx.show_text("100% Free & Sovereign Rust")
    ctx.restore()
    
    # 2. LIVE DEMO CTA CARD (y: 490 - 740)
    card2_w, card2_h = 960, 240
    card2_x = (W - card2_w) / 2
    card2_y = 490
    
    pulse2 = 1.0 + 0.02 * math.cos(t * 10.0)
    ctx.save()
    ctx.translate(card2_x + card2_w/2, card2_y + card2_h/2)
    ctx.scale(pulse2, pulse2)
    ctx.translate(-card2_w/2, -card2_h/2)
    
    ctx.set_source_rgba(0.08, 0.09, 0.12, 0.96)
    ctx.rectangle(0, 0, card2_w, card2_h); ctx.fill()
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(6); ctx.stroke()
    
    # Header Pill
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.rectangle(0, 0, card2_w, 48); ctx.fill()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26); ctx.set_source_rgb(0.05, 0.05, 0.07)
    head_txt2 = ">> WATCH AGENTS WORK IN REAL-TIME <<"
    ext_h2 = ctx.text_extents(head_txt2)
    ctx.move_to((card2_w - ext_h2.width)/2, 34); ctx.show_text(head_txt2)
    
    # Giant URL
    ctx.set_font_size(54); ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(40, 135); ctx.show_text(">> FLOWORKOS.COM")
    
    # Subtitle
    ctx.set_font_size(26); ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(40, 195); ctx.show_text("Put an Autonomous AI Team on Your Payroll!")
    ctx.restore()
    
    ctx.restore()

def draw_mr_flow(ctx, x, y, scale=1.0, state=None):
    if state is None: state = {}
    pose = state.get("pose", "idle")
    t = state.get("t", 0.0)
    squash_x = state.get("squash_x", 1.0)
    squash_y = state.get("squash_y", 1.0)
    brow = state.get("brow", "normal")
    eye = state.get("eye", "normal")
    mouth = state.get("mouth", "smile")
    is_talking = state.get("talk", False)
    has_hammer = state.get("hammer", False)
    hammer_angle = state.get("hammer_angle", 0.0)
    has_coffee = state.get("coffee", False)
    hoodie_glow = state.get("glow", 0.0)
    
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale * squash_x, scale * squash_y)
    
    # Drop shadow
    ctx.save()
    ctx.set_source_rgba(0.18, 0.16, 0.14, 0.28)
    ctx.scale(1.0, 0.28)
    shadow_y_rel = (FLOOR_Y - y) / (scale * squash_y * 0.28)
    ctx.arc(0, shadow_y_rel, 105 * squash_x, 0, 2*math.pi)
    ctx.fill()
    ctx.restore()
    
    hip_y = 0
    torso_y = hip_y - 80
    head_y = torso_y - 120
    floor_rel = (FLOOR_Y - y) / (scale * squash_y)
    
    # 1. LEGS (Rubber-Hose Bezier)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(15)
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    
    if pose == "walk":
        stride = math.sin(t * 12.0)
        l_foot_y = floor_rel - max(0, -stride * 35.0)
        r_foot_y = floor_rel - max(0, stride * 35.0)
        l_foot_x = -stride * 55.0
        r_foot_x = stride * 55.0
        ctx.move_to(-25, hip_y); ctx.curve_to(-35, hip_y + 60, l_foot_x - 10, l_foot_y - 40, l_foot_x, l_foot_y); ctx.stroke()
        ctx.move_to(l_foot_x, l_foot_y); ctx.line_to(l_foot_x - 30, l_foot_y); ctx.stroke()
        ctx.move_to(25, hip_y); ctx.curve_to(35, hip_y + 60, r_foot_x + 10, r_foot_y - 40, r_foot_x, r_foot_y); ctx.stroke()
        ctx.move_to(r_foot_x, r_foot_y); ctx.line_to(r_foot_x + 30, r_foot_y); ctx.stroke()
    elif pose in ["jump_swing", "crouch"]:
        ctx.move_to(-28, hip_y); ctx.curve_to(-65, hip_y + 40, -50, floor_rel - 10, -35, floor_rel); ctx.stroke()
        ctx.move_to(28, hip_y); ctx.curve_to(65, hip_y + 40, 50, floor_rel - 10, 35, floor_rel); ctx.stroke()
        ctx.move_to(-35, floor_rel); ctx.line_to(-65, floor_rel); ctx.stroke()
        ctx.move_to(35, floor_rel); ctx.line_to(65, floor_rel); ctx.stroke()
    else: # idle, lean_point, shrug, triumphant
        ctx.move_to(-25, hip_y); ctx.curve_to(-40, hip_y + 70, -45, floor_rel - 30, -50, floor_rel); ctx.stroke()
        ctx.move_to(-50, floor_rel); ctx.line_to(-80, floor_rel); ctx.stroke()
        ctx.move_to(25, hip_y); ctx.curve_to(40, hip_y + 70, 45, floor_rel - 30, 50, floor_rel); ctx.stroke()
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
    
    if hoodie_glow > 0.0:
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.4 * hoodie_glow)
        ctx.set_line_width(8)
        ctx.stroke_preserve()
    ctx.set_source_rgb(0.05, 0.05, 0.07)
    ctx.set_line_width(4)
    ctx.stroke()
    
    # 3. STACKED CHEST BRANDING: Line 1 "FLOWORKOS", Line 2 ".COM"
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_source_rgb(0.0, 1.0, 0.4) # Matrix Green
    
    # Line 1: FLOWORKOS
    ctx.set_font_size(15.0)
    ext1 = ctx.text_extents("FLOWORKOS")
    ctx.move_to(-ext1.width / 2, torso_y - 6)
    ctx.show_text("FLOWORKOS")
    
    # Line 2: .COM
    ctx.set_font_size(12.5)
    ext2 = ctx.text_extents(".COM")
    ctx.move_to(-ext2.width / 2, torso_y + 16)
    ctx.show_text(".COM")
    ctx.restore()
    
    # 4. ARMS & PROPS (Rubber-Hose Bezier)
    ctx.set_line_width(15)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    
    if pose == "lean_point":
        ctx.move_to(-55, torso_y - 40); ctx.curve_to(-105, torso_y - 20, -115, torso_y + 20, -75, torso_y + 35); ctx.stroke()
        ctx.arc(-75, torso_y + 35, 14, 0, 2*math.pi); ctx.fill()
        ctx.move_to(55, torso_y - 40); ctx.curve_to(110, torso_y - 50, 150, torso_y - 20, 175, torso_y + 10); ctx.stroke()
        ctx.arc(175, torso_y + 10, 16, 0, 2*math.pi); ctx.fill()
        ctx.set_line_width(10)
        ctx.move_to(175, torso_y + 10); ctx.line_to(205, torso_y + 10); ctx.stroke()
        ctx.set_line_width(15)
        
    elif pose == "coffee_clipboard":
        ctx.move_to(-55, torso_y - 30); ctx.curve_to(-95, torso_y - 10, -105, torso_y - 40, -85, torso_y - 60); ctx.stroke()
        ctx.arc(-85, torso_y - 60, 14, 0, 2*math.pi); ctx.fill()
        # Clipboard
        ctx.save()
        ctx.set_source_rgb(0.55, 0.40, 0.25); ctx.rectangle(-125, torso_y - 95, 45, 60); ctx.fill()
        ctx.set_source_rgb(0.95, 0.95, 0.95); ctx.rectangle(-120, torso_y - 90, 35, 50); ctx.fill()
        ctx.restore()
        
        # Coffee cup
        ctx.move_to(55, torso_y - 30); ctx.curve_to(95, torso_y - 10, 105, torso_y - 30, 85, torso_y - 60); ctx.stroke()
        ctx.arc(85, torso_y - 60, 14, 0, 2*math.pi); ctx.fill()
        ctx.save()
        ctx.set_source_rgb(0.9, 0.9, 0.9); ctx.rectangle(85, torso_y - 85, 30, 35); ctx.fill()
        ctx.set_source_rgba(0.8, 0.8, 0.8, 0.6); ctx.set_line_width(3)
        steam_w = math.sin(t * 10.0) * 6.0
        ctx.move_to(95, torso_y - 90); ctx.curve_to(95 + steam_w, torso_y - 105, 95 - steam_w, torso_y - 115, 95, torso_y - 125); ctx.stroke()
        ctx.restore()
        
    elif pose == "shrug_question":
        shrug_wave = math.sin(t * 14.0) * 8.0
        ctx.move_to(-55, torso_y - 30); ctx.curve_to(-110, torso_y - 60, -130, torso_y - 120 + shrug_wave, -115, torso_y - 150 + shrug_wave); ctx.stroke()
        ctx.arc(-115, torso_y - 150 + shrug_wave, 16, 0, 2*math.pi); ctx.fill()
        ctx.move_to(55, torso_y - 30); ctx.curve_to(110, torso_y - 60, 130, torso_y - 120 - shrug_wave, 115, torso_y - 150 - shrug_wave); ctx.stroke()
        ctx.arc(115, torso_y - 150 - shrug_wave, 16, 0, 2*math.pi); ctx.fill()
        
    elif pose in ["crouch", "jump_swing", "smash_down"]:
        if has_hammer:
            ctx.save()
            hx = 45 if pose != "smash_down" else 85
            hy = torso_y - 140 if pose == "jump_swing" else (torso_y + 20 if pose == "smash_down" else torso_y - 20)
            ctx.translate(hx, hy); ctx.rotate(hammer_angle)
            ctx.set_source_rgb(0.55, 0.35, 0.18); ctx.set_line_width(16)
            ctx.move_to(0, 100); ctx.line_to(0, -160); ctx.stroke()
            ctx.set_source_rgb(0.22, 0.25, 0.32); ctx.rectangle(-75, -230, 150, 90); ctx.fill_preserve()
            ctx.set_source_rgb(0.10, 0.11, 0.14); ctx.set_line_width(8); ctx.stroke()
            ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.rectangle(-60, -195, 120, 20); ctx.fill()
            ctx.restore()
            
        if pose == "jump_swing":
            ctx.move_to(-55, torso_y - 40); ctx.curve_to(-30, torso_y - 120, 20, torso_y - 160, 45, torso_y - 140); ctx.stroke()
            ctx.move_to(55, torso_y - 40); ctx.curve_to(65, torso_y - 100, 55, torso_y - 130, 45, torso_y - 140); ctx.stroke()
            ctx.arc(45, torso_y - 140, 16, 0, 2*math.pi); ctx.fill()
        elif pose == "smash_down":
            ctx.move_to(-55, torso_y - 20); ctx.curve_to(-20, torso_y + 20, 50, torso_y + 40, 85, torso_y + 20); ctx.stroke()
            ctx.move_to(55, torso_y - 20); ctx.curve_to(70, torso_y, 80, torso_y + 10, 85, torso_y + 20); ctx.stroke()
            ctx.arc(85, torso_y + 20, 16, 0, 2*math.pi); ctx.fill()
            
    elif pose == "triumphant":
        for side in [-1, 1]:
            ctx.move_to(side * 55, torso_y - 30); ctx.curve_to(side * 95, torso_y - 60, side * 115, torso_y - 70, side * 95, torso_y - 110); ctx.stroke()
            ctx.arc(side * 95, torso_y - 110, 16, 0, 2*math.pi); ctx.fill()
            ctx.set_line_width(10)
            ctx.move_to(side * 95, torso_y - 110); ctx.line_to(side * 95, torso_y - 135); ctx.stroke()
            ctx.set_line_width(15)
            
    # 5. HEAD
    ctx.save()
    ctx.set_source_rgb(0.98, 0.98, 0.98)
    ctx.scale(1.0, 1.08)
    ctx.arc(0, head_y / 1.08, 68, 0, 2*math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    ctx.set_line_width(7)
    ctx.stroke()
    ctx.restore()
    
    # 6. DYNAMIC CARTOON FACE RIG
    ctx.set_line_width(6.5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    
    if brow == "skeptical":
        ctx.move_to(-46, head_y - 42); ctx.curve_to(-30, head_y - 58, -15, head_y - 52, -5, head_y - 44); ctx.stroke()
        ctx.move_to(10, head_y - 36); ctx.curve_to(25, head_y - 42, 40, head_y - 34, 48, head_y - 26); ctx.stroke()
    elif brow == "incredulous":
        ctx.move_to(-45, head_y - 50); ctx.curve_to(-30, head_y - 64, -15, head_y - 64, -5, head_y - 50); ctx.stroke()
        ctx.move_to(5, head_y - 50); ctx.curve_to(15, head_y - 64, 30, head_y - 64, 45, head_y - 50); ctx.stroke()
    elif brow == "intense_smash":
        ctx.move_to(-45, head_y - 45); ctx.curve_to(-30, head_y - 38, -15, head_y - 28, -5, head_y - 24); ctx.stroke()
        ctx.move_to(5, head_y - 24); ctx.curve_to(15, head_y - 28, 30, head_y - 38, 45, head_y - 45); ctx.stroke()
    else:
        ctx.move_to(-42, head_y - 40); ctx.curve_to(-28, head_y - 50, -15, head_y - 48, -6, head_y - 38); ctx.stroke()
        ctx.move_to(6, head_y - 38); ctx.curve_to(15, head_y - 48, 28, head_y - 50, 42, head_y - 40); ctx.stroke()
        
    blink = ((t * 2.5) % 3.6 > 3.42)
    if eye == "wink":
        ctx.move_to(-35, head_y - 18); ctx.curve_to(-24, head_y - 26, -15, head_y - 26, -5, head_y - 18); ctx.stroke()
        ctx.arc(25, head_y - 16, 12, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgb(1, 1, 1); ctx.arc(28, head_y - 19, 4, 0, 2*math.pi); ctx.fill()
    elif eye == "bloodshot":
        ctx.arc(-24, head_y - 18, 14, 0, 2*math.pi); ctx.fill()
        ctx.arc(24, head_y - 18, 14, 0, 2*math.pi); ctx.fill()
        ctx.set_source_rgb(0.9, 0.2, 0.2); ctx.set_line_width(2.5)
        ctx.move_to(-32, head_y - 22); ctx.line_to(-24, head_y - 18); ctx.stroke()
        ctx.move_to(32, head_y - 22); ctx.line_to(24, head_y - 18); ctx.stroke()
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
        ctx.move_to(-24, head_y + 16); ctx.line_to(24, head_y + 16)
        ctx.curve_to(24, head_y + 16 + m_h, -24, head_y + 16 + m_h, -24, head_y + 16)
        ctx.close_path(); ctx.fill_preserve(); ctx.stroke(); ctx.clip()
        ctx.set_source_rgb(0.95, 0.35, 0.45)
        ctx.arc(0, head_y + 16 + m_h, 18, 0, 2*math.pi); ctx.fill()
        ctx.restore()
    elif mouth == "grit_teeth":
        ctx.save()
        ctx.rectangle(-28, head_y + 16, 56, 22)
        ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve()
        ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(4); ctx.stroke()
        for tx in [-14, 0, 14]:
            ctx.move_to(tx, head_y + 16); ctx.line_to(tx, head_y + 38); ctx.stroke()
        ctx.move_to(-28, head_y + 27); ctx.line_to(28, head_y + 27); ctx.stroke()
        ctx.restore()
    elif mouth == "gasp_o":
        ctx.save(); ctx.arc(0, head_y + 28, 16, 0, 2*math.pi); ctx.fill(); ctx.restore()
    else:
        ctx.save(); ctx.move_to(-24, head_y + 18); ctx.curve_to(-12, head_y + 36, 12, head_y + 36, 24, head_y + 18)
        ctx.set_line_width(5); ctx.stroke(); ctx.restore()
        
    ctx.restore()

def draw_subtitle_pill(ctx, text, y=1720):
    if not text: return
    ctx.save()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    
    font_size = 52
    ctx.set_font_size(font_size)
    ext = ctx.text_extents(text)
    if ext.width > (W - 140):
        font_size = int(font_size * (W - 140) / ext.width)
        ctx.set_font_size(font_size)
        ext = ctx.text_extents(text)
        
    sx = (W - ext.width) / 2
    sy = y
    
    # Outer dark stroke
    ctx.set_source_rgb(0.04, 0.04, 0.06)
    ctx.set_line_width(12)
    ctx.move_to(sx, sy); ctx.text_path(text); ctx.stroke()
    
    # Inner white text
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(sx, sy); ctx.show_text(text)
    ctx.restore()

def render_58s_cartoon():
    print(f"🎬 Starting Master Render: 58-Second Cartoon Short @ {FPS} FPS ({TOTAL_FRAMES} frames)...")
    
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
    
    contact_frame_indices = [int(TOTAL_FRAMES * i / 12) for i in range(12)]
    contact_surfaces = []
    
    for f in range(TOTAL_FRAMES):
        t = f / FPS
        cam_shake_x = 0
        cam_shake_y = 0
        subtitle = ""
        bg_type = "office"
        
        # 1. BEAT 1 (0.0s - 4.19s): Tired dev at desk with chaotic floating chat boxes
        # DETIK PERTAMA: Centered Hook Title!
        if t < 4.19:
            bg_type = "dark_room"
            draw_wall_and_floor(ctx, t, bg_type)
            
            # Desk and computer
            ctx.set_source_rgb(0.35, 0.25, 0.18)
            ctx.rectangle(200, FLOOR_Y - 220, 680, 220); ctx.fill()
            ctx.set_source_rgb(0.1, 0.1, 0.1)
            ctx.rectangle(440, FLOOR_Y - 440, 200, 220); ctx.fill()
            # Monitor glowing blue
            ctx.set_source_rgb(0.2, 0.6, 0.9)
            ctx.rectangle(450, FLOOR_Y - 430, 180, 180); ctx.fill()
            
            # Floating chaotic chat bubbles
            for i in range(6):
                bx = 150 + (i % 3) * 280
                by = 400 + (i // 3) * 160 + math.sin(t * 4.0 + i) * 12
                ctx.set_source_rgba(0.9, 0.9, 0.9, 0.85)
                ctx.rectangle(bx, by, 180, 70); ctx.fill()
                ctx.set_source_rgb(0.2, 0.2, 0.2)
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(24)
                ctx.move_to(bx + 20, by + 45); ctx.show_text("Prompt...")
                
            # Tired Developer Stickman
            state_dev = {"pose": "idle", "t": t, "eye": "bloodshot", "brow": "skeptical", "mouth": "gasp_o"}
            draw_mr_flow(ctx, 360, FLOOR_Y - 260, scale=1.3, state=state_dev)
            
            # DETIK PERTAMA HOOK TITLE OVERLAY
            draw_center_hook_title(ctx, t)
            
            subtitle = "PROMPTS AT 3 AM?"
            
        # 2. BEAT 2 (4.19s - 6.01s): Red error OUT OF TOKENS & chair tips over
        elif t < 6.01:
            bg_type = "dark_room"
            dt = t - 4.19
            cam_shake_x = math.sin(dt * 60) * 15 * math.exp(-dt * 3)
            draw_wall_and_floor(ctx, t, bg_type, cam_shake_x, cam_shake_y)
            
            # Flashing RED Error on monitor
            ctx.set_source_rgb(0.9, 0.1, 0.1)
            ctx.rectangle(200, 480, 680, 180); ctx.fill()
            ctx.set_source_rgb(1, 1, 1)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(52)
            ctx.move_to(250, 590); ctx.show_text("ERROR: OUT OF TOKENS!")
            
            # Fallen developer
            state_dev = {"pose": "crouch", "t": t, "squash_y": 0.5, "eye": "bloodshot", "brow": "incredulous", "mouth": "gasp_o"}
            draw_mr_flow(ctx, 360, FLOOR_Y - 140, scale=1.3, state=state_dev)
            subtitle = "OUT OF TOKENS!"
            
        # 3. BEAT 3 (6.01s - 10.97s): Pizza hallucination & mess
        elif t < 10.97:
            bg_type = "dark_room"
            draw_wall_and_floor(ctx, t, bg_type)
            
            # Flying Cartoon Pizza Slices
            for i in range(5):
                pz_x = 200 + i * 160 + math.sin(t * 3.0 + i) * 30
                pz_y = 350 + math.cos(t * 4.0 + i) * 120
                ctx.save(); ctx.translate(pz_x, pz_y); ctx.rotate(t * 2.0 + i)
                ctx.set_source_rgb(0.95, 0.75, 0.2); ctx.move_to(0, -40); ctx.line_to(35, 40); ctx.line_to(-35, 40); ctx.close_path(); ctx.fill()
                ctx.set_source_rgb(0.85, 0.15, 0.15); ctx.arc(0, 10, 8, 0, 2*math.pi); ctx.fill()
                ctx.restore()
                
            state_dev = {"pose": "shrug_question", "t": t, "eye": "bloodshot", "brow": "incredulous", "mouth": "gasp_o"}
            draw_mr_flow(ctx, 540, FLOOR_Y - 260, scale=1.35, state=state_dev)
            subtitle = "AI PIZZA HALLUCINATIONS!"
            
        # 4. BEAT 4 (10.97s - 13.0s): Mr. Flow kicks the door open!
        elif t < 13.0:
            dt = t - 10.97
            cam_shake_x = math.sin(dt * 70) * 20 * math.exp(-dt * 4)
            draw_wall_and_floor(ctx, t, "office", cam_shake_x, cam_shake_y)
            
            # Mr. Flow kicks in holding coffee & clipboard
            p = min(1.0, dt / 0.8)
            char_x = -150 + p * (540 - (-150))
            state_mf = {"pose": "coffee_clipboard", "t": t, "brow": "skeptical", "mouth": "talk_open", "talk": True, "coffee": True}
            draw_mr_flow(ctx, char_x, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "STOP DOING THAT RIGHT NOW!"
            
        # 5. BEAT 5 (13.0s - 16.84s): Meet AI Agent Office on GitHub! (REAL REPO SCREENSHOT EMBEDDED)
        elif t < 16.84:
            draw_wall_and_floor(ctx, t, "office")
            
            # Display Real GitHub Repo Screenshot Card
            card_w, card_h = 940, 520
            card_x = (W - card_w) / 2
            card_y = 220
            draw_github_repo_card(ctx, card_x, card_y, card_w, card_h, t, show_pointer=True)
            
            # Mr. Flow standing right next to it, pointing at the repo!
            state_mf = {"pose": "lean_point", "t": t, "brow": "skeptical", "mouth": "talk_open", "talk": True, "glow": 0.5}
            draw_mr_flow(ctx, 360, FLOOR_Y - 260, scale=1.45, state=state_mf)
            subtitle = "MEET AI AGENT OFFICE ON GITHUB!"
            
        # 6. BEAT 6 & 7 (16.84s - 20.68s): Deployed on bare metal (REAL 3D VIRTUAL OFFICE COVER)
        elif t < 20.68:
            draw_wall_and_floor(ctx, t, "office")
            
            # Display Real 3D Swarm Virtual Office Cover
            disp_w, disp_h = 960, 420
            disp_x = (W - disp_w) / 2
            disp_y = 240
            draw_3d_office_display(ctx, disp_x, disp_y, disp_w, disp_h, t)
            
            state_mf = {"pose": "shrug_question", "t": t, "brow": "incredulous", "mouth": "talk_open", "talk": True}
            draw_mr_flow(ctx, 540, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "ENTIRE DEPARTMENT ON BARE METAL!"
            
        # 7. BEAT 8 (20.68s - 25.11s): Marketing Agent Station (Laser Binoculars spying)
        elif t < 25.11:
            draw_wall_and_floor(ctx, t, "office")
            # Large spy HUD
            ctx.save()
            ctx.set_source_rgba(0.10, 0.12, 0.16, 0.9)
            ctx.rectangle(120, 280, 840, 260); ctx.fill()
            ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(4); ctx.stroke()
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(36)
            ctx.move_to(160, 360); ctx.show_text(">> RECON: YOUTUBE SPY MINING")
            ctx.set_source_rgb(1, 1, 1); ctx.set_font_size(28)
            ctx.move_to(160, 420); ctx.show_text("Mining competitor complaints & market gaps...")
            ctx.restore()
            
            # Laser beams from eyes
            ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6)
            ctx.set_line_width(6)
            ctx.move_to(450, FLOOR_Y - 380); ctx.line_to(900, 350); ctx.stroke()
            
            state_mkt = {"pose": "lean_point", "t": t, "brow": "skeptical", "mouth": "talk_open", "talk": True}
            draw_mr_flow(ctx, 420, FLOOR_Y - 260, scale=1.55, state=state_mkt)
            subtitle = "MARKETING SPIES ON COMPETITORS!"
            
        # 8. BEAT 9 (25.11s - 28.95s): Finance Agent (Giant Calculator & Cash)
        elif t < 28.95:
            draw_wall_and_floor(ctx, t, "office")
            # Giant Gold Calculator
            ctx.save()
            ctx.set_source_rgb(0.85, 0.70, 0.20)
            ctx.rectangle(180, 320, 720, 280); ctx.fill()
            ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(6); ctx.stroke()
            ctx.set_source_rgb(0.9, 0.95, 0.9)
            ctx.rectangle(220, 350, 640, 90); ctx.fill()
            ctx.set_source_rgb(0.1, 0.5, 0.1)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(44)
            calc_val = f"${int(t * 128450) % 9999999:,}"
            ctx.move_to(250, 415); ctx.show_text(f"CAC/LTV: {calc_val}")
            ctx.restore()
            
            state_fin = {"pose": "shrug_question", "t": t, "brow": "incredulous", "mouth": "talk_open", "talk": True}
            draw_mr_flow(ctx, 540, FLOOR_Y - 260, scale=1.55, state=state_fin)
            subtitle = "FINANCE STRESS-TESTS ECONOMICS!"
            
        # 9. BEAT 10 (28.95s - 32.92s): Engineering Agent (Rust Engine & Server Pipes)
        elif t < 32.92:
            draw_wall_and_floor(ctx, t, "office")
            # Glowing matrix green server pipes
            ctx.save()
            ctx.set_source_rgb(0.2, 0.25, 0.3)
            ctx.rectangle(150, FLOOR_Y - 550, 220, 550); ctx.fill()
            # Green coolant pipe
            ctx.set_source_rgb(0.0, 1.0, 0.4)
            ctx.set_line_width(22)
            ctx.move_to(370, FLOOR_Y - 450); ctx.line_to(750, FLOOR_Y - 450); ctx.line_to(750, FLOOR_Y - 200); ctx.stroke()
            # Rust Badge
            ctx.set_source_rgb(0.85, 0.35, 0.15)
            ctx.arc(750, 380, 65, 0, 2*math.pi); ctx.fill()
            ctx.set_source_rgb(1, 1, 1)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(32); ctx.move_to(710, 390); ctx.show_text("RUST")
            ctx.restore()
            
            state_eng = {"pose": "lean_point", "t": t, "brow": "intense_smash", "mouth": "talk_open", "talk": True}
            draw_mr_flow(ctx, 480, FLOOR_Y - 260, scale=1.55, state=state_eng)
            subtitle = "RUST BARE-METAL ENGINE!"
            
        # 10. BEAT 11 (32.92s - 37.84s): Rogue Bug sneaks in & Mr. Flow SMASH!
        elif t < 37.84:
            dt = t - 32.92
            is_smash = (dt > 1.8)
            cam_shake_x = math.sin(dt * 75) * 32 * math.exp(-max(0, dt - 1.8) * 6) if is_smash else 0
            cam_shake_y = math.cos(dt * 85) * 28 * math.exp(-max(0, dt - 1.8) * 6) if is_smash else 0
            draw_wall_and_floor(ctx, t, "office", cam_shake_x, cam_shake_y)
            
            bug_x, bug_y = 760, FLOOR_Y - 14
            # Draw bug
            ctx.save(); ctx.translate(bug_x + cam_shake_x, bug_y + cam_shake_y)
            if not is_smash:
                ctx.set_source_rgb(0.9, 0.2, 0.2); ctx.arc(0, 0, 30, 0, 2*math.pi); ctx.fill()
            else: # flattened
                ctx.scale(2.2, 0.15); ctx.set_source_rgb(0.9, 0.2, 0.2); ctx.arc(0, 0, 30, 0, 2*math.pi); ctx.fill()
            ctx.restore()
            
            if is_smash:
                # Golden Exit Code 0 Stamp
                ctx.save()
                ctx.set_source_rgba(0.0, 1.0, 0.4, 0.95)
                ctx.rectangle(200, 320, 680, 150); ctx.fill()
                ctx.set_source_rgb(0.05, 0.05, 0.07)
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(52); ctx.move_to(240, 415); ctx.show_text("STRICT EXIT CODE 0")
                ctx.restore()
                
            pose_mf = "smash_down" if is_smash else ("jump_swing" if dt > 1.0 else "crouch")
            state_mf = {"pose": pose_mf, "t": t, "brow": "intense_smash", "mouth": "grit_teeth", "hammer": True, "hammer_angle": 1.6 if is_smash else -0.8}
            draw_mr_flow(ctx, 640 + cam_shake_x, FLOOR_Y - 260 + cam_shake_y, scale=1.55, state=state_mf)
            subtitle = "MR. FLOW SMASHES ROGUE BUGS!" if not is_smash else "STRICT EXIT CODE ZERO!"
            
        # 11. BEAT 12 & 13 (37.84s - 41.62s): Zero Cloud Leaks & Padlock
        elif t < 41.62:
            draw_wall_and_floor(ctx, t, "office")
            # Giant Security Padlock
            ctx.save()
            ctx.set_source_rgb(0.2, 0.5, 0.8) # Landlock shield
            ctx.rectangle(340, 360, 400, 280); ctx.fill()
            ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(8); ctx.stroke()
            # Keyhole
            ctx.set_source_rgb(1, 1, 1); ctx.arc(540, 480, 35, 0, 2*math.pi); ctx.fill()
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(38); ctx.set_source_rgb(1, 1, 1)
            ctx.move_to(380, 590); ctx.show_text("LANDLOCK LSM")
            ctx.restore()
            
            state_mf = {"pose": "lean_point", "t": t, "brow": "skeptical", "mouth": "talk_open", "talk": True}
            draw_mr_flow(ctx, 540, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "ZERO CLOUD LEAKS!" if t < 39.63 else "ZERO CORPORATE FLUFF!"
            
        # 12. BEAT 14 (41.62s - 46.44s): Orchestrating Swarm & Rocket Launch
        elif t < 46.44:
            draw_wall_and_floor(ctx, t, "office")
            # Glowing neural streams connecting
            for ang in np.linspace(0.2, math.pi - 0.2, 5):
                ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6)
                ctx.set_line_width(6)
                ctx.move_to(540, FLOOR_Y - 320)
                ctx.curve_to(540 + math.cos(ang) * 350, 600, 540 + math.cos(ang) * 450, 400, 540 + math.cos(ang) * 400, 250)
                ctx.stroke()
                
            # Rocket Launching upward
            r_y = 650 - (t - 41.62) * 85
            ctx.save(); ctx.translate(850, r_y)
            ctx.set_source_rgb(0.9, 0.25, 0.25); ctx.move_to(0, -90); ctx.line_to(35, 30); ctx.line_to(-35, 30); ctx.close_path(); ctx.fill()
            ctx.set_source_rgb(0.95, 0.95, 0.95); ctx.rectangle(-30, 30, 60, 90); ctx.fill()
            # Fire flame
            ctx.set_source_rgb(1.0, 0.7, 0.1); ctx.move_to(-25, 120); ctx.line_to(0, 180 + math.sin(t*30)*25); ctx.line_to(25, 120); ctx.close_path(); ctx.fill()
            ctx.restore()
            
            state_mf = {"pose": "triumphant", "t": t, "brow": "happy", "mouth": "talk_open", "talk": True, "glow": 0.8}
            draw_mr_flow(ctx, 450, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "SHIPPED SOFTWARE!"
            
        # 13. BEAT 15 (46.44s - 51.63s): Star Repo Call-To-Action!
        elif t < 51.63:
            draw_wall_and_floor(ctx, t, "office")
            
            # Prominent GitHub Repo Card
            card_w, card_h = 940, 500
            card_x = (W - card_w) / 2
            card_y = 240
            draw_github_repo_card(ctx, card_x, card_y, card_w, card_h, t, show_pointer=True)
            
            # Gold Star Chime Graphic popping
            draw_comic_sparks(ctx, W/2 + 220, 280, scale=1.2 * (0.8 + 0.2*math.sin(t*16)), color=(1.0, 0.85, 0.0))
            
            # Mr. Flow pointing rubber-hose arm at the Star button!
            state_mf = {"pose": "lean_point", "t": t, "brow": "happy", "mouth": "talk_open", "talk": True, "glow": 0.8}
            draw_mr_flow(ctx, 420, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "STAR REPO: github.com/flowork-os/ai-agent-office"
            
        # 14. BEAT 16 (51.63s - 58.0s): Dual CTA Outro & floworkos.com
        else:
            draw_wall_and_floor(ctx, t, "office")
            
            # Dual High-Impact Call-To-Action Cards
            draw_dual_cta_outro(ctx, t)
            
            # Peer Agents cheering on sides
            state_side1 = {"pose": "triumphant", "t": t, "brow": "happy", "mouth": "smile", "glow": 0.5}
            draw_mr_flow(ctx, 220, FLOOR_Y - 240, scale=1.1, state=state_side1)
            
            state_side2 = {"pose": "triumphant", "t": t, "brow": "happy", "mouth": "smile", "glow": 0.5}
            draw_mr_flow(ctx, 860, FLOOR_Y - 240, scale=1.1, state=state_side2)
            
            # Mr. Flow center close-up
            dt_end = t - 51.63
            state_mf = {
                "pose": "triumphant", "t": t,
                "brow": "happy", "eye": "wink" if dt_end > 3.0 else "normal",
                "mouth": "smile", "talk": (dt_end < 3.2), "glow": 1.0
            }
            draw_mr_flow(ctx, 540, FLOOR_Y - 260, scale=1.65, state=state_mf)
            subtitle = "WATCH LIVE AT FLOWORKOS.COM!" if t < 55.0 else "PUT AN ENTIRE AI TEAM ON YOUR PAYROLL!"
            
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
            
        if (f + 1) % 300 == 0:
            print(f"  Frame {f+1}/{TOTAL_FRAMES} ({(f+1)/TOTAL_FRAMES*100:.0f}%) rendered...")
            
    proc.stdin.close()
    proc.wait()
    print("✅ 58-Second Video encoded successfully with NVENC!")
    
    print("📸 Creating 12-frame contact sheet...")
    cs_w, cs_h = 2880, 2160
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
    print(f"📸 Contact sheet saved to {CONTACT_SHEET_PNG}!")
    
    subprocess.run(["cp", "-f", OUT_MP4, USER_OUT_DIR], check=True)
    subprocess.run(["cp", "-f", CONTACT_SHEET_PNG, USER_OUT_DIR], check=True)
    print(f"📁 Video & Contact Sheet copied to {USER_OUT_DIR}!")

if __name__ == "__main__":
    render_58s_cartoon()
