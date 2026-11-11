use crate::config::{AppConfig, McpServerConfig};
use crate::inference::ToolDeclaration;
use futures_util::StreamExt;
use reqwest::Client;
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::atomic::{AtomicI64, Ordering};
use std::sync::Arc;
use std::time::Duration;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, Command};
use tokio::sync::{oneshot, Mutex};
use tokio::time::timeout;

#[derive(Debug, Clone)]
pub struct McpDiscoveredTool {
    pub server_name: String,
    pub tool_name: String,
    pub qualified_name: String,
    pub description: String,
    pub parameters_schema: Value,
}

#[derive(Debug, Clone)]
pub struct McpResourceInfo {
    pub server: String,
    pub uri: String,
    pub name: String,
    pub mime_type: Option<String>,
}

#[derive(Debug, Clone)]
pub struct McpPromptInfo {
    pub server: String,
    pub name: String,
    pub description: Option<String>,
    pub arguments: Vec<Value>,
}

#[derive(Debug, Clone)]
pub struct McpServerStatus {
    pub name: String,
    pub transport: String,
    pub tool_count: usize,
    pub trusted: bool,
}

type PendingMap = Arc<Mutex<HashMap<i64, oneshot::Sender<Result<Value, String>>>>>;

enum McpTransport {
    Stdio {
        stdin: Arc<Mutex<ChildStdin>>,
        pending: PendingMap,
        child_pid: Option<u32>,
        child: Arc<Mutex<Option<Child>>>,
    },
    StreamableHttp {
        http: Client,
        endpoint: String,
        headers: HashMap<String, String>,
        session_id: Arc<Mutex<Option<String>>>,
    },
    Sse {
        http: Client,
        post_endpoint: Arc<Mutex<String>>,
        headers: HashMap<String, String>,
        pending: PendingMap,
        reader_task: Arc<Mutex<Option<tokio::task::JoinHandle<()>>>>,
    },
}

struct McpClientHandle {
    server_name: String,
    transport_kind: &'static str,
    trusted: bool,
    default_timeout: Duration,
    transport: McpTransport,
    next_id: AtomicI64,
}

