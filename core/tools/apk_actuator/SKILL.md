---
name: apk_actuator
description: Autonomous Android APK Actuator & Bridge. Controls, automates, and interacts with any Android application running in the Flowork Micro-VM Subsystem.
keywords:
  - apk
  - android
  - actuator
  - mobile
  - uiautomator
  - dump
  - click
  - tap
  - swipe
  - scroll
  - video
  - upload
  - gallery
  - media
  - install
  - search
  - launch
  - keyboard
  - scrcpy
  - microvm
---

# 📱 SOVEREIGN ANDROID APK ACTUATOR & BRIDGE RUNBOOK

## 1. Core Operating Principles
The `apk_actuator` tool provides autonomous control of Android applications inside the Flowork Micro-VM Subsystem (Android 14 API 34). It bridges the agent directly into the Android accessibility tree (`uiautomator`), input subsystem (`evdev/adb`), and media gallery.

## 2. Autonomous App Awareness & Installation SOP
Never fail with "app not found". Follow this autonomous discovery reflex:
1. **Check Installed Apps**: Run `apk_actuator` with `action: "list_apps"`.
2. **Handle Missing App**:
   - If user requests an app that is not in the installed list, do NOT stop or give up.
   - Run `action: "search_app", query: "<app_name>"` to locate the candidate package on Google Play Store or APK CDN.
   - Run `action: "install_app", package: "<package_name>"` to download and install cleanly.
   - Once installed, proceed to `action: "launch", package: "<package_name>"`.
   - Alternatively, pass `auto_install: true` directly to `action: "launch"` to let the actuator search and install automatically.

## 3. Semantic UI Navigation & Inspection SOP
Avoid guessing pixel coordinates whenever possible:
1. **Introspect Active State**: Call `action: "dump_ui"`.
2. **Locate Target Elements**: Look through `elements` for relevant `text`, `desc` (content description), or `id`.
3. **Semantic Click**: Call `action: "click", text: "TargetText"` or `resource_id: "id_name"`. The actuator automatically computes the center coordinates `[cx, cy]` and executes the tap.
4. **Coordinate Tap Fallback**: If an element has no text or ID, use pre-calculated `center` coordinates from `dump_ui` via `action: "click", x: cx, y: cy`.
5. **Form Input**: Focus the input field via `action: "click"`, then type via `action: "type_text", text: "Your text here"`.

## 4. Video & Short Drama Scrolling SOP
For Melolo, DramaBox, TikTok, YouTube Shorts, and Instagram Reels:
- **Next Video / Next Episode**: Call `action: "scroll", direction: "up"`. This performs an instant vertical flick from `(360, 950)` to `(360, 250)`.
- **Previous Video / Previous Episode**: Call `action: "scroll", direction: "down"`.
- **Inspect Drama Metadata**: Call `action: "dump_ui"` to read episode title, episode number, like count, and comment buttons.

## 5. Media Upload & Social Publishing Workflow
To publish or upload videos/photos from the Linux host into Android apps:
1. **Stage Media into Android Gallery**:
   ```json
   {
     "action": "push_media",
     "file_path": "/path/to/host/video.mp4"
   }
   ```
   *Note: This automatically pushes the file to `/sdcard/DCIM/Camera/` and dispatches `MEDIA_SCANNER_SCAN_FILE` broadcast. The video appears at the top of the Android media picker immediately.*
2. **Launch Target App**:
   ```json
   {
     "action": "launch",
     "package": "tiktok"
   }
   ```
3. **Trigger Media Picker**:
   - Call `action: "dump_ui"` to identify the camera/upload or plus button (`"+"`, `"Unggah"`, `"Upload"`).
   - Call `action: "click", text: "+"` or relevant button ID.
4. **Select Pushed Media**:
   - The newly scanned media item is the first thumbnail in the gallery grid. Call `action: "click"` on the top-left item.
5. **Add Metadata & Publish**:
   - Type caption/tags via `action: "type_text"`.
   - Click `"Next"` / `"Berikutnya"` and `"Post"` / `"Posting"`.
