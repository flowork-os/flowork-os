use axum::body::{Body, Bytes};
use axum::extract::State;
use axum::http::{HeaderValue, Method, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use chrono::Utc;
use flowork_core_rs::flowpipe::{
    discover_pipelines, execute_flowpipe_dag, load_flowpipe_from_path_or_id, now_ms_u128 as fp_now_ms,
    parse_flowpipe_str, validate_flowpipe, EventSink, FlowpipeRunResult, FlowpipeSpec, RunControl,
};
use flowork_core_rs::resolve_home_dir;
use futures_util::stream;
use regex::Regex;
use serde_json::{json, Map, Value};
use std::collections::{HashMap, VecDeque};
use std::convert::Infallible;
use std::env;
use std::fs;
use std::io::Write as _;
use std::net::SocketAddr;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::{TcpListener, UnixListener};
use tokio::sync::{broadcast, Mutex};
use tower_http::cors::{Any, CorsLayer};
use uuid::Uuid;

const TMP_SYMLINK: &str = "/tmp/flowork-neural-bus.sock";
const MAX_HISTORY: usize = 100;

#[derive(Clone)]
struct ActivePipeRun {
    run_id: String,
    pipeline_id: String,
    status: String,
    control: Arc<RunControl>,
    started_ms: u128,
    result: Option<FlowpipeRunResult>,
}

#[derive(Clone)]
struct BusState {
    socket_path: PathBuf,
    manage_primary_symlink: bool,
    history: Arc<Mutex<VecDeque<Value>>>,
    registered_apps: Arc<Mutex<HashMap<String, Value>>>,
    pipe_runs: Arc<Mutex<HashMap<String, ActivePipeRun>>>,
    unix_clients: Arc<AtomicUsize>,
    sse_clients: Arc<AtomicUsize>,
    tx: broadcast::Sender<String>,
    seq: Arc<AtomicU64>,
}

fn now_ms_u128() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0)
}

fn resolve_socket_path(port: u16) -> (PathBuf, bool) {
    if let Ok(explicit) = env::var("FLOWORK_BUS_SOCKET") {
        let trimmed = explicit.trim();
        if !trimmed.is_empty() {
            return (PathBuf::from(trimmed), port == 18095);
        }
    }
    let run_sock = Path::new("/run/flowork/bus.sock");
    if port != 18095 {
        return (
            PathBuf::from(format!("/tmp/flowork-neural-bus-{}.sock", port)),
            false,
        );
    }

    let run_dir = Path::new("/run/flowork");
    let use_run = if fs::create_dir_all(run_dir).is_ok() {
        let _ = fs::set_permissions(run_dir, fs::Permissions::from_mode(0o777));
        let probe = run_dir.join(".write_probe");
        let ok = fs::write(&probe, b"").is_ok();
        let _ = fs::remove_file(&probe);
        ok
    } else {
        false
    };

    if use_run {
        (run_sock.to_path_buf(), true)
    } else {
        let fallback_dir = resolve_home_dir().join(".flowork");
        let _ = fs::create_dir_all(&fallback_dir);
        let _ = fs::set_permissions(&fallback_dir, fs::Permissions::from_mode(0o755));
        (fallback_dir.join("bus.sock"), true)
    }
}

fn is_safe_app_name(app_name: &str) -> bool {
    !app_name.is_empty()
        && app_name
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
}

fn find_headless_binary(app_name: &str) -> Option<String> {
    if !is_safe_app_name(app_name) {
        return None;
    }
    let candidates = [
        format!("/opt/floworkos/apps/{}/bin/{}-cli", app_name, app_name),
        format!("/opt/floworkos/apps/{}/bin/{}", app_name, app_name),
        format!("/opt/floworkos/bin/{}-cli", app_name),
        format!("/opt/floworkos/bin/{}", app_name),
        format!("/usr/local/bin/{}", app_name),
    ];
    let is_exec = |p: &Path| -> bool {
        if let Ok(meta) = fs::metadata(p) {
            meta.is_file() && (meta.permissions().mode() & 0o111 != 0)
        } else {
            false
        }
    };
    for cand in candidates {
        let p = Path::new(&cand);
        if is_exec(p) {
            return Some(cand);
        }
    }
    if let Ok(env_path) = env::var("PATH") {
        for dir in env_path.split(':') {
            let full = Path::new(dir).join(app_name);
            if is_exec(&full) {
                return Some(full.to_string_lossy().to_string());
            }
        }
    }
    None
}

fn discover_headless_clis() -> HashMap<String, String> {
    let mut map = HashMap::new();
    let apps_root = Path::new("/opt/floworkos/apps");
    if let Ok(entries) = fs::read_dir(apps_root) {
        for entry in entries.flatten() {
            let path = entry.path();
            if !path.is_dir() {
                continue;
            }
            let Some(app_name) = path.file_name().and_then(|s| s.to_str()) else {
                continue;
            };
            let cli_path = path.join("bin").join(format!("{}-cli", app_name));
            if let Ok(meta) = fs::metadata(&cli_path) {
                if meta.is_file() && (meta.permissions().mode() & 0o111 != 0) {
                    map.insert(
                        app_name.to_string(),
                        cli_path.to_string_lossy().to_string(),
                    );
                }
            }
        }
    }
    map
}

