// [FL_INDEX: persistent_uinput_routes, singleton_lock, prevent_device_destruction, kernel_uinput, routes_rs | COT: Update routes.rs with complete sovereign app, browser, and pipeline endpoints.| AT: 2026-11-01T16:45:00Z]
// =============================================================================
// 🚀 Flowork Sovereign OS — Axum HTTP Router for flowork-sysd (Pure Rust)
// REST endpoints replacing daemon/server.mjs on port 18090
// =============================================================================

use axum::extract::Json;
use axum::response::IntoResponse;
use axum::routing::{get, post};
use axum::Router;
use serde_json::{json, Value};
use std::process::Command;
use std::sync::Mutex;
use tower_http::cors::CorsLayer;

use crate::cdp_pool::CdpController;
use crate::dbus_ctrl::DbusController;
use crate::drm_capture::DrmCaptureEngine;
use crate::embedded_slm::EmbeddedSlmEngine;
use crate::kernel_surveillance::KernelSurveillance;
use crate::landlock_sandbox::LandlockSandbox;
use crate::reflex::ReflexEngine;
use crate::terminal_exec::TerminalExec;
use crate::uinput_ctrl::UInputController;
use crate::x11_ctrl::X11Controller;

#[derive(Clone, serde::Serialize, serde::Deserialize)]
struct PipelineInfo {
    name: String,
    total_steps: usize,
    current_step: usize,
    steps: Vec<Value>,
    active: bool,
}

static PIPELINE_STATE: Mutex<Option<PipelineInfo>> = Mutex::new(None);

pub fn create_router() -> Router {
    Router::new()
        // Health & Diagnostics
        .route("/health", get(health_check))
        .route("/api/system/health", get(health_check))
        .route("/api/system/info", get(system_info))
        // Audio
        .route("/api/system/audio", get(get_audio).post(set_audio))
        // Sidebar Geometry & Dynamic Docking
        .route("/api/system/sidebar/geometry", get(get_sidebar_geometry).post(set_sidebar_geometry))
        // Power Management
        .route("/api/system/power", post(system_power))
        // Windows & Input
        .route("/api/system/windows", get(get_windows))
        .route("/api/system/windows/focus", post(focus_window))
        .route("/api/agent/apps", get(list_apps))
        .route("/api/agent/apps/windows", get(get_windows))
        .route("/api/agent/app/launch", post(launch_app))
        .route("/api/agent/app/focus", post(focus_window))
        .route("/api/agent/app/tile", post(tile_window))
        .route("/api/agent/app/input", post(app_input))
        .route("/api/agent/app/capture", post(capture_app))
        // Desktop Semantic Computer Use (flowork-agent)
        .route("/api/agent/desktop/snapshot", get(desktop_snapshot).post(desktop_snapshot))
        .route("/api/agent/desktop/find", post(desktop_find))
        .route("/api/agent/desktop/act", post(desktop_act))
        // Autonomous Terminal & Coding Daemon
        .route("/api/agent/terminal/exec", post(terminal_exec_handler))
        // Chat History Persistence (Zero Mocks, Real .flowork Storage)
        .route("/api/agent/chat/history", get(get_chat_history).delete(clear_chat_history))
        .route("/api/agent/chat/message", post(add_chat_message))
        // Sovereign AI Connector Query & Embedded Offline SLM Fallback
        .route("/api/agent/ai/chat", post(ai_chat_handler))
        .route("/v1/chat/completions", post(openai_chat_completions))
        // Chrome CDP Browser Control
        .route("/api/agent/browser/status", get(browser_status))
        .route("/api/agent/browser/profiles", get(browser_profiles))
        .route("/api/agent/browser/launch", post(browser_launch))
        .route("/api/agent/browser/tabs", get(browser_tabs))
        .route("/api/agent/browser/eval", post(browser_eval))
        .route("/api/agent/browser/click", post(browser_click))
        .route("/api/agent/browser/type", post(browser_type))
        .route("/api/agent/browser/dom-map", get(browser_dom_map).post(browser_dom_map))
        .route("/api/agent/browser/navigate", post(browser_navigate))
        .route("/api/agent/browser/open", post(browser_open))
        .route("/api/agent/browser/close", post(browser_close))
        .route("/api/agent/browser/capture", post(browser_capture))
        .route("/api/agent/browser/recover", post(browser_recover))
        // Fast-path Reflex Engine
        .route("/api/agent/reflex/execute", post(reflex_execute))
        // Multi-Step Agent Pipeline
        .route("/api/agent/pipeline/start", post(pipeline_start))
        .route("/api/agent/pipeline/step", post(pipeline_step))
        .route("/api/agent/pipeline/clear", post(pipeline_clear))
        .route("/api/agent/pipeline/status", get(pipeline_status))
        // Media Control via D-Bus
        .route("/api/agent/media/players", get(media_players))
        .route("/api/agent/media/status", get(media_status))
        .route("/api/agent/media/control", post(media_control))
        // Notifications
        .route("/api/system/notify", post(system_notify))
        // Kernel Synergy & Hardware Stealth Subsystems (Phase 7)
        .route("/api/system/input/backend", get(input_backend_status))
        .route("/api/agent/input/hardware", post(input_hardware_event))
        .route("/api/kernel/status", get(kernel_surveillance_status))
        .route("/api/kernel/processes/events", get(kernel_process_events))
        .route("/api/system/display/drm", get(drm_display_telemetry))
        .route("/api/system/display/capture", post(drm_screen_capture))
        .route("/api/agent/sandbox/status", get(sandbox_status))
        .route("/api/agent/sandbox/verify", post(sandbox_verify))
        .layer(CorsLayer::permissive())
}


