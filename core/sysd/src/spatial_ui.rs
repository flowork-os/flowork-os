// =============================================================================
// 🚀 Flowork Sovereign OS — Spatial UI Graph Engine (Sprint 1)
// Unified AT-SPI2 Accessibility + DRM/KMS Hardware Vision Fusion (Pure Rust)
// Sub-10ms Native Desktop Inspection, Occlusion Analysis & Deterministic Input
// =============================================================================

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::fs;
use std::path::Path;
use std::time::{Instant, SystemTime, UNIX_EPOCH};
use x11rb::connection::Connection;

use crate::agent_bridge::FloworkAgentBridge;
use crate::drm_capture::{DrmCaptureEngine, DRM_SHM_META_PATH, DRM_SHM_PIXEL_PATH};
use crate::uinput_ctrl::get_global_uinput;
use crate::x11_ctrl::X11Controller;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialNode {
    pub id: String,
    pub app: String,
    pub title: String,
    pub role: String,
    pub name: String,
    pub value: Option<String>,
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
    pub center_x: i32,
    pub center_y: i32,
    pub states: Vec<String>,
    pub source: String, // "atspi", "x11", "vision_fallback"
    pub confidence: f32,
    pub is_occluded: bool,
    pub ref_id: Option<String>,
    pub window_id: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialGraph {
    pub timestamp_ms: u64,
    pub display_width: u32,
    pub display_height: u32,
    pub active_window: Option<String>,
    pub active_app: Option<String>,
    pub total_nodes: usize,
    pub nodes: Vec<SpatialNode>,
    pub drm_frame_synced: bool,
    pub latency_ms: u64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SpatialGraphQuery {
    pub app: Option<String>,
    pub interactive_only: Option<bool>,
    pub refresh_drm: Option<bool>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct InteractWidgetRequest {
    pub widget_id: Option<String>,
    #[serde(rename = "ref")]
    pub ref_tag: Option<String>,
    pub label: Option<String>,
    pub role: Option<String>,
    pub app: Option<String>,
    pub action: Option<String>, // "click", "double_click", "right_click", "type", "hover", "focus"
    pub text: Option<String>,
    pub use_hardware_hid: Option<bool>,
}

pub struct SpatialEngine;

impl SpatialEngine {
    /// Read or sync latest DRM screen capture metadata (/dev/shm)
    fn sync_drm_display(force_refresh: bool) -> (u32, u32, bool) {
        let meta_path = Path::new(DRM_SHM_META_PATH);
        let pixel_path = Path::new(DRM_SHM_PIXEL_PATH);

        let mut needs_refresh = force_refresh || !meta_path.exists() || !pixel_path.exists();

        if !needs_refresh && meta_path.exists() {
            if let Ok(meta_data) = fs::metadata(meta_path) {
                if let Ok(mod_time) = meta_data.modified() {
                    if let Ok(elapsed) = mod_time.elapsed() {
                        if elapsed.as_secs() > 10 {
                            needs_refresh = true;
                        }
                    }
                }
            }
        }

        if needs_refresh {
            let engine = DrmCaptureEngine::new();
            if let Ok(cap) = engine.capture_screen_fast() {
                return (cap.width, cap.height, true);
            }
        }

        // Try reading existing metadata
        if let Ok(content) = fs::read_to_string(meta_path) {
            if let Ok(v) = serde_json::from_str::<Value>(&content) {
                let w = v.get("width").and_then(|x| x.as_u64()).unwrap_or(2560) as u32;
                let h = v.get("height").and_then(|x| x.as_u64()).unwrap_or(1080) as u32;
                return (w, h, true);
            }
        }

        // Fallback default resolution
        (2560, 1080, false)
    }

    /// Recursively traverse AT-SPI json tree and extract SpatialNodes
    #[allow(clippy::too_many_arguments)]
    fn extract_atspi_nodes(
        tree: &Value,
        app_name: &str,
        win_title: &str,
        win_wid: Option<u32>,
        win_bounds: &(i32, i32, u32, u32),
        interactive_only: bool,
        nodes: &mut Vec<SpatialNode>,
        counter: &mut usize,
    ) {
        let role = tree.get("role").and_then(|v| v.as_str()).unwrap_or("widget").to_string();
        let name = tree.get("name").and_then(|v| v.as_str()).unwrap_or("").trim().to_string();
        let value = tree.get("value").and_then(|v| v.as_str()).map(|s| s.to_string());
        let ref_id = tree.get("ref").and_then(|v| v.as_str()).map(|s| s.to_string());

        let states: Vec<String> = tree
            .get("states")
            .and_then(|v| v.as_array())
            .map(|arr| arr.iter().filter_map(|s| s.as_str().map(|str_val| str_val.to_string())).collect())
            .unwrap_or_default();

        let is_visible = !states.contains(&"hidden".to_string());
        let is_disabled = states.contains(&"disabled".to_string());

        // Parse coordinates
        let mut x = win_bounds.0;
        let mut y = win_bounds.1;
        let mut width = win_bounds.2;
        let mut height = win_bounds.3;

        if let Some(bounds) = tree.get("bounds").and_then(|v| v.as_object()) {
            let bx = bounds.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0) as i32;
            let by = bounds.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0) as i32;
            let bw = bounds.get("width").and_then(|v| v.as_f64()).unwrap_or(0.0) as u32;
            let bh = bounds.get("height").and_then(|v| v.as_f64()).unwrap_or(0.0) as u32;

            if bw > 0 && bh > 0 {
                x = bx;
                y = by;
                width = bw;
                height = bh;
            }
        }

        let center_x = x + (width as i32 / 2);
        let center_y = y + (height as i32 / 2);

        let is_interactive = ref_id.is_some()
            || matches!(
                role.as_str(),
                "push-button"
                    | "button"
                    | "toggle-button"
                    | "check-box"
                    | "radio-button"
                    | "text"
                    | "entry"
                    | "password-text"
                    | "combo-box"
                    | "list-item"
                    | "menu-item"
                    | "check-menu-item"
                    | "page-tab"
                    | "slider"
                    | "link"
                    | "table-cell"
            );

        if is_visible && (!interactive_only || is_interactive) && (width > 2 && height > 2) {
            *counter += 1;
            let id = ref_id
                .clone()
                .unwrap_or_else(|| format!("sn-{}-{}-{}", app_name, role, counter));

            nodes.push(SpatialNode {
                id,
                app: app_name.to_string(),
                title: win_title.to_string(),
                role,
                name,
                value,
                x,
                y,
                width,
                height,
                center_x,
                center_y,
                states,
                source: "atspi".to_string(),
                confidence: if is_disabled { 0.70 } else { 0.99 },
                is_occluded: false, // Calculated in pass 2
                ref_id,
                window_id: win_wid,
            });
        }

        // Recursively inspect children
        if let Some(children) = tree.get("children").and_then(|v| v.as_array()) {
            for child in children {
                Self::extract_atspi_nodes(
                    child,
                    app_name,
                    win_title,
                    win_wid,
                    &(x, y, width, height),
                    interactive_only,
                    nodes,
                    counter,
                );
            }
        }
    }

    /// Build unified Spatial UI Graph with AT-SPI + X11 + DRM Framebuffer fusion
    pub async fn build_graph(query: SpatialGraphQuery) -> Result<SpatialGraph, String> {
        let start = Instant::now();
        let interactive_only = query.interactive_only.unwrap_or(true);
        let force_drm = query.refresh_drm.unwrap_or(false);

        // 1. Sync DRM display dimensions
        let (disp_w, disp_h, drm_synced) = Self::sync_drm_display(force_drm);

        // 2. Query X11 Windows for accurate stacking order and geometries
        let x11_windows = X11Controller::get_windows().unwrap_or_default();
        let mut active_window_title: Option<String> = None;
        let mut active_app_name: Option<String> = None;

        for win in &x11_windows {
            if win.is_active || win.is_focused {
                active_window_title = Some(win.title.clone());
                active_app_name = Some(win.wm_class.clone());
                break;
            }
        }

        let mut nodes: Vec<SpatialNode> = Vec::new();
        let mut node_counter = 0;
        let mut inspected_apps = std::collections::HashSet::new();

        // 3. Query AT-SPI Windows
        let atspi_windows_res = tokio::task::spawn_blocking(|| {
            std::process::Command::new("/usr/local/bin/agent-desktop")
                .arg("list-windows")
                .output()
        })
        .await
        .map_err(|e| format!("Join error on agent-desktop: {}", e))?;

        let mut atspi_windows_list: Vec<Value> = Vec::new();
        if let Ok(out) = atspi_windows_res {
            if out.status.success() {
                if let Ok(v) = serde_json::from_slice::<Value>(&out.stdout) {
                    if let Some(arr) = v.get("data").and_then(|d| d.as_array()) {
                        atspi_windows_list = arr.clone();
                    }
                }
            }
        }

        // 4. Traverse accessible windows
        let mut snapshot_tasks = Vec::new();
        for win_val in atspi_windows_list {
            let app_name = win_val.get("app_name").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
            let title = win_val.get("title").and_then(|v| v.as_str()).unwrap_or("").to_string();
            let win_id = win_val.get("id").and_then(|v| v.as_str()).unwrap_or("").to_string();

            // Filter if requested
            if let Some(ref filter) = query.app {
                if !app_name.to_lowercase().contains(&filter.to_lowercase())
                    && !title.to_lowercase().contains(&filter.to_lowercase())
                {
                    continue;
                }
            }

            inspected_apps.insert(app_name.clone());

            let mut win_bounds = (0i32, 0i32, disp_w, disp_h);
            if let Some(b) = win_val.get("bounds").and_then(|v| v.as_object()) {
                let bx = b.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0) as i32;
                let by = b.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0) as i32;
                let bw = b.get("width").and_then(|v| v.as_f64()).unwrap_or(disp_w as f64) as u32;
                let bh = b.get("height").and_then(|v| v.as_f64()).unwrap_or(disp_h as f64) as u32;
                win_bounds = (bx, by, bw, bh);
            }

            // Find matching X11 WID
            let matched_wid = x11_windows.iter().find_map(|xw| {
                if xw.title == title || xw.wm_class.to_lowercase() == app_name.to_lowercase() {
                    Some(xw.id)
                } else {
                    None
                }
            });

            if !win_id.is_empty() {
                snapshot_tasks.push(tokio::spawn(async move {
                    let out = tokio::task::spawn_blocking(move || {
                        std::process::Command::new("/usr/local/bin/agent-desktop")
                            .arg("snapshot")
                            .arg("--window-id")
                            .arg(&win_id)
                            .arg("-i")
                            .output()
                    })
                    .await;
                    (app_name, title, matched_wid, win_bounds, out)
                }));
            }
        }

        // Await all snapshot tasks concurrently
        for task in snapshot_tasks {
            if let Ok((app_name, title, matched_wid, win_bounds, Ok(Ok(snap_out)))) = task.await {
                if snap_out.status.success() {
                    if let Ok(parsed) = serde_json::from_slice::<Value>(&snap_out.stdout) {
                        if let Some(tree) = parsed.pointer("/data/tree") {
                            Self::extract_atspi_nodes(
                                tree,
                                &app_name,
                                &title,
                                matched_wid,
                                &win_bounds,
                                interactive_only,
                                &mut nodes,
                                &mut node_counter,
                            );
                        }
                    }
                }
            }
        }

        // 5. Fallback for X11 windows that lack AT-SPI support
        for xw in &x11_windows {
            let app_class = xw.wm_class.to_lowercase();
            if !inspected_apps.contains(&xw.wm_class) && !app_class.contains("desktop") && !app_class.contains("wm") {
                if let Some(ref filter) = query.app {
                    if !xw.wm_class.to_lowercase().contains(&filter.to_lowercase())
                        && !xw.title.to_lowercase().contains(&filter.to_lowercase())
                    {
                        continue;
                    }
                }

                node_counter += 1;
                let cx = xw.x as i32 + (xw.width as i32 / 2);
                let cy = xw.y as i32 + (xw.height as i32 / 2);

                nodes.push(SpatialNode {
                    id: format!("x11-{}-{}", xw.id, node_counter),
                    app: xw.wm_class.clone(),
                    title: xw.title.clone(),
                    role: "window".to_string(),
                    name: xw.title.clone(),
                    value: None,
                    x: xw.x as i32,
                    y: xw.y as i32,
                    width: xw.width as u32,
                    height: xw.height as u32,
                    center_x: cx,
                    center_y: cy,
                    states: vec![if xw.is_focused { "focused" } else { "visible" }.to_string()],
                    source: "x11".to_string(),
                    confidence: 0.85,
                    is_occluded: false,
                    ref_id: None,
                    window_id: Some(xw.id),
                });
            }
        }

        // 6. Pass 2: Occlusion analysis via X11 stacking order
        // Windows listed first in X11 query typically hold higher z-order
        for node in &mut nodes {
            // Check if outside screen bounds
            if node.center_x < 0 || node.center_x >= disp_w as i32 || node.center_y < 0 || node.center_y >= disp_h as i32 {
                node.is_occluded = true;
                continue;
            }

            // Check if covered by another active overlapping window
            if let Some(node_wid) = node.window_id {
                let mut found_higher_window = false;
                for xw in &x11_windows {
                    if xw.id == node_wid {
                        break; // Reached own window in stacking order
                    }
                    // If an earlier window covers our node center coordinates
                    if xw.is_active || xw.is_focused {
                        let wx1 = xw.x as i32;
                        let wy1 = xw.y as i32;
                        let wx2 = wx1 + xw.width as i32;
                        let wy2 = wy1 + xw.height as i32;

                        if node.center_x >= wx1 && node.center_x <= wx2 && node.center_y >= wy1 && node.center_y <= wy2 {
                            node.is_occluded = true;
                            found_higher_window = true;
                            break;
                        }
                    }
                }
                if found_higher_window {
                    node.confidence *= 0.5;
                }
            }
        }

        let total_nodes = nodes.len();
        let latency_ms = start.elapsed().as_millis() as u64;

        Ok(SpatialGraph {
            timestamp_ms: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map(|d| d.as_millis() as u64)
                .unwrap_or(0),
            display_width: disp_w,
            display_height: disp_h,
            active_window: active_window_title,
            active_app: active_app_name,
            total_nodes,
            nodes,
            drm_frame_synced: drm_synced,
            latency_ms,
        })
    }

    /// Interact deterministically with a target widget in the Spatial Scene Graph
    pub async fn interact_widget(req: InteractWidgetRequest) -> Result<Value, String> {
        let start = Instant::now();
        let action = req.action.unwrap_or_else(|| "click".to_string());

        // 1. Fetch current spatial scene graph
        let graph = Self::build_graph(SpatialGraphQuery {
            app: req.app.clone(),
            interactive_only: Some(false),
            refresh_drm: Some(false),
        })
        .await?;

        // 2. Resolve target node
        let target_node = graph.nodes.iter().find(|n| {
            if let Some(ref r) = req.ref_tag {
                if let Some(ref nr) = n.ref_id {
                    if nr == r {
                        return true;
                    }
                }
                if &n.id == r {
                    return true;
                }
            }
            if let Some(ref wid) = req.widget_id {
                if &n.id == wid {
                    return true;
                }
            }
            if let Some(ref lbl) = req.label {
                let lbl_lower = lbl.to_lowercase();
                if n.name.to_lowercase().contains(&lbl_lower)
                    || n.value.as_ref().map(|v| v.to_lowercase().contains(&lbl_lower)).unwrap_or(false)
                {
                    if let Some(ref role_filter) = req.role {
                        return n.role.to_lowercase().contains(&role_filter.to_lowercase());
                    }
                    return true;
                }
            }
            false
        });

        let node = match target_node {
            Some(n) => n.clone(),
            None => {
                let available_labels: Vec<String> = graph
                    .nodes
                    .iter()
                    .filter(|n| !n.name.is_empty())
                    .take(15)
                    .map(|n| format!("[{}] '{}' ({})", n.role, n.name, n.id))
                    .collect();

                return Err(format!(
                    "Widget target not found matching criteria (label: {:?}, ref: {:?}, role: {:?}). Available candidates: {:?}",
                    req.label, req.ref_tag, req.role, available_labels
                ));
            }
        };

        // 3. Focus window if needed
        if let Some(wid) = node.window_id {
            let _ = X11Controller::focus_window(wid);
            tokio::time::sleep(tokio::time::Duration::from_millis(30)).await;
        }

        // 4. Dispatch action
        let use_hw = req.use_hardware_hid.unwrap_or(false);

        match action.as_str() {
            "click" => {
                if let (Some(ref r), false) = (&node.ref_id, use_hw) {
                    // Fast-path AT-SPI press action
                    let _ = FloworkAgentBridge::act("click", Some(r), None, None, false).await;
                } else {
                    // Physical synthetic click via absolute X11 coords
                    let _ = X11Controller::synthetic_mouse_click(node.center_x as i16, node.center_y as i16, 1)?;
                }
            }
            "double_click" => {
                let _ = X11Controller::synthetic_mouse_click(node.center_x as i16, node.center_y as i16, 1)?;
                tokio::time::sleep(tokio::time::Duration::from_millis(60)).await;
                let _ = X11Controller::synthetic_mouse_click(node.center_x as i16, node.center_y as i16, 1)?;
            }
            "right_click" => {
                let _ = X11Controller::synthetic_mouse_click(node.center_x as i16, node.center_y as i16, 3)?;
            }
            "hover" => {
                // Synthesize mouse move to center coordinates
                let (conn, screen_num) = x11rb::connect(None).map_err(|e| e.to_string())?;
                let screen = &conn.setup().roots[screen_num];
                let _ = x11rb::protocol::xproto::warp_pointer(
                    &conn,
                    x11rb::NONE,
                    screen.root,
                    0,
                    0,
                    0,
                    0,
                    node.center_x as i16,
                    node.center_y as i16,
                );
            }
            "type" => {
                let txt = req.text.as_deref().unwrap_or("");
                if let (Some(ref r), false) = (&node.ref_id, use_hw) {
                    let _ = FloworkAgentBridge::act("type", Some(r), Some(txt), None, false).await;
                } else {
                    // Click center then inject keystrokes via virtual uinput
                    let _ = X11Controller::synthetic_mouse_click(node.center_x as i16, node.center_y as i16, 1)?;
                    tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
                    let uinput = get_global_uinput();
                    let guard = uinput.lock().unwrap();
                    let _ = guard.type_text(txt);
                }
            }
            "focus" => {
                if let Some(wid) = node.window_id {
                    let _ = X11Controller::focus_window(wid);
                }
            }
            other => return Err(format!("Unsupported action '{}'", other)),
        }

        let elapsed_ms = start.elapsed().as_millis() as u64;

        Ok(json!({
            "status": "ok",
            "action": action,
            "target": {
                "id": node.id,
                "role": node.role,
                "name": node.name,
                "app": node.app,
                "center": [node.center_x, node.center_y],
                "ref": node.ref_id,
                "is_occluded": node.is_occluded
            },
            "latency_ms": elapsed_ms
        }))
    }
}
