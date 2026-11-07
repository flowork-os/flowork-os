// [FL_INDEX: sidebar_geometry_engine, x11_docking, auto_hide, pure_rust_sysd, floworkos | COT: Native Rust implementation of sidebar geometry and dynamic docking controller for flowork-sysd.| AT: 2026-11-02T00:55:00Z]
// =============================================================================
// 🚀 Flowork Sovereign OS — Sidebar Geometry & Dynamic Docking Engine
// Replaces daemon/server.mjs geometry subsystem with Pure Rust synergy
// Handles expand, collapse, drag resize, left/right docking, and struts
// =============================================================================

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::fs;
use std::path::PathBuf;
use std::process::Command;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SidebarGeometry {
    pub dock: String,       // "left" | "right"
    pub width: i32,         // 300..900
    pub state: String,      // "expanded" | "collapsed"
    pub pinned: bool,
}

impl Default for SidebarGeometry {
    fn default() -> Self {
        Self {
            dock: "right".to_string(),
            width: 440,
            state: "expanded".to_string(),
            pinned: true,
        }
    }
}

#[derive(Debug, Deserialize, Clone, Default)]
#[allow(non_snake_case)]
pub struct SidebarGeometryRequest {
    pub dock: Option<String>,
    pub width: Option<i32>,
    pub state: Option<String>,
    pub pinned: Option<bool>,
    pub save: Option<bool>,
    pub fast: Option<bool>,
    pub screenW: Option<i32>,
    pub screenH: Option<i32>,
    pub display: Option<String>,
}

fn get_geometry_file_path() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    PathBuf::from(home).join(".flowork_sidebar_geometry.json")
}

pub fn load_geometry() -> SidebarGeometry {
    let path = get_geometry_file_path();
    if path.exists() {
        if let Ok(content) = fs::read_to_string(&path) {
            if let Ok(geo) = serde_json::from_str::<SidebarGeometry>(&content) {
                return geo;
            }
        }
    }
    SidebarGeometry::default()
}

pub fn save_geometry(geo: &SidebarGeometry) {
    let path = get_geometry_file_path();
    if let Ok(content) = serde_json::to_string_pretty(geo) {
        let _ = fs::write(path, content);
    }
}

/// Discover active X11 displays and locate the Flowork Sidebar window ID
fn find_sidebar_window(req_display: Option<&str>) -> (String, Option<String>) {
    let mut candidate_displays: Vec<String> = Vec::new();
    if let Some(d) = req_display {
        if !d.is_empty() {
            candidate_displays.push(d.to_string());
        }
    }
    if let Ok(env_disp) = std::env::var("DISPLAY") {
        if !env_disp.is_empty() && !candidate_displays.contains(&env_disp) {
            candidate_displays.push(env_disp);
        }
    }
    if !candidate_displays.iter().any(|d| d == ":0") {
        candidate_displays.push(":0".to_string());
    }

    // Check /tmp/.X11-unix sockets
    if let Ok(entries) = fs::read_dir("/tmp/.X11-unix") {
        for entry in entries.flatten() {
            if let Ok(name) = entry.file_name().into_string() {
                if name.starts_with('X') {
                    let disp = format!(":{}", &name[1..]);
                    if !candidate_displays.contains(&disp) {
                        candidate_displays.push(disp);
                    }
                }
            }
        }
    }

    let default_display = candidate_displays.first().cloned().unwrap_or_else(|| ":0".to_string());

    for disp in &candidate_displays {
        let search_cmd = format!(
            "wid=\"$(DISPLAY=\"{disp}\" xdotool search --name \"Flowork Agent Sidebar\" 2>/dev/null | tail -n 1)\"; \
             [ -z \"$wid\" ] && wid=\"$(DISPLAY=\"{disp}\" xdotool search --class \"FloworkSidebar\" 2>/dev/null | tail -n 1)\"; \
             [ -z \"$wid\" ] && wid=\"$(DISPLAY=\"{disp}\" xdotool search --name \"Sovereign Launcher\" 2>/dev/null | tail -n 1)\"; \
             [ -z \"$wid\" ] && wid=\"$(DISPLAY=\"{disp}\" xdotool search --name \"127.0.0.1:19890\" 2>/dev/null | tail -n 1)\"; \
             echo \"$wid\""
        );
        if let Ok(output) = Command::new("sh").arg("-c").arg(&search_cmd).output() {
            let wid = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !wid.is_empty() && wid.chars().all(|c| c.is_ascii_digit()) {
                return (disp.clone(), Some(wid));
            }
        }
    }

    (default_display, None)
}

/// Detect screen dimensions for target display or fallback to client values
fn detect_screen_dim(target_disp: &str, req_w: Option<i32>, req_h: Option<i32>) -> (i32, i32) {
    if let (Some(w), Some(h)) = (req_w, req_h) {
        if w > 400 && h > 400 {
            return (w, h);
        }
    }

    let cmd = format!(
        "DISPLAY=\"{target_disp}\" xdotool getdisplaygeometry 2>/dev/null || \
         DISPLAY=\"{target_disp}\" xrandr --current 2>/dev/null | grep -o 'current [0-9]* x [0-9]*' | awk '{{print $2, $4}}'"
    );
    if let Ok(output) = Command::new("sh").arg("-c").arg(&cmd).output() {
        let txt = String::from_utf8_lossy(&output.stdout);
        let parts: Vec<&str> = txt.split_whitespace().collect();
        if parts.len() >= 2 {
            if let (Ok(w), Ok(h)) = (parts[0].parse::<i32>(), parts[1].parse::<i32>()) {
                if w > 400 && h > 400 {
                    return (w, h);
                }
            }
        }
    }

    (2560, 1080)
}

