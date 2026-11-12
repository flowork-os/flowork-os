use flowork_core_rs::flowpipe::{
    discover_pipelines, execute_flowpipe_dag, load_flowpipe_from_path_or_id, parse_flowpipe_str,
    synthesize_flowpipe_from_events, user_pipelines_dir, validate_flowpipe, RunControl,
};
use flowork_core_rs::resolve_home_dir;
use futures_util::StreamExt;
use regex::Regex;
use serde_json::{json, Map, Value};
use std::env;
use std::fs;
use std::io::{BufRead, BufReader, Write as _};
use std::os::unix::net::UnixStream;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{Duration, Instant};

fn bus_http_base() -> String {
    env::var("FLOWORK_BUS_URL")
        .ok()
        .filter(|s| !s.trim().is_empty())
        .unwrap_or_else(|| "http://127.0.0.1:18095".to_string())
        .trim_end_matches('/')
        .to_string()
}

fn find_bus_socket() -> Option<PathBuf> {
    if let Ok(explicit) = env::var("FLOWORK_BUS_SOCKET") {
        let p = PathBuf::from(explicit.trim());
        if p.exists() {
            return Some(p);
        }
    }
    let home_sock = resolve_home_dir().join(".flowork/bus.sock");
    for cand in [
        Path::new("/run/flowork/bus.sock"),
        Path::new("/tmp/flowork-neural-bus.sock"),
        home_sock.as_path(),
    ] {
        if cand.exists() {
            return Some(cand.to_path_buf());
        }
    }
    None
}

fn send_unix_rpc(payload: &Value) -> Result<Value, String> {
    let sock = find_bus_socket().ok_or_else(|| "Neural Bus UNIX socket not found".to_string())?;
    let mut stream = UnixStream::connect(&sock)
        .map_err(|e| format!("Failed connecting UNIX socket {}: {}", sock.display(), e))?;
    let _ = stream.set_read_timeout(Some(Duration::from_secs(180)));
    let _ = stream.set_write_timeout(Some(Duration::from_secs(10)));

    let line = format!("{}\n", serde_json::to_string(payload).unwrap_or_default());
    stream
        .write_all(line.as_bytes())
        .map_err(|e| format!("UNIX socket write error: {}", e))?;

    let mut reader = BufReader::new(stream);
    let mut reply_line = String::new();
    loop {
        reply_line.clear();
        let n = reader
            .read_line(&mut reply_line)
            .map_err(|e| format!("UNIX socket read error: {}", e))?;
        if n == 0 {
            return Err("EOF waiting for Neural Bus UNIX reply".to_string());
        }
        if let Ok(v) = serde_json::from_str::<Value>(reply_line.trim()) {
            // Skip interleaved broadcast events (which always include "seq" from record_and_broadcast)
            if v.get("seq").is_none() && v.get("status").is_some() {
                return Ok(v);
            }
        }
    }
}

async fn post_bus_http(endpoint: &str, body: &Value) -> Result<Value, String> {
    let url = format!("{}/{}", bus_http_base(), endpoint.trim_start_matches('/'));
    let client = reqwest::Client::new();
    let resp = client
        .post(&url)
        .json(body)
        .timeout(Duration::from_secs(180))
        .send()
        .await
        .map_err(|e| format!("HTTP POST {} error: {}", url, e))?;
    resp.json::<Value>()
        .await
        .map_err(|e| format!("Invalid JSON from {}: {}", url, e))
}

async fn get_bus_http(endpoint: &str) -> Result<Value, String> {
    let url = format!("{}/{}", bus_http_base(), endpoint.trim_start_matches('/'));
    let client = reqwest::Client::new();
    let resp = client
        .get(&url)
        .timeout(Duration::from_secs(15))
        .send()
        .await
        .map_err(|e| format!("HTTP GET {} error: {}", url, e))?;
    resp.json::<Value>()
        .await
        .map_err(|e| format!("Invalid JSON from {}: {}", url, e))
}

async fn dispatch_rpc(unix_msg: Value, http_endpoint: &str, is_post: bool) -> Result<Value, String> {
    let custom_url = env::var("FLOWORK_BUS_URL")
        .ok()
        .map(|s| !s.trim().is_empty())
        .unwrap_or(false);
    if !custom_url {
        if let Ok(v) = send_unix_rpc(&unix_msg) {
            return Ok(v);
        }
    }
    if is_post {
        post_bus_http(http_endpoint, &unix_msg).await
    } else {
        get_bus_http(http_endpoint).await
    }
}

