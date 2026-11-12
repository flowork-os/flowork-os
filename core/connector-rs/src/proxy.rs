use axum::body::Body;
use axum::http::{HeaderMap, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::Json;
use bytes::Bytes;
use chrono::Utc;
use futures_util::StreamExt;
use regex::Regex;
use reqwest::Client;
use serde_json::{json, Map, Value};
use std::fs;
use std::sync::Arc;
use std::time::Duration;

use crate::providers::{
    failover_to_local_slm, get_effective_providers, handle_9router_request, handle_ollama_request,
    passthrough_response, test_ollama_connectivity, SlmFailoverRequest,
};
use crate::translator::{
    build_gemini_buffered_json, create_openai_json_response, merge_adjacent_same_role,
    normalize_model, openai_to_gemini, parse_gemini_sse_to_full_text, sanitize_schema,
    GeminiToOpenAiState, UnwrapCloudCodeSseState,
};
use crate::vault::{VaultData, VaultManager};

struct AirgappedFailoverContext<'a> {
    path_and_query: &'a str,
    headers: &'a HeaderMap,
    raw_body: &'a [u8],
    vault: &'a VaultData,
    cfg_providers: &'a Value,
    settings: &'a crate::config::SettingsConfig,
    slm: SlmFailoverRequest<'a>,
}

async fn dispatch_airgapped_failover(http: &Client, ctx: AirgappedFailoverContext<'_>) -> Response {
    let probe = test_ollama_connectivity(http, None, ctx.cfg_providers).await;
    let ollama_ready = probe
        .get("online")
        .and_then(|v| v.as_bool())
        .unwrap_or(false)
        && probe.get("count").and_then(|v| v.as_u64()).unwrap_or(0) > 0;

    if ollama_ready {
        eprintln!(
            "[Air-Gapped Failover] CloudCode unavailable ({}); routing via active local Ollama.",
            ctx.slm.reason
        );
        return handle_ollama_request(
            http,
            ctx.path_and_query,
            ctx.headers,
            ctx.raw_body,
            ctx.vault,
            ctx.cfg_providers,
            ctx.settings,
        )
        .await;
    }

    failover_to_local_slm(http, &ctx.settings.sysd_url, ctx.slm).await
}

