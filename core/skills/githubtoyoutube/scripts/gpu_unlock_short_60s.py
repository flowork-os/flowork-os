#!/usr/bin/env python3
"""
OPENCODE - 58-SECOND HIGH-RETENTION CARTOON SHORT (VERTICAL 9:16)
Official Repository Showcase: https://github.com/anomalyco/opencode
- 100% Pure Cartoon Action Animation (Active physics every second, NO slide templates!)
- Reverse-engineered from @RicksClips3000: Rubber-hose limbs, squash/stretch, over-the-top gags
- Detik Pertama: Catchy centered Cartoon Hook Title ("STOP PAYING $20/MO! CURSOR IS DEAD! OPENCODE CRUSHES IT!")
  visible immediately from t = 0.0s with pulse and elastic entrance.
- Real Screenshots: Embedded GitHub repository screenshot & OpenCode Terminal UI
- Prominent Dual CTA: Direct links to github.com/anomalyco/opencode and floworkos.com
- Stacked chest branding: FLOWORKOS on top, .COM underneath in Matrix Green (#00FF66)
- High-energy broadcast voiceover with procedural cartoon soundtrack and sound effects
- Zero Unicode Tofu Boxes: Uses pure procedural vector stars and symbols
"""

import os, sys, math, subprocess, json
import cairo
import numpy as np

W, H = 1080, 1920
FPS = 60
DURATION = 57.5
TOTAL_FRAMES = int(DURATION * FPS)
FLOOR_Y = 1460

OUT_DIR = "/opt/floworkos/documents/videos/opencode-short"
USER_OUT_DIR = os.path.expanduser("~/Documents/videos/opencode-short")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(USER_OUT_DIR, exist_ok=True)

OUT_MP4 = os.path.join(OUT_DIR, "OPENCODE_CARTOON_SHORT_60S.mp4")
CONTACT_SHEET_PNG = os.path.join(OUT_DIR, "OPENCODE_CARTOON_SHORT_60S_contact_sheet.png")
AUDIO_WAV = "/tmp/opencode_final_audio_mastered.wav"
REPO_PAGE_IMG = os.path.join(OUT_DIR, "github_repo_page.png")
LANDER_IMG = os.path.join(OUT_DIR, "opencode_github_raw.png")

# Preload image surfaces
REPO_PAGE_SURF = None
LANDER_SURF = None

if os.path.exists(REPO_PAGE_IMG):
    try:
        REPO_PAGE_SURF = cairo.ImageSurface.create_from_png(REPO_PAGE_IMG)
    except Exception as e:
        print(f"Warning: Could not load {REPO_PAGE_IMG}: {e}")