fn parse_legacy_stage(stage_str: &str) -> Value {
    let trimmed = stage_str.trim();
    let re_head = Regex::new(r"^([a-zA-Z0-9_-]+)::([a-zA-Z0-9_.-]+)(.*)$").expect("regex");
    let (app, action, args_str) = if let Some(c) = re_head.captures(trimmed) {
        (
            c[1].to_string(),
            c[2].to_string(),
            c[3].trim().to_string(),
        )
    } else {
        let mut parts = trimmed.splitn(2, char::is_whitespace);
        let a = parts.next().unwrap_or("").to_string();
        let rest = parts.next().unwrap_or("").trim().to_string();
        (a, "default".to_string(), rest)
    };

    let mut params = Map::new();
    if !args_str.is_empty() {
        let re_flag =
            Regex::new(r#"--([a-zA-Z0-9_-]+)(?:\s+(?:"([^"]*)"|'([^']*)'|([^\s]+)))?"#)
                .expect("regex");
        for cap in re_flag.captures_iter(&args_str) {
            let key = cap[1].to_string();
            let val = cap
                .get(2)
                .or_else(|| cap.get(3))
                .or_else(|| cap.get(4))
                .map(|m| Value::String(m.as_str().to_string()))
                .unwrap_or(Value::Bool(true));
            params.insert(key, val);
        }
    }

    json!({
        "app": app,
        "action": action,
        "params": params,
        "raw": trimmed
    })
}

async fn run_legacy_expression(expr: &str, json_mode: bool) -> i32 {
    let stages_raw: Vec<&str> = expr.split('|').map(str::trim).filter(|s| !s.is_empty()).collect();
    if stages_raw.is_empty() {
        eprintln!("Error: Empty pipeline expression");
        return 1;
    }
    let pipeline: Vec<Value> = stages_raw.into_iter().map(parse_legacy_stage).collect();

    if !json_mode {
        println!(
            "⚡ Flowork Agentic Pipe: Executing {} stage(s)...",
            pipeline.len()
        );
        for (i, p) in pipeline.iter().enumerate() {
            println!(
                "  Stage {}: [{}::{}] with {}",
                i + 1,
                p["app"].as_str().unwrap_or(""),
                p["action"].as_str().unwrap_or(""),
                p["params"]
            );
        }
    }

    let req_data = json!({
        "pipeline": pipeline,
        "initial_payload": {}
    });

    match post_bus_http("/api/bus/pipe", &req_data).await {
        Ok(result) => {
            if json_mode {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&result).unwrap_or_else(|_| "{}".to_string())
                );
                return if result.get("status").and_then(|v| v.as_str()) == Some("ok") {
                    0
                } else {
                    1
                };
            }
            if result.get("status").and_then(|v| v.as_str()) == Some("ok") {
                println!(
                    "\n✓ Pipeline [{}] COMPLETED ({} stages)!",
                    result["pipeline_id"].as_str().unwrap_or(""),
                    result["stages_completed"]
                );
                if let Some(arr) = result.get("results").and_then(|v| v.as_array()) {
                    for r in arr {
                        let out_s = r["output"].to_string();
                        let clipped = if out_s.len() > 80 {
                            format!("{}...", &out_s[..77])
                        } else {
                            out_s
                        };
                        println!(
                            "  • Stage {} [{}::{}]: {}",
                            r["stage"],
                            r["target"].as_str().unwrap_or(""),
                            r["action"].as_str().unwrap_or(""),
                            clipped
                        );
                    }
                }
                0
            } else {
                eprintln!(
                    "Pipeline failed at Stage {} [{}]: {}",
                    result["failed_stage"],
                    result["target"].as_str().unwrap_or("unknown"),
                    result["error"]
                        .as_str()
                        .or_else(|| result["message"].as_str())
                        .unwrap_or("unknown error")
                );
                1
            }
        }
        Err(e) => {
            eprintln!("Failed to dispatch pipeline to Neural Bus: {}", e);
            1
        }
    }
}

fn parse_kv_input(raw: &str, map: &mut Map<String, Value>) {
    if let Some((k, v)) = raw.split_once('=') {
        let key = k.trim().to_string();
        let val_str = v.trim();
        let val = if val_str == "true" {
            Value::Bool(true)
        } else if val_str == "false" {
            Value::Bool(false)
        } else if let Ok(i) = val_str.parse::<i64>() {
            json!(i)
        } else {
            Value::String(val_str.to_string())
        };
        map.insert(key, val);
    }
}