pub fn update_geometry(req: SidebarGeometryRequest) -> Value {
    let mut current = load_geometry();

    if let Some(d) = req.dock.as_deref() {
        current.dock = if d == "left" { "left".to_string() } else { "right".to_string() };
    }
    if let Some(w) = req.width {
        if w > 0 {
            current.width = w.clamp(300, 1200);
        }
    }
    if let Some(s) = req.state.as_deref() {
        current.state = if s == "expanded" { "expanded".to_string() } else { "collapsed".to_string() };
    }
    if let Some(p) = req.pinned {
        current.pinned = p;
    }

    if req.save.unwrap_or(true) {
        save_geometry(&current);
    }

    let (target_disp, wid_opt) = find_sidebar_window(req.display.as_deref());
    let (screen_w, screen_h) = detect_screen_dim(&target_disp, req.screenW, req.screenH);

    let is_collapsed = current.state == "collapsed";
    let effective_w = if is_collapsed { 6 } else { current.width };
    let pos_x = if current.dock == "left" { 0 } else { screen_w - effective_w };
    let pos_y = 0;
    let win_h = screen_h;

    let is_fast = req.fast.unwrap_or(false);

    if let Some(ref wid) = wid_opt {
        // When collapsed or unpinned auto-hide, clear struts so other windows take full screen
        let (strut_partial, strut) = if is_collapsed || !current.pinned {
            ("0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0".to_string(), "0, 0, 0, 0".to_string())
        } else if current.dock == "left" {
            (format!("{}, 0, 0, 0, 0, {}, 0, 0, 0, 0, 0, 0", effective_w, win_h), format!("{}, 0, 0, 0", effective_w))
        } else {
            (format!("0, {}, 0, 0, 0, 0, 0, {}, 0, 0, 0, 0", effective_w, win_h), format!("0, {}, 0, 0", effective_w))
        };

        if is_fast {
            let cmd = format!(
                "DISPLAY=\"{target_disp}\" xprop -id \"{wid}\" -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE \"_NET_WM_WINDOW_TYPE_NORMAL\" 2>/dev/null || true; \
                 DISPLAY=\"{target_disp}\" xprop -id \"{wid}\" -f _NET_WM_STRUT_PARTIAL 32c -set _NET_WM_STRUT_PARTIAL \"{strut_partial}\" 2>/dev/null || true; \
                 DISPLAY=\"{target_disp}\" xprop -id \"{wid}\" -f _NET_WM_STRUT 32c -set _NET_WM_STRUT \"{strut}\" 2>/dev/null || true; \
                 DISPLAY=\"{target_disp}\" xdotool windowsize \"{wid}\" \"{effective_w}\" \"{win_h}\" windowmove \"{wid}\" \"{pos_x}\" \"{pos_y}\" 2>/dev/null || true;"
            );
            let _ = Command::new("sh").arg("-c").arg(cmd).output();
        } else {
            let cmd = format!(
                "DISPLAY=\"{target_disp}\" wmctrl -i -r \"{wid}\" -b remove,maximized_vert,maximized_horz,hidden 2>/dev/null || true; \
                 DISPLAY=\"{target_disp}\" xprop -id \"{wid}\" -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE \"_NET_WM_WINDOW_TYPE_NORMAL\" 2>/dev/null || true; \
                 DISPLAY=\"{target_disp}\" xprop -id \"{wid}\" -f _MOTIF_WM_HINTS 32c -set _MOTIF_WM_HINTS \"0x2, 0x0, 0x0, 0x0, 0x0\" 2>/dev/null || true; \
                 DISPLAY=\"{target_disp}\" xprop -id \"{wid}\" -f _NET_WM_STRUT_PARTIAL 32c -set _NET_WM_STRUT_PARTIAL \"{strut_partial}\" 2>/dev/null || true; \
                 DISPLAY=\"{target_disp}\" xprop -id \"{wid}\" -f _NET_WM_STRUT 32c -set _NET_WM_STRUT \"{strut}\" 2>/dev/null || true; \
                 DISPLAY=\"{target_disp}\" xdotool windowsize \"{wid}\" \"{effective_w}\" \"{win_h}\" windowmove \"{wid}\" \"{pos_x}\" \"{pos_y}\" 2>/dev/null || true; \
                 DISPLAY=\"{target_disp}\" wmctrl -i -r \"{wid}\" -b add,above,skip_taskbar,skip_pager 2>/dev/null || true;"
            );
            let _ = Command::new("sh").arg("-c").arg(cmd).output();
        }
    }

    json!({
        "success": true,
        "dock": current.dock,
        "width": current.width,
        "state": current.state,
        "pinned": current.pinned,
        "posX": pos_x,
        "posY": pos_y,
        "effectiveW": effective_w,
        "height": win_h,
        "wid": wid_opt,
        "display": target_disp
    })
}