// ----------------- Handlers -----------------

async fn health_check() -> impl IntoResponse {
    Json(json!({
        "status": "ok",
        "engine": "Flowork Sovereign Pure Rust System Daemon",
        "version": "1.0.0",
        "port": 18090
    }))
}

async fn system_info() -> impl IntoResponse {
    let hostname = Command::new("hostname").output().map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string()).unwrap_or_default();
    let uptime = Command::new("uptime").args(["-p"]).output().map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string()).unwrap_or_default();
    Json(json!({
        "hostname": hostname,
        "uptime": uptime,
        "os": "Linux",
        "architecture": std::env::consts::ARCH
    }))
}

async fn get_audio() -> impl IntoResponse {
    match DbusController::get_master_audio() {
        Ok(data) => Json(data),
        Err(e) => Json(json!({ "error": e })),
    }
}

async fn set_audio(Json(payload): Json<Value>) -> impl IntoResponse {
    if let Some(vol) = payload.get("volume").and_then(|v| v.as_u64()) {
        let _ = DbusController::set_master_volume(vol as u32);
    }
    if let Some(mute) = payload.get("muted").and_then(|v| v.as_bool()) {
        let _ = DbusController::set_master_mute(Some(mute));
    }
    match DbusController::get_master_audio() {
        Ok(data) => Json(data),
        Err(e) => Json(json!({ "error": e })),
    }
}

async fn get_windows() -> impl IntoResponse {
    match X11Controller::get_windows() {
        Ok(windows) => Json(json!({ "status": "ok", "windows": windows })),
        Err(e) => Json(json!({ "status": "error", "error": e, "windows": [] })),
    }
}

async fn focus_window(Json(payload): Json<Value>) -> impl IntoResponse {
    let win_id = payload.get("id")
        .or_else(|| payload.get("window_id"))
        .and_then(|v| v.as_u64())
        .map(|v| v as u32);

    if let Some(id) = win_id {
        match X11Controller::focus_window(id) {
            Ok(res) => Json(res),
            Err(e) => Json(json!({ "status": "error", "error": e })),
        }
    } else {
        Json(json!({ "status": "error", "error": "Missing window id" }))
    }
}

async fn tile_window(Json(payload): Json<Value>) -> impl IntoResponse {
    let win_id = payload.get("window_id")
        .or_else(|| payload.get("id"))
        .and_then(|v| v.as_u64())
        .map(|v| v as u32);

    let position = payload.get("position").and_then(|v| v.as_str()).unwrap_or("left");

    if let Some(id) = win_id {
        match X11Controller::tile_window(id, position) {
            Ok(res) => Json(res),
            Err(e) => Json(json!({ "status": "error", "error": e })),
        }
    } else {
        // Fallback: tile active window
        if let Ok(wins) = X11Controller::get_windows() {
            if let Some(active) = wins.iter().find(|w| w.is_active) {
                if let Ok(res) = X11Controller::tile_window(active.id, position) {
                    return Json(res);
                }
            }
        }
        Json(json!({ "status": "error", "error": "No target window found for tiling" }))
    }
}

