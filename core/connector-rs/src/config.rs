use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::RwLock;
use std::time::SystemTime;

use crate::paths::ConnectorPaths;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ModelEntry {
    pub id: String,
    pub name: String,
    #[serde(default = "default_owned_by")]
    pub owned_by: String,
}

fn default_owned_by() -> String {
    "flowork".to_string()
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ModelsConfig {
    #[serde(default = "default_model_id")]
    pub default_model: String,
    #[serde(default)]
    pub catalog: Vec<ModelEntry>,
}

fn default_model_id() -> String {
    "gemini-3.8-flash-high".to_string()
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct NetworkConfig {
    #[serde(default = "default_upstream_host")]
    pub upstream_host: String,
    #[serde(default = "default_user_agent")]
    pub user_agent: String,
    #[serde(default)]
    pub default_headers: HashMap<String, String>,
    #[serde(default = "default_timeout_ms")]
    pub timeout_ms: u64,
    #[serde(default = "default_max_retries")]
    pub max_retry_attempts: usize,
}

fn default_upstream_host() -> String {
    "https://daily-cloudcode-pa.googleapis.com".to_string()
}

fn default_user_agent() -> String {
    "antigravity/2.8.1".to_string()
}

fn default_timeout_ms() -> u64 {
    90000
}

fn default_max_retries() -> usize {
    6
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SettingsConfig {
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default = "default_host")]
    pub host: String,
    #[serde(default = "default_max_accounts")]
    pub max_accounts: usize,
    #[serde(default = "default_rotation")]
    pub default_rotation_mode: String,
    #[serde(default = "default_cooldown")]
    pub cooldown_duration_sec: u64,
    #[serde(default = "default_refresh_margin")]
    pub token_refresh_margin_sec: i64,
    #[serde(default = "default_true")]
    pub offline_resilience: bool,
    #[serde(default = "default_true")]
    pub enable_local_cache: bool,
    #[serde(default = "default_true")]
    pub enable_privacy_shield: bool,
    #[serde(default = "default_sysd_url")]
    pub sysd_url: String,
}

fn default_true() -> bool {
    true
}

fn default_sysd_url() -> String {
    std::env::var("FLOWORK_SYSD_URL")
        .ok()
        .filter(|s| !s.trim().is_empty())
        .unwrap_or_else(|| "http://127.0.0.1:18090".to_string())
}

fn default_port() -> u16 {
    9099
}

fn default_host() -> String {
    "127.0.0.1".to_string()
}

fn default_max_accounts() -> usize {
    50
}

fn default_rotation() -> String {
    "failover".to_string()
}

fn default_cooldown() -> u64 {
    60
}

fn default_refresh_margin() -> i64 {
    300
}

pub fn default_providers_value() -> Value {
    json!({
        "connector": {
            "id": "connector",
            "name": "Sovereign Connector",
            "badge": "GOOGLE PRO POOL",
            "type": "google_multi_account",
            "desc": "Multi-Account Google Pro Rotator with automatic 429 quota failover."
        },
        "ollama": {
            "id": "ollama",
            "name": "Ollama Local Engine",
            "badge": "LOCAL GPU",
            "type": "ollama",
            "host": "http://127.0.0.1:11434",
            "default_model": "deepseek-v4-9b-uncensored:latest",
            "custom_models": [
                "deepseek-v4-9b-uncensored:latest",
                "qwen2.5-coder:7b",
                "qwen2.5-coder:1.5b"
            ],
            "desc": "Direct offline inference via your local GPU without internet dependence."
        },
        "9router": {
            "id": "9router",
            "name": "9Router Universal Gateway",
            "badge": "ROUTED PROXY",
            "type": "openai_proxy",
            "host": "http://127.0.0.1:20128",
            "api_key": "",
            "default_model": "clinepass/cline-pass/glm-5.2",
            "custom_models": [
                "clinepass/cline-pass/glm-5.2",
                "deepseek/deepseek-r1",
                "openai/gpt-4o",
                "anthropic/claude-3.5-sonnet"
            ],
            "desc": "Universal proxy gateway routing requests to 9Router or OpenAI-compatible backends."
        }
    })
}

pub struct ConfigManager {
    paths: ConnectorPaths,
    cache: RwLock<HashMap<PathBuf, (SystemTime, Value)>>,
}

impl ConfigManager {
    pub fn new(paths: ConnectorPaths) -> Self {
        let mgr = Self {
            paths,
            cache: RwLock::new(HashMap::new()),
        };
        mgr.init_defaults();
        mgr
    }

    fn init_defaults(&self) {
        let models_path = self.paths.config_file("models.json");
        if !models_path.exists() {
            let def = json!({
                "default_model": "gemini-3.8-flash-high",
                "catalog": [{
                    "id": "gemini-3.8-flash-high",
                    "name": "Gemini 3.8 Flash (High)",
                    "owned_by": "flowork"
                }]
            });
            let _ = fs::write(&models_path, serde_json::to_string_pretty(&def).unwrap_or_default());
        }

        let network_path = self.paths.config_file("network.json");
        if !network_path.exists() {
            let def = json!({
                "upstream_host": "https://daily-cloudcode-pa.googleapis.com",
                "user_agent": "antigravity/2.8.1",
                "default_headers": {
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json",
                    "Connection": "close"
                },
                "timeout_ms": 90000,
                "max_retry_attempts": 6
            });
            let _ = fs::write(&network_path, serde_json::to_string_pretty(&def).unwrap_or_default());
        }

        let providers_path = self.paths.config_file("providers.json");
        if !providers_path.exists() {
            let def = default_providers_value();
            let _ = fs::write(&providers_path, serde_json::to_string_pretty(&def).unwrap_or_default());
        }

        let settings_path = self.paths.config_file("settings.json");
        if !settings_path.exists() {
            let def = json!({
                "port": 9099,
                "host": "127.0.0.1",
                "max_accounts": 50,
                "default_rotation_mode": "failover",
                "cooldown_duration_sec": 60,
                "token_refresh_margin_sec": 300,
                "offline_resilience": true,
                "enable_local_cache": true,
                "enable_privacy_shield": true
            });
            let _ = fs::write(&settings_path, serde_json::to_string_pretty(&def).unwrap_or_default());
        }
    }

    pub fn read_json_cached(&self, name: &str, fallback: Value) -> Value {
        let file_path = self.paths.config_file(name);
        let Ok(meta) = fs::metadata(&file_path) else {
            return fallback;
        };
        let Ok(mtime) = meta.modified() else {
            return fallback;
        };

        if let Ok(guard) = self.cache.read() {
            if let Some((cached_time, val)) = guard.get(&file_path) {
                if *cached_time == mtime {
                    return val.clone();
                }
            }
        }

        match fs::read_to_string(&file_path) {
            Ok(raw) => match serde_json::from_str::<Value>(&raw) {
                Ok(parsed) => {
                    if let Ok(mut guard) = self.cache.write() {
                        guard.insert(file_path, (mtime, parsed.clone()));
                    }
                    parsed
                }
                Err(e) => {
                    eprintln!("[ConfigManager] Warning parsing {}: {}", name, e);
                    self.cache
                        .read()
                        .ok()
                        .and_then(|g| g.get(&file_path).map(|(_, v)| v.clone()))
                        .unwrap_or(fallback)
                }
            },
            Err(e) => {
                eprintln!("[ConfigManager] Warning reading {}: {}", name, e);
                fallback
            }
        }
    }

    pub fn get_models(&self) -> ModelsConfig {
        let val = self.read_json_cached(
            "models.json",
            json!({ "default_model": "gemini-3.8-flash-high", "catalog": [] }),
        );
        serde_json::from_value(val).unwrap_or(ModelsConfig {
            default_model: "gemini-3.8-flash-high".to_string(),
            catalog: Vec::new(),
        })
    }

    pub fn get_network(&self) -> NetworkConfig {
        let val = self.read_json_cached(
            "network.json",
            json!({
                "upstream_host": "https://daily-cloudcode-pa.googleapis.com",
                "user_agent": "antigravity/2.8.1",
                "default_headers": {
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json"
                },
                "timeout_ms": 90000,
                "max_retry_attempts": 6
            }),
        );
        serde_json::from_value(val).unwrap_or(NetworkConfig {
            upstream_host: "https://daily-cloudcode-pa.googleapis.com".to_string(),
            user_agent: "antigravity/2.8.1".to_string(),
            default_headers: HashMap::new(),
            timeout_ms: 90000,
            max_retry_attempts: 6,
        })
    }

    pub fn get_providers(&self) -> Value {
        let val = self.read_json_cached("providers.json", default_providers_value());
        if let Some(inner) = val.get("providers") {
            if inner.is_object() {
                return inner.clone();
            }
        }
        val
    }

    pub fn get_settings(&self) -> SettingsConfig {
        let val = self.read_json_cached(
            "settings.json",
            json!({
                "port": 9099,
                "host": "127.0.0.1",
                "max_accounts": 50,
                "default_rotation_mode": "failover",
                "cooldown_duration_sec": 60,
                "token_refresh_margin_sec": 300,
                "offline_resilience": true,
                "enable_local_cache": true,
                "enable_privacy_shield": true
            }),
        );
        serde_json::from_value(val).unwrap_or(SettingsConfig {
            port: 9099,
            host: "127.0.0.1".to_string(),
            max_accounts: 50,
            default_rotation_mode: "failover".to_string(),
            cooldown_duration_sec: 60,
            token_refresh_margin_sec: 300,
            offline_resilience: true,
            enable_local_cache: true,
            enable_privacy_shield: true,
            sysd_url: default_sysd_url(),
        })
    }
}