impl McpClientHandle {
    async fn connect(
        server_name: String,
        cfg: McpServerConfig,
        workspace_cwd: PathBuf,
    ) -> Result<(Self, Vec<McpDiscoveredTool>), String> {
        let timeout_ms = cfg.timeout.unwrap_or(60_000).clamp(2_000, 300_000);
        let default_timeout = Duration::from_millis(timeout_ms);
        let init_timeout = Duration::from_millis(timeout_ms.clamp(4_000, 15_000));

        // Expand ${VAR} and ${VAR:-default} in env first so later fields can reference them too
        let mut expanded_env: HashMap<String, String> = HashMap::new();
        for (k, v) in &cfg.env {
            expanded_env.insert(
                k.clone(),
                expand_env_vars(v, None, Some(&workspace_cwd)),
            );
        }

        let expanded_headers: HashMap<String, String> = cfg
            .headers
            .iter()
            .map(|(k, v)| {
                (
                    k.clone(),
                    expand_env_vars(v, Some(&expanded_env), Some(&workspace_cwd)),
                )
            })
            .collect();

        let ttype_lower = cfg
            .transport_type
            .as_deref()
            .map(|s| s.trim().to_ascii_lowercase())
            .unwrap_or_default();

        let raw_http_url = cfg
            .http_url
            .as_deref()
            .map(|s| expand_env_vars(s, Some(&expanded_env), Some(&workspace_cwd)))
            .filter(|s| !s.trim().is_empty());
        let raw_url = cfg
            .url
            .as_deref()
            .map(|s| expand_env_vars(s, Some(&expanded_env), Some(&workspace_cwd)))
            .filter(|s| !s.trim().is_empty());

        let is_explicit_sse = ttype_lower == "sse"
            || (raw_http_url.is_none()
                && ttype_lower.is_empty()
                && raw_url
                    .as_deref()
                    .map(|u| u.trim_end_matches('/').ends_with("/sse"))
                    .unwrap_or(false));

        let is_streamable_http = raw_http_url.is_some()
            || matches!(ttype_lower.as_str(), "http" | "streamable-http" | "streamablehttp")
            || (cfg.command.as_ref().map(|c| c.trim().is_empty()).unwrap_or(true)
                && raw_url.is_some()
                && !is_explicit_sse);

        let handle = if is_streamable_http {
            let endpoint = raw_http_url
                .or(raw_url)
                .ok_or_else(|| format!("MCP HTTP server '{}' missing url/httpUrl", server_name))?;
            let http = Client::builder()
                .connect_timeout(Duration::from_secs(10))
                .timeout(default_timeout)
                .build()
                .unwrap_or_else(|_| Client::new());
            Self {
                server_name: server_name.clone(),
                transport_kind: "http",
                trusted: cfg.trust,
                default_timeout,
                transport: McpTransport::StreamableHttp {
                    http,
                    endpoint,
                    headers: expanded_headers,
                    session_id: Arc::new(Mutex::new(None)),
                },
                next_id: AtomicI64::new(1),
            }
        } else if is_explicit_sse {
            let sse_url = raw_url
                .ok_or_else(|| format!("MCP SSE server '{}' missing url", server_name))?;
            let http = Client::builder()
                .connect_timeout(Duration::from_secs(10))
                .build()
                .unwrap_or_else(|_| Client::new());

            let pending: PendingMap = Arc::new(Mutex::new(HashMap::new()));
            let post_endpoint = Arc::new(Mutex::new(sse_url.clone()));

            let mut req_builder = http.get(&sse_url).header("Accept", "text/event-stream");
            for (k, v) in &expanded_headers {
                req_builder = req_builder.header(k.as_str(), v.as_str());
            }
            let resp = timeout(init_timeout, req_builder.send())
                .await
                .map_err(|_| format!("MCP SSE '{}' connection timed out", server_name))?
                .map_err(|e| format!("MCP SSE '{}' connect error: {}", server_name, e))?;

            if !resp.status().is_success() {
                return Err(format!(
                    "MCP SSE '{}' returned HTTP {}",
                    server_name,
                    resp.status()
                ));
            }

            let (ep_tx, ep_rx) = oneshot::channel::<String>();
            let pending_clone = Arc::clone(&pending);
            let post_ep_clone = Arc::clone(&post_endpoint);
            let sse_base = sse_url.clone();

            let reader_task = tokio::spawn(async move {
                let mut stream = resp.bytes_stream();
                let mut buf = String::new();
                let mut ep_sender = Some(ep_tx);

                while let Some(chunk_res) = stream.next().await {
                    let Ok(bytes) = chunk_res else {
                        break;
                    };
                    buf.push_str(&String::from_utf8_lossy(&bytes));
                    for (ev_name, data) in drain_sse_events(&mut buf, false) {
                        let ev_l = ev_name.as_deref().unwrap_or("message").trim();
                        if ev_l == "endpoint" {
                            let resolved = resolve_relative_url(&sse_base, data.trim());
                            *post_ep_clone.lock().await = resolved.clone();
                            if let Some(tx) = ep_sender.take() {
                                let _ = tx.send(resolved);
                            }
                            continue;
                        }
                        if let Ok(v) = serde_json::from_str::<Value>(data.trim()) {
                            dispatch_jsonrpc_message(&pending_clone, &v).await;
                        }
                    }
                }
            });

            // Wait briefly for server's initial `event: endpoint` announcement (fallback to base URL if omitted)
            let _ = timeout(Duration::from_secs(3), ep_rx).await;

            Self {
                server_name: server_name.clone(),
                transport_kind: "sse",
                trusted: cfg.trust,
                default_timeout,
                transport: McpTransport::Sse {
                    http,
                    post_endpoint,
                    headers: expanded_headers,
                    pending,
                    reader_task: Arc::new(Mutex::new(Some(reader_task))),
                },
                next_id: AtomicI64::new(1),
            }
        } else {
            let Some(cmd_bin_raw) = cfg.command.as_ref().filter(|s| !s.trim().is_empty()) else {
                return Err(format!("MCP server '{}' missing command/url", server_name));
            };
            let cmd_bin = expand_env_vars(cmd_bin_raw, Some(&expanded_env), Some(&workspace_cwd));

            let mut cmd = Command::new(&cmd_bin);
            let expanded_args: Vec<String> = cfg
                .args
                .iter()
                .map(|a| expand_env_vars(a, Some(&expanded_env), Some(&workspace_cwd)))
                .collect();
            cmd.args(&expanded_args)
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::null());

            if let Some(ref raw_cwd) = cfg.cwd {
                let resolved_cwd = PathBuf::from(expand_env_vars(
                    raw_cwd,
                    Some(&expanded_env),
                    Some(&workspace_cwd),
                ));
                if resolved_cwd.is_dir() {
                    cmd.current_dir(resolved_cwd);
                }
            }
            for (k, v) in &expanded_env {
                cmd.env(k, v);
            }

            #[cfg(unix)]
            unsafe {
                cmd.pre_exec(|| {
                    libc::setpgid(0, 0);
                    Ok(())
                });
            }

            let mut child = cmd
                .spawn()
                .map_err(|e| format!("Failed spawning MCP server '{}': {}", server_name, e))?;
            let pid = child.id();
            let stdin = child
                .stdin
                .take()
                .ok_or_else(|| format!("MCP '{}': stdin unavailable", server_name))?;
            let stdout = child
                .stdout
                .take()
                .ok_or_else(|| format!("MCP '{}': stdout unavailable", server_name))?;

            let pending: PendingMap = Arc::new(Mutex::new(HashMap::new()));
            let pending_reader = Arc::clone(&pending);

            tokio::spawn(async move {
                let mut reader = BufReader::new(stdout).lines();
                while let Ok(Some(line)) = reader.next_line().await {
                    let trimmed = line.trim();
                    if trimmed.is_empty() {
                        continue;
                    }
                    let Ok(v) = serde_json::from_str::<Value>(trimmed) else {
                        continue;
                    };
                    dispatch_jsonrpc_message(&pending_reader, &v).await;
                }
            });

            Self {
                server_name: server_name.clone(),
                transport_kind: "stdio",
                trusted: cfg.trust,
                default_timeout,
                transport: McpTransport::Stdio {
                    stdin: Arc::new(Mutex::new(stdin)),
                    pending,
                    child_pid: pid,
                    child: Arc::new(Mutex::new(Some(child))),
                },
                next_id: AtomicI64::new(1),
            }
        };