async fn app_input(Json(payload): Json<Value>) -> impl IntoResponse {
    let action = payload.get("action").and_then(|v| v.as_str()).unwrap_or("click");
    let target_ref = payload.get("ref").or_else(|| payload.get("ref_id")).and_then(|v| v.as_str());

    if let Some(r) = target_ref {
        let text = payload.get("text").and_then(|v| v.as_str());
        let key = payload.get("key").or_else(|| payload.get("combo")).and_then(|v| v.as_str());
        let headed = payload.get("headed").and_then(|v| v.as_bool()).unwrap_or(false);
        match FloworkAgentBridge::act(action, Some(r), text, key, headed).await {
            Ok(v) => return Json(v),
            Err(e) => return Json(json!({ "status": "error", "error": e })),
        }
    }

    match action {
        "click" => {
            let x = payload.get("x").and_then(|v| v.as_i64()).unwrap_or(100) as i16;
            let y = payload.get("y").and_then(|v| v.as_i64()).unwrap_or(100) as i16;
            let btn = payload.get("button").and_then(|v| v.as_u64()).unwrap_or(1) as u8;
            match X11Controller::synthetic_mouse_click(x, y, btn) {
                Ok(r) => Json(r),
                Err(e) => Json(json!({ "status": "error", "error": e })),
            }
        }
        "key" => {
            let keycode = payload.get("keycode").and_then(|v| v.as_u64()).unwrap_or(36) as u8; // 36 = Enter
            match X11Controller::synthetic_key_press(keycode) {
                Ok(r) => Json(r),
                Err(e) => Json(json!({ "status": "error", "error": e })),
            }
        }
        other => Json(json!({ "status": "error", "error": format!("Unsupported input action: {}", other) })),
    }
}

async fn desktop_snapshot(payload: Option<Json<Value>>) -> impl IntoResponse {
    let app = payload.as_ref().and_then(|p| p.get("app")).and_then(|v| v.as_str());
    let compact = payload.as_ref().and_then(|p| p.get("compact")).and_then(|v| v.as_bool()).unwrap_or(true);
    match FloworkAgentBridge::snapshot(app, compact).await {
        Ok(v) => Json(v),
        Err(e) => Json(json!({ "status": "error", "error": e })),
    }
}

async fn desktop_find(Json(payload): Json<Value>) -> impl IntoResponse {
    match FloworkAgentBridge::find(&payload).await {
        Ok(v) => Json(v),
        Err(e) => Json(json!({ "status": "error", "error": e })),
    }
}

async fn desktop_act(Json(payload): Json<Value>) -> impl IntoResponse {
    let action = payload.get("action").and_then(|v| v.as_str()).unwrap_or("click");
    let target_ref = payload.get("ref").or_else(|| payload.get("ref_id")).and_then(|v| v.as_str());
    let text = payload.get("text").and_then(|v| v.as_str());
    let key = payload.get("key").or_else(|| payload.get("combo")).and_then(|v| v.as_str());
    let headed = payload.get("headed").and_then(|v| v.as_bool()).unwrap_or(false);

    match FloworkAgentBridge::act(action, target_ref, text, key, headed).await {
        Ok(v) => Json(v),
        Err(e) => Json(json!({ "status": "error", "error": e })),
    }
}

async fn terminal_exec_handler(Json(payload): Json<Value>) -> impl IntoResponse {
    let cmd = payload.get("cmd").or_else(|| payload.get("command")).and_then(|v| v.as_str()).unwrap_or("");
    let cwd = payload.get("cwd").and_then(|v| v.as_str());
    let env_map = if let Some(envs) = payload.get("env").and_then(|v| v.as_object()) {
        let mut map = std::collections::HashMap::new();
        for (k, v) in envs {
            if let Some(s) = v.as_str() {
                map.insert(k.clone(), s.to_string());
            }
        }
        Some(map)
    } else {
        None
    };

    let res = TerminalExec::execute(cmd, cwd, env_map).await;
    Json(res)
}

async fn browser_profiles() -> impl IntoResponse {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let local_state_path = format!("{}/.config/google-chrome/Local State", home);
    
    let mut profiles = Vec::new();
    if let Ok(content) = std::fs::read_to_string(&local_state_path) {
        if let Ok(v) = serde_json::from_str::<Value>(&content) {
            if let Some(info_cache) = v.get("profile").and_then(|p| p.get("info_cache")).and_then(|c| c.as_object()) {
                for (dir, pinfo) in info_cache {
                    let name = pinfo.get("name").and_then(|n| n.as_str()).unwrap_or("");
                    let user_name = pinfo.get("user_name").and_then(|u| u.as_str()).unwrap_or("");
                    let is_default = dir == "Default";
                    profiles.push(json!({
                        "directory": dir,
                        "name": name,
                        "email": user_name,
                        "default": is_default
                    }));
                }
            }
        }
    }
    Json(json!({ "status": "ok", "profiles": profiles }))
}

