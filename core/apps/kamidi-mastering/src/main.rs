// ==============================================================================
// 👑 FLOWORK OS — SOVEREIGN NATIVE RUST ENGINE: KAMIDI MASTERING PRO (v5.0.10)
// High-Performance Audio Mastering Console & DSP Studio Workstation
// Architecture: Native GTK3 + WebKit2GTK + Embedded HTTP Loopback Daemon
// ==============================================================================

use std::env;
use std::ffi::CString;
use std::fs;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::os::raw::{c_char, c_int, c_void};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, AtomicU16, Ordering};
use std::sync::Arc;
use std::thread;

// --- GTK & WebKit2GTK FFI Declarations ---
type GtkWidget = c_void;
type GtkWindow = c_void;
type WebKitWebView = c_void;
type WebKitSettings = c_void;
type WebKitUserContentManager = c_void;
type WebKitUserScript = c_void;

#[repr(C)]
pub struct GdkRGBA {
    pub red: f64,
    pub green: f64,
    pub blue: f64,
    pub alpha: f64,
}

extern "C" {
    fn gtk_init(argc: *mut c_int, argv: *mut *mut *mut c_char);
    fn gtk_main();
    fn gtk_main_quit();
    fn gtk_window_new(window_type: c_int) -> *mut GtkWidget;
    fn gtk_window_set_title(window: *mut GtkWindow, title: *const c_char);
    fn gtk_window_set_default_size(window: *mut GtkWindow, width: c_int, height: c_int);
    fn gtk_window_set_position(window: *mut GtkWindow, position: c_int);
    fn gtk_window_set_icon_from_file(window: *mut GtkWindow, filename: *const c_char, err: *mut *mut c_void) -> c_int;
    fn gtk_container_add(container: *mut GtkWidget, widget: *mut GtkWidget);
    fn gtk_widget_show_all(widget: *mut GtkWidget);
    fn g_signal_connect_data(
        instance: *mut c_void,
        detailed_signal: *const c_char,
        c_handler: extern "C" fn(*mut c_void, *mut c_void),
        data: *mut c_void,
        destroy_data: *mut c_void,
        connect_flags: c_int,
    ) -> u64;

    fn webkit_web_view_new() -> *mut GtkWidget;
    fn webkit_web_view_load_uri(web_view: *mut WebKitWebView, uri: *const c_char);
    fn webkit_web_view_get_settings(web_view: *mut WebKitWebView) -> *mut WebKitSettings;
    fn webkit_web_view_set_background_color(web_view: *mut WebKitWebView, rgba: *const GdkRGBA);
    fn webkit_web_view_get_user_content_manager(web_view: *mut WebKitWebView) -> *mut WebKitUserContentManager;

    fn webkit_settings_set_enable_javascript(settings: *mut WebKitSettings, enabled: c_int);
    fn webkit_settings_set_enable_webaudio(settings: *mut WebKitSettings, enabled: c_int);
    fn webkit_settings_set_allow_file_access_from_file_urls(settings: *mut WebKitSettings, enabled: c_int);
    fn webkit_settings_set_allow_universal_access_from_file_urls(settings: *mut WebKitSettings, enabled: c_int);
    fn webkit_settings_set_hardware_acceleration_policy(settings: *mut WebKitSettings, policy: c_int);
    fn webkit_settings_set_enable_write_console_messages_to_stdout(settings: *mut WebKitSettings, enabled: c_int);

    fn webkit_user_script_new(
        source: *const c_char,
        injected_frames: c_int,
        injection_time: c_int,
        allow_list: *const *const c_char,
        block_list: *const *const c_char,
    ) -> *mut WebKitUserScript;
    fn webkit_user_content_manager_add_script(manager: *mut WebKitUserContentManager, script: *mut WebKitUserScript);
    fn webkit_user_script_unref(script: *mut WebKitUserScript);
}

extern "C" fn on_window_destroy(_widget: *mut c_void, _data: *mut c_void) {
    unsafe { gtk_main_quit(); }
}

static SERVER_PORT: AtomicU16 = AtomicU16::new(17860);
static IS_RUNNING: AtomicBool = AtomicBool::new(true);

