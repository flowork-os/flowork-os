#!/usr/bin/env python3
"""
Suno AI Audio Processor (sunoskill helper script)
Downloads YouTube song, isolates center vocal, and time-stretches to exactly 59.0s.
"""

import sys
import os
import subprocess
import shutil

def process_song(url, output_prefix="vocal_59s"):
    work_dir = "/opt/floworkos/documents/suno_experiment"
    dest_dir = "/home/awenkaudico/Documents/suno_experiment"
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(dest_dir, exist_ok=True)

    raw_wav = os.path.join(work_dir, "temp_source.wav")
    iso_wav = os.path.join(work_dir, "temp_iso.wav")
    out_mp3 = os.path.join(work_dir, f"{output_prefix}.mp3")
    out_wav = os.path.join(work_dir, f"{output_prefix}.wav")

    # 1. Download source audio
    print(f"→ Downloading source audio from {url}...")
    subprocess.run([
        "yt-dlp", "-x", "--audio-format", "wav", "--audio-quality", "0",
        "-o", raw_wav, url
    ], check=True)

    # 2. Extract center vocal
    print("→ Isolating center vocal track...")
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_wav,
        "-af", "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=180,lowpass=f=4200,dynaudnorm",
        iso_wav
    ], check=True)

    # 3. Calculate time-stretch factor to 59.0s
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", iso_wav
    ], capture_output=True, text=True, check=True)
    orig_dur = float(probe.stdout.strip())
    speed = orig_dur / 59.0
    print(f"→ Original: {orig_dur:.2f}s | Target: 59.0s | Speedup: {speed:.4f}x")

    factors = []
    rem = speed
    while rem > 2.0:
        factors.append(2.0)
        rem /= 2.0
    factors.append(rem)
    atempo_str = ",".join([f"atempo={f:.8f}" for f in factors])

    # 4. Render 59s artifacts
    print("→ Rendering 59-second time-stretched artifacts...")
    subprocess.run(["ffmpeg", "-y", "-i", iso_wav, "-af", atempo_str, "-t", "59", out_mp3], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", iso_wav, "-af", atempo_str, "-t", "59", out_wav], check=True)

    # 5. Mirror to user Documents
    shutil.copy2(out_mp3, os.path.join(dest_dir, f"{output_prefix}.mp3"))
    shutil.copy2(out_wav, os.path.join(dest_dir, f"{output_prefix}.wav"))

    print(f"✅ Success! Deliverables mirrored to {dest_dir}/{output_prefix}.mp3")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: process_song.py <youtube_url> [output_prefix]")
        sys.exit(1)
    prefix = sys.argv[2] if len(sys.argv) > 2 else "vocal_59s"
    process_song(sys.argv[1], prefix)