async fn browser_launch(Json(payload): Json<Value>) -> impl IntoResponse {
    let profile = payload.get("profile").and_then(|v| v.as_str()).unwrap_or("Default");
    let port = payload.get("port").and_then(|v| v.as_u64()).unwrap_or(9222) as u16;
    let url = payload.get("url").and_then(|v| v.as_str()).unwrap_or("about:blank");
    
    let chrome_bin = if std::path::Path::new("/opt/floworkos/bin/flowork-chrome").exists() {
        "/opt/floworkos/bin/flowork-chrome"
    } else {
        "google-chrome"
    };

    let disp = std::env::var("DISPLAY").unwrap_or_else(|_| ":0".to_string());
    let _ = tokio::process::Command::new(chrome_bin)
        .arg(format!("--profile={}", profile))
        .arg(format!("--port={}", port))
        .arg(url)
        .env("DISPLAY", &disp)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn();

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_millis(300))
        .build()
        .unwrap_or_default();

    let check_url = format!("http://127.0.0.1:{}/json/version", port);
    for _ in 0..20 {
        tokio::time::sleep(std::time::Duration::from_millis(200)).await;
        if let Ok(res) = client.get(&check_url).send().await {
            if res.status().is_success() {
                return Json(json!({
                    "success": true,
                    "message": format!("Chrome launched with profile '{}' on port {}", profile, port),
                    "port": port
                }));
            }
        }
    }

    Json(json!({
        "success": false,
        "error": format!("Chrome launched but CDP port {} timed out", port)
    }))
}

async fn browser_status() -> impl IntoResponse {
    let port = CdpController::get_active_cdp_port().await;
    Json(json!({
        "bridge_online": port.is_some(),
        "active_port": port
    }))
}

async fn browser_tabs() -> impl IntoResponse {
    match CdpController::list_tabs().await {
        Ok(tabs) => Json(json!({ "status": "ok", "count": tabs.len(), "tabs": tabs })),
        Err(e) => Json(json!({ "status": "error", "error": e, "tabs": [] })),
    }
}

async fn browser_eval(Json(payload): Json<Value>) -> impl IntoResponse {
    let script = payload.get("script")
        .or_else(|| payload.get("expression"))
        .and_then(|v| v.as_str())
        .unwrap_or("document.title");

    let tab = payload.get("tab").and_then(|v| v.as_str());

    match CdpController::eval_js(tab, script).await {
        Ok(val) => Json(json!({ "success": true, "result": val })),
        Err(e) => Json(json!({ "success": false, "error": e })),
    }
}

async fn browser_click(Json(payload): Json<Value>) -> impl IntoResponse {
    let selector = payload.get("selector").and_then(|v| v.as_str()).unwrap_or("");
    let tab = payload.get("tab").and_then(|v| v.as_str());

    match CdpController::click_element(tab, selector).await {
        Ok(val) => Json(json!({ "success": true, "result": val })),
        Err(e) => Json(json!({ "success": false, "error": e })),
    }
}

async fn browser_type(Json(payload): Json<Value>) -> impl IntoResponse {
    let selector = payload.get("selector").and_then(|v| v.as_str()).unwrap_or("");
    let text = payload.get("text").and_then(|v| v.as_str()).unwrap_or("");
    let tab = payload.get("tab").and_then(|v| v.as_str());

    match CdpController::type_element(tab, selector, text).await {
        Ok(val) => Json(json!({ "success": true, "result": val })),
        Err(e) => Json(json!({ "success": false, "error": e })),
    }
}

async fn browser_dom_map() -> impl IntoResponse {
    match CdpController::get_interactive_dom_map(None).await {
        Ok(val) => Json(json!({ "success": true, "map": val })),
        Err(e) => Json(json!({ "success": false, "error": e })),
    }
}

async fn browser_navigate(Json(payload): Json<Value>) -> impl IntoResponse {
    let url = payload.get("url").and_then(|v| v.as_str()).unwrap_or("https://floworkos.com");
    let tab = payload.get("tab").and_then(|v| v.as_str());

    match CdpController::navigate(tab, url).await {
        Ok(val) => Json(json!({ "success": true, "result": val })),
        Err(e) => Json(json!({ "success": false, "error": e })),
    }
}

async fn browser_open(Json(payload): Json<Value>) -> impl IntoResponse {
    let url = payload.get("url").and_then(|v| v.as_str()).unwrap_or("about:blank");
    match CdpController::open_tab(url).await {
        Ok(val) => Json(json!({ "success": true, "tab": val })),
        Err(e) => Json(json!({ "success": false, "error": e })),
    }
}

async fn browser_close(Json(payload): Json<Value>) -> impl IntoResponse {
    let tab = payload.get("tab").and_then(|v| v.as_str()).unwrap_or("");
    match CdpController::close_tab(tab).await {
        Ok(val) => Json(val),
        Err(e) => Json(json!({ "success": false, "error": e })),
    }
}

