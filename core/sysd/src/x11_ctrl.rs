// [FL_INDEX: update_windowinfo_fields, add_wid_and_wm_class, x11_ctrl_struct, rust_windowinfo, compatibility_fields | COT: Add wid, wm_class, is_focused fields to WindowInfo struct for universal client compatibility.| AT: 2026-11-01T16:50:05Z]
// =============================================================================
// 🚀 Flowork Sovereign OS — Native X11 & XTest Controller (Pure Rust)
// Zero-subshell window management, instant geometry tiling & synthetic input
// =============================================================================

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use x11rb::connection::Connection;
use x11rb::protocol::xproto::{
    Atom, AtomEnum, ClientMessageData, ClientMessageEvent, ConfigureWindowAux,
    ConnectionExt as _, EventMask, GetPropertyReply, Window, CLIENT_MESSAGE_EVENT,
};
use x11rb::protocol::xtest::ConnectionExt as _;
use x11rb::rust_connection::RustConnection;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WindowInfo {
    pub id: u32,
    pub wid: u32,
    pub title: String,
    pub class_name: String,
    pub wm_class: String,
    pub pid: Option<u32>,
    pub x: i16,
    pub y: i16,
    pub width: u16,
    pub height: u16,
    pub is_active: bool,
    pub is_focused: bool,
}

pub struct X11Controller;

impl X11Controller {
    /// Connect to local X11 display ($DISPLAY)
    fn connect() -> Result<(RustConnection, usize), String> {
        x11rb::connect(None).map_err(|e| format!("Failed to connect to X11 display: {}", e))
    }

    /// Helper to intern an X11 atom
    fn intern_atom(conn: &RustConnection, name: &str) -> Result<Atom, String> {
        conn.intern_atom(false, name.as_bytes())
            .map_err(|e| format!("Failed to intern atom {}: {}", name, e))?
            .reply()
            .map_err(|e| format!("Atom reply failed for {}: {}", name, e))
            .map(|r| r.atom)
    }

    /// Read string property from window
    fn read_string_property(conn: &RustConnection, window: Window, atom: Atom) -> Option<String> {
        if let Ok(cookie) = conn.get_property(false, window, atom, AtomEnum::ANY, 0, 1024) {
            if let Ok(reply) = cookie.reply() {
                if !reply.value.is_empty() {
                    return Some(String::from_utf8_lossy(&reply.value).trim_matches('\0').to_string());
                }
            }
        }
        None
    }

    /// Read u32 property from window
    fn read_u32_property(conn: &RustConnection, window: Window, atom: Atom) -> Option<u32> {
        if let Ok(cookie) = conn.get_property(false, window, atom, AtomEnum::CARDINAL, 0, 1) {
            if let Ok(reply) = cookie.reply() {
                if reply.value.len() >= 4 {
                    return Some(u32::from_ne_bytes([
                        reply.value[0], reply.value[1], reply.value[2], reply.value[3],
                    ]));
                }
            }
        }
        None
    }

    /// Query detailed list of all managed windows
    pub fn get_windows() -> Result<Vec<WindowInfo>, String> {
        let (conn, screen_num) = Self::connect()?;
        let screen = &conn.setup().roots[screen_num];
        let root = screen.root;

        let net_client_list = Self::intern_atom(&conn, "_NET_CLIENT_LIST")?;
        let net_active_window = Self::intern_atom(&conn, "_NET_ACTIVE_WINDOW")?;
        let net_wm_name = Self::intern_atom(&conn, "_NET_WM_NAME")?;
        let net_wm_pid = Self::intern_atom(&conn, "_NET_WM_PID")?;

        let active_win = Self::read_u32_property(&conn, root, net_active_window).unwrap_or(0);

        let mut windows = Vec::new();

        let client_list_reply: GetPropertyReply = conn
            .get_property(false, root, net_client_list, AtomEnum::WINDOW, 0, 1024)
            .map_err(|e| format!("Failed to get _NET_CLIENT_LIST: {}", e))?
            .reply()
            .map_err(|e| format!("Failed reply for _NET_CLIENT_LIST: {}", e))?;

        let win_ids: Vec<u32> = client_list_reply
            .value32()
            .map(|iter| iter.collect())
            .unwrap_or_default();

        for win_id in win_ids {
            let win = win_id as Window;
            let geom = match conn.get_geometry(win) {
                Ok(c) => match c.reply() {
                    Ok(g) => g,
                    Err(_) => continue,
                },
                Err(_) => continue,
            };

            let title = Self::read_string_property(&conn, win, net_wm_name)
                .or_else(|| Self::read_string_property(&conn, win, AtomEnum::WM_NAME.into()))
                .unwrap_or_else(|| "Unknown".to_string());

            let class_name = Self::read_string_property(&conn, win, AtomEnum::WM_CLASS.into())
                .unwrap_or_else(|| "Unknown".to_string());

            let pid = Self::read_u32_property(&conn, win, net_wm_pid);

            windows.push(WindowInfo {
                id: win_id,
                wid: win_id,
                title,
                class_name: class_name.clone(),
                wm_class: class_name,
                pid,
                x: geom.x,
                y: geom.y,
                width: geom.width,
                height: geom.height,
                is_active: win_id == active_win,
                is_focused: win_id == active_win,
            });
        }

        Ok(windows)
    }

