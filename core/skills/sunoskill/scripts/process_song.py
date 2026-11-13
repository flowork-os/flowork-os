#!/usr/bin/env python3
"""
Suno AI Audio Processor (sunoskill helper script)
Downloads YouTube song, isolates center vocal, and time-stretches (by percentage or to target duration).
"""

import sys
import os
import argparse
import subprocess
import shutil

def process_song(url, output_prefix="vocal_processed", speed_pct=None, target_sec=None):
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

    # 2. Extract true neural AI vocal track (Demucs Hybrid Transformer)
    print("→ Separating true vocal track via Demucs AI...")
    demucs_bin = "/opt/floworkos/apps/suno-demucs/venv/bin/demucs"
    stems_out = os.path.join(work_dir, "stems")
    if os.path.exists(demucs_bin):
        env = os.environ.copy()
        env["SSL_CERT_FILE"] = "/etc/ssl/certs/ca-certificates.crt"
        subprocess.run([
            demucs_bin, "--two-stems", "vocals", "-n", "htdemucs",
            "-o", stems_out, raw_wav
        ], env=env, check=True)
        # Locate generated vocals.wav
        bname = os.path.splitext(os.path.basename(raw_wav))[0]
        gen_vocal = os.path.join(stems_out, "htdemucs", bname, "vocals.wav")
        if os.path.exists(gen_vocal):
            shutil.copy2(gen_vocal, iso_wav)
        else:
            # Fallback
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_wav,
                "-af", "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=180,lowpass=f=4200,dynaudnorm",
                iso_wav
            ], check=True)
    else:
        # Fallback to center bandpass
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_wav,
            "-af", "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=180,lowpass=f=4200,dynaudnorm",
            iso_wav
        ], check=True)

    # 3. Calculate time-stretch factor
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", iso_wav
    ], capture_output=True, text=True, check=True)
    orig_dur = float(probe.stdout.strip())

    if speed_pct is not None:
        speed = 1.0 + (float(speed_pct) / 100.0)
        final_target = orig_dur / speed
        print(f"→ Original: {orig_dur:.2f}s | Speedup: +{speed_pct}% ({speed:.2f}x) | Result: {final_target:.2f}s")
    elif target_sec is not None:
        final_target = float(target_sec)
        speed = orig_dur / final_target
        print(f"→ Original: {orig_dur:.2f}s | Target: {final_target:.2f}s | Speedup: {speed:.4f}x")
    else:
        # Default to 30% speedup
        speed = 1.30
        final_target = orig_dur / speed
        print(f"→ Defaulting to +30% speedup: {orig_dur:.2f}s -> {final_target:.2f}s ({speed:.2f}x)")

    factors = []
    rem = speed
    while rem > 2.0:
        factors.append(2.0)
        rem /= 2.0
    factors.append(rem)
    atempo_str = ",".join([f"atempo={f:.8f}" for f in factors])

    # 4. Render artifacts
    print(f"→ Rendering time-stretched artifacts ({atempo_str})...")
    cmd_mp3 = ["ffmpeg", "-y", "-i", iso_wav, "-af", atempo_str]
    cmd_wav = ["ffmpeg", "-y", "-i", iso_wav, "-af", atempo_str]
    if target_sec is not None:
        cmd_mp3.extend(["-t", str(target_sec)])
        cmd_wav.extend(["-t", str(target_sec)])
    cmd_mp3.append(out_mp3)
    cmd_wav.append(out_wav)

    subprocess.run(cmd_mp3, check=True)
    subprocess.run(cmd_wav, check=True)

    # 5. Mirror to user Documents
    shutil.copy2(out_mp3, os.path.join(dest_dir, f"{output_prefix}.mp3"))
    shutil.copy2(out_wav, os.path.join(dest_dir, f"{output_prefix}.wav"))

    print(f"✅ Success! Deliverables mirrored to {dest_dir}/{output_prefix}.mp3")

def main():
    parser = argparse.ArgumentParser(description="Suno AI Audio Processor")
    parser.add_argument("url", help="YouTube source URL")
    parser.add_argument("--prefix", default="vocal_processed", help="Output filename prefix")
    parser.add_argument("--speed-pct", type=float, default=None, help="Speed up by percentage (e.g. 30 for +30%% speed)")
    parser.add_argument("--target-sec", type=float, default=None, help="Speed up to exact target duration in seconds (e.g. 59)")

    args = parser.parse_args()
    process_song(args.url, args.prefix, args.speed_pct, args.target_sec)

if __name__ == "__main__":
    main()