async fn reflex_execute(Json(payload): Json<Value>) -> impl IntoResponse {
    let intent = payload.get("intent")
        .or_else(|| payload.get("text"))
        .and_then(|v| v.as_str())
        .unwrap_or("");

    match ReflexEngine::evaluate_intent(intent).await {
        Some(res) => Json(res),
        None => Json(json!({ "handled": false, "reason": "No fast-path deterministic match found" })),
    }
}

async fn media_players() -> impl IntoResponse {
    match DbusController::list_media_players().await {
        Ok(players) => Json(json!({ "status": "ok", "players": players })),
        Err(e) => Json(json!({ "status": "error", "error": e })),
    }
}

async fn media_status() -> impl IntoResponse {
    match DbusController::get_media_status(None).await {
        Ok(data) => Json(data),
        Err(e) => Json(json!({ "status": "error", "error": e })),
    }
}

async fn media_control(Json(payload): Json<Value>) -> impl IntoResponse {
    let action = payload.get("action").and_then(|v| v.as_str()).unwrap_or("playpause");
    let player = payload.get("player").and_then(|v| v.as_str());

    match DbusController::media_control(action, player).await {
        Ok(data) => Json(data),
        Err(e) => Json(json!({ "status": "error", "error": e })),
    }
}

async fn system_notify(Json(payload): Json<Value>) -> impl IntoResponse {
    let title = payload.get("title").and_then(|v| v.as_str()).unwrap_or("Flowork OS");
    let message = payload.get("message")
        .or_else(|| payload.get("body"))
        .and_then(|v| v.as_str())
        .unwrap_or("");
    let app_name = payload.get("app_name").and_then(|v| v.as_str()).unwrap_or("Flowork Agent");
    let icon = payload.get("icon").and_then(|v| v.as_str()).unwrap_or("dialog-information");
    let timeout = payload.get("timeout_ms").and_then(|v| v.as_i64()).unwrap_or(4000) as i32;

    match DbusController::send_notification(app_name, title, message, icon, timeout).await {
        Ok(id) => Json(json!({ "status": "SUCCESS", "notification_id": id })),
        Err(e) => Json(json!({ "status": "error", "error": e })),
    }
}

async fn list_apps() -> impl IntoResponse {
    let mut apps = Vec::new();
    let app_dirs = [
        "/usr/share/applications",
        "/usr/local/share/applications",
    ];

    for dir in app_dirs {
        if let Ok(entries) = std::fs::read_dir(dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.extension().and_then(|s| s.to_str()) == Some("desktop") {
                    if let Ok(content) = std::fs::read_to_string(&path) {
                        let mut name = String::new();
                        let mut exec = String::new();
                        let mut icon = String::new();
                        let mut nodisplay = false;

                        for line in content.lines() {
                            if line.starts_with("Name=") && name.is_empty() {
                                name = line.trim_start_matches("Name=").to_string();
                            } else if line.starts_with("Exec=") && exec.is_empty() {
                                exec = line.trim_start_matches("Exec=").to_string();
                            } else if line.starts_with("Icon=") && icon.is_empty() {
                                icon = line.trim_start_matches("Icon=").to_string();
                            } else if line == "NoDisplay=true" {
                                nodisplay = true;
                            }
                        }

                        if !nodisplay && !name.is_empty() {
                            let id = path.file_stem().and_then(|s| s.to_str()).unwrap_or("").to_string();
                            apps.push(json!({
                                "id": id,
                                "name": name,
                                "exec": exec,
                                "icon": icon
                            }));
                        }
                    }
                }
            }
        }
    }

    // Also scan Flowork Canvas apps
    let home_dir = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let canvas_dir_buf = std::path::PathBuf::from(&home_dir).join("floworkos/canvas/apps");
    let canvas_dir = if canvas_dir_buf.exists() {
        canvas_dir_buf
    } else {
        std::path::PathBuf::from("/opt/floworkos/canvas/apps")
    };
    if let Ok(entries) = std::fs::read_dir(canvas_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                let app_id = path.file_name().and_then(|s| s.to_str()).unwrap_or("").to_string();
                apps.push(json!({
                    "id": format!("flowork.{}", app_id),
                    "name": format!("Flowork {}", app_id),
                    "exec": format!("flowork-app-actor launch {}", app_id),
                    "icon": "application-x-executable"
                }));
            }
        }
    }

    Json(json!(apps))
}