fn resolve_placeholders(val: &Value, payload: &Value) -> Value {
    let Some(s) = val.as_str() else {
        return val.clone();
    };
    let prev_str = payload
        .get("output")
        .or_else(|| payload.get("result"))
        .and_then(|v| v.as_str().map(str::to_string))
        .unwrap_or_else(|| serde_json::to_string(payload).unwrap_or_else(|_| "{}".to_string()));
    let file_str = payload
        .get("file")
        .or_else(|| payload.get("path"))
        .and_then(|v| v.as_str())
        .unwrap_or("");
    let input_str = payload
        .get("input")
        .or_else(|| payload.get("text"))
        .and_then(|v| v.as_str())
        .unwrap_or("");

    let out = s
        .replace("{prev}", &prev_str)
        .replace("{file}", file_str)
        .replace("{input}", input_str);
    Value::String(out)
}

async fn record_and_broadcast(state: &BusState, mut evt: Value) -> Value {
    let n = state.seq.fetch_add(1, Ordering::Relaxed);
    let ts_id = format!("evt_{}_{}", now_ms_u128(), &Uuid::new_v4().to_string()[..4]);
    let ts_iso = Utc::now().to_rfc3339();
    if let Some(obj) = evt.as_object_mut() {
        obj.insert("id".to_string(), Value::String(ts_id));
        obj.insert("seq".to_string(), json!(n));
        obj.insert("timestamp".to_string(), Value::String(ts_iso));
    }

    let raw = serde_json::to_string(&evt).unwrap_or_else(|_| "{}".to_string());
    {
        let mut hist = state.history.lock().await;
        hist.push_back(evt.clone());
        while hist.len() > MAX_HISTORY {
            hist.pop_front();
        }
    }
    let _ = state.tx.send(raw);
    evt
}

async fn handle_incoming_message(state: &BusState, msg: Value) -> Value {
    let Some(obj) = msg.as_object() else {
        return json!({ "status": "error", "message": "Payload must be JSON object" });
    };

    let msg_type = obj.get("type").and_then(|v| v.as_str()).unwrap_or("event");
    let source = obj
        .get("source")
        .and_then(|v| v.as_str())
        .unwrap_or("anonymous");
    let target = obj.get("target").and_then(|v| v.as_str()).unwrap_or("*");
    let action = obj.get("action").and_then(|v| v.as_str()).unwrap_or("ping");
    let payload = obj.get("payload").cloned().unwrap_or_else(|| json!({}));
    let shm_key = obj.get("shm_key").cloned().unwrap_or(Value::Null);

    if msg_type == "register" {
        let mut apps = state.registered_apps.lock().await;
        let name = obj.get("name").and_then(|v| v.as_str()).unwrap_or(source);
        let caps = obj.get("capabilities").cloned().unwrap_or_else(|| json!([]));
        apps.insert(
            source.to_string(),
            json!({
                "name": name,
                "capabilities": caps,
                "lastSeen": Utc::now().to_rfc3339()
            }),
        );
        return json!({
            "status": "ok",
            "message": format!("App [{}] registered on Neural Bus", source)
        });
    }

    if msg_type == "list_apps" {
        let apps = state.registered_apps.lock().await;
        return json!({
            "status": "ok",
            "apps": *apps
        });
    }

    match msg_type {
        "pipe_list" => return build_pipe_list_json(),
        "pipe_validate" => return handle_pipe_validate_payload(msg.clone()).await,
        "pipe_run" => return handle_pipe_run_payload(state, msg.clone()).await,
        "pipe_runs" => return build_pipe_runs_json(state).await,
        "pipe_pause" => return handle_pipe_control(state, msg.clone(), "pause").await,
        "pipe_resume" => return handle_pipe_control(state, msg.clone(), "resume").await,
        "pipe_cancel" => return handle_pipe_control(state, msg.clone(), "cancel").await,
        _ => {}
    }

    let evt = record_and_broadcast(
        state,
        json!({
            "type": msg_type,
            "source": source,
            "target": target,
            "action": action,
            "payload": payload,
            "shm_key": shm_key
        }),
    )
    .await;

    json!({
        "status": "ok",
        "event_id": evt.get("id").cloned().unwrap_or(Value::Null),
        "timestamp": evt.get("timestamp").cloned().unwrap_or(Value::Null)
    })
}

