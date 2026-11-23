#!/usr/bin/env python3
"""
🎬 MASTER OPENCLAW DOCUMENTARY ASSEMBLER (NVENC HARDWARE ACCELERATED)
Autonomous Flowork OS Video Foundry for 'openclaw/openclaw' (395,000+ Stars).

Standards Enforced:
1. High-Contrast Inversion: Warm non-white bright architectural backgrounds (Kraft, Cream, Mint, Amber, Slate).
2. Dark Matte Elements: Obsidian frosted cards (#0c1117) & Dark matte stickman (#12161f).
3. Mandatory Branding: Permanent Matrix Green (#00ff66) 'FLOWORKOS.COM' badge on chest.
4. Kinetic Variety: 16 dynamic poses (walking, bouncing, salto, hanging, sitting with laptop, turbo sprint, splat, hover, peeking, confused, thinking, leaning, heavy lifting, panic, victory jump, macro camera zoom 2.5x).
5. Dynamic Virtual Camera Zoom: Smooth punch-ins into face and punchlines.
6. Deliverables: Full MP4, Subtitles (.srt), High-CTR Thumbnail, 12-Frame Contact Sheet, SEO Package.
"""

import os
import sys
import math
import argparse
import subprocess
import cairo

SKILL_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SKILL_SCRIPTS_DIR)
import stickman_engine_v2 as eng
import openclaw_cadence_director as cadence

WIDTH = 1920
HEIGHT = 1080
FPS = 30
REPO_URL = "https://github.com/openclaw/openclaw"
PIPELINE_DIR = "/opt/floworkos/pipelines/stickman_openclaw_documentary"
THEME_VAULT = "/opt/floworkos/documents/videos/openclaw-documentary"
USER_VAULT = os.path.expanduser("~/Documents/videos/openclaw-documentary")

# Preload cues for all 6 chapters
CHAPTER_CUES = {
    ch: eng.parse_srt(os.path.join(PIPELINE_DIR, f"ch{ch}_voice.srt"))
    for ch in range(1, 7)
}

BG_PALETTES = {
    "kraft": ((0.94, 0.91, 0.86), (0.88, 0.84, 0.78)),
    "cream": ((0.96, 0.93, 0.89), (0.91, 0.88, 0.83)),
    "sage":  ((0.86, 0.91, 0.88), (0.80, 0.86, 0.83)),
    "amber": ((0.93, 0.89, 0.82), (0.86, 0.82, 0.74)),
    "slate": ((0.88, 0.90, 0.91), (0.83, 0.85, 0.87)),
}

# ------------------------------------------------------------------------------
# VIRTUAL CAMERA & COMPOSITING UTILITIES
# ------------------------------------------------------------------------------

def apply_virtual_camera(ctx, target_x, target_y, zoom=1.0, roll=0.0):
    """Punches the virtual camera into target_x, target_y with zoom & roll."""
    if zoom <= 1.001 and abs(roll) < 0.001:
        return
    ctx.translate(WIDTH / 2.0, HEIGHT / 2.0)
    ctx.scale(zoom, zoom)
    if roll != 0.0:
        ctx.rotate(roll)
    ctx.translate(-target_x, -target_y)


def draw_openclaw_header_bar(ctx, t):
    """Sovereign top telemetry bar with OpenClaw repo identity."""
    ctx.save()
    ctx.set_source_rgba(0.04, 0.07, 0.10, 0.95)
    ctx.rectangle(40, 20, WIDTH - 80, 52); ctx.fill()
    ctx.set_source_rgba(0.0, 1.0, 0.4, 0.90); ctx.set_line_width(1.8)
    ctx.rectangle(40, 20, WIDTH - 80, 52); ctx.stroke()

    # Red lobster icon badge
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(18); ctx.set_source_rgb(1.0, 0.35, 0.25)
    ctx.move_to(65, 52); ctx.show_text("🦞 OPENCLAW // REPO DEEP DIVE")

    ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(13); ctx.set_source_rgba(0.0, 1.0, 0.4, 0.95)
    ctx.move_to(450, 52); ctx.show_text("github.com/openclaw/openclaw")

    # Star badge
    ctx.set_source_rgba(1.0, 0.85, 0.2, 0.95)
    ctx.move_to(WIDTH - 380, 52); ctx.show_text("★ 395,000+ STARS (MIT)")

    ctx.set_source_rgba(0.8, 0.9, 1.0, 0.85)
    ctx.move_to(WIDTH - 180, 52); ctx.show_text("PORT: 18789")
    ctx.restore()