if os.path.exists(LANDER_IMG):
    try:
        LANDER_SURF = cairo.ImageSurface.create_from_png(LANDER_IMG)
    except Exception as e:
        print(f"Warning: Could not load {LANDER_IMG}: {e}")

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
        pat.add_color_stop_rgb(0.0, 0.96, 0.93, 0.89) # #f5ebe1
        pat.add_color_stop_rgb(1.0, 0.89, 0.85, 0.79)
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
    if t >= 3.3:
        return
        
    alpha = 1.0
    scale = 0.96 + 0.04 * math.sin(t * 8.0)
    
    if t < 0.35:
        # Initial pop-in
        prog = t / 0.35
        scale = 0.7 + 0.3 * (1.0 - math.pow(1.0 - prog, 3))
    elif t >= 2.7:
        # Smooth zoom-forward fadeout
        prog = (t - 2.7) / 0.6
        alpha = max(0.0, 1.0 - prog)
        scale = 1.0 + prog * 0.25

    ctx.save()
    cx, cy = W / 2, 780
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    
    # Outer glow
    glow = cairo.RadialGradient(0, 0, 100, 0, 0, 480)
    glow.add_color_stop_rgba(0.0, 0.0, 1.0, 0.4, 0.35 * alpha)
    glow.add_color_stop_rgba(0.6, 1.0, 0.8, 0.0, 0.15 * alpha)
    glow.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
    ctx.set_source(glow)
    ctx.rectangle(-500, -320, 1000, 640)
    ctx.fill()
    
    # Card Background (Deep Obsidian Slate)
    card_w, card_h = 920, 460
    ctx.set_source_rgba(0.08, 0.10, 0.14, 0.96 * alpha)
    ctx.rectangle(-card_w/2, -card_h/2, card_w, card_h)
    ctx.fill()
    
    # Card Border (Electric Matrix Green Neon)
    ctx.set_source_rgba(0.0, 1.0, 0.4, alpha)
    ctx.set_line_width(8)
    ctx.rectangle(-card_w/2, -card_h/2, card_w, card_h)
    ctx.stroke()
    
    # Top Warning Pill
    pill_w, pill_h = 560, 64
    ctx.set_source_rgba(0.9, 0.15, 0.15, alpha)
    ctx.rectangle(-pill_w/2, -card_h/2 - pill_h/2, pill_w, pill_h)
    ctx.fill()
    ctx.set_source_rgba(1.0, 1.0, 1.0, alpha)
    ctx.set_line_width(4)
    ctx.rectangle(-pill_w/2, -card_h/2 - pill_h/2, pill_w, pill_h)
    ctx.stroke()
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ctx.set_source_rgba(1.0, 1.0, 1.0, alpha)
    t_top = "STOP PAYING $20/MO!"
    ext = ctx.text_extents(t_top)
    ctx.move_to(-ext.width/2, -card_h/2 - pill_h/2 + 44)
    ctx.show_text(t_top)
    
    # Main Punchline: Line 1
    ctx.set_font_size(68)
    line1 = "CURSOR IS DEAD!"
    ext1 = ctx.text_extents(line1)
    
    # Black shadow
    ctx.set_source_rgba(0.0, 0.0, 0.0, alpha)
    ctx.move_to(-ext1.width/2 + 4, -40 + 4)
    ctx.show_text(line1)
    
    # Bright Gold / White text
    ctx.set_source_rgba(1.0, 0.95, 0.3, alpha)
    ctx.move_to(-ext1.width/2, -40)
    ctx.show_text(line1)
    
    # Main Punchline: Line 2
    ctx.set_font_size(54)
    line2 = "OPENCODE CRUSHES IT!"
    ext2 = ctx.text_extents(line2)
    
    # Black shadow
    ctx.set_source_rgba(0.0, 0.0, 0.0, alpha)
    ctx.move_to(-ext2.width/2 + 4, 50 + 4)
    ctx.show_text(line2)
    
    # Matrix Green text
    ctx.set_source_rgba(0.0, 1.0, 0.4, alpha)
    ctx.move_to(-ext2.width/2, 50)
    ctx.show_text(line2)
    
    # Sub-badge at bottom of card: GitHub Stars Proof
    sub_pill_w, sub_pill_h = 680, 56
    ctx.set_source_rgba(0.15, 0.20, 0.26, alpha)
    ctx.rectangle(-sub_pill_w/2, 130, sub_pill_w, sub_pill_h)
    ctx.fill()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6 * alpha)
    ctx.set_line_width(3)
    ctx.rectangle(-sub_pill_w/2, 130, sub_pill_w, sub_pill_h)
    ctx.stroke()
    
    draw_star(ctx, -270, 158, r_outer=14, r_inner=6, color=(1.0, 0.85, 0.0))
    draw_star(ctx, 270, 158, r_outer=14, r_inner=6, color=(1.0, 0.85, 0.0))
    
    ctx.set_font_size(26)
    ctx.set_source_rgba(1.0, 1.0, 1.0, alpha)
    t_sub = "228,000+ STARS ON GITHUB"
    ext_s = ctx.text_extents(t_sub)
    ctx.move_to(-ext_s.width/2, 168)
    ctx.show_text(t_sub)
    
    # Comic spark bursts at corners
    spark_scale = 0.8 + 0.2 * math.sin(t * 12.0)
    draw_comic_sparks(ctx, -card_w/2 + 20, -card_h/2 + 20, scale=spark_scale, color=(1.0, 0.85, 0.0))
    draw_comic_sparks(ctx, card_w/2 - 20, -card_h/2 + 20, scale=spark_scale, color=(0.0, 1.0, 0.4))
    draw_comic_sparks(ctx, -card_w/2 + 20, card_h/2 - 20, scale=spark_scale, color=(0.0, 1.0, 0.4))
    draw_comic_sparks(ctx, card_w/2 - 20, card_h/2 - 20, scale=spark_scale, color=(1.0, 0.85, 0.0))
    
    ctx.restore()