async fn execute_pipeline(state: &BusState, pipe_req: Value) -> Value {
    let Some(pipeline) = pipe_req.get("pipeline").and_then(|v| v.as_array()) else {
        return json!({ "status": "error", "message": "Pipeline array cannot be empty" });
    };
    if pipeline.is_empty() {
        return json!({ "status": "error", "message": "Pipeline array cannot be empty" });
    }

    let strict_mode = pipe_req
        .get("strict")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);
    let default_timeout_secs = pipe_req
        .get("timeout_secs")
        .and_then(|v| v.as_u64())
        .unwrap_or(120)
        .clamp(5, 600);

    let pipeline_id = format!("pipe_{}", now_ms_u128());
    let mut current_payload = pipe_req
        .get("initial_payload")
        .cloned()
        .unwrap_or_else(|| json!({}));
    let mut results = Vec::new();
    let total_stages = pipeline.len();

    for (idx, stage) in pipeline.iter().enumerate() {
        let stage_num = idx + 1;
        let app_name = stage
            .get("app")
            .or_else(|| stage.get("target"))
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let action = stage
            .get("action")
            .and_then(|v| v.as_str())
            .unwrap_or("run");
        let stage_timeout_secs = stage
            .get("timeout_secs")
            .and_then(|v| v.as_u64())
            .unwrap_or(default_timeout_secs)
            .clamp(5, 600);

        let mut resolved_params = serde_json::Map::new();
        if let Some(params_obj) = stage.get("params").and_then(|v| v.as_object()) {
            for (k, v) in params_obj {
                if let Some(arr) = v.as_array() {
                    let resolved_arr: Vec<Value> = arr
                        .iter()
                        .map(|elem| resolve_placeholders(elem, &current_payload))
                        .collect();
                    resolved_params.insert(k.clone(), Value::Array(resolved_arr));
                } else {
                    resolved_params.insert(k.clone(), resolve_placeholders(v, &current_payload));
                }
            }
        }

        let mut positional_args: Vec<String> = Vec::new();
        for pos_src in [stage.get("args"), stage.get("positional"), resolved_params.get("args"), resolved_params.get("positional")]
            .into_iter()
            .flatten()
        {
            if let Some(arr) = pos_src.as_array() {
                for elem in arr {
                    let rv = resolve_placeholders(elem, &current_payload);
                    if let Some(s) = rv.as_str() {
                        positional_args.push(s.to_string());
                    } else if !rv.is_null() {
                        positional_args.push(rv.to_string());
                    }
                }
            }
        }

        let mut evt_payload = resolved_params.clone();
        evt_payload.insert("input_data".to_string(), current_payload.clone());

        let evt = record_and_broadcast(
            state,
            json!({
                "type": "pipeline_stage",
                "pipeline_id": pipeline_id,
                "stage": stage_num,
                "total_stages": total_stages,
                "target": app_name,
                "action": action,
                "payload": Value::Object(evt_payload)
            }),
        )
        .await;

        let mut stage_output = json!(null);
        let mut stage_success = true;
        let mut stage_error = String::new();
        let mut stage_mode = "event_broadcast_only";

        if let Some(bin_path) = find_headless_binary(app_name) {
            stage_mode = "headless_cli";
            let mut args: Vec<String> = Vec::new();
            if !action.is_empty() && action != "default" && action != "run" {
                args.push(action.to_string());
            }
            args.extend(positional_args.clone());
            for (k, v) in &resolved_params {
                if k == "args" || k == "positional" || k == "timeout_secs" {
                    continue;
                }
                match v {
                    Value::Bool(true) => args.push(format!("--{}", k)),
                    Value::Bool(false) | Value::Null => {}
                    Value::String(s) => {
                        args.push(format!("--{}", k));
                        args.push(s.clone());
                    }
                    other => {
                        args.push(format!("--{}", k));
                        args.push(other.to_string());
                    }
                }
            }

            let stdin_payload = serde_json::to_string(&current_payload).unwrap_or_else(|_| "{}".to_string());
            let pid_clone = pipeline_id.clone();
            let bin_for_exec = bin_path.clone();
            let exec_res = tokio::task::spawn_blocking(move || {
                let mut child = Command::new(&bin_for_exec)
                    .args(&args)
                    .env("FLOWORK_PIPELINE_ID", &pid_clone)
                    .env("FLOWORK_STAGE", stage_num.to_string())
                    .stdin(Stdio::piped())
                    .stdout(Stdio::piped())
                    .stderr(Stdio::piped())
                    .spawn()?;
                if let Some(mut stdin) = child.stdin.take() {
                    let _ = stdin.write_all(stdin_payload.as_bytes());
                }
                child.wait_with_output()
            });

            match tokio::time::timeout(Duration::from_secs(stage_timeout_secs), exec_res).await {
                Ok(Ok(Ok(out))) => {
                    if !out.status.success() {
                        stage_success = false;
                        let stderr_s = String::from_utf8_lossy(&out.stderr).trim().to_string();
                        let stdout_s = String::from_utf8_lossy(&out.stdout).trim().to_string();
                        stage_error = if !stderr_s.is_empty() {
                            stderr_s
                        } else if !stdout_s.is_empty() {
                            stdout_s
                        } else {
                            format!("Exit code {:?}", out.status.code())
                        };
                    } else {
                        let raw_out = String::from_utf8_lossy(&out.stdout).trim().to_string();
                        stage_output = serde_json::from_str::<Value>(&raw_out)
                            .unwrap_or_else(|_| json!({ "output": raw_out }));
                        if let Some(obj) = stage_output.as_object_mut() {
                            if !obj.contains_key("binary") {
                                obj.insert("binary".to_string(), json!(bin_path));
                            }
                        }
                    }
                }
                Ok(Ok(Err(e))) => {
                    stage_success = false;
                    stage_error = e.to_string();
                }
                Ok(Err(e)) => {
                    stage_success = false;
                    stage_error = e.to_string();
                }
                Err(_) => {
                    stage_success = false;
                    stage_error = format!("Stage execution timed out after {}s", stage_timeout_secs);
                }
            }
        } else if strict_mode {
            stage_success = false;
            stage_error = format!("No headless CLI binary discovered for app '{}'", app_name);
        } else {
            stage_output = json!({
                "dispatched": true,
                "mode": "event_broadcast_only",
                "target": app_name,
                "action": action
            });
        }

        if !stage_success {
            let _ = record_and_broadcast(
                state,
                json!({
                    "type": "pipeline_failed",
                    "pipeline_id": pipeline_id,
                    "stage": stage_num,
                    "target": app_name,
                    "error": stage_error
                }),
            )
            .await;

            return json!({
                "status": "error",
                "pipeline_id": pipeline_id,
                "failed_stage": stage_num,
                "target": app_name,
                "error": stage_error,
                "results": results
            });
        }

        let mut merged = current_payload.as_object().cloned().unwrap_or_default();
        if let Some(out_obj) = stage_output.as_object() {
            for (k, v) in out_obj {
                merged.insert(k.clone(), v.clone());
            }
        } else {
            merged.insert("result".to_string(), stage_output.clone());
        }
        merged.insert("last_stage".to_string(), json!(stage_num));
        merged.insert("last_target".to_string(), json!(app_name));
        current_payload = Value::Object(merged);

        results.push(json!({
            "stage": stage_num,
            "target": app_name,
            "action": action,
            "mode": stage_mode,
            "event_id": evt.get("id").cloned().unwrap_or(Value::Null),
            "output": stage_output
        }));
    }

    let _ = record_and_broadcast(
        state,
        json!({
            "type": "pipeline_complete",
            "pipeline_id": pipeline_id,
            "total_stages": total_stages,
            "final_payload": current_payload
        }),
    )
    .await;

    json!({
        "status": "ok",
        "pipeline_id": pipeline_id,
        "stages_completed": results.len(),
        "results": results,
        "final_payload": current_payload
    })
}

