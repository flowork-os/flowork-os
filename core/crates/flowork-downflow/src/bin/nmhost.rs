// 👑 FLOWORK OS SOVEREIGN DOWNFLOW - CHROME NATIVE MESSAGING HOST
// Clean-room stdio host protocol under Apache-2.0

#[path = "../ipc.rs"]
mod ipc;
#[path = "../models.rs"]
mod models;

use ipc::{IpcClient, IpcRequest};
use serde_json::Value;
use std::io::{self, Read, Write};
use std::process::Command;
use std::time::Duration;

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

        let raw_val: Result<Value, _> = serde_json::from_slice(&msg_buf);
        let resp: Value = match raw_val {
            Ok(v) => {
                // 1. Handshake / rules query from extension
                if v.get("rules").is_some() {
                    serde_json::json!({
                        "ok": true,
                        "version": "1.0.0",
                        "types": "3gp,7z,apk,avi,bz2,deb,dmg,doc,docx,exe,flv,gz,iso,jar,mkv,mp3,mp4,mov,mpeg,mpg,msi,pdf,pkg,rar,rpm,tar,tgz,torrent,webm,wma,wmv,xz,zip",
                        "capture": true,
                        "opened": true
                    })
                }
                // 2. Open DownFlow UI request
                else if v.get("open").is_some() {
                    let _ = Command::new("/opt/floworkos/bin/downflow").spawn();
                    serde_json::json!({ "ok": true })
                }
                // 3. Open options request
                else if v.get("openOptions").is_some() {
                    serde_json::json!({ "ok": true })
                }
                // 4. Download media / file request
                else {
                    let download_url = v.get("finalUrl")
                        .or_else(|| v.get("url"))
                        .and_then(|u| u.as_str())
                        .map(|s| s.to_string());

                    if let Some(url) = download_url {
                        let filename = v.get("filename")
                            .or_else(|| v.get("fileName"))
                            .and_then(|f| f.as_str())
                            .map(|s| s.to_string());

                        // If daemon is not running, start it in background
                        if IpcClient::read_metadata().is_none() {
                            let _ = Command::new("/opt/floworkos/apps/downflow/flowork-downflow")
                                .arg("--daemon")
                                .spawn();
                            tokio::time::sleep(Duration::from_millis(300)).await;
                        }

                        let res = IpcClient::send_request(IpcRequest::Add {
                            url,
                            file_name: filename,
                            category: None,
                            later: None,
                        }).await;

                        match res {
                            Ok(_) => serde_json::json!({ "ok": true, "message": "Download queued" }),
                            Err(e) => serde_json::json!({ "ok": false, "message": e }),
                        }
                    } else {
                        serde_json::json!({ "ok": false, "message": "No URL provided" })
                    }
                }
            }
            Err(e) => serde_json::json!({ "ok": false, "message": e.to_string() }),
        };

        let resp_json = serde_json::to_vec(&resp).unwrap_or_default();
        let resp_len = (resp_json.len() as u32).to_ne_bytes();

        let _ = stdout.write_all(&resp_len);
        let _ = stdout.write_all(&resp_json);
        let _ = stdout.flush();
    }
}