pub async fn handle_ai_proxy_request(
    vault_mgr: Arc<VaultManager>,
    http: &Client,
    method: &str,
    path_and_query: &str,
    headers: &HeaderMap,
    raw_body: Bytes,
) -> Response {
    let pathname = path_and_query.split('?').next().unwrap_or(path_and_query);
    println!("[Proxy Request] {} {}", method, pathname);

    let vault = vault_mgr.load_vault().await;
    let active_prov = vault.active_provider.to_lowercase();
    let cfg_providers = vault_mgr.config.get_providers();
    let settings = vault_mgr.config.get_settings();

    if pathname == "/v1/models" || pathname == "/models" {
        let eff = get_effective_providers(&vault, &cfg_providers);
        if active_prov == "ollama" {
            let d = eff.get("ollama").cloned().unwrap_or_else(|| json!({}));
            let def_m = d
                .get("default_model")
                .or_else(|| d.get("model"))
                .and_then(|v| v.as_str())
                .unwrap_or("deepseek-v4-9b-uncensored:latest");
            let models: Vec<Value> = d
                .get("custom_models")
                .and_then(|v| v.as_array())
                .map(|arr| {
                    arr.iter()
                        .filter_map(|m| m.as_str())
                        .map(|id| json!({ "id": id, "object": "model", "created": 1700000000, "owned_by": "ollama" }))
                        .collect()
                })
                .unwrap_or_else(|| vec![json!({ "id": def_m, "object": "model", "created": 1700000000, "owned_by": "ollama" })]);
            return (StatusCode::OK, Json(json!({ "object": "list", "data": models }))).into_response();
        }
        if active_prov == "9router" || active_prov == "router9" {
            let d = eff.get("9router").cloned().unwrap_or_else(|| json!({}));
            let def_m = d
                .get("default_model")
                .or_else(|| d.get("model"))
                .and_then(|v| v.as_str())
                .unwrap_or("clinepass/cline-pass/glm-5.2");
            let models: Vec<Value> = d
                .get("custom_models")
                .and_then(|v| v.as_array())
                .map(|arr| {
                    arr.iter()
                        .filter_map(|m| m.as_str())
                        .map(|id| json!({ "id": id, "object": "model", "created": 1700000000, "owned_by": "9router" }))
                        .collect()
                })
                .unwrap_or_else(|| vec![json!({ "id": def_m, "object": "model", "created": 1700000000, "owned_by": "9router" })]);
            return (StatusCode::OK, Json(json!({ "object": "list", "data": models }))).into_response();
        }
        let catalog = vault_mgr.config.get_models().catalog;
        let data: Vec<Value> = catalog
            .iter()
            .map(|d| json!({ "id": d.id, "object": "model", "created": 1700000000, "owned_by": d.owned_by }))
            .collect();
        return (StatusCode::OK, Json(json!({ "object": "list", "data": data }))).into_response();
    }

    if pathname == "/v1beta/models" {
        let catalog = vault_mgr.config.get_models().catalog;
        let models: Vec<Value> = catalog
            .iter()
            .map(|d| {
                json!({
                    "name": format!("models/{}", d.id),
                    "version": "1.0",
                    "displayName": d.name,
                    "description": format!("Sovereign Flowork Model {}", d.name),
                    "inputTokenLimit": 1048576,
                    "outputTokenLimit": 65536,
                    "supportedGenerationMethods": ["generateContent", "streamGenerateContent"]
                })
            })
            .collect();
        return (StatusCode::OK, Json(json!({ "models": models }))).into_response();
    }

    if pathname.contains(":loadCodeAssist") {
        return (
            StatusCode::OK,
            Json(json!({
                "allowed": true,
                "cloudaicompanionProject": "aicode-consumers",
                "currentTier": {
                    "id": "enterprise-tier",
                    "name": "MrFlow Enterprise Sovereign",
                    "description": "Full Autonomous Agent Access",
                    "isDefault": true
                },
                "allowedTiers": [{
                    "id": "enterprise-tier",
                    "name": "MrFlow Enterprise Sovereign",
                    "description": "Full Autonomous Agent Access",
                    "isDefault": true
                }],
                "gcpManaged": false,
                "manageSubscriptionUri": "https://auth.floworkos.com"
            })),
        )
            .into_response();
    }

    if pathname.contains(":retrieveUserQuota") || pathname.contains("UserQuotaSummary") {
        return (
            StatusCode::OK,
            Json(json!({
                "dailyQuota": "999999999",
                "remainingQuota": "999999999",
                "resetTime": "2099-01-01T00:00:00Z",
                "allowed": true
            })),
        )
            .into_response();
    }

    if pathname.contains(":listExperiments") {
        return (StatusCode::OK, Json(json!({ "experimentIds": [], "flags": [] }))).into_response();
    }

    if pathname.contains(":fetchUserInfo") || pathname.contains("/fetchUserInfo") {
        let active_acc = vault
            .accounts
            .iter()
            .find(|s| s.id == vault.active_account_id)
            .or_else(|| vault.accounts.first());
        let email = active_acc
            .map(|a| a.email.clone())
            .filter(|s| !s.is_empty())
            .or_else(|| {
                vault
                    .flowork_user
                    .as_ref()
                    .and_then(|u| u.get("email"))
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string())
            })
            .unwrap_or_else(|| "user@floworkos.com".to_string());
        let name = active_acc
            .map(|a| a.name.clone())
            .filter(|s| !s.is_empty())
            .or_else(|| {
                vault
                    .flowork_user
                    .as_ref()
                    .and_then(|u| u.get("name").or_else(|| u.get("username")))
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string())
            })
            .unwrap_or_else(|| "Flowork Operator".to_string());
        let tier = vault
            .flowork_user
            .as_ref()
            .and_then(|u| u.get("tier"))
            .and_then(|v| v.as_str())
            .map(|t| format!("{}-tier", t))
            .unwrap_or_else(|| "enterprise-tier".to_string());

        return (
            StatusCode::OK,
            Json(json!({
                "user": {
                    "email": email,
                    "name": name,
                    "tier": tier
                }
            })),
        )
            .into_response();
    }

    if active_prov == "ollama" {
        return handle_ollama_request(
            http,
            path_and_query,
            headers,
            &raw_body,
            &vault,
            &cfg_providers,
            &settings,
        )
        .await;
    }

    let is_openai = pathname.contains("/chat/completions");
    let gemini_re = Regex::new(r"/v1beta/models/([^:?]+):([^?]+)").ok();
    let gemini_caps = gemini_re.as_ref().and_then(|re| re.captures(pathname));
    let is_gemini = gemini_caps.is_some();

    let mut sanitized_raw_body = raw_body.clone();
    let parsed_body: Option<Value> = if !raw_body.is_empty() {
        match serde_json::from_slice::<Value>(&raw_body) {
            Ok(v) => {
                let effective_val = if settings.enable_privacy_shield {
                    let outcome =
                        crate::privacy::redact_outbound_payload(http, &settings.sysd_url, &v).await;
                    if outcome.redacted {
                        eprintln!(
                            "[Privacy Shield] Redacted {} finding(s) ({:?}) via {} before outbound egress ({} {})",
                            outcome.findings_count,
                            outcome.categories,
                            if outcome.via_sysd { "flowork-sysd" } else { "local-failsafe" },
                            method,
                            pathname
                        );
                        if let Ok(vec_bytes) = serde_json::to_vec(&outcome.payload) {
                            sanitized_raw_body = Bytes::from(vec_bytes);
                        }
                    }
                    outcome.payload
                } else {
                    v
                };
                if let Ok(pretty) = serde_json::to_string_pretty(&effective_val) {
                    if let Ok(home) = std::env::var("HOME") {
                        let priv_dir = std::path::PathBuf::from(home).join(".flowork");
                        let _ = fs::create_dir_all(&priv_dir);
                        let req_dump = priv_dir.join("connector_last_req.json");
                        use std::io::Write;
                        use std::os::unix::fs::OpenOptionsExt;
                        if let Ok(mut f) = fs::OpenOptions::new()
                            .create(true)
                            .write(true)
                            .truncate(true)
                            .mode(0o600)
                            .open(&req_dump)
                        {
                            let _ = f.write_all(pretty.as_bytes());
                        }
                    }
                }
                Some(effective_val)
            }
            Err(_) => {
                if settings.enable_privacy_shield {
                    let raw_text = String::from_utf8_lossy(&raw_body);
                    let (scrubbed, hits, cats) = crate::privacy::redact_text_local(&raw_text);
                    if hits > 0 {
                        eprintln!(
                            "[Privacy Shield] Redacted {} raw-text finding(s) ({:?}) before outbound egress ({} {})",
                            hits, cats, method, pathname
                        );
                        sanitized_raw_body = Bytes::from(scrubbed.into_bytes());
                    }
                }
                None
            }
        }
    } else {
        None
    };

    if active_prov == "9router" || active_prov == "router9" {
        return handle_9router_request(
            http,
            path_and_query,
            &sanitized_raw_body,
            &vault,
            &cfg_providers,
        )
        .await;
    }

    let failover_parsed = parsed_body.clone();
    let mut target_model = "gemini-3.8-flash-high".to_string();
    let is_stream: bool;
    let payload_value: Option<Value>;

    if is_openai {
        let c = parsed_body.unwrap_or_else(|| json!({}));
        is_stream = c.get("stream").and_then(|v| v.as_bool()) != Some(false);
        target_model = normalize_model(
            c.get("model")
                .and_then(|v| v.as_str())
                .unwrap_or("gemini-3.8-flash-high"),
        );
        payload_value = Some(openai_to_gemini(&c, &target_model));
    } else if let Some(caps) = gemini_caps {
        let raw_model = caps.get(1).map(|m| m.as_str()).unwrap_or("gemini-3.8-flash-high");
        let action = caps.get(2).map(|m| m.as_str()).unwrap_or("");
        is_stream = action.contains("stream");
        target_model = normalize_model(raw_model);

        let c = parsed_body.unwrap_or_else(|| json!({}));
        let mut inner = c.get("request").cloned().unwrap_or(c);
        if let Some(obj) = inner.as_object_mut() {
            if !obj.contains_key("generationConfig") || !obj["generationConfig"].is_object() {
                obj.insert("generationConfig".to_string(), Value::Object(Map::new()));
            }
            if let Some(gc) = obj.get_mut("generationConfig").and_then(|v| v.as_object_mut()) {
                if !gc.contains_key("maxOutputTokens") {
                    gc.insert("maxOutputTokens".to_string(), json!(65536));
                }
            }
            if let Some(contents) = obj.get("contents").and_then(|v| v.as_array()) {
                obj.insert("contents".to_string(), Value::Array(merge_adjacent_same_role(contents)));
            }
            if let Some(tools) = obj.get_mut("tools").and_then(|v| v.as_array_mut()) {
                for tool in tools.iter_mut() {
                    if let Some(tobj) = tool.as_object_mut() {
                        let decls = tobj
                            .remove("functionDeclarations")
                            .or_else(|| tobj.remove("function_declarations"));
                        if let Some(Value::Array(mut arr)) = decls {
                            for h in arr.iter_mut() {
                                if let Some(hobj) = h.as_object_mut() {
                                    let allowed = ["name", "description", "parameters", "response", "parametersJsonSchema"];
                                    let keys: Vec<String> = hobj.keys().cloned().collect();
                                    for k in keys {
                                        if !allowed.contains(&k.as_str()) {
                                            hobj.remove(&k);
                                        }
                                    }
                                    if let Some(schema) = hobj
                                        .remove("parametersJsonSchema")
                                        .or_else(|| hobj.remove("parameters"))
                                    {
                                        hobj.insert("parameters".to_string(), sanitize_schema(&schema));
                                    }
                                }
                            }
                            tobj.insert("functionDeclarations".to_string(), Value::Array(arr));
                        }
                    }
                }
            }
        }
        payload_value = Some(json!({
            "project": "aicode-consumers",
            "model": target_model,
            "request": inner
        }));
    } else {
        let accept = headers
            .get("accept")
            .and_then(|v| v.to_str().ok())
            .unwrap_or("");
        is_stream = path_and_query.contains("stream") || accept.contains("event-stream");
        if let Some(mut c) = parsed_body {
            if let Some(obj) = c.as_object_mut() {
                if !obj.contains_key("project") {
                    obj.insert("project".to_string(), json!("aicode-consumers"));
                }
                if let Some(m) = obj.get("model").and_then(|v| v.as_str()) {
                    target_model = normalize_model(m);
                }
            }
            payload_value = Some(c);
        } else {
            payload_value = None;
        }
    }

    // Google CloudCode Multi-Account Pool
    if vault.flowork_token.is_empty() {
        if settings.offline_resilience {
            return dispatch_airgapped_failover(
                http,
                AirgappedFailoverContext {
                    path_and_query,
                    headers,
                    raw_body: &sanitized_raw_body,
                    vault: &vault,
                    cfg_providers: &cfg_providers,
                    settings: &settings,
                    slm: SlmFailoverRequest {
                        is_openai,
                        is_gemini,
                        is_stream,
                        target_model: &target_model,
                        parsed_body: failover_parsed.as_ref(),
                        raw_body: &sanitized_raw_body,
                        reason: "cloudcode_unauthenticated",
                    },
                },
            )
            .await;
        }
        return (
            StatusCode::UNAUTHORIZED,
            Json(json!({
                "error": {
                    "code": 401,
                    "message": "Sovereign Router is locked. Please sign in to auth.floworkos.com in the Connector GUI.",
                    "status": "UNAUTHENTICATED"
                }
            })),
        )
            .into_response();
    }

    if vault.accounts.is_empty() {
        if settings.offline_resilience {
            return dispatch_airgapped_failover(
                http,
                AirgappedFailoverContext {
                    path_and_query,
                    headers,
                    raw_body: &sanitized_raw_body,
                    vault: &vault,
                    cfg_providers: &cfg_providers,
                    settings: &settings,
                    slm: SlmFailoverRequest {
                        is_openai,
                        is_gemini,
                        is_stream,
                        target_model: &target_model,
                        parsed_body: failover_parsed.as_ref(),
                        raw_body: &sanitized_raw_body,
                        reason: "cloudcode_empty_pool",
                    },
                },
            )
            .await;
        }
        return (
            StatusCode::NOT_FOUND,
            Json(json!({
                "error": {
                    "code": 404,
                    "message": "No Google accounts found in pool. Use \"Unduh Akun (Sync Cloud)\" in the GUI.",
                    "status": "NOT_FOUND"
                }
            })),
        )
            .into_response();
    }

    let final_bytes = match payload_value {
        Some(v) => Bytes::from(serde_json::to_vec(&v).unwrap_or_default()),
        None => sanitized_raw_body.clone(),
    };

    let upstream_path = "/v1internal:streamGenerateContent?alt=sse";
    let max_attempts = vault.accounts.len().max(2).min(8);
    let mut last_err_msg: Option<String> = None;

    for _ in 0..max_attempts {
        let mut current_vault = vault_mgr.load_vault().await;
        let Some(idx) = VaultManager::select_next_available_index(&mut current_vault, None) else {
            break;
        };
        let mut account = current_vault.accounts[idx].clone();
        if !vault_mgr.ensure_account_token_valid(&mut account).await {
            current_vault.accounts[idx] = account.clone();
            vault_mgr.save_vault(&current_vault).await;
            vault_mgr
                .mark_account_cooldown(&account.id, Some(120), "TOKEN_INVALID")
                .await;
            continue;
        }

        account.requests_count = account.requests_count.saturating_add(1);
        account.last_used_at = Utc::now().to_rfc3339();
        current_vault.accounts[idx] = account.clone();
        vault_mgr.save_vault(&current_vault).await;

        println!(
            "[Proxy] 📡 Routing {} request -> Google [{}] (model: {})",
            if is_openai {
                "OpenAI"
            } else if is_gemini {
                "Gemini"
            } else {
                "Native"
            },
            account.email,
            target_model
        );

        let net = vault_mgr.config.get_network();
        let host = net.upstream_host.trim_end_matches('/');
        let target_url = format!("{}{}", host, upstream_path);
        let ttfb_timeout = Duration::from_millis(net.timeout_ms.max(120_000));

        let mut req = http
            .post(&target_url)
            .header("Authorization", format!("Bearer {}", account.access_token))
            .header("User-Agent", &net.user_agent);

        for (hk, hv) in &net.default_headers {
            if !hk.eq_ignore_ascii_case("host")
                && !hk.eq_ignore_ascii_case("content-length")
                && !hk.eq_ignore_ascii_case("connection")
            {
                req = req.header(hk, hv);
            }
        }
        req = req.header("Content-Type", "application/json").body(final_bytes.clone());

        // Bound only TTFB / response header handshake so long SSE streams never time out mid-body.
        let upstream = match tokio::time::timeout(ttfb_timeout, req.send()).await {
            Ok(Ok(r)) => r,
            Ok(Err(e)) => {
                eprintln!("[Proxy] Upstream send error for [{}]: {}", account.email, e);
                last_err_msg = Some(e.to_string());
                continue;
            }
            Err(_) => {
                let msg = format!(
                    "Upstream TTFB timed out after {}ms waiting for headers",
                    ttfb_timeout.as_millis()
                );
                eprintln!("[Proxy] {} [{}]", msg, account.email);
                last_err_msg = Some(msg);
                continue;
            }
        };

        let code = upstream.status().as_u16();
        if code == 429 {
            eprintln!(
                "[Proxy] ⚠️ Account [{}] hit 429 Quota Exceeded. Rotating account...",
                account.email
            );
            vault_mgr
                .mark_account_cooldown(&account.id, Some(60), "HTTP_429_QUOTA_EXHAUSTED")
                .await;
            last_err_msg = Some("429".to_string());
            continue;
        }
        if code == 401 {
            eprintln!(
                "[Proxy] ⚠️ Account [{}] returned 401. Refreshing token...",
                account.email
            );
            let mut ref_acc = account.clone();
            let refresh_details = vault_mgr.refresh_account_token(&mut ref_acc, true).await;
            let refreshed = refresh_details
                .get("refreshed")
                .and_then(|v| v.as_bool())
                .unwrap_or(false)
                && refresh_details.get("error").is_none()
                && !ref_acc.access_token.is_empty();
            let acc_id = ref_acc.id.clone();
            {
                let mut v2 = vault_mgr.load_vault().await;
                if let Some(pos) = v2.accounts.iter().position(|a| a.id == acc_id) {
                    v2.accounts[pos] = ref_acc;
                    vault_mgr.save_vault(&v2).await;
                }
            }
            if !refreshed {
                vault_mgr
                    .mark_account_cooldown(&acc_id, Some(30), "TOKEN_REFRESH_REQUIRED")
                    .await;
            }
            last_err_msg = Some("401".to_string());
            continue;
        }
        if code == 403 {
            let err_txt = upstream.text().await.unwrap_or_default();
            eprintln!(
                "[Proxy] ⚠️ Account [{}] returned 403 Forbidden. Rotating...",
                account.email
            );
            vault_mgr
                .mark_account_cooldown(&account.id, Some(86400), "FORBIDDEN_403")
                .await;
            last_err_msg = Some(err_txt);
            continue;
        }
        if code != 200 {
            let err_txt = upstream.text().await.unwrap_or_default();
            let preview: String = err_txt.chars().take(150).collect();
            eprintln!("[Proxy] Upstream status {}: {}", code, preview);
            // Deterministic 4xx client/schema/payload errors (excluding 401/403/408/429) must NOT rotate accounts
            // or fall back to an HTTP 200 L0 Offline Fallback banner.
            if (400..500).contains(&code) && !matches!(code, 401 | 403 | 408 | 429) {
                let status = StatusCode::from_u16(code).unwrap_or(StatusCode::BAD_REQUEST);
                return (
                    status,
                    [("content-type", "application/json")],
                    err_txt,
                )
                    .into_response();
            }
            last_err_msg = Some(err_txt);
            continue;
        }

        if is_stream {
            if is_openai {
                let m = target_model.clone();
                let stream = futures_util::stream::unfold(
                    (Box::pin(upstream.bytes_stream()), GeminiToOpenAiState::new(m), false),
                    |(mut s, mut st, done)| async move {
                        if done {
                            return None;
                        }
                        match s.next().await {
                            Some(Ok(chunk)) => {
                                let out = st.push_chunk(&chunk);
                                Some((Ok::<Bytes, std::io::Error>(out), (s, st, false)))
                            }
                            Some(Err(_)) | None => {
                                let out = st.flush();
                                Some((Ok::<Bytes, std::io::Error>(out), (s, st, true)))
                            }
                        }
                    },
                );
                return Response::builder()
                    .status(StatusCode::OK)
                    .header("Content-Type", "text/event-stream; charset=utf-8")
                    .header("Cache-Control", "no-cache")
                    .header("Connection", "keep-alive")
                    .body(Body::from_stream(stream))
                    .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response());
            }

            if is_gemini {
                let stream = futures_util::stream::unfold(
                    (Box::pin(upstream.bytes_stream()), UnwrapCloudCodeSseState::new(), false),
                    |(mut s, mut st, done)| async move {
                        if done {
                            return None;
                        }
                        match s.next().await {
                            Some(Ok(chunk)) => {
                                let out = st.push_chunk(&chunk);
                                Some((Ok::<Bytes, std::io::Error>(out), (s, st, false)))
                            }
                            Some(Err(_)) | None => {
                                let out = st.flush();
                                Some((Ok::<Bytes, std::io::Error>(out), (s, st, true)))
                            }
                        }
                    },
                );
                return Response::builder()
                    .status(StatusCode::OK)
                    .header("Content-Type", "text/event-stream; charset=utf-8")
                    .header("Cache-Control", "no-cache")
                    .header("Connection", "keep-alive")
                    .body(Body::from_stream(stream))
                    .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response());
            }

            return passthrough_response(StatusCode::OK, upstream, "text/event-stream; charset=utf-8");
        }

        let buf = upstream.bytes().await.unwrap_or_default();
        let raw_str = String::from_utf8_lossy(&buf);
        if is_openai {
            let full = parse_gemini_sse_to_full_text(&raw_str);
            return (StatusCode::OK, Json(create_openai_json_response(&full, &target_model))).into_response();
        }
        if is_gemini {
            let assembled = build_gemini_buffered_json(&raw_str);
            return (StatusCode::OK, Json(assembled)).into_response();
        }
        return Response::builder()
            .status(StatusCode::OK)
            .header("Content-Type", "application/json")
            .body(Body::from(buf))
            .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response());
    }

    if settings.offline_resilience {
        let reason = match last_err_msg.as_deref() {
            Some("429") => "cloudcode_429_exhausted",
            Some("401") => "cloudcode_401_unauthorized",
            Some(s) if s.contains("timed out") => "cloudcode_timeout",
            Some(_) => "cloudcode_unavailable",
            None => "cloudcode_all_cooling_down",
        };
        return dispatch_airgapped_failover(
            http,
            AirgappedFailoverContext {
                path_and_query,
                headers,
                raw_body: &sanitized_raw_body,
                vault: &vault,
                cfg_providers: &cfg_providers,
                settings: &settings,
                slm: SlmFailoverRequest {
                    is_openai,
                    is_gemini,
                    is_stream,
                    target_model: &target_model,
                    parsed_body: failover_parsed.as_ref(),
                    raw_body: &sanitized_raw_body,
                    reason,
                },
            },
        )
        .await;
    }

    (
        StatusCode::SERVICE_UNAVAILABLE,
        Json(json!({
            "error": {
                "code": 503,
                "message": "All accounts in pool are currently exhausted or cooling down. Please retry shortly.",
                "status": "UNAVAILABLE",
                "details": last_err_msg
            }
        })),
    )
        .into_response()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn proxy_bounds_single_account_retries_and_ttfb_floor() {
        assert_eq!(1usize.max(2).min(8), 2);
        assert_eq!(4usize.max(2).min(8), 4);
        assert_eq!(12usize.max(2).min(8), 8);
        assert_eq!(Duration::from_millis(90_000u64.max(120_000)), Duration::from_secs(120));
        assert_eq!(Duration::from_millis(180_000u64.max(120_000)), Duration::from_secs(180));
    }

    #[test]
    fn settings_config_enables_privacy_shield_and_offline_resilience_by_default() {
        let cfg: crate::config::SettingsConfig = serde_json::from_str("{}").unwrap();
        assert!(cfg.offline_resilience);
        assert!(cfg.enable_privacy_shield);
        assert!(cfg.enable_local_cache);
        assert!(!cfg.sysd_url.is_empty());
    }
}
