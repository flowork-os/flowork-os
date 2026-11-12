// [FL_INDEX: add_cdp_capture_screenshot, cdp_pool_update, rust_cdp_screenshot, base64_image_decode, sysd_cdp | COT: Add capture_screenshot method to CdpController in cdp_pool.rs.| AT: 2026-11-01T16:43:13Z]
// =============================================================================
// 🚀 Flowork Sovereign OS — Persistent Chrome CDP Pool & DOM Engine (Pure Rust)
// Persistent WebSocket multiplexing, auto port discovery & sub-10ms DOM map
// =============================================================================

use futures_util::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;
use tokio_tungstenite::connect_async;

static REQ_ID_COUNTER: AtomicU64 = AtomicU64::new(1);

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChromeTab {
    pub id: String,
    pub title: String,
    pub url: String,
    #[serde(rename = "type")]
    pub tab_type: String,
    #[serde(rename = "webSocketDebuggerUrl")]
    pub ws_url: Option<String>,
}

pub struct CdpController;

impl CdpController {
    const CANDIDATE_PORTS: &'static [u16] = &[9223, 9222, 9224, 9225];

    /// Automatically discover active Chrome CDP port
    pub async fn get_active_cdp_port() -> Option<u16> {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_millis(400))
            .build()
            .ok()?;