fn cmd_validate(args: &[String], json_mode: bool) -> i32 {
    let Some(target) = args.iter().find(|a| !a.starts_with('-')) else {
        eprintln!("Usage: flowork-pipe validate <file.flowpipe|id> [--json]");
        return 1;
    };
    let (spec, path) = match load_flowpipe_from_path_or_id(target) {
        Ok(v) => v,
        Err(e) => {
            if json_mode {
                println!("{}", json!({ "valid": false, "errors": [e] }));
            } else {
                eprintln!("Validation error: {}", e);
            }
            return 1;
        }
    };
    let rep = validate_flowpipe(&spec);
    if json_mode {
        println!(
            "{}",
            serde_json::to_string_pretty(&rep).unwrap_or_else(|_| "{}".to_string())
        );
    } else if rep.valid {
        println!(
            "✓ Valid .flowpipe DAG [{}] ({}, {} nodes, {} layers)",
            rep.id,
            path.display(),
            rep.node_count,
            rep.topo_layers.len()
        );
        for (i, layer) in rep.topo_layers.iter().enumerate() {
            println!("  Layer {}: {}", i + 1, layer.join(", "));
        }
        for w in &rep.warnings {
            println!("  Warning: {}", w);
        }
    } else {
        eprintln!("❌ Invalid .flowpipe [{}]:", rep.id);
        for e in &rep.errors {
            eprintln!("  - {}", e);
        }
    }
    if rep.valid { 0 } else { 1 }
}

fn cmd_list(json_mode: bool) -> i32 {
    let entries = discover_pipelines();
    if json_mode {
        let arr: Vec<Value> = entries
            .iter()
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
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({ "status": "ok", "pipelines": arr }))
                .unwrap_or_else(|_| "{}".to_string())
        );
        return 0;
    }
    if entries.is_empty() {
        println!("No .flowpipe manifests found in /opt/floworkos/pipelines or ~/.flowork/pipelines.");
        return 0;
    }
    println!("⚡ Flowpipe Studio Manifests ({}):", entries.len());
    for p in entries {
        println!(
            "  • [{}] {} ({} nodes, {}) — {}",
            p.scope, p.id, p.node_count, p.name, p.path
        );
    }
    0
}

async fn cmd_run(args: &[String], json_mode: bool) -> i32 {
    let mut target: Option<String> = None;
    let mut inputs = Map::new();
    let mut no_cache = false;
    let mut background = false;
    let mut local_only = false;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--input" | "-i" => {
                if let Some(kv) = args.get(i + 1) {
                    parse_kv_input(kv, &mut inputs);
                    i += 1;
                }
            }
            "--no-cache" => no_cache = true,
            "--async" | "--background" => background = true,
            "--local" | "--offline" => local_only = true,
            "--json" => {}
            other if !other.starts_with('-') && target.is_none() => {
                target = Some(other.to_string());
            }
            _ => {}
        }
        i += 1;
    }

    let Some(tgt) = target else {
        eprintln!("Usage: flowork-pipe run <file.flowpipe|id> [--input k=v] [--no-cache] [--async] [--local] [--json]");
        return 1;
    };

    if !local_only {
        let mut req_map = Map::new();
        if Path::new(&tgt).is_file() {
            if let Ok(raw) = fs::read_to_string(&tgt) {
                req_map.insert("toml".to_string(), Value::String(raw));
            } else {
                req_map.insert("path".to_string(), Value::String(tgt.clone()));
            }
        } else {
            req_map.insert("id".to_string(), Value::String(tgt.clone()));
        }
        req_map.insert("type".to_string(), Value::String("pipe_run".to_string()));
        req_map.insert("inputs".to_string(), Value::Object(inputs.clone()));
        req_map.insert("no_cache".to_string(), Value::Bool(no_cache));
        req_map.insert("background".to_string(), Value::Bool(background));

        if let Ok(res) = dispatch_rpc(Value::Object(req_map), "/api/bus/pipe/run", true).await {
            if json_mode {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&res).unwrap_or_else(|_| "{}".to_string())
                );
            } else {
                let st = res["status"].as_str().unwrap_or("error");
                if st == "ok" || st == "accepted" {
                    println!(
                        "✓ Flowpipe [{}] {} (run_id={}, {}ms, cache_hits={}, llm_calls={})",
                        res["pipeline_id"].as_str().unwrap_or(&tgt),
                        st,
                        res["run_id"].as_str().unwrap_or(""),
                        res["duration_ms"].as_u64().unwrap_or(0),
                        res["cache_hits"].as_u64().unwrap_or(0),
                        res["llm_calls"].as_u64().unwrap_or(0)
                    );
                } else {
                    eprintln!(
                        "❌ Flowpipe [{}] failed: {}",
                        tgt,
                        res["error"].as_str().unwrap_or("unknown error")
                    );
                }
            }
            let ok = matches!(res["status"].as_str(), Some("ok") | Some("accepted"));
            return if ok { 0 } else { 1 };
        }
    }

    // Fallback or explicit --local execution
    let (spec, _) = match load_flowpipe_from_path_or_id(&tgt) {
        Ok(v) => v,
        Err(e) => {
            if json_mode {
                println!("{}", json!({ "status": "error", "error": e }));
            } else {
                eprintln!("{}", e);
            }
            return 1;
        }
    };
    let ctrl = Arc::new(RunControl::new(format!("local_{}", std::process::id())));
    let res = execute_flowpipe_dag(spec, inputs, !no_cache, ctrl, None).await;
    if json_mode {
        println!(
            "{}",
            serde_json::to_string_pretty(&res).unwrap_or_else(|_| "{}".to_string())
        );
    } else if res.status == "ok" {
        println!(
            "✓ Flowpipe [{}] completed locally ({}ms, cache_hits={}, llm_calls=0)",
            res.pipeline_id, res.duration_ms, res.cache_hits
        );
    } else {
        eprintln!(
            "❌ Flowpipe [{}] failed: {}",
            res.pipeline_id,
            res.error.as_deref().unwrap_or("unknown")
        );
    }
    if res.status == "ok" { 0 } else { 1 }
}

