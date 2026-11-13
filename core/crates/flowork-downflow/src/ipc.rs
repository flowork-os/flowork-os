// 👑 FLOWORK OS SOVEREIGN DOWNFLOW - IPC PROTOCOL & SERVER
// Clean-room IPC server under Apache-2.0

use crate::models::{DownloadItem, DownloadStatus, StateManager};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

#[derive(Debug, Serialize, Deserialize)]
pub struct IpcMetadata {
    pub port: u16,
    pub token: String,
    pub pid: u32,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "action", content = "payload")]
pub enum IpcRequest {
    Add {
        url: String,
        file_name: Option<String>,
        category: Option<String>,
        later: Option<bool>,
    },
    List {
        status: Option<String>,
        search: Option<String>,
        limit: Option<usize>,
    },
    Pause {
        ids: Vec<u64>,
    },
    Resume {
        ids: Vec<u64>,
    },
    Remove {
        ids: Vec<u64>,
        delete_files: Option<bool>,
    },
    StartQueue,
    Ping,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct IpcResponse {
    pub success: bool,
    pub message: Option<String>,
    pub data: Option<serde_json::Value>,
}

pub struct IpcServer {
    state: StateManager,
    token: String,
}

impl IpcServer {
    pub fn new(state: StateManager) -> Self {
        let token = format!("{:x}", rand_u128());
        Self { state, token }
    }

    pub async fn run(&self) -> Result<(), Box<dyn std::error::Error>> {
        let listener = TcpListener::bind("127.0.0.1:0").await?;
        let port = listener.local_addr()?.port();

        // Write ipc.json for discovery by CLI, MCP, and NMHost
        Self::write_ipc_file(port, &self.token)?;

        loop {
            if let Ok((mut stream, _)) = listener.accept().await {
                let state = self.state.clone();
                let server_token = self.token.clone();

                tokio::spawn(async move {
                    let _ = Self::handle_client(&mut stream, state, &server_token).await;
                });
            }
        }
    }

    async fn handle_client(
        stream: &mut TcpStream,
        state: StateManager,
        _server_token: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let mut buf = vec![0u8; 65536];
        let n = stream.read(&mut buf).await?;
        if n == 0 {
            return Ok(());
        }

        let req_str = String::from_utf8_lossy(&buf[..n]);
        // Support both HTTP POST and raw JSON IPC
        let body = if req_str.starts_with("POST ") || req_str.starts_with("GET ") {
            if let Some(pos) = req_str.find("\r\n\r\n") {
                &req_str[pos + 4..]
            } else {
                "{}"
            }
        } else {
            req_str.trim()
        };

        let response = match serde_json::from_str::<IpcRequest>(body) {
            Ok(IpcRequest::Add { url, file_name, category, later }) => {
                let item = state.add(url, file_name, category);
                IpcResponse {
                    success: true,
                    message: Some("Download added".to_string()),
                    data: Some(serde_json::to_value(item).unwrap_or_default()),
                }
            }
            Ok(IpcRequest::List { status, search, limit }) => {
                let mut items = state.list();
                if let Some(st) = status {
                    items.retain(|i| i.status.to_string().eq_ignore_ascii_case(&st));
                }
                if let Some(query) = search {
                    let q = query.to_lowercase();
                    items.retain(|i| i.file_name.to_lowercase().contains(&q) || i.url.to_lowercase().contains(&q));
                }
                if let Some(lim) = limit {
                    items.truncate(lim);
                }
                IpcResponse {
                    success: true,
                    message: None,
                    data: Some(serde_json::to_value(items).unwrap_or_default()),
                }
            }
            Ok(IpcRequest::Pause { ids }) => {
                for id in &ids {
                    state.update_status(*id, DownloadStatus::Paused, None);
                }
                IpcResponse {
                    success: true,
                    message: Some(format!("Paused {} downloads", ids.len())),
                    data: Some(serde_json::json!({ "done": ids, "skipped": [] })),
                }
            }
            Ok(IpcRequest::Resume { ids }) => {
                for id in &ids {
                    state.update_status(*id, DownloadStatus::Queued, None);
                }
                IpcResponse {
                    success: true,
                    message: Some(format!("Resumed {} downloads", ids.len())),
                    data: Some(serde_json::json!({ "done": ids, "skipped": [] })),
                }
            }
            Ok(IpcRequest::Remove { ids, delete_files }) => {
                let del = delete_files.unwrap_or(false);
                let mut done = Vec::new();
                for id in &ids {
                    if state.remove(*id, del) {
                        done.push(*id);
                    }
                }
                IpcResponse {
                    success: true,
                    message: Some(format!("Removed {} downloads", done.len())),
                    data: Some(serde_json::json!({ "done": done, "skipped": [] })),
                }
            }
            Ok(IpcRequest::StartQueue) | Ok(IpcRequest::Ping) => IpcResponse {
                success: true,
                message: Some("OK".to_string()),
                data: None,
            },
            Err(e) => IpcResponse {
                success: false,
                message: Some(format!("Invalid request: {}", e)),
                data: None,
            },
        };

        let res_json = serde_json::to_string(&response).unwrap_or_default();
        if req_str.starts_with("POST ") || req_str.starts_with("GET ") {
            let http_res = format!(
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                res_json.len(),
                res_json
            );
            stream.write_all(http_res.as_bytes()).await?;
        } else {
            stream.write_all(res_json.as_bytes()).await?;
        }

        Ok(())
    }

