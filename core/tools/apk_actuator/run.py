#!/usr/bin/env python3
"""
⚡ FLOWORK OS — SOVEREIGN ANDROID APK ACTUATOR & BRIDGE
Autonomous agent bridge for controlling, inspecting, automating, and interacting
with Android apps inside the Flowork Micro-VM Subsystem.
Author: Dr. Flow / Flowork Architecture Board
"""

import sys
import os
import json
import re
import subprocess
import time
import glob
import xml.etree.ElementTree as ET

ADB_BIN = "/opt/floworkos/android-sdk/platform-tools/adb"
if not os.path.exists(ADB_BIN):
    ADB_BIN = "adb"

FLOWORK_APK = "/opt/floworkos/bin/flowork-apk"

KNOWN_ALIASES = {
    "melolo": "com.worldance.drama",
    "tiktok": "com.ss.android.ugc.trill",
    "capcut": "com.lemon.lvoverseas",
    "shopee": "com.shopee.id",
    "deepseek": "com.deepseek.chat",
    "gemini": "com.google.android.apps.bard",
    "chatgpt": "com.openai.chatgpt",
    "suno": "com.suno.android",
    "dramabox": "com.storymatrix.drama",
    "aurora": "com.aurora.store",
    "playstore": "com.android.vending",
    "instagram": "com.instagram.android",
    "youtube": "com.google.android.youtube",
    "snackvideo": "com.kwai.video"
}

def run_cmd(cmd, timeout=30):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def run_adb(args, timeout=30):
    cmd = [ADB_BIN] + args
    return run_cmd(cmd, timeout=timeout)

