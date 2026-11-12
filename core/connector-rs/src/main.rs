mod config;
mod paths;
mod providers;
mod proxy;
mod translator;
mod vault;

use axum::body::Bytes;
use axum::extract::{Query, Request, State};
use axum::http::{HeaderValue, Method, StatusCode};
use axum::response::{Html, IntoResponse, Response};
use axum::routing::{any, get, post};
use axum::{Json, Router};
use chrono::Utc;
use reqwest::Client;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::fs;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::net::TcpListener;
use tower_http::cors::{Any, CorsLayer};

use crate::config::ConfigManager;
use crate::paths::ConnectorPaths;
use crate::providers::{
    get_effective_providers, test_9router_connectivity, test_ollama_connectivity,
};
use crate::proxy::handle_ai_proxy_request;
use crate::vault::{new_account_id, now_ms, Account, VaultManager};

const FALLBACK_INDEX_HTML: &str = include_str!("../../connector/gui/index.html");
const FALLBACK_STYLE_CSS: &str = include_str!("../../connector/gui/style.css");
const FALLBACK_APP_JS: &str = include_str!("../../connector/gui/app.js");

#[derive(Clone)]
struct AppState {
    paths: ConnectorPaths,
    config: Arc<ConfigManager>,
    vault: Arc<VaultManager>,
    http: Client,
    port: u16,
}

fn html_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#39;")
}

fn serve_gui_file(paths: &ConnectorPaths, file_name: &str, content_type: &'static str, fallback: &'static str) -> Response {
    let disk_path = paths.gui_dir.join(file_name);
    let body = fs::read_to_string(&disk_path).unwrap_or_else(|_| fallback.to_string());
    Response::builder()
        .status(StatusCode::OK)
        .header("Content-Type", HeaderValue::from_static(content_type))
        .body(axum::body::Body::from(body))
        .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response())
}

async fn handle_health() -> impl IntoResponse {
    (StatusCode::OK, Json(json!({ "status": "ok", "online": true })))
}

async fn handle_gui_index(State(st): State<AppState>) -> Response {
    serve_gui_file(&st.paths, "index.html", "text/html; charset=utf-8", FALLBACK_INDEX_HTML)
}

async fn handle_gui_css(State(st): State<AppState>) -> Response {
    serve_gui_file(&st.paths, "style.css", "text/css; charset=utf-8", FALLBACK_STYLE_CSS)
}

async fn handle_gui_app_js(State(st): State<AppState>) -> Response {
    serve_gui_file(&st.paths, "app.js", "application/javascript; charset=utf-8", FALLBACK_APP_JS)
}

async fn handle_router_status(State(st): State<AppState>) -> Response {
    let mut vault = st.vault.load_vault().await;
    let now = now_ms();
    let authenticated = !vault.flowork_token.is_empty() && vault.flowork_user.is_some();
    let cfg_providers = st.config.get_providers();

    if vault.providers.is_none() {
        vault.providers = Some(cfg_providers.clone());
        st.vault.save_vault(&vault).await;
    }

    vault.accounts.sort_by_key(|a| if a.cooldown_until > now { 1 } else { 0 });

    let accounts_view: Vec<Value> = vault
        .accounts
        .iter()
        .map(|p| {
            let in_cooldown = p.cooldown_until > now;
            let status = if in_cooldown {
                "cooldown".to_string()
            } else if p.status.is_empty() {
                "ready".to_string()
            } else {
                p.status.clone()
            };
            let cooldown_until = if in_cooldown { p.cooldown_until } else { 0 };
            let remaining_sec = if in_cooldown {
                ((p.cooldown_until - now + 999) / 1000).max(1)
            } else {
                0
            };
            let name = if p.name.is_empty() {
                p.email.split('@').next().unwrap_or("account").to_string()
            } else {
                p.name.clone()
            };
            json!({
                "id": p.id,
                "email": p.email,
                "name": name,
                "status": status,
                "cooldown_until": cooldown_until,
                "cooldown_remaining_sec": remaining_sec,
                "is_active": p.id == vault.active_account_id,
                "expires_at": p.expires_at,
                "requests_count": p.requests_count,
                "errors_count": p.errors_count,
                "added_at": p.added_at,
                "last_used_at": p.last_used_at,
                "error_message": p.error_message
            })
        })
        .collect();

    let active_email = accounts_view
        .iter()
        .find(|a| a.get("is_active").and_then(|v| v.as_bool()) == Some(true))
        .or_else(|| accounts_view.first())
        .and_then(|a| a.get("email").and_then(|v| v.as_str()))
        .unwrap_or("None")
        .to_string();

    let active_account_id = if !vault.active_account_id.is_empty() {
        vault.active_account_id.clone()
    } else {
        accounts_view
            .first()
            .and_then(|a| a.get("id").and_then(|v| v.as_str()))
            .unwrap_or("")
            .to_string()
    };

    let healthy_count = accounts_view
        .iter()
        .filter(|a| {
            let st_str = a.get("status").and_then(|v| v.as_str()).unwrap_or("");
            st_str != "cooldown" && st_str != "error"
        })
        .count();
    let cooldown_count = accounts_view
        .iter()
        .filter(|a| a.get("status").and_then(|v| v.as_str()) == Some("cooldown"))
        .count();

    let providers = get_effective_providers(&vault, &cfg_providers);
    let max_accounts = st.config.get_settings().max_accounts;

    (
        StatusCode::OK,
        Json(json!({
            "success": true,
            "connected": true,
            "authenticated": authenticated,
            "user": vault.flowork_user,
            "active_provider": if vault.active_provider.is_empty() { "connector" } else { &vault.active_provider },
            "providers": providers,
            "port": st.port,
            "total_accounts": accounts_view.len(),
            "max_accounts": max_accounts,
            "active_account_id": active_account_id,
            "active_email": active_email,
            "rotation_mode": if vault.rotation_mode.is_empty() { "failover" } else { &vault.rotation_mode },
            "healthy_count": healthy_count,
            "cooldown_count": cooldown_count,
            "accounts": accounts_view
        })),
    )
        .into_response()
}