def draw_openclaw_beat_card(ctx, ch_num, t, active_cue_idx, beat_spec, x=180, y=95, w=1560, h=610):
    """Renders dark frosted card (#0c1117) with glowing neon rim and rich content."""
    ctx.save()
    title = beat_spec.get("title", f"CHAPTER {ch_num}")
    cat = beat_spec.get("cat", "SYSTEM")
    card_type = beat_spec.get("type", "quote")

    eng.draw_dark_card(ctx, x, y, w, h, f"[{cat}] {title}")

    # Inner Card Layout
    cx = x + w / 2.0
    cy = y + h / 2.0

    if card_type == "quote":
        quote_text = beat_spec.get("quote", "")
        author = beat_spec.get("author", "")
        ctx.save()
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.25)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(90); ctx.move_to(x + 50, y + 150); ctx.show_text('“')
        ctx.set_source_rgb(0.95, 0.98, 1.0)
        ctx.set_font_size(24)
        for idx, line in enumerate(quote_text.split("\n")):
            ctx.move_to(x + 120, y + 170 + idx * 38); ctx.show_text(line)
        ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_font_size(17)
        ctx.move_to(x + 120, y + 270); ctx.show_text(f"— {author}")
        ctx.restore()

    elif card_type == "metric":
        stat = beat_spec.get("stat", "")
        sub = beat_spec.get("sub", "")
        col = beat_spec.get("col", (0.0, 1.0, 0.4))
        ctx.save()
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(68); ctx.set_source_rgb(*col)
        ctx.move_to(x + 80, y + 210); ctx.show_text(stat)
        ctx.set_font_size(20); ctx.set_source_rgba(0.85, 0.92, 1.0, 0.95)
        ctx.move_to(x + 85, y + 270); ctx.show_text(sub)
        ctx.restore()

    elif card_type == "comparison":
        left = beat_spec.get("left", "")
        right = beat_spec.get("right", "")
        col_w = (w - 140) / 2.0
        # Left (Red/Warning)
        ctx.save()
        ctx.set_source_rgba(0.18, 0.05, 0.07, 0.85)
        ctx.rectangle(x + 50, y + 80, col_w, h - 120); ctx.fill()
        ctx.set_source_rgb(1.0, 0.35, 0.35); ctx.set_line_width(1.5)
        ctx.rectangle(x + 50, y + 80, col_w, h - 120); ctx.stroke()
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(18); ctx.move_to(x + 70, y + 125); ctx.show_text("⚠️ THE CLOUD TRAP")
        ctx.set_font_size(15); ctx.set_source_rgba(1.0, 0.9, 0.9, 0.9)
        for i, l in enumerate(left.split("\n")):
            ctx.move_to(x + 70, y + 180 + i * 28); ctx.show_text(l)
        ctx.restore()

        # Right (Matrix Green/Sovereign)
        ctx.save()
        ctx.set_source_rgba(0.04, 0.14, 0.08, 0.85)
        ctx.rectangle(x + 70 + col_w, y + 80, col_w, h - 120); ctx.fill()
        ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(1.5)
        ctx.rectangle(x + 70 + col_w, y + 80, col_w, h - 120); ctx.stroke()
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(18); ctx.move_to(x + 90 + col_w, y + 125); ctx.show_text("🦞 OPENCLAW SOVEREIGNTY")
        ctx.set_font_size(15); ctx.set_source_rgba(0.9, 1.0, 0.9, 0.9)
        for i, l in enumerate(right.split("\n")):
            ctx.move_to(x + 90 + col_w, y + 180 + i * 28); ctx.show_text(l)
        ctx.restore()

    elif card_type == "code":
        file_name = beat_spec.get("file", "source.ts")
        lines = beat_spec.get("lines", [])
        ctx.save()
        # Inner code window
        cw_x, cw_y, cw_w, cw_h = x + 50, y + 70, w - 100, h - 110
        ctx.set_source_rgba(0.02, 0.04, 0.06, 0.95); ctx.rectangle(cw_x, cw_y, cw_w, cw_h); ctx.fill()
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.75); ctx.set_line_width(1.2); ctx.rectangle(cw_x, cw_y, cw_w, cw_h); ctx.stroke()
        # Title bar
        ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(14); ctx.set_source_rgb(0.0, 1.0, 0.4)
        ctx.move_to(cw_x + 20, cw_y + 30); ctx.show_text(f"// FILE: {file_name}")
        # Lines
        ctx.set_font_size(16); ctx.set_source_rgba(0.85, 0.95, 1.0, 0.95)
        for idx, line in enumerate(lines):
            ly = cw_y + 80 + idx * 36
            if line.startswith("//") or line.startswith("--"):
                ctx.set_source_rgba(0.0, 1.0, 0.5, 0.8)
            elif "[FATAL]" in line or "[ALERT]" in line:
                ctx.set_source_rgb(1.0, 0.35, 0.35)
            elif "const" in line or "new" in line or "await" in line:
                ctx.set_source_rgb(0.2, 0.85, 1.0)
            else:
                ctx.set_source_rgba(0.9, 0.95, 1.0, 0.95)
            ctx.move_to(cw_x + 25, ly); ctx.show_text(line)
        ctx.restore()

    elif card_type == "diagram":
        kind = beat_spec.get("kind", "gateway_architecture")
        ctx.save()
        if kind == "gateway_architecture":
            # Gateway Central Node Architecture Diagram
            gw_x, gw_y = cx - 180, cy - 20
            ctx.set_source_rgba(0.04, 0.12, 0.18, 0.95); ctx.rectangle(gw_x - 140, gw_y - 80, 280, 160); ctx.fill()
            ctx.set_source_rgb(0.0, 1.0, 0.4); ctx.set_line_width(2.0); ctx.rectangle(gw_x - 140, gw_y - 80, 280, 160); ctx.stroke()
            ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(18); ctx.move_to(gw_x - 110, gw_y - 30); ctx.show_text("OPENCLAW GATEWAY")
            ctx.set_font_size(14); ctx.set_source_rgb(0.2, 0.9, 1.0)
            ctx.move_to(gw_x - 90, gw_y + 10); ctx.show_text("PORT: 127.0.0.1:18789")
            ctx.move_to(gw_x - 85, gw_y + 40); ctx.show_text("SQLite State Store")

            # Surrounding Channels
            channels = [("WhatsApp", -380, -90), ("Telegram", -380, 50), ("Terminal CLI", 160, -90), ("GitHub Node", 160, 50)]
            for ch_name, off_x, off_y in channels:
                ctx.set_source_rgba(0.08, 0.12, 0.16, 0.9); ctx.rectangle(gw_x + off_x, gw_y + off_y, 160, 60); ctx.fill()
                ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_line_width(1.4); ctx.rectangle(gw_x + off_x, gw_y + off_y, 160, 60); ctx.stroke()
                ctx.set_font_size(14); ctx.set_source_rgb(0.9, 0.95, 1.0)
                ctx.move_to(gw_x + off_x + 20, gw_y + off_y + 36); ctx.show_text(ch_name)
                # Bus lines
                ctx.set_source_rgba(0.0, 1.0, 0.4, 0.6); ctx.set_line_width(1.5)
                ctx.move_to(gw_x + off_x + 80, gw_y + off_y + 30); ctx.line_to(gw_x, gw_y); ctx.stroke()

        elif kind == "pairing_wall":
            # Two-tier pairing security wall
            ctx.set_source_rgba(1.0, 0.25, 0.35, 0.9); ctx.set_line_width(3.0)
            ctx.move_to(cx - 200, y + 80); ctx.line_to(cx - 200, y + h - 80); ctx.stroke()
            ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(18); ctx.move_to(x + 60, y + 160); ctx.show_text("UNTRUSTED SENDER (WHATSAPP)")
            ctx.set_font_size(13); ctx.set_source_rgba(1.0, 0.7, 0.7, 0.9)
            ctx.move_to(x + 60, y + 200); ctx.show_text("Incoming prompt injection attempt...")
            ctx.move_to(x + 60, y + 230); ctx.show_text("STATUS: BLOCKED BY GATEWAY")

            ctx.set_source_rgb(0.0, 1.0, 0.4)
            ctx.set_font_size(18); ctx.move_to(cx - 150, y + 160); ctx.show_text("PAIRING AUTHORIZATION GATEWAY")
            ctx.set_font_size(14); ctx.set_source_rgba(0.85, 0.95, 1.0, 0.95)
            ctx.move_to(cx - 150, y + 200); ctx.show_text("openclaw pairing approve <channel> <code>")
            ctx.move_to(cx - 150, y + 230); ctx.show_text("Zero privileges granted without operator key!")

        ctx.restore()

    ctx.restore()