def ensure_vm_online():
    code, out, _ = run_adb(["get-state"], timeout=5)
    if code == 0 and "device" in out:
        return True
    if os.path.exists(FLOWORK_APK):
        subprocess.Popen([FLOWORK_APK, "daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(10):
            time.sleep(1)
            code, out, _ = run_adb(["get-state"], timeout=3)
            if code == 0 and "device" in out:
                return True
    return False

def list_installed_apps():
    code, out, _ = run_adb(["shell", "pm", "list", "packages", "-3"])
    pkgs = []
    if code == 0:
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                pkgs.append(line[len("package:"):].strip())
    if "com.android.vending" not in pkgs:
        pkgs.insert(0, "com.android.vending")
    
    registry_file = os.path.expanduser("~/.config/flowork-apk/registry.json")
    reg_data = {}
    if os.path.exists(registry_file):
        try:
            with open(registry_file, "r") as f:
                reg_data = json.load(f)
        except Exception:
            pass

    results = []
    for p in pkgs:
        label = reg_data.get(p, {}).get("name", "")
        if not label:
            for k, v in KNOWN_ALIASES.items():
                if v == p:
                    label = k.capitalize()
                    break
        if not label:
            label = p.split(".")[-1].capitalize()
        results.append({
            "package": p,
            "label": label
        })
    return results

def is_app_installed(pkg_name):
    if not pkg_name:
        return False
    installed = list_installed_apps()
    for app in installed:
        if app["package"].lower() == pkg_name.lower():
            return True
    return False

def resolve_package(target):
    if not target:
        return None
    target_clean = target.strip().lower()
    if target_clean in KNOWN_ALIASES:
        return KNOWN_ALIASES[target_clean]
    
    installed = list_installed_apps()
    for app in installed:
        if app["package"].lower() == target_clean:
            return app["package"]
        if app["label"].lower() == target_clean:
            return app["package"]
    if "." in target:
        return target.strip()
    return None

def search_store(query):
    if not os.path.exists(FLOWORK_APK):
        return []
    code, out, _ = run_cmd([FLOWORK_APK, "search", query], timeout=15)
    results = []
    for line in out.splitlines():
        m = re.search(r'•\s*(.*?)\s*\[([a-zA-Z0-9_\.]+)\](?:\s*⭐\s*([0-9,\.]+))?(?:\s*\(Dev:\s*(.*?)\))?', line)
        if m:
            results.append({
                "title": m.group(1).strip(),
                "package": m.group(2).strip(),
                "rating": m.group(3) or "",
                "developer": m.group(4) or ""
            })
    return results

def install_app(target):
    if os.path.isfile(target):
        code, out, err = run_adb(["install", "-r", target], timeout=120)
        return {
            "status": "ok" if code == 0 else "error",
            "message": out if code == 0 else err,
            "path": target
        }
    else:
        code, out, err = run_cmd([FLOWORK_APK, "download", target, "--install"], timeout=180)
        return {
            "status": "ok" if code == 0 else "error",
            "message": out if code == 0 else err,
            "package": target
        }

def launch_app(target, auto_install=True):
    ensure_vm_online()
    resolved = resolve_package(target)
    
    # Autonomous awareness check: Is it actually installed?
    if not resolved or not is_app_installed(resolved):
        candidates = search_store(target)
        if candidates and auto_install:
            top_pkg = candidates[0]["package"]
            install_res = install_app(top_pkg)
            if install_res.get("status") == "ok":
                resolved = top_pkg
            else:
                return {
                    "status": "install_failed",
                    "message": f"App '{target}' was not installed. Auto-install attempted for '{top_pkg}' but failed.",
                    "error": install_res.get("message"),
                    "candidates": candidates
                }
        else:
            return {
                "status": "not_installed",
                "message": f"App '{target}' is not installed in the Flowork Micro-VM.",
                "action_needed": "Search and install the app first via action: 'search_app' or 'install_app'.",
                "candidates": candidates
            }

    code, out, err = run_cmd([FLOWORK_APK, "launch", resolved], timeout=15)
    time.sleep(2)
    return {
        "status": "ok",
        "message": f"Application '{resolved}' launched successfully.",
        "package": resolved
    }

def stop_app(target):
    resolved = resolve_package(target) or target
    run_adb(["shell", "am", "force-stop", resolved])
    run_adb(["shell", "input", "keyevent", "127"])
    run_adb(["shell", "cmd", "media_session", "dispatch", "pause"])
    return {
        "status": "ok",
        "message": f"Application '{resolved}' stopped and silenced.",
        "package": resolved
    }

def dump_ui():
    ensure_vm_online()
    tmp_xml = "/data/local/tmp/uidump.xml"
    run_adb(["shell", "uiautomator", "dump", tmp_xml], timeout=10)
    code, out, _ = run_adb(["shell", "cat", tmp_xml], timeout=10)
    if code != 0 or not out:
        return {"status": "error", "message": "Failed to dump Android UI hierarchy"}

    try:
        root = ET.fromstring(out)
    except Exception as e:
        return {"status": "error", "message": f"XML parse error: {e}"}

    elements = []
    for node in root.iter("node"):
        text = node.attrib.get("text", "").strip()
        cd = node.attrib.get("content-desc", "").strip()
        rid = node.attrib.get("resource-id", "").strip()
        cls_name = node.attrib.get("class", "").split(".")[-1]
        clickable = node.attrib.get("clickable", "false") == "true"
        scrollable = node.attrib.get("scrollable", "false") == "true"
        bounds = node.attrib.get("bounds", "")

        if text or cd or clickable or scrollable or rid:
            m = re.findall(r'\[(\d+),(\d+)\]', bounds)
            if len(m) == 2:
                x1, y1 = int(m[0][0]), int(m[0][1])
                x2, y2 = int(m[1][0]), int(m[1][1])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                if x2 > 0 and y2 > 0 and x1 < 720 and y1 < 1280:
                    el = {
                        "center": [cx, cy],
                        "bounds": [x1, y1, x2, y2],
                        "class": cls_name,
                        "clickable": clickable
                    }
                    if text:
                        el["text"] = text
                    if cd:
                        el["desc"] = cd
                    if rid:
                        el["id"] = rid.split("/")[-1] if "/" in rid else rid
                    if scrollable:
                        el["scrollable"] = True
                    elements.append(el)

    return {
        "status": "ok",
        "elements_count": len(elements),
        "elements": elements
    }

def click_element(params):
    if "x" in params and "y" in params:
        x, y = int(params["x"]), int(params["y"])
        run_adb(["shell", "input", "tap", str(x), str(y)])
        return {"status": "ok", "action": "tap", "coordinates": [x, y]}

    target_text = params.get("text", "").strip().lower()
    target_desc = params.get("desc", "").strip().lower()
    target_id = params.get("resource_id", "").strip().lower()

    if not target_text and not target_desc and not target_id:
        return {"status": "error", "message": "Specify 'x'/'y', 'text', 'desc', or 'resource_id' to click"}

    ui_res = dump_ui()
    if ui_res.get("status") != "ok":
        return ui_res

    matched = None
    for el in ui_res.get("elements", []):
        el_text = el.get("text", "").lower()
        el_desc = el.get("desc", "").lower()
        el_id = el.get("id", "").lower()

        if target_text and (target_text == el_text or target_text in el_text):
            matched = el
            break
        if target_desc and (target_desc == el_desc or target_desc in el_desc):
            matched = el
            break
        if target_id and (target_id == el_id or target_id in el_id):
            matched = el
            break

    if matched:
        cx, cy = matched["center"]
        run_adb(["shell", "input", "tap", str(cx), str(cy)])
        return {
            "status": "ok",
            "action": "clicked_element",
            "element": matched,
            "coordinates": [cx, cy]
        }
    else:
        return {
            "status": "not_found",
            "message": f"No element matching text='{target_text}', desc='{target_desc}', or id='{target_id}' found.",
            "visible_texts": [e.get("text") for e in ui_res.get("elements", []) if e.get("text")][:15]
        }

def type_text(text):
    if not text:
        return {"status": "error", "message": "No text provided to type"}
    escaped = text.replace(" ", "%s").replace("&", "\\&").replace("<", "\\<").replace(">", "\\>").replace("\"", "\\\"").replace("'", "\\'")
    code, out, err = run_adb(["shell", "input", "text", escaped])
    return {
        "status": "ok" if code == 0 else "error",
        "action": "type_text",
        "typed": text
    }

def scroll(params):
    direction = params.get("direction", "up").lower()
    distance = params.get("distance", "normal").lower()
    duration = int(params.get("duration_ms", 250))

    if all(k in params for k in ("x1", "y1", "x2", "y2")):
        x1, y1 = int(params["x1"]), int(params["y1"])
        x2, y2 = int(params["x2"]), int(params["y2"])
    else:
        if direction == "up":
            if distance == "short":
                x1, y1, x2, y2 = 360, 800, 360, 450
            else:
                x1, y1, x2, y2 = 360, 950, 360, 250
        elif direction == "down":
            if distance == "short":
                x1, y1, x2, y2 = 360, 450, 360, 800
            else:
                x1, y1, x2, y2 = 360, 250, 360, 950
        elif direction == "left":
            x1, y1, x2, y2 = 620, 640, 100, 640
        elif direction == "right":
            x1, y1, x2, y2 = 100, 640, 620, 640
        else:
            x1, y1, x2, y2 = 360, 950, 360, 250

    run_adb(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])
    return {
        "status": "ok",
        "action": "scroll",
        "direction": direction,
        "from": [x1, y1],
        "to": [x2, y2],
        "duration_ms": duration
    }

def press_key(key):
    key_map = {
        "back": 4,
        "home": 3,
        "enter": 66,
        "tab": 61,
        "app_switch": 187,
        "volume_up": 24,
        "volume_down": 25,
        "play_pause": 85,
        "del": 67,
        "delete": 67
    }
    key_str = str(key).lower()
    keycode = key_map.get(key_str)
    if keycode is None:
        try:
            keycode = int(key)
        except ValueError:
            return {"status": "error", "message": f"Unknown key '{key}'"}

    run_adb(["shell", "input", "keyevent", str(keycode)])
    return {
        "status": "ok",
        "action": "press_key",
        "key": key_str,
        "keycode": keycode
    }

def push_media(params):
    file_path = params.get("file_path", "")
    if not file_path or not os.path.exists(file_path):
        return {"status": "error", "message": f"File does not exist on host: {file_path}"}

    filename = os.path.basename(file_path)
    dest_dir = params.get("destination_folder", "/sdcard/DCIM/Camera")
    dest_path = f"{dest_dir}/{filename}"

    run_adb(["shell", "mkdir", "-p", dest_dir])
    code, out, err = run_adb(["push", file_path, dest_path], timeout=120)
    if code != 0:
        return {"status": "error", "message": f"ADB push failed: {err}"}

    run_adb(["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{dest_path}"])
    run_adb(["shell", "cmd", "media", "scan-volume", "external"])

    return {
        "status": "ok",
        "action": "push_media",
        "host_path": file_path,
        "android_path": dest_path,
        "scanned": True,
        "message": f"Media '{filename}' pushed to Android gallery and indexed successfully."
    }

def capture_screen(params):
    out_path = params.get("output_path", "/dev/shm/flowork_apk_screen.png")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    tmp_remote = "/data/local/tmp/flowork_cap.png"
    code, _, _ = run_adb(["shell", "screencap", "-p", tmp_remote], timeout=10)
    if code == 0:
        p_code, _, _ = run_adb(["pull", tmp_remote, out_path], timeout=10)
        if p_code == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return {
                "status": "ok",
                "method": "adb_screencap",
                "path": out_path,
                "size_bytes": os.path.getsize(out_path)
            }

    try:
        find_w = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "Melolo"], capture_output=True, text=True)
        wids = find_w.stdout.strip().split()
        if not wids:
            find_w2 = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "flowork-apk"], capture_output=True, text=True)
            wids = find_w2.stdout.strip().split()

        if wids:
            wid = wids[0]
            c_res = subprocess.run(["import", "-window", wid, out_path], capture_output=True, timeout=5)
            if c_res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                return {
                    "status": "ok",
                    "method": "x11_window_capture",
                    "window_id": wid,
                    "path": out_path,
                    "size_bytes": os.path.getsize(out_path)
                }
    except Exception:
        pass

    return {
        "status": "error",
        "message": "Screen capture failed via both ADB and X11 fallback."
    }