async fn handle_provider_config(
    State(st): State<AppState>,
    method: Method,
    body: Bytes,
) -> Response {
    let mut vault = st.vault.load_vault().await;
    let cfg_providers = st.config.get_providers();
    if vault.providers.is_none() {
        vault.providers = Some(cfg_providers);
    }

    if method == Method::GET {
        return (
            StatusCode::OK,
            Json(json!({
                "success": true,
                "active_provider": if vault.active_provider.is_empty() { "connector" } else { &vault.active_provider },
                "providers": vault.providers
            })),
        )
            .into_response();
    }

    let r: Value = match serde_json::from_slice(&body) {
        Ok(v) => v,
        Err(e) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({ "success": false, "error": e.to_string() })),
            )
                .into_response();
        }
    };

    if let Some(ap) = r.get("active_provider").and_then(|v| v.as_str()) {
        if !ap.is_empty() {
            vault.active_provider = ap.to_string();
            println!("[Server] Active AI Provider set to: {}", ap);
        }
    }

    let mut prov_map = vault
        .providers
        .clone()
        .unwrap_or_else(|| json!({}));
    if !prov_map.is_object() {
        prov_map = json!({});
    }
    if let Some(root) = prov_map.as_object_mut() {
        if let Some(oll) = r.get("ollama").and_then(|v| v.as_object()) {
            let entry = root.entry("ollama".to_string()).or_insert_with(|| json!({}));
            if let Some(eobj) = entry.as_object_mut() {
                if let Some(h) = oll.get("host").and_then(|v| v.as_str()) {
                    eobj.insert("host".to_string(), json!(h));
                }
                if let Some(dm) = oll.get("default_model").and_then(|v| v.as_str()) {
                    eobj.insert("default_model".to_string(), json!(dm));
                }
                if let Some(cm) = oll.get("custom_models").and_then(|v| v.as_array()) {
                    eobj.insert("custom_models".to_string(), Value::Array(cm.clone()));
                }
            }
        }
        if let Some(r9) = r.get("9router").or_else(|| r.get("router9")).and_then(|v| v.as_object()) {
            let entry = root.entry("9router".to_string()).or_insert_with(|| json!({}));
            if let Some(eobj) = entry.as_object_mut() {
                if let Some(h) = r9.get("host").and_then(|v| v.as_str()) {
                    eobj.insert("host".to_string(), json!(h));
                }
                if let Some(ak) = r9.get("api_key").and_then(|v| v.as_str()) {
                    eobj.insert("api_key".to_string(), json!(ak));
                }
                if let Some(dm) = r9.get("default_model").and_then(|v| v.as_str()) {
                    eobj.insert("default_model".to_string(), json!(dm));
                }
                if let Some(cm) = r9.get("custom_models").and_then(|v| v.as_array()) {
                    eobj.insert("custom_models".to_string(), Value::Array(cm.clone()));
                }
            }
        }
    }
    vault.providers = Some(prov_map.clone());
    st.vault.save_vault(&vault).await;

    (
        StatusCode::OK,
        Json(json!({
            "success": true,
            "active_provider": vault.active_provider,
            "providers": prov_map
        })),
    )
        .into_response()
}

