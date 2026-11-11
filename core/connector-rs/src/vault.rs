use base64::engine::general_purpose::{STANDARD, URL_SAFE_NO_PAD};
use base64::Engine;
use chrono::Utc;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::sync::Mutex;
use uuid::Uuid;

use crate::config::ConfigManager;
use crate::paths::ConnectorPaths;

pub fn now_ms() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis() as i64)
        .unwrap_or(0)
}

pub fn base36_u64(mut n: u64) -> String {
    if n == 0 {
        return "0".to_string();
    }
    const CHARS: &[u8] = b"0123456789abcdefghijklmnopqrstuvwxyz";
    let mut out = Vec::new();
    while n > 0 {
        out.push(CHARS[(n % 36) as usize]);
        n /= 36;
    }
    out.reverse();
    String::from_utf8(out).unwrap_or_else(|_| "0".to_string())
}

pub fn new_account_id() -> String {
    let ts = base36_u64(now_ms().max(0) as u64);
    let u = Uuid::new_v4().simple().to_string();
    format!("acc_{}_{}", ts, &u[..4])
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Account {
    #[serde(default = "new_account_id")]
    pub id: String,
    #[serde(default)]
    pub email: String,
    #[serde(default)]
    pub name: String,
    #[serde(default)]
    pub access_token: String,
    #[serde(default)]
    pub refresh_token: String,
    #[serde(default)]
    pub expires_at: i64,
    #[serde(default)]
    pub client_id: String,
    #[serde(default = "default_ready")]
    pub status: String,
    #[serde(default)]
    pub cooldown_until: i64,
    #[serde(default)]
    pub requests_count: u64,
    #[serde(default)]
    pub errors_count: u64,
    #[serde(default)]
    pub added_at: String,
    #[serde(default)]
    pub last_used_at: String,
    #[serde(default)]
    pub error_message: String,
    #[serde(flatten)]
    pub extra: HashMap<String, Value>,
}

fn default_ready() -> String {
    "ready".to_string()
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PkceSession {
    pub verifier: String,
    #[serde(rename = "redirectUri", default)]
    pub redirect_uri: String,
    #[serde(default)]
    pub provider: String,
    #[serde(rename = "createdAt", default)]
    pub created_at: i64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SessionTicket {
    pub port: u16,
    pub created_at: i64,
    pub expires_at: i64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VaultData {
    #[serde(default = "default_provider_name")]
    pub active_provider: String,
    #[serde(default)]
    pub active_account_id: String,
    #[serde(default = "default_rotation_mode")]
    pub rotation_mode: String,
    #[serde(default)]
    pub flowork_token: String,
    #[serde(default)]
    pub flowork_user: Option<Value>,
    #[serde(default)]
    pub is_logged_out: bool,
    #[serde(default)]
    pub accounts: Vec<Account>,
    #[serde(default)]
    pub providers: Option<Value>,
    #[serde(default)]
    pub session_tickets: HashMap<String, SessionTicket>,
    #[serde(default)]
    pub pending_oauth_sessions: HashMap<String, PkceSession>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_ticket: Option<String>,
    #[serde(flatten)]
    pub extra: HashMap<String, Value>,
}

fn default_provider_name() -> String {
    "connector".to_string()
}

fn default_rotation_mode() -> String {
    "failover".to_string()
}

pub struct VaultManager {
    vault_path: PathBuf,
    pub config: Arc<ConfigManager>,
    pub http: Client,
    io_lock: Mutex<()>,
    tickets: Mutex<HashMap<String, SessionTicket>>,
    pkce_sessions: Mutex<HashMap<String, PkceSession>>,
}

impl VaultManager {
    pub fn new(paths: &ConnectorPaths, config: Arc<ConfigManager>, http: Client) -> Self {
        Self {
            vault_path: paths.data_file("vault.json"),
            config,
            http,
            io_lock: Mutex::new(()),
            tickets: Mutex::new(HashMap::new()),
            pkce_sessions: Mutex::new(HashMap::new()),
        }
    }

    fn enforce_private_permissions(path: &std::path::Path) {
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            if let Err(e) = fs::set_permissions(path, fs::Permissions::from_mode(0o600)) {
                eprintln!(
                    "[Rotator] Warning enforcing 0600 permissions on {}: {}",
                    path.display(),
                    e
                );
            }
        }
        #[cfg(not(unix))]
        let _ = path;
    }

    pub async fn load_vault(&self) -> VaultData {
        let _guard = self.io_lock.lock().await;
        self.load_vault_unlocked()
    }

    fn load_vault_unlocked(&self) -> VaultData {
        let settings = self.config.get_settings();
        if self.vault_path.exists() {
            Self::enforce_private_permissions(&self.vault_path);
            match fs::read_to_string(&self.vault_path) {
                Ok(raw) => match serde_json::from_str::<VaultData>(&raw) {
                    Ok(mut v) => {
                        if v.rotation_mode.is_empty() {
                            v.rotation_mode = settings.default_rotation_mode.clone();
                        }
                        if v.active_provider.is_empty() || v.active_provider == "google" {
                            v.active_provider = "connector".to_string();
                        }
                        for acc in &mut v.accounts {
                            if acc.id.is_empty() {
                                acc.id = new_account_id();
                            }
                            if acc.name.is_empty() && !acc.email.is_empty() {
                                acc.name = acc.email.split('@').next().unwrap_or("account").to_string();
                            }
                            if acc.status.is_empty() {
                                acc.status = "ready".to_string();
                            }
                        }
                        return v;
                    }
                    Err(e) => {
                        eprintln!("[Rotator] Error parsing vault file: {}", e);
                    }
                },
                Err(e) => {
                    eprintln!("[Rotator] Error reading vault file: {}", e);
                }
            }
        }

        let default_vault = VaultData {
            active_provider: "connector".to_string(),
            active_account_id: String::new(),
            rotation_mode: settings.default_rotation_mode,
            flowork_token: String::new(),
            flowork_user: None,
            is_logged_out: false,
            accounts: Vec::new(),
            providers: None,
            session_tickets: HashMap::new(),
            pending_oauth_sessions: HashMap::new(),
            last_ticket: None,
            extra: HashMap::new(),
        };
        self.save_vault_unlocked(&default_vault);
        default_vault
    }

    pub async fn save_vault(&self, vault: &VaultData) {
        let _guard = self.io_lock.lock().await;
        self.save_vault_unlocked(vault);
    }

    fn save_vault_unlocked(&self, vault: &VaultData) {
        if let Some(dir) = self.vault_path.parent() {
            if !dir.exists() {
                let _ = fs::create_dir_all(dir);
            }
        }
        let tmp_path = PathBuf::from(format!(
            "{}.tmp.{}.{}",
            self.vault_path.display(),
            std::process::id(),
            now_ms()
        ));
        match serde_json::to_string_pretty(vault) {
            Ok(serialized) => {
                #[cfg(unix)]
                let write_res: std::io::Result<()> = (|| {
                    use std::io::Write;
                    use std::os::unix::fs::{OpenOptionsExt, PermissionsExt};
                    let mut f = fs::OpenOptions::new()
                        .write(true)
                        .create(true)
                        .truncate(true)
                        .mode(0o600)
                        .open(&tmp_path)?;
                    f.write_all(serialized.as_bytes())?;
                    f.sync_all()?;
                    fs::set_permissions(&tmp_path, fs::Permissions::from_mode(0o600))?;
                    Ok(())
                })();
                #[cfg(not(unix))]
                let write_res: std::io::Result<()> = fs::write(&tmp_path, serialized);

                if let Err(e) = write_res {
                    eprintln!("[Rotator] Error writing temp vault file: {}", e);
                    let _ = fs::remove_file(&tmp_path);
                    return;
                }
                if let Err(e) = fs::rename(&tmp_path, &self.vault_path) {
                    eprintln!("[Rotator] Error renaming vault file: {}", e);
                    let _ = fs::remove_file(&tmp_path);
                    return;
                }
                Self::enforce_private_permissions(&self.vault_path);
            }
            Err(e) => {
                eprintln!("[Rotator] Error serializing vault: {}", e);
            }
        }
    }

    pub fn open_url_in_browser(&self, target_url: &str) -> bool {
        let trimmed = target_url.trim();
        if !(trimmed.starts_with("http://") || trimmed.starts_with("https://")) {
            return false;
        }
        let disp = std::env::var("DISPLAY")
            .ok()
            .filter(|s| !s.is_empty())
            .unwrap_or_else(|| ":0".to_string());
        let target = trimmed.to_string();

        std::thread::spawn(move || {
            let launched = Command::new("xdg-open")
                .arg(&target)
                .env("DISPLAY", &disp)
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .is_ok();
            if !launched {
                let chrome_ok = Command::new("google-chrome-stable")
                    .arg(&target)
                    .env("DISPLAY", &disp)
                    .stdin(Stdio::null())
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .spawn()
                    .is_ok();
                if !chrome_ok {
                    let _ = Command::new("gio")
                        .args(["open", &target])
                        .env("DISPLAY", &disp)
                        .stdin(Stdio::null())
                        .stdout(Stdio::null())
                        .stderr(Stdio::null())
                        .spawn();
                }
            }
            std::thread::sleep(Duration::from_millis(300));
            let _ = Command::new("wmctrl")
                .args(["-xa", "google-chrome"])
                .env("DISPLAY", &disp)
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn();
        });
        true
    }

    pub async fn create_session_ticket(&self, port: u16) -> (String, String) {
        let now = now_ms();
        let rand_hex = &Uuid::new_v4().simple().to_string()[..16];
        let ticket = format!("flw_tkt_{}_{}", base36_u64(now.max(0) as u64), rand_hex);
        let entry = SessionTicket {
            port,
            created_at: now,
            expires_at: now + 1_800_000,
        };
        {
            let mut guard = self.tickets.lock().await;
            guard.insert(ticket.clone(), entry.clone());
        }
        let mut vault = self.load_vault().await;
        vault.session_tickets.insert(ticket.clone(), entry);
        vault.last_ticket = Some(ticket.clone());
        self.save_vault(&vault).await;
        let gate_url = format!("https://auth.floworkos.com/?ticket={}&port={}", ticket, port);
        (ticket, gate_url)
    }

    #[allow(dead_code)]
    pub async fn resolve_session_ticket(&self, ticket: &str) -> Option<SessionTicket> {
        if ticket.is_empty() {
            return None;
        }
        {
            let mut guard = self.tickets.lock().await;
            if let Some(found) = guard.remove(ticket) {
                return Some(found);
            }
        }
        let mut vault = self.load_vault().await;
        if let Some(found) = vault.session_tickets.remove(ticket) {
            self.save_vault(&vault).await;
            return Some(found);
        }
        None
    }

    pub async fn verify_flowork_token(&self, token: &str) -> Result<Value, String> {
        if token.trim().is_empty() {
            return Err("Token missing".to_string());
        }
        let res = self
            .http
            .get("https://auth.floworkos.com/api/auth/verify")
            .header("Authorization", format!("Bearer {}", token))
            .header("User-Agent", "MrFlow-Connector/1.0")
            .timeout(Duration::from_secs(6))
            .send()
            .await
            .map_err(|e| format!("Verification request failed: {}", e))?;

        let body: Value = res.json().await.map_err(|e| e.to_string())?;
        let valid = body.get("valid").and_then(|v| v.as_bool()).unwrap_or(false);
        if valid {
            if let Some(user) = body.get("user") {
                return Ok(user.clone());
            }
        }
        let err_msg = body
            .get("error")
            .and_then(|v| v.as_str())
            .unwrap_or("Token invalid")
            .to_string();
        Err(err_msg)
    }

    pub async fn pull_cloud_vault(&self, token_override: Option<&str>) -> Result<Value, String> {
        let mut vault = self.load_vault().await;
        let token = token_override
            .map(|s| s.to_string())
            .unwrap_or_else(|| vault.flowork_token.clone());
        if token.is_empty() {
            return Err("No active session token from auth.floworkos.com".to_string());
        }

        let res = self
            .http
            .get("https://auth.floworkos.com/api/connector/vault")
            .header("Authorization", format!("Bearer {}", token))
            .header("User-Agent", "MrFlow-Connector/1.0")
            .timeout(Duration::from_secs(8))
            .send()
            .await
            .map_err(|e| format!("Cloud vault request failed: {}", e))?;

        let data: Value = res
            .json()
            .await
            .map_err(|e| format!("Invalid response from cloud vault: {}", e))?;

        let success = data.get("success").and_then(|v| v.as_bool()).unwrap_or(false);
        let exists = data.get("exists").and_then(|v| v.as_bool()).unwrap_or(false);
        if success && exists {
            if let Some(cloud_v) = data.get("vault") {
                let raw_accounts = cloud_v
                    .get("accounts")
                    .and_then(|v| v.as_array())
                    .cloned()
                    .unwrap_or_default();
                let mut accounts = Vec::new();
                for item in raw_accounts {
                    let email = item.get("email").and_then(|v| v.as_str()).unwrap_or("").to_string();
                    let access_token = item
                        .get("access_token")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    let refresh_token = item
                        .get("refresh_token")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    if email.is_empty() || (access_token.is_empty() && refresh_token.is_empty()) {
                        continue;
                    }
                    let id = item
                        .get("id")
                        .and_then(|v| v.as_str())
                        .filter(|s| !s.is_empty())
                        .map(|s| s.to_string())
                        .unwrap_or_else(new_account_id);
                    let name = item
                        .get("name")
                        .and_then(|v| v.as_str())
                        .filter(|s| !s.is_empty())
                        .map(|s| s.to_string())
                        .unwrap_or_else(|| email.split('@').next().unwrap_or("account").to_string());
                    let now_iso = Utc::now().to_rfc3339();
                    accounts.push(Account {
                        id,
                        email,
                        name,
                        access_token,
                        refresh_token,
                        expires_at: item.get("expires_at").and_then(|v| v.as_i64()).unwrap_or(0),
                        client_id: item.get("client_id").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                        status: item
                            .get("status")
                            .and_then(|v| v.as_str())
                            .unwrap_or("ready")
                            .to_string(),
                        cooldown_until: 0,
                        requests_count: item.get("requests_count").and_then(|v| v.as_u64()).unwrap_or(0),
                        errors_count: item.get("errors_count").and_then(|v| v.as_u64()).unwrap_or(0),
                        added_at: item
                            .get("added_at")
                            .and_then(|v| v.as_str())
                            .map(|s| s.to_string())
                            .unwrap_or_else(|| now_iso.clone()),
                        last_used_at: item
                            .get("last_used_at")
                            .and_then(|v| v.as_str())
                            .map(|s| s.to_string())
                            .unwrap_or(now_iso),
                        error_message: String::new(),
                        extra: HashMap::new(),
                    });
                }

                if !accounts.is_empty() {
                    vault.active_account_id = cloud_v
                        .get("active_account_id")
                        .and_then(|v| v.as_str())
                        .filter(|s| !s.is_empty())
                        .map(|s| s.to_string())
                        .unwrap_or_else(|| accounts[0].id.clone());
                }
                if let Some(rm) = cloud_v.get("rotation_mode").and_then(|v| v.as_str()) {
                    if !rm.is_empty() {
                        vault.rotation_mode = rm.to_string();
                    }
                }
                let count = accounts.len();
                vault.accounts = accounts;
                self.save_vault(&vault).await;
                println!(
                    "[Rotator] ☁️ Successfully synchronized {} accounts from auth.floworkos.com Cloud Vault!",
                    count
                );
                return Ok(json!({
                    "success": true,
                    "count": count,
                    "accounts": vault.accounts,
                    "active_account_id": vault.active_account_id
                }));
            }
        }

        if success && !exists {
            return Ok(json!({
                "success": true,
                "count": 0,
                "accounts": [],
                "message": "Cloud vault exists but has no accounts stored yet."
            }));
        }

        Err(data
            .get("error")
            .and_then(|v| v.as_str())
            .unwrap_or("Failed to parse cloud vault")
            .to_string())
    }

    pub async fn push_cloud_vault(&self, vault_override: Option<&VaultData>) -> Result<Value, String> {
        let owned;
        let vault = match vault_override {
            Some(v) => v,
            None => {
                owned = self.load_vault().await;
                &owned
            }
        };
        if vault.flowork_token.is_empty() {
            return Err("Not authenticated".to_string());
        }

        let mapped_accounts: Vec<Value> = vault
            .accounts
            .iter()
            .map(|a| {
                json!({
                    "id": a.id,
                    "email": a.email,
                    "name": a.name,
                    "access_token": a.access_token,
                    "refresh_token": a.refresh_token,
                    "expires_at": a.expires_at,
                    "status": if a.status.is_empty() { "ready" } else { &a.status },
                    "added_at": a.added_at,
                    "last_used_at": a.last_used_at
                })
            })
            .collect();

        let payload = json!({
            "vault": {
                "active_provider": "google",
                "rotation_mode": if vault.rotation_mode.is_empty() { "failover" } else { &vault.rotation_mode },
                "active_account_id": vault.active_account_id,
                "accounts": mapped_accounts,
                "last_updated": Utc::now().to_rfc3339()
            }
        });

        let res = self
            .http
            .post("https://auth.floworkos.com/api/connector/vault")
            .header("Authorization", format!("Bearer {}", vault.flowork_token))
            .header("User-Agent", "MrFlow-Connector/1.0")
            .json(&payload)
            .timeout(Duration::from_secs(8))
            .send()
            .await
            .map_err(|e| e.to_string())?;

        let data: Value = res.json().await.map_err(|e| e.to_string())?;
        let ok = data.get("success").and_then(|v| v.as_bool()).unwrap_or(false);
        Ok(json!({ "success": ok, "data": data }))
    }

    pub fn parse_jwt_claims(token: &str) -> Option<Value> {
        let parts: Vec<&str> = token.split('.').collect();
        if parts.len() < 2 {
            return None;
        }
        let payload_b64 = parts[1];
        let decoded = URL_SAFE_NO_PAD
            .decode(payload_b64)
            .or_else(|_| STANDARD.decode(payload_b64))
            .ok()?;
        let text = String::from_utf8(decoded).ok()?;
        serde_json::from_str(&text).ok()
    }

    pub async fn fetch_google_userinfo(&self, access_token: &str) -> Result<Value, String> {
        let res = self
            .http
            .get("https://www.googleapis.com/oauth2/v3/userinfo")
            .header("Authorization", format!("Bearer {}", access_token))
            .header("User-Agent", "MrFlowConnector/1.0")
            .timeout(Duration::from_secs(8))
            .send()
            .await
            .map_err(|e| e.to_string())?;
        res.json::<Value>().await.map_err(|e| e.to_string())
    }

    pub async fn generate_login_url(&self, port: u16) -> Result<Value, String> {
        let mut raw_bytes = [0u8; 32];
        let u1 = Uuid::new_v4();
        let u2 = Uuid::new_v4();
        raw_bytes[..16].copy_from_slice(u1.as_bytes());
        raw_bytes[16..].copy_from_slice(u2.as_bytes());

        let verifier = URL_SAFE_NO_PAD.encode(raw_bytes);
        let challenge_bytes = Sha256::digest(verifier.as_bytes());
        let code_challenge = URL_SAFE_NO_PAD.encode(challenge_bytes);

        let now = now_ms();
        let rand_hex = &Uuid::new_v4().simple().to_string()[..12];
        let state = format!("flw_multi_{}_{}_{}", port, base36_u64(now.max(0) as u64), rand_hex);
        let redirect_uri = "http://localhost:51121/oauth-callback".to_string();

        let session = PkceSession {
            verifier: verifier.clone(),
            redirect_uri: redirect_uri.clone(),
            provider: "antigravity".to_string(),
            created_at: now,
        };
        {
            let mut guard = self.pkce_sessions.lock().await;
            guard.insert(state.clone(), session.clone());
        }
        let mut vault = self.load_vault().await;
        vault.pending_oauth_sessions.insert(state.clone(), session);
        self.save_vault(&vault).await;

        let init_payload = json!({
            "provider": "antigravity",
            "state": state,
            "codeChallenge": code_challenge,
            "redirectUri": redirect_uri
        });

        if let Ok(res) = self
            .http
            .post("https://auth.floworkos.com/api/auth/oauth/init")
            .json(&init_payload)
            .timeout(Duration::from_secs(8))
            .send()
            .await
        {
            if let Ok(d) = res.json::<Value>().await {
                if let Some(auth_url) = d.get("authUrl").and_then(|v| v.as_str()) {
                    return Ok(json!({
                        "loginUrl": auth_url,
                        "state": state,
                        "redirectUri": redirect_uri
                    }));
                }
            }
        }

        let fallback = format!(
            "https://auth.floworkos.com/api/auth/oauth/init?provider=antigravity&state={}&redirectUri={}&codeChallenge={}",
            urlencoding::encode(&state),
            urlencoding::encode(&redirect_uri),
            urlencoding::encode(&code_challenge)
        );
        Ok(json!({
            "loginUrl": fallback,
            "state": state,
            "redirectUri": redirect_uri
        }))
    }

    pub async fn take_pkce_session(&self, state: &str, vault: &mut VaultData) -> Option<PkceSession> {
        let mem = {
            let mut guard = self.pkce_sessions.lock().await;
            guard.remove(state)
        };
        let disk = vault.pending_oauth_sessions.remove(state);
        mem.or(disk)
    }

    pub async fn exchange_oauth_code(
        &self,
        code: &str,
        verifier: &str,
        redirect_uri: &str,
    ) -> Result<Value, String> {
        let vault = self.load_vault().await;
        let payload = json!({
            "code": code,
            "verifier": verifier,
            "code_verifier": verifier,
            "provider": "antigravity",
            "redirectUri": if redirect_uri.is_empty() { "http://localhost:51121/oauth-callback" } else { redirect_uri }
        });

        let mut req = self
            .http
            .post("https://auth.floworkos.com/api/auth/oauth/exchange")
            .header("User-Agent", "MrFlow-Connector/1.0")
            .json(&payload)
            .timeout(Duration::from_secs(15));
        if !vault.flowork_token.is_empty() {
            req = req.header("Authorization", format!("Bearer {}", vault.flowork_token));
        }

        let res = req.send().await.map_err(|e| e.to_string())?;
        let s: Value = res.json().await.map_err(|e| e.to_string())?;
        let success = s.get("success").and_then(|v| v.as_bool()).unwrap_or(false);
        let access_token = s
            .get("accessToken")
            .or_else(|| s.get("access_token"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        if success && !access_token.is_empty() {
            let refresh_token = s
                .get("refreshToken")
                .or_else(|| s.get("refresh_token"))
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();
            let expires_in = s
                .get("expiresIn")
                .or_else(|| s.get("expires_in"))
                .and_then(|v| v.as_i64())
                .unwrap_or(3600);
            let id_token = s
                .get("idToken")
                .or_else(|| s.get("id_token"))
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();
            let email = s
                .get("email")
                .or_else(|| s.pointer("/user/email"))
                .or_else(|| s.get("user_email"))
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();
            return Ok(json!({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                "id_token": id_token,
                "email": email
            }));
        }

        Err(s
            .get("error")
            .and_then(|v| v.as_str())
            .unwrap_or("Token exchange failed")
            .to_string())
    }

    pub async fn refresh_account_token(&self, acc: &mut Account, force: bool) -> Value {
        if acc.refresh_token.is_empty() {
            return json!({ "refreshed": false, "reason": "NO_REFRESH_TOKEN" });
        }
        let settings = self.config.get_settings();
        let margin_ms = settings.token_refresh_margin_sec * 1000;
        let now = now_ms();
        if !force && acc.expires_at > 0 && (acc.expires_at - now) > margin_ms {
            return json!({
                "refreshed": false,
                "reason": "TOKEN_STILL_VALID",
                "access_token": acc.access_token
            });
        }

        let vault = self.load_vault().await;
        let payload = json!({
            "refreshToken": acc.refresh_token,
            "provider": "antigravity"
        });
        let mut req = self
            .http
            .post("https://auth.floworkos.com/api/auth/oauth/refresh")
            .header("User-Agent", "MrFlow-Connector/1.0")
            .json(&payload)
            .timeout(Duration::from_secs(10));
        if !vault.flowork_token.is_empty() {
            req = req.header("Authorization", format!("Bearer {}", vault.flowork_token));
        }

        match req.send().await {
            Ok(resp) => match resp.json::<Value>().await {
                Ok(s) => {
                    let success = s.get("success").and_then(|v| v.as_bool()).unwrap_or(false);
                    let access = s
                        .get("accessToken")
                        .or_else(|| s.get("access_token"))
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    if success && !access.is_empty() {
                        acc.access_token = access.clone();
                        if let Some(rt) = s
                            .get("refreshToken")
                            .or_else(|| s.get("refresh_token"))
                            .and_then(|v| v.as_str())
                        {
                            if !rt.is_empty() {
                                acc.refresh_token = rt.to_string();
                            }
                        }
                        let exp_sec = s
                            .get("expiresIn")
                            .or_else(|| s.get("expires_in"))
                            .and_then(|v| v.as_i64())
                            .unwrap_or(3600);
                        acc.expires_at = now_ms() + exp_sec * 1000;
                        acc.status = "active".to_string();
                        acc.error_message.clear();
                        println!("[Rotator] ✅ Token refreshed for {} (valid for {}s)", acc.email, exp_sec);
                        json!({ "refreshed": true, "access_token": access })
                    } else {
                        let err = s
                            .get("error")
                            .and_then(|v| v.as_str())
                            .unwrap_or("Refresh failed")
                            .to_string();
                        acc.status = "error".to_string();
                        acc.error_message = err.clone();
                        eprintln!("[Rotator] Refresh failed for {}: {}", acc.email, err);
                        json!({ "refreshed": false, "error": err })
                    }
                }
                Err(e) => json!({ "refreshed": false, "error": e.to_string() }),
            },
            Err(e) => {
                let msg = if e.is_timeout() {
                    "Token refresh timed out".to_string()
                } else {
                    e.to_string()
                };
                json!({ "refreshed": false, "error": msg })
            }
        }
    }

    pub async fn ensure_account_token_valid(&self, acc: &mut Account) -> bool {
        let settings = self.config.get_settings();
        let margin_ms = settings.token_refresh_margin_sec * 1000;
        let now = now_ms();
        if !acc.access_token.is_empty() && acc.expires_at > 0 && (acc.expires_at - now) > margin_ms {
            return true;
        }
        let details = self.refresh_account_token(acc, true).await;
        let refreshed = details.get("refreshed").and_then(|v| v.as_bool()).unwrap_or(false);
        let has_err = details.get("error").is_some();
        refreshed || !has_err
    }

    pub fn select_next_available_index(vault: &mut VaultData, exclude_id: Option<&str>) -> Option<usize> {
        if vault.accounts.is_empty() {
            return None;
        }
        let now = now_ms();
        if let Some(idx) = vault.accounts.iter().position(|a| {
            a.id == vault.active_account_id
                && exclude_id.map_or(true, |ex| a.id != ex)
                && a.cooldown_until <= now
                && a.status != "error"
        }) {
            return Some(idx);
        }

        if let Some(idx) = vault.accounts.iter().position(|a| {
            exclude_id.map_or(true, |ex| a.id != ex) && a.cooldown_until <= now && a.status != "error"
        }) {
            vault.active_account_id = vault.accounts[idx].id.clone();
            return Some(idx);
        }

        let idx = vault
            .accounts
            .iter()
            .position(|a| exclude_id.map_or(true, |ex| a.id != ex))
            .unwrap_or(0);
        vault.active_account_id = vault.accounts[idx].id.clone();
        Some(idx)
    }

    pub async fn mark_account_cooldown(&self, account_id: &str, cooldown_sec: Option<u64>, reason: &str) {
        let mut vault = self.load_vault().await;
        let Some(pos) = vault.accounts.iter().position(|a| a.id == account_id) else {
            return;
        };
        let settings = self.config.get_settings();
        let duration_sec = cooldown_sec.unwrap_or(settings.cooldown_duration_sec);
        let mut acc = vault.accounts.remove(pos);
        acc.cooldown_until = now_ms() + (duration_sec as i64) * 1000;
        acc.status = "cooldown".to_string();
        acc.errors_count = acc.errors_count.saturating_add(1);
        acc.error_message = reason.to_string();
        eprintln!(
            "[Rotator] 🛑 Account [{}] entered cooldown for {}s ({}). Moving to end of queue.",
            acc.email, duration_sec, reason
        );
        vault.accounts.push(acc);
        if let Some(next_idx) = Self::select_next_available_index(&mut vault, Some(account_id)) {
            let next_email = vault.accounts[next_idx].email.clone();
            vault.active_account_id = vault.accounts[next_idx].id.clone();
            println!("[Rotator] 🔀 Switched active account to next in line: [{}]", next_email);
        }
        self.save_vault(&vault).await;
    }

    pub async fn clear_all_cooldowns(&self) -> usize {
        let mut vault = self.load_vault().await;
        let now = now_ms();
        let mut count = 0;
        for acc in &mut vault.accounts {
            if acc.cooldown_until > now || acc.status == "cooldown" || acc.status == "error" {
                acc.cooldown_until = 0;
                acc.status = "ready".to_string();
                acc.error_message.clear();
                count += 1;
            }
        }
        self.save_vault(&vault).await;
        println!("[Rotator] ⚡ Cleared cooldowns and errors for {} accounts.", count);
        count
    }

    pub fn spawn_background_keeper(self: Arc<Self>) {
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(60));
            interval.tick().await; // skip immediate first tick
            loop {
                interval.tick().await;
                let mut vault = self.load_vault().await;
                if vault.flowork_token.is_empty() || vault.accounts.is_empty() {
                    continue;
                }
                let margin_ms = self.config.get_settings().token_refresh_margin_sec * 1000;
                let now = now_ms();
                let mut changed = false;
                for acc in &mut vault.accounts {
                    if !acc.refresh_token.is_empty() && acc.expires_at > 0 && (acc.expires_at - now) <= margin_ms {
                        println!(
                            "[Rotator Keeper] Proactively refreshing expiring token for: {}",
                            acc.email
                        );
                        self.refresh_account_token(acc, true).await;
                        changed = true;
                    }
                }
                if changed {
                    self.save_vault(&vault).await;
                }
            }
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_paths(label: &str) -> (PathBuf, ConnectorPaths) {
        let root = std::env::temp_dir().join(format!(
            "flowork_vault_test_{}_{}_{}",
            label,
            std::process::id(),
            Uuid::new_v4().simple()
        ));
        let paths = ConnectorPaths {
            base_dir: root.clone(),
            config_dir: root.join("config"),
            data_dir: root.join("data"),
            logs_dir: root.join("logs"),
            gui_dir: root.join("gui"),
        };
        paths.ensure_structure();
        (root, paths)
    }

    #[cfg(unix)]
    #[tokio::test]
    async fn save_and_load_enforce_0600_permissions() {
        use std::os::unix::fs::PermissionsExt;

        let (root, paths) = test_paths("perms");
        let cfg = Arc::new(ConfigManager::new(paths.clone()));
        let vm = VaultManager::new(&paths, cfg, Client::new());

        let _ = vm.load_vault().await;
        let initial_mode = fs::metadata(&vm.vault_path).unwrap().permissions().mode() & 0o777;
        assert_eq!(initial_mode, 0o600);

        // Simulate legacy 0664 exposure, verify load hardens back to 0600
        fs::set_permissions(&vm.vault_path, fs::Permissions::from_mode(0o664)).unwrap();
        let mut vault = vm.load_vault().await;
        let reloaded_mode = fs::metadata(&vm.vault_path).unwrap().permissions().mode() & 0o777;
        assert_eq!(reloaded_mode, 0o600);

        // Simulate 0664 before save, verify atomic rename preserves 0600 despite default umask
        fs::set_permissions(&vm.vault_path, fs::Permissions::from_mode(0o664)).unwrap();
        vault.rotation_mode = "round-robin".to_string();
        vm.save_vault(&vault).await;
        let saved_mode = fs::metadata(&vm.vault_path).unwrap().permissions().mode() & 0o777;
        assert_eq!(saved_mode, 0o600);

        let _ = fs::remove_dir_all(&root);
    }
}

