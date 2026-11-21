use serde::{Deserialize, Serialize};
use std::{
    io::{BufRead, BufReader, Write},
    path::PathBuf,
    process::{Child, ChildStdin, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    thread,
    time::Duration,
};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CursorSample {
    #[serde(rename = "timeMs")]
    pub time_ms: u64,
    pub cx: f64,
    pub cy: f64,
    pub visible: bool,
    #[serde(rename = "interactionType")]
    pub interaction_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CursorRecordingData {
    pub version: u32,
    pub provider: String,
    pub samples: Vec<CursorSample>,
    pub assets: Vec<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecordingSession {
    #[serde(rename = "screenVideoPath")]
    pub screen_video_path: String,
    #[serde(rename = "createdAt")]
    pub created_at: u64,
    #[serde(rename = "cursorCaptureMode")]
    pub cursor_capture_mode: String,
}

pub struct ActiveRecorder {
    child: Option<Child>,
    stdin: Option<ChildStdin>,
    pub output_path: PathBuf,
    pub created_at: u64,
    pub samples: Arc<Mutex<Vec<CursorSample>>>,
    pub running: Arc<AtomicBool>,
}

pub struct RecorderManager {
    helper_path: PathBuf,
    active: Mutex<Option<ActiveRecorder>>,
}

impl RecorderManager {
    pub fn new(helper_path: PathBuf) -> Self {
        Self {
            helper_path,
            active: Mutex::new(None),
        }
    }

    pub fn is_available(&self) -> bool {
        self.helper_path.exists()
    }

    pub fn helper_path(&self) -> &PathBuf {
        &self.helper_path
    }

    #[allow(clippy::too_many_arguments)]
    pub fn start_recording(
        &self,
        output_path: PathBuf,
        fps: u32,
        bitrate: Option<u32>,
        display_width: u32,
        display_height: u32,
        system_audio: bool,
        mic_audio: bool,
    ) -> Result<u64, String> {
        let mut active_lock = self.active.lock().unwrap();
        if active_lock.is_some() {
            return Err("A recording is already in progress".into());
        }

        if let Some(parent) = output_path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }

        let created_at = chrono::Utc::now().timestamp_millis() as u64;

        let config = serde_json::json!({
            "outputPath": output_path.to_string_lossy(),
            "cursorMode": "metadata",
            "video": {
                "fps": fps,
                "bitrate": bitrate.unwrap_or(6_000_000)
            },
            "audio": {
                "system": { "enabled": system_audio },
                "microphone": { "enabled": mic_audio }
            },
            "source": {
                "kind": "display",
                "x": 0,
                "y": 0,
                "width": display_width,
                "height": display_height
            }
        });

        let config_str = config.to_string();

        let mut child = Command::new(&self.helper_path)
            .arg(config_str)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to spawn pipewire helper: {}", e))?;

        let stdin = child.stdin.take();
        let stdout = child.stdout.take();

        let samples = Arc::new(Mutex::new(Vec::with_capacity(1000)));
        let running = Arc::new(AtomicBool::new(true));

        // Reader thread for stdout (parses cursor-sample live)
        if let Some(stdout) = stdout {
            let samples_clone = samples.clone();
            let running_clone = running.clone();

            thread::spawn(move || {
                let reader = BufReader::new(stdout);
                let mut start_time: Option<u64> = None;

                for line in reader.lines().map_while(Result::ok) {
                    if !running_clone.load(Ordering::Relaxed) {
                        break;
                    }
                    if line.trim().is_empty() {
                        continue;
                    }

                    if let Ok(val) = serde_json::from_str::<serde_json::Value>(&line) {
                        let event = val.get("event").and_then(|v| v.as_str()).unwrap_or("");

                        if event == "capture-started" {
                            if let Some(ts) = val.get("timestampMs").and_then(|v| v.as_u64()) {
                                start_time = Some(ts);
                            }
                        } else if event == "cursor-sample" {
                            let ts = val
                                .get("timestampMs")
                                .and_then(|v| v.as_u64())
                                .unwrap_or(0);
                            let origin = start_time.unwrap_or(ts);
                            let time_ms = ts.saturating_sub(origin);

                            let x = val.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
                            let y = val.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
                            let w = val
                                .get("width")
                                .and_then(|v| v.as_f64())
                                .unwrap_or(1.0)
                                .max(1.0);
                            let h = val
                                .get("height")
                                .and_then(|v| v.as_f64())
                                .unwrap_or(1.0)
                                .max(1.0);

                            let cx = (x / w).clamp(0.0, 1.0);
                            let cy = (y / h).clamp(0.0, 1.0);
                            let visible =
                                val.get("visible").and_then(|v| v.as_bool()).unwrap_or(true);
                            let interaction_type = val
                                .get("interactionType")
                                .and_then(|v| v.as_str())
                                .unwrap_or("move")
                                .to_string();

                            let sample = CursorSample {
                                time_ms,
                                cx,
                                cy,
                                visible,
                                interaction_type,
                            };

                            let mut lock = samples_clone.lock().unwrap();
                            lock.push(sample);
                        }
                    }
                }
            });
        }

        *active_lock = Some(ActiveRecorder {
            child: Some(child),
            stdin,
            output_path,
            created_at,
            samples,
            running,
        });

        Ok(created_at)
    }

    pub fn stop_recording(&self, discard: bool) -> Result<RecordingSession, String> {
        let mut active_lock = self.active.lock().unwrap();
        let mut recorder = active_lock
            .take()
            .ok_or_else(|| "No active recording to stop".to_string())?;

        recorder.running.store(false, Ordering::Relaxed);

        // Send stop command to stdin
        if let Some(mut stdin) = recorder.stdin.take() {
            let _ = writeln!(stdin, "stop");
            let _ = stdin.flush();
        }

        // Wait up to 5s for child to finish encoding
        if let Some(mut child) = recorder.child.take() {
            let start_wait = std::time::Instant::now();
            let mut exited = false;
            while start_wait.elapsed() < Duration::from_secs(5) {
                if let Ok(Some(_)) = child.try_wait() {
                    exited = true;
                    break;
                }
                thread::sleep(Duration::from_millis(100));
            }
            if !exited {
                let _ = child.kill();
            }
        }

        let output_str = recorder.output_path.to_string_lossy().to_string();

        if discard {
            let _ = std::fs::remove_file(&recorder.output_path);
            let cursor_file = format!("{}.cursor.json", output_str);
            let _ = std::fs::remove_file(cursor_file);
            return Err("Recording discarded".to_string());
        }

        // Write cursor.json
        let samples = {
            let lock = recorder.samples.lock().unwrap();
            lock.clone()
        };

        let cursor_data = CursorRecordingData {
            version: 2,
            provider: "native".into(),
            samples,
            assets: Vec::new(),
        };

        let cursor_path = format!("{}.cursor.json", output_str);
        if let Ok(cursor_json) = serde_json::to_string_pretty(&cursor_data) {
            let _ = std::fs::write(&cursor_path, cursor_json);
        }

        // Write session JSON
        let session = RecordingSession {
            screen_video_path: output_str.clone(),
            created_at: recorder.created_at,
            cursor_capture_mode: "editable-overlay".into(),
        };

        let file_stem = recorder
            .output_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("recording");

        if let Some(parent) = recorder.output_path.parent() {
            let session_path = parent.join(format!("{}.session.json", file_stem));
            if let Ok(session_json) = serde_json::to_string_pretty(&session) {
                let _ = std::fs::write(session_path, session_json);
            }
        }

        Ok(session)
    }
}