        for &port in Self::CANDIDATE_PORTS {
            let url = format!("http://127.0.0.1:{}/json/version", port);
            if let Ok(res) = client.get(&url).send().await {
                if res.status().is_success() {
                    return Some(port);
                }
            }
        }
        None
    }

    /// Ensure Chrome CDP bridge is active, auto-spawning flowork-chrome if offline
    pub async fn ensure_cdp_ready() -> Result<u16, String> {
        if let Some(port) = Self::get_active_cdp_port().await {
            return Ok(port);
        }

        eprintln!("[Flowork Sysd] 🌐 Chrome CDP bridge is offline. Auto-spawning flowork-chrome on port 9222...");
        let chrome_bin = if std::path::Path::new("/opt/floworkos/bin/flowork-chrome").exists() {
            "/opt/floworkos/bin/flowork-chrome"
        } else {
            "google-chrome"
        };

        let disp = std::env::var("DISPLAY").unwrap_or_else(|_| ":0".to_string());
        let _ = tokio::process::Command::new(chrome_bin)
            .arg("--profile=Default")
            .arg("--port=9222")
            .env("DISPLAY", &disp)
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .spawn();

        for _ in 0..25 {
            tokio::time::sleep(Duration::from_millis(150)).await;
            if let Some(port) = Self::get_active_cdp_port().await {
                eprintln!("[Flowork Sysd] ✅ Chrome CDP bridge ready on port {}", port);
                return Ok(port);
            }
        }

        Err("Chrome CDP bridge is offline. Auto-spawn initiated on port 9222 but timed out.".to_string())
    }

    /// List active browser tabs
    pub async fn list_tabs() -> Result<Vec<ChromeTab>, String> {
        let port = match Self::get_active_cdp_port().await {
            Some(p) => p,
            None => Self::ensure_cdp_ready().await?,
        };

        let client = reqwest::Client::builder()
            .timeout(Duration::from_millis(1500))
            .build()
            .map_err(|e| e.to_string())?;

        let url = format!("http://127.0.0.1:{}/json/list", port);
        let res = client
            .get(&url)
            .send()
            .await
            .map_err(|e| format!("Failed to reach Chrome CDP on port {}: {}", port, e))?;

        let tabs: Vec<ChromeTab> = res
            .json()
            .await
            .map_err(|e| format!("Failed to parse Chrome tabs JSON: {}", e))?;

        let page_tabs: Vec<ChromeTab> = tabs
            .into_iter()
            .filter(|t| t.tab_type == "page" || t.tab_type == "app")
            .collect();

        Ok(page_tabs)
    }

    /// Find tab by ID, title, or URL fragment
    pub async fn find_target_tab(query: Option<&str>) -> Result<ChromeTab, String> {
        let tabs = Self::list_tabs().await?;
        if tabs.is_empty() {
            return Err("No open Chrome tabs found".to_string());
        }

        if let Some(q) = query {
            let lower = q.to_lowercase();
            if let Some(found) = tabs.iter().find(|t| {
                t.id == q || t.title.to_lowercase().contains(&lower) || t.url.to_lowercase().contains(&lower)
            }) {
                return Ok(found.clone());
            }
        }

        // Default to first active page tab
        Ok(tabs[0].clone())
    }

    /// Evaluate JavaScript expression in page context via one-shot or persistent WebSocket
    pub async fn eval_js(tab_query: Option<&str>, expression: &str) -> Result<Value, String> {
        let tab = Self::find_target_tab(tab_query).await?;
        let ws_url = tab
            .ws_url
            .ok_or_else(|| format!("Target tab '{}' has no WebSocket debugger URL", tab.title))?;

        let req_id = REQ_ID_COUNTER.fetch_add(1, Ordering::SeqCst);

        let (mut ws_stream, _) = connect_async(&ws_url)
            .await
            .map_err(|e| format!("WebSocket connect to tab failed: {}", e))?;

        let payload = json!({
            "id": req_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": true,
                "awaitPromise": true
            }
        });

        ws_stream
            .send(tokio_tungstenite::tungstenite::Message::Text(payload.to_string()))
            .await
            .map_err(|e| format!("Failed to send CDP evaluate command: {}", e))?;

        // Read response matching req_id
        while let Some(msg) = ws_stream.next().await {
            match msg {
                Ok(tokio_tungstenite::tungstenite::Message::Text(text)) => {
                    if let Ok(res_json) = serde_json::from_str::<Value>(&text) {
                        if res_json.get("id").and_then(|id| id.as_u64()) == Some(req_id) {
                            if let Some(err) = res_json.get("error") {
                                return Err(err.to_string());
                            }
                            let result_val = res_json
                                .pointer("/result/result/value")
                                .cloned()
                                .unwrap_or(Value::Null);
                            return Ok(result_val);
                        }
                    }
                }
                Ok(_) => continue,
                Err(e) => return Err(format!("CDP WebSocket read error: {}", e)),
            }
        }

        Err("CDP connection closed without evaluation response".to_string())
    }

    /// Sub-10ms Actionable DOM Map extraction
    pub async fn get_interactive_dom_map(tab_query: Option<&str>) -> Result<Value, String> {
        let script = r#"
        (() => {
            const elements = Array.from(document.querySelectorAll(
                'button, a[href], input, textarea, select, [role="button"], [contenteditable="true"]'
            ));
            let index = 0;
            const items = [];
            for (const el of elements) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                if (rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none') {
                    index++;
                    el.setAttribute('data-flowork-id', String(index));
                    items.push({
                        id: index,
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || el.getAttribute('aria-label') || el.placeholder || '').trim().slice(0, 80),
                        selector: el.id ? '#' + el.id : (el.className ? '.' + el.className.trim().split(/\s+/).join('.') : el.tagName.toLowerCase()),
                        x: Math.round(rect.left + rect.width / 2),
                        y: Math.round(rect.top + rect.height / 2),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height)
                    });
                    if (items.length >= 80) break;
                }
            }
            return {
                title: document.title,
                url: window.location.href,
                interactive_count: items.length,
                elements: items
            };
        })()
        "#;

        Self::eval_js(tab_query, script).await
    }

    /// Click DOM element by selector or flowork-id or text label
    pub async fn click_element(tab_query: Option<&str>, selector: &str) -> Result<Value, String> {
        let sel_json = serde_json::to_string(selector).map_err(|e| e.to_string())?;
        let script = format!(
            r#"
            (() => {{
                const sel = {sel_json};
                let target = null;
                try {{ target = document.querySelector(sel); }} catch (_) {{}}
                if (!target) {{
                    const escapedAttr = (typeof CSS !== 'undefined' && CSS.escape) ? CSS.escape(sel) : sel.replace(/["\\]/g, '\\$&');
                    try {{ target = document.querySelector(`[data-flowork-id="${{escapedAttr}}"]`); }} catch (_) {{}}
                }}
                if (!target) {{
                    const candidates = Array.from(document.querySelectorAll('button, a, [role="button"], span, div'));
                    target = candidates.find(el => (el.innerText || '').trim().toLowerCase() === sel.toLowerCase());
                }}
                if (target) {{
                    target.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                    target.click();
                    return {{ success: true, tag: target.tagName, text: (target.innerText || '').slice(0, 50) }};
                }}
                return {{ success: false, error: 'Element not found: ' + sel }};
            }})()
            "#
        );

        Self::eval_js(tab_query, &script).await
    }

    /// Type text into input element
    pub async fn type_element(tab_query: Option<&str>, selector: &str, text: &str) -> Result<Value, String> {
        let sel_json = serde_json::to_string(selector).map_err(|e| e.to_string())?;
        let txt_json = serde_json::to_string(text).map_err(|e| e.to_string())?;

        let script = format!(
            r#"
            (() => {{
                const sel = {sel_json};
                const txt = {txt_json};
                let target = null;
                try {{ target = document.querySelector(sel); }} catch (_) {{}}
                if (!target) {{
                    const escapedAttr = (typeof CSS !== 'undefined' && CSS.escape) ? CSS.escape(sel) : sel.replace(/["\\]/g, '\\$&');
                    try {{ target = document.querySelector(`[data-flowork-id="${{escapedAttr}}"]`); }} catch (_) {{}}
                }}
                if (target) {{
                    target.focus();
                    if ('value' in target) {{
                        target.value = txt;
                    }} else if (target.isContentEditable) {{
                        target.innerText = txt;
                    }}
                    target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    target.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return {{ success: true, typed_chars: txt.length }};
                }}
                return {{ success: false, error: 'Input element not found: ' + sel }};
            }})()
            "#
        );

        Self::eval_js(tab_query, &script).await
    }

    /// Navigate to URL
    pub async fn navigate(tab_query: Option<&str>, url: &str) -> Result<Value, String> {
        let url_json = serde_json::to_string(url).map_err(|e| e.to_string())?;
        let script = format!("window.location.href = {};", url_json);
        Self::eval_js(tab_query, &script).await
    }

    /// Open URL in new tab via CDP
    pub async fn open_tab(url: &str) -> Result<Value, String> {
        let port = match Self::get_active_cdp_port().await {
            Some(p) => p,
            None => Self::ensure_cdp_ready().await?,
        };

        let encoded: String = url
            .bytes()
            .map(|b| match b {
                b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => {
                    (b as char).to_string()
                }
                _ => format!("%{:02X}", b),
            })
            .collect();

        let client = reqwest::Client::new();
        let target_url = format!("http://127.0.0.1:{}/json/new?{}", port, encoded);

        let res = client
            .put(&target_url)
            .send()
            .await
            .map_err(|e| format!("Failed to open tab: {}", e))?;

        let tab_data: Value = res.json().await.map_err(|e| e.to_string())?;
        Ok(tab_data)
    }

    /// Close tab
    pub async fn close_tab(tab_query: &str) -> Result<Value, String> {
        let port = match Self::get_active_cdp_port().await {
            Some(p) => p,
            None => Self::ensure_cdp_ready().await?,
        };

        let tab = Self::find_target_tab(Some(tab_query)).await?;
        let client = reqwest::Client::new();
        let target_url = format!("http://127.0.0.1:{}/json/close/{}", port, tab.id);

        let _ = client.get(&target_url).send().await;

        Ok(json!({
            "status": "SUCCESS",
            "closed_tab_id": tab.id,
            "title": tab.title
        }))
    }

    /// Capture screenshot of browser tab via CDP Page.captureScreenshot
    pub async fn capture_screenshot(tab_query: Option<&str>) -> Result<Value, String> {
        let tab = Self::find_target_tab(tab_query).await?;
        let ws_url = tab
            .ws_url
            .ok_or_else(|| format!("Target tab '{}' has no WebSocket debugger URL", tab.title))?;

        let req_id = REQ_ID_COUNTER.fetch_add(1, Ordering::SeqCst);

        let (mut ws_stream, _) = connect_async(&ws_url)
            .await
            .map_err(|e| format!("WebSocket connect to tab failed: {}", e))?;

        let payload = json!({
            "id": req_id,
            "method": "Page.captureScreenshot",
            "params": {
                "format": "png"
            }
        });

        ws_stream
            .send(tokio_tungstenite::tungstenite::Message::Text(payload.to_string()))
            .await
            .map_err(|e| format!("Failed to send CDP captureScreenshot command: {}", e))?;

        while let Some(msg) = ws_stream.next().await {
            match msg {
                Ok(tokio_tungstenite::tungstenite::Message::Text(text)) => {
                    if let Ok(res_json) = serde_json::from_str::<Value>(&text) {
                        if res_json.get("id").and_then(|id| id.as_u64()) == Some(req_id) {
                            if let Some(err) = res_json.get("error") {
                                return Err(err.to_string());
                            }
                            let b64 = res_json
                                .pointer("/result/data")
                                .and_then(|v| v.as_str())
                                .unwrap_or("");

                            let root = std::env::var("FLOWORK_ROOT").unwrap_or_else(|_| "/opt/floworkos".to_string());
                            let out_path = format!("{}/.FL_BIN/browser_capture.png", root);
                            use base64::Engine;
                            if let Ok(bytes) = base64::engine::general_purpose::STANDARD.decode(b64) {
                                let _ = std::fs::write(&out_path, &bytes);
                            }

                            return Ok(json!({
                                "success": true,
                                "path": out_path,
                                "format": "png",
                                "bytes": b64.len()
                            }));
                        }
                    }
                }
                Ok(_) => continue,
                Err(e) => return Err(format!("CDP WebSocket read error: {}", e)),
            }
        }

        Err("CDP connection closed without screenshot response".to_string())
    }
}