# ------------------------------------------------------------------------------
# MASTER CHAPTER FRAME RENDERER
# ------------------------------------------------------------------------------

def render_openclaw_chapter_frame(ctx, ch_num, t, active_sub):
    """Renders one 1080p frame for chapter ch_num with complete High-Contrast Inversion."""
    cues = CHAPTER_CUES[ch_num]
    beats_list = cadence.OPENCLAW_BEATS[ch_num]

    # Find active cue
    active_idx = 0
    for idx, (s, e, txt) in enumerate(cues):
        if s <= t <= e:
            active_idx = idx
            break
        elif t > e:
            active_idx = idx

    active_idx = min(active_idx, len(beats_list) - 1)
    beat_spec = beats_list[active_idx]

    bg_type = beat_spec.get("bg", "cream")
    action = beat_spec.get("action", "walking")
    mood = beat_spec.get("mood", "confident")
    pos = beat_spec.get("pos", (960, 720))
    zoom = beat_spec.get("zoom", 1.0)

    # 1. Background (Non-White Warm Tone with Parallax Drift)
    ctx.save()
    top_c, bot_c = BG_PALETTES.get(bg_type, BG_PALETTES["cream"])
    pat = cairo.LinearGradient(0, 0, WIDTH, HEIGHT)
    pat.add_color_stop_rgb(0.0, *top_c)
    pat.add_color_stop_rgb(1.0, *bot_c)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    ctx.fill()
    # Subtle architectural grid
    ctx.set_source_rgba(0.25, 0.30, 0.35, 0.05)
    ctx.set_line_width(1.0)
    for gx in range(0, WIDTH, 40):
        ctx.move_to(gx, 0); ctx.line_to(gx, HEIGHT); ctx.stroke()
    for gy in range(0, HEIGHT, 40):
        ctx.move_to(0, gy); ctx.line_to(WIDTH, gy); ctx.stroke()
    ctx.restore()

    # 2. Virtual Camera Punch-In
    ctx.save()
    if zoom > 1.0:
        apply_virtual_camera(ctx, pos[0], pos[1] - 80, zoom=zoom, roll=0.0)

    # 3. Content Card Frame
    draw_openclaw_beat_card(ctx, ch_num, t, active_idx, beat_spec, x=180, y=105, w=1560, h=610)

    # 4. Sticky Character (Mr. Flow) with permanent FLOWORKOS.COM chest branding
    sc = 1.35
    if action == "camera_zoom":
        # Extreme close up
        eng.draw_stylized_stickman(ctx, pos[0], pos[1] + 120, scale=2.4, mood=mood, t=t, action="explaining")
        ctx.save()
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.9); ctx.set_line_width(2.0)
        ctx.rectangle(pos[0] - 220, pos[1] - 120, 440, 280); ctx.stroke()
        ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(14); ctx.move_to(pos[0] - 200, pos[1] - 90); ctx.show_text("[CAMERA PUNCH-IN: 2.5x]")
        ctx.restore()
    elif action == "hanging":
        # Hanging from top of the dark card
        eng.draw_hanging_stickman(ctx, pos[0], 105, scale=sc, t=t)
    elif action == "walking":
        eng.draw_walking_stickman(ctx, pos[0], pos[1], scale=sc, t=t)
    else:
        eng.draw_stylized_stickman(ctx, pos[0], pos[1], scale=sc, mood=mood, t=t, action=action)

    ctx.restore() # Restore camera zoom

    # 5. Header Telemetry & Subtitles
    draw_openclaw_header_bar(ctx, t)
    eng.draw_subtitles(ctx, active_sub)