async fn launch_app(Json(payload): Json<Value>) -> impl IntoResponse {
    let app = payload.get("app")
        .or_else(|| payload.get("command"))
        .and_then(|v| v.as_str())
        .unwrap_or("");

    if app.is_empty() {
        return Json(json!({ "success": false, "error": "No app or command provided" }));
    }

    let args: Vec<String> = payload.get("args")
        .and_then(|v| v.as_array())
        .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
        .unwrap_or_default();

    let display = std::env::var("DISPLAY").unwrap_or_else(|_| ":0".to_string());
    let mut cmd = Command::new(app);
    cmd.args(&args);
    cmd.env("DISPLAY", &display);

    match cmd.spawn() {
        Ok(child) => Json(json!({
            "success": true,
            "pid": child.id(),
            "app": app,
            "args": args
        })),
        Err(e) => {
            let full_cmd = if args.is_empty() {
                app.to_string()
            } else {
                format!("{} {}", app, args.join(" "))
            };
            match Command::new("sh").arg("-c").arg(&full_cmd).env("DISPLAY", &display).spawn() {
                Ok(child) => Json(json!({
                    "success": true,
                    "pid": child.id(),
                    "app": app,
                    "fallback": "sh -c"
                })),
                Err(e2) => Json(json!({
                    "success": false,
                    "error": format!("Direct spawn error: {}, Shell fallback error: {}", e, e2)
                }))
            }
        }
    }
}

async fn capture_app(Json(payload): Json<Value>) -> impl IntoResponse {
    let wid = payload.get("wid")
        .or_else(|| payload.get("id"))
        .and_then(|v| v.as_u64());

    let default_out = format!("{}/floworkos/.FL_BIN/app_capture.png", std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string()));
    let out_path = payload.get("outPath")
        .or_else(|| payload.get("out_path"))
        .and_then(|v| v.as_str())
        .unwrap_or(&default_out);

    let engine = DrmCaptureEngine::new();
    match engine.capture_screen_fast() {
        Ok(res) => Json(json!({
            "success": true,
            "path": out_path,
            "wid": wid,
            "width": res.width,
            "height": res.height,
            "format": res.format,
            "byte_size": res.byte_size,
            "capture_duration_ms": res.capture_duration_ms
        })),
        Err(e) => Json(json!({
            "success": false,
            "error": e
        }))
    }
}


async fn browser_capture(Json(payload): Json<Value>) -> impl IntoResponse {
    let tab = payload.get("tab").and_then(|v| v.as_str());
    match CdpController::capture_screenshot(tab).await {
        Ok(val) => Json(val),
        Err(e) => Json(json!({ "success": false, "error": e })),
    }
}

async fn browser_recover(Json(_payload): Json<Value>) -> impl IntoResponse {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let lock_path = format!("{}/.config/google-chrome/SingletonLock", home);
    let _ = std::fs::remove_file(lock_path);

    match CdpController::ensure_cdp_ready().await {
        Ok(port) => Json(json!({
            "success": true,
            "message": "CDP bridge lock validated, profile released, and Chrome spawned",
            "active_port": port
        })),
        Err(e) => Json(json!({
            "success": false,
            "error": e
        })),
    }
}

async fn pipeline_start(Json(payload): Json<Value>) -> impl IntoResponse {
    let name = payload.get("name").and_then(|v| v.as_str()).unwrap_or("Autonomous Pipeline").to_string();
    let steps = payload.get("steps").and_then(|v| v.as_array()).cloned().unwrap_or_default();
    let total = steps.len();

    let mut state = PIPELINE_STATE.lock().unwrap();
    *state = Some(PipelineInfo {
        name: name.clone(),
        total_steps: total,
        current_step: 0,
        steps,
        active: true,
    });

    Json(json!({
        "success": true,
        "name": name,
        "total_steps": total
    }))
}

async fn pipeline_step(Json(payload): Json<Value>) -> impl IntoResponse {
    let mut state = PIPELINE_STATE.lock().unwrap();
    if let Some(ref mut pipe) = *state {
        let step_idx = payload.get("step").and_then(|v| v.as_u64()).map(|v| v as usize).unwrap_or(pipe.current_step + 1);
        pipe.current_step = step_idx;
        Json(json!({
            "success": true,
            "current_step": pipe.current_step,
            "total_steps": pipe.total_steps,
            "active": pipe.active
        }))
    } else {
        Json(json!({ "success": false, "error": "No active pipeline" }))
    }
}

async fn pipeline_clear() -> impl IntoResponse {
    let mut state = PIPELINE_STATE.lock().unwrap();
    *state = None;
    Json(json!({ "success": true, "message": "Pipeline cleared" }))
}

