use crate::lifecycle;
use crate::resolve_path_from_cwd;
use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use futures_util::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use std::process::{Command, Stdio};
use std::time::Duration;
use tokio::net::TcpStream;
use tokio_tungstenite::{connect_async, tungstenite::Message, MaybeTlsStream, WebSocketStream};

const BROWSER_STATE_FILE: &str = "/tmp/flowork_browser_state.json";
const DEFAULT_USER_DATA_DIR: &str = "/tmp/flowork_sovereign_browser_profile";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct CachedUidElement {
    pub x: f64,
    pub y: f64,
    pub selector: String,
    pub role: String,
    pub name: String,
    #[serde(default)]
    pub value: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BrowserState {
    #[serde(default)]
    pub selected_page_id: Option<String>,
    #[serde(default)]
    pub cdp_port: Option<u16>,
    #[serde(default)]
    pub uid_map: HashMap<String, CachedUidElement>,
}

fn load_browser_state() -> BrowserState {
    if let Ok(raw) = fs::read_to_string(BROWSER_STATE_FILE) {
        if let Ok(parsed) = serde_json::from_str::<BrowserState>(&raw) {
            return parsed;
        }
    }
    BrowserState::default()
}

fn save_browser_state(st: &BrowserState) {
    if let Ok(raw) = serde_json::to_string_pretty(st) {
        let _ = fs::write(BROWSER_STATE_FILE, raw);
    }
}

pub fn normalize_short_name(tool: &str) -> &str {
    tool.strip_prefix("browser_").unwrap_or(tool)
}

pub fn validate_required_args(short_name: &str, args: &Value) -> Result<(), String> {
    let missing = |field: &str| -> Result<(), String> {
        Err(format!(
            "FLOWORK BROWSER TOOL ERROR: Missing required parameter '{}' for '{}'.",
            field, short_name
        ))
    };
    let has_non_empty_str = |k: &str| {
        args.get(k)
            .and_then(|v| v.as_str())
            .map(|s| !s.trim().is_empty())
            .unwrap_or(false)
    };
    match short_name {
        "click" | "hover" => {
            if !has_non_empty_str("uid") && !args.get("x").is_some() {
                return missing("uid");
            }
        }
        "close_page" | "select_page" => {
            if args.get("pageId").is_none() {
                return missing("pageId");
            }
        }
        "drag" => {
            if !has_non_empty_str("from_uid") {
                return missing("from_uid");
            }
            if !has_non_empty_str("to_uid") {
                return missing("to_uid");
            }
        }
        "evaluate_script" => {
            if !has_non_empty_str("function") {
                return missing("function");
            }
        }
        "fill" => {
            if !has_non_empty_str("uid") {
                return missing("uid");
            }
            if args.get("value").is_none() {
                return missing("value");
            }
        }
        "fill_form" => {
            if !args.get("elements").map(|v| v.is_array()).unwrap_or(false) {
                return missing("elements");
            }
        }
        "get_console_message" => {
            if args.get("msgid").is_none() {
                return missing("msgid");
            }
        }
        "handle_dialog" => {
            if !has_non_empty_str("action") {
                return missing("action");
            }
        }
        "new_page" => {
            if !has_non_empty_str("url") {
                return missing("url");
            }
        }
        "press_key" => {
            if !has_non_empty_str("key") {
                return missing("key");
            }
        }
        "resize_page" => {
            if args.get("width").is_none() {
                return missing("width");
            }
            if args.get("height").is_none() {
                return missing("height");
            }
        }
        "take_memory_snapshot" => {
            if !has_non_empty_str("filePath") {
                return missing("filePath");
            }
        }
        "type_text" => {
            if args.get("text").and_then(|v| v.as_str()).is_none() {
                return missing("text");
            }
        }
        "upload_file" => {
            if !has_non_empty_str("uid") {
                return missing("uid");
            }
            if !has_non_empty_str("filePath") {
                return missing("filePath");
            }
        }
        "wait_for" => {
            let valid = args
                .get("text")
                .map(|v| v.is_array() || v.as_str().map(|s| !s.is_empty()).unwrap_or(false))
                .unwrap_or(false);
            if !valid {
                return missing("text");
            }
        }
        _ => {}
    }
    Ok(())
}

fn candidate_ports() -> Vec<u16> {
    let mut ports = Vec::new();
    if let Ok(p) = std::env::var("FLOWORK_CDP_PORT") {
        if let Ok(num) = p.trim().parse::<u16>() {
            ports.push(num);
        }
    }
    if let Some(saved) = load_browser_state().cdp_port {
        if !ports.contains(&saved) {
            ports.push(saved);
        }
    }
    for p in [9223u16, 9222, 9224, 9225] {
        if !ports.contains(&p) {
            ports.push(p);
        }
    }
    ports
}

async fn find_cdp_base_url(client: &reqwest::Client) -> Option<String> {
    if let Ok(explicit) = std::env::var("FLOWORK_BROWSER_URL") {
        let trimmed = explicit.trim().trim_end_matches('/');
        if !trimmed.is_empty()
            && client
                .get(format!("{}/json/version", trimmed))
                .timeout(Duration::from_millis(800))
                .send()
                .await
                .is_ok()
        {
            return Some(trimmed.to_string());
        }
    }
    for port in candidate_ports() {
        let base = format!("http://127.0.0.1:{}", port);
        if let Ok(resp) = client
            .get(format!("{}/json/version", base))
            .timeout(Duration::from_millis(450))
            .send()
            .await
        {
            if resp.status().is_success() {
                let mut st = load_browser_state();
                st.cdp_port = Some(port);
                save_browser_state(&st);
                return Some(base);
            }
        }
    }
    None
}

fn find_chrome_binary() -> Option<&'static str> {
    [
        "/opt/floworkos/bin/google-chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    .into_iter()
    .find(|&bin| Path::new(bin).is_file())
}

async fn ensure_cdp_base_url(client: &reqwest::Client, user_data_dir: Option<&str>) -> Result<String, String> {
    if let Some(base) = find_cdp_base_url(client).await {
        return Ok(base);
    }

    let bin = find_chrome_binary()
        .ok_or_else(|| "No Chromium/Chrome binary found to launch headless CDP backend".to_string())?;
    let port: u16 = std::env::var("FLOWORK_CDP_PORT")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(9223);
    let profile_dir = user_data_dir.unwrap_or(DEFAULT_USER_DATA_DIR);
    let _ = fs::create_dir_all(profile_dir);

    Command::new(bin)
        .args([
            "--headless=new",
            &format!("--remote-debugging-port={}", port),
            &format!("--user-data-dir={}", profile_dir),
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--no-sandbox",
            "about:blank",
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed spawning headless browser {}: {}", bin, e))?;

    for _ in 0..30 {
        tokio::time::sleep(Duration::from_millis(200)).await;
        if let Some(base) = find_cdp_base_url(client).await {
            return Ok(base);
        }
    }
    Err("Timed out waiting for headless Chrome DevTools Protocol endpoint".to_string())
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CdpTarget {
    pub id: String,
    #[serde(default)]
    pub title: String,
    #[serde(default)]
    pub url: String,
    #[serde(rename = "type", default)]
    pub target_type: String,
    #[serde(default)]
    pub web_socket_debugger_url: Option<String>,
}

async fn fetch_pages(client: &reqwest::Client, base: &str) -> Result<Vec<CdpTarget>, String> {
    let list: Vec<CdpTarget> = client
        .get(format!("{}/json/list", base))
        .timeout(Duration::from_secs(3))
        .send()
        .await
        .map_err(|e| format!("CDP /json/list error: {}", e))?
        .json()
        .await
        .map_err(|e| format!("Invalid /json/list JSON: {}", e))?;
    Ok(list
        .into_iter()
        .filter(|t| t.target_type == "page")
        .collect())
}

fn select_target<'a>(pages: &'a [CdpTarget], state: &BrowserState) -> Option<&'a CdpTarget> {
    if let Some(ref sel_id) = state.selected_page_id {
        if let Some(t) = pages.iter().find(|p| &p.id == sel_id) {
            return Some(t);
        }
        if let Ok(idx) = sel_id.parse::<usize>() {
            if let Some(t) = pages.get(idx) {
                return Some(t);
            }
        }
    }
    pages.first()
}

struct CdpSession {
    ws: WebSocketStream<MaybeTlsStream<TcpStream>>,
    next_id: u64,
    captured_events: Vec<Value>,
}

impl CdpSession {
    async fn connect(ws_url: &str) -> Result<Self, String> {
        let (ws, _) = connect_async(ws_url)
            .await
            .map_err(|e| format!("CDP WebSocket connect error ({}): {}", ws_url, e))?;
        Ok(Self {
            ws,
            next_id: 1,
            captured_events: Vec::new(),
        })
    }

    async fn call(&mut self, method: &str, params: Value) -> Result<Value, String> {
        let id = self.next_id;
        self.next_id += 1;
        let payload = json!({
            "id": id,
            "method": method,
            "params": params
        });
        self.ws
            .send(Message::Text(payload.to_string()))
            .await
            .map_err(|e| format!("CDP send error on {}: {}", method, e))?;

        let deadline = tokio::time::Instant::now() + Duration::from_secs(12);
        while tokio::time::Instant::now() < deadline {
            let msg = match tokio::time::timeout(Duration::from_secs(12), self.ws.next()).await {
                Ok(Some(Ok(m))) => m,
                Ok(Some(Err(e))) => return Err(format!("CDP read error: {}", e)),
                Ok(None) => return Err("CDP WebSocket closed unexpectedly".to_string()),
                Err(_) => return Err(format!("CDP timeout waiting for {}", method)),
            };
            if let Message::Text(txt) = msg {
                if let Ok(val) = serde_json::from_str::<Value>(&txt) {
                    if val.get("id").and_then(|v| v.as_u64()) == Some(id) {
                        if let Some(err) = val.get("error") {
                            return Err(format!("CDP error on {}: {}", method, err));
                        }
                        return Ok(val.get("result").cloned().unwrap_or_else(|| json!({})));
                    } else if val.get("method").is_some() {
                        self.captured_events.push(val);
                    }
                }
            }
        }
        Err(format!("CDP deadline exceeded on {}", method))
    }

    async fn eval_json(&mut self, expr: &str) -> Result<Value, String> {
        let res = self
            .call(
                "Runtime.evaluate",
                json!({
                    "expression": expr,
                    "awaitPromise": true,
                    "returnByValue": true
                }),
            )
            .await?;
        if let Some(exc) = res.get("exceptionDetails") {
            return Err(format!("Page JS exception: {}", exc));
        }
        Ok(res
            .pointer("/result/value")
            .cloned()
            .unwrap_or(Value::Null))
    }
}

async fn get_active_ws_session(
    client: &reqwest::Client,
    base: &str,
) -> Result<(CdpTarget, CdpSession, Vec<CdpTarget>), String> {
    let mut pages = fetch_pages(client, base).await?;
    if pages.is_empty() {
        let _ = client
            .put(format!("{}/json/new?about:blank", base))
            .send()
            .await;
        pages = fetch_pages(client, base).await?;
    }
    let st = load_browser_state();
    let target = select_target(&pages, &st)
        .ok_or_else(|| "No browser page target available".to_string())?
        .clone();
    let ws_url = target
        .web_socket_debugger_url
        .clone()
        .ok_or_else(|| format!("Target {} has no webSocketDebuggerUrl", target.id))?;
    let session = CdpSession::connect(&ws_url).await?;
    Ok((target, session, pages))
}

async fn capture_dom_snapshot(session: &mut CdpSession) -> Result<(String, HashMap<String, CachedUidElement>), String> {
    let script = r#"(() => {
        const els = Array.from(document.querySelectorAll('a,button,input,textarea,select,[role],[tabindex],h1,h2,h3,label'));
        const items = [];
        let idx = 1;
        for (const el of els) {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden') continue;
            if (rect.width === 0 && rect.height === 0 && el.tagName !== 'INPUT') continue;
            const uid = 'e' + idx++;
            el.setAttribute('data-flowork-uid', uid);
            const role = el.getAttribute('role') || el.tagName.toLowerCase();
            const name = (el.getAttribute('aria-label') || el.innerText || el.placeholder || el.value || el.name || '').trim().replace(/\s+/g, ' ').slice(0, 120);
            const val = el.value !== undefined ? String(el.value).slice(0, 80) : '';
            items.push({
                uid,
                role,
                name,
                value: val,
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
                selector: `[data-flowork-uid="${uid}"]`
            });
            if (items.length >= 200) break;
        }
        return {
            title: document.title,
            url: location.href,
            items
        };
    })()"#;
    let val = session.eval_json(script).await?;
    let title = val.get("title").and_then(|v| v.as_str()).unwrap_or("");
    let url = val.get("url").and_then(|v| v.as_str()).unwrap_or("");
    let mut uid_map = HashMap::new();
    let mut lines = vec![format!("RootPage title={:?} url={:?}", title, url)];
    if let Some(arr) = val.get("items").and_then(|v| v.as_array()) {
        for item in arr {
            let uid = item.get("uid").and_then(|v| v.as_str()).unwrap_or("").to_string();
            let role = item.get("role").and_then(|v| v.as_str()).unwrap_or("").to_string();
            let name = item.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string();
            let value = item.get("value").and_then(|v| v.as_str()).unwrap_or("").to_string();
            let x = item.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
            let y = item.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
            let selector = item.get("selector").and_then(|v| v.as_str()).unwrap_or("").to_string();
            lines.push(format!("  uid={} {} {:?}", uid, role, name));
            uid_map.insert(
                uid,
                CachedUidElement {
                    x,
                    y,
                    selector,
                    role,
                    name,
                    value,
                },
            );
        }
    }
    Ok((lines.join("\n"), uid_map))
}

