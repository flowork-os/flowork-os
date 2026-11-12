// =============================================================================
// 🚀 Flowork Sovereign Linux OS — Sovereign Window Manager (flowork-wm)
// Pure Rust lightweight X11 window manager, auto-tiler & dock manager
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================

use std::collections::HashSet;
use std::process::{Child, Command};
use x11rb::connection::Connection;
use x11rb::protocol::xproto::{
    Atom, AtomEnum, ButtonIndex, ChangeWindowAttributesAux,
    ClientMessageData, ClientMessageEvent, ConfigWindow, ConfigureWindowAux,
    ConnectionExt as _, CreateWindowAux, EventMask, GrabMode, ModMask,
    PropMode, StackMode, Window, CLIENT_MESSAGE_EVENT,
};
use x11rb::rust_connection::RustConnection;
use x11rb::wrapper::ConnectionExt as _;
use x11rb::CURRENT_TIME;

struct Atoms {
    net_supporting_wm_check: Atom,
    net_supported: Atom,
    net_client_list: Atom,
    net_active_window: Atom,
    net_wm_name: Atom,
    net_close_window: Atom,
    wm_protocols: Atom,
    wm_delete_window: Atom,
    net_wm_window_type: Atom,
    net_wm_window_type_dock: Atom,
    net_wm_window_type_desktop: Atom,
    net_wm_window_type_notification: Atom,
}

impl Atoms {
    fn new(conn: &RustConnection) -> Result<Self, Box<dyn std::error::Error>> {
        let net_supporting_wm_check = conn.intern_atom(false, b"_NET_SUPPORTING_WM_CHECK")?.reply()?.atom;
        let net_supported = conn.intern_atom(false, b"_NET_SUPPORTED")?.reply()?.atom;
        let net_client_list = conn.intern_atom(false, b"_NET_CLIENT_LIST")?.reply()?.atom;
        let net_active_window = conn.intern_atom(false, b"_NET_ACTIVE_WINDOW")?.reply()?.atom;
        let net_wm_name = conn.intern_atom(false, b"_NET_WM_NAME")?.reply()?.atom;
        let net_close_window = conn.intern_atom(false, b"_NET_CLOSE_WINDOW")?.reply()?.atom;
        let wm_protocols = conn.intern_atom(false, b"WM_PROTOCOLS")?.reply()?.atom;
        let wm_delete_window = conn.intern_atom(false, b"WM_DELETE_WINDOW")?.reply()?.atom;
        let net_wm_window_type = conn.intern_atom(false, b"_NET_WM_WINDOW_TYPE")?.reply()?.atom;
        let net_wm_window_type_dock = conn.intern_atom(false, b"_NET_WM_WINDOW_TYPE_DOCK")?.reply()?.atom;
        let net_wm_window_type_desktop = conn.intern_atom(false, b"_NET_WM_WINDOW_TYPE_DESKTOP")?.reply()?.atom;
        let net_wm_window_type_notification = conn.intern_atom(false, b"_NET_WM_WINDOW_TYPE_NOTIFICATION")?.reply()?.atom;

        Ok(Self {
            net_supporting_wm_check,
            net_supported,
            net_client_list,
            net_active_window,
            net_wm_name,
            net_close_window,
            wm_protocols,
            wm_delete_window,
            net_wm_window_type,
            net_wm_window_type_dock,
            net_wm_window_type_desktop,
            net_wm_window_type_notification,
        })
    }
}

struct FloworkWm {
    conn: RustConnection,
    root: Window,
    wm_check_win: Window,
    atoms: Atoms,
    clients: Vec<Window>,
    floating_clients: HashSet<Window>,
    spawned_children: Vec<Child>,
    sidebar_win: Option<Window>,
    active_client: Option<Window>,
    sidebar_width: u32,
    screen_width: u32,
    screen_height: u32,
}

impl FloworkWm {
    fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let (conn, screen_num) = x11rb::connect(None)?;
        let screen = &conn.setup().roots[screen_num];
        let root = screen.root;
        let screen_width = screen.width_in_pixels as u32;
        let screen_height = screen.height_in_pixels as u32;