const TAURI_POLYFILL_JS: &str = r#"
(function() {
    console.log('[Kamidi Rust Engine] Initializing sovereign Tauri v2 compatibility layer...');
    
    // Polyfill IPC Bridge
    async function apiRequest(endpoint, payload) {
        const res = await fetch('/api/' + endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const err = await res.text();
            throw new Error(err || 'Server error ' + res.status);
        }
        return await res.json();
    }

    const tauriCore = {
        invoke: async function(cmd, args) {
            return await apiRequest('invoke', { cmd: cmd, args: args || {} });
        },
        convertFileSrc: function(filePath) {
            return '/fs-stream?path=' + encodeURIComponent(filePath);
        }
    };

    const tauriDialog = {
        open: async function(options) {
            return await apiRequest('dialog/open', options || {});
        },
        save: async function(options) {
            return await apiRequest('dialog/save', options || {});
        }
    };

    const tauriFs = {
        readFile: async function(filePath) {
            const res = await fetch('/api/fs/read-binary?path=' + encodeURIComponent(filePath));
            if (!res.ok) throw new Error('Failed to read file: ' + filePath);
            const buf = await res.arrayBuffer();
            return new Uint8Array(buf);
        },
        readTextFile: async function(filePath) {
            const res = await fetch('/api/fs/read-text?path=' + encodeURIComponent(filePath));
            if (!res.ok) throw new Error('Failed to read text file: ' + filePath);
            return await res.text();
        },
        writeFile: async function(filePath, data) {
            let body;
            if (data instanceof Uint8Array || data instanceof ArrayBuffer) {
                body = data;
            } else if (Array.isArray(data)) {
                body = new Uint8Array(data);
            } else {
                body = new TextEncoder().encode(String(data));
            }
            const res = await fetch('/api/fs/write-binary?path=' + encodeURIComponent(filePath), {
                method: 'POST',
                headers: { 'Content-Type': 'application/octet-stream' },
                body: body
            });
            if (!res.ok) throw new Error('Failed to write file: ' + filePath);
            return true;
        },
        writeTextFile: async function(filePath, text) {
            const res = await fetch('/api/fs/write-text?path=' + encodeURIComponent(filePath), {
                method: 'POST',
                headers: { 'Content-Type': 'text/plain; charset=utf-8' },
                body: text
            });
            if (!res.ok) throw new Error('Failed to write text: ' + filePath);
            return true;
        },
        exists: async function(filePath) {
            const res = await apiRequest('fs/exists', { path: filePath });
            return !!res.exists;
        },
        mkdir: async function(dirPath, options) {
            return await apiRequest('fs/mkdir', { path: dirPath, recursive: !!(options && options.recursive) });
        }
    };

    const tauriApp = {
        getVersion: async function() {
            return "5.0.10";
        }
    };

    const tauriPath = {
        appDataDir: async function() {
            const res = await apiRequest('path/app-data', {});
            return res.path;
        }
    };

    const tauriShell = {
        Command: {
            sidecar: function(program, args) {
                return {
                    execute: async function() {
                        return await apiRequest('shell/exec', { program: program, args: args });
                    }
                };
            }
        }
    };

    window.__TAURI__ = {
        core: tauriCore,
        dialog: tauriDialog,
        fs: tauriFs,
        app: tauriApp,
        path: tauriPath,
        shell: tauriShell
    };

    window.__TAURI_INTERNALS__ = {
        invoke: tauriCore.invoke,
        convertFileSrc: tauriCore.convertFileSrc
    };

    console.log('[Kamidi Rust Engine] Tauri v2 bridge active and operational.');
})();
"#;