async fn handle_health(State(st): State<BusState>) -> impl IntoResponse {
    let hist_len = st.history.lock().await.len();
    let app_keys: Vec<String> = st.registered_apps.lock().await.keys().cloned().collect();
    Json(json!({
        "status": "ok",
        "bus": "Flowork Neural Bus v2.0.0-sovereign",
        "socket": st.socket_path.to_string_lossy(),
        "unix_clients": st.unix_clients.load(Ordering::Relaxed),
        "sse_clients": st.sse_clients.load(Ordering::Relaxed),
        "events_recorded": hist_len,
        "registered_apps": app_keys
    }))
}

async fn handle_apps(State(st): State<BusState>) -> impl IntoResponse {
    let reg = st.registered_apps.lock().await.clone();
    let clis = discover_headless_clis();
    Json(json!({
        "status": "ok",
        "registered_apps": reg,
        "headless_clis": clis,
        "headless_count": clis.len()
    }))
}

async fn handle_events(State(st): State<BusState>) -> impl IntoResponse {
    let events: Vec<Value> = st.history.lock().await.iter().cloned().collect();
    Json(json!({
        "status": "ok",
        "count": events.len(),
        "events": events
    }))
}

struct SseClientGuard(Arc<AtomicUsize>);
impl Drop for SseClientGuard {
    fn drop(&mut self) {
        self.0.fetch_sub(1, Ordering::Relaxed);
    }
}

async fn handle_sse(State(st): State<BusState>) -> Response {
    st.sse_clients.fetch_add(1, Ordering::Relaxed);
    let guard = Arc::new(SseClientGuard(st.sse_clients.clone()));
    let rx = st.tx.subscribe();
    let hello = format!(
        "data: {}\n\n",
        json!({"type": "connected", "socket": st.socket_path.to_string_lossy()})
    );

    let event_stream = stream::unfold((rx, Some(hello), guard), |(mut rx, hello_opt, guard)| async move {
        if let Some(first) = hello_opt {
            return Some((Ok::<Bytes, Infallible>(Bytes::from(first)), (rx, None, guard)));
        }
        loop {
            match rx.recv().await {
                Ok(raw) => {
                    let frame = format!("data: {}\n\n", raw);
                    return Some((Ok(Bytes::from(frame)), (rx, None, guard)));
                }
                Err(broadcast::error::RecvError::Lagged(_)) => continue,
                Err(broadcast::error::RecvError::Closed) => return None,
            }
        }
    });

    Response::builder()
        .status(StatusCode::OK)
        .header("Content-Type", HeaderValue::from_static("text/event-stream; charset=utf-8"))
        .header("Cache-Control", HeaderValue::from_static("no-cache"))
        .header("Connection", HeaderValue::from_static("keep-alive"))
        .body(Body::from_stream(event_stream))
        .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response())
}