        // 1. JSON-RPC initialize
        let _init_res = handle
            .request(
                "initialize",
                json!({
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mrflow",
                        "version": "2.0.0"
                    }
                }),
                init_timeout,
            )
            .await?;

        // 2. notifications/initialized
        let _ = handle
            .notify("notifications/initialized", json!({}))
            .await;

        // 3. tools/list + includeTools / excludeTools filtering
        let tools_val = handle
            .request("tools/list", json!({}), init_timeout)
            .await
            .unwrap_or_else(|_| json!({ "tools": [] }));

        let mut tools = Vec::new();
        if let Some(arr) = tools_val.get("tools").and_then(|t| t.as_array()) {
            for t in arr {
                let Some(tname) = t.get("name").and_then(|s| s.as_str()) else {
                    continue;
                };
                if !is_tool_permitted(&cfg.include_tools, &cfg.exclude_tools, tname) {
                    continue;
                }
                let desc = t
                    .get("description")
                    .and_then(|s| s.as_str())
                    .unwrap_or("")
                    .to_string();
                let schema = t
                    .get("inputSchema")
                    .or_else(|| t.get("parametersJsonSchema"))
                    .cloned()
                    .unwrap_or_else(|| json!({ "type": "object", "properties": {} }));
                let safe_srv = server_name.replace('-', "_");
                let qualified_name = format!("mcp_{}_{}", safe_srv, tname);
                tools.push(McpDiscoveredTool {
                    server_name: server_name.clone(),
                    tool_name: tname.to_string(),
                    qualified_name,
                    description: format!("[MCP:{}] {}", server_name, desc),
                    parameters_schema: schema,
                });
            }
        }

        Ok((handle, tools))
    }

    async fn notify(&self, method: &str, params: Value) -> Result<(), String> {
        let msg = json!({
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        });
        match &self.transport {
            McpTransport::Stdio { stdin, .. } => {
                let mut line = serde_json::to_string(&msg).map_err(|e| e.to_string())?;
                line.push('\n');
                let mut lock = stdin.lock().await;
                lock.write_all(line.as_bytes())
                    .await
                    .map_err(|e| e.to_string())?;
                lock.flush().await.map_err(|e| e.to_string())?;
                Ok(())
            }
            McpTransport::StreamableHttp {
                http,
                endpoint,
                headers,
                session_id,
            } => {
                let mut rb = http
                    .post(endpoint)
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json, text/event-stream");
                if let Some(ref sid) = *session_id.lock().await {
                    rb = rb.header("Mcp-Session-Id", sid.as_str());
                }
                for (k, v) in headers {
                    rb = rb.header(k.as_str(), v.as_str());
                }
                let _ = rb.json(&msg).send().await;
                Ok(())
            }
            McpTransport::Sse {
                http,
                post_endpoint,
                headers,
                ..
            } => {
                let url = post_endpoint.lock().await.clone();
                let mut rb = http
                    .post(&url)
                    .header("Content-Type", "application/json");
                for (k, v) in headers {
                    rb = rb.header(k.as_str(), v.as_str());
                }
                let _ = rb.json(&msg).send().await;
                Ok(())
            }
        }
    }

    async fn request(&self, method: &str, params: Value, dur: Duration) -> Result<Value, String> {
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);
        let msg = json!({
            "jsonrpc": "2.0",
            "id": id,
            "method": method,
            "params": params
        });

        match &self.transport {
            McpTransport::Stdio { stdin, pending, .. } => {
                let (tx, rx) = oneshot::channel();
                pending.lock().await.insert(id, tx);

                let mut line = serde_json::to_string(&msg).map_err(|e| e.to_string())?;
                line.push('\n');
                {
                    let mut lock = stdin.lock().await;
                    if let Err(e) = lock.write_all(line.as_bytes()).await {
                        pending.lock().await.remove(&id);
                        return Err(format!("MCP write error: {}", e));
                    }
                    let _ = lock.flush().await;
                }

                match timeout(dur, rx).await {
                    Ok(Ok(res)) => res,
                    Ok(Err(_)) => Err(format!("MCP '{}' channel closed", self.server_name)),
                    Err(_) => {
                        pending.lock().await.remove(&id);
                        Err(format!("MCP '{}' RPC '{}' timed out", self.server_name, method))
                    }
                }
            }
            McpTransport::StreamableHttp {
                http,
                endpoint,
                headers,
                session_id,
            } => {
                let mut rb = http
                    .post(endpoint)
                    .timeout(dur)
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json, text/event-stream");
                if let Some(ref sid) = *session_id.lock().await {
                    rb = rb.header("Mcp-Session-Id", sid.as_str());
                }
                for (k, v) in headers {
                    rb = rb.header(k.as_str(), v.as_str());
                }

                let resp = rb
                    .json(&msg)
                    .send()
                    .await
                    .map_err(|e| format!("MCP HTTP '{}' RPC '{}' failed: {}", self.server_name, method, e))?;

                if let Some(sid_hdr) = resp.headers().get("mcp-session-id").and_then(|v| v.to_str().ok()) {
                    let trimmed = sid_hdr.trim();
                    if !trimmed.is_empty() {
                        *session_id.lock().await = Some(trimmed.to_string());
                    }
                }

                let status = resp.status();
                let ctype = resp
                    .headers()
                    .get("content-type")
                    .and_then(|v| v.to_str().ok())
                    .unwrap_or("")
                    .to_ascii_lowercase();

                if status.as_u16() == 202 || status.as_u16() == 204 {
                    return Ok(Value::Null);
                }

                let body = resp
                    .text()
                    .await
                    .map_err(|e| format!("MCP HTTP '{}' read body failed: {}", self.server_name, e))?;

                if !status.is_success() {
                    return Err(format!(
                        "MCP HTTP '{}' returned HTTP {}: {}",
                        self.server_name,
                        status,
                        body.chars().take(400).collect::<String>()
                    ));
                }

                parse_http_jsonrpc_body(&body, ctype.contains("text/event-stream"), id)
                    .ok_or_else(|| format!("MCP HTTP '{}' missing result for id={}", self.server_name, id))?
            }
            McpTransport::Sse {
                http,
                post_endpoint,
                headers,
                pending,
                ..
            } => {
                let (tx, rx) = oneshot::channel();
                pending.lock().await.insert(id, tx);

                let post_url = post_endpoint.lock().await.clone();
                let mut rb = http
                    .post(&post_url)
                    .timeout(dur)
                    .header("Content-Type", "application/json");
                for (k, v) in headers {
                    rb = rb.header(k.as_str(), v.as_str());
                }

                let resp = match rb.json(&msg).send().await {
                    Ok(r) => r,
                    Err(e) => {
                        pending.lock().await.remove(&id);
                        return Err(format!("MCP SSE '{}' POST failed: {}", self.server_name, e));
                    }
                };

                if !resp.status().is_success() {
                    let st = resp.status();
                    let body = resp.text().await.unwrap_or_default();
                    pending.lock().await.remove(&id);
                    return Err(format!(
                        "MCP SSE '{}' POST HTTP {}: {}",
                        self.server_name,
                        st,
                        body.chars().take(300).collect::<String>()
                    ));
                }

                // Some hybrid SSE servers also answer inline when Content-Type is application/json
                let ctype = resp
                    .headers()
                    .get("content-type")
                    .and_then(|v| v.to_str().ok())
                    .unwrap_or("")
                    .to_ascii_lowercase();
                if ctype.contains("application/json") {
                    if let Ok(body) = resp.text().await {
                        if let Some(parsed) = parse_http_jsonrpc_body(&body, false, id) {
                            pending.lock().await.remove(&id);
                            return parsed;
                        }
                    }
                }

                match timeout(dur, rx).await {
                    Ok(Ok(res)) => res,
                    Ok(Err(_)) => Err(format!("MCP SSE '{}' channel closed", self.server_name)),
                    Err(_) => {
                        pending.lock().await.remove(&id);
                        Err(format!("MCP SSE '{}' RPC '{}' timed out", self.server_name, method))
                    }
                }
            }
        }
    }

    async fn shutdown(&self) {
        match &self.transport {
            McpTransport::Stdio {
                child_pid, child, ..
            } => {
                if let Some(pid) = *child_pid {
                    #[cfg(unix)]
                    unsafe {
                        libc::kill(-(pid as i32), libc::SIGTERM);
                        libc::kill(-(pid as i32), libc::SIGKILL);
                    }
                }
                if let Some(mut c) = child.lock().await.take() {
                    let _ = c.kill().await;
                }
            }
            McpTransport::Sse { reader_task, .. } => {
                if let Some(handle) = reader_task.lock().await.take() {
                    handle.abort();
                }
            }
            McpTransport::StreamableHttp { .. } => {}
        }
    }
}