async fn handle_test_provider(State(st): State<AppState>, body: Bytes) -> Response {
    let req_json: Value = serde_json::from_slice(&body).unwrap_or_else(|_| json!({}));
    let prov = req_json
        .get("provider")
        .and_then(|v| v.as_str())
        .unwrap_or("ollama");
    let cfg_providers = st.config.get_providers();

    if prov == "ollama" {
        let host = req_json.get("host").and_then(|v| v.as_str());
        let res = test_ollama_connectivity(&st.http, host, &cfg_providers).await;
        return (StatusCode::OK, Json(res)).into_response();
    }
    if prov == "9router" {
        let host = req_json.get("host").and_then(|v| v.as_str());
        let api_key = req_json.get("api_key").and_then(|v| v.as_str());
        let res = test_9router_connectivity(&st.http, host, api_key, &cfg_providers).await;
        return (StatusCode::OK, Json(res)).into_response();
    }
    (
        StatusCode::BAD_REQUEST,
        Json(json!({ "success": false, "error": format!("Unknown provider: {}", prov) })),
    )
        .into_response()
}

async fn handle_test_ollama_get(State(st): State<AppState>) -> Response {
    let cfg_providers = st.config.get_providers();
    let res = test_ollama_connectivity(&st.http, None, &cfg_providers).await;
    (StatusCode::OK, Json(res)).into_response()
}

async fn handle_login_ticket(
    State(st): State<AppState>,
    method: Method,
    Query(q): Query<HashMap<String, String>>,
) -> Response {
    let (ticket, gate_url) = st.vault.create_session_ticket(st.port).await;
    if method == Method::GET && !q.contains_key("no_open") {
        st.vault.open_url_in_browser(&gate_url);
    }
    (
        StatusCode::OK,
        Json(json!({
            "status": "STARTED",
            "ticket": ticket,
            "gate_url": gate_url,
            "login_url": gate_url,
            "port": st.port
        })),
    )
        .into_response()
}

