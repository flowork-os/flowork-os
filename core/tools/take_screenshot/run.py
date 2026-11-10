#!/usr/bin/env python3
"""
⚡ FLOWORK OS — SOVEREIGN TOOL RUNNER: take_screenshot
Captures screen via maim, optimizes dimensions, saves to ~/Pictures/Screenshots,
and sends realtime notification to Mr. Flow companion chat UI.
"""
import sys
import os
import json
import time
import subprocess
import glob
import io
import base64
from PIL import Image

def notify_sidebar_chat(image_path):
    sockets = glob.glob("/tmp/mrflow-sidebar-*.sock")
    if not sockets:
        return
    import socket
    payload = json.dumps({
        "action": "eval_js",
        "code": f"if (window.displayScreenshotNotification) {{ window.displayScreenshotNotification({json.dumps(image_path)}); }}"
    })
    for s_path in sockets:
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(1.0)
            client.connect(s_path)
            client.sendall(payload.encode("utf-8"))
            client.close()
        except Exception:
            pass

def main():
    params = {}
    if not sys.stdin.isatty():
        try:
            raw_in = sys.stdin.read().strip()
            if raw_in:
                params = json.loads(raw_in)
        except Exception:
            pass

    if len(sys.argv) > 1 and not params:
        try:
            params = json.loads(sys.argv[1])
        except Exception:
            params = {"filename": sys.argv[1]}

    home = os.environ.get("HOME") or os.path.expanduser("~")
    target_dir = os.path.join(home, "Pictures/Screenshots")
    os.makedirs(target_dir, exist_ok=True)

    filename = params.get("filename")
    target = params.get("target", "full")
    compress = params.get("compress", True)
    fast = params.get("fast", False)
    ram_only = params.get("ram_only", False)

    start_time = time.time()

    if ram_only:
        output_path = "/dev/shm/flowork_framebuffer.webp" if fast else "/dev/shm/flowork_framebuffer.png"
    elif not filename:
        timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S")
        ext = ".webp" if fast else ".png"
        filename = f"Screenshot_{timestamp_str}{ext}"
        output_path = os.path.join(target_dir, filename)
    else:
        if not any(filename.endswith(e) for e in [".png", ".jpg", ".jpeg", ".webp"]):
            filename += ".webp" if fast else ".png"
        output_path = os.path.join(target_dir, filename)

    env = dict(os.environ)
    if not env.get("DISPLAY"):
        env["DISPLAY"] = ":0"
    if not env.get("XAUTHORITY"):
        env["XAUTHORITY"] = os.path.expanduser("~/.Xauthority")

    cmd = ["/usr/bin/maim"]
    if target == "active":
        try:
            xid = subprocess.check_output(["/usr/bin/xdotool", "getactivewindow"], env=env).decode().strip()
            if xid:
                cmd.extend(["-i", xid])
        except Exception:
            pass

    # High-speed in-memory stream capture (zero intermediate disk write)
    try:
        raw_stream = subprocess.check_output(cmd, env=env, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode().strip() or "maim capture failed"
        print(json.dumps({"error": err_msg}))
        sys.exit(e.returncode or 1)

    orig_w, orig_h = 0, 0
    try:
        with Image.open(io.BytesIO(raw_stream)) as img:
            orig_w, orig_h = img.size
            if compress:
                max_w, max_h = (1280, 720) if fast else (1600, 1000)
                if orig_w > max_w or orig_h > max_h:
                    resample_filter = Image.Resampling.BILINEAR if fast else Image.Resampling.LANCZOS
                    img.thumbnail((max_w, max_h), resample_filter)
            
            # Single atomic write to destination
            if fast or output_path.endswith(".webp"):
                img.save(output_path, "WEBP", quality=80)
            else:
                img.save(output_path, "PNG", optimize=False, compress_level=1)
    except Exception as e:
        print(json.dumps({"error": f"Image processing failed: {e}"}))
        sys.exit(1)

    capture_duration_ms = round((time.time() - start_time) * 1000, 1)
    size_bytes = os.path.getsize(output_path) if os.path.exists(output_path) else 0

    notify_sidebar_chat(output_path)

    response = {
        "status": "success",
        "file_path": output_path,
        "width": orig_w,
        "height": orig_h,
        "size_bytes": size_bytes,
        "size_kb": round(size_bytes / 1024, 1),
        "capture_duration_ms": capture_duration_ms,
        "markdown": f"![Screenshot](file://{output_path})",
        "message": f"Screenshot successfully captured in {capture_duration_ms}ms and saved to {output_path} ({round(size_bytes/1024, 1)} KB)."
    }
    print(json.dumps(response))
    sys.exit(0)

if __name__ == "__main__":
    main()