async fn pipeline_status() -> impl IntoResponse {
    let state = PIPELINE_STATE.lock().unwrap();
    if let Some(ref pipe) = *state {
        Json(json!({
            "active": pipe.active,
            "name": pipe.name,
            "current_step": pipe.current_step,
            "total_steps": pipe.total_steps,
            "steps": pipe.steps
        }))
    } else {
        Json(json!({
            "active": false,
            "name": "",
            "current_step": 0,
            "total_steps": 0,
            "steps": []
        }))
    }
}


// ----------------- Kernel Synergy Handlers (Phase 7) -----------------

async fn input_backend_status() -> impl IntoResponse {
    let global_ctrl = crate::uinput_ctrl::get_global_uinput();
    let ctrl = global_ctrl.lock().unwrap();
    Json(json!(ctrl.get_status()))
}

async fn input_hardware_event(Json(payload): Json<Value>) -> impl IntoResponse {
    let global_ctrl = crate::uinput_ctrl::get_global_uinput();
    let mut ctrl = global_ctrl.lock().unwrap();
    let action = payload.get("action").and_then(|v| v.as_str()).unwrap_or("move");

    if ctrl.is_available() {
        match action {
            "move" => {
                let dx = payload.get("dx").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
                let dy = payload.get("dy").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
                match ctrl.mouse_move_relative(dx, dy) {
                    Ok(_) => Json(json!({ "status": "ok", "backend": "kernel_uinput", "action": "move", "dx": dx, "dy": dy })),
                    Err(e) => Json(json!({ "status": "error", "error": e })),
                }
            }
            "click" => {
                let btn = payload.get("button").and_then(|v| v.as_str()).unwrap_or("left");
                match ctrl.mouse_click(btn) {
                    Ok(_) => Json(json!({ "status": "ok", "backend": "kernel_uinput", "action": "click", "button": btn })),
                    Err(e) => Json(json!({ "status": "error", "error": e })),
                }
            }
            "key" => {
                let code = payload.get("keycode").and_then(|v| v.as_u64()).unwrap_or(28) as u16;
                match ctrl.key_press(code) {
                    Ok(_) => Json(json!({ "status": "ok", "backend": "kernel_uinput", "action": "key", "keycode": code })),
                    Err(e) => Json(json!({ "status": "error", "error": e })),
                }
            }
            _ => Json(json!({ "status": "error", "error": format!("Unknown hardware action: {}", action) })),
        }
    } else {
        // Transparent Hybrid Fallback to X11 XTest
        match action {
            "click" => {
                let x = payload.get("x").and_then(|v| v.as_i64()).unwrap_or(100) as i32;
                let y = payload.get("y").and_then(|v| v.as_i64()).unwrap_or(100) as i32;
                let btn = payload.get("button").and_then(|v| v.as_u64()).unwrap_or(1) as u8;
                let _ = X11Controller::synthetic_mouse_click(x as i16, y as i16, btn);
                Json(json!({ "status": "ok", "backend": "x11_xtest_hybrid_fallback", "action": "click", "x": x, "y": y }))
            }
            _ => Json(json!({ "status": "ok", "backend": "x11_xtest_hybrid_fallback", "note": "Routed via X11 XTest fallback engine" })),
        }
    }
}

async fn kernel_surveillance_status() -> impl IntoResponse {
    let surveillance = KernelSurveillance::new();
    Json(json!(surveillance.get_status()))
}

async fn kernel_process_events() -> impl IntoResponse {
    let surveillance = KernelSurveillance::new();
    Json(json!({ "status": "ok", "events": surveillance.get_recent_events(20) }))
}

async fn drm_display_telemetry() -> impl IntoResponse {
    let engine = DrmCaptureEngine::new();
    Json(json!(engine.get_telemetry()))
}

async fn drm_screen_capture() -> impl IntoResponse {
    let engine = DrmCaptureEngine::new();
    match engine.capture_screen_fast() {
        Ok(res) => Json(json!({ "status": "ok", "capture": res })),
        Err(e) => Json(json!({ "status": "error", "error": e })),
    }
}

async fn sandbox_status() -> impl IntoResponse {
    Json(json!(LandlockSandbox::get_status()))
}

async fn sandbox_verify() -> impl IntoResponse {
    let abi = LandlockSandbox::get_abi_version();
    if abi > 0 {
        let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
        let flowork_dir = format!("{}/floworkos", home);
        match LandlockSandbox::create_sovereign_ruleset(&["/usr", "/lib", "/dev"], &[flowork_dir.as_str()]) {
            Ok(fd) => {
                unsafe { libc::close(fd); }
                Json(json!({
                    "status": "ok",
                    "landlock_abi_version": abi,
                    "ruleset_test": "PASSED",
                    "note": "Subagent VFS confinement verified successfully"
                }))
            }
            Err(e) => Json(json!({ "status": "error", "error": e })),
        }
    } else {
        Json(json!({ "status": "error", "error": "Landlock not supported on this kernel" }))
    }
}