async fn handle_oauth_callback(
    State(st): State<AppState>,
    Query(q): Query<HashMap<String, String>>,
) -> Response {
    let token = q
        .get("token")
        .or_else(|| q.get("flowork_token"))
        .map(|s| s.trim().to_string())
        .unwrap_or_default();
    let state_param = q.get("state").cloned().unwrap_or_default();
    let code = q.get("code").cloned().unwrap_or_default();
    let error = q.get("error").cloned().unwrap_or_default();

    if !token.is_empty() {
        match st.vault.verify_flowork_token(&token).await {
            Ok(user) => {
                let mut vault = st.vault.load_vault().await;
                vault.flowork_token = token.clone();
                vault.flowork_user = Some(user.clone());
                vault.is_logged_out = false;
                st.vault.save_vault(&vault).await;
                let username = user
                    .get("username")
                    .and_then(|v| v.as_str())
                    .unwrap_or("operator");
                println!("[Server] ✅ Flowork OS Passport authenticated for @{}", username);
                let synced_count = st
                    .vault
                    .pull_cloud_vault(Some(&token))
                    .await
                    .ok()
                    .and_then(|v| v.get("count").and_then(|c| c.as_u64()))
                    .unwrap_or(0);
                let page = format!(
                    r#"<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MrFlow — Authenticated</title>
    <style>
        body {{ margin:0; background:#070b14; color:#fff; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; }}
        .card {{ background:#0f172a; border:1px solid #10b981; border-radius:18px; padding:36px 44px; text-align:center; max-width:440px; box-shadow:0 12px 36px rgba(0,0,0,0.8), 0 0 24px rgba(16,185,129,0.3); }}
        .icon {{ font-size:44px; margin-bottom:12px; }}
        h1 {{ font-size:22px; color:#10b981; margin:0 0 8px; }}
        p {{ font-size:13.5px; color:#94a3b8; line-height:1.6; margin:0 0 20px; }}
        .btn {{ background:#10b981; color:#fff; font-weight:700; border:none; padding:10px 24px; border-radius:999px; cursor:pointer; font-size:13px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🛡️</div>
        <h1>Welcome, @{}!</h1>
        <p>Your session with <strong>auth.floworkos.com</strong> has been verified.<br>Cloud Vault successfully synchronized (<strong>{}</strong> accounts loaded).</p>
        <button class="btn" onclick="window.close()">Close Window</button>
    </div>
    <script>setTimeout(() => window.close(), 1800);</script>
</body>
</html>"#,
                    html_escape(username),
                    synced_count
                );
                return (StatusCode::OK, Html(page)).into_response();
            }
            Err(err) => {
                return (
                    StatusCode::UNAUTHORIZED,
                    Html(format!("<h2>Authentication Failed</h2><p>{}</p>", html_escape(&err))),
                )
                    .into_response();
            }
        }
    }

    if state_param.starts_with("flw_multi_") {
        if !error.is_empty() {
            return (
                StatusCode::OK,
                Html("<h2>Google Authorization Cancelled</h2><button onclick=\"window.close()\">Close</button>".to_string()),
            )
                .into_response();
        }
        let mut vault = st.vault.load_vault().await;
        let pkce = st.vault.take_pkce_session(&state_param, &mut vault).await;
        let verifier = pkce.as_ref().map(|p| p.verifier.as_str()).unwrap_or("");
        let redirect_uri = pkce
            .as_ref()
            .map(|p| p.redirect_uri.as_str())
            .filter(|s| !s.is_empty())
            .unwrap_or("http://localhost:8080/callback");

        let tokens = match st.vault.exchange_oauth_code(&code, verifier, redirect_uri).await {
            Ok(t) => t,
            Err(e) => {
                return (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    Html(format!("<h2>Token Exchange Failed</h2><p>{}</p>", html_escape(&e))),
                )
                    .into_response();
            }
        };

        let access_token = tokens.get("access_token").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let refresh_token = tokens.get("refresh_token").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let expires_in = tokens.get("expires_in").and_then(|v| v.as_i64()).unwrap_or(3600);
        let id_token = tokens.get("id_token").and_then(|v| v.as_str()).unwrap_or("");
        let mut email = tokens.get("email").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let mut name = String::new();

        if email.is_empty() && !id_token.is_empty() {
            if let Some(claims) = VaultManager::parse_jwt_claims(id_token) {
                if let Some(e) = claims.get("email").and_then(|v| v.as_str()) {
                    email = e.to_string();
                }
                if let Some(n) = claims.get("name").and_then(|v| v.as_str()) {
                    name = n.to_string();
                }
            }
        }
        if email.is_empty() {
            if let Ok(uinfo) = st.vault.fetch_google_userinfo(&access_token).await {
                if let Some(e) = uinfo.get("email").and_then(|v| v.as_str()) {
                    email = e.to_string();
                }
                if let Some(n) = uinfo.get("name").and_then(|v| v.as_str()) {
                    name = n.to_string();
                }
            }
        }
        if email.is_empty() {
            email = format!("account_{}@gmail.com", vault.accounts.len() + 1);
        }

        if let Some(existing) = vault
            .accounts
            .iter_mut()
            .find(|a| a.email.eq_ignore_ascii_case(&email))
        {
            existing.access_token = access_token;
            if !refresh_token.is_empty() {
                existing.refresh_token = refresh_token;
            }
            existing.expires_at = now_ms() + expires_in * 1000;
            existing.status = "ready".to_string();
            existing.cooldown_until = 0;
            existing.error_message.clear();
        } else {
            let now_iso = Utc::now().to_rfc3339();
            let acc_id = new_account_id();
            let disp_name = if !name.is_empty() {
                name
            } else {
                email.split('@').next().unwrap_or("account").to_string()
            };
            vault.accounts.push(Account {
                id: acc_id.clone(),
                email: email.clone(),
                name: disp_name,
                access_token,
                refresh_token,
                expires_at: now_ms() + expires_in * 1000,
                client_id: String::new(),
                status: "ready".to_string(),
                cooldown_until: 0,
                requests_count: 0,
                errors_count: 0,
                added_at: now_iso.clone(),
                last_used_at: now_iso,
                error_message: String::new(),
                extra: HashMap::new(),
            });
            if vault.active_account_id.is_empty() {
                vault.active_account_id = acc_id;
            }
        }
        st.vault.save_vault(&vault).await;

        let cloud_ok = match st.vault.push_cloud_vault(Some(&vault)).await {
            Ok(v) => v.get("success").and_then(|b| b.as_bool()).unwrap_or(false),
            Err(e) => {
                eprintln!("[Server] ☁️ Cloud auto-backup error: {}", e);
                false
            }
        };

        let page = format!(
            r#"<!DOCTYPE html><html><body style="background:#070b14;color:#fff;font-family:sans-serif;text-align:center;padding:40px;">
            <h1 style="color:#10b981;">Google Account Linked</h1>
            <p><strong>{}</strong> has been added to the accounts pool.</p>
            <p style="color:#64748b;font-size:12px;">Cloud Vault Backup: {}</p>
            <script>setTimeout(() => window.close(), 1800);</script>
        </body></html>"#,
            html_escape(&email),
            if cloud_ok { "Synchronized" } else { "Saved locally" }
        );
        return (StatusCode::OK, Html(page)).into_response();
    }

    (StatusCode::BAD_REQUEST, "Invalid callback parameters").into_response()
}

async fn handle_add_account(State(st): State<AppState>, body: Bytes) -> Response {
    let o: Value = match serde_json::from_slice(&body) {
        Ok(v) => v,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({ "success": false, "error": e.to_string() })),
            )
                .into_response();
        }
    };

    let email = o
        .get("email")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim()
        .to_string();
    let refresh_token = o
        .get("refresh_token")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim()
        .to_string();
    let access_token = o
        .get("access_token")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim()
        .to_string();
    let fallback_name = email.split('@').next().unwrap_or("account").to_string();
    let name = o
        .get("name")
        .and_then(|v| v.as_str())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or(fallback_name);

    if email.is_empty() {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({ "success": false, "error": "Email is required" })),
        )
            .into_response();
    }
    if refresh_token.is_empty() && access_token.is_empty() {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({ "success": false, "error": "Refresh token or access token is required" })),
        )
            .into_response();
    }

    let mut vault = st.vault.load_vault().await;
    if let Some(p) = vault
        .accounts
        .iter_mut()
        .find(|u| u.email.eq_ignore_ascii_case(&email))
    {
        if !refresh_token.is_empty() {
            p.refresh_token = refresh_token;
        }
        if !access_token.is_empty() {
            p.access_token = access_token;
            p.expires_at = now_ms() + 3_600_000;
        }
        p.status = "ready".to_string();
        p.cooldown_until = 0;
        p.error_message.clear();
    } else {
        let now_iso = Utc::now().to_rfc3339();
        let acc_id = new_account_id();
        let exp = if !access_token.is_empty() {
            now_ms() + 3_600_000
        } else {
            0
        };
        vault.accounts.push(Account {
            id: acc_id.clone(),
            email: email.clone(),
            name,
            access_token,
            refresh_token,
            expires_at: exp,
            client_id: String::new(),
            status: "ready".to_string(),
            cooldown_until: 0,
            requests_count: 0,
            errors_count: 0,
            added_at: now_iso.clone(),
            last_used_at: now_iso,
            error_message: String::new(),
            extra: HashMap::new(),
        });
        if vault.active_account_id.is_empty() {
            vault.active_account_id = acc_id;
        }
    }
    st.vault.save_vault(&vault).await;

    let cloud_backup = if !vault.flowork_token.is_empty() {
        match st.vault.push_cloud_vault(Some(&vault)).await {
            Ok(v) => v,
            Err(e) => json!({ "success": false, "error": e }),
        }
    } else {
        json!({ "success": false, "message": "Cloud backup skipped (no flowork token)" })
    };

    (
        StatusCode::OK,
        Json(json!({
            "success": true,
            "email": email,
            "total_accounts": vault.accounts.len(),
            "cloud_backup": cloud_backup
        })),
    )
        .into_response()
}

async fn handle_sync_cloud(State(st): State<AppState>) -> Response {
    let vault = st.vault.load_vault().await;
    if vault.flowork_token.is_empty() {
        return (
            StatusCode::UNAUTHORIZED,
            Json(json!({
                "success": false,
                "error": "Not authenticated with auth.floworkos.com. Please sign in first."
            })),
        )
            .into_response();
    }

    match st.vault.pull_cloud_vault(None).await {
        Ok(o) => {
            let count = o.get("count").and_then(|v| v.as_u64()).unwrap_or(0);
            let accounts = o.get("accounts").cloned().unwrap_or_else(|| json!([]));
            (
                StatusCode::OK,
                Json(json!({
                    "success": true,
                    "count": count,
                    "accounts": accounts,
                    "message": format!("Downloaded {} accounts from Cloud Vault", count)
                })),
            )
                .into_response()
        }
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "success": false, "error": e })),
        )
            .into_response(),
    }
}