# ------------------------------------------------------------------------------
# CONTACT SHEET & THUMBNAIL BUILDER
# ------------------------------------------------------------------------------

def generate_openclaw_contact_sheet(master_mp4, out_cs_path):
    """Generates 12-frame empirical contact sheet proving visual diversity."""
    print(f"\n[*] Generating 12-Frame Empirical Contact Sheet from {master_mp4}...")
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", master_mp4
    ]
    dur = float(subprocess.check_output(probe_cmd).decode().strip())

    COLS, ROWS = 4, 3
    PW, PH = 640, 360
    SHEET_W = COLS * PW
    SHEET_H = ROWS * PH

    sheet_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SHEET_W, SHEET_H)
    sheet_ctx = cairo.Context(sheet_surf)

    # Architectural cream background
    sheet_ctx.set_source_rgb(0.94, 0.91, 0.86)
    sheet_ctx.rectangle(0, 0, SHEET_W, SHEET_H); sheet_ctx.fill()

    timestamps = [
        (dur * 0.05, "01. CLOUD SUBSCRIPTION TRAP"),
        (dur * 0.12, "02. CONCRETE WALL (CONFUSED)"),
        (dur * 0.20, "03. DATA EXFILTRATION (SHOCKED)"),
        (dur * 0.28, "04. THE LOBSTER RISES (BOUNCING)"),
        (dur * 0.36, "05. 395K STARS CELEBRATION"),
        (dur * 0.44, "06. GATEWAY PORT 18789 (THINKING)"),
        (dur * 0.49, "07. EMBEDDED SQLITE (HEAVY LIFT)"),
        (dur * 0.58, "08. WHATSAPP OMNI-NERVE (HANGING)"),
        (dur * 0.68, "09. CODING ON LAPTOP (SEATED)"),
        (dur * 0.78, "10. MOBILE TO GIT TURBO SPRINT"),
        (dur * 0.88, "11. PAIRING ZERO-TRUST (PEEKING)"),
        (dur * 0.96, "12. SOVEREIGN FINALE (VICTORY)"),
    ]

    for idx, (sec, label) in enumerate(timestamps):
        c = idx % COLS
        r = idx // COLS
        px = c * PW
        py = r * PH
        tmp_img = f"/tmp/openclaw_cs_frame_{idx}.png"
        cmd = ["ffmpeg", "-y", "-ss", str(sec), "-i", master_mp4, "-frames:v", "1", "-q:v", "2", tmp_img]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        if os.path.exists(tmp_img):
            frame_surf = cairo.ImageSurface.create_from_png(tmp_img)
            sheet_ctx.save()
            sheet_ctx.translate(px, py)
            sheet_ctx.scale(PW / 1920.0, PH / 1080.0)
            sheet_ctx.set_source_surface(frame_surf, 0, 0)
            sheet_ctx.paint()
            sheet_ctx.restore()
            os.remove(tmp_img)

        # Label pill
        sheet_ctx.save()
        sheet_ctx.set_source_rgba(0.04, 0.07, 0.10, 0.94)
        sheet_ctx.rectangle(px + 10, py + 10, 360, 30); sheet_ctx.fill()
        sheet_ctx.set_source_rgb(0.0, 1.0, 0.4); sheet_ctx.set_line_width(1.2)
        sheet_ctx.rectangle(px + 10, py + 10, 360, 30); sheet_ctx.stroke()
        sheet_ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        sheet_ctx.set_font_size(12); sheet_ctx.move_to(px + 18, py + 30); sheet_ctx.show_text(label)
        sheet_ctx.restore()

    # Borders
    sheet_ctx.set_source_rgba(0.0, 1.0, 0.4, 0.5)
    sheet_ctx.set_line_width(1.5)
    for c in range(1, COLS):
        sheet_ctx.move_to(c * PW, 0); sheet_ctx.line_to(c * PW, SHEET_H); sheet_ctx.stroke()
    for r in range(1, ROWS):
        sheet_ctx.move_to(0, r * PH); sheet_ctx.line_to(SHEET_W, r * PH); sheet_ctx.stroke()

    sheet_surf.write_to_png(out_cs_path)
    print(f"[✓] Contact sheet rendered: {out_cs_path}")