// --- Embedded Local Micro HTTP Server ---
fn start_http_server(doc_root: PathBuf, requested_port: u16) -> u16 {
    let mut port = requested_port;
    let listener = loop {
        match TcpListener::bind(format!("127.0.0.1:{}", port)) {
            Ok(l) => break l,
            Err(_) => {
                if port == requested_port {
                    // Try to see if existing instance responds
                    if let Ok(mut stream) = TcpStream::connect(format!("127.0.0.1:{}", port)) {
                        let _ = stream.write_all(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n");
                        let mut buf = [0u8; 64];
                        if let Ok(n) = stream.read(&mut buf) {
                            if n > 0 && String::from_utf8_lossy(&buf).contains("200 OK") {
                                SERVER_PORT.store(port, Ordering::SeqCst);
                                return port;
                            }
                        }
                    }
                }
                port += 1;
                if port > requested_port + 20 {
                    panic!("Failed to bind HTTP server port");
                }
            }
        }
    };

    SERVER_PORT.store(port, Ordering::SeqCst);
    let root = Arc::new(doc_root);

    thread::spawn(move || {
        for stream in listener.incoming() {
            if !IS_RUNNING.load(Ordering::SeqCst) {
                break;
            }
            if let Ok(stream) = stream {
                let doc = Arc::clone(&root);
                thread::spawn(move || {
                    handle_http_connection(stream, &doc);
                });
            }
        }
    });

    port
}

fn handle_http_connection(mut stream: TcpStream, doc_root: &Path) {
    let mut buffer = Vec::new();
    let mut temp = [0u8; 8192];
    
    // Read headers
    let mut header_len = 0;
    while let Ok(n) = stream.read(&mut temp) {
        if n == 0 { break; }
        buffer.extend_from_slice(&temp[..n]);
        if let Some(pos) = buffer.windows(4).position(|w| w == b"\r\n\r\n") {
            header_len = pos + 4;
            break;
        }
        if buffer.len() > 65536 { break; }
    }

    if header_len == 0 { return; }

    let req_header_str = String::from_utf8_lossy(&buffer[..header_len]);
    let mut lines = req_header_str.lines();
    let first_line = lines.next().unwrap_or("");
    let mut parts = first_line.split_whitespace();
    let method = parts.next().unwrap_or("GET");
    let full_path = parts.next().unwrap_or("/");

    let url_path = full_path.split('?').next().unwrap_or("/");
    let query_string = if let Some(idx) = full_path.find('?') {
        &full_path[idx + 1..]
    } else {
        ""
    };

    // Parse Content-Length for POST body
    let mut content_length = 0;
    for line in lines {
        let lower = line.to_lowercase();
        if lower.starts_with("content-length:") {
            if let Some(val) = line.split(':').nth(1) {
                content_length = val.trim().parse::<usize>().unwrap_or(0);
            }
        }
    }

    // Read remaining body if POST
    let mut body = buffer[header_len..].to_vec();
    while body.len() < content_length {
        let to_read = (content_length - body.len()).min(temp.len());
        match stream.read(&mut temp[..to_read]) {
            Ok(0) => break,
            Ok(n) => body.extend_from_slice(&temp[..n]),
            Err(_) => break,
        }
    }

    // Route requests
    if url_path == "/health" {
        let resp = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK";
        let _ = stream.write_all(resp.as_bytes());
        return;
    }

    if url_path.starts_with("/api/") {
        handle_api_route(&mut stream, url_path, query_string, &body, doc_root);
        return;
    }

    if url_path == "/fs-stream" {
        handle_file_stream(&mut stream, query_string);
        return;
    }

    // Serve static files
    let rel_path = if url_path == "/" || url_path.is_empty() {
        "index.html"
    } else {
        url_path.trim_start_matches('/')
    };

    let target_file = doc_root.join(rel_path);
    if target_file.is_file() {
        if let Ok(content) = fs::read(&target_file) {
            let mime = get_mime_type(rel_path);
            let header = format!(
                "HTTP/1.1 200 OK\r\nContent-Type: {}\r\nContent-Length: {}\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n",
                mime, content.len()
            );
            let _ = stream.write_all(header.as_bytes());
            let _ = stream.write_all(&content);
            return;
        }
    }

    // 404
    let not_found = "HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\nConnection: close\r\n\r\nNot Found";
    let _ = stream.write_all(not_found.as_bytes());
}

fn get_mime_type(path: &str) -> &'static str {
    if path.ends_with(".html") { "text/html; charset=utf-8" }
    else if path.ends_with(".js") { "application/javascript; charset=utf-8" }
    else if path.ends_with(".css") { "text/css; charset=utf-8" }
    else if path.ends_with(".png") { "image/png" }
    else if path.ends_with(".svg") { "image/svg+xml" }
    else if path.ends_with(".woff2") { "font/woff2" }
    else if path.ends_with(".json") { "application/json; charset=utf-8" }
    else if path.ends_with(".wav") { "audio/wav" }
    else if path.ends_with(".mp3") { "audio/mpeg" }
    else { "application/octet-stream" }
}

fn get_query_param(query: &str, key: &str) -> Option<String> {
    for part in query.split('&') {
        let mut kv = part.split('=');
        if let (Some(k), Some(v)) = (kv.next(), kv.next()) {
            if k == key {
                if let Ok(decoded) = percent_decode(v) {
                    return Some(decoded);
                }
            }
        }
    }
    None
}