async fn handle_set_token(State(st): State<AppState>, body: Bytes) -> Response {
    let o: Value = match serde_json::from_slice(&body) {
        Ok(v) => v,
        Err(e) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({ "success": false, "error": e.to_string() })),
            )
                .into_response();
        }
    };
    let r = o
        .get("token")
        .or_else(|| o.get("flowork_token"))
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim()
        .to_string();
    if r.is_empty() {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({ "success": false, "error": "Token missing" })),
        )
            .into_response();
    }
    let user = match st.vault.verify_flowork_token(&r).await {
        Ok(u) => u,
        Err(err) => {
            return (
                StatusCode::UNAUTHORIZED,
                Json(json!({ "success": false, "error": err })),
            )
                .into_response();
        }
    };

    let mut vault = st.vault.load_vault().await;
    vault.flowork_token = r.clone();
    vault.flowork_user = Some(user.clone());
    vault.is_logged_out = false;
    st.vault.save_vault(&vault).await;

    let count = st
        .vault
        .pull_cloud_vault(Some(&r))
        .await
        .ok()
        .and_then(|v| v.get("count").and_then(|c| c.as_u64()))
        .unwrap_or(0);

    (
        StatusCode::OK,
        Json(json!({
            "success": true,
            "user": user,
            "cloud_accounts": count
        })),
    )
        .into_response()
}