async fn handle_publish(State(st): State<BusState>, body: Bytes) -> impl IntoResponse {
    let parsed: Value = if body.is_empty() {
        json!({})
    } else {
        match serde_json::from_slice(&body) {
            Ok(v) => v,
            Err(e) => {
                return (
                    StatusCode::BAD_REQUEST,
                    Json(json!({ "status": "error", "error": e.to_string() })),
                );
            }
        }
    };
    let reply = handle_incoming_message(&st, parsed).await;
    (StatusCode::OK, Json(reply))
}

async fn handle_pipe(State(st): State<BusState>, body: Bytes) -> impl IntoResponse {
    let parsed: Value = if body.is_empty() {
        json!({})
    } else {
        match serde_json::from_slice(&body) {
            Ok(v) => v,
            Err(e) => {
                return (
                    StatusCode::BAD_REQUEST,
                    Json(json!({ "status": "error", "error": e.to_string() })),
                );
            }
        }
    };
    let reply = execute_pipeline(&st, parsed).await;
    (StatusCode::OK, Json(reply))
}

fn extract_flowpipe_spec(req: &Value) -> Result<FlowpipeSpec, String> {
    if let Some(raw_toml) = req.get("toml").or_else(|| req.get("raw")).and_then(|v| v.as_str()) {
        return parse_flowpipe_str(raw_toml, None);
    }
    if let Some(spec_val) = req.get("spec") {
        if let Some(s) = spec_val.as_str() {
            return parse_flowpipe_str(s, None);
        }
        return serde_json::from_value::<FlowpipeSpec>(spec_val.clone())
            .map_err(|e| format!("Invalid spec JSON: {}", e));
    }
    if let Some(target) = req
        .get("path")
        .or_else(|| req.get("id"))
        .and_then(|v| v.as_str())
    {
        let (spec, _) = load_flowpipe_from_path_or_id(target)?;
        return Ok(spec);
    }
    if req.get("nodes").is_some() && req.get("id").is_some() {
        return serde_json::from_value::<FlowpipeSpec>(req.clone())
            .map_err(|e| format!("Invalid inline .flowpipe spec: {}", e));
    }
    Err("Expected 'path', 'id', 'toml', or 'spec' in request".to_string())
}

fn build_pipe_list_json() -> Value {
    let list = discover_pipelines();
    let arr: Vec<Value> = list
        .into_iter()
        .map(|p| {
            json!({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "path": p.path,
                "scope": p.scope,
                "node_count": p.node_count
            })
        })
        .collect();
    json!({
        "status": "ok",
        "count": arr.len(),
        "pipelines": arr
    })
}

async fn handle_pipe_validate_payload(req: Value) -> Value {
    match extract_flowpipe_spec(&req) {
        Ok(spec) => {
            let rep = validate_flowpipe(&spec);
            json!({
                "status": if rep.valid { "ok" } else { "error" },
                "valid": rep.valid,
                "id": rep.id,
                "node_count": rep.node_count,
                "topo_layers": rep.topo_layers,
                "errors": rep.errors,
                "warnings": rep.warnings
            })
        }
        Err(e) => json!({ "status": "error", "valid": false, "errors": [e] }),
    }
}

async fn build_pipe_runs_json(state: &BusState) -> Value {
    let runs = state.pipe_runs.lock().await;
    let mut items: Vec<Value> = runs
        .values()
        .map(|r| {
            json!({
                "run_id": r.run_id,
                "pipeline_id": r.pipeline_id,
                "status": r.status,
                "paused": r.control.paused.load(Ordering::SeqCst),
                "cancelled": r.control.cancelled.load(Ordering::SeqCst),
                "started_ms": r.started_ms,
                "result": r.result
            })
        })
        .collect();
    items.sort_by(|a, b| {
        b.get("started_ms")
            .and_then(|v| v.as_u64())
            .cmp(&a.get("started_ms").and_then(|v| v.as_u64()))
    });
    json!({
        "status": "ok",
        "count": items.len(),
        "runs": items
    })
}