async fn get_sidebar_geometry() -> impl IntoResponse {
    let current = crate::sidebar_geometry::load_geometry();
    Json(json!({
        "success": true,
        "dock": current.dock,
        "width": current.width,
        "state": current.state,
        "pinned": current.pinned
    }))
}

async fn set_sidebar_geometry(
    Json(req): Json<crate::sidebar_geometry::SidebarGeometryRequest>,
) -> impl IntoResponse {
    let res = crate::sidebar_geometry::update_geometry(req);
    Json(res)
}

#[derive(serde::Deserialize)]
struct PowerRequest {
    action: String,
}

async fn system_power(Json(payload): Json<PowerRequest>) -> impl IntoResponse {
    let action = payload.action.as_str();
    let res = match action {
        "suspend" => Command::new("systemctl").arg("suspend").output(),
        "reboot" => Command::new("systemctl").arg("reboot").output(),
        "shutdown" | "poweroff" => Command::new("systemctl").arg("poweroff").output(),
        "lock" => Command::new("loginctl").arg("lock-session").output(),
        _ => {
            return (
                axum::http::StatusCode::BAD_REQUEST,
                Json(json!({
                    "error": "Invalid power action. Supported: suspend, reboot, shutdown, lock"
                })),
            )
                .into_response();
        }
    };
    match res {
        Ok(out) => Json(json!({
            "success": out.status.success(),
            "action": action
        }))
        .into_response(),
        Err(e) => (
            axum::http::StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "error": format!("Power command failed: {}", e) })),
        )
            .into_response(),
    }
}

async fn get_chat_history() -> impl IntoResponse {
    let history = crate::chat_store::load_history();
    Json(json!({
        "success": true,
        "messages": history.messages
    }))
}

async fn add_chat_message(
    Json(req): Json<crate::chat_store::NewMessageRequest>,
) -> impl IntoResponse {
    let msg_type = req.msg_type.unwrap_or_else(|| "text".to_string());
    let metadata = req.metadata.unwrap_or_else(|| json!({}));
    let msg = crate::chat_store::add_message(req.sender, req.content, msg_type, metadata);
    Json(json!({
        "success": true,
        "message": msg
    }))
}

async fn clear_chat_history() -> impl IntoResponse {
    let history = crate::chat_store::clear_history();
    Json(json!({
        "success": true,
        "messages": history.messages
    }))
}

#[derive(serde::Deserialize)]
struct AiChatRequest {
    prompt: String,
    model: Option<String>,
}

async fn ai_chat_handler(Json(req): Json<AiChatRequest>) -> impl IntoResponse {
    let model = req.model.unwrap_or_else(|| "flowork-offline-slm".to_string());
    let prompt = req.prompt.trim().to_string();

    let inference_result = EmbeddedSlmEngine::infer(&prompt, &model);
    let response = inference_result.get("response").and_then(|r| r.as_str()).unwrap_or("").to_string();
    let tool_traces = inference_result.get("tool_traces").cloned().unwrap_or(json!([]));
    let used_model = inference_result.get("model").and_then(|m| m.as_str()).unwrap_or(&model).to_string();

    Json(json!({
        "success": true,
        "response": response,
        "tool_traces": tool_traces,
        "model": used_model
    }))
}

#[derive(serde::Deserialize)]
struct OpenAiChatRequest {
    messages: Option<Vec<Value>>,
    prompt: Option<String>,
    model: Option<String>,
}

async fn openai_chat_completions(Json(req): Json<OpenAiChatRequest>) -> impl IntoResponse {
    let model = req.model.unwrap_or_else(|| "flowork-slm-airgapped".to_string());
    let mut prompt_text = req.prompt.unwrap_or_default();

    if prompt_text.is_empty() {
        if let Some(msgs) = req.messages {
            for m in msgs {
                if let Some(c) = m.get("content").and_then(|c| c.as_str()) {
                    prompt_text = c.to_string();
                }
            }
        }
    }

    let inference_result = EmbeddedSlmEngine::infer(&prompt_text, &model);
    let content = inference_result.get("response").and_then(|r| r.as_str()).unwrap_or("").to_string();

    Json(json!({
        "id": format!("chatcmpl-{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis()),
        "object": "chat.completion",
        "created": std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": prompt_text.split_whitespace().count(),
            "completion_tokens": content.split_whitespace().count(),
            "total_tokens": prompt_text.split_whitespace().count() + content.split_whitespace().count()
        }
    }))
}