impl Drop for McpClientHandle {
    fn drop(&mut self) {
        match &self.transport {
            McpTransport::Stdio { child_pid, .. } => {
                if let Some(pid) = *child_pid {
                    #[cfg(unix)]
                    unsafe {
                        libc::kill(-(pid as i32), libc::SIGTERM);
                    }
                }
            }
            McpTransport::Sse { reader_task, .. } => {
                if let Ok(mut guard) = reader_task.try_lock() {
                    if let Some(h) = guard.take() {
                        h.abort();
                    }
                }
            }
            McpTransport::StreamableHttp { .. } => {}
        }
    }
}

async fn dispatch_jsonrpc_message(pending: &PendingMap, v: &Value) {
    if let Some(arr) = v.as_array() {
        for item in arr {
            Box::pin(dispatch_jsonrpc_message(pending, item)).await;
        }
        return;
    }
    if let Some(id) = v.get("id").and_then(|i| i.as_i64()) {
        let mut map = pending.lock().await;
        if let Some(tx) = map.remove(&id) {
            if let Some(err) = v.get("error") {
                let msg = err
                    .get("message")
                    .and_then(|m| m.as_str())
                    .unwrap_or("MCP RPC error")
                    .to_string();
                let _ = tx.send(Err(msg));
            } else {
                let res = v.get("result").cloned().unwrap_or(Value::Null);
                let _ = tx.send(Ok(res));
            }
        }
    }
}

fn parse_http_jsonrpc_body(
    body: &str,
    force_sse: bool,
    target_id: i64,
) -> Option<Result<Value, String>> {
    let trimmed = body.trim();
    if trimmed.is_empty() {
        return None;
    }
    if force_sse || trimmed.starts_with("data:") || trimmed.starts_with("event:") {
        let mut buf = trimmed.to_string();
        let events = drain_sse_events(&mut buf, true);
        let mut fallback: Option<Result<Value, String>> = None;
        for (_, data) in events {
            let Ok(v) = serde_json::from_str::<Value>(data.trim()) else {
                continue;
            };
            if let Some(res) = extract_jsonrpc_by_id(&v, target_id) {
                return Some(res);
            }
            if v.get("result").is_some() || v.get("error").is_some() {
                fallback = Some(extract_jsonrpc_payload(&v));
            }
        }
        return fallback;
    }

    let v: Value = serde_json::from_str(trimmed).ok()?;
    extract_jsonrpc_by_id(&v, target_id).or_else(|| {
        if v.get("result").is_some() || v.get("error").is_some() {
            Some(extract_jsonrpc_payload(&v))
        } else {
            None
        }
    })
}