async fn handle_pipe_control(state: &BusState, req: Value, op: &str) -> Value {
    let run_id = req.get("run_id").and_then(|v| v.as_str()).unwrap_or("").trim();
    let mut runs = state.pipe_runs.lock().await;
    let target = if !run_id.is_empty() {
        runs.get_mut(run_id)
    } else {
        runs.values_mut().find(|r| r.status == "running" || r.status == "paused")
    };
    let Some(run) = target else {
        return json!({ "status": "error", "message": "Matching pipe run not found" });
    };
    match op {
        "pause" => {
            run.control.pause();
            run.status = "paused".to_string();
        }
        "resume" => {
            run.control.resume();
            run.status = "running".to_string();
        }
        "cancel" => {
            run.control.cancel();
            run.status = "cancelled".to_string();
        }
        _ => {}
    }
    let rid = run.run_id.clone();
    let pid = run.pipeline_id.clone();
    let st_str = run.status.clone();
    drop(runs);

    let _ = record_and_broadcast(
        state,
        json!({
            "type": format!("pipe.run.{}", st_str),
            "run_id": rid,
            "pipeline_id": pid,
            "status": st_str
        }),
    )
    .await;

    json!({
        "status": "ok",
        "run_id": rid,
        "run_status": st_str
    })
}

async fn handle_pipe_run_payload(state: &BusState, req: Value) -> Value {
    let spec = match extract_flowpipe_spec(&req) {
        Ok(s) => s,
        Err(e) => return json!({ "status": "error", "error": e }),
    };

    let input_overrides: Map<String, Value> = req
        .get("inputs")
        .and_then(|v| v.as_object())
        .cloned()
        .unwrap_or_default();
    let use_cache = !req
        .get("no_cache")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);
    let background = req
        .get("background")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);

    let run_id = format!("dpr_{}_{}", fp_now_ms(), &Uuid::new_v4().to_string()[..6]);
    let control = Arc::new(RunControl::new(run_id.clone()));

    {
        let mut runs = state.pipe_runs.lock().await;
        if runs.len() > 40 {
            if let Some(oldest_done) = runs
                .iter()
                .filter(|(_, r)| r.result.is_some())
                .min_by_key(|(_, r)| r.started_ms)
                .map(|(k, _)| k.clone())
            {
                runs.remove(&oldest_done);
            }
        }
        runs.insert(
            run_id.clone(),
            ActivePipeRun {
                run_id: run_id.clone(),
                pipeline_id: spec.id.clone(),
                status: "running".to_string(),
                control: control.clone(),
                started_ms: fp_now_ms(),
                result: None,
            },
        );
    }

    let state_for_sink = state.clone();
    let sink: EventSink = Arc::new(move |evt: Value| {
        let st = state_for_sink.clone();
        tokio::spawn(async move {
            let _ = record_and_broadcast(&st, evt).await;
        });
    });

    if background {
        let st_bg = state.clone();
        let rid_bg = run_id.clone();
        let pid_bg = spec.id.clone();
        tokio::spawn(async move {
            let res = execute_flowpipe_dag(spec, input_overrides, use_cache, control, Some(sink)).await;
            let mut runs = st_bg.pipe_runs.lock().await;
            if let Some(entry) = runs.get_mut(&rid_bg) {
                entry.status = res.status.clone();
                entry.result = Some(res);
            }
        });
        return json!({
            "status": "accepted",
            "run_id": run_id,
            "pipeline_id": pid_bg
        });
    }

    let res = execute_flowpipe_dag(spec, input_overrides, use_cache, control, Some(sink)).await;
    {
        let mut runs = state.pipe_runs.lock().await;
        if let Some(entry) = runs.get_mut(&run_id) {
            entry.status = res.status.clone();
            entry.result = Some(res.clone());
        }
    }
    serde_json::to_value(res).unwrap_or_else(|e| json!({ "status": "error", "error": e.to_string() }))
}

fn parse_json_body(body: &Bytes) -> Result<Value, (StatusCode, Json<Value>)> {
    if body.is_empty() {
        return Ok(json!({}));
    }
    serde_json::from_slice(body).map_err(|e| {
        (
            StatusCode::BAD_REQUEST,
            Json(json!({ "status": "error", "error": e.to_string() })),
        )
    })
}

async fn handle_pipe_list() -> impl IntoResponse {
    (StatusCode::OK, Json(build_pipe_list_json()))
}

async fn handle_pipe_runs(State(st): State<BusState>) -> impl IntoResponse {
    (StatusCode::OK, Json(build_pipe_runs_json(&st).await))
}

async fn handle_pipe_validate(body: Bytes) -> impl IntoResponse {
    match parse_json_body(&body) {
        Ok(v) => (StatusCode::OK, Json(handle_pipe_validate_payload(v).await)),
        Err(resp) => resp,
    }
}

async fn handle_pipe_run(State(st): State<BusState>, body: Bytes) -> impl IntoResponse {
    match parse_json_body(&body) {
        Ok(v) => (StatusCode::OK, Json(handle_pipe_run_payload(&st, v).await)),
        Err(resp) => resp,
    }
}