fn percent_decode(input: &str) -> Result<String, ()> {
    let mut bytes = Vec::new();
    let mut chars = input.bytes();
    while let Some(b) = chars.next() {
        if b == b'%' {
            let h1 = chars.next().ok_or(())?;
            let h2 = chars.next().ok_or(())?;
            let hex_str = [h1, h2];
            let val = u8::from_str_radix(std::str::from_utf8(&hex_str).map_err(|_| ())?, 16).map_err(|_| ())?;
            bytes.push(val);
        } else if b == b'+' {
            bytes.push(b' ');
        } else {
            bytes.push(b);
        }
    }
    String::from_utf8(bytes).map_err(|_| ())
}

fn handle_file_stream(stream: &mut TcpStream, query_string: &str) {
    if let Some(file_path) = get_query_param(query_string, "path") {
        let p = Path::new(&file_path);
        if p.is_file() {
            if let Ok(data) = fs::read(p) {
                let mime = get_mime_type(&file_path);
                let header = format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: {}\r\nContent-Length: {}\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n",
                    mime, data.len()
                );
                let _ = stream.write_all(header.as_bytes());
                let _ = stream.write_all(&data);
                return;
            }
        }
    }
    let _ = stream.write_all(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n");
}

fn send_json_response(stream: &mut TcpStream, status: &str, json_str: &str) {
    let header = format!(
        "HTTP/1.1 {}\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: {}\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n",
        status, json_str.len()
    );
    let _ = stream.write_all(header.as_bytes());
    let _ = stream.write_all(json_str.as_bytes());
}

