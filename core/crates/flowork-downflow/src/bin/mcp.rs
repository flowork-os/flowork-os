// 👑 FLOWORK OS SOVEREIGN DOWNFLOW - MODEL CONTEXT PROTOCOL (MCP) SERVER
// Clean-room stdio JSON-RPC MCP server for Mr. Flow AI under Apache-2.0

#[path = "../ipc.rs"]
mod ipc;
#[path = "../models.rs"]
mod models;

use ipc::{IpcClient, IpcRequest};
use models::DownloadItem;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::io::{self, BufRead, Write};

#[derive(Debug, Deserialize)]
struct JsonRpcRequest {
    jsonrpc: String,
    id: Option<Value>,
    method: String,
    params: Option<Value>,
}

#[derive(Debug, Serialize)]
struct JsonRpcResponse {
    jsonrpc: String,
    id: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<Value>,
}

#[tokio::main]
async fn main() {
    let stdin = io::stdin();
    let mut stdout = io::stdout();

    for line in stdin.lock().lines() {
        if let Ok(line_str) = line {
            if line_str.trim().is_empty() {
                continue;
            }

            if let Ok(req) = serde_json::from_str::<JsonRpcRequest>(&line_str) {
                let id = req.id.clone();
                let result = handle_mcp_method(&req.method, req.params).await;

                let resp = match result {
                    Ok(val) => JsonRpcResponse {
                        jsonrpc: "2.0".to_string(),
                        id,
                        result: Some(val),
                        error: None,
                    },
                    Err(e) => JsonRpcResponse {
                        jsonrpc: "2.0".to_string(),
                        id,
                        result: None,
                        error: Some(serde_json::json!({ "code": -32000, "message": e })),
                    },
                };

                let resp_str = serde_json::to_string(&resp).unwrap_or_default();
                let _ = writeln!(stdout, "{}", resp_str);
                let _ = stdout.flush();
            }
        }
    }
}

async fn handle_mcp_method(method: &str, params: Option<Value>) -> Result<Value, String> {
    match method {
        "initialize" => Ok(serde_json::json!({
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "flowork-downflow-mcp",
                "version": "1.0.0"
            }
        })),
        "notifications/initialized" => Ok(serde_json::json!({})),
        "tools/list" => Ok(serde_json::json!({
            "tools": [
                {
                    "name": "add_download",
                    "description": "Add a new URL to DownFlow download queue",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": { "type": "string", "description": "The URL to download" },
                            "filename": { "type": "string", "description": "Optional destination filename" },
                            "category": { "type": "string", "description": "Optional category" }
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "list_downloads",
                    "description": "List active and historical downloads with progress and status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "status": { "type": "string", "description": "Filter by status" },
                            "search": { "type": "string", "description": "Search keyword" }
                        }
                    }
                },
                {
                    "name": "pause_download",
                    "description": "Pause download by ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "id": { "type": "integer", "description": "Download item ID" }
                        },
                        "required": ["id"]
                    }
                },
                {
                    "name": "resume_download",
                    "description": "Resume download by ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "id": { "type": "integer", "description": "Download item ID" }
                        },
                        "required": ["id"]
                    }
                }
            ]
        })),
        "tools/call" => {
            let p = params.ok_or_else(|| "Missing params".to_string())?;
            let tool_name = p.get("name").and_then(|v| v.as_str()).unwrap_or("");
            let args = p.get("arguments").cloned().unwrap_or(serde_json::json!({}));

            match tool_name {
                "add_download" => {
                    let url = args.get("url").and_then(|v| v.as_str()).ok_or("url is required")?.to_string();
                    let file_name = args.get("filename").and_then(|v| v.as_str()).map(|s| s.to_string());
                    let category = args.get("category").and_then(|v| v.as_str()).map(|s| s.to_string());
                    let res = IpcClient::send_request(IpcRequest::Add { url, file_name, category, later: None }).await?;
                    Ok(serde_json::json!({
                        "content": [{ "type": "text", "text": format!("Download added: {:?}", res.data) }]
                    }))
                }
                "list_downloads" => {
                    let status = args.get("status").and_then(|v| v.as_str()).map(|s| s.to_string());
                    let search = args.get("search").and_then(|v| v.as_str()).map(|s| s.to_string());
                    let res = IpcClient::send_request(IpcRequest::List { status, search, limit: Some(20) }).await?;
                    Ok(serde_json::json!({
                        "content": [{ "type": "text", "text": serde_json::to_string_pretty(&res.data).unwrap_or_default() }]
                    }))
                }
                "pause_download" => {
                    let id = args.get("id").and_then(|v| v.as_u64()).ok_or("id is required")?;
                    let _ = IpcClient::send_request(IpcRequest::Pause { ids: vec![id] }).await?;
                    Ok(serde_json::json!({
                        "content": [{ "type": "text", "text": format!("Download {} paused", id) }]
                    }))
                }
                "resume_download" => {
                    let id = args.get("id").and_then(|v| v.as_u64()).ok_or("id is required")?;
                    let _ = IpcClient::send_request(IpcRequest::Resume { ids: vec![id] }).await?;
                    Ok(serde_json::json!({
                        "content": [{ "type": "text", "text": format!("Download {} resumed", id) }]
                    }))
                }
                _ => Err(format!("Unknown tool: {}", tool_name)),
            }
        }
        _ => Err(format!("Method not supported: {}", method)),
    }
}