async fn handle_logout(State(st): State<AppState>) -> Response {
    let mut vault = st.vault.load_vault().await;
    vault.flowork_token.clear();
    vault.flowork_user = None;
    vault.is_logged_out = true;
    vault.accounts.clear();
    vault.active_account_id.clear();
    st.vault.save_vault(&vault).await;
    println!("[Server] 🚪 Signed out from auth.floworkos.com. Router locked.");
    (
        StatusCode::OK,
        Json(json!({ "success": true, "message": "Signed out successfully" })),
    )
        .into_response()
}

async fn handle_router_login_url(
    State(st): State<AppState>,
    Query(q): Query<HashMap<String, String>>,
) -> Response {
    match st.vault.generate_login_url(st.port).await {
        Ok(e) => {
            let login_url = e.get("loginUrl").and_then(|v| v.as_str()).unwrap_or("");
            if q.get("open").map(|v| v == "1").unwrap_or(false) {
                st.vault.open_url_in_browser(login_url);
            }
            (
                StatusCode::OK,
                Json(json!({
                    "success": true,
                    "provider": "google",
                    "loginUrl": login_url,
                    "state": e.get("state")
                })),
            )
                .into_response()
        }
        Err(err) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "success": false, "error": err })),
        )
            .into_response(),
    }
}

async fn handle_select_account(State(st): State<AppState>, body: Bytes) -> Response {
    let o: Value = match serde_json::from_slice(&body) {
        Ok(v) => v,
        Err(e) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({ "success": false, "error": e.to_string() })),
            )
                .into_response();
        }
    };
    let id = o.get("id").and_then(|v| v.as_str()).unwrap_or("");
    let mut vault = st.vault.load_vault().await;
    let Some(email) = vault
        .accounts
        .iter()
        .find(|c| c.id == id)
        .map(|c| c.email.clone())
    else {
        return (
            StatusCode::NOT_FOUND,
            Json(json!({ "success": false, "error": "Account not found" })),
        )
            .into_response();
    };
    vault.active_account_id = id.to_string();
    st.vault.save_vault(&vault).await;
    println!("[Server] Active account switched to: {}", email);
    (
        StatusCode::OK,
        Json(json!({ "success": true, "active_account_id": id, "email": email })),
    )
        .into_response()
}

async fn handle_remove_account(State(st): State<AppState>, body: Bytes) -> Response {
    let o: Value = match serde_json::from_slice(&body) {
        Ok(v) => v,
        Err(e) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({ "success": false, "error": e.to_string() })),
            )
                .into_response();
        }
    };
    let id = o.get("id").and_then(|v| v.as_str()).unwrap_or("");
    let mut vault = st.vault.load_vault().await;
    let before = vault.accounts.len();
    vault.accounts.retain(|c| c.id != id);
    if vault.accounts.len() == before {
        return (
            StatusCode::NOT_FOUND,
            Json(json!({ "success": false, "error": "Account not found" })),
        )
            .into_response();
    }
    if vault.active_account_id == id {
        vault.active_account_id = vault
            .accounts
            .first()
            .map(|a| a.id.clone())
            .unwrap_or_default();
    }
    st.vault.save_vault(&vault).await;
    let _ = st.vault.push_cloud_vault(Some(&vault)).await;
    println!(
        "[Server] Removed account {}. Remaining: {}",
        id,
        vault.accounts.len()
    );
    (
        StatusCode::OK,
        Json(json!({ "success": true, "remaining": vault.accounts.len() })),
    )
        .into_response()
}

async fn handle_set_rotation_mode(State(st): State<AppState>, body: Bytes) -> Response {
    let o: Value = match serde_json::from_slice(&body) {
        Ok(v) => v,
        Err(e) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({ "success": false, "error": e.to_string() })),
            )
                .into_response();
        }
    };
    let mode = o
        .get("mode")
        .and_then(|v| v.as_str())
        .unwrap_or("failover")
        .to_string();
    let mut vault = st.vault.load_vault().await;
    vault.rotation_mode = mode.clone();
    st.vault.save_vault(&vault).await;
    let _ = st.vault.push_cloud_vault(Some(&vault)).await;
    println!("[Server] Rotation mode set to: {}", mode);
    (
        StatusCode::OK,
        Json(json!({ "success": true, "rotation_mode": mode })),
    )
        .into_response()
}