fn handle_api_route(stream: &mut TcpStream, path: &str, query_string: &str, body: &[u8], _doc_root: &Path) {
    match path {
        "/api/path/app-data" => {
            let home = env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
            let app_data = format!("{}/.config/KamidiMasteringPro", home);
            let _ = fs::create_dir_all(&app_data);
            send_json_response(stream, "200 OK", &format!("{{\"path\": \"{}\"}}", app_data));
        }
        "/api/fs/exists" => {
            let body_str = String::from_utf8_lossy(body);
            let target_path = extract_json_field(&body_str, "path").unwrap_or_default();
            let exists = Path::new(&target_path).exists();
            send_json_response(stream, "200 OK", &format!("{{\"exists\": {}}}", exists));
        }
        "/api/fs/mkdir" => {
            let body_str = String::from_utf8_lossy(body);
            let target_path = extract_json_field(&body_str, "path").unwrap_or_default();
            let _ = fs::create_dir_all(&target_path);
            send_json_response(stream, "200 OK", "{\"success\": true}");
        }
        "/api/fs/read-text" => {
            if let Some(target_path) = get_query_param(query_string, "path") {
                if let Ok(text) = fs::read_to_string(&target_path) {
                    let header = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: {}\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n",
                        text.len()
                    );
                    let _ = stream.write_all(header.as_bytes());
                    let _ = stream.write_all(text.as_bytes());
                    return;
                }
            }
            send_json_response(stream, "404 Not Found", "{\"error\": \"Not found\"}");
        }
        "/api/fs/read-binary" => {
            if let Some(target_path) = get_query_param(query_string, "path") {
                if let Ok(bytes) = fs::read(&target_path) {
                    let header = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {}\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n",
                        bytes.len()
                    );
                    let _ = stream.write_all(header.as_bytes());
                    let _ = stream.write_all(&bytes);
                    return;
                }
            }
            send_json_response(stream, "404 Not Found", "{\"error\": \"Not found\"}");
        }
        "/api/fs/write-text" => {
            if let Some(target_path) = get_query_param(query_string, "path") {
                if let Some(parent) = Path::new(&target_path).parent() {
                    let _ = fs::create_dir_all(parent);
                }
                if fs::write(&target_path, body).is_ok() {
                    send_json_response(stream, "200 OK", "{\"success\": true}");
                    return;
                }
            }
            send_json_response(stream, "500 Internal Error", "{\"error\": \"Write failed\"}");
        }
        "/api/fs/write-binary" => {
            if let Some(target_path) = get_query_param(query_string, "path") {
                if let Some(parent) = Path::new(&target_path).parent() {
                    let _ = fs::create_dir_all(parent);
                }
                if fs::write(&target_path, body).is_ok() {
                    send_json_response(stream, "200 OK", "{\"success\": true}");
                    return;
                }
            }
            send_json_response(stream, "500 Internal Error", "{\"error\": \"Write failed\"}");
        }
        "/api/dialog/open" => {
            let body_str = String::from_utf8_lossy(body);
            let is_dir = body_str.contains("\"directory\":true") || body_str.contains("\"directory\": true");
            let is_multiple = body_str.contains("\"multiple\":true") || body_str.contains("\"multiple\": true");
            let default_path = extract_json_field(&body_str, "defaultPath").unwrap_or_default();
            
            let mut cmd = Command::new("zenity");
            cmd.arg("--file-selection");
            cmd.env("DISPLAY", env::var("DISPLAY").unwrap_or_else(|_| ":0".to_string()));
            if is_dir {
                cmd.arg("--directory");
                cmd.arg("--title=Pilih Folder Tujuan Export");
            } else {
                cmd.arg("--title=Load Audio Tracks");
                cmd.arg("--file-filter=Audio Files | *.wav *.mp3 *.flac *.ogg *.aac *.m4a *.aiff *.aif *.wma");
                cmd.arg("--file-filter=All Files | *");
            }
            if is_multiple {
                cmd.arg("--multiple").arg("--separator=|");
            }
            if !default_path.is_empty() {
                cmd.arg(format!("--filename={}", default_path));
            }

            match cmd.output() {
                Ok(out) if out.status.success() => {
                    let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
                    if stdout.is_empty() {
                        send_json_response(stream, "200 OK", "null");
                    } else if is_multiple {
                        let parts: Vec<String> = stdout.split('|')
                            .map(|s| s.trim())
                            .filter(|s| !s.is_empty())
                            .map(|s| format!("\"{}\"", s.escape_debug()))
                            .collect();
                        send_json_response(stream, "200 OK", &format!("[{}]", parts.join(",")));
                    } else {
                        send_json_response(stream, "200 OK", &format!("\"{}\"", stdout.escape_debug()));
                    }
                }
                _ => {
                    send_json_response(stream, "200 OK", "null");
                }
            }
        }
        "/api/dialog/save" => {
            let body_str = String::from_utf8_lossy(body);
            let default_path = extract_json_field(&body_str, "defaultPath").unwrap_or_default();
            let title = extract_json_field(&body_str, "title").unwrap_or_else(|| "Export Master Audio".to_string());
            
            let mut cmd = Command::new("zenity");
            cmd.arg("--file-selection").arg("--save").arg("--confirm-overwrite");
            cmd.env("DISPLAY", env::var("DISPLAY").unwrap_or_else(|_| ":0".to_string()));
            cmd.arg(format!("--title={}", title));
            if !default_path.is_empty() {
                cmd.arg(format!("--filename={}", default_path));
            }
            cmd.arg("--file-filter=WAV Audio (*.wav) | *.wav");
            cmd.arg("--file-filter=All Files | *");

            match cmd.output() {
                Ok(out) if out.status.success() => {
                    let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
                    if stdout.is_empty() {
                        send_json_response(stream, "200 OK", "null");
                    } else {
                        send_json_response(stream, "200 OK", &format!("\"{}\"", stdout.escape_debug()));
                    }
                }
                _ => {
                    send_json_response(stream, "200 OK", "null");
                }
            }
        }
        "/api/invoke" => {
            let body_str = String::from_utf8_lossy(body);
            let cmd_name = extract_json_field(&body_str, "cmd").unwrap_or_default();
            match cmd_name.as_str() {
                "bypass_read_dir_presets" => {
                    let folder = extract_json_field(&body_str, "folder").unwrap_or_default();
                    let mut filenames = Vec::new();
                    if let Ok(entries) = fs::read_dir(&folder) {
                        for entry in entries.flatten() {
                            if let Ok(file_type) = entry.file_type() {
                                if file_type.is_file() {
                                    let name = entry.file_name().to_string_lossy().to_string();
                                    if name.ends_with(".json") {
                                        filenames.push(format!("\"{}\"", name.escape_debug()));
                                    }
                                }
                            }
                        }
                    }
                    send_json_response(stream, "200 OK", &format!("[{}]", filenames.join(",")));
                }
                "bypass_read_preset" => {
                    let path = extract_json_field(&body_str, "path").unwrap_or_default();
                    let content = fs::read_to_string(&path).unwrap_or_default();
                    send_json_response(stream, "200 OK", &format!("\"{}\"", content.escape_debug()));
                }
                "bypass_write_preset" => {
                    let path = extract_json_field(&body_str, "path").unwrap_or_default();
                    let content = extract_json_field(&body_str, "content").unwrap_or_default();
                    if let Some(parent) = Path::new(&path).parent() {
                        let _ = fs::create_dir_all(parent);
                    }
                    let _ = fs::write(&path, content);
                    send_json_response(stream, "200 OK", "true");
                }
                "bypass_delete_preset" => {
                    let path = extract_json_field(&body_str, "path").unwrap_or_default();
                    let _ = fs::remove_file(&path);
                    send_json_response(stream, "200 OK", "true");
                }
                _ => {
                    send_json_response(stream, "200 OK", "null");
                }
            }
        }
        "/api/shell/exec" => {
            let body_str = String::from_utf8_lossy(body);
            let mut program = extract_json_field(&body_str, "program").unwrap_or_default();
            if program == "bin/ffmpeg" || program == "ffmpeg" {
                program = "/usr/bin/ffmpeg".to_string();
            }

            // Extract args array
            let args = extract_json_array(&body_str, "args");
            let mut cmd = Command::new(&program);
            cmd.args(&args);
            cmd.stdout(Stdio::piped());
            cmd.stderr(Stdio::piped());

            match cmd.output() {
                Ok(out) => {
                    let code = out.status.code().unwrap_or(0);
                    let stdout = String::from_utf8_lossy(&out.stdout);
                    let stderr = String::from_utf8_lossy(&out.stderr);
                    let resp = format!(
                        "{{\"code\": {}, \"stdout\": \"{}\", \"stderr\": \"{}\"}}",
                        code, stdout.escape_debug(), stderr.escape_debug()
                    );
                    send_json_response(stream, "200 OK", &resp);
                }
                Err(e) => {
                    let resp = format!("{{\"code\": 1, \"stdout\": \"\", \"stderr\": \"{}\"}}", e.to_string().escape_debug());
                    send_json_response(stream, "200 OK", &resp);
                }
            }
        }
        _ => {
            send_json_response(stream, "404 Not Found", "{\"error\": \"Route not found\"}");
        }
    }
}