fn extract_jsonrpc_by_id(v: &Value, target_id: i64) -> Option<Result<Value, String>> {
    if let Some(arr) = v.as_array() {
        for item in arr {
            if let Some(r) = extract_jsonrpc_by_id(item, target_id) {
                return Some(r);
            }
        }
        return None;
    }
    if v.get("id").and_then(|i| i.as_i64()) == Some(target_id) {
        return Some(extract_jsonrpc_payload(v));
    }
    None
}

fn extract_jsonrpc_payload(v: &Value) -> Result<Value, String> {
    if let Some(err) = v.get("error") {
        let msg = err
            .get("message")
            .and_then(|m| m.as_str())
            .unwrap_or("MCP RPC error")
            .to_string();
        Err(msg)
    } else {
        Ok(v.get("result").cloned().unwrap_or(Value::Null))
    }
}

fn drain_sse_events(buf: &mut String, flush_eof: bool) -> Vec<(Option<String>, String)> {
    if buf.contains('\r') {
        *buf = buf.replace("\r\n", "\n");
    }
    let mut events = Vec::new();
    while let Some(pos) = buf.find("\n\n") {
        let block = buf[..pos].to_string();
        buf.drain(..pos + 2);
        if let Some(ev) = parse_sse_block(&block) {
            events.push(ev);
        }
    }
    if flush_eof && !buf.trim().is_empty() {
        let block = std::mem::take(buf);
        if let Some(ev) = parse_sse_block(&block) {
            events.push(ev);
        }
    }
    events
}

fn parse_sse_block(block: &str) -> Option<(Option<String>, String)> {
    let mut ev_name: Option<String> = None;
    let mut data_lines: Vec<String> = Vec::new();
    for line in block.lines() {
        if line.starts_with(':') || line.trim().is_empty() {
            continue;
        }
        if let Some(rest) = line.strip_prefix("event:") {
            ev_name = Some(rest.trim().to_string());
        } else if let Some(rest) = line.strip_prefix("data:") {
            data_lines.push(rest.trim_start().to_string());
        }
    }
    if data_lines.is_empty() {
        None
    } else {
        Some((ev_name, data_lines.join("\n")))
    }
}

pub fn resolve_relative_url(base_url: &str, relative: &str) -> String {
    let rel = relative.trim();
    if rel.starts_with("http://") || rel.starts_with("https://") {
        return rel.to_string();
    }
    if rel.is_empty() {
        return base_url.to_string();
    }

    let Some(scheme_pos) = base_url.find("://") else {
        return rel.to_string();
    };
    let after_scheme = scheme_pos + 3;
    let path_start = base_url[after_scheme..]
        .find('/')
        .map(|i| after_scheme + i)
        .unwrap_or(base_url.len());
    let origin = &base_url[..path_start];

    if rel.starts_with('/') {
        format!("{}{}", origin, rel)
    } else {
        let no_query = base_url.split(['?', '#']).next().unwrap_or(base_url);
        let dir = match no_query.rfind('/') {
            Some(idx) if idx >= after_scheme => &no_query[..idx],
            _ => origin,
        };
        format!("{}/{}", dir.trim_end_matches('/'), rel)
    }
}

pub fn expand_env_vars(
    input: &str,
    extra_env: Option<&HashMap<String, String>>,
    workspace_cwd: Option<&Path>,
) -> String {
    let mut out = String::with_capacity(input.len());
    let chars: Vec<char> = input.chars().collect();
    let mut i = 0usize;
    while i < chars.len() {
        if chars[i] == '$' && i + 1 < chars.len() && chars[i + 1] == '{' {
            if let Some(close_rel) = chars[i + 2..].iter().position(|&c| c == '}') {
                let expr: String = chars[i + 2..i + 2 + close_rel].iter().collect();
                let (var_name, default_val) = match expr.split_once(":-") {
                    Some((k, d)) => (k.trim(), Some(d)),
                    None => (expr.trim(), None),
                };
                let resolved = if var_name == "workspaceFolder" || var_name == "FLOWORK_WORKSPACE" {
                    workspace_cwd.map(|p| p.to_string_lossy().to_string())
                } else {
                    extra_env
                        .and_then(|m| m.get(var_name).cloned())
                        .or_else(|| std::env::var(var_name).ok())
                };
                match resolved {
                    Some(v) if !v.is_empty() => out.push_str(&v),
                    _ => {
                        if let Some(d) = default_val {
                            out.push_str(d);
                        }
                    }
                }
                i = i + 2 + close_rel + 1;
                continue;
            }
        }
        out.push(chars[i]);
        i += 1;
    }
    out
}

pub fn is_tool_permitted(include_tools: &[String], exclude_tools: &[String], tool_name: &str) -> bool {
    if !include_tools.is_empty() && !include_tools.iter().any(|p| matches_glob_prefix(p, tool_name)) {
        return false;
    }
    if exclude_tools.iter().any(|p| matches_glob_prefix(p, tool_name)) {
        return false;
    }
    true
}

fn matches_glob_prefix(pat: &str, name: &str) -> bool {
    let p = pat.trim();
    if p == "*" || p == name {
        return true;
    }
    if let Some(prefix) = p.strip_suffix('*') {
        return name.starts_with(prefix);
    }
    false
}

pub struct McpManager {
    clients: HashMap<String, Arc<McpClientHandle>>,
    pub tools: Vec<McpDiscoveredTool>,
    tool_lookup: HashMap<String, (String, String)>, // qualified_name -> (server, tool)
}

impl McpManager {
    #[allow(dead_code)]
    pub fn empty() -> Self {
        Self {
            clients: HashMap::new(),
            tools: Vec::new(),
            tool_lookup: HashMap::new(),
        }
    }