async fn handle_pipe_pause(State(st): State<BusState>, body: Bytes) -> impl IntoResponse {
    match parse_json_body(&body) {
        Ok(v) => (StatusCode::OK, Json(handle_pipe_control(&st, v, "pause").await)),
        Err(resp) => resp,
    }
}

async fn handle_pipe_resume(State(st): State<BusState>, body: Bytes) -> impl IntoResponse {
    match parse_json_body(&body) {
        Ok(v) => (StatusCode::OK, Json(handle_pipe_control(&st, v, "resume").await)),
        Err(resp) => resp,
    }
}

async fn handle_pipe_cancel(State(st): State<BusState>, body: Bytes) -> impl IntoResponse {
    match parse_json_body(&body) {
        Ok(v) => (StatusCode::OK, Json(handle_pipe_control(&st, v, "cancel").await)),
        Err(resp) => resp,
    }
}

async fn serve_unix_socket(state: BusState) {
    let sock_path = state.socket_path.clone();
    let _ = fs::remove_file(&sock_path);
    let listener = match UnixListener::bind(&sock_path) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("[NeuralBus] UNIX socket bind error on {:?}: {}", sock_path, e);
            return;
        }
    };
    let _ = fs::set_permissions(&sock_path, fs::Permissions::from_mode(0o666));
    if state.manage_primary_symlink {
        let _ = fs::remove_file(TMP_SYMLINK);
        let _ = std::os::unix::fs::symlink(&sock_path, TMP_SYMLINK);
    }

    println!("⚡ Flowork Neural Bus UNIX Socket active: {}", sock_path.display());
    let _keep = Regex::new("").ok();

    loop {
        let Ok((stream, _)) = listener.accept().await else {
            continue;
        };
        let st = state.clone();
        tokio::spawn(async move {
            st.unix_clients.fetch_add(1, Ordering::Relaxed);
            let (reader, writer) = stream.into_split();
            let writer = Arc::new(Mutex::new(writer));
            let mut bcast_rx = st.tx.subscribe();

            let writer_bcast = writer.clone();
            let bcast_task = tokio::spawn(async move {
                loop {
                    match bcast_rx.recv().await {
                        Ok(raw) => {
                            let mut w = writer_bcast.lock().await;
                            if w.write_all(format!("{}\n", raw).as_bytes()).await.is_err() {
                                break;
                            }
                        }
                        Err(broadcast::error::RecvError::Lagged(_)) => continue,
                        Err(_) => break,
                    }
                }
            });

            let mut lines = BufReader::new(reader).lines();
            while let Ok(Some(line)) = lines.next_line().await {
                let trimmed = line.trim();
                if trimmed.is_empty() {
                    continue;
                }
                let reply = match serde_json::from_str::<Value>(trimmed) {
                    Ok(msg) => handle_incoming_message(&st, msg).await,
                    Err(e) => json!({ "error": e.to_string(), "status": "error" }),
                };
                let mut w = writer.lock().await;
                if w.write_all(format!("{}\n", reply).as_bytes()).await.is_err() {
                    break;
                }
            }

            bcast_task.abort();
            st.unix_clients.fetch_sub(1, Ordering::Relaxed);
        });
    }
}

fn cleanup_sockets(socket_path: &Path, manage_primary_symlink: bool) {
    let _ = fs::remove_file(socket_path);
    if manage_primary_symlink {
        let _ = fs::remove_file(TMP_SYMLINK);
    }
}

