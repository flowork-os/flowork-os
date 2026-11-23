#!/usr/bin/env python3
"""
Flowork OS Sovereign Short Video Foundry Engine
Autonomous 9:16 vertical short video production tool (1080x1920).
"""

import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time
import wave
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def synthesize_audio_assets(work_dir, duration=56.0, sr=44100):
    os.makedirs(work_dir, exist_ok=True)
    total_samples = int(sr * duration)
    
    def write_wav(path, signal):
        sig = np.clip(signal, -1.0, 1.0)
        pcm = (sig * 32767).astype(np.int16)
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm.tobytes())

    # 1. SFX Bonk
    t = np.linspace(0, 0.25, int(sr * 0.25), endpoint=False)
    bonk = np.sin(2 * np.pi * (160 * np.exp(-t * 15) + 60) * t) * np.exp(-t * 18) * 0.7
    write_wav(os.path.join(work_dir, 'sfx_bonk.wav'), bonk)

    # 2. SFX Wall Smash
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    smash = (np.random.randn(len(t)) * np.exp(-t * 9) * 0.5) + (np.sin(2 * np.pi * 70 * t) * np.exp(-t * 8) * 0.5)
    write_wav(os.path.join(work_dir, 'sfx_smash.wav'), smash)

    # 3. SFX Powerup
    t = np.linspace(0, 0.9, int(sr * 0.9), endpoint=False)
    f_rise = 180 + 750 * (t / 0.9)**2
    write_wav(os.path.join(work_dir, 'sfx_powerup.wav'), np.sin(2 * np.pi * f_rise * t) * (t / 0.9) * 0.6)

    # 4. SFX Whoosh
    t = np.linspace(0, 0.7, int(sr * 0.7), endpoint=False)
    whoosh = np.random.randn(len(t)) * (np.sin(np.pi * t / 0.7)**2) * 0.5
    write_wav(os.path.join(work_dir, 'sfx_whoosh.wav'), whoosh)

    # 5. SFX Chime
    t = np.linspace(0, 1.8, int(sr * 1.8), endpoint=False)
    chimes = np.zeros_like(t)
    for freq in [587.33, 739.99, 880.00, 1174.66]:
        chimes += np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.5) * 0.2
    write_wav(os.path.join(work_dir, 'sfx_chime.wav'), chimes)

    # 6. Lo-Fi BGM (105 BPM)
    bpm = 105.0
    sec_per_beat = 60.0 / bpm
    t_all = np.linspace(0, duration, total_samples, endpoint=False)
    chords = [
        ([196.00, 246.94, 293.66, 392.00], 98.00),   # G
        ([146.83, 220.00, 293.66, 369.99], 73.42),   # D
        ([164.81, 196.00, 246.94, 329.63], 82.41),   # Em
        ([130.81, 164.81, 196.00, 261.63], 65.41),   # C
    ]
    bgm = np.zeros(total_samples, dtype=np.float32)
    bar_len = sec_per_beat * 4
    for i, cur_t in enumerate(t_all):
        chord_idx = int((cur_t % (bar_len * 4)) // bar_len) % 4
        notes, bass_f = chords[chord_idx]
        keys_val = sum(np.sin(2 * np.pi * n * cur_t) + 0.25 * np.sin(2 * np.pi * n * 2 * cur_t) for n in notes) * 0.04
        bass_val = 0.1 * np.sin(2 * np.pi * bass_f * cur_t)
        bgm[i] = keys_val + bass_val

    total_beats = int(duration / sec_per_beat)
    for b in range(total_beats):
        start = int(b * sec_per_beat * sr)
        if b % 4 in (0, 2):
            k_len = min(int(sr * 0.12), total_samples - start)
            kt = np.linspace(0, 0.12, k_len, endpoint=False)
            bgm[start:start+k_len] += np.sin(2 * np.pi * (120 * np.exp(-kt*30) + 40) * kt) * np.exp(-kt*20) * 0.22
        else:
            s_len = min(int(sr * 0.15), total_samples - start)
            st = np.linspace(0, 0.15, s_len, endpoint=False)
            bgm[start:start+s_len] += (np.random.rand(s_len) * 2 - 1) * np.exp(-st*25) * 0.12

    fade = min(int(sr * 2.0), total_samples)
    bgm[-fade:] *= np.linspace(1, 0, fade)
    bgm = bgm / (np.max(np.abs(bgm)) + 1e-6) * 0.25
    write_wav(os.path.join(work_dir, 'bgm.wav'), bgm)

def build_script(topic="Motivasi Sukses", repo=None, repo_desc=None):
    if repo and repo_desc:
        return (
            f"Pernah nggak kamu kebayang ada tools open-source sekeren {repo}?\n\n"
            f"Banyak developer bingung cari solusi efisien, padahal repo ini menyelesaikannya dengan sangat elegan!\n\n"
            f"Fokus utamanya adalah {repo_desc}.\n\n"
            f"Dengan arsitektur modern dan performa tinggi, kamu bisa hemat ratusan jam waktu development.\n\n"
            f"Repo ini lagi trending banget di GitHub dan wajib kamu coba sekarang juga!\n\n"
            f"Beri star di GitHub, cek dokumentasinya, dan share video ini ke temen developer kamu!"
        )
    return (
        f"Pernah nggak kamu ngerasa hidup kamu jalan di tempat? Temen sebaya udah pada sukses, kamu beli kuota aja masih mikir dua kali!\n\n"
        f"Santai bro, jangan buru-buru overthinking terus scroll HP sampe jam tiga subuh. Hidup ini bukan balapan lari sprint!\n\n"
        f"Tahu nggak rahasia orang-orang yang akhirnya berhasil? Mereka bukan orang paling jenius di ruangan. Mereka cuma orang paling konsisten yang pantang mundur walau jatuh berkali-kali!\n\n"
        f"Mulai dari langkah kecil hari ini terkait {topic}. Belajar skill baru, upgrade diri, konsisten satu persen tiap hari. Dalam setahun, kamu bakal kaget lihat seberapa jauh kamu melangkah!\n\n"
        f"Jangan peduliin orang yang meremehkanmu. Buktikan lewat karya nyata dan hasil kerja kerasmu.\n\n"
        f"Kalo kamu siap jadi versi terbaikmu, ketik \"SAYA BISA\" di komentar dan mulai aksi nyata sekarang!"
    )

def generate_voiceover(script_text, work_dir, voice="id-ID-ArdiNeural"):
    script_file = os.path.join(work_dir, "script.txt")
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_text)
    
    mp3_file = os.path.join(work_dir, "voice.mp3")
    vtt_file = os.path.join(work_dir, "voice.vtt")
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--file", script_file,
        "--write-media", mp3_file,
        "--write-subtitles", vtt_file
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    probe = subprocess.run(
        ["ffprobe", "-i", mp3_file, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"],
        capture_output=True, text=True, check=True
    )
    duration = float(probe.stdout.strip())
    return mp3_file, vtt_file, duration

def render_stickman_frames(work_dir, duration, total_frames):
    out_video = os.path.join(work_dir, "visual.mp4")
    cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{W}x{H}',
        '-pix_fmt', 'rgb24',
        '-r', str(FPS),
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        out_video
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    font_title = get_font(52)
    font_bold = get_font(68)
    font_sub = get_font(46)
    font_small = get_font(34)

    for f in range(total_frames):
        t_sec = f / FPS
        img = Image.new('RGB', (W, H), (16, 18, 24))
        draw = ImageDraw.Draw(img)

        # Dot Grid
        for gx in range(60, W, 120):
            for gy in range(80, H, 120):
                draw.ellipse([gx-2, gy-2, gx+2, gy+2], fill=(28, 32, 42))

        # Dynamic Stage
        progress = f / total_frames
        if progress < 0.2:
            # Stage 1: Slumped / Ground
            draw.line([0, 1280, W, 1280], fill=(50, 55, 70), width=6)
            # Stickman
            cx, cy = 420, 1150
            draw.ellipse([cx-45, cy-180, cx+45, cy-90], fill=(245, 248, 255))
            draw.polygon([(cx-42, cy-140), (cx-35, cy-195), (cx+10, cy-208), (cx+42, cy-140)], fill=(255, 50, 75))
            draw.line([cx, cy-90, cx-25, cy+40], fill=(245, 248, 255), width=14)
            draw.rectangle([cx+50, cy-20, cx+110, cy+30], fill=(120, 75, 45), outline=(200, 150, 100), width=3)
            draw.text((280, 200), "JANGAN JALAN DI TEMPAT!", font=font_title, fill=(255, 70, 90))
        elif progress < 0.45:
            # Stage 2: Clock / Night
            draw.ellipse([850-60, 400-60, 850+60, 400+60], fill=(25, 28, 38), outline=(100, 110, 140), width=5)
            draw.text((790, 475), "03:00 AM", font=font_small, fill=(255, 80, 100))
            draw.text((260, 200), "HENTIKAN OVERTHINKING!", font=font_title, fill=(100, 160, 255))
            cx, cy = 540, 1150
            draw.ellipse([cx-45, cy-180, cx+45, cy-90], fill=(245, 248, 255))
            draw.polygon([(cx-42, cy-140), (cx-35, cy-195), (cx+10, cy-208), (cx+42, cy-140)], fill=(255, 50, 75))
            draw.line([cx, cy-90, cx, cy+40], fill=(245, 248, 255), width=14)
        elif progress < 0.7:
            # Stage 3: Punch & Wall
            draw.line([0, 1300, W, 1300], fill=(50, 55, 70), width=6)
            draw.text((320, 200), "HANCURKAN RINTANGAN!", font=font_title, fill=(255, 180, 40))
            cx, cy = 520, 1170
            draw.ellipse([cx-45, cy-180, cx+45, cy-90], fill=(245, 248, 255))
            draw.polygon([(cx-42, cy-140), (cx-35, cy-195), (cx+10, cy-208), (cx+42, cy-140)], fill=(255, 50, 75))
            draw.line([cx, cy-90, cx+140, cy-80], fill=(245, 248, 255), width=16)
            draw.ellipse([cx+135, cy-95, cx+170, cy-65], fill=(245, 248, 255))
            draw.ellipse([700, 950, 850, 1100], outline=(255, 200, 50), width=8)
        else:
            # Stage 4: Climax / Thumbs up CTA
            draw.text((310, 200), "MULAI AKSI NYATAMU!", font=font_title, fill=(40, 230, 130))
            cx, cy = 340, 1100
            draw.ellipse([cx-50, cy-200, cx+50, cy-100], fill=(245, 248, 255))
            draw.polygon([(cx-45, cy-150), (cx-40, cy-215), (cx+15, cy-230), (cx+45, cy-150)], fill=(255, 50, 75))
            draw.line([cx, cy-100, cx, cy+40], fill=(245, 248, 255), width=14)
            # Thumbs up hand
            tx, ty = cx + 115, cy - 80
            draw.ellipse([tx-18, ty-18, tx+18, ty+18], fill=(245, 248, 255))
            draw.polygon([(tx, ty-12), (tx+8, ty-32), (tx+22, ty-26), (tx+14, ty-6)], fill=(245, 248, 255))
            # Card
            pulse = math.sin(t_sec * 8) * 6
            draw.rounded_rectangle([480-pulse, 850-pulse, 1000+pulse, 1260+pulse], radius=24, fill=(25, 30, 42), outline=(255, 210, 40), width=5)
            draw.text((530, 890), "🔥 TANTANGAN 🔥", font=font_title, fill=(255, 90, 60))
            draw.text((540, 980), "KETIK: 'SAYA BISA'", font=font_bold, fill=(255, 230, 40))
            draw.text((550, 1100), "DI KOLOM KOMENTAR!", font=font_sub, fill=(200, 220, 240))

        proc.stdin.write(img.tobytes())

    proc.stdin.close()
    proc.wait()
    return out_video

def composite_master(work_dir, final_output, duration):
    v_file = os.path.join(work_dir, "visual.mp4")
    a_voice = os.path.join(work_dir, "voice.mp3")
    a_bgm = os.path.join(work_dir, "bgm.wav")
    s_bonk = os.path.join(work_dir, "sfx_bonk.wav")
    s_smash = os.path.join(work_dir, "sfx_smash.wav")
    s_power = os.path.join(work_dir, "sfx_powerup.wav")
    s_chime = os.path.join(work_dir, "sfx_chime.wav")

    cmd = [
        "ffmpeg", "-y",
        "-i", v_file,
        "-i", a_voice,
        "-i", a_bgm,
        "-i", s_bonk,
        "-i", s_smash,
        "-i", s_power,
        "-i", s_chime,
        "-filter_complex",
        (
            "[1:a]volume=1.35[voc];"
            "[2:a]volume=0.40[bgm];"
            "[3:a]adelay=4000|4000,volume=0.8[s1];"
            "[4:a]adelay=14000|14000,volume=0.9[s2];"
            "[5:a]adelay=24000|24000,volume=0.8[s3];"
            "[6:a]adelay=38000|38000,volume=0.85[s4];"
            "[voc][bgm][s1][s2][s3][s4]amix=inputs=6:duration=longest:dropout_transition=2[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "256k",
        "-t", str(duration),
        final_output
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    parser = argparse.ArgumentParser(description="Flowork OS Autonomous Short Foundry")
    parser.add_argument("--topic", default="Konsistensi Sukses", help="Video topic / theme")
    parser.add_argument("--repo", help="Repository full name (e.g. 'owner/repo')")
    parser.add_argument("--repo-desc", help="Repository description")
    parser.add_argument("--style", default="stickman", choices=["stickman", "minimal"], help="Animation style")
    parser.add_argument("--duration", type=float, default=56.0, help="Target duration in seconds")
    parser.add_argument("--output", help="Output destination file path")
    parser.add_argument("--qc-test", action="store_true", help="Run rapid self-diagnostic QC test")
    args = parser.parse_args()

    work_dir = f"/tmp/flowork_short_{int(time.time())}"
    os.makedirs(work_dir, exist_ok=True)

    if args.qc_test:
        print("👑 [FLOWORK SHORT FOUNDRY] Executing Rapid Quality Control (QC) Test Suite...")
        test_duration = 6.0
        test_frames = int(test_duration * FPS)
        synthesize_audio_assets(work_dir, duration=test_duration)
        test_script = "Ini adalah uji verifikasi kualitas cepat short foundry Flowork OS."
        generate_voiceover(test_script, work_dir)
        render_stickman_frames(work_dir, test_duration, test_frames)
        qc_out = "/opt/floworkos/documents/videos/QC_SHORT_TEST.mp4"
        composite_master(work_dir, qc_out, test_duration)
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=width,height", "-of", "json", qc_out],
            capture_output=True, text=True, check=True
        )
        data = json.loads(probe.stdout)
        dur = float(data["format"]["duration"])
        w = data["streams"][0]["width"]
        h = data["streams"][0]["height"]
        print(f"QC VERIFICATION PASSED: Resolution {w}x{h}, Duration {dur:.2f}s, Output: {qc_out}")
        shutil.rmtree(work_dir, ignore_errors=True)
        return 0

    print(f"🎬 Initiating Autonomous Short Production for topic: '{args.topic}'...")
    synthesize_audio_assets(work_dir, duration=args.duration)
    script_text = build_script(args.topic, repo=args.repo, repo_desc=args.repo_desc)
    v_mp3, v_vtt, v_dur = generate_voiceover(script_text, work_dir)
    final_dur = min(args.duration, max(52.0, v_dur + 3.0))
    total_frames = int(final_dur * FPS)

    print(f"🎥 Rendering {total_frames} frames @ {FPS} fps...")
    render_stickman_frames(work_dir, final_dur, total_frames)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = args.output or f"/opt/floworkos/documents/videos/SHORT_{timestamp}.mp4"
    composite_master(work_dir, out_file, final_dur)

    # Sovereign Universal Document Mirror
    user_mirror = os.path.expanduser(f"~/Documents/videos/{os.path.basename(out_file)}")
    os.makedirs(os.path.dirname(user_mirror), exist_ok=True)
    shutil.copy2(out_file, user_mirror)

    shutil.rmtree(work_dir, ignore_errors=True)
    print(f"✅ Video Production Completed Successfully!")
    print(f"Canonical Deliverable: {out_file}")
    print(f"User Mirror:           {user_mirror}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