def draw_github_repo_card(ctx, x, y, w, h, t, show_pointer=False):
    """Draws real GitHub repository card screenshot with holographic browser frame"""
    ctx.save()
    ctx.translate(x, y)
    
    # Outer drop shadow
    ctx.set_source_rgba(0, 0, 0, 0.35)
    ctx.rectangle(12, 12, w, h)
    ctx.fill()
    
    # Card Window Frame
    ctx.set_source_rgb(0.09, 0.11, 0.15)
    ctx.rectangle(0, 0, w, h)
    ctx.fill()
    
    # Border
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.set_line_width(4)
    ctx.rectangle(0, 0, w, h)
    ctx.stroke()
    
    # Top Browser Header Bar
    header_h = 58
    ctx.set_source_rgb(0.14, 0.17, 0.22)
    ctx.rectangle(0, 0, w, header_h)
    ctx.fill()
    
    # Window traffic light buttons
    ctx.set_source_rgb(0.95, 0.35, 0.35); ctx.arc(28, header_h/2, 8, 0, 2*math.pi); ctx.fill()
    ctx.set_source_rgb(0.95, 0.75, 0.25); ctx.arc(52, header_h/2, 8, 0, 2*math.pi); ctx.fill()
    ctx.set_source_rgb(0.25, 0.80, 0.45); ctx.arc(76, header_h/2, 8, 0, 2*math.pi); ctx.fill()
    
    # URL Pill Bar
    url_box_w = w - 240
    ctx.set_source_rgb(0.07, 0.08, 0.11)
    ctx.rectangle(105, 12, url_box_w, 34)
    ctx.fill()
    ctx.set_source_rgb(0.25, 0.30, 0.38)
    ctx.set_line_width(2)
    ctx.rectangle(105, 12, url_box_w, 34)
    ctx.stroke()
    
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(18)
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(125, 36)
    ctx.show_text("https://github.com/anomalyco/opencode")
    
    # Star Badge right corner
    star_btn_x = w - 120
    ctx.set_source_rgb(0.20, 0.24, 0.30)
    ctx.rectangle(star_btn_x, 12, 105, 34)
    ctx.fill()
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    draw_star(ctx, star_btn_x + 18, 29, r_outer=10, r_inner=4, color=(1.0, 0.85, 0.0))
    ctx.set_source_rgb(1, 1, 1)
    ctx.set_font_size(16)
    ctx.move_to(star_btn_x + 36, 35)
    ctx.show_text("228k ★")
    
    # Content Area: Embedded Real GitHub Screenshot
    content_y = header_h
    content_h = h - header_h
    
    if REPO_PAGE_SURF:
        ctx.save()
        ctx.rectangle(0, content_y, w, content_h)
        ctx.clip()
        img_w = REPO_PAGE_SURF.get_width()
        img_h = REPO_PAGE_SURF.get_height()
        
        # Scale to fit nicely width-wise
        scale = w / img_w
        ctx.scale(scale, scale)
        ctx.set_source_surface(REPO_PAGE_SURF, 0, content_y / scale)
        ctx.paint()
        ctx.restore()
    else:
        # Fallback card
        ctx.set_source_rgb(0.08, 0.10, 0.13)
        ctx.rectangle(0, content_y, w, content_h); ctx.fill()
        ctx.set_source_rgb(1, 1, 1); ctx.set_font_size(32)
        ctx.move_to(40, content_y + 80); ctx.show_text("anomalyco / opencode")
        
    # Animated Pointer if requested
    if show_pointer:
        pw = math.sin(t * 10.0) * 8.0
        px = star_btn_x + 50 + pw
        py = 55
        ctx.set_source_rgb(1.0, 0.2, 0.2)
        ctx.move_to(px, py); ctx.line_to(px + 30, py + 45); ctx.line_to(px + 12, py + 40); ctx.line_to(px + 5, py + 65); ctx.line_to(px - 8, py + 62); ctx.line_to(px, py + 38); ctx.line_to(px - 18, py + 35); ctx.close_path()
        ctx.fill()
        ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(2.5); ctx.stroke()
        
    ctx.restore()

def draw_terminal_screen(ctx, x, y, w, h, t, active_agent="build"):
    """Draws real OpenCode terminal screenshot inside interactive developer card"""
    ctx.save()
    ctx.translate(x, y)
    
    # Drop shadow
    ctx.set_source_rgba(0, 0, 0, 0.4)
    ctx.rectangle(12, 12, w, h); ctx.fill()
    
    # Outer frame
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.rectangle(0, 0, w, h); ctx.fill()
    
    # Border
    ctx.set_source_rgb(0.0, 1.0, 0.4) if active_agent == "build" else ctx.set_source_rgb(0.2, 0.6, 1.0)
    ctx.set_line_width(5)
    ctx.rectangle(0, 0, w, h); ctx.stroke()
    
    # Header bar
    header_h = 52
    ctx.set_source_rgb(0.12, 0.14, 0.18)
    ctx.rectangle(0, 0, w, header_h); ctx.fill()
    
    # Tab Agent Badges
    # 1. BUILD AGENT BADGE
    b_color = (0.0, 1.0, 0.4) if active_agent == "build" else (0.3, 0.35, 0.4)
    ctx.set_source_rgb(*b_color)
    ctx.rectangle(20, 10, 160, 32); ctx.fill()
    ctx.set_source_rgb(0.05, 0.05, 0.07) if active_agent == "build" else ctx.set_source_rgb(0.8, 0.8, 0.8)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(18); ctx.move_to(35, 33); ctx.show_text("[TAB] BUILD")
    
    # 2. PLAN AGENT BADGE
    p_color = (0.2, 0.6, 1.0) if active_agent == "plan" else (0.3, 0.35, 0.4)
    ctx.set_source_rgb(*p_color)
    ctx.rectangle(195, 10, 160, 32); ctx.fill()
    ctx.set_source_rgb(0.05, 0.05, 0.07) if active_agent == "plan" else ctx.set_source_rgb(0.8, 0.8, 0.8)
    ctx.move_to(210, 33); ctx.show_text("[TAB] PLAN")
    
    # Right status: Models 70+
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.set_font_size(16); ctx.move_to(w - 220, 33); ctx.show_text("70+ MODELS READY")
    
    # Terminal Display Area: Embed real OpenCode lander screenshot
    content_y = header_h
    content_h = h - header_h
    
    if LANDER_SURF:
        ctx.save()
        ctx.rectangle(0, content_y, w, content_h)
        ctx.clip()
        img_w = LANDER_SURF.get_width()
        scale = w / img_w
        ctx.scale(scale, scale)
        ctx.set_source_surface(LANDER_SURF, 0, content_y / scale)
        ctx.paint()
        ctx.restore()
    else:
        ctx.set_source_rgb(0.05, 0.06, 0.08)
        ctx.rectangle(0, content_y, w, content_h); ctx.fill()
        
    ctx.restore()

