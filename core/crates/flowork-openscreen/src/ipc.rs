use crate::recorder::{RecorderManager, RecordingSession};
use base64::Engine;
use serde::{Deserialize, Serialize};
use std::{
    path::PathBuf,
    process::Command,
    sync::{Arc, Mutex},
};

#[derive(Debug, Deserialize)]
pub struct IpcRequest {
    pub id: u64,
    pub channel: String,
    pub args: Option<Vec<serde_json::Value>>,
}

#[derive(Debug, Serialize)]
pub struct IpcResponse {
    pub id: u64,
    pub success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

pub struct AppState {
    pub recordings_dir: PathBuf,
    pub selected_source: serde_json::Value,
    pub current_session: Mutex<Option<RecordingSession>>,
    pub prepared_recording_id: Mutex<Option<u64>>,
    pub recorder: Arc<RecorderManager>,
}

impl AppState {
    pub fn new(recordings_dir: PathBuf, helper_path: PathBuf) -> Self {
        let _ = std::fs::create_dir_all(&recordings_dir);
        Self {
            recordings_dir,
            selected_source: serde_json::json!({
                "id": "screen:0:0",
                "name": "Entire Screen (Display 1)",
                "display_id": "0"
            }),
            current_session: Mutex::new(None),
            prepared_recording_id: Mutex::new(None),
            recorder: Arc::new(RecorderManager::new(helper_path)),
        }
    }

    pub fn handle_ipc(&self, raw: &str) -> Option<IpcResponse> {
        let req: IpcRequest = match serde_json::from_str(raw) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("[IPC] Parse error: {} for raw: {}", e, raw);
                return None;
            }
        };

        if req.id == 0 {
            // One-way send event, no response required
            self.handle_send(&req.channel, req.args.as_deref().unwrap_or(&[]));
            return None;
        }

        let res = match self.dispatch(&req.channel, req.args.as_deref().unwrap_or(&[])) {
            Ok(val) => IpcResponse {
                id: req.id,
                success: true,
                result: Some(val),
                error: None,
            },
            Err(err) => IpcResponse {
                id: req.id,
                success: false,
                result: None,
                error: Some(err),
            },
        };