        println!("=============================================================================");
        println!("  ⚡ Flowork Sovereign Window Manager (flowork-wm)");
        println!("  Architecture: Pure Rust X11 Window Manager & Auto-Tiling Compositor");
        println!("  Screen: {}x{} on Display Screen #{}", screen_width, screen_height, screen_num);
        println!("=============================================================================");

        // 1. Claim Window Manager Ownership on Root Window
        let change = ChangeWindowAttributesAux::new().event_mask(
            EventMask::SUBSTRUCTURE_REDIRECT
                | EventMask::SUBSTRUCTURE_NOTIFY
                | EventMask::STRUCTURE_NOTIFY
                | EventMask::BUTTON_PRESS
                | EventMask::KEY_PRESS
                | EventMask::PROPERTY_CHANGE,
        );

        if let Err(e) = conn.change_window_attributes(root, &change)?.check() {
            eprintln!("❌ [flowork-wm] Failed to claim window manager ownership: another WM is running! ({})", e);
            return Err(e.into());
        }

        // 2. Intern Atoms
        let atoms = Atoms::new(&conn)?;

        // 3. EWMH Supporting Window Check
        let wm_check_win = conn.generate_id()?;
        conn.create_window(
            0,
            wm_check_win,
            root,
            -1,
            -1,
            1,
            1,
            0,
            x11rb::protocol::xproto::WindowClass::INPUT_ONLY,
            0,
            &CreateWindowAux::new(),
        )?;

        conn.change_property32(
            PropMode::REPLACE,
            wm_check_win,
            atoms.net_supporting_wm_check,
            AtomEnum::WINDOW,
            &[wm_check_win],
        )?;

        conn.change_property8(
            PropMode::REPLACE,
            wm_check_win,
            atoms.net_wm_name,
            AtomEnum::STRING,
            b"flowork-wm",
        )?;

        conn.change_property32(
            PropMode::REPLACE,
            root,
            atoms.net_supporting_wm_check,
            AtomEnum::WINDOW,
            &[wm_check_win],
        )?;

        // Advertise Supported EWMH Atoms
        let supported_atoms = [
            atoms.net_supporting_wm_check,
            atoms.net_supported,
            atoms.net_client_list,
            atoms.net_active_window,
            atoms.net_wm_name,
            atoms.net_close_window,
            atoms.net_wm_window_type,
            atoms.net_wm_window_type_dock,
            atoms.net_wm_window_type_desktop,
            atoms.net_wm_window_type_notification,
        ];

        conn.change_property32(
            PropMode::REPLACE,
            root,
            atoms.net_supported,
            AtomEnum::ATOM,
            &supported_atoms,
        )?;

        // 4. Bind Global Sovereign Hotkeys (Super + Key)
        Self::grab_global_keys(&conn, root)?;

        conn.flush()?;

        let mut wm = Self {
            conn,
            root,
            wm_check_win,
            atoms,
            clients: Vec::new(),
            floating_clients: HashSet::new(),
            spawned_children: Vec::new(),
            sidebar_win: None,
            active_client: None,
            sidebar_width: 800,
            screen_width,
            screen_height,
        };

        // 5. Scan and manage pre-existing windows
        wm.scan_existing_windows()?;