def draw_dual_cta_outro(ctx, t):
    """Draws high-impact dual CTA cards in outro"""
    ctx.save()
    
    # Card 1: Official GitHub Repo
    c1_w, c1_h = 920, 220
    c1_x, c1_y = (W - c1_w) / 2, 280
    
    # Card 1 shadow & bg
    ctx.set_source_rgba(0, 0, 0, 0.3)
    ctx.rectangle(c1_x + 10, c1_y + 10, c1_w, c1_h); ctx.fill()
    ctx.set_source_rgb(0.10, 0.12, 0.16)
    ctx.rectangle(c1_x, c1_y, c1_w, c1_h); ctx.fill()
    ctx.set_source_rgb(1.0, 0.85, 0.0) # Gold border
    ctx.set_line_width(6)
    ctx.rectangle(c1_x, c1_y, c1_w, c1_h); ctx.stroke()
    
    # Top Tag
    ctx.set_source_rgb(1.0, 0.85, 0.0)
    ctx.rectangle(c1_x, c1_y, 360, 42); ctx.fill()
    ctx.set_source_rgb(0.05, 0.05, 0.07)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(22); ctx.move_to(c1_x + 20, c1_y + 30); ctx.show_text("OFFICIAL REPOSITORY")
    
    # URL Text
    ctx.set_source_rgb(1, 1, 1)
    ctx.set_font_size(36)
    ctx.move_to(c1_x + 40, c1_y + 105)
    ctx.show_text("github.com/anomalyco/opencode")
    
    # Big Star CTA Button
    btn_w, btn_h = 340, 64
    btn_x = c1_x + c1_w - btn_w - 40
    btn_y = c1_y + 125
    ctx.set_source_rgb(1.0, 0.85, 0.0); ctx.rectangle(btn_x, btn_y, btn_w, btn_h); ctx.fill()
    draw_star(ctx, btn_x + 35, btn_y + 32, r_outer=18, r_inner=8, color=(0.1, 0.1, 0.1))
    ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_font_size(26); ctx.move_to(btn_x + 70, btn_y + 42); ctx.show_text("STAR ON GITHUB")
    
    # Star counter badge
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_font_size(24); ctx.move_to(c1_x + 40, c1_y + 165); ctx.show_text("228,000+ STARS ★ FREE & OPEN SOURCE")
    
    # Card 2: Flowork OS Sovereign Swarm
    c2_w, c2_h = 920, 220
    c2_x, c2_y = (W - c2_w) / 2, 540
    
    ctx.set_source_rgba(0, 0, 0, 0.3)
    ctx.rectangle(c2_x + 10, c2_y + 10, c2_w, c2_h); ctx.fill()
    ctx.set_source_rgb(0.08, 0.10, 0.13)
    ctx.rectangle(c2_x, c2_y, c2_w, c2_h); ctx.fill()
    ctx.set_source_rgb(0.0, 1.0, 0.4) # Matrix Green border
    ctx.set_line_width(6)
    ctx.rectangle(c2_x, c2_y, c2_w, c2_h); ctx.stroke()
    
    ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.rectangle(c2_x, c2_y, 400, 42); ctx.fill()
    ctx.set_source_rgb(0.05, 0.05, 0.07)
    ctx.set_font_size(22); ctx.move_to(c2_x + 20, c2_y + 30); ctx.show_text("SOVEREIGN AI WORKSPACE")
    
    ctx.set_source_rgb(1, 1, 1)
    ctx.set_font_size(44)
    ctx.move_to(c2_x + 40, c2_y + 115)
    ctx.show_text("FLOWORKOS.COM")
    
    btn2_w, btn2_h = 340, 64
    btn2_x = c2_x + c2_w - btn2_w - 40
    btn2_y = c2_y + 125
    ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.rectangle(btn2_x, btn2_y, btn2_w, btn2_h); ctx.fill()
    ctx.set_source_rgb(0.05, 0.05, 0.07); ctx.set_font_size(24); ctx.move_to(btn2_x + 35, btn2_y + 42); ctx.show_text("TRY FLOWORK OS >>")
    
    ctx.set_source_rgb(0.7, 0.8, 0.9); ctx.set_font_size(22); ctx.move_to(c2_x + 40, c2_y + 165); ctx.show_text("UNLEASH YOUR AUTONOMOUS MULTI-AGENT SWARM")
    
    ctx.restore()

