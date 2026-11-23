#!/usr/bin/env python3
"""
Suno Music Producer - Audio Preparation Script
Separates pure vocal stem using Demucs AI, speeds up 5x (500% robot pitch) to bypass Suno copyright filter,
and auto-syncs audio to Android Subsystem for Suno APK ingestion.
"""
import os
import sys
import argparse
import subprocess
import shutil

DEMUCS_BIN = "/opt/floworkos/apps/suno-demucs/venv/bin/demucs"
ADB_BIN = "/opt/floworkos/android-sdk/platform-tools/adb"
DEFAULT_OUT_DIR = os.path.expanduser("~/Music/suno_ready")
ANDROID_OUT_DIR = "/sdcard/Music/suno_ready"

def run_cmd(cmd, check=True):
    return subprocess.run(cmd, check=check, capture_output=True, text=True)

def process_track(input_source, speed=5.0, mode="pitch", launch=False):
    os.makedirs(DEFAULT_OUT_DIR, exist_ok=True)
    work_dir = "/tmp/suno_prep"
    os.makedirs(work_dir, exist_ok=True)

    raw_wav = os.path.join(work_dir, "raw_source.wav")

    # 1. Acquire audio
    if input_source.startswith("http://") or input_source.startswith("https://"):
        print(f"[*] Downloading audio from URL: {input_source}...")
        meta_cmd = ["/usr/local/bin/yt-dlp", "--get-title", input_source]
        title_res = subprocess.run(meta_cmd, capture_output=True, text=True)
        raw_title = title_res.stdout.strip() if title_res.returncode == 0 else "source_track"
        dl_cmd = [
            "/usr/local/bin/yt-dlp", "-x", "--audio-format", "wav",
            "--audio-quality", "0", "-o", raw_wav, input_source
        ]
        run_cmd(dl_cmd)
    else:
        print(f"[*] Reading local audio file: {input_source}...")
        raw_title = os.path.splitext(os.path.basename(input_source))[0]
        # convert to standard wav
        conv_cmd = ["ffmpeg", "-y", "-i", input_source, "-vn", "-acodec", "pcm_s16le", raw_wav]
        run_cmd(conv_cmd)

    safe_title = "".join(c for c in raw_title if c.isalnum() or c in (" ", "-", "_")).strip()[:40]
    safe_title = safe_title.replace(" ", "_")

    # 2. Vocal isolation via Demucs AI
    print("[*] Isolating pure vocal stem using Demucs AI Hybrid Transformer...")
    stems_out = os.path.join(work_dir, "stems")
    os.makedirs(stems_out, exist_ok=True)

    demucs_cmd = [
        DEMUCS_BIN, "--two-stems", "vocals", "-n", "htdemucs",
        "-o", stems_out, raw_wav
    ]
    subprocess.run(demucs_cmd, check=True)

    vocal_wav = os.path.join(stems_out, "htdemucs", "raw_source", "vocals.wav")
    if not os.path.exists(vocal_wav):
        print("[!] Error: Demucs vocals.wav not found!")
        sys.exit(1)

    # 3. Probe vocal duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", vocal_wav
    ]
    p_res = run_cmd(probe_cmd)
    orig_dur = float(p_res.stdout.strip())
    final_dur = orig_dur / speed
    print(f"[*] Original duration: {orig_dur:.1f}s | Speedup: {speed}x | Target duration: {final_dur:.1f}s")

    # 4. Apply 5x robot voice / modulation
    out_mp3_name = f"{safe_title}_suno_robot_{speed}x.mp3"
    out_mp3_path = os.path.join(DEFAULT_OUT_DIR, out_mp3_name)

    if mode == "pitch":
        # Extreme pitch shift + speedup (chipmunk robot effect)
        rate_mult = int(44100 * speed)
        af_filter = f"asetrate={rate_mult},aresample=44100,volume=1.5"
    else:
        # Chained atempo (tempo only)
        factors = []
        rem = speed
        while rem > 2.0:
            factors.append(2.0)
            rem /= 2.0
        factors.append(rem)
        af_filter = ",".join([f"atempo={f:.6f}" for f in factors]) + ",volume=1.5"

    print(f"[*] Rendering robot audio with filter: {af_filter}...")
    render_cmd = [
        "ffmpeg", "-y", "-i", vocal_wav,
        "-af", af_filter,
        "-b:a", "192k",
        out_mp3_path
    ]
    run_cmd(render_cmd)

    print(f"✅ Host audio saved to: {out_mp3_path}")

    # 5. Sync to Android Micro-VM
    print("[*] Syncing audio to Android Subsystem (/sdcard/Music/suno_ready/)...")
    if os.path.exists(ADB_BIN):
        run_cmd([ADB_BIN, "shell", "mkdir", "-p", ANDROID_OUT_DIR], check=False)
        android_dest = f"{ANDROID_OUT_DIR}/{out_mp3_name}"
        run_cmd([ADB_BIN, "push", out_mp3_path, android_dest], check=False)
        run_cmd([ADB_BIN, "shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{android_dest}"], check=False)
        print(f"✅ Synced to Android: {android_dest}")

    # 6. Launch Suno APK if requested
    if launch:
        print("[*] Launching Suno APK window on desktop...")
        launch_cmd = ["/opt/floworkos/bin/flowork-apk", "launch", "com.suno.android"]
        subprocess.Popen(launch_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return out_mp3_path

def main():
    parser = argparse.ArgumentParser(description="Prepare trending songs for Suno Music Producer (AI Vocal Isolation + 5x Robot Modulation)")
    parser.add_argument("source", help="YouTube URL or local audio/video file")
    parser.add_argument("--speed", type=float, default=5.0, help="Speedup multiplier (default: 5.0 for 500%% robot voice)")
    parser.add_argument("--mode", choices=["pitch", "atempo"], default="pitch", help="Audio modulation mode: 'pitch' (robot chipmunk) or 'atempo' (tempo only)")
    parser.add_argument("--launch", action="store_true", help="Launch Suno APK on desktop upon completion")

    args = parser.parse_args()
    process_track(args.source, speed=args.speed, mode=args.mode, launch=args.launch)

if __name__ == "__main__":
    main()
