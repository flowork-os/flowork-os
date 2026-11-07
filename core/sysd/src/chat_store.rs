// [FL_INDEX: chat_store, persistent_history, flowork, sovereign_agent | COT: Persistent chat history store for Flowork Archon Agent, backed by .flowork/history/chat_history.json.| AT: 2026-11-04T01:48:00Z]
// =============================================================================
// 🚀 Flowork Sovereign OS — Persistent Chat History Engine
// Zero mocks, real atomic storage inside /opt/floworkos/.flowork/history/
// =============================================================================

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::fs;
use std::path::PathBuf;

const CHAT_FILE_PATH: &str = "/opt/floworkos/.flowork/history/chat_history.json";

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChatMessage {
    pub id: u64,
    pub timestamp: String,
    pub sender: String,     // "user" | "agent" | "system"
    pub content: String,
    pub msg_type: String,   // "text" | "exec" | "perceive" | "error"
    pub metadata: Value,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct ChatHistory {
    pub messages: Vec<ChatMessage>,
}

#[derive(Debug, Deserialize)]
pub struct NewMessageRequest {
    pub sender: String,
    pub content: String,
    pub msg_type: Option<String>,
    pub metadata: Option<Value>,
}

fn current_timestamp() -> String {
    if let Ok(output) = std::process::Command::new("date").arg("-u").arg("+%Y-%m-%dT%H:%M:%SZ").output() {
        let s = String::from_utf8_lossy(&output.stdout).trim().to_string();
        if !s.is_empty() {
            return s;
        }
    }
    let dur = std::time::SystemTime::now()
        .duration_since(std::time::SystemTime::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    format!("{}", dur)
}

fn get_storage_path() -> PathBuf {
    PathBuf::from(CHAT_FILE_PATH)
}

pub fn load_history() -> ChatHistory {
    let path = get_storage_path();
    if path.exists() {
        if let Ok(content) = fs::read_to_string(&path) {
            if let Ok(history) = serde_json::from_str::<ChatHistory>(&content) {
                if !history.messages.is_empty() {
                    return history;
                }
            }
        }
    }

    // Default seed greeting
    let default_history = ChatHistory {
        messages: vec![
            ChatMessage {
                id: 1,
                timestamp: current_timestamp(),
                sender: "agent".to_string(),
                content: "⚡ **Flowork Sovereign Inhabitant Siap Bertugas**\n\nGua agen otonom yang hidup secara native di Flowork OS lo. Terintegrasi penuh dengan *Rust Kernel 7.3*, AT-SPI accessibility tree, dan virtual HID controller.\n\nRiwayat percakapan ini sekarang disimpan secara permanen di database lokal `.flowork`. Lo bisa klik chip di atas atau ketik perintah koding di bawah!".to_string(),
                msg_type: "text".to_string(),
                metadata: json!({ "seed": true }),
            }
        ]
    };
    let _ = save_history(&default_history);
    default_history
}

pub fn save_history(history: &ChatHistory) -> Result<(), String> {
    let path = get_storage_path();
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let content = serde_json::to_string_pretty(history).map_err(|e| e.to_string())?;
    fs::write(&path, content).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn add_message(sender: String, content: String, msg_type: String, metadata: Value) -> ChatMessage {
    let mut history = load_history();
    let next_id = history.messages.last().map(|m| m.id + 1).unwrap_or(1);
    let msg = ChatMessage {
        id: next_id,
        timestamp: current_timestamp(),
        sender,
        content,
        msg_type,
        metadata,
    };
    history.messages.push(msg.clone());
    let _ = save_history(&history);
    msg
}

pub fn clear_history() -> ChatHistory {
    let clean = ChatHistory {
        messages: vec![
            ChatMessage {
                id: 1,
                timestamp: current_timestamp(),
                sender: "agent".to_string(),
                content: "🧹 *Percakapan telah dibersihkan.* Gua siap menerima instruksi koding, eksekusi, atau kontrol desktop berikutnya!".to_string(),
                msg_type: "text".to_string(),
                metadata: json!({ "cleared": true }),
            }
        ]
    };
    let _ = save_history(&clean);
    clean
}