// Simple JSON extraction helpers
fn extract_json_field(json: &str, field: &str) -> Option<String> {
    let key = format!("\"{}\":", field);
    let key_spaced = format!("\"{}\" :", field);
    let start = json.find(&key).map(|p| p + key.len())
        .or_else(|| json.find(&key_spaced).map(|p| p + key_spaced.len()))?;

    let rest = json[start..].trim_start();
    if rest.starts_with('"') {
        // String value
        let mut result = String::new();
        let mut escaped = false;
        for c in rest[1..].chars() {
            if escaped {
                result.push(c);
                escaped = false;
            } else if c == '\\' {
                escaped = true;
            } else if c == '"' {
                break;
            } else {
                result.push(c);
            }
        }
        Some(result)
    } else {
        // Non-string value (number/bool)
        let end = rest.find(|c| c == ',' || c == '}' || c == ']' || c == '\n').unwrap_or(rest.len());
        Some(rest[..end].trim().to_string())
    }
}

fn extract_json_array(json: &str, field: &str) -> Vec<String> {
    let key = format!("\"{}\":", field);
    let key_spaced = format!("\"{}\" :", field);
    let pos = json.find(&key)
        .or_else(|| json.find(&key_spaced));
    let pos = match pos {
        Some(p) => p,
        None => return Vec::new(),
    };

    let start = match json[pos..].find('[') {
        Some(s) => pos + s + 1,
        None => return Vec::new(),
    };

    let mut items = Vec::new();
    let mut in_str = false;
    let mut escaped = false;
    let mut cur = String::new();

    for c in json[start..].chars() {
        if !in_str {
            if c == '"' {
                in_str = true;
                cur.clear();
            } else if c == ']' {
                break;
            }
        } else {
            if escaped {
                cur.push(c);
                escaped = false;
            } else if c == '\\' {
                escaped = true;
            } else if c == '"' {
                in_str = false;
                items.push(cur.clone());
            } else {
                cur.push(c);
            }
        }
    }
    items
}

