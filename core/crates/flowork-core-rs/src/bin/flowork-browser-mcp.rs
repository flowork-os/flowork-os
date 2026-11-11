use flowork_core_rs::{cdp, DEFAULT_TOOLS_DIR};
use serde_json::{json, Value};
use std::env;
use std::fs;
use std::io::{self, BufRead, Write};
use std::path::PathBuf;

fn print_help() {
    println!("flowork-browser-mcp — Flowork OS Sovereign CDP MCP Server");
    println!("Usage: flowork-browser-mcp [--check] [--help] [--headless] [--no-usage-statistics] [--userDataDir=<dir>] [--browserUrl=<url>]");
}

fn load_browser_tool_schemas() -> Vec<Value> {
    let tools_dir = env::var("FLOWORK_TOOLS_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from(DEFAULT_TOOLS_DIR));
    let mut tools = Vec::new();
    if let Ok(entries) = fs::read_dir(&tools_dir) {
        let mut dirs: Vec<PathBuf> = entries
            .flatten()
            .filter_map(|e| {
                let p = e.path();
                let name = e.file_name().to_string_lossy().to_string();
                (p.is_dir() && name.starts_with("browser_") && name != "browser_backend").then_some(p)
            })
            .collect();
        dirs.sort();

        for d in dirs {
            let mf = d.join("manifest.json");
            let Ok(raw) = fs::read_to_string(&mf) else {
                continue;
            };
            let Ok(val) = serde_json::from_str::<Value>(&raw) else {
                continue;
            };
            let Some(full_name) = val.get("name").and_then(|v| v.as_str()) else {
                continue;
            };
            let short_name = cdp::normalize_short_name(full_name);
            let desc = val
                .get("description")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let input_schema = val
                .get("parametersJsonSchema")
                .cloned()
                .unwrap_or_else(|| json!({"type":"object","properties":{}}));
            tools.push(json!({
                "name": short_name,
                "description": desc,
                "inputSchema": input_schema
            }));
        }
    }
    tools
}

#[tokio::main]
async fn main() {
    let mut user_data_dir: Option<String> = None;

    for arg in env::args().skip(1) {
        match arg.as_str() {
            "--help" | "-h" => {
                print_help();
                return;
            }
            "--check" => {
                println!("flowork-browser-mcp: OK (native Rust CDP)");
                return;
            }
            other if other.starts_with("--userDataDir=") => {
                user_data_dir = Some(other.trim_start_matches("--userDataDir=").to_string());
            }
            other if other.starts_with("--browserUrl=") => {
                env::set_var(
                    "FLOWORK_BROWSER_URL",
                    other.trim_start_matches("--browserUrl="),
                );
            }
            _ => {}
        }
    }

    let stdin = io::stdin();
    let mut stdout = io::stdout();
    let reader = stdin.lock();

    for line_res in reader.lines() {
        let Ok(line) = line_res else {
            break;
        };
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let msg: Value = match serde_json::from_str(trimmed) {
            Ok(v) => v,
            Err(e) => {
                let err_resp = json!({
                    "jsonrpc": "2.0",
                    "id": Value::Null,
                    "error": { "code": -32700, "message": format!("Parse error: {}", e) }
                });
                let _ = writeln!(stdout, "{}", err_resp);
                let _ = stdout.flush();
                continue;
            }
        };

        let id = msg.get("id").cloned();
        let method = msg.get("method").and_then(|v| v.as_str()).unwrap_or("");
        let params = msg.get("params").cloned().unwrap_or_else(|| json!({}));

        if id.is_none() || method == "notifications/initialized" {
            continue;
        }
        let req_id = id.unwrap();

        let response = match method {
            "initialize" => json!({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": { "tools": {} },
                    "serverInfo": {
                        "name": "flowork-browser-mcp",
                        "version": "2.0.0-sovereign"
                    }
                }
            }),
            "ping" => json!({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }),
            "tools/list" => json!({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": load_browser_tool_schemas()
                }
            }),
            "tools/call" => {
                let tool_name = params.get("name").and_then(|v| v.as_str()).unwrap_or("");
                let args = params.get("arguments").cloned().unwrap_or_else(|| json!({}));
                match cdp::call_browser_tool(tool_name, &args, user_data_dir.as_deref()).await {
                    Ok(res) => json!({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": res
                    }),
                    Err(e) => json!({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32000,
                            "message": e
                        }
                    }),
                }
            }
            other => json!({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": format!("Method '{}' not found", other)
                }
            }),
        };

        if writeln!(stdout, "{}", response).is_err() {
            break;
        }
        let _ = stdout.flush();
    }
}