        Ok(wm)
    }

    fn grab_global_keys(conn: &RustConnection, root: Window) -> Result<(), Box<dyn std::error::Error>> {
        // Grab specific Super hotkeys cleanly across NumLock (M2) and CapsLock (LOCK) states
        let lock_masks = [
            ModMask::M4,
            ModMask::M4 | ModMask::M2,
            ModMask::M4 | ModMask::LOCK,
            ModMask::M4 | ModMask::M2 | ModMask::LOCK,
        ];
        for keycode in [38u8, 24u8, 36u8] {
            for mods in lock_masks {
                let _ = conn.grab_key(
                    false,
                    root,
                    mods,
                    keycode,
                    GrabMode::ASYNC,
                    GrabMode::ASYNC,
                );
            }
        }

        // Also grab mouse button clicks on clients
        let _ = conn.grab_button(
            false,
            root,
            EventMask::BUTTON_PRESS,
            GrabMode::SYNC,
            GrabMode::ASYNC,
            x11rb::NONE,
            x11rb::NONE,
            ButtonIndex::M1, // Left click
            ModMask::ANY,
        );

        Ok(())
    }

    fn get_window_title(&self, win: Window) -> String {
        if let Ok(cookie) = self.conn.get_property(false, win, self.atoms.net_wm_name, AtomEnum::ANY, 0, 512) {
            if let Ok(reply) = cookie.reply() {
                if !reply.value.is_empty() {
                    return String::from_utf8_lossy(&reply.value).trim_matches('\0').to_string();
                }
            }
        }
        if let Ok(cookie) = self.conn.get_property(false, win, AtomEnum::WM_NAME, AtomEnum::STRING, 0, 512) {
            if let Ok(reply) = cookie.reply() {
                if !reply.value.is_empty() {
                    return String::from_utf8_lossy(&reply.value).trim_matches('\0').to_string();
                }
            }
        }
        String::new()
    }

    fn is_ignored_wm_type(&self, win: Window) -> bool {
        if let Ok(cookie) = self.conn.get_window_attributes(win) {
            if let Ok(reply) = cookie.reply() {
                if reply.override_redirect {
                    return true;
                }
            }
        }
        if let Ok(cookie) = self.conn.get_property(false, win, self.atoms.net_wm_window_type, AtomEnum::ATOM, 0, 16) {
            if let Ok(reply) = cookie.reply() {
                if let Some(iter) = reply.value32() {
                    for atom in iter {
                        if atom == self.atoms.net_wm_window_type_dock
                            || atom == self.atoms.net_wm_window_type_desktop
                            || atom == self.atoms.net_wm_window_type_notification
                        {
                            return true;
                        }
                    }
                }
            }
        }
        false
    }

    fn is_sidebar_window(&self, win: Window) -> bool {
        let title = self.get_window_title(win).to_lowercase();
        title.contains("flowork agent sidebar") || title.contains("floworksidebar") || title.contains("sidebar.html")
    }

    fn is_auth_window(&self, win: Window) -> bool {
        let title = self.get_window_title(win).to_lowercase();
        title.contains("flowork auth")
            || title.contains("sign in - google")
            || title.contains("accounts - google")
            || title.contains("auth.floworkos.com")
            || title.contains("sovereign single sign-on")
    }

    fn scan_existing_windows(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let tree = self.conn.query_tree(self.root)?.reply()?;
        let mut to_manage = Vec::new();

        for &win in &tree.children {
            if win == self.wm_check_win {
                continue;
            }
            if let Ok(cookie) = self.conn.get_window_attributes(win) {
                if let Ok(reply) = cookie.reply() {
                    if reply.map_state == x11rb::protocol::xproto::MapState::VIEWABLE {
                        to_manage.push(win);
                    }
                }
            }
        }

        for win in to_manage {
            let _ = self.manage_window(win);
        }

        self.retile_all()?;
        Ok(())
    }

    fn manage_window(&mut self, win: Window) -> Result<(), Box<dyn std::error::Error>> {
        if win == self.wm_check_win || win == self.root {
            return Ok(());
        }

        // Detect Sidebar before WM type filtering so panel/dock hints never break sidebar docking
        if self.is_sidebar_window(win) {
            println!("  [flowork-wm] 📌 Docking Flowork Agent Sidebar (Window: {})", win);
            self.sidebar_win = Some(win);
            self.apply_sidebar_geometry(win)?;
            return Ok(());
        }

        if self.is_ignored_wm_type(win) {
            let _ = self.conn.map_window(win);
            let _ = self.conn.flush();
            return Ok(());
        }

        // Subscribe to client window events
        let _ = self.conn.change_window_attributes(
            win,
            &ChangeWindowAttributesAux::new().event_mask(
                EventMask::STRUCTURE_NOTIFY | EventMask::PROPERTY_CHANGE | EventMask::FOCUS_CHANGE,
            ),
        );

        // Auto-center floating auth windows without adding them to tiled clients
        if self.is_auth_window(win) {
            println!("  [flowork-wm] ⚡ Auto-raising Sovereign Auth Window (Window: {})", win);
            self.floating_clients.insert(win);
            self.update_client_list_property()?;
            self.center_floating_window(win)?;
            self.focus_window(win)?;
            return Ok(());
        }

        // Add to tiled client list if not present
        if !self.clients.contains(&win) {
            self.clients.push(win);
            self.update_client_list_property()?;
        }

        Ok(())
    }

    fn unmanage_window(&mut self, win: Window) -> Result<(), Box<dyn std::error::Error>> {
        if Some(win) == self.sidebar_win {
            println!("  [flowork-wm] 📌 Flowork Agent Sidebar Unmapped");
            self.sidebar_win = None;
            self.retile_all()?;
            return Ok(());
        }

        if self.floating_clients.remove(&win) {
            self.update_client_list_property()?;
            if self.active_client == Some(win) {
                self.active_client = self.clients.last().copied();
                if let Some(next) = self.active_client {
                    let _ = self.focus_window(next);
                }
            }
            return Ok(());
        }

        if let Some(pos) = self.clients.iter().position(|&w| w == win) {
            self.clients.remove(pos);
            self.update_client_list_property()?;
            if self.active_client == Some(win) {
                self.active_client = self.clients.last().copied();
                if let Some(next) = self.active_client {
                    let _ = self.focus_window(next);
                }
            }
            self.retile_all()?;
        }

        Ok(())
    }

    fn apply_sidebar_geometry(&self, win: Window) -> Result<(), Box<dyn std::error::Error>> {
        let x = (self.screen_width.saturating_sub(self.sidebar_width)) as i32;
        let y = 0;
        let w = self.sidebar_width;
        let h = self.screen_height;

        let _ = self.conn.configure_window(
            win,
            &ConfigureWindowAux::new()
                .x(x)
                .y(y)
                .width(w)
                .height(h)
                .stack_mode(StackMode::ABOVE),
        );
        let _ = self.conn.map_window(win);
        self.conn.flush()?;
        Ok(())
    }

    fn center_floating_window(&self, win: Window) -> Result<(), Box<dyn std::error::Error>> {
        let w = (self.screen_width * 70 / 100).max(640);
        let h = (self.screen_height * 80 / 100).max(480);
        let x = (self.screen_width.saturating_sub(w) / 2) as i32;
        let y = (self.screen_height.saturating_sub(h) / 2) as i32;

        let _ = self.conn.configure_window(
            win,
            &ConfigureWindowAux::new()
                .x(x)
                .y(y)
                .width(w)
                .height(h)
                .stack_mode(StackMode::ABOVE),
        );
        let _ = self.conn.map_window(win);
        self.conn.flush()?;
        Ok(())
    }

    fn retile_all(&self) -> Result<(), Box<dyn std::error::Error>> {
        let canvas_w = if self.sidebar_win.is_some() {
            self.screen_width.saturating_sub(self.sidebar_width)
        } else {
            self.screen_width
        };
        let canvas_h = self.screen_height;

        let client_count = self.clients.len();
        if client_count == 0 {
            return Ok(());
        }

        println!("  [flowork-wm] 🔄 Auto-tiling {} active client window(s) across canvas: {}x{}", client_count, canvas_w, canvas_h);

        match client_count {
            1 => {
                // Single app: Maximize across remaining canvas
                let win = self.clients[0];
                let _ = self.conn.configure_window(
                    win,
                    &ConfigureWindowAux::new()
                        .x(0)
                        .y(0)
                        .width(canvas_w)
                        .height(canvas_h),
                );
            }
            2 => {
                // Two apps: 50/50 Side-by-Side Split
                let half_w = canvas_w / 2;
                // App 1 (Left)
                let _ = self.conn.configure_window(
                    self.clients[0],
                    &ConfigureWindowAux::new().x(0).y(0).width(half_w).height(canvas_h),
                );
                // App 2 (Right)
                let _ = self.conn.configure_window(
                    self.clients[1],
                    &ConfigureWindowAux::new().x(half_w as i32).y(0).width(canvas_w - half_w).height(canvas_h),
                );
            }
            _ => {
                // 3+ apps: Master & Stack layout
                let master_w = (canvas_w * 60 / 100).max(400);
                let stack_w = canvas_w - master_w;
                let stack_count = (client_count - 1) as u32;
                let stack_h = canvas_h / stack_count;

                // Master window
                let _ = self.conn.configure_window(
                    self.clients[0],
                    &ConfigureWindowAux::new().x(0).y(0).width(master_w).height(canvas_h),
                );

                // Stack windows
                for (i, &win) in self.clients.iter().skip(1).enumerate() {
                    let y = (i as u32 * stack_h) as i32;
                    let h = if i as u32 == stack_count - 1 {
                        canvas_h - (i as u32 * stack_h)
                    } else {
                        stack_h
                    };
                    let _ = self.conn.configure_window(
                        win,
                        &ConfigureWindowAux::new().x(master_w as i32).y(y).width(stack_w).height(h),
                    );
                }
            }
        }

        self.conn.flush()?;
        Ok(())
    }

    fn focus_window(&mut self, win: Window) -> Result<(), Box<dyn std::error::Error>> {
        self.active_client = Some(win);
        let _ = self.conn.set_input_focus(
            x11rb::protocol::xproto::InputFocus::POINTER_ROOT,
            win,
            CURRENT_TIME,
        );
        let _ = self.conn.change_property32(
            PropMode::REPLACE,
            self.root,
            self.atoms.net_active_window,
            AtomEnum::WINDOW,
            &[win],
        );
        self.conn.flush()?;
        Ok(())
    }

    fn close_window(&self, win: Window) -> Result<(), Box<dyn std::error::Error>> {
        // Send WM_DELETE_WINDOW client message
        let event = ClientMessageEvent {
            response_type: CLIENT_MESSAGE_EVENT,
            format: 32,
            sequence: 0,
            window: win,
            type_: self.atoms.wm_protocols,
            data: ClientMessageData::from([self.atoms.wm_delete_window, CURRENT_TIME, 0, 0, 0]),
        };

        let _ = self.conn.send_event(false, win, EventMask::NO_EVENT, event);
        self.conn.flush()?;
        Ok(())
    }

    fn update_client_list_property(&self) -> Result<(), Box<dyn std::error::Error>> {
        let mut list = self.clients.clone();
        for &fw in &self.floating_clients {
            if !list.contains(&fw) {
                list.push(fw);
            }
        }
        if let Some(sb) = self.sidebar_win {
            list.push(sb);
        }
        let _ = self.conn.change_property32(
            PropMode::REPLACE,
            self.root,
            self.atoms.net_client_list,
            AtomEnum::WINDOW,
            &list,
        );
        self.conn.flush()?;
        Ok(())
    }

    fn reap_children(&mut self) {
        self.spawned_children
            .retain_mut(|child| !matches!(child.try_wait(), Ok(Some(_)) | Err(_)));
    }

    fn run(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        println!("🚀 [flowork-wm] Sovereign Event Loop running. Awaiting X11 events...");

        loop {
            let event = self.conn.wait_for_event()?;
            self.reap_children();

            match event {
                x11rb::protocol::Event::MapRequest(e) => {
                    println!("  [flowork-wm] 📥 MapRequest for Window {}", e.window);
                    let _ = self.manage_window(e.window);
                    let _ = self.conn.map_window(e.window);
                    if !self.floating_clients.contains(&e.window)
                        && Some(e.window) != self.sidebar_win
                        && self.clients.contains(&e.window)
                    {
                        let _ = self.retile_all();
                        let _ = self.focus_window(e.window);
                    }
                    let _ = self.conn.flush();
                }
                x11rb::protocol::Event::ConfigureRequest(e) => {
                    let mut aux = ConfigureWindowAux::new();
                    if e.value_mask.contains(ConfigWindow::X) {
                        aux = aux.x(e.x as i32);
                    }
                    if e.value_mask.contains(ConfigWindow::Y) {
                        aux = aux.y(e.y as i32);
                    }
                    if e.value_mask.contains(ConfigWindow::WIDTH) {
                        aux = aux.width(e.width as u32);
                    }
                    if e.value_mask.contains(ConfigWindow::HEIGHT) {
                        aux = aux.height(e.height as u32);
                    }
                    if e.value_mask.contains(ConfigWindow::BORDER_WIDTH) {
                        aux = aux.border_width(e.border_width as u32);
                    }
                    if e.value_mask.contains(ConfigWindow::SIBLING) {
                        aux = aux.sibling(e.sibling);
                    }
                    if e.value_mask.contains(ConfigWindow::STACK_MODE) {
                        aux = aux.stack_mode(e.stack_mode);
                    }
                    let _ = self.conn.configure_window(e.window, &aux);
                    let _ = self.conn.flush();
                }
                x11rb::protocol::Event::UnmapNotify(e) => {
                    let _ = self.unmanage_window(e.window);
                }
                x11rb::protocol::Event::DestroyNotify(e) => {
                    let _ = self.unmanage_window(e.window);
                }
                x11rb::protocol::Event::ButtonPress(e) => {
                    if e.child != x11rb::NONE && e.child != self.root {
                        let _ = self.focus_window(e.child);
                        let _ = self.conn.configure_window(
                            e.child,
                            &ConfigureWindowAux::new().stack_mode(StackMode::ABOVE),
                        );
                    }
                    // Allow click to pass through to application
                    let _ = self.conn.allow_events(x11rb::protocol::xproto::Allow::REPLAY_POINTER, CURRENT_TIME);
                    let _ = self.conn.flush();
                }
                x11rb::protocol::Event::KeyPress(e) => {
                    // Hotkey dispatcher:
                    // Super + A: Toggle Flowork Sidebar (Keycode 38)
                    // Super + Q: Close window (Keycode 24)
                    // Super + Return: Launch terminal (Keycode 36)
                    match e.detail {
                        38 => {
                            println!("  [flowork-wm] ⚡ Super+A: Toggling Flowork Sidebar");
                            let sidebar_bin = if std::path::Path::new("/usr/local/bin/flowork-sidebar").exists() {
                                "/usr/local/bin/flowork-sidebar"
                            } else if std::path::Path::new("/opt/floworkos/bin/flowork-sidebar").exists() {
                                "/opt/floworkos/bin/flowork-sidebar"
                            } else {
                                "flowork-sidebar"
                            };
                            if let Ok(child) = Command::new(sidebar_bin).arg("toggle").spawn() {
                                self.spawned_children.push(child);
                            }
                        }
                        24 => {
                            if let Some(active) = self.active_client {
                                println!("  [flowork-wm] ⚡ Super+Q: Closing Active Window {}", active);
                                let _ = self.close_window(active);
                            }
                        }
                        36 => {
                            println!("  [flowork-wm] ⚡ Super+Enter: Launching Sovereign Terminal");
                            let spawned = Command::new("/opt/floworkos/bin/mrflow-terminal").spawn()
                                .or_else(|_| Command::new("alacritty").spawn())
                                .or_else(|_| Command::new("xfce4-terminal").spawn())
                                .or_else(|_| Command::new("gnome-terminal").spawn())
                                .or_else(|_| Command::new("xterm").spawn());
                            if let Ok(child) = spawned {
                                self.spawned_children.push(child);
                            }
                        }
                        _ => {}
                    }
                }
                x11rb::protocol::Event::ClientMessage(e) => {
                    if e.type_ == self.atoms.net_active_window {
                        let _ = self.focus_window(e.window);
                    } else if e.type_ == self.atoms.net_close_window {
                        let _ = self.close_window(e.window);
                    }
                }
                _ => {}
            }
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut wm = FloworkWm::new()?;
    wm.run()
}