async fn handle_test_account(State(st): State<AppState>, body: Bytes) -> Response {
    let o: Value = match serde_json::from_slice(&body) {
        Ok(v) => v,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({ "success": false, "error": e.to_string() })),
            )
                .into_response();
        }
    };
    let id = o.get("id").and_then(|v| v.as_str()).unwrap_or("");
    let mut vault = st.vault.load_vault().await;
    let Some(pos) = vault.accounts.iter().position(|s| s.id == id) else {
        return (
            StatusCode::NOT_FOUND,
            Json(json!({ "success": false, "error": "Account not found" })),
        )
            .into_response();
    };
    let mut acc = vault.accounts[pos].clone();
    let details = st.vault.refresh_account_token(&mut acc, true).await;
    vault.accounts[pos] = acc.clone();
    st.vault.save_vault(&vault).await;

    let ok = details
        .get("refreshed")
        .and_then(|v| v.as_bool())
        .unwrap_or(false)
        || details.get("error").is_none();

    (
        StatusCode::OK,
        Json(json!({
            "success": ok,
            "email": acc.email,
            "status": acc.status,
            "expires_at": acc.expires_at,
            "details": details
        })),
    )
        .into_response()
}

async fn handle_clear_cooldown(State(st): State<AppState>) -> Response {
    let cleared = st.vault.clear_all_cooldowns().await;
    (
        StatusCode::OK,
        Json(json!({ "success": true, "cleared_count": cleared })),
    )
        .into_response()
}

async fn handle_ai_fallback(State(st): State<AppState>, req: Request) -> Response {
    let method = req.method().as_str().to_string();
    let path_and_query = req
        .uri()
        .path_and_query()
        .map(|pq| pq.as_str().to_string())
        .unwrap_or_else(|| "/".to_string());
    let headers = req.headers().clone();
    let body = match axum::body::to_bytes(req.into_body(), 32 * 1024 * 1024).await {
        Ok(b) => b,
        Err(e) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({ "error": format!("Failed reading request body: {}", e) })),
            )
                .into_response();
        }
    };
    handle_ai_proxy_request(st.vault.clone(), &st.http, &method, &path_and_query, &headers, body).await
}

fn spawn_aux_oauth_listener(st: AppState, host: String, port: u16) {
    tokio::spawn(async move {
        let addr_str = format!("{}:{}", host, port);
        let Ok(addr) = addr_str.parse::<SocketAddr>() else {
            return;
        };
        let cors = CorsLayer::new()
            .allow_origin(Any)
            .allow_methods(Any)
            .allow_headers(Any);
        let app = Router::new()
            .route("/oauth-callback", get(handle_oauth_callback))
            .route("/callback", get(handle_oauth_callback))
            .route("/auth/callback", get(handle_oauth_callback))
            .fallback(|| async { (StatusCode::NOT_FOUND, "Not Found") })
            .layer(cors)
            .with_state(st);

        match TcpListener::bind(addr).await {
            Ok(listener) => {
                println!(
                    "🔗 Auxiliary Antigravity OAuth Callback: http://{}/oauth-callback",
                    addr_str
                );
                if let Err(e) = axum::serve(listener, app).await {
                    eprintln!("[Server] Auxiliary port {} stopped: {}", port, e);
                }
            }
            Err(e) => {
                eprintln!("[Server] Auxiliary port {} note: {}", port, e);
            }
        }
    });
}