    fn parse_server_entry(v: &Value) -> McpServerConfig {
        let str_field = |k: &str| v.get(k).and_then(|s| s.as_str()).map(|s| s.to_string());
        let str_vec = |k: &str| -> Vec<String> {
            v.get(k)
                .and_then(|a| a.as_array())
                .map(|arr| {
                    arr.iter()
                        .filter_map(|x| x.as_str().map(|s| s.to_string()))
                        .collect()
                })
                .unwrap_or_default()
        };
        let str_map = |k: &str| -> HashMap<String, String> {
            v.get(k)
                .and_then(|e| e.as_object())
                .map(|obj| {
                    obj.iter()
                        .filter_map(|(mk, mv)| mv.as_str().map(|s| (mk.clone(), s.to_string())))
                        .collect()
                })
                .unwrap_or_default()
        };

        McpServerConfig {
            command: str_field("command"),
            args: str_vec("args"),
            env: str_map("env"),
            cwd: str_field("cwd"),
            url: str_field("url"),
            http_url: str_field("httpUrl").or_else(|| str_field("http_url")),
            transport_type: str_field("type").or_else(|| str_field("transport")),
            headers: str_map("headers"),
            timeout: v.get("timeout").and_then(|n| n.as_u64()),
            trust: v.get("trust").and_then(|b| b.as_bool()).unwrap_or(false),
            include_tools: str_vec("includeTools"),
            exclude_tools: str_vec("excludeTools"),
            description: str_field("description"),
            disabled: v.get("disabled").and_then(|b| b.as_bool()).unwrap_or(false),
        }
    }

    fn scan_mcp_folder_dir(dir: &Path, servers: &mut HashMap<String, McpServerConfig>) {
        let Ok(entries) = fs::read_dir(dir) else {
            return;
        };
        for entry in entries.flatten() {
            let p = entry.path();
            if !p.is_dir() {
                continue;
            }
            let folder_name = p
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("")
                .to_string();
            for fname in &["config.json", "manifest.json"] {
                let cfg_file = p.join(fname);
                if !cfg_file.is_file() {
                    continue;
                }
                let Ok(raw) = fs::read_to_string(&cfg_file) else {
                    continue;
                };
                let Ok(v) = serde_json::from_str::<Value>(&raw) else {
                    continue;
                };
                let name = v
                    .get("name")
                    .and_then(|s| s.as_str())
                    .unwrap_or(&folder_name)
                    .to_string();
                let mut sc = Self::parse_server_entry(&v);
                if sc.cwd.is_none() {
                    sc.cwd = Some(p.to_string_lossy().to_string());
                }
                servers.insert(name, sc);
                break;
            }
        }
    }

    fn scan_mcp_json_file(file_path: &Path, servers: &mut HashMap<String, McpServerConfig>) {
        let Ok(raw) = fs::read_to_string(file_path) else {
            return;
        };
        let Ok(v) = serde_json::from_str::<Value>(&raw) else {
            return;
        };
        let target_map = v
            .get("mcpServers")
            .and_then(|m| m.as_object())
            .or_else(|| v.as_object());
        let Some(obj) = target_map else {
            return;
        };
        for (name, val) in obj {
            if !val.is_object() {
                continue;
            }
            if val.get("command").is_some()
                || val.get("url").is_some()
                || val.get("httpUrl").is_some()
                || val.get("http_url").is_some()
            {
                servers.insert(name.clone(), Self::parse_server_entry(val));
            }
        }
    }

    /// Discovers MCP servers from:
    /// 1) /opt/floworkos/mcp/*/{config.json,manifest.json}
    /// 2) ~/.flowork/mcp/*/{config.json,manifest.json}
    /// 3) <cwd>/.mcp.json, <cwd>/.flowork/mcp_config.json, <cwd>/.flowork/settings.json
    /// 4) ~/.flowork/settings.json
    pub fn discover_configs(config: &AppConfig) -> HashMap<String, McpServerConfig> {
        let mut servers: HashMap<String, McpServerConfig> = HashMap::new();

        // System & user folder-based MCP manifests
        Self::scan_mcp_folder_dir(&config.paths.mcp_dir, &mut servers);
        Self::scan_mcp_folder_dir(&config.paths.user_flowork_dir.join("mcp"), &mut servers);

        // Workspace project MCP declarations
        for candidate in [
            config.cwd.join(".mcp.json"),
            config.cwd.join(".flowork/mcp_config.json"),
            config.cwd.join(".flowork/settings.json"),
        ] {
            if candidate.is_file() {
                Self::scan_mcp_json_file(&candidate, &mut servers);
            }
        }

        // User overrides from ~/.flowork/settings.json
        for (name, scfg) in &config.settings.mcp_servers {
            servers.insert(name.clone(), scfg.clone());
        }

        let disabled: HashSet<String> = config
            .settings
            .disabled_mcp_servers
            .iter()
            .map(|s| s.to_ascii_lowercase())
            .collect();

        servers.retain(|name, sc| {
            if sc.disabled || disabled.contains(&name.to_ascii_lowercase()) {
                return false;
            }
            if let Some(ref allowed) = config.allowed_mcp_server_names {
                if !allowed.is_empty() && !allowed.contains(name) {
                    return false;
                }
            }
            true
        });

        servers
    }