def generate_openclaw_thumbnail(out_thumb_path):
    """Renders high-CTR YouTube thumbnail for OpenClaw."""
    print(f"[*] Generating High-CTR Thumbnail: {out_thumb_path}...")
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1920, 1080)
    ctx = cairo.Context(surf)

    # Warm architectural cream background
    cadence.cairo = cairo
    ctx.save()
    pat = cairo.LinearGradient(0, 0, 1920, 1080)
    pat.add_color_stop_rgb(0.0, 0.96, 0.93, 0.89)
    pat.add_color_stop_rgb(1.0, 0.90, 0.87, 0.82)
    ctx.set_source(pat); ctx.rectangle(0, 0, 1920, 1080); ctx.fill()
    ctx.restore()

    # Dark Card Frame
    eng.draw_dark_card(ctx, 80, 80, 1760, 920, "🦞 OPENCLAW // LOCAL AI REVOLUTION")

    # Giant Headline
    ctx.save()
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(78); ctx.set_source_rgb(1.0, 0.4, 0.2)
    ctx.move_to(140, 240); ctx.show_text("395,000 DEVS ESCAPED")

    ctx.set_font_size(72); ctx.set_source_rgb(0.0, 1.0, 0.4)
    ctx.move_to(140, 340); ctx.show_text("THE CLOUD AI TRAP.")

    ctx.set_font_size(32); ctx.set_source_rgba(0.9, 0.95, 1.0, 0.95)
    ctx.move_to(145, 430); ctx.show_text("Local Gateway Port 18789 • 20+ Channels • 100% Free")

    # High CTR Badge
    ctx.set_source_rgba(0.08, 0.16, 0.22, 0.95)
    ctx.rectangle(140, 480, 520, 85); ctx.fill()
    ctx.set_source_rgb(0.0, 1.0, 0.5); ctx.set_line_width(2.5)
    ctx.rectangle(140, 480, 520, 85); ctx.stroke()
    ctx.set_font_size(34); ctx.set_source_rgb(0.0, 1.0, 0.5)
    ctx.move_to(170, 538); ctx.show_text("NO SUBSCRIPTION // MIT")
    ctx.restore()

    # Sticky doing dynamic pose (Hover / Jetpack or Salto)
    eng.draw_stylized_stickman(ctx, 1480, 680, scale=2.3, mood="celebrating", t=1.0, action="celebrating")

    surf.write_to_png(out_thumb_path)
    print(f"[✓] High-CTR Thumbnail Created: {out_thumb_path}")


