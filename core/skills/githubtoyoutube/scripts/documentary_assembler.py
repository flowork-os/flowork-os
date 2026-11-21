#!/usr/bin/env python3
"""
🎬 MASTER DOCUMENTARY ASSEMBLER FOR GITHUBTOYOUTUBE SKILL
Executes the full longform documentary production cycle:
1. High-Contrast Inversion: Non-white bright backgrounds (warm kraft, cream, sage mint, loft amber, slate).
2. Foreground Dark Elements: Dark frosted cards + Dark matte stickman.
3. Permanent Chest Branding: High-luminance Matrix Green (#00ff66) 'FLOWORKOS.COM'.
4. Comedic Kinematics: Hanging from card top edge, walking across frame, dynamic zoom punch.
5. NVENC 1080p hardware rendering & Dedicated Theme-Folder delivery.
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
import sentence_cadence_director as beats

WIDTH = 1920
HEIGHT = 1080

def get_pipeline_dir():
    return "/opt/floworkos/pipelines/stickman_billion_context_documentary"

PIPELINE_DIR = get_pipeline_dir()
BG_DIR = os.path.join(PIPELINE_DIR, "assets", "backgrounds")

SURF_HEADER = cairo.ImageSurface.create_from_png(os.path.join(PIPELINE_DIR, "assets", "github_repo_header.png"))
SURF_README = cairo.ImageSurface.create_from_png(os.path.join(PIPELINE_DIR, "assets", "github_repo_readme.png"))

# Preload all 6 chapter sentence cues (111 beats total)
CHAPTER_CUES = {
    ch: eng.parse_srt(os.path.join(PIPELINE_DIR, f"ch{ch}_voice.srt"))
    for ch in range(1, 7)
}

# 5 Non-White Bright Backgrounds (Avoiding sterile pure white)
BACKGROUND_DEFAULTS = {
    1: os.path.join(BG_DIR, "warm_kraft_paper.png"),
    2: os.path.join(BG_DIR, "architectural_cream.png"),
    3: os.path.join(BG_DIR, "sage_mint_studio.png"),
    4: os.path.join(BG_DIR, "loft_daylight_amber.png"),
    5: os.path.join(BG_DIR, "warm_slate_concrete.png"),
    6: os.path.join(BG_DIR, "architectural_cream.png"),
}

LOADED_SURFACES = {}
GLOBAL_BG_SURF = None

def get_chapter_bg(ch_num):
    global GLOBAL_BG_SURF
    if GLOBAL_BG_SURF is not None:
        return GLOBAL_BG_SURF
    if ch_num in LOADED_SURFACES:
        return LOADED_SURFACES[ch_num]
    bg_file = BACKGROUND_DEFAULTS.get(ch_num)
    if bg_file and os.path.exists(bg_file):
        surf = cairo.ImageSurface.create_from_png(bg_file)
        LOADED_SURFACES[ch_num] = surf
        return surf
    return None

# ==============================================================================
# SPECIALIZED CHAPTER FRAME RENDERERS (AUDIO-SYNCHRONIZED SENTENCE BEATS)
# ==============================================================================

def render_ch1_frame(ctx, t, active_sub):
    """Chapter 1: The Dev Office (The Million-Token Illusion)"""
    bg = get_chapter_bg(1)
    eng.draw_modular_background(ctx, t, bg_surface=bg)
    cues = CHAPTER_CUES[1]
    action, mood, pos, scale = beats.draw_sentence_beat_card(ctx, 1, t, cues, x=220, y=95, w=1480, h=590, img_surf=SURF_HEADER)
    eng.draw_stylized_stickman(ctx, pos[0], pos[1], scale=scale, mood=mood, t=t, action=action)
    eng.draw_link_callout_banner(ctx, eng.REPO_URL, t)
    eng.draw_subtitles(ctx, active_sub)

def render_ch2_frame(ctx, t, active_sub):
    """Chapter 2: The Hacker Cafe (The Breakout Discovery)"""
    bg = get_chapter_bg(2)
    eng.draw_modular_background(ctx, t, bg_surface=bg)
    cues = CHAPTER_CUES[2]
    action, mood, pos, scale = beats.draw_sentence_beat_card(ctx, 2, t, cues, x=220, y=95, w=1480, h=590, img_surf=SURF_HEADER)
    eng.draw_stylized_stickman(ctx, pos[0], pos[1], scale=scale, mood=mood, t=t, action=action)
    eng.draw_link_callout_banner(ctx, eng.REPO_URL, t)
    eng.draw_subtitles(ctx, active_sub)

def render_ch3_frame(ctx, t, active_sub):
    """Chapter 3: Sci-Fi Hologram Lab (Reversible Dynamic Folding)"""
    bg = get_chapter_bg(3)
    eng.draw_modular_background(ctx, t, bg_surface=bg)
    cues = CHAPTER_CUES[3]
    action, mood, pos, scale = beats.draw_sentence_beat_card(ctx, 3, t, cues, x=220, y=95, w=1480, h=590, img_surf=SURF_README)
    eng.draw_stylized_stickman(ctx, pos[0], pos[1], scale=scale, mood=mood, t=t, action=action)
    eng.draw_link_callout_banner(ctx, eng.REPO_URL, t)
    eng.draw_subtitles(ctx, active_sub)

def render_ch4_frame(ctx, t, active_sub):
    """Chapter 4: Cloud Datacenter (Prefix-Cache Preservation)"""
    bg = get_chapter_bg(4)
    eng.draw_modular_background(ctx, t, bg_surface=bg)
    cues = CHAPTER_CUES[4]
    action, mood, pos, scale = beats.draw_sentence_beat_card(ctx, 4, t, cues, x=220, y=95, w=1480, h=590, img_surf=SURF_README)
    eng.draw_stylized_stickman(ctx, pos[0], pos[1], scale=scale, mood=mood, t=t, action=action)
    eng.draw_link_callout_banner(ctx, eng.REPO_URL, t)
    eng.draw_subtitles(ctx, active_sub)

def render_ch5_frame(ctx, t, active_sub):
    """Chapter 5: Keynote Auditorium Stage (18.7 Billion Token Benchmark Victory)"""
    bg = get_chapter_bg(5)
    eng.draw_modular_background(ctx, t, bg_surface=bg)
    cues = CHAPTER_CUES[5]
    action, mood, pos, scale = beats.draw_sentence_beat_card(ctx, 5, t, cues, x=220, y=95, w=1480, h=590, img_surf=SURF_HEADER)
    # Floating celebratory confetti
    ctx.save()
    for cp in range(25):
        c_x = (cp * 67 + t * 90) % WIDTH
        c_y = (cp * 89 + t * 140) % 730
        c_ang = t * 4.0 + cp
        ctx.set_source_rgba(0.2 + 0.3 * math.sin(cp), 0.8, 0.4, 0.85)
        ctx.save()
        ctx.translate(c_x, c_y)
        ctx.rotate(c_ang)
        ctx.rectangle(-4, -2, 8, 4)
        ctx.fill()
        ctx.restore()
    ctx.restore()
    eng.draw_stylized_stickman(ctx, pos[0], pos[1], scale=scale, mood=mood, t=t, action=action)
    eng.draw_link_callout_banner(ctx, eng.REPO_URL, t)
    eng.draw_subtitles(ctx, active_sub)

def render_ch6_frame(ctx, t, active_sub):
    """Chapter 6: Sovereign Verdict & Master Finale"""
    bg = get_chapter_bg(6)
    eng.draw_modular_background(ctx, t, bg_surface=bg)
    cues = CHAPTER_CUES[6]
    action, mood, pos, scale = beats.draw_sentence_beat_card(ctx, 6, t, cues, x=220, y=95, w=1480, h=590, img_surf=SURF_HEADER)
    eng.draw_stylized_stickman(ctx, pos[0], pos[1], scale=scale, mood=mood, t=t, action=action)
    if t > 50.0:
        ctx.save()
        cx, cy = 960, 840
        ctx.set_source_rgba(0.04, 0.08, 0.14, 0.95)
        ctx.rectangle(cx - 260, cy - 25, 520, 50); ctx.fill()
        ctx.set_source_rgba(0.0, 1.0, 0.4, 0.9); ctx.set_line_width(2.0)
        ctx.rectangle(cx - 260, cy - 25, 520, 50); ctx.stroke()
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(18); ctx.set_source_rgb(0.0, 1.0, 0.4)
        ctx.move_to(cx - 220, cy + 8); ctx.show_text("🔔 SUBSCRIBE FOR MORE REPO DEEP DIVES")
        ctx.restore()
    eng.draw_link_callout_banner(ctx, eng.REPO_URL, t)
    eng.draw_subtitles(ctx, active_sub)


# ==============================================================================
# EMPIRICAL CONTACT SHEET GENERATOR (12 CINEMATIC FRAMES)
# ==============================================================================

def generate_empirical_contact_sheet(master_mp4, out_cs_path):
    print(f"[*] Generating Empirical 12-Frame Contact Sheet from {master_mp4}...")
    sample_timestamps = [
        ("00:00:20", "Ch 1: Closeup (FLOWORKOS.COM)"),
        ("00:00:35", "Ch 1: $1,450 API Shock"),
        ("00:00:48", "Ch 1: Hanging on Card (Humor)"),
        ("00:01:05", "Ch 1: Full-Bleed O(N²) Curve"),
        ("00:02:40", "Ch 2: Warm Cream Loft Discovery"),
        ("00:03:20", "Ch 2: Fullscreen Code Window"),
        ("00:04:45", "Ch 3: Sage Mint AST Folding"),
        ("00:06:10", "Ch 3: Closeup Reversible Folding"),
        ("00:07:30", "Ch 4: Loft Amber Datacenter"),
        ("00:08:45", "Ch 4: Fullscreen Cache Invariant"),
        ("00:10:05", "Ch 5: 18.7B Benchmark + Confetti"),
        ("00:12:45", "Ch 6: Final CTA + Subscribe Banner"),
    ]

    tmp_dir = os.path.join(PIPELINE_DIR, "assets", "cs_samples")
    os.makedirs(tmp_dir, exist_ok=True)

    extracted_images = []
    for idx, (ts, desc) in enumerate(sample_timestamps):
        tmp_img = os.path.join(tmp_dir, f"frame_{idx:02d}.png")
        cmd = [
            "ffmpeg", "-y", "-ss", ts, "-i", master_mp4,
            "-vframes", "1", "-q:v", "2", tmp_img
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(tmp_img):
            extracted_images.append((tmp_img, desc))

    if not extracted_images:
        print("[!] No sample frames extracted for contact sheet.")
        return

    COLS, ROWS = 4, 3
    PW, PH = 480, 270
    SHEET_W, SHEET_H = 1920, 810
    sheet_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SHEET_W, SHEET_H)
    sheet_ctx = cairo.Context(sheet_surf)

    # Warm light background for sheet border
    sheet_ctx.set_source_rgb(0.92, 0.90, 0.86)
    sheet_ctx.rectangle(0, 0, SHEET_W, SHEET_H)
    sheet_ctx.fill()

    for idx, (img_path, desc) in enumerate(extracted_images):
        c = idx % COLS
        r = idx // COLS
        px = c * PW
        py = r * PH
        surf = cairo.ImageSurface.create_from_png(img_path)
        sheet_ctx.save()
        sheet_ctx.translate(px, py)
        sheet_ctx.scale(PW / 1920.0, PH / 1080.0)
        sheet_ctx.set_source_surface(surf, 0, 0)
        sheet_ctx.paint()
        sheet_ctx.restore()

        # Label tag
        sheet_ctx.save()
        sheet_ctx.set_source_rgba(0.04, 0.07, 0.10, 0.92)
        sheet_ctx.rectangle(px + 8, py + 8, 330, 26)
        sheet_ctx.fill()
        sheet_ctx.set_source_rgb(0.0, 1.0, 0.4)
        sheet_ctx.set_line_width(1.2)
        sheet_ctx.rectangle(px + 8, py + 8, 330, 26)
        sheet_ctx.stroke()
        sheet_ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        sheet_ctx.set_font_size(11)
        sheet_ctx.move_to(px + 14, py + 25)
        sheet_ctx.show_text(desc)
        sheet_ctx.restore()

    # Borders
    sheet_ctx.set_source_rgba(0.0, 1.0, 0.4, 0.5)
    sheet_ctx.set_line_width(1.5)
    for c in range(1, COLS):
        sheet_ctx.move_to(c * PW, 0); sheet_ctx.line_to(c * PW, SHEET_H); sheet_ctx.stroke()
    for r in range(1, ROWS):
        sheet_ctx.move_to(0, r * PH); sheet_ctx.line_to(SHEET_W, r * PH); sheet_ctx.stroke()

    sheet_surf.write_to_png(out_cs_path)
    print(f"[✓] Master Contact Sheet Created: {out_cs_path}")


# ==============================================================================
# MASTER ORCHESTRATOR & THEME SUBFOLDER DELIVERY
# ==============================================================================

CHAPTERS = [
    (1, "The Million-Token Illusion", render_ch1_frame),
    (2, "The Breakout Discovery", render_ch2_frame),
    (3, "Reversible Dynamic Folding", render_ch3_frame),
    (4, "Cache Preservation Architecture", render_ch4_frame),
    (5, "18.7 Billion Token Benchmark", render_ch5_frame),
    (6, "The Sovereign Verdict", render_ch6_frame),
]

def main():
    parser = argparse.ArgumentParser(description="Master Stickman Longform Documentary Pipeline")
    parser.add_argument("--bg", type=str, default=None, help="Global background override image for anti-duplicate syndication")
    parser.add_argument("--force", action="store_true", default=True, help="Force re-rendering of all chapters")
    parser.add_argument("--chapter", type=int, default=None, help="Render specific chapter (1-6)")
    args = parser.parse_args()

    global GLOBAL_BG_SURF
    if args.bg and os.path.exists(args.bg):
        print(f"[+] Global background override loaded for anti-duplicate syndication: {args.bg}")
        GLOBAL_BG_SURF = cairo.ImageSurface.create_from_png(args.bg)

    print(f"========================================================")
    print(f"🎬 MASTER DOCUMENTARY PRODUCTION PIPELINE (NVENC 1080P)")
    print(f"    HIGH-CONTRAST INVERSION: NON-WHITE BRIGHT BACKGROUNDS")
    print(f"    DARK MATTE STICKMAN + COMEDIC KINEMATICS (HANGING/WALK)")
    print(f"    MANDATORY BRAND: FLOWORKOS.COM (MATRIX GREEN #00ff66)")
    print(f"========================================================")

    rendered_files = []
    chapters_to_render = [c for c in CHAPTERS if args.chapter is None or c[0] == args.chapter]

    for num, title, frame_func in chapters_to_render:
        audio_file = os.path.join(PIPELINE_DIR, f"ch{num}_audio.wav")
        srt_file = os.path.join(PIPELINE_DIR, f"ch{num}_voice.srt")
        out_video = os.path.join(PIPELINE_DIR, f"ch{num}_video_1080p.mp4")

        if args.force and os.path.exists(out_video):
            os.remove(out_video)

        eng.render_chapter_pipeline(num, title, audio_file, srt_file, out_video, frame_func)
        rendered_files.append(out_video)

    all_ch_videos = [os.path.join(PIPELINE_DIR, f"ch{num}_video_1080p.mp4") for num in range(1, 7)]
    if not all(os.path.exists(f) for f in all_ch_videos):
        print("[!] Not all 6 chapters rendered yet. Skipping master concat.")
        return

    # Concat Manifest
    concat_txt = os.path.join(PIPELINE_DIR, "concat_manifest.txt")
    with open(concat_txt, "w") as f:
        for vf in all_ch_videos:
            f.write(f"file '{vf}'\n")

    master_mp4 = os.path.join(PIPELINE_DIR, "STICKMAN_BILLION_CONTEXT_LONGFORM_1080P.mp4")
    print(f"\n[*] Concatenating 6 chapters into Master MP4...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_txt,
        "-c", "copy",
        master_mp4
    ]
    subprocess.run(concat_cmd, check=True)
    print(f"[✓] MASTER DOCUMENTARY READY: {master_mp4}")

    # Extract High-CTR Thumbnail
    thumb_path = os.path.join(PIPELINE_DIR, "STICKMAN_BILLION_CONTEXT_LONGFORM_1080P_thumbnail.png")
    thumb_cmd = [
        "ffmpeg", "-y",
        "-ss", "00:09:45",
        "-i", master_mp4,
        "-vframes", "1",
        "-q:v", "2",
        thumb_path
    ]
    subprocess.run(thumb_cmd, check=True)
    print(f"[✓] Thumbnail Extracted: {thumb_path}")

    # Render Empirical 12-Frame Master Contact Sheet
    contact_sheet_path = os.path.join(PIPELINE_DIR, "STICKMAN_BILLION_CONTEXT_LONGFORM_1080P_contact_sheet.png")
    generate_empirical_contact_sheet(master_mp4, contact_sheet_path)

    # Mandatory Theme Subfolder Isolation
    theme_vault_dir = "/opt/floworkos/documents/videos/billion-context-documentary"
    user_vault_dir = os.path.expanduser("~/Documents/videos/billion-context-documentary")
    os.makedirs(theme_vault_dir, exist_ok=True)
    os.makedirs(user_vault_dir, exist_ok=True)

    deliverables = [
        (master_mp4, "STICKMAN_BILLION_CONTEXT_LONGFORM_1080P.mp4"),
        (thumb_path, "STICKMAN_BILLION_CONTEXT_LONGFORM_1080P_thumbnail.png"),
        (contact_sheet_path, "STICKMAN_BILLION_CONTEXT_LONGFORM_1080P_contact_sheet.png"),
        (os.path.join(PIPELINE_DIR, "STICKMAN_BILLION_CONTEXT_LONGFORM_1080P.srt"), "STICKMAN_BILLION_CONTEXT_LONGFORM_1080P.srt"),
        (os.path.join(PIPELINE_DIR, "YOUTUBE_DOCUMENTARY_PACKAGE.md"), "STICKMAN_BILLION_CONTEXT_LONGFORM_1080P_SEO.md"),
        (os.path.join(PIPELINE_DIR, "master_script.txt"), "master_script.txt")
    ]

    for src, dst_name in deliverables:
        if os.path.exists(src):
            subprocess.run(["cp", src, os.path.join(theme_vault_dir, dst_name)], check=True)
            subprocess.run(["cp", src, os.path.join(user_vault_dir, dst_name)], check=True)

    print(f"\n[✓] ALL DELIVERABLES SYNCED TO DEDICATED THEME VAULT:")
    print(f"    • {theme_vault_dir}")
    print(f"    • {user_vault_dir}")

if __name__ == "__main__":
    main()