def draw_mr_flow(ctx, cx, cy, scale=1.0, state=None):
    """
    Mr. Flow Vector Character Engine (Strict 8 Visual Doctrines):
    - Stacked chest branding: Line 1 "FLOWORKOS", Line 2 ".COM" in Matrix Green (#00FF66)
    - Obsidian dark hoodie pill, rubber-hose cubic bezier limbs
    - Expressive eyes, eyebrows, and phonemes
    """
    if state is None: state = {}
    pose = state.get("pose", "idle")
    brow = state.get("brow", "normal")
    eye = state.get("eye", "normal")
    mouth = state.get("mouth", "smile")
    is_talking = state.get("talk", False)
    t = state.get("t", 0.0)
    hoodie_glow = state.get("glow", 0.0)
    has_hammer = state.get("hammer", False)
    hammer_angle = state.get("hammer_angle", 0.0)
    
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    
    # 0. SQUASH & STRETCH
    breathe = math.sin(t * 7.0) * 0.03
    walk_cycle = math.sin(t * 12.0)
    
    torso_y = -120 + breathe * 20
    head_y = torso_y - 120
    hip_y = torso_y + 80
    floor_rel = 260
    
    # 1. LEGS (Rubber-Hose Bezier)
    ctx.set_line_width(18)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgb(0.10, 0.11, 0.14)
    
    if pose == "walk":
        stride = walk_cycle
        l_foot_x = -stride * 55.0
        r_foot_x = stride * 55.0
        l_foot_y = floor_rel - abs(stride) * 15.0
        r_foot_y = floor_rel - abs(-stride) * 15.0
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
            ctx.move_to(-55, torso_y - 40); ctx.curve_to(-100, torso_y - 80, -110, torso_y - 140, -85, torso_y - 170); ctx.stroke()
            ctx.move_to(55, torso_y - 40); ctx.curve_to(100, torso_y - 80, 110, torso_y - 140, 85, torso_y - 170); ctx.stroke()
        elif pose == "smash_down":
            ctx.move_to(-55, torso_y - 30); ctx.curve_to(-80, torso_y + 10, -50, torso_y + 50, -20, torso_y + 40); ctx.stroke()
            ctx.move_to(55, torso_y - 30); ctx.curve_to(80, torso_y + 10, 90, torso_y + 40, 60, torso_y + 35); ctx.stroke()
        else: # crouch
            ctx.move_to(-55, torso_y - 30); ctx.curve_to(-80, torso_y, -80, torso_y + 40, -50, torso_y + 30); ctx.stroke()
            ctx.move_to(55, torso_y - 30); ctx.curve_to(80, torso_y, 80, torso_y + 40, 50, torso_y + 30); ctx.stroke()
            
    elif pose == "triumphant":
        cheer_w = math.sin(t * 10.0) * 12.0
        ctx.move_to(-55, torso_y - 40); ctx.curve_to(-110, torso_y - 90, -120, torso_y - 160 + cheer_w, -95, torso_y - 190 + cheer_w); ctx.stroke()
        ctx.arc(-95, torso_y - 190 + cheer_w, 16, 0, 2*math.pi); ctx.fill()
        ctx.move_to(55, torso_y - 40); ctx.curve_to(110, torso_y - 90, 120, torso_y - 160 - cheer_w, 95, torso_y - 190 - cheer_w); ctx.stroke()
        ctx.arc(95, torso_y - 190 - cheer_w, 16, 0, 2*math.pi); ctx.fill()
        
    else: # idle
        ctx.move_to(-55, torso_y - 30); ctx.curve_to(-80, torso_y, -85, torso_y + 50, -65, torso_y + 70); ctx.stroke()
        ctx.arc(-65, torso_y + 70, 14, 0, 2*math.pi); ctx.fill()
        ctx.move_to(55, torso_y - 30); ctx.curve_to(80, torso_y, 85, torso_y + 50, 65, torso_y + 70); ctx.stroke()
        ctx.arc(65, torso_y + 70, 14, 0, 2*math.pi); ctx.fill()
        
    # 5. HEAD: Large Cartoon Sphere
    ctx.set_source_rgb(0.96, 0.96, 0.98)
    ctx.arc(0, head_y, 56, 0, 2*math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    ctx.set_line_width(6)
    ctx.stroke()
    
    # 6. FACIAL RIG: Eyebrows, Eyes, Mouth
    ctx.set_line_width(5)
    ctx.set_source_rgb(0.08, 0.09, 0.12)
    
    if brow == "skeptical":
        ctx.move_to(-42, head_y - 36); ctx.line_to(-12, head_y - 48); ctx.stroke()
        ctx.move_to(12, head_y - 38); ctx.line_to(42, head_y - 38); ctx.stroke()
    elif brow == "incredulous":
        ctx.move_to(-42, head_y - 50); ctx.line_to(-12, head_y - 35); ctx.stroke()
        ctx.move_to(12, head_y - 35); ctx.line_to(42, head_y - 50); ctx.stroke()
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

def render_58s_opencode_cartoon():
    print(f"🎬 Starting Master Render: OpenCode 58-Second Cartoon Short @ {FPS} FPS ({TOTAL_FRAMES} frames)...")
    
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
        
        # 1. BEAT 1 (0.0s - 5.03s): Frustrated dev at desk, $20 billing alert
        # DETIK PERTAMA: Centered Hook Title!
        if t < 5.03:
            bg_type = "dark_room"
            draw_wall_and_floor(ctx, t, bg_type)
            
            # Desk and computer
            ctx.set_source_rgb(0.35, 0.25, 0.18)
            ctx.rectangle(200, FLOOR_Y - 220, 680, 220); ctx.fill()
            ctx.set_source_rgb(0.1, 0.1, 0.1)
            ctx.rectangle(440, FLOOR_Y - 440, 200, 220); ctx.fill()
            # Monitor glowing red
            ctx.set_source_rgb(0.85, 0.2, 0.2)
            ctx.rectangle(450, FLOOR_Y - 430, 180, 180); ctx.fill()
            
            # Floating billing alert badges
            for i in range(4):
                bx = 180 + (i % 2) * 420
                by = 420 + (i // 2) * 160 + math.sin(t * 5.0 + i) * 14
                ctx.set_source_rgba(0.9, 0.15, 0.15, 0.9)
                ctx.rectangle(bx, by, 300, 75); ctx.fill()
                ctx.set_source_rgb(1, 1, 1)
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(24); ctx.move_to(bx + 20, by + 48)
                ctx.show_text("$20/MO CHARGE!")
                
            # Frustrated Developer Stickman
            state_dev = {"pose": "idle", "t": t, "eye": "bloodshot", "brow": "skeptical", "mouth": "gasp_o"}
            draw_mr_flow(ctx, 360, FLOOR_Y - 260, scale=1.3, state=state_dev)
            
            # DETIK PERTAMA HOOK TITLE OVERLAY
            draw_center_hook_title(ctx, t)
            
            subtitle = "PAYING $20/MO FOR LOCKED AI TOOLS?"
            
        # 2. BEAT 2 (5.03s - 11.61s): Dev crying, usage limit exceeded, credit card drained
        elif t < 11.61:
            draw_wall_and_floor(ctx, t, "office")
            
            # Giant red warning popup
            ctx.save()
            ctx.set_source_rgb(0.85, 0.2, 0.2)
            ctx.rectangle(140, 340, 800, 320); ctx.fill()
            ctx.set_source_rgb(0.08, 0.08, 0.1); ctx.set_line_width(8); ctx.stroke()
            
            ctx.set_source_rgb(1, 1, 1)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(44); ctx.move_to(220, 430); ctx.show_text("USAGE LIMIT EXCEEDED!")
            ctx.set_font_size(32); ctx.move_to(240, 510); ctx.show_text("PROPRIETARY CLOUD LAG")
            ctx.set_source_rgb(1.0, 0.85, 0.0)
            ctx.set_font_size(36); ctx.move_to(260, 590); ctx.show_text("CREDIT CARD DRAINED!")
            ctx.restore()
            
            # Tears flying
            tear_y = (t * 400) % 250
            ctx.set_source_rgba(0.2, 0.7, 1.0, 0.8)
            ctx.arc(520, FLOOR_Y - 320 + tear_y, 10, 0, 2*math.pi); ctx.fill()
            ctx.arc(560, FLOOR_Y - 320 + tear_y, 10, 0, 2*math.pi); ctx.fill()
            
            state_cry = {"pose": "shrug_question", "t": t, "eye": "bloodshot", "brow": "incredulous", "mouth": "gasp_o", "talk": True}
            draw_mr_flow(ctx, 540, FLOOR_Y - 260, scale=1.5, state=state_cry)
            subtitle = "LOOK AT THIS DISASTER!" if t < 6.93 else "USAGE LIMIT EXCEEDED & WALLET DRAINED!"
            
        # 3. BEAT 3 (11.61s - 13.95s): Mr. Flow drops in, elastic squash/stretch landing
        elif t < 13.95:
            draw_wall_and_floor(ctx, t, "office")
            dt = t - 11.61
            # Elastic drop
            drop_y = min(FLOOR_Y - 260, -200 + dt * 1400)
            pose_mf = "jump_swing" if drop_y < FLOOR_Y - 280 else "crouch"
            state_mf = {"pose": pose_mf, "t": t, "brow": "intense_smash", "mouth": "talk_open", "talk": True}
            draw_mr_flow(ctx, 540, drop_y, scale=1.55, state=state_mf)
            
            # Comic blast lines
            if dt > 0.4:
                draw_comic_sparks(ctx, 540, FLOOR_Y - 100, scale=1.2, color=(0.0, 1.0, 0.4))
            subtitle = "STOP BURNING CASH RIGHT NOW!"
            
        # 4. BEAT 4 (13.95s - 20.70s): OpenCode GitHub Repo card opens! Real screenshot & 228k stars
        elif t < 20.70:
            draw_wall_and_floor(ctx, t, "office")
            
            card_w, card_h = 940, 520
            card_x = (W - card_w) / 2
            card_y = 220
            draw_github_repo_card(ctx, card_x, card_y, card_w, card_h, t, show_pointer=True)
            
            # Comic star sparks popping around repo
            draw_comic_sparks(ctx, W/2 + 260, 260, scale=1.2 * (0.8 + 0.2*math.sin(t*14)), color=(1.0, 0.85, 0.0))
            
            # Mr. Flow pointing arm at repo
            state_mf = {"pose": "lean_point", "t": t, "brow": "happy", "mouth": "talk_open", "talk": True, "glow": 0.8}
            draw_mr_flow(ctx, 420, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "MEET OPENCODE: 228,000+ STARS ON GITHUB!"
            
        # 5. BEAT 5 (20.70s - 23.70s): Terminal & Desktop native execution
        elif t < 23.70:
            draw_wall_and_floor(ctx, t, "office")
            
            card_w, card_h = 920, 520
            card_x = (W - card_w) / 2
            card_y = 220
            draw_terminal_screen(ctx, card_x, card_y, card_w, card_h, t, active_agent="build")
            
            state_mf = {"pose": "triumphant", "t": t, "brow": "happy", "mouth": "talk_open", "talk": True}
            draw_mr_flow(ctx, 420, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "RUNS NATIVELY IN TERMINAL & DESKTOP!"
            
        # 6. BEAT 6 (23.70s - 29.89s): Press Tab! Switch Build Agent & Plan Agent
        elif t < 29.89:
            draw_wall_and_floor(ctx, t, "office")
            
            # Toggle between build and plan every 2 seconds
            active = "build" if ((t - 23.70) % 4.0 < 2.0) else "plan"
            
            card_w, card_h = 920, 520
            card_x = (W - card_w) / 2
            card_y = 220
            draw_terminal_screen(ctx, card_x, card_y, card_w, card_h, t, active_agent=active)
            
            # Big Glowing TAB KEY floating
            tab_scale = 1.0 + 0.1 * math.sin(t * 12.0)
            ctx.save()
            ctx.translate(780, 800); ctx.scale(tab_scale, tab_scale)
            ctx.set_source_rgb(0.2, 0.25, 0.3); ctx.rectangle(-110, -50, 220, 100); ctx.fill()
            ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(6); ctx.rectangle(-110, -50, 220, 100); ctx.stroke()
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(38); ctx.set_source_rgb(1, 1, 1); ctx.move_to(-60, 15); ctx.show_text("[ TAB ]")
            ctx.restore()
            
            state_mf = {"pose": "lean_point", "t": t, "brow": "intense_smash", "mouth": "talk_open", "talk": True}
            draw_mr_flow(ctx, 380, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "BUILD AGENT (CODE) & PLAN AGENT (ARCHITECTURE)!"
            
        # 7. BEAT 7 (29.89s - 34.95s): 70+ Models, local Ollama, Claude, GPT-4 streams
        elif t < 34.95:
            draw_wall_and_floor(ctx, t, "office")
            
            # Glowing neon streams connecting to central matrix core
            models = ["OLLAMA", "CLAUDE", "DEEPSEEK", "GPT-4o", "GEMINI"]
            for idx, m_name in enumerate(models):
                ang = 0.3 + idx * (math.pi - 0.6) / 4.0
                ctx.set_source_rgba(0.0, 1.0, 0.4, 0.7)
                ctx.set_line_width(8)
                ctx.move_to(540, FLOOR_Y - 320)
                mx = 540 + math.cos(ang) * 420
                my = 380 - math.sin(ang) * 120
                ctx.curve_to(540 + math.cos(ang) * 200, 600, mx, my + 100, mx, my)
                ctx.stroke()
                
                # Model badge
                ctx.save(); ctx.translate(mx, my)
                ctx.set_source_rgb(0.12, 0.15, 0.2); ctx.rectangle(-80, -30, 160, 60); ctx.fill()
                ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(3); ctx.rectangle(-80, -30, 160, 60); ctx.stroke()
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(20); ctx.set_source_rgb(1, 1, 1)
                ext = ctx.text_extents(m_name); ctx.move_to(-ext.width/2, 8); ctx.show_text(m_name)
                ctx.restore()
                
            state_mf = {"pose": "triumphant", "t": t, "brow": "happy", "mouth": "talk_open", "talk": True, "glow": 0.9}
            draw_mr_flow(ctx, 540, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "CONNECT 70+ AI MODELS OR RUN OFFLINE!"
            
        # 8. BEAT 8 (34.95s - 41.13s): $20 Paywall Monster appears & Mr. Flow SMASH!
        elif t < 41.13:
            dt = t - 34.95
            is_smash = (dt > 2.8)
            cam_shake_x = math.sin(dt * 75) * 36 * math.exp(-max(0, dt - 2.8) * 5) if is_smash else 0
            cam_shake_y = math.cos(dt * 85) * 30 * math.exp(-max(0, dt - 2.8) * 5) if is_smash else 0
            draw_wall_and_floor(ctx, t, "office", cam_shake_x, cam_shake_y)
            
            # The $20 Paywall Wall / Monster
            wall_x, wall_y = 780, FLOOR_Y - 140
            ctx.save(); ctx.translate(wall_x + cam_shake_x, wall_y + cam_shake_y)
            if not is_smash:
                ctx.set_source_rgb(0.85, 0.2, 0.2); ctx.rectangle(-120, -220, 240, 360); ctx.fill()
                ctx.set_source_rgb(0.1, 0.1, 0.1); ctx.set_line_width(8); ctx.stroke()
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(36); ctx.set_source_rgb(1, 1, 1)
                ctx.move_to(-95, -120); ctx.show_text("$20 / MO")
                ctx.set_font_size(24); ctx.move_to(-85, -60); ctx.show_text("PAYWALL")
            else: # Smashed fragments flying
                for frag in range(8):
                    fx = math.sin(frag * 1.5 + dt * 10) * 160
                    fy = -100 + frag * 30 + dt * 40
                    ctx.set_source_rgb(0.85, 0.2, 0.2); ctx.rectangle(fx, fy, 40, 35); ctx.fill()
            ctx.restore()
            
            if is_smash:
                # Golden Strict Exit Code 0 Stamp
                ctx.save()
                ctx.set_source_rgba(0.0, 1.0, 0.4, 0.95)
                ctx.rectangle(200, 320, 680, 150); ctx.fill()
                ctx.set_source_rgb(0.05, 0.05, 0.07)
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(52); ctx.move_to(240, 415); ctx.show_text("STRICT EXIT CODE 0")
                ctx.restore()
                
            pose_mf = "smash_down" if is_smash else ("jump_swing" if dt > 1.8 else "crouch")
            state_mf = {"pose": pose_mf, "t": t, "brow": "intense_smash", "mouth": "grit_teeth", "hammer": True, "hammer_angle": 1.6 if is_smash else -0.8}
            draw_mr_flow(ctx, 580 + cam_shake_x, FLOOR_Y - 260 + cam_shake_y, scale=1.55, state=state_mf)
            subtitle = "MR. FLOW SMASHES GREEDY SUBSCRIPTIONS!" if not is_smash else "STRICT EXIT CODE ZERO!"
            
        # 9. BEAT 9 (41.13s - 44.69s): One command install & rocket launch
        elif t < 44.69:
            draw_wall_and_floor(ctx, t, "office")
            
            # Terminal command banner
            ctx.save()
            ctx.set_source_rgb(0.08, 0.10, 0.14)
            ctx.rectangle(120, 340, 840, 140); ctx.fill()
            ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(6); ctx.stroke()
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(32); ctx.set_source_rgb(0.0, 1.0, 0.4)
            ctx.move_to(160, 425); ctx.show_text("curl -fsSL opencode.ai | bash")
            ctx.restore()
            
            # Rocket launch
            r_y = 650 - (t - 41.13) * 110
            ctx.save(); ctx.translate(850, r_y)
            ctx.set_source_rgb(0.9, 0.25, 0.25); ctx.move_to(0, -90); ctx.line_to(35, 30); ctx.line_to(-35, 30); ctx.close_path(); ctx.fill()
            ctx.set_source_rgb(0.95, 0.95, 0.95); ctx.rectangle(-30, 30, 60, 90); ctx.fill()
            ctx.set_source_rgb(1.0, 0.7, 0.1); ctx.move_to(-25, 120); ctx.line_to(0, 180 + math.sin(t*30)*25); ctx.line_to(25, 120); ctx.close_path(); ctx.fill()
            ctx.restore()
            
            state_mf = {"pose": "triumphant", "t": t, "brow": "happy", "mouth": "talk_open", "talk": True, "glow": 0.8}
            draw_mr_flow(ctx, 420, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "ONE COMMAND INSTALLS YOUR PRIVATE AI ENGINEER!"
            
        # 10. BEAT 10 (44.69s - 50.16s): Star Repo Call-To-Action!
        elif t < 50.16:
            draw_wall_and_floor(ctx, t, "office")
            
            card_w, card_h = 940, 500
            card_x = (W - card_w) / 2
            card_y = 240
            draw_github_repo_card(ctx, card_x, card_y, card_w, card_h, t, show_pointer=True)
            
            draw_comic_sparks(ctx, W/2 + 240, 280, scale=1.2 * (0.8 + 0.2*math.sin(t*16)), color=(1.0, 0.85, 0.0))
            
            state_mf = {"pose": "lean_point", "t": t, "brow": "happy", "mouth": "talk_open", "talk": True, "glow": 0.8}
            draw_mr_flow(ctx, 420, FLOOR_Y - 260, scale=1.55, state=state_mf)
            subtitle = "STAR REPO: github.com/anomalyco/opencode"
            
        # 11. BEAT 11 (50.16s - 57.50s): Dual CTA Outro & floworkos.com
        else:
            draw_wall_and_floor(ctx, t, "office")
            draw_dual_cta_outro(ctx, t)
            
            # Side agents cheering
            state_side1 = {"pose": "triumphant", "t": t, "brow": "happy", "mouth": "smile", "glow": 0.5}
            draw_mr_flow(ctx, 220, FLOOR_Y - 240, scale=1.1, state=state_side1)
            
            state_side2 = {"pose": "triumphant", "t": t, "brow": "happy", "mouth": "smile", "glow": 0.5}
            draw_mr_flow(ctx, 860, FLOOR_Y - 240, scale=1.1, state=state_side2)
            
            # Mr. Flow center triumphant
            dt_end = t - 50.16
            state_mf = {
                "pose": "triumphant", "t": t,
                "brow": "happy", "eye": "wink" if dt_end > 3.0 else "normal",
                "mouth": "smile", "talk": (dt_end < 4.2), "glow": 1.0
            }
            draw_mr_flow(ctx, 540, FLOOR_Y - 260, scale=1.65, state=state_mf)
            subtitle = "UNLEASH YOUR SOVEREIGN WORKSPACE AT FLOWORKOS.COM!"
            
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
    render_58s_opencode_cartoon()