async fn resolve_uid_coords(session: &mut CdpSession, uid: &str) -> Result<(f64, f64), String> {
    let script = format!(
        r#"(() => {{
            const el = document.querySelector('[data-flowork-uid="{}"]') || document.getElementById('{}');
            if (!el) return null;
            el.scrollIntoView({{block:'center',inline:'center'}});
            const r = el.getBoundingClientRect();
            return {{ x: r.left + r.width / 2, y: r.top + r.height / 2 }};
        }})()"#,
        uid.replace('"', ""),
        uid.replace('"', "")
    );
    if let Ok(v) = session.eval_json(&script).await {
        if let (Some(x), Some(y)) = (v.get("x").and_then(|n| n.as_f64()), v.get("y").and_then(|n| n.as_f64())) {
            return Ok((x, y));
        }
    }
    let st = load_browser_state();
    if let Some(el) = st.uid_map.get(uid) {
        return Ok((el.x, el.y));
    }
    Err(format!("Element uid '{}' not found in active page or snapshot cache", uid))
}

fn parse_key_combo(combo: &str) -> (u32, String) {
    let mut modifiers = 0u32;
    let parts: Vec<&str> = combo.split('+').collect();
    let main_key = parts.last().copied().unwrap_or(combo).to_string();
    for p in &parts[..parts.len().saturating_sub(1)] {
        match p.trim().to_ascii_lowercase().as_str() {
            "alt" => modifiers |= 1,
            "control" | "ctrl" => modifiers |= 2,
            "meta" | "cmd" | "super" => modifiers |= 4,
            "shift" => modifiers |= 8,
            _ => {}
        }
    }
    (modifiers, main_key)
}