def get_current_activity():
    code, out, _ = run_adb(["shell", "dumpsys", "window"])
    if code != 0:
        return {"status": "error", "message": "Failed to inspect window manager"}

    focus_pkg = ""
    focus_act = ""
    for line in out.splitlines():
        if "mCurrentFocus" in line:
            m = re.search(r'([a-zA-Z0-9_\.]+)/([a-zA-Z0-9_\.]+)', line)
            if m:
                focus_pkg = m.group(1)
                focus_act = m.group(2)
                break

    return {
        "status": "ok",
        "package": focus_pkg,
        "activity": focus_act
    }

def main():
    try:
        raw_in = sys.stdin.read().strip()
        params = json.loads(raw_in) if raw_in else {}
        action = params.get("action", "list_apps").lower()

        if action in ("list_apps", "list"):
            apps = list_installed_apps()
            print(json.dumps({"status": "ok", "apps": apps, "count": len(apps)}))

        elif action in ("search_app", "search"):
            query = params.get("query", params.get("package", ""))
            results = search_store(query)
            print(json.dumps({"status": "ok", "query": query, "results": results, "count": len(results)}))

        elif action in ("install_app", "install"):
            target = params.get("package", params.get("file_path", ""))
            res = install_app(target)
            print(json.dumps(res))

        elif action in ("uninstall_app", "uninstall"):
            pkg = resolve_package(params.get("package", "")) or params.get("package", "")
            code, out, err = run_adb(["uninstall", pkg])
            print(json.dumps({"status": "ok" if code == 0 else "error", "message": out if code == 0 else err, "package": pkg}))

        elif action in ("launch_app", "launch", "open"):
            target = params.get("package", params.get("app", ""))
            auto_inst = params.get("auto_install", True)
            res = launch_app(target, auto_install=auto_inst)
            print(json.dumps(res))

        elif action in ("stop_app", "stop", "close"):
            target = params.get("package", params.get("app", ""))
            res = stop_app(target)
            print(json.dumps(res))

        elif action in ("dump_ui", "inspect_ui", "ui_tree"):
            res = dump_ui()
            print(json.dumps(res))

        elif action in ("click", "tap"):
            res = click_element(params)
            print(json.dumps(res))

        elif action in ("type_text", "type"):
            text = params.get("text", "")
            res = type_text(text)
            print(json.dumps(res))

        elif action in ("scroll", "swipe", "flick"):
            res = scroll(params)
            print(json.dumps(res))

        elif action in ("press_key", "key"):
            key = params.get("key", params.get("keycode", "back"))
            res = press_key(key)
            print(json.dumps(res))

        elif action in ("push_media", "upload_media"):
            res = push_media(params)
            print(json.dumps(res))

        elif action in ("capture_screen", "screenshot"):
            res = capture_screen(params)
            print(json.dumps(res))

        elif action in ("get_current_activity", "current_app"):
            res = get_current_activity()
            print(json.dumps(res))

        else:
            print(json.dumps({"status": "error", "message": f"Unknown action '{action}'"}))
            sys.exit(1)

    except Exception as e:
        sys.stderr.write(f"apk_actuator error: {e}\n")
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