    /// Focus target window by sending _NET_ACTIVE_WINDOW ClientMessage
    pub fn focus_window(win_id: u32) -> Result<Value, String> {
        let (conn, screen_num) = Self::connect()?;
        let screen = &conn.setup().roots[screen_num];
        let root = screen.root;

        let net_active_window = Self::intern_atom(&conn, "_NET_ACTIVE_WINDOW")?;

        let event = ClientMessageEvent {
            response_type: CLIENT_MESSAGE_EVENT,
            format: 32,
            sequence: 0,
            window: win_id as Window,
            type_: net_active_window,
            data: ClientMessageData::from([2u32, 0, 0, 0, 0]), // 2 = source indication (pager)
        };

        conn.send_event(
            false,
            root,
            EventMask::SUBSTRUCTURE_REDIRECT | EventMask::SUBSTRUCTURE_NOTIFY,
            event,
        )
        .map_err(|e| format!("Failed to send _NET_ACTIVE_WINDOW event: {}", e))?;

        let _ = conn.set_input_focus(
            x11rb::protocol::xproto::InputFocus::POINTER_ROOT,
            win_id as Window,
            x11rb::CURRENT_TIME,
        );

        conn.flush().map_err(|e| format!("Flush failed: {}", e))?;

        Ok(json!({
            "status": "SUCCESS",
            "focused_window_id": win_id
        }))
    }

    /// Tile window side-by-side: left, right, full, center
    pub fn tile_window(win_id: u32, position: &str) -> Result<Value, String> {
        let (conn, screen_num) = Self::connect()?;
        let screen = &conn.setup().roots[screen_num];
        let screen_width = screen.width_in_pixels as i32;
        let screen_height = screen.height_in_pixels as i32;

        let (x, y, w, h) = match position.to_lowercase().as_str() {
            "left" => (0, 0, (screen_width / 2) as u32, screen_height as u32),
            "right" => (screen_width / 2, 0, (screen_width / 2) as u32, screen_height as u32),
            "full" | "maximize" => (0, 0, screen_width as u32, screen_height as u32),
            "center" => (
                screen_width / 4,
                screen_height / 4,
                (screen_width / 2) as u32,
                (screen_height / 2) as u32,
            ),
            _ => (0, 0, (screen_width / 2) as u32, screen_height as u32),
        };

        // Raise window first
        let _ = conn.configure_window(
            win_id as Window,
            &ConfigureWindowAux::new()
                .stack_mode(x11rb::protocol::xproto::StackMode::ABOVE)
                .x(x)
                .y(y)
                .width(w)
                .height(h),
        );

        conn.flush().map_err(|e| format!("Configure window flush failed: {}", e))?;
        let _ = Self::focus_window(win_id);

        Ok(json!({
            "status": "SUCCESS",
            "window_id": win_id,
            "position": position,
            "geometry": { "x": x, "y": y, "width": w, "height": h }
        }))
    }

    /// Synthetic Mouse Click via XTest
    pub fn synthetic_mouse_click(x: i16, y: i16, button: u8) -> Result<Value, String> {
        let (conn, screen_num) = Self::connect()?;
        let screen = &conn.setup().roots[screen_num];
        let root = screen.root;

        // 1. Move cursor (MOTION_NOTIFY = 6)
        conn.xtest_fake_input(
            x11rb::protocol::xproto::MOTION_NOTIFY_EVENT,
            0,
            0,
            root,
            x,
            y,
            0,
        )
        .map_err(|e| format!("XTest motion failed: {}", e))?;

        // 2. Button Press (BUTTON_PRESS = 4)
        conn.xtest_fake_input(
            x11rb::protocol::xproto::BUTTON_PRESS_EVENT,
            button,
            0,
            root,
            x,
            y,
            0,
        )
        .map_err(|e| format!("XTest button press failed: {}", e))?;

        // 3. Button Release (BUTTON_RELEASE = 5)
        conn.xtest_fake_input(
            x11rb::protocol::xproto::BUTTON_RELEASE_EVENT,
            button,
            0,
            root,
            x,
            y,
            0,
        )
        .map_err(|e| format!("XTest button release failed: {}", e))?;

        conn.flush().map_err(|e| format!("XTest flush failed: {}", e))?;

        Ok(json!({
            "status": "SUCCESS",
            "action": "click",
            "x": x,
            "y": y,
            "button": button
        }))
    }

    /// Synthetic Key Press via XTest
    pub fn synthetic_key_press(keycode: u8) -> Result<Value, String> {
        let (conn, screen_num) = Self::connect()?;
        let screen = &conn.setup().roots[screen_num];
        let root = screen.root;

        // KEY_PRESS = 2
        conn.xtest_fake_input(
            x11rb::protocol::xproto::KEY_PRESS_EVENT,
            keycode,
            0,
            root,
            0,
            0,
            0,
        )
        .map_err(|e| format!("XTest key press failed: {}", e))?;

        // KEY_RELEASE = 3
        conn.xtest_fake_input(
            x11rb::protocol::xproto::KEY_RELEASE_EVENT,
            keycode,
            0,
            root,
            0,
            0,
            0,
        )
        .map_err(|e| format!("XTest key release failed: {}", e))?;

        conn.flush().map_err(|e| format!("XTest key flush failed: {}", e))?;

        Ok(json!({
            "status": "SUCCESS",
            "action": "key_press",
            "keycode": keycode
        }))
    }
}