    pub async fn connect_all(config: &AppConfig) -> Self {
        let configs = Self::discover_configs(config);
        let mut clients = HashMap::new();
        let mut tools = Vec::new();
        let mut tool_lookup = HashMap::new();

        let mut handles = Vec::new();
        for (name, scfg) in configs {
            let has_endpoint = scfg.command.as_ref().map(|c| !c.trim().is_empty()).unwrap_or(false)
                || scfg.url.as_ref().map(|u| !u.trim().is_empty()).unwrap_or(false)
                || scfg.http_url.as_ref().map(|u| !u.trim().is_empty()).unwrap_or(false);
            if !has_endpoint {
                continue;
            }
            let cwd = config.cwd.clone();
            handles.push(tokio::spawn(async move {
                McpClientHandle::connect(name, scfg, cwd).await
            }));
        }

        for h in handles {
            if let Ok(Ok((client, srv_tools))) = h.await {
                let sname = client.server_name.clone();
                clients.insert(sname, Arc::new(client));
                for t in srv_tools {
                    tool_lookup.insert(
                        t.qualified_name.clone(),
                        (t.server_name.clone(), t.tool_name.clone()),
                    );
                    tools.push(t);
                }
            }
        }

        tools.sort_by(|a, b| a.qualified_name.cmp(&b.qualified_name));

        Self {
            clients,
            tools,
            tool_lookup,
        }
    }

    pub fn is_mcp_tool(&self, name: &str) -> Option<&str> {
        self.tool_lookup.get(name).map(|(srv, _)| srv.as_str())
    }

    #[allow(dead_code)]
    pub fn is_server_trusted(&self, server: &str) -> bool {
        self.clients.get(server).map(|c| c.trusted).unwrap_or(false)
    }

    pub fn server_statuses(&self) -> Vec<McpServerStatus> {
        let mut list: Vec<McpServerStatus> = self
            .clients
            .iter()
            .map(|(name, client)| {
                let count = self.tools.iter().filter(|t| &t.server_name == name).count();
                McpServerStatus {
                    name: name.clone(),
                    transport: client.transport_kind.to_string(),
                    tool_count: count,
                    trusted: client.trusted,
                }
            })
            .collect();
        list.sort_by(|a, b| a.name.cmp(&b.name));
        list
    }

    pub fn declarations_with_intercept_gate(&self) -> Vec<ToolDeclaration> {
        self.tools
            .iter()
            .map(|t| {
                let mut schema = t.parameters_schema.clone();
                inject_intercept_gate_fields(&mut schema);
                ToolDeclaration {
                    name: t.qualified_name.clone(),
                    description: t.description.clone(),
                    parameters_json_schema: schema,
                }
            })
            .collect()
    }

    pub async fn call_tool(&self, qualified_name: &str, args: &Value) -> Result<Value, String> {
        let Some((srv, raw_tool)) = self.tool_lookup.get(qualified_name) else {
            return Err(format!("Unknown MCP tool '{}'", qualified_name));
        };
        let Some(client) = self.clients.get(srv) else {
            return Err(format!("MCP server '{}' is not connected", srv));
        };

        // Strip Flowork Intercept Gate metadata fields before dispatching to upstream MCP server
        let mut clean_args = args.clone();
        if let Some(obj) = clean_args.as_object_mut() {
            obj.remove("reason");
            obj.remove("keywords");
            obj.remove("goal");
        }

        client
            .request(
                "tools/call",
                json!({
                    "name": raw_tool,
                    "arguments": clean_args
                }),
                client.default_timeout,
            )
            .await
    }

    pub async fn list_resources(&self, server_filter: Option<&str>) -> Vec<McpResourceInfo> {
        let mut out = Vec::new();
        for (name, client) in &self.clients {
            if let Some(f) = server_filter {
                if name != f {
                    continue;
                }
            }
            if let Ok(res) = client
                .request("resources/list", json!({}), Duration::from_secs(5))
                .await
            {
                if let Some(arr) = res.get("resources").and_then(|r| r.as_array()) {
                    for r in arr {
                        let uri = r.get("uri").and_then(|s| s.as_str()).unwrap_or("").to_string();
                        let rname = r.get("name").and_then(|s| s.as_str()).unwrap_or(&uri).to_string();
                        let mime = r.get("mimeType").and_then(|s| s.as_str()).map(|s| s.to_string());
                        if !uri.is_empty() {
                            out.push(McpResourceInfo {
                                server: name.clone(),
                                uri,
                                name: rname,
                                mime_type: mime,
                            });
                        }
                    }
                }
            }
        }
        out
    }

    pub async fn read_resource(&self, server: Option<&str>, uri: &str) -> Result<Value, String> {
        let target_clients: Vec<(&String, &Arc<McpClientHandle>)> = if let Some(srv) = server {
            self.clients.iter().filter(|(k, _)| k.as_str() == srv).collect()
        } else {
            self.clients.iter().collect()
        };
        for (_, client) in target_clients {
            if let Ok(val) = client
                .request("resources/read", json!({ "uri": uri }), Duration::from_secs(10))
                .await
            {
                return Ok(val);
            }
        }
        Err(format!("MCP resource '{}' not found", uri))
    }

    pub async fn list_prompts(&self, server_filter: Option<&str>) -> Vec<McpPromptInfo> {
        let mut out = Vec::new();
        for (name, client) in &self.clients {
            if let Some(f) = server_filter {
                if name != f {
                    continue;
                }
            }
            if let Ok(res) = client
                .request("prompts/list", json!({}), Duration::from_secs(5))
                .await
            {
                if let Some(arr) = res.get("prompts").and_then(|p| p.as_array()) {
                    for p in arr {
                        let pname = p.get("name").and_then(|s| s.as_str()).unwrap_or("").to_string();
                        if pname.is_empty() {
                            continue;
                        }
                        let desc = p.get("description").and_then(|s| s.as_str()).map(|s| s.to_string());
                        let args = p
                            .get("arguments")
                            .and_then(|a| a.as_array())
                            .cloned()
                            .unwrap_or_default();
                        out.push(McpPromptInfo {
                            server: name.clone(),
                            name: pname,
                            description: desc,
                            arguments: args,
                        });
                    }
                }
            }
        }
        out
    }