#[tokio::main]
async fn main() {
    let mut port: u16 = env::var("FLOWORK_BUS_PORT")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(18095);

    let args: Vec<String> = env::args().skip(1).collect();
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--help" | "-h" => {
                println!("flowork-neural-bus — Sovereign UNIX & HTTP/SSE Neural Bus Daemon");
                println!("Usage: flowork-neural-bus [--check] [--port <port>] [--help]");
                return;
            }
            "--check" => {
                println!("flowork-neural-bus: OK (native Rust UNIX+HTTP/SSE daemon)");
                return;
            }
            "--port" => {
                if let Some(p) = args.get(i + 1).and_then(|s| s.parse().ok()) {
                    port = p;
                    i += 1;
                }
            }
            _ => {}
        }
        i += 1;
    }

    let (socket_path, manage_primary_symlink) = resolve_socket_path(port);
    let (tx, _) = broadcast::channel(256);

    let state = BusState {
        socket_path: socket_path.clone(),
        manage_primary_symlink,
        history: Arc::new(Mutex::new(VecDeque::with_capacity(MAX_HISTORY))),
        registered_apps: Arc::new(Mutex::new(HashMap::new())),
        pipe_runs: Arc::new(Mutex::new(HashMap::new())),
        unix_clients: Arc::new(AtomicUsize::new(0)),
        sse_clients: Arc::new(AtomicUsize::new(0)),
        tx,
        seq: Arc::new(AtomicU64::new(1)),
    };

    tokio::spawn(serve_unix_socket(state.clone()));

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([Method::GET, Method::POST, Method::OPTIONS])
        .allow_headers(Any);

    let app = Router::new()
        .route("/health", get(handle_health))
        .route("/api/bus/health", get(handle_health))
        .route("/api/bus/apps", get(handle_apps))
        .route("/api/bus/events", get(handle_events))
        .route("/api/bus/stream", get(handle_sse))
        .route("/api/bus/subscribe", get(handle_sse))
        .route("/api/bus/publish", post(handle_publish))
        .route("/api/bus/pipe", post(handle_pipe))
        .route("/api/bus/pipe/list", get(handle_pipe_list))
        .route("/api/bus/pipe/validate", post(handle_pipe_validate))
        .route("/api/bus/pipe/run", post(handle_pipe_run))
        .route("/api/bus/pipe/runs", get(handle_pipe_runs))
        .route("/api/bus/pipe/pause", post(handle_pipe_pause))
        .route("/api/bus/pipe/resume", post(handle_pipe_resume))
        .route("/api/bus/pipe/cancel", post(handle_pipe_cancel))
        .layer(cors)
        .with_state(state);

    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    let listener = match TcpListener::bind(addr).await {
        Ok(l) => l,
        Err(e) => {
            eprintln!("[NeuralBus] HTTP bind error on {}: {}", addr, e);
            std::process::exit(1);
        }
    };

    println!("=============================================================================");
    println!("  ⚡ Flowork OS — Neural Bus Daemon Online (Semantic Agentic Pipe)");
    println!("  UNIX Socket:  {}", socket_path.display());
    println!("  HTTP Bridge:  http://127.0.0.1:{}", port);
    println!("=============================================================================");

    let sp_clone = socket_path.clone();
    let shutdown = async move {
        #[cfg(unix)]
        {
            let mut term = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
                .expect("SIGTERM handler");
            tokio::select! {
                _ = tokio::signal::ctrl_c() => {},
                _ = term.recv() => {},
            }
        }
        #[cfg(not(unix))]
        let _ = tokio::signal::ctrl_c().await;
        println!("\n[NeuralBus] Shutting down cleanly...");
        cleanup_sockets(&sp_clone, manage_primary_symlink);
    };

    let _ = axum::serve(listener, app)
        .with_graceful_shutdown(shutdown)
        .await;
    cleanup_sockets(&socket_path, manage_primary_symlink);
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_state() -> BusState {
        let (tx, _) = broadcast::channel(32);
        BusState {
            socket_path: PathBuf::from("/tmp/flowork-bus-test.sock"),
            manage_primary_symlink: false,
            history: Arc::new(Mutex::new(VecDeque::with_capacity(MAX_HISTORY))),
            registered_apps: Arc::new(Mutex::new(HashMap::new())),
            pipe_runs: Arc::new(Mutex::new(HashMap::new())),
            unix_clients: Arc::new(AtomicUsize::new(0)),
            sse_clients: Arc::new(AtomicUsize::new(0)),
            tx,
            seq: Arc::new(AtomicU64::new(1)),
        }
    }

    #[test]
    fn validates_app_names_and_discovers_studio_clis() {
        assert!(is_safe_app_name("kamidi-mastering"));
        assert!(is_safe_app_name("cutvii"));
        assert!(!is_safe_app_name(""));
        assert!(!is_safe_app_name("../escape"));
        assert!(!is_safe_app_name("bad/app"));

        let discovered = discover_headless_clis();
        assert!(discovered.contains_key("kamidi-mastering"));
        assert!(discovered.contains_key("cutvii"));
        assert!(find_headless_binary("kamidi-mastering").is_some());
        assert!(find_headless_binary("cutvii").is_some());
    }

    #[test]
    fn resolves_pipeline_placeholders() {
        let payload = json!({
            "output": "/tmp/out.wav",
            "file": "/tmp/audio.wav",
            "input": "hello"
        });
        assert_eq!(
            resolve_placeholders(&json!("{file}"), &payload),
            json!("/tmp/audio.wav")
        );
        assert_eq!(
            resolve_placeholders(&json!("{prev}"), &payload),
            json!("/tmp/out.wav")
        );
        assert_eq!(
            resolve_placeholders(&json!("prefix:{input}"), &payload),
            json!("prefix:hello")
        );
    }

    #[tokio::test]
    async fn registers_and_lists_apps_over_bus_handler() {
        let st = test_state();
        let reg = handle_incoming_message(
            &st,
            json!({
                "type": "register",
                "source": "cutvii",
                "name": "CutVii Studio Engine",
                "capabilities": ["render", "probe"]
            }),
        )
        .await;
        assert_eq!(reg["status"], json!("ok"));

        let list = handle_incoming_message(&st, json!({ "type": "list_apps" })).await;
        assert_eq!(list["status"], json!("ok"));
        assert_eq!(list["apps"]["cutvii"]["name"], json!("CutVii Studio Engine"));
    }
}

