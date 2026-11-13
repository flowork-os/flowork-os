// 👑 FLOWORK OS SOVEREIGN DOWNFLOW - CHROME NATIVE MESSAGING HOST
// Clean-room stdio host protocol under Apache-2.0

#[path = "../ipc.rs"]
mod ipc;
#[path = "../models.rs"]
mod models;

use ipc::{IpcClient, IpcRequest};
use serde::{Deserialize, Serialize};
use std::io::{self, Read, Write};

#[derive(Debug, Deserialize)]
struct ExtensionDownloadMsg {
    url: Option<String>,
    #[serde(rename = "finalUrl")]
    final_url: Option<String>,
    filename: Option<String>,
    referrer: Option<String>,
    size: Option<u64>,
}

#[derive(Debug, Serialize)]
struct HostResponse {
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    message: Option<String>,
}

#[tokio::main]
async fn main() {
    let mut stdin = io::stdin();
    let mut stdout = io::stdout();

    loop {
        // Read 4-byte little-endian message length prefix
        let mut len_buf = [0u8; 4];
        if stdin.read_exact(&mut len_buf).is_err() {
            break; // Browser closed pipe
        }

        let msg_len = u32::from_ne_bytes(len_buf) as usize;
        if msg_len == 0 || msg_len > 10 * 1024 * 1024 {
            break;
        }

        let mut msg_buf = vec![0u8; msg_len];
        if stdin.read_exact(&mut msg_buf).is_err() {
            break;
        }

        let parsed: Result<ExtensionDownloadMsg, _> = serde_json::from_slice(&msg_buf);
        let resp = match parsed {
            Ok(msg) => {
                let download_url = msg.final_url.or(msg.url);
                if let Some(url) = download_url {
                    let _ = IpcClient::send_request(IpcRequest::Add {
                        url,
                        file_name: msg.filename,
                        category: None,
                        later: None,
                    }).await;
                    HostResponse { ok: true, message: Some("Download queued".to_string()) }
                } else {
                    HostResponse { ok: false, message: Some("No URL provided".to_string()) }
                }
            }
            Err(e) => HostResponse { ok: false, message: Some(e.to_string()) },
        };

        let resp_json = serde_json::to_vec(&resp).unwrap_or_default();
        let resp_len = (resp_json.len() as u32).to_ne_bytes();

        let _ = stdout.write_all(&resp_len);
        let _ = stdout.write_all(&resp_json);
        let _ = stdout.flush();
    }
}