    #[allow(dead_code)]
    pub async fn get_prompt(
        &self,
        server: &str,
        name: &str,
        arguments: Option<Value>,
    ) -> Result<Value, String> {
        let Some(client) = self.clients.get(server) else {
            return Err(format!("MCP server '{}' is not connected", server));
        };
        let mut params = json!({ "name": name });
        if let Some(args) = arguments {
            params["arguments"] = args;
        }
        client.request("prompts/get", params, client.default_timeout).await
    }

    pub async fn shutdown_all(&self) {
        for (_, client) in &self.clients {
            client.shutdown().await;
        }
    }
}

pub fn inject_intercept_gate_fields(schema: &mut Value) {
    if !schema.is_object() {
        *schema = json!({ "type": "object", "properties": {}, "required": [] });
    }
    let obj = schema.as_object_mut().unwrap();
    if !obj.contains_key("type") {
        obj.insert("type".to_string(), json!("object"));
    }
    if !obj.get("properties").map(|p| p.is_object()).unwrap_or(false) {
        obj.insert("properties".to_string(), json!({}));
    }
    let props = obj.get_mut("properties").unwrap().as_object_mut().unwrap();
    props.insert(
        "reason".to_string(),
        json!({
            "type": "string",
            "maxLength": 160,
            "description": "Audit rationale in technical English (max 160 chars)."
        }),
    );
    props.insert(
        "keywords".to_string(),
        json!({
            "type": "array",
            "items": { "type": "string" },
            "minItems": 5,
            "description": "At least 5 semantic English routing keywords."
        }),
    );
    props.insert(
        "goal".to_string(),
        json!({
            "type": "string",
            "maxLength": 160,
            "description": "Task objective in concise English (max 160 chars)."
        }),
    );

    if !obj.get("required").map(|r| r.is_array()).unwrap_or(false) {
        obj.insert("required".to_string(), json!([]));
    }
    let req = obj.get_mut("required").unwrap().as_array_mut().unwrap();
    for k in &["reason", "keywords"] {
        if !req.iter().any(|x| x.as_str() == Some(*k)) {
            req.push(json!(*k));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::CliOverrides;

    #[test]
    fn expands_env_vars_and_defaults() {
        let mut extra = HashMap::new();
        extra.insert("CUSTOM_TOKEN".to_string(), "tok-123".to_string());
        let ws = PathBuf::from("/tmp/work");
        let s = expand_env_vars(
            "Bearer ${CUSTOM_TOKEN} root=${workspaceFolder} opt=${UNSET_VAR:-fallback}",
            Some(&extra),
            Some(&ws),
        );
        assert_eq!(s, "Bearer tok-123 root=/tmp/work opt=fallback");
    }

    #[test]
    fn filters_include_and_exclude_tools_accurately() {
        let inc = vec!["search_*".to_string(), "fetch_doc".to_string()];
        let exc = vec!["search_admin*".to_string()];
        assert!(is_tool_permitted(&inc, &exc, "search_docs"));
        assert!(is_tool_permitted(&inc, &exc, "fetch_doc"));
        assert!(!is_tool_permitted(&inc, &exc, "search_admin_users"));
        assert!(!is_tool_permitted(&inc, &exc, "delete_all"));
    }

    #[test]
    fn resolves_sse_relative_and_absolute_endpoints() {
        assert_eq!(
            resolve_relative_url("http://127.0.0.1:8080/mcp/sse", "/messages?sessionId=42"),
            "http://127.0.0.1:8080/messages?sessionId=42"
        );
        assert_eq!(
            resolve_relative_url("https://api.example.com/v1/sse", "post?id=7"),
            "https://api.example.com/v1/post?id=7"
        );
        assert_eq!(
            resolve_relative_url("http://localhost:3000/sse", "http://localhost:3001/rpc"),
            "http://localhost:3001/rpc"
        );
    }

    #[test]
    fn discovers_workspace_mcp_json_and_http_config() {
        let tmp = std::env::temp_dir().join(format!("mrflow_mcp_disc_{}", uuid::Uuid::new_v4()));
        fs::create_dir_all(&tmp).unwrap();
        fs::write(
            tmp.join(".mcp.json"),
            serde_json::to_string_pretty(&json!({
                "mcpServers": {
                    "remote_docs": {
                        "httpUrl": "https://docs.example.test/mcp",
                        "headers": { "Authorization": "Bearer ${DOCS_KEY:-demo}" },
                        "includeTools": ["query_*"],
                        "trust": true
                    }
                }
            }))
            .unwrap(),
        )
        .unwrap();

        let mut cfg = AppConfig::build(CliOverrides::default());
        cfg.cwd = tmp.clone();
        let discovered = McpManager::discover_configs(&cfg);
        let remote = discovered.get("remote_docs").expect("discovered remote_docs");
        assert_eq!(remote.http_url.as_deref(), Some("https://docs.example.test/mcp"));
        assert!(remote.trust);
        assert_eq!(remote.include_tools, vec!["query_*"]);
        let _ = fs::remove_dir_all(&tmp);
    }
}