# ------------------------------------------------------------------------------
# MASTER PRODUCTION PIPELINE
# ------------------------------------------------------------------------------

def main():
    os.makedirs(PIPELINE_DIR, exist_ok=True)
    os.makedirs(THEME_VAULT, exist_ok=True)
    os.makedirs(USER_VAULT, exist_ok=True)

    print("========================================================")
    print("🎬 MASTER OPENCLAW DOCUMENTARY PIPELINE (NVENC 1080P)")
    print("    THEME: openclaw/openclaw (395K STARS)")
    print("    CONTRAST: HIGH-CONTRAST INVERSION (DARK MATTE + NON-WHITE BG)")
    print("    BRAND: MANDATORY MATRIX GREEN FLOWORKOS.COM CHEST BADGE")
    print("========================================================")

    chapter_videos = []
    for ch_num in range(1, 7):
        audio_file = os.path.join(PIPELINE_DIR, f"ch{ch_num}_audio.wav")
        srt_file = os.path.join(PIPELINE_DIR, f"ch{ch_num}_voice.srt")
        out_video = os.path.join(PIPELINE_DIR, f"ch{ch_num}_video_1080p.mp4")

        title = f"Chapter {ch_num}"
        def make_renderer(c_num):
            return lambda ctx, t, sub: render_openclaw_chapter_frame(ctx, c_num, t, sub)

        eng.render_chapter_pipeline(ch_num, title, audio_file, srt_file, out_video, make_renderer(ch_num))
        chapter_videos.append(out_video)

    # Master Concatenation
    concat_txt = os.path.join(PIPELINE_DIR, "concat_manifest.txt")
    with open(concat_txt, "w") as f:
        for cv in chapter_videos:
            f.write(f"file '{cv}'\n")

    master_mp4 = os.path.join(PIPELINE_DIR, "OPENCLAW_STICKMAN_DOCUMENTARY_1080P.mp4")
    print(f"\n[*] Concatenating 6 chapters into Master MP4: {master_mp4}...")
    concat_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", master_mp4]
    subprocess.run(concat_cmd, check=True)

    # Generate Thumbnail & Contact Sheet
    thumb_path = os.path.join(PIPELINE_DIR, "OPENCLAW_STICKMAN_DOCUMENTARY_1080P_thumbnail.png")
    generate_openclaw_thumbnail(thumb_path)

    cs_path = os.path.join(PIPELINE_DIR, "OPENCLAW_STICKMAN_DOCUMENTARY_1080P_contact_sheet.png")
    generate_openclaw_contact_sheet(master_mp4, cs_path)

    # Combine SRT Subtitles
    master_srt = os.path.join(PIPELINE_DIR, "OPENCLAW_STICKMAN_DOCUMENTARY_1080P.srt")
    print(f"[*] Consolidating Master Subtitle: {master_srt}...")
    time_offset = 0.0
    combined_cues = []
    cue_idx = 1
    for ch_num in range(1, 7):
        s_file = os.path.join(PIPELINE_DIR, f"ch{ch_num}_voice.srt")
        cues = eng.parse_srt(s_file)
        a_file = os.path.join(PIPELINE_DIR, f"ch{ch_num}_audio.wav")
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", a_file]).decode().strip())
        for start, end, text in cues:
            combined_cues.append((start + time_offset, end + time_offset, text))
        time_offset += dur

    with open(master_srt, "w", encoding="utf-8") as f:
        for idx, (start, end, text) in enumerate(combined_cues, 1):
            def fmt_ts(s):
                h = int(s // 3600)
                m = int((s % 3600) // 60)
                sec = int(s % 60)
                ms = int((s - int(s)) * 1000)
                return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
            f.write(f"{idx}\n{fmt_ts(start)} --> {fmt_ts(end)}\n{text}\n\n")

    # Generate YouTube SEO Package
    seo_md = os.path.join(PIPELINE_DIR, "OPENCLAW_DOCUMENTARY_PACKAGE.md")
    with open(seo_md, "w", encoding="utf-8") as f:
        f.write("""# 🦞 OPENCLAW: HOW 395,000 DEVELOPERS ESCAPED THE CLOUD AI TRAP

## 🎬 Video Overview
- **Repository**: [openclaw/openclaw](https://github.com/openclaw/openclaw) (395,000+ Stars)
- **Tagline**: The AI that really does things. Any OS. Any Platform. The lobster way. 🦞
- **Created By**: Peter Steinberger (@steipete) & OpenClaw Foundation
- **Visual Style**: High-Contrast Inversion (Matte Obsidian Stickman + Warm Architectural Light Backgrounds)
- **Branding**: FLOWORKOS.COM Matrix Green Chest Badge
- **Hardware Acceleration**: NVENC H.264 1080p @ 30 FPS

## ⏱️ Video Chapters (Timestamps)
- `00:00` - Chapter 1: The Cloud Subscription Trap ($200/mo Paywalls)
- `00:50` - Chapter 2: The Lobster Rises (Peter Steinberger & Molty)
- `01:36` - Chapter 3: Gateway Port 18789 & Local SQLite Architecture
- `02:24` - Chapter 4: The 20+ Channel Omni-Nerve (WhatsApp to Terminal)
- `03:05` - Chapter 5: Zero-Trust Pairing Security & Sandboxing
- `03:45` - Chapter 6: The Sovereign AI Era (The Lobster Revolution)

## 🏷️ High-CTR YouTube Tags & Keywords
`openclaw`, `local ai agent`, `peter steinberger`, `molty lobster`, `claude code alternative`, `self hosted ai`, `open source agent`, `autonomous coding`, `whatsapp ai bot`, `telegram ai bot`, `floworkos`, `stickman animation`, `developer documentary`
""")

    # Mirror to Theme Vault & User Vault
    print(f"\n[*] Syncing all deliverables to Theme Vault and User Vault...")
    deliverables = [
        ("OPENCLAW_STICKMAN_DOCUMENTARY_1080P.mp4", master_mp4),
        ("OPENCLAW_STICKMAN_DOCUMENTARY_1080P_thumbnail.png", thumb_path),
        ("OPENCLAW_STICKMAN_DOCUMENTARY_1080P_contact_sheet.png", cs_path),
        ("OPENCLAW_STICKMAN_DOCUMENTARY_1080P.srt", master_srt),
        ("OPENCLAW_DOCUMENTARY_PACKAGE.md", seo_md)
    ]
    for fname, src in deliverables:
        dst_theme = os.path.join(THEME_VAULT, fname)
        dst_user = os.path.join(USER_VAULT, fname)
        subprocess.run(["cp", src, dst_theme], check=True)
        subprocess.run(["cp", src, dst_user], check=True)
        print(f"  ✓ Delivered: {fname}")

    print(f"\n[✓] ALL DELIVERABLES PERSISTED IN THEME VAULT:")
    print(f"    • {THEME_VAULT}")
    print(f"    • {USER_VAULT}")


if __name__ == "__main__":
    main()