pub async fn call_browser_tool(
    tool_name: &str,
    args: &Value,
    user_data_dir: Option<&str>,
) -> Result<Value, String> {
    let short = normalize_short_name(tool_name);
    validate_required_args(short, args)?;

    let client = reqwest::Client::new();
    let base = ensure_cdp_base_url(&client, user_data_dir).await?;

    let result_json = match short {
        "list_pages" => {
            let pages = fetch_pages(&client, &base).await?;
            let formatted: Vec<Value> = pages
                .iter()
                .enumerate()
                .map(|(i, p)| {
                    json!({
                        "pageId": i,
                        "targetId": p.id,
                        "title": p.title,
                        "url": p.url
                    })
                })
                .collect();
            json!({
                "content": [{
                    "type": "text",
                    "text": serde_json::to_string_pretty(&formatted).unwrap_or_default()
                }],
                "pages": formatted
            })
        }
        "new_page" => {
            let url = args.get("url").and_then(|v| v.as_str()).unwrap_or("about:blank");
            crate::ssrf::validate_browser_url_dns(url, true).await?;
            let encoded = urlencoding::encode(url);
            let resp = client
                .put(format!("{}/json/new?{}", base, encoded))
                .timeout(Duration::from_secs(5))
                .send()
                .await
                .map_err(|e| format!("CDP new_page failed: {}", e))?;
            let target: CdpTarget = resp
                .json()
                .await
                .map_err(|e| format!("Invalid new_page target response: {}", e))?;
            let mut st = load_browser_state();
            st.selected_page_id = Some(target.id.clone());
            save_browser_state(&st);
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Opened new page {} -> {}", target.id, target.url)
                }],
                "targetId": target.id,
                "url": target.url
            })
        }
        "close_page" => {
            let pages = fetch_pages(&client, &base).await?;
            let target_id = if let Some(idx) = args.get("pageId").and_then(|v| v.as_u64()) {
                pages
                    .get(idx as usize)
                    .map(|p| p.id.clone())
                    .unwrap_or_else(|| idx.to_string())
            } else {
                args.get("pageId")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string()
            };
            let resp = client
                .get(format!("{}/json/close/{}", base, target_id))
                .timeout(Duration::from_secs(4))
                .send()
                .await
                .map_err(|e| format!("CDP close_page failed: {}", e))?;
            let txt = resp.text().await.unwrap_or_default();
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Closed page {}: {}", target_id, txt)
                }]
            })
        }
        "select_page" => {
            let pages = fetch_pages(&client, &base).await?;
            let sel = if let Some(idx) = args.get("pageId").and_then(|v| v.as_u64()) {
                pages
                    .get(idx as usize)
                    .map(|p| p.id.clone())
                    .ok_or_else(|| format!("Page index {} out of range", idx))?
            } else {
                args.get("pageId")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string()
            };
            let _ = client
                .get(format!("{}/json/activate/{}", base, sel))
                .timeout(Duration::from_secs(3))
                .send()
                .await;
            let mut st = load_browser_state();
            st.selected_page_id = Some(sel.clone());
            save_browser_state(&st);
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Selected page {}", sel)
                }]
            })
        }
        "navigate_page" => {
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let nav_type = args.get("type").and_then(|v| v.as_str()).unwrap_or("url");
            match nav_type {
                "reload" => {
                    let ignore = args.get("ignoreCache").and_then(|v| v.as_bool()).unwrap_or(false);
                    session.call("Page.reload", json!({ "ignoreCache": ignore })).await?;
                }
                "back" => {
                    session.eval_json("history.back()").await?;
                }
                "forward" => {
                    session.eval_json("history.forward()").await?;
                }
                _ => {
                    let url = args
                        .get("url")
                        .and_then(|v| v.as_str())
                        .ok_or_else(|| "navigate_page with type=url requires 'url'".to_string())?;
                    crate::ssrf::validate_browser_url_dns(url, false).await?;
                    session.call("Page.enable", json!({})).await?;
                    session.call("Page.navigate", json!({ "url": url })).await?;
                }
            }
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Navigation '{}' dispatched", nav_type)
                }]
            })
        }
        "take_snapshot" => {
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let (text_snap, uid_map) = capture_dom_snapshot(&mut session).await?;
            let mut st = load_browser_state();
            st.uid_map = uid_map;
            save_browser_state(&st);
            if let Some(fp) = args.get("filePath").and_then(|v| v.as_str()) {
                let cwd = std::env::current_dir().unwrap_or_else(|_| Path::new("/tmp").to_path_buf());
                let resolved = resolve_path_from_cwd(fp, &cwd);
                fs::write(&resolved, &text_snap)
                    .map_err(|e| format!("Failed writing snapshot to {:?}: {}", resolved, e))?;
                json!({
                    "content": [{
                        "type": "text",
                        "text": format!("Snapshot written to {}", resolved.display())
                    }]
                })
            } else {
                json!({
                    "content": [{
                        "type": "text",
                        "text": text_snap
                    }]
                })
            }
        }
        "click" => {
            let uid = args.get("uid").and_then(|v| v.as_str()).unwrap_or("");
            let dbl = args.get("dblClick").and_then(|v| v.as_bool()).unwrap_or(false);
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let (x, y) = if !uid.is_empty() {
                resolve_uid_coords(&mut session, uid).await?
            } else {
                (
                    args.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0),
                    args.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0),
                )
            };
            let click_count = if dbl { 2 } else { 1 };
            session.call("Input.dispatchMouseEvent", json!({"type":"mouseMoved","x":x,"y":y})).await?;
            session.call("Input.dispatchMouseEvent", json!({"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":click_count})).await?;
            session.call("Input.dispatchMouseEvent", json!({"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":click_count})).await?;
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Clicked '{}' at ({:.1}, {:.1})", uid, x, y)
                }]
            })
        }
        "hover" => {
            let uid = args.get("uid").and_then(|v| v.as_str()).unwrap_or("");
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let (x, y) = resolve_uid_coords(&mut session, uid).await?;
            session.call("Input.dispatchMouseEvent", json!({"type":"mouseMoved","x":x,"y":y})).await?;
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Hovered '{}' at ({:.1}, {:.1})", uid, x, y)
                }]
            })
        }
        "drag" => {
            let from_uid = args.get("from_uid").and_then(|v| v.as_str()).unwrap_or("");
            let to_uid = args.get("to_uid").and_then(|v| v.as_str()).unwrap_or("");
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let (fx, fy) = resolve_uid_coords(&mut session, from_uid).await?;
            let (tx, ty) = resolve_uid_coords(&mut session, to_uid).await?;
            session.call("Input.dispatchMouseEvent", json!({"type":"mouseMoved","x":fx,"y":fy})).await?;
            session.call("Input.dispatchMouseEvent", json!({"type":"mousePressed","x":fx,"y":fy,"button":"left","clickCount":1})).await?;
            session.call("Input.dispatchMouseEvent", json!({"type":"mouseMoved","x":tx,"y":ty,"button":"left"})).await?;
            session.call("Input.dispatchMouseEvent", json!({"type":"mouseReleased","x":tx,"y":ty,"button":"left","clickCount":1})).await?;
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Dragged '{}' -> '{}'", from_uid, to_uid)
                }]
            })
        }
        "fill" => {
            let uid = args.get("uid").and_then(|v| v.as_str()).unwrap_or("");
            let value = args
                .get("value")
                .map(|v| v.as_str().map(str::to_string).unwrap_or_else(|| v.to_string()))
                .unwrap_or_default();
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let script = format!(
                r#"(() => {{
                    const el = document.querySelector('[data-flowork-uid="{}"]');
                    if (!el) return false;
                    el.focus();
                    el.value = {};
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }})()"#,
                uid.replace('"', ""),
                serde_json::to_string(&value).unwrap_or_else(|_| "\"\"".to_string())
            );
            let ok = session.eval_json(&script).await?;
            if ok != Value::Bool(true) {
                let (x, y) = resolve_uid_coords(&mut session, uid).await?;
                session.call("Input.dispatchMouseEvent", json!({"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})).await?;
                session.call("Input.dispatchMouseEvent", json!({"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})).await?;
                session.call("Input.insertText", json!({"text": value})).await?;
            }
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Filled '{}' successfully", uid)
                }]
            })
        }
        "fill_form" => {
            let elements = args
                .get("elements")
                .and_then(|v| v.as_array())
                .cloned()
                .unwrap_or_default();
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            for item in &elements {
                let uid = item.get("uid").and_then(|v| v.as_str()).unwrap_or("");
                let val = item
                    .get("value")
                    .map(|v| v.as_str().map(str::to_string).unwrap_or_else(|| v.to_string()))
                    .unwrap_or_default();
                let script = format!(
                    r#"(() => {{
                        const el = document.querySelector('[data-flowork-uid="{}"]');
                        if (!el) return false;
                        el.focus();
                        el.value = {};
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }})()"#,
                    uid.replace('"', ""),
                    serde_json::to_string(&val).unwrap_or_else(|_| "\"\"".to_string())
                );
                let _ = session.eval_json(&script).await;
            }
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Filled {} form field(s)", elements.len())
                }]
            })
        }
        "type_text" => {
            let text = args.get("text").and_then(|v| v.as_str()).unwrap_or("");
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            session.call("Input.insertText", json!({ "text": text })).await?;
            if let Some(key) = args.get("submitKey").and_then(|v| v.as_str()) {
                session.call("Input.dispatchKeyEvent", json!({"type":"keyDown","key":key})).await?;
                session.call("Input.dispatchKeyEvent", json!({"type":"keyUp","key":key})).await?;
            }
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Typed {} character(s)", text.len())
                }]
            })
        }
        "press_key" => {
            let combo = args.get("key").and_then(|v| v.as_str()).unwrap_or("");
            let (mods, key) = parse_key_combo(combo);
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            session.call("Input.dispatchKeyEvent", json!({"type":"keyDown","modifiers":mods,"key":key})).await?;
            session.call("Input.dispatchKeyEvent", json!({"type":"keyUp","modifiers":mods,"key":key})).await?;
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Pressed key '{}'", combo)
                }]
            })
        }
        "evaluate_script" => {
            let func_src = args.get("function").and_then(|v| v.as_str()).unwrap_or("() => null");
            let fn_args = args.get("args").cloned().unwrap_or_else(|| json!([]));
            let expr = format!(
                "({})(...{})",
                func_src.trim(),
                serde_json::to_string(&fn_args).unwrap_or_else(|_| "[]".to_string())
            );
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let val = session.eval_json(&expr).await?;
            json!({
                "content": [{
                    "type": "text",
                    "text": serde_json::to_string_pretty(&val).unwrap_or_else(|_| "null".to_string())
                }],
                "value": val
            })
        }
        "take_screenshot" => {
            let fmt = args.get("format").and_then(|v| v.as_str()).unwrap_or("png");
            let mut params = json!({ "format": fmt });
            if let Some(q) = args.get("quality").and_then(|v| v.as_u64()) {
                params["quality"] = json!(q);
            }
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            if args.get("fullPage").and_then(|v| v.as_bool()) == Some(true) {
                params["captureBeyondViewport"] = json!(true);
            }
            let res = session.call("Page.captureScreenshot", params).await?;
            let b64 = res.get("data").and_then(|v| v.as_str()).unwrap_or("");
            if let Some(fp) = args.get("filePath").and_then(|v| v.as_str()) {
                let raw = B64
                    .decode(b64)
                    .map_err(|e| format!("Failed decoding screenshot base64: {}", e))?;
                let cwd = std::env::current_dir().unwrap_or_else(|_| Path::new("/tmp").to_path_buf());
                let resolved = resolve_path_from_cwd(fp, &cwd);
                fs::write(&resolved, &raw)
                    .map_err(|e| format!("Failed writing screenshot to {:?}: {}", resolved, e))?;
                json!({
                    "content": [{
                        "type": "text",
                        "text": format!("Screenshot saved to {} ({} bytes)", resolved.display(), raw.len())
                    }]
                })
            } else {
                json!({
                    "content": [{
                        "type": "image",
                        "mimeType": format!("image/{}", fmt),
                        "data": b64
                    }]
                })
            }
        }
        "resize_page" => {
            let w = args.get("width").and_then(|v| v.as_u64()).unwrap_or(1280);
            let h = args.get("height").and_then(|v| v.as_u64()).unwrap_or(800);
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            session
                .call(
                    "Emulation.setDeviceMetricsOverride",
                    json!({"width": w, "height": h, "deviceScaleFactor": 1, "mobile": false}),
                )
                .await?;
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Resized viewport to {}x{}", w, h)
                }]
            })
        }
        "emulate" => {
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            if let Some(ua) = args.get("userAgent").and_then(|v| v.as_str()) {
                session
                    .call("Emulation.setUserAgentOverride", json!({ "userAgent": ua }))
                    .await?;
            }
            if let Some(rate) = args.get("cpuThrottlingRate").and_then(|v| v.as_f64()) {
                session
                    .call("Emulation.setCPUThrottlingRate", json!({ "rate": rate }))
                    .await?;
            }
            if let Some(scheme) = args.get("colorScheme").and_then(|v| v.as_str()) {
                session
                    .call(
                        "Emulation.setEmulatedMedia",
                        json!({"features": [{"name": "prefers-color-scheme", "value": scheme}]}),
                    )
                    .await?;
            }
            if let Some(vp) = args.get("viewport").and_then(|v| v.as_object()) {
                let w = vp.get("width").and_then(|v| v.as_u64()).unwrap_or(1280);
                let h = vp.get("height").and_then(|v| v.as_u64()).unwrap_or(800);
                let mobile = vp.get("isMobile").and_then(|v| v.as_bool()).unwrap_or(false);
                session
                    .call(
                        "Emulation.setDeviceMetricsOverride",
                        json!({"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}),
                    )
                    .await?;
            }
            json!({
                "content": [{
                    "type": "text",
                    "text": "Emulation parameters applied"
                }]
            })
        }
        "wait_for" => {
            let targets: Vec<String> = match args.get("text") {
                Some(Value::Array(arr)) => arr
                    .iter()
                    .filter_map(|v| v.as_str().map(str::to_string))
                    .collect(),
                Some(Value::String(s)) => vec![s.clone()],
                _ => Vec::new(),
            };
            let timeout_ms = args.get("timeout").and_then(|v| v.as_u64()).unwrap_or(10_000).max(500);
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let deadline = tokio::time::Instant::now() + Duration::from_millis(timeout_ms);
            let mut matched = None;
            while tokio::time::Instant::now() < deadline {
                if let Ok(Value::String(body)) = session.eval_json("document.body ? document.body.innerText : ''").await {
                    if let Some(found) = targets.iter().find(|t| body.contains(t.as_str())) {
                        matched = Some(found.clone());
                        break;
                    }
                }
                tokio::time::sleep(Duration::from_millis(250)).await;
            }
            if let Some(m) = matched {
                json!({
                    "content": [{
                        "type": "text",
                        "text": format!("Found expected text '{}'", m)
                    }]
                })
            } else {
                return Err(format!("Timed out waiting for text {:?}", targets));
            }
        }
        "handle_dialog" => {
            let action = args.get("action").and_then(|v| v.as_str()).unwrap_or("accept");
            let accept = action == "accept";
            let prompt_text = args.get("promptText").and_then(|v| v.as_str());
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let mut params = json!({ "accept": accept });
            if let Some(pt) = prompt_text {
                params["promptText"] = json!(pt);
            }
            let _ = session.call("Page.handleJavaScriptDialog", params).await;
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Dialog action '{}' dispatched", action)
                }]
            })
        }
        "upload_file" => {
            let uid = args.get("uid").and_then(|v| v.as_str()).unwrap_or("");
            let file_path = args.get("filePath").and_then(|v| v.as_str()).unwrap_or("");
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            session.call("DOM.enable", json!({})).await?;
            let doc = session.call("DOM.getDocument", json!({ "depth": 0 })).await?;
            let root_id = doc.pointer("/root/nodeId").and_then(|v| v.as_i64()).unwrap_or(1);
            let q = session
                .call(
                    "DOM.querySelector",
                    json!({ "nodeId": root_id, "selector": format!("[data-flowork-uid=\"{}\"]", uid.replace('"', "")) }),
                )
                .await?;
            let node_id = q.get("nodeId").and_then(|v| v.as_i64()).unwrap_or(0);
            if node_id <= 0 {
                return Err(format!("File input uid '{}' not found in DOM", uid));
            }
            session
                .call(
                    "DOM.setFileInputFiles",
                    json!({ "nodeId": node_id, "files": [file_path] }),
                )
                .await?;
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Uploaded '{}' to uid '{}'", file_path, uid)
                }]
            })
        }
        "list_console_messages" | "get_console_message" => {
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let _ = session.call("Runtime.enable", json!({})).await;
            let _ = session.call("Log.enable", json!({})).await;
            let entries: Vec<Value> = session
                .captured_events
                .iter()
                .filter(|e| {
                    let m = e.get("method").and_then(|v| v.as_str()).unwrap_or("");
                    m.starts_with("Runtime.console") || m.starts_with("Log.entry")
                })
                .cloned()
                .collect();
            json!({
                "content": [{
                    "type": "text",
                    "text": serde_json::to_string_pretty(&entries).unwrap_or_else(|_| "[]".to_string())
                }]
            })
        }
        "list_network_requests" | "get_network_request" => {
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            let entries = session
                .eval_json("performance.getEntriesByType('resource').map((r,i)=>({reqid:i+1,name:r.name,initiatorType:r.initiatorType,duration:Math.round(r.duration),transferSize:r.transferSize||0}))")
                .await
                .unwrap_or_else(|_| json!([]));
            json!({
                "content": [{
                    "type": "text",
                    "text": serde_json::to_string_pretty(&entries).unwrap_or_else(|_| "[]".to_string())
                }]
            })
        }
        "take_memory_snapshot" => {
            let fp = args.get("filePath").and_then(|v| v.as_str()).unwrap_or("");
            let cwd = std::env::current_dir().unwrap_or_else(|_| Path::new("/tmp").to_path_buf());
            let resolved = resolve_path_from_cwd(fp, &cwd);
            let (_t, mut session, _pages) = get_active_ws_session(&client, &base).await?;
            session.call("HeapProfiler.enable", json!({})).await?;
            session
                .call(
                    "HeapProfiler.takeHeapSnapshot",
                    json!({ "reportProgress": false }),
                )
                .await?;
            let mut buf = String::new();
            for ev in &session.captured_events {
                if ev.get("method").and_then(|v| v.as_str()) == Some("HeapProfiler.addHeapSnapshotChunk") {
                    if let Some(chunk) = ev.pointer("/params/chunk").and_then(|v| v.as_str()) {
                        buf.push_str(chunk);
                    }
                }
            }
            fs::write(&resolved, &buf)
                .map_err(|e| format!("Failed saving heapsnapshot {:?}: {}", resolved, e))?;
            json!({
                "content": [{
                    "type": "text",
                    "text": format!("Heap snapshot saved to {} ({} bytes)", resolved.display(), buf.len())
                }]
            })
        }
        other => return Err(format!("Unsupported browser tool '{}'", other)),
    };

    let full_name = if tool_name.starts_with("browser_") {
        tool_name.to_string()
    } else {
        format!("browser_{}", short)
    };
    lifecycle::on_tool_executed(
        &full_name,
        &json!({
            "reason": format!("Executed browser tool {}", short),
            "keywords": ["browser", "web", "page", "dom", short]
        }),
    );

    Ok(result_json)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validates_required_browser_tool_arguments_before_cdp() {
        assert!(validate_required_args("click", &json!({})).is_err());
        assert!(validate_required_args("click", &json!({"uid": "e1"})).is_ok());
        assert!(validate_required_args("new_page", &json!({})).is_err());
        assert!(validate_required_args("new_page", &json!({"url": "https://floworkos.com"})).is_ok());
        assert!(validate_required_args("wait_for", &json!({})).is_err());
        assert!(validate_required_args("wait_for", &json!({"text": ["OK"]})).is_ok());
    }
}