// --- Main Application Entry Point ---
fn main() {
    let args: Vec<String> = env::args().collect();

    // 1. Headless Health Check Mode
    if args.iter().any(|a| a == "--check-health" || a == "-c") {
        let gui_dir = Path::new("/opt/floworkos/apps/kamidi-mastering/gui");
        if !gui_dir.join("index.html").is_file() {
            eprintln!("HEALTH_FAIL: gui/index.html not found.");
            std::process::exit(1);
        }
        if !Path::new("/usr/bin/ffmpeg").is_file() {
            eprintln!("HEALTH_FAIL: /usr/bin/ffmpeg not found.");
            std::process::exit(1);
        }
        println!("HEALTH_OK: Kamidi Mastering Pro v5.0.10 native Rust engine & UI operational.");
        std::process::exit(0);
    }

    // 2. Flowork Sovereign WebKit Hardware & Audio Environment Tuning
    env::set_var("WEBKIT_DISABLE_COMPOSITING_MODE", "1");
    env::set_var("LIBGL_ALWAYS_SOFTWARE", "1");

    // 3. Locate GUI Root
    let app_root = PathBuf::from("/opt/floworkos/apps/kamidi-mastering");
    let gui_dir = app_root.join("gui");
    if !gui_dir.exists() {
        eprintln!("Error: GUI directory not found at {}", gui_dir.display());
        std::process::exit(1);
    }

    // 4. Start Embedded High-Speed HTTP Server
    let port = start_http_server(gui_dir, 17860);
    let app_url = format!("http://127.0.0.1:{}/index.html", port);
    println!("[Kamidi Rust] Listening on http://127.0.0.1:{}", port);

    // 5. Initialize GTK3 Window & WebKit
    unsafe {
        gtk_init(std::ptr::null_mut(), std::ptr::null_mut());

        let window = gtk_window_new(0); // GTK_WINDOW_TOPLEVEL = 0
        let title = CString::new("Kamidi Mastering Pro v5.0.10 — Audio Mastering Console").unwrap();
        gtk_window_set_title(window, title.as_ptr());
        gtk_window_set_default_size(window, 1280, 850);
        gtk_window_set_position(window, 1); // GTK_WIN_POS_CENTER = 1

        let icon_path = app_root.join("gui/img/logo.png");
        if icon_path.exists() {
            let c_icon = CString::new(icon_path.to_str().unwrap()).unwrap();
            gtk_window_set_icon_from_file(window, c_icon.as_ptr(), std::ptr::null_mut());
        }

        let web_view = webkit_web_view_new();
        let settings = webkit_web_view_get_settings(web_view);
        webkit_settings_set_enable_javascript(settings, 1);
        webkit_settings_set_enable_webaudio(settings, 1);
        webkit_settings_set_allow_file_access_from_file_urls(settings, 1);
        webkit_settings_set_allow_universal_access_from_file_urls(settings, 1);
        webkit_settings_set_hardware_acceleration_policy(settings, 0); // NEVER policy
        webkit_settings_set_enable_write_console_messages_to_stdout(settings, 0);

        // Obsidian Background Color (#080c10)
        let bg_color = GdkRGBA {
            red: 8.0 / 255.0,
            green: 12.0 / 255.0,
            blue: 16.0 / 255.0,
            alpha: 1.0,
        };
        webkit_web_view_set_background_color(web_view, &bg_color);

        // Inject Tauri Polyfill UserScript at document start
        let content_mgr = webkit_web_view_get_user_content_manager(web_view);
        let polyfill_c = CString::new(TAURI_POLYFILL_JS).unwrap();
        let user_script = webkit_user_script_new(
            polyfill_c.as_ptr(),
            0, // WEBKIT_USER_CONTENT_INJECT_ALL_FRAMES = 0
            0, // WEBKIT_USER_SCRIPT_INJECT_AT_DOCUMENT_START = 0
            std::ptr::null(),
            std::ptr::null(),
        );
        webkit_user_content_manager_add_script(content_mgr, user_script);
        webkit_user_script_unref(user_script);

        // Connect Window Destroy Event
        let destroy_sig = CString::new("destroy").unwrap();
        g_signal_connect_data(
            window as *mut c_void,
            destroy_sig.as_ptr(),
            on_window_destroy,
            std::ptr::null_mut(),
            std::ptr::null_mut(),
            0,
        );

        // Pack WebView into Window
        gtk_container_add(window, web_view);

        // Load Target URL
        let c_url = CString::new(app_url).unwrap();
        webkit_web_view_load_uri(web_view, c_url.as_ptr());

        // Show All
        gtk_widget_show_all(window);

        // Run Event Loop
        gtk_main();
    }

    IS_RUNNING.store(false, Ordering::SeqCst);
}