async fn cmd_control(op: &str, args: &[String], json_mode: bool) -> i32 {
    let run_id = args.iter().find(|a| !a.starts_with('-')).cloned().unwrap_or_default();
    let (msg, endpoint, is_post) = match op {
        "runs" => (json!({ "type": "pipe_runs" }), "/api/bus/pipe/runs", false),
        "pause" => (
            json!({ "type": "pipe_pause", "run_id": run_id }),
            "/api/bus/pipe/pause",
            true,
        ),
        "resume" => (
            json!({ "type": "pipe_resume", "run_id": run_id }),
            "/api/bus/pipe/resume",
            true,
        ),
        "cancel" => (
            json!({ "type": "pipe_cancel", "run_id": run_id }),
            "/api/bus/pipe/cancel",
            true,
        ),
        _ => return 1,
    };

    match dispatch_rpc(msg, endpoint, is_post).await {
        Ok(res) => {
            if json_mode {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&res).unwrap_or_else(|_| "{}".to_string())
                );
            } else {
                println!("{}", res);
            }
            if res["status"].as_str() == Some("ok") { 0 } else { 1 }
        }
        Err(e) => {
            eprintln!("Neural Bus control error: {}", e);
            1
        }
    }
}

async fn cmd_record(args: &[String], json_mode: bool) -> i32 {
    let mut name = String::from("captured_macro");
    let mut duration_secs: u64 = 10;
    let mut out_path: Option<PathBuf> = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--name" | "-n" => {
                if let Some(v) = args.get(i + 1) {
                    name = v.clone();
                    i += 1;
                }
            }
            "--duration" | "-d" => {
                if let Some(v) = args.get(i + 1).and_then(|s| s.parse().ok()) {
                    duration_secs = v;
                    i += 1;
                }
            }
            "--out" | "-o" => {
                if let Some(v) = args.get(i + 1) {
                    out_path = Some(PathBuf::from(v));
                    i += 1;
                }
            }
            _ => {}
        }
        i += 1;
    }

    let sse_url = format!("{}/api/bus/subscribe", bus_http_base());
    if !json_mode {
        println!(
            "🎙️ Flowpipe Recorder listening on {} for {}s (macro='{}')...",
            sse_url, duration_secs, name
        );
    }

    let client = reqwest::Client::new();
    let mut captured: Vec<Value> = Vec::new();
    let deadline = Instant::now() + Duration::from_secs(duration_secs.clamp(1, 300));

    if let Ok(resp) = client
        .get(&sse_url)
        .timeout(Duration::from_secs(duration_secs.clamp(1, 300) + 5))
        .send()
        .await
    {
        let mut stream = resp.bytes_stream();
        let mut buf = String::new();
        while Instant::now() < deadline {
            let rem = deadline.saturating_duration_since(Instant::now());
            tokio::select! {
                _ = tokio::signal::ctrl_c() => break,
                _ = tokio::time::sleep(rem) => break,
                chunk = stream.next() => {
                    let Some(Ok(bytes)) = chunk else { break };
                    buf.push_str(&String::from_utf8_lossy(&bytes));
                    while let Some(pos) = buf.find('\n') {
                        let line = buf[..pos].trim().to_string();
                        buf.drain(..=pos);
                        if let Some(json_str) = line.strip_prefix("data:") {
                            if let Ok(v) = serde_json::from_str::<Value>(json_str.trim()) {
                                let t = v.get("type").and_then(|x| x.as_str()).unwrap_or("");
                                if t != "connected" && !t.starts_with("pipe.") {
                                    captured.push(v);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    let spec = synthesize_flowpipe_from_events(&name, &captured);
    let toml_out = toml::to_string_pretty(&spec).unwrap_or_default();
    let dest = out_path.unwrap_or_else(|| {
        user_pipelines_dir().join(format!("{}.flowpipe", spec.id))
    });
    if let Some(parent) = dest.parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Err(e) = fs::write(&dest, &toml_out) {
        eprintln!("Failed saving recorded .flowpipe to {}: {}", dest.display(), e);
        return 1;
    }

    if json_mode {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "status": "ok",
                "id": spec.id,
                "path": dest,
                "captured_events": captured.len(),
                "nodes": spec.nodes.len()
            }))
            .unwrap_or_default()
        );
    } else {
        println!(
            "✓ Saved deterministic macro [{}] ({} nodes from {} captured bus events) -> {}",
            spec.id,
            spec.nodes.len(),
            captured.len(),
            dest.display()
        );
    }
    0
}

#[tokio::main]
async fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() || args.iter().any(|a| a == "--help" || a == "-h") {
        println!("flowork-pipe — Flowpipe Studio Pure Rust DAG Orchestrator & Legacy Pipe Client");
        println!("Usage:");
        println!("  flowork-pipe validate <file.flowpipe|id> [--json]");
        println!("  flowork-pipe run <file.flowpipe|id> [--input k=v] [--no-cache] [--async] [--local] [--json]");
        println!("  flowork-pipe list [--json]");
        println!("  flowork-pipe record --name <macro> [--duration 10] [--out path] [--json]");
        println!("  flowork-pipe runs|pause|resume|cancel [run_id] [--json]");
        println!("  flowork-pipe [--json] \"<app1>::<action> [--params] | <app2>::<action>\"");
        return;
    }

    if args.iter().any(|a| a == "--check") {
        println!("flowork-pipe-rs: OK (Flowpipe Studio Pure Rust DAG engine)");
        return;
    }

    let json_mode = args.iter().any(|a| a == "--json");
    let first = args[0].as_str();

    // Check `--json "app1 | app2"` order as used by QC-03
    if first == "--json" {
        let rest: Vec<String> = args.iter().skip(1).cloned().collect();
        if let Some(sub) = rest.first().map(String::as_str) {
            if matches!(sub, "validate" | "run" | "list" | "record" | "runs" | "pause" | "resume" | "cancel") {
                let code = match sub {
                    "validate" => cmd_validate(&rest[1..], true),
                    "list" => cmd_list(true),
                    "run" => cmd_run(&rest[1..], true).await,
                    "record" => cmd_record(&rest[1..], true).await,
                    other => cmd_control(other, &rest[1..], true).await,
                };
                std::process::exit(code);
            }
        }
        let expr = rest.join(" ");
        std::process::exit(run_legacy_expression(&expr, true).await);
    }

    let code = match first {
        "validate" => cmd_validate(&args[1..], json_mode),
        "list" => cmd_list(json_mode),
        "run" => cmd_run(&args[1..], json_mode).await,
        "record" => cmd_record(&args[1..], json_mode).await,
        "runs" | "pause" | "resume" | "cancel" => cmd_control(first, &args[1..], json_mode).await,
        other if other.ends_with(".flowpipe") && Path::new(other).is_file() => {
            let _ = parse_flowpipe_str(&fs::read_to_string(other).unwrap_or_default(), Some(Path::new(other)));
            cmd_run(&args, json_mode).await
        }
        _ => {
            let filtered: Vec<String> = args.into_iter().filter(|a| a != "--json").collect();
            let expr = filtered.join(" ");
            run_legacy_expression(&expr, json_mode).await
        }
    };
    std::process::exit(code);
}
