#!/usr/bin/env python3
"""
Flowork Sovereign Profile Manager Backend
"""

import os
import pwd
import sys
import base64
import getpass
import platform
import shutil
from PIL import Image

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AVATAR_DIR = os.path.join(APP_DIR, "assets", "avatars")

def get_base64_img(path):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(path)[1].lower().replace(".", "")
            if ext == "svg":
                ext = "svg+xml"
            return f"data:image/{ext};base64,{b64}"
    except Exception:
        return ""

def execute(payload):
    action = payload.get("action", "")
    username = getpass.getuser()
    pw_entry = pwd.getpwnam(username)

    if action == "get_profile":
        face_path = os.path.expanduser("~/.face")
        presets = [
            {"id": "flowork-cyan", "name": "Cyber Cyan (Default)", "color": "#00f3ff", "file": "flowork-cyan.png"},
            {"id": "flowork-green", "name": "Matrix Neon Green", "color": "#00ff66", "file": "flowork-green.png"},
            {"id": "flowork-purple", "name": "Quantum Violet", "color": "#a855f7", "file": "flowork-purple.png"},
            {"id": "flowork-amber", "name": "Solar Amber", "color": "#f59e0b", "file": "flowork-amber.png"},
            {"id": "flowork-crimson", "name": "Crimson Cyber", "color": "#ef4444", "file": "flowork-crimson.png"},
        ]
        
        for p in presets:
            p_path = os.path.join(AVATAR_DIR, p["file"])
            p["image"] = get_base64_img(p_path)

        real_name = pw_entry.pw_gecos.split(",")[0] if pw_entry.pw_gecos else username

        return {
            "status": "success",
            "profile": {
                "username": username,
                "real_name": real_name or username,
                "home": pw_entry.pw_dir,
                "shell": pw_entry.pw_shell,
                "os": "Flowork OS 1.0 (Sovereign Linux)",
                "kernel": platform.release(),
                "avatar": get_base64_img(face_path),
                "presets": presets
            }
        }

    elif action == "set_avatar_preset":
        preset_id = payload.get("preset_id", "flowork-cyan")
        src_path = os.path.join(AVATAR_DIR, f"{preset_id}.png")
        if not os.path.exists(src_path):
            return {"status": "error", "error": f"Preset '{preset_id}' not found."}

        face_path = os.path.expanduser("~/.face")
        face_icon = os.path.expanduser("~/.face.icon")
        
        # Copy to ~/.face
        shutil.copyfile(src_path, face_path)
        if os.path.islink(face_icon) or os.path.exists(face_icon):
            try:
                os.remove(face_icon)
            except Exception:
                pass
        os.symlink(".face", face_icon)

        # Mirror to repo skel if present
        repo_skel = os.path.expanduser("~/flowork-os-repo/skel/.face")
        if os.path.exists(os.path.dirname(repo_skel)):
            try:
                shutil.copyfile(src_path, repo_skel)
            except Exception:
                pass

        return {
            "status": "success",
            "message": f"Avatar updated to {preset_id}!",
            "avatar": get_base64_img(face_path)
        }

    elif action == "set_custom_avatar":
        data_b64 = payload.get("image_data", "")
        if not data_b64:
            return {"status": "error", "error": "No image data received."}

        try:
            # Strip header if present
            if "," in data_b64:
                data_b64 = data_b64.split(",")[1]
            raw_bytes = base64.b64decode(data_b64)
            
            from io import BytesIO
            img = Image.open(BytesIO(raw_bytes)).convert("RGBA")
            img = img.resize((256, 256), Image.Resampling.LANCZOS)

            face_path = os.path.expanduser("~/.face")
            face_icon = os.path.expanduser("~/.face.icon")
            img.save(face_path, "PNG")

            if os.path.islink(face_icon) or os.path.exists(face_icon):
                try:
                    os.remove(face_icon)
                except Exception:
                    pass
            os.symlink(".face", face_icon)

            return {
                "status": "success",
                "message": "Custom avatar uploaded and applied!",
                "avatar": get_base64_img(face_path)
            }
        except Exception as e:
            return {"status": "error", "error": f"Failed to process custom image: {e}"}

    return {"status": "error", "error": f"Unknown action: {action}"}