#[tokio::main]
async fn main() {
    for arg in std::env::args().skip(1) {
        match arg.as_str() {
            "-h" | "--help" => {
                println!(
                    "flowork-connector {} — Flowork Sovereign Multi-Account AI Gateway (:9099)",
                    env!("CARGO_PKG_VERSION")
                );
                println!("Usage: flowork-connector [--help | --version | --check]");
                return;
            }
            "-V" | "--version" => {
                println!("flowork-connector {}", env!("CARGO_PKG_VERSION"));
                return;
            }
            "--check" => {
                let paths = ConnectorPaths::resolve();
                println!(
                    "flowork-connector {} CHECK_OK base_dir={}",
                    env!("CARGO_PKG_VERSION"),
                    paths.base_dir.display()
                );
                return;
            }
            _ => {}
        }
    }

    let paths = ConnectorPaths::resolve();
    let config = Arc::new(ConfigManager::new(paths.clone()));
    let settings = config.get_settings();

    let port: u16 = std::env::var("CONNECTOR_PORT")
        .or_else(|_| std::env::var("FLOWORK_ROUTER_PORT"))
        .or_else(|_| std::env::var("PORT"))
        .ok()
        .and_then(|s| s.trim().parse().ok())
        .unwrap_or(settings.port);

    let host: String = std::env::var("CONNECTOR_HOST")
        .or_else(|_| std::env::var("HOST"))
        .ok()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or(settings.host);

    let http = Client::builder()
        .tcp_nodelay(true)
        .connect_timeout(std::time::Duration::from_secs(10))
        .pool_idle_timeout(std::time::Duration::from_secs(15))
        .build()
        .expect("Failed building HTTP client");

    let vault = Arc::new(VaultManager::new(&paths, config.clone(), http.clone()));
    let state = AppState {
        paths,
        config,
        vault: vault.clone(),
        http,
        port,
    };

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([
            Method::GET,
            Method::POST,
            Method::PUT,
            Method::DELETE,
            Method::OPTIONS,
        ])
        .allow_headers(Any);

    let app = Router::new()
        .route("/health", get(handle_health))
        .route("/", any(|st, req: Request| async move {
            if req.method() == Method::GET {
                handle_gui_index(st).await
            } else {
                handle_ai_fallback(st, req).await
            }
        }))
        .route("/gui", get(handle_gui_index))
        .route("/gui/", get(handle_gui_index))
        .route("/index.html", get(handle_gui_index))
        .route("/gui/style.css", get(handle_gui_css))
        .route("/style.css", get(handle_gui_css))
        .route("/gui/app.js", get(handle_gui_app_js))
        .route("/app.js", get(handle_gui_app_js))
        .route("/auth/router/accounts", get(handle_router_status))
        .route("/api/router/accounts", get(handle_router_status))
        .route("/auth/router/status", get(handle_router_status))
        .route("/api/router/status", get(handle_router_status))
        .route("/auth/router/refresh-pool", get(handle_router_status))
        .route("/auth/router/provider-config", get(handle_provider_config).post(handle_provider_config))
        .route("/api/router/provider-config", get(handle_provider_config).post(handle_provider_config))
        .route("/auth/router/test-provider", post(handle_test_provider))
        .route("/auth/test/ollama", get(handle_test_ollama_get))
        .route("/auth/login-url", get(handle_login_ticket).post(handle_login_ticket))
        .route("/auth/ticket", get(handle_login_ticket).post(handle_login_ticket))
        .route("/api/auth/ticket", get(handle_login_ticket).post(handle_login_ticket))
        .route("/auth/callback", get(handle_oauth_callback))
        .route("/callback", get(handle_oauth_callback))
        .route("/auth/flowork-callback", get(handle_oauth_callback))
        .route("/auth/router/add-account", post(handle_add_account))
        .route("/auth/router/sync-cloud", get(handle_sync_cloud).post(handle_sync_cloud))
        .route("/api/router/sync-cloud", get(handle_sync_cloud).post(handle_sync_cloud))
        .route("/auth/set-token", post(handle_set_token))
        .route("/auth/logout", post(handle_logout))
        .route("/auth/router/login-url", get(handle_router_login_url))
        .route("/auth/router/select-account", post(handle_select_account))
        .route("/auth/router/remove-account", post(handle_remove_account))
        .route("/auth/router/set-rotation-mode", post(handle_set_rotation_mode))
        .route("/auth/router/test-account", post(handle_test_account))
        .route("/auth/router/clear-cooldown", post(handle_clear_cooldown))
        .fallback(handle_ai_fallback)
        .layer(cors)
        .with_state(state.clone());

    let bind_addr: SocketAddr = format!("{}:{}", host, port)
        .parse()
        .expect("Invalid bind address");
    let listener = TcpListener::bind(bind_addr)
        .await
        .expect("Failed binding connector listener");

    println!("=======================================================");
    println!("🚀 MrFlow Sovereign Connector & Account Rotator Online (Pure Rust)");
    println!("📡 Server Address: http://{}:{}", host, port);
    println!("🎨 Web GUI:        http://{}:{}/gui", host, port);
    println!("=======================================================");

    vault.spawn_background_keeper();

    if std::env::var("CONNECTOR_NO_AUX").ok().as_deref() != Some("1") {
        spawn_aux_oauth_listener(state.clone(), host.clone(), 51121);
        spawn_aux_oauth_listener(state, host, 8080);
    }

    if let Err(e) = axum::serve(listener, app).await {
        eprintln!("[Server] Fatal serve error: {}", e);
        std::process::exit(1);
    }
}
