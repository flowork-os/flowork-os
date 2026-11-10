#!/usr/bin/env python3
"""
👑 KAMIDI MASTERING PRO — SOVEREIGN LINUX BACKEND ENGINE
Provides native Linux OS integration:
- Presets filesystem management (~/.config/kamidi/presets)
- Native Linux FFmpeg sidecar dual-pass LUFS normalization
- Native Zenity file dialog integration (open audio, save master)
- Full binary and text file operations
"""

import sys
import os
import json
import subprocess
import base64

PRESETS_DIR = os.path.expanduser("~/.config/kamidi/presets")
os.makedirs(PRESETS_DIR, exist_ok=True)

def open_file_dialog(args):
    """Native file chooser dialog using Zenity."""
    title = args.get("title", "Load Audio Tracks")
    multiple = args.get("multiple", True)
    directory = args.get("directory", False)
    default_path = args.get("defaultPath")
    
    cmd = [
        "/usr/bin/zenity",
        "--file-selection",
        f"--title={title}"
    ]
    if directory:
        cmd.append("--directory")
    else:
        filters = args.get("filters", [])
        if filters:
            for f in filters:
                name = f.get("name", "Files")
                exts = " ".join(f"*.{e}" for e in f.get("extensions", []))
                cmd.append(f"--file-filter={name} | {exts}")
        cmd.append("--file-filter=Audio Files (*.wav, *.mp3, *.flac, *.ogg, *.aac, *.m4a, *.aiff) | *.wav *.mp3 *.flac *.ogg *.aac *.m4a *.aiff *.aif *.wma")
        cmd.append("--file-filter=All Files | *")

    if multiple:
        cmd.append("--multiple")
        cmd.append("--separator=|")
    if default_path and os.path.exists(default_path):
        cmd.append(f"--filename={default_path}")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            raw = res.stdout.strip()
            if not raw:
                return {"status": "success", "result": None}
            if multiple:
                paths = [p.strip() for p in raw.split("|") if p.strip()]
                return {"status": "success", "result": paths}
            else:
                return {"status": "success", "result": raw}
        return {"status": "success", "result": None}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def save_file_dialog(args):
    """Native save file dialog using Zenity."""
    title = args.get("title", "Simpan Master Audio")
    default_path = args.get("defaultPath", "mastered_track.wav")
    is_dir = args.get("directory", False)
    
    # If default_path is relative, put it in user's Music or home
    if not os.path.isabs(default_path):
        music_dir = os.path.expanduser("~/Music")
        if not os.path.exists(music_dir):
            music_dir = os.path.expanduser("~")
        default_path = os.path.join(music_dir, default_path)

    cmd = ["/usr/bin/zenity", "--file-selection"]
    if is_dir:
        cmd.extend([f"--title={title}", f"--filename={default_path}", "--directory"])
    else:
        cmd.extend([
            "--save",
            "--confirm-overwrite",
            f"--title={title}",
            f"--filename={default_path}",
            "--file-filter=WAV Audio (*.wav) | *.wav",
            "--file-filter=MP3 Audio (*.mp3) | *.mp3",
            "--file-filter=FLAC Audio (*.flac) | *.flac",
            "--file-filter=All Files | *"
        ])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            target = res.stdout.strip()
            return {"status": "success", "result": target if target else None}
        return {"status": "success", "result": None}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def execute(payload):
    """
    Handle IPC dispatch from WebKit2GTK frontend.
    """
    cmd = payload.get("cmd")
    args = payload.get("args", {})
    
    # 1. Native File Dialogs
    if cmd == "open_dialog":
        return open_file_dialog(args)

    elif cmd == "save_dialog":
        return save_file_dialog(args)

    # 2. File Reading & Writing
    elif cmd == "read_file":
        path = args.get("path", "")
        if not os.path.isabs(path):
            path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"status": "error", "error": f"File not found: {path}"}
        try:
            with open(path, "rb") as f:
                data_bytes = f.read()
            return {
                "status": "success",
                "result": {
                    "data_b64": base64.b64encode(data_bytes).decode("ascii")
                }
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif cmd == "write_file":
        path = args.get("path", "")
        data_b64 = args.get("data_b64", "")
        try:
            if not os.path.isabs(path):
                music_dir = os.path.expanduser("~/Music")
                os.makedirs(music_dir, exist_ok=True)
                path = os.path.join(music_dir, path)
            data_bytes = base64.b64decode(data_b64)
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "wb") as f:
                f.write(data_bytes)
            return {"status": "success", "result": True}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif cmd == "write_file_chunk":
        path = args.get("path", "")
        data_b64 = args.get("data_b64", "")
        is_first = args.get("first", False)
        try:
            if not os.path.isabs(path):
                music_dir = os.path.expanduser("~/Music")
                os.makedirs(music_dir, exist_ok=True)
                path = os.path.join(music_dir, path)
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            mode = "wb" if is_first else "ab"
            data_bytes = base64.b64decode(data_b64)
            with open(path, mode) as f:
                f.write(data_bytes)
            return {"status": "success", "result": True}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif cmd == "read_text_file":
        path = args.get("path", "")
        if not os.path.isabs(path):
            path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"status": "error", "error": f"File not found: {path}"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {"status": "success", "result": f.read()}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif cmd == "write_text_file":
        path = args.get("path", "")
        content = args.get("content", "")
        try:
            if not os.path.isabs(path):
                path = os.path.join(PRESETS_DIR, path)
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "result": True}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif cmd == "exists":
        path = args.get("path", "")
        if not os.path.isabs(path):
            path = os.path.expanduser(path)
        return {"status": "success", "result": os.path.exists(path)}

    elif cmd == "mkdir":
        path = args.get("path", "")
        if not os.path.isabs(path):
            path = os.path.expanduser(path)
        try:
            os.makedirs(path, exist_ok=True)
            return {"status": "success", "result": True}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # 3. Presets Management
    elif cmd == "bypass_read_dir_presets":
        folder = args.get("folder", PRESETS_DIR)
        target = folder if os.path.isabs(folder) else PRESETS_DIR
        os.makedirs(target, exist_ok=True)
        files = [f for f in os.listdir(target) if f.endswith(".json")]
        return {"status": "success", "result": files}

    elif cmd == "bypass_read_preset":
        path = args.get("path", "")
        if not os.path.isabs(path):
            path = os.path.join(PRESETS_DIR, path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"status": "success", "result": content}
        return {"status": "error", "error": f"Preset not found: {path}"}

    elif cmd == "bypass_write_preset":
        path = args.get("path", "")
        content = args.get("content", "{}")
        if not os.path.isabs(path):
            path = os.path.join(PRESETS_DIR, path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "success", "result": True}

    elif cmd == "bypass_delete_preset":
        path = args.get("path", "")
        if not os.path.isabs(path):
            path = os.path.join(PRESETS_DIR, path)
        if os.path.exists(path):
            os.remove(path)
        return {"status": "success", "result": True}

    # 4. Native Linux FFmpeg Sidecar execution
    elif cmd == "run_ffmpeg":
        ffmpeg_args = args.get("args", [])
        ffmpeg_bin = "/usr/bin/ffmpeg"
        if not os.path.exists(ffmpeg_bin):
            ffmpeg_bin = "ffmpeg"
            
        full_cmd = [ffmpeg_bin] + ffmpeg_args
        try:
            res = subprocess.run(full_cmd, capture_output=True, text=True, timeout=300)
            return {
                "status": "success",
                "result": {
                    "code": res.returncode,
                    "stdout": res.stdout,
                    "stderr": res.stderr
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "result": {
                    "code": 1,
                    "stdout": "",
                    "stderr": str(e)
                }
            }

    elif cmd == "extract_audio":
        video_path = args.get("path", "")
        if not os.path.exists(video_path):
            return {"status": "error", "error": f"Video file not found: {video_path}"}
        try:
            import hashlib
            temp_dir = "/tmp/flowork_audio"
            os.makedirs(temp_dir, exist_ok=True)
            stat = os.stat(video_path)
            h = hashlib.sha256(f"{video_path}_{stat.st_size}".encode()).hexdigest()[:16]
            out_wav = os.path.join(temp_dir, f"extracted_{h}.wav")
            if not os.path.exists(out_wav):
                cmd_ffmpeg = [
                    "/usr/bin/ffmpeg", "-y", "-i", video_path,
                    "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", out_wav
                ]
                res = subprocess.run(cmd_ffmpeg, capture_output=True, text=True)
                if res.returncode != 0:
                    return {"status": "error", "error": res.stderr}
            return {"status": "success", "result": {"path": out_wav}}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # 5. App Info
    elif cmd == "get_version":
        return {"status": "success", "result": "5.0.10"}

    elif cmd == "get_app_data_dir":
        app_dir = os.path.expanduser("~/.config/kamidi")
        os.makedirs(app_dir, exist_ok=True)
        return {"status": "success", "result": app_dir}

    return {"status": "error", "error": f"Unknown command: {cmd}"}
