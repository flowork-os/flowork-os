#!/usr/bin/env python3
import os
import subprocess
import glob
import shutil

FLOWORK_SVG = "/usr/share/icons/flowork/flowork-logo.svg"
FLOWORK_EMBLEM_SVG = "/usr/share/icons/flowork/flowork-emblem.svg"

# Pre-render PNGs at all common sizes
RENDER_DIR = "/tmp/flowork_renders"
os.makedirs(RENDER_DIR, exist_ok=True)
SIZES = [16, 22, 24, 32, 36, 48, 64, 96, 128, 256, 512]

for sz in SIZES:
    png_path = f"{RENDER_DIR}/flowork_{sz}.png"
    subprocess.run(["rsvg-convert", "-w", str(sz), "-h", str(sz), FLOWORK_SVG, "-o", png_path], check=True)

def get_best_png(target_path):
    # Try to deduce size from path
    for sz in [512, 256, 128, 96, 64, 48, 36, 32, 24, 22, 16]:
        if f"{sz}x{sz}" in target_path or f"/{sz}/" in target_path:
            return f"{RENDER_DIR}/flowork_{sz}.png"
    # Inspect with identify if available or default 128
    try:
        res = subprocess.run(["identify", "-format", "%w", target_path], capture_output=True, text=True)
        w = int(res.stdout.strip())
        closest = min(SIZES, key=lambda x: abs(x - w))
        return f"{RENDER_DIR}/flowork_{closest}.png"
    except Exception:
        return f"{RENDER_DIR}/flowork_128.png"

# 1. Replace all debian SVG icons in /usr/share/icons
replaced_count = 0
for root, dirs, files in os.walk("/usr/share/icons"):
    for f in files:
        full_path = os.path.join(root, f)
        f_lower = f.lower()
        if "debian" in f_lower:
            if f_lower.endswith(".svg"):
                try:
                    shutil.copyfile(FLOWORK_SVG, full_path)
                    replaced_count += 1
                except Exception as e:
                    print(f"Error copying to {full_path}: {e}")
            elif f_lower.endswith(".png"):
                best = get_best_png(full_path)
                try:
                    shutil.copyfile(best, full_path)
                    replaced_count += 1
                except Exception as e:
                    print(f"Error copying to {full_path}: {e}")

# 2. Replace generic distributor-logo and start-here in main themes
for root, dirs, files in os.walk("/usr/share/icons"):
    for f in files:
        full_path = os.path.join(root, f)
        if f in ["distributor-logo.svg", "start-here.svg", "start-here-symbolic.svg", "distributor-logo-symbolic.svg"]:
            try:
                shutil.copyfile(FLOWORK_SVG, full_path)
                replaced_count += 1
            except Exception:
                pass

# 3. Replace debian & ubuntu pixmaps in /usr/share/pixmaps
for root, dirs, files in os.walk("/usr/share/pixmaps"):
    for f in files:
        full_path = os.path.join(root, f)
        f_lower = f.lower()
        if "debian" in f_lower or "ubuntu" in f_lower:
            if f_lower.endswith(".svg"):
                try:
                    shutil.copyfile(FLOWORK_SVG, full_path)
                    replaced_count += 1
                except Exception:
                    pass
            elif f_lower.endswith(".png"):
                best = get_best_png(full_path)
                try:
                    shutil.copyfile(best, full_path)
                    replaced_count += 1
                except Exception:
                    pass

# 4. Replace debian plymouth theme logos
for root, dirs, files in os.walk("/usr/share/plymouth"):
    for f in files:
        full_path = os.path.join(root, f)
        f_lower = f.lower()
        if "debian" in f_lower or "ubuntu" in f_lower or f in ["logo.png", "watermark.png"]:
            if f_lower.endswith(".svg"):
                try:
                    shutil.copyfile(FLOWORK_SVG, full_path)
                    replaced_count += 1
                except Exception:
                    pass
            elif f_lower.endswith(".png"):
                best = get_best_png(full_path)
                try:
                    shutil.copyfile(best, full_path)
                    replaced_count += 1
                except Exception:
                    pass

# 5. Replace desktop-base debian references
for root, dirs, files in os.walk("/usr/share/desktop-base"):
    for f in files:
        full_path = os.path.join(root, f)
        f_lower = f.lower()
        if "debian" in f_lower:
            if f_lower.endswith(".svg"):
                try:
                    shutil.copyfile(FLOWORK_SVG, full_path)
                    replaced_count += 1
                except Exception:
                    pass
            elif f_lower.endswith(".png"):
                best = get_best_png(full_path)
                try:
                    shutil.copyfile(best, full_path)
                    replaced_count += 1
                except Exception:
                    pass

# 6. Sanitize /etc/debian_version
with open("/etc/debian_version", "w") as fp:
    fp.write("1.0 (Flowork Sovereign)\n")

# 7. Replace skel .face and .face.icon with Flowork Sovereign avatar
skel_face = "/etc/skel/.face"
skel_icon = "/etc/skel/.face.icon"
try:
    best_face = f"{RENDER_DIR}/flowork_256.png"
    if os.path.exists(best_face):
        shutil.copyfile(best_face, skel_face)
        if os.path.islink(skel_icon) or os.path.exists(skel_icon):
            os.remove(skel_icon)
        os.symlink(".face", skel_icon)
        print("Updated /etc/skel/.face and /etc/skel/.face.icon with Flowork Avatar")
except Exception as e:
    print(f"Notice: /etc/skel/.face update: {e}")

print(f"[Flowork OS Branding] Successfully replaced {replaced_count} Debian branding assets with Flowork Sovereign Logo!")