    fn write_ipc_file(port: u16, token: &str) -> std::io::Result<()> {
        let meta = IpcMetadata {
            port,
            token: token.to_string(),
            pid: std::process::id(),
        };
        let content = serde_json::to_string(&meta)?;

        if let Ok(home) = std::env::var("HOME") {
            let p1 = PathBuf::from(&home).join(".local/share/flowork/downflow/ipc.json");
            if let Some(p) = p1.parent() {
                let _ = fs::create_dir_all(p);
            }
            let _ = fs::write(&p1, &content);

            // Also mirror to legacy path for seamless backwards compatibility
            let p2 = PathBuf::from(&home).join(".local/share/misterdownloadmanager/ipc.json");
            if let Some(p) = p2.parent() {
                let _ = fs::create_dir_all(p);
            }
            let _ = fs::write(&p2, &content);
        }

        Ok(())
    }
}

pub struct IpcClient;

impl IpcClient {
    pub fn read_metadata() -> Option<IpcMetadata> {
        let home = std::env::var("HOME").ok()?;
        let p1 = PathBuf::from(&home).join(".local/share/flowork/downflow/ipc.json");
        if let Ok(content) = fs::read_to_string(&p1) {
            if let Ok(m) = serde_json::from_str::<IpcMetadata>(&content) {
                return Some(m);
            }
        }
        let p2 = PathBuf::from(&home).join(".local/share/misterdownloadmanager/ipc.json");
        if let Ok(content) = fs::read_to_string(&p2) {
            if let Ok(m) = serde_json::from_str::<IpcMetadata>(&content) {
                return Some(m);
            }
        }
        None
    }

    pub async fn send_request(req: IpcRequest) -> Result<IpcResponse, String> {
        let meta = Self::read_metadata().ok_or_else(|| "DownFlow daemon is not running".to_string())?;
        let addr = format!("127.0.0.1:{}", meta.port);
        let mut stream = TcpStream::connect(&addr).await.map_err(|e| e.to_string())?;

        let body = serde_json::to_string(&req).map_err(|e| e.to_string())?;
        stream.write_all(body.as_bytes()).await.map_err(|e| e.to_string())?;

        let mut buf = vec![0u8; 65536];
        let n = stream.read(&mut buf).await.map_err(|e| e.to_string())?;
        let res_str = String::from_utf8_lossy(&buf[..n]);

        serde_json::from_str::<IpcResponse>(&res_str).map_err(|e| e.to_string())
    }
}

fn rand_u128() -> u128 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let d = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default();
    (d.as_nanos() ^ (std::process::id() as u128))
}