        Some(res)
    }

    fn handle_send(&self, channel: &str, args: &[serde_json::Value]) {
        match channel {
            "console:log" => {
                println!("[Frontend LOG] {:?}", args);
            }
            "console:warn" => {
                println!("[Frontend WARN] {:?}", args);
            }
            "console:error" => {
                eprintln!("[Frontend ERROR] {:?}", args);
            }
            "app-quit" => {
                std::process::exit(0);
            }
            "set-recording-state"
            | "set-has-unsaved-changes"
            | "set-countdown-overlay-value"
            | "set-titlebar-overlay"
            | "ai-edition:set-open-project"
            | "hud-overlay-hide"
            | "hud-overlay-close"
            | "hud-overlay-drag-start"
            | "hud-overlay-drag-to"
            | "hud-overlay-drag-end"
            | "hud-overlay-set-size"
            | "hud-overlay-set-content"
            | "hud-overlay-set-ignore-mouse-events"
            | "hud:setMicrophoneExpanded"
            | "renderer-console" => {
                // UI state tracking
            }
            _ => {
                eprintln!("[IPC] Unhandled send event: {} {:?}", channel, args);
            }
        }
    }

    fn dispatch(&self, channel: &str, args: &[serde_json::Value]) -> Result<serde_json::Value, String> {
        match channel {
            "get-platform" => Ok(serde_json::json!("linux")),

            "get-system-version" => Ok(serde_json::json!("7.3.0-flowork-rust")),

            "get-app-info" => Ok(serde_json::json!({
                "name": "OpenScreen",
                "version": "2.2.2-flowork",
                "platform": "linux",
                "arch": "x64"
            })),

            "can-check-for-updates-now" => Ok(serde_json::json!(false)),
            "check-for-updates" | "get-update-badge" | "show-about" | "apply-update" => {
                Ok(serde_json::Value::Null)
            }

            "get-recording-prefs" => Ok(serde_json::json!({
                "autoStart": false,
                "showCountdown": true,
                "countdownSeconds": 3,
                "aspectRatio": "16:9",
                "resolution": "1080p",
                "fps": 60,
                "frameTheme": "modern",
                "wallpaper": "mesh-dark",
                "cursorTheme": "default",
                "cursorSmoothing": 0.5,
                "cursorMotionBlur": 0.2
            })),
            "set-recording-prefs" => Ok(serde_json::json!({ "success": true })),
            "get-shortcuts" => Ok(serde_json::json!({})),
            "save-shortcuts" | "update-global-shortcut" | "set-locale" | "save-diagnostic" => {
                Ok(serde_json::json!({ "success": true }))
            }

            "permissions" | "permissions:get" => Ok(serde_json::json!({
                "screen": true,
                "microphone": true,
                "camera": true,
                "notifications": true
            })),

            "permissions:request"
            | "permissions:open-settings"
            | "permissions:relaunch"
            | "permissions:close"
            | "request-camera-access"
            | "request-native-mac-cursor-access" => {
                Ok(serde_json::json!(true))
            }

            "get-last-picked-source" => Ok(self.selected_source.clone()),
            "uses-system-source-picker" => Ok(serde_json::json!(false)),
            "open-source-selector" => Ok(serde_json::json!({ "success": true })),
            "get-audio-peaks" => Ok(serde_json::json!([])),
            "prepare-preview-audio-track" => Ok(serde_json::json!({ "success": true })),
            "get-loudness-gain" => Ok(serde_json::json!(1.0)),
            "export:capabilities" => Ok(serde_json::json!({
                "hardwareEncoding": true,
                "codecs": ["h264", "hevc"]
            })),

            "is-native-linux-capture-available" => {
                let available = self.recorder.is_available();
                Ok(serde_json::json!({
                    "success": true,
                    "available": available,
                    "helperPath": self.recorder.helper_path().to_string_lossy(),
                    "backend": "x11"
                }))
            }

            "is-native-mac-capture-available" | "is-native-windows-capture-available" => {
                Ok(serde_json::json!({
                    "success": false,
                    "available": false
                }))
            }

            "get-sources" => {
                // Return primary display as primary source
                Ok(serde_json::json!([
                    {
                        "id": "screen:0:0",
                        "name": "Entire Screen (Display 1)",
                        "display_id": "0",
                        "thumbnail": ""
                    }
                ]))
            }

            "get-selected-source" => Ok(self.selected_source.clone()),

            "select-source" => Ok(serde_json::json!({ "success": true })),

            "get-recordings-dir" => {
                Ok(serde_json::json!(self.recordings_dir.to_string_lossy()))
            }

            "choose-recordings-dir" => {
                Ok(serde_json::json!(self.recordings_dir.to_string_lossy()))
            }

            "reset-recordings-dir" => {
                Ok(serde_json::json!(self.recordings_dir.to_string_lossy()))
            }

            "check-recording-storage" => Ok(serde_json::json!({
                "totalBytes": 1_000_000_000_000u64,
                "freeBytes": 500_000_000_000u64
            })),

            "prepare-native-linux-recording" => {
                let rec_id = args
                    .first()
                    .and_then(|v| v.get("recordingId"))
                    .and_then(|v| v.as_u64())
                    .unwrap_or_else(|| chrono::Utc::now().timestamp_millis() as u64);

                let mut prep = self.prepared_recording_id.lock().unwrap();
                *prep = Some(rec_id);

                Ok(serde_json::json!({
                    "success": true,
                    "recordingId": rec_id,
                    "sourceKind": "display"
                }))
            }

            "cancel-native-linux-prepare" => {
                let mut prep = self.prepared_recording_id.lock().unwrap();
                *prep = None;
                Ok(serde_json::json!({ "success": true }))
            }

            "start-native-linux-recording" => {
                let payload = args.first();
                let rec_id = payload
                    .and_then(|v| v.get("recordingId"))
                    .and_then(|v| v.as_u64())
                    .or_else(|| *self.prepared_recording_id.lock().unwrap())
                    .unwrap_or_else(|| chrono::Utc::now().timestamp_millis() as u64);

                let out_name = format!("recording-{}.mp4", rec_id);
                let out_path = self.recordings_dir.join(out_name);

                let fps = payload
                    .and_then(|v| v.get("video"))
                    .and_then(|v| v.get("fps"))
                    .and_then(|v| v.as_u64())
                    .unwrap_or(30) as u32;

                let bitrate = payload
                    .and_then(|v| v.get("video"))
                    .and_then(|v| v.get("bitrate"))
                    .and_then(|v| v.as_u64())
                    .map(|b| b as u32);

                let sys_audio = payload
                    .and_then(|v| v.get("audio"))
                    .and_then(|v| v.get("system"))
                    .and_then(|v| v.get("enabled"))
                    .and_then(|v| v.as_bool())
                    .unwrap_or(true);

                let mic_audio = payload
                    .and_then(|v| v.get("audio"))
                    .and_then(|v| v.get("microphone"))
                    .and_then(|v| v.get("enabled"))
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);

                // Default Flowork OS desktop resolution
                let width = 2560;
                let height = 1080;

                self.recorder.start_recording(
                    out_path,
                    fps,
                    bitrate,
                    width,
                    height,
                    sys_audio,
                    mic_audio,
                )?;

                Ok(serde_json::json!({ "success": true }))
            }

            "stop-native-linux-recording" => {
                let discard = args
                    .first()
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);

                let session = self.recorder.stop_recording(discard)?;
                let path = session.screen_video_path.clone();

                let mut current = self.current_session.lock().unwrap();
                *current = Some(session.clone());

                Ok(serde_json::json!({
                    "success": true,
                    "path": path,
                    "session": session
                }))
            }

            "read-binary-file" => {
                let path_str = args
                    .first()
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| "Missing file path".to_string())?;

                let path = PathBuf::from(path_str);
                let bytes = std::fs::read(&path)
                    .map_err(|e| format!("Failed to read file {}: {}", path_str, e))?;

                let b64 = base64::engine::general_purpose::STANDARD.encode(&bytes);

                Ok(serde_json::json!({
                    "success": true,
                    "path": path_str,
                    "data": b64
                }))
            }

            "get-readable-file-info" => {
                let path_str = args
                    .first()
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| "Missing file path".to_string())?;

                let path = PathBuf::from(path_str);
                let meta = std::fs::metadata(&path)
                    .map_err(|e| format!("Failed to stat file: {}", e))?;

                Ok(serde_json::json!({
                    "success": true,
                    "path": path_str,
                    "size": meta.len()
                }))
            }

            "get-current-recording-session" => {
                let lock = self.current_session.lock().unwrap();
                match &*lock {
                    Some(s) => Ok(serde_json::to_value(s).unwrap()),
                    None => Ok(serde_json::Value::Null),
                }
            }

            "set-current-recording-session" => {
                if let Some(val) = args.first() {
                    if let Ok(sess) = serde_json::from_value::<RecordingSession>(val.clone()) {
                        let mut lock = self.current_session.lock().unwrap();
                        *lock = Some(sess);
                    }
                }
                Ok(serde_json::json!({ "success": true }))
            }

            "store-recorded-session" => {
                if let Some(val) = args.first() {
                    if let Ok(sess) = serde_json::from_value::<RecordingSession>(val.clone()) {
                        let p = PathBuf::from(&sess.screen_video_path);
                        if let Some(stem) = p.file_stem().and_then(|s| s.to_str()) {
                            let session_path = self.recordings_dir.join(format!("{}.session.json", stem));
                            if let Ok(json_str) = serde_json::to_string_pretty(&sess) {
                                let _ = std::fs::write(session_path, json_str);
                            }
                        }
                        let mut lock = self.current_session.lock().unwrap();
                        *lock = Some(sess);
                    }
                }
                Ok(serde_json::json!({ "success": true }))
            }

            "open-external-url" => {
                if let Some(url) = args.first().and_then(|v| v.as_str()) {
                    let _ = Command::new("xdg-open").arg(url).spawn();
                }
                Ok(serde_json::json!({ "success": true }))
            }

            "switch-to-editor" => Ok(serde_json::json!({ "success": true })),

            "show-countdown-overlay" | "hide-countdown-overlay" => {
                Ok(serde_json::json!({ "success": true }))
            }

            "clipboard:write-text" => {
                if let Some(txt) = args.first().and_then(|v| v.as_str()) {
                    let mut child = Command::new("wl-copy")
                        .stdin(std::process::Stdio::piped())
                        .spawn()
                        .or_else(|_| {
                            Command::new("xclip")
                                .arg("-selection")
                                .arg("clipboard")
                                .stdin(std::process::Stdio::piped())
                                .spawn()
                        });

                    if let Ok(ref mut c) = child {
                        if let Some(ref mut stdin) = c.stdin {
                            use std::io::Write;
                            let _ = stdin.write_all(txt.as_bytes());
                        }
                    }
                }
                Ok(serde_json::json!({ "success": true }))
            }

            "write-export-to-path" => {
                // If export is requested, copy or write source to destination
                if let Some(opts) = args.first() {
                    let src = opts.get("sourcePath").and_then(|v| v.as_str()).unwrap_or("");
                    let dst = opts.get("outputPath").and_then(|v| v.as_str()).unwrap_or("");
                    if !src.is_empty() && !dst.is_empty() {
                        let _ = std::fs::copy(src, dst);
                    }
                }
                Ok(serde_json::json!({ "success": true }))
            }

            _ => {
                eprintln!("[IPC] Unhandled channel: {} with args: {:?}", channel, args);
                Ok(serde_json::json!({ "success": true }))
            }
        }
    }
}
