use axum::body::Body;
use axum::http::{HeaderMap, HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::Json;
use bytes::Bytes;
use futures_util::StreamExt;
use regex::Regex;
use reqwest::Client;
use serde_json::{json, Value};
use std::time::Duration;
use uuid::Uuid;

use crate::config::{default_providers_value, SettingsConfig};
use crate::translator::{create_openai_json_response, gemini_to_openai, OpenAiToGeminiState};
use crate::vault::{now_ms, VaultData};

pub fn get_effective_providers(vault: &VaultData, cfg_providers: &Value) -> Value {
    if let Some(ref p) = vault.providers {
        if p.is_object() {
            return p.clone();
        }
    }
    if cfg_providers.is_object() {
        return cfg_providers.clone();
    }
    default_providers_value()
}

pub async fn test_ollama_connectivity(http: &Client, host_override: Option<&str>, cfg_providers: &Value) -> Value {
    let default_host = cfg_providers
        .pointer("/ollama/host")
        .or_else(|| cfg_providers.pointer("/ollama/endpoint"))
        .and_then(|v| v.as_str())
        .unwrap_or("http://127.0.0.1:11434");
    let base = host_override
        .filter(|s| !s.trim().is_empty())
        .unwrap_or(default_host)
        .trim_end_matches('/');
    let url = format!("{}/api/tags", base);

    match http
        .get(&url)
        .timeout(Duration::from_millis(2500))
        .send()
        .await
    {
        Ok(res) => match res.json::<Value>().await {
            Ok(data) => {
                let models: Vec<String> = data
                    .get("models")
                    .and_then(|v| v.as_array())
                    .map(|arr| {
                        arr.iter()
                            .filter_map(|m| m.get("name").and_then(|n| n.as_str()).map(|s| s.to_string()))
                            .collect()
                    })
                    .unwrap_or_default();
                let count = models.len();
                json!({ "success": true, "online": true, "models": models, "count": count })
            }
            Err(_) => json!({ "success": true, "online": true, "models": [], "count": 0 }),
        },
        Err(e) => {
            let msg = if e.is_timeout() {
                "Connection timed out".to_string()
            } else {
                e.to_string()
            };
            json!({ "success": false, "online": false, "error": msg })
        }
    }
}

pub async fn test_9router_connectivity(
    http: &Client,
    host_override: Option<&str>,
    key_override: Option<&str>,
    cfg_providers: &Value,
) -> Value {
    let default_host = cfg_providers
        .pointer("/9router/host")
        .or_else(|| cfg_providers.pointer("/9router/endpoint"))
        .and_then(|v| v.as_str())
        .unwrap_or("http://127.0.0.1:20128");
    let default_key = cfg_providers
        .pointer("/9router/api_key")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    let base = host_override
        .filter(|s| !s.trim().is_empty())
        .unwrap_or(default_host)
        .trim_end_matches('/');
    let key = key_override.unwrap_or(default_key);
    let url = if base.ends_with("/v1") {
        format!("{}/models", base)
    } else {
        format!("{}/v1/models", base)
    };

    let mut req = http.get(&url).timeout(Duration::from_secs(3));
    if !key.is_empty() {
        req = req.header("Authorization", format!("Bearer {}", key));
    }

    match req.send().await {
        Ok(res) => match res.json::<Value>().await {
            Ok(data) => {
                let arr_opt = data.get("data").and_then(|v| v.as_array()).or_else(|| data.as_array());
                let models: Vec<String> = arr_opt
                    .map(|arr| {
                        arr.iter()
                            .filter_map(|m| {
                                m.get("id")
                                    .or_else(|| m.get("name"))
                                    .and_then(|n| n.as_str())
                                    .map(|s| s.to_string())
                            })
                            .collect()
                    })
                    .unwrap_or_default();
                let count = models.len();
                json!({ "success": true, "online": true, "models": models, "count": count })
            }
            Err(_) => json!({ "success": true, "online": true, "models": [], "count": 0 }),
        },
        Err(e) => {
            let msg = if e.is_timeout() {
                "Connection timed out".to_string()
            } else {
                e.to_string()
            };
            json!({ "success": false, "online": false, "error": msg })
        }
    }
}

pub fn stream_openai_to_gemini_response(upstream: reqwest::Response) -> Response {
    let stream = futures_util::stream::unfold(
        (Box::pin(upstream.bytes_stream()), OpenAiToGeminiState::new(), false),
        |(mut s, mut state, flushed)| async move {
            if flushed {
                return None;
            }
            match s.next().await {
                Some(Ok(chunk)) => {
                    let out = state.push_chunk(&chunk);
                    Some((Ok::<Bytes, std::io::Error>(out), (s, state, false)))
                }
                Some(Err(_)) | None => {
                    let out = state.flush();
                    Some((Ok::<Bytes, std::io::Error>(out), (s, state, true)))
                }
            }
        },
    );

    Response::builder()
        .status(StatusCode::OK)
        .header("Content-Type", "text/event-stream; charset=utf-8")
        .header("Cache-Control", "no-cache")
        .header("Connection", "keep-alive")
        .body(Body::from_stream(stream))
        .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response())
}

pub fn passthrough_response(status: StatusCode, upstream: reqwest::Response, default_ct: &str) -> Response {
    let ct = upstream
        .headers()
        .get("content-type")
        .and_then(|v| v.to_str().ok())
        .unwrap_or(default_ct)
        .to_string();
    let stream = upstream
        .bytes_stream()
        .map(|res| res.map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e)));
    Response::builder()
        .status(status)
        .header("Content-Type", ct)
        .body(Body::from_stream(stream))
        .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response())
}

pub async fn handle_ollama_request(
    http: &Client,
    path_and_query: &str,
    _headers: &HeaderMap,
    raw_body: &[u8],
    vault: &VaultData,
    cfg_providers: &Value,
    settings: &SettingsConfig,
) -> Response {
    let is_stream = path_and_query.contains("stream") || path_and_query.contains("alt=sse");
    let is_chat = path_and_query.contains("/chat/completions");

    if !is_stream
        && !is_chat
        && (path_and_query.contains("generateContent") || path_and_query.contains("GenerateContent"))
    {
        let cls = json!({
            "complexity_reasoning": "Direct query",
            "complexity_score": 1,
            "category": 0,
            "status": "ok"
        });
        let g_resp = json!({
            "response": {
                "candidates": [{
                    "content": { "role": "model", "parts": [{ "text": cls.to_string() }] },
                    "finishReason": "STOP"
                }],
                "usageMetadata": { "promptTokenCount": 10, "candidatesTokenCount": 10, "totalTokenCount": 20 }
            },
            "candidates": [{
                "content": { "role": "model", "parts": [{ "text": cls.to_string() }] },
                "finishReason": "STOP"
            }],
            "usageMetadata": { "promptTokenCount": 10, "candidatesTokenCount": 10, "totalTokenCount": 20 }
        });
        return (StatusCode::OK, Json(g_resp)).into_response();
    }

    let providers = get_effective_providers(vault, cfg_providers);
    let ollama_cfg = providers.get("ollama").cloned().unwrap_or_else(|| json!({}));
    let host = ollama_cfg
        .get("host")
        .or_else(|| ollama_cfg.get("endpoint"))
        .and_then(|v| v.as_str())
        .unwrap_or("http://127.0.0.1:11434")
        .trim_end_matches('/')
        .to_string();
    let default_model = ollama_cfg
        .get("default_model")
        .or_else(|| ollama_cfg.get("model"))
        .and_then(|v| v.as_str())
        .unwrap_or("deepseek-v4-9b-uncensored:latest")
        .to_string();

    let parsed_req: Value = serde_json::from_slice(raw_body).unwrap_or_else(|_| json!({}));
    let effective_stream = if is_chat {
        parsed_req
            .get("stream")
            .and_then(|v| v.as_bool())
            .unwrap_or(false)
    } else {
        is_stream
    };
    let is_gemini = path_and_query.contains("/v1beta/models/");

    let is_remote_ollama = reqwest::Url::parse(&host)
        .ok()
        .and_then(|u| u.host_str().map(str::to_ascii_lowercase))
        .map(|h| !matches!(h.as_str(), "127.0.0.1" | "localhost" | "::1" | "[::1]"))
        .unwrap_or(true);

    let mut payload_val = if is_chat {
        let mut p = parsed_req.clone();
        if let Some(obj) = p.as_object_mut() {
            if !obj.contains_key("model") {
                obj.insert("model".to_string(), json!(default_model));
            }
            if !obj.contains_key("options") {
                obj.insert("options".to_string(), json!({ "num_ctx": 8192 }));
            }
        }
        p
    } else {
        let mut p = gemini_to_openai(&parsed_req, &default_model, true);
        if let Some(obj) = p.as_object_mut() {
            if !is_stream {
                obj.insert("stream".to_string(), json!(false));
            }
            obj.insert("options".to_string(), json!({ "num_ctx": 8192 }));
        }
        p
    };

    if is_remote_ollama && settings.enable_privacy_shield {
        let outcome = crate::privacy::redact_outbound_payload(http, &settings.sysd_url, &payload_val).await;
        payload_val = outcome.payload;
    }

    let payload_bytes = serde_json::to_vec(&payload_val).unwrap_or_else(|_| raw_body.to_vec());

    let target_url = format!("{}/v1/chat/completions", host);
    let send_fut = http
        .post(&target_url)
        .header("Content-Type", "application/json")
        .body(payload_bytes)
        .send();
    let upstream = match tokio::time::timeout(Duration::from_secs(120), send_fut).await {
        Ok(Ok(r)) => r,
        Ok(Err(e)) => {
            if settings.offline_resilience {
                return failover_to_local_slm(
                    http,
                    &settings.sysd_url,
                    SlmFailoverRequest {
                        is_openai: is_chat,
                        is_gemini,
                        is_stream: effective_stream,
                        target_model: &default_model,
                        parsed_body: Some(&parsed_req),
                        raw_body,
                        reason: "ollama_unreachable",
                    },
                )
                .await;
            }
            return (
                StatusCode::BAD_GATEWAY,
                Json(json!({
                    "error": {
                        "code": 502,
                        "message": format!("Ollama connection failed at {}: {}. Ensure Ollama is running.", host, e),
                        "status": "BAD_GATEWAY"
                    }
                })),
            )
                .into_response();
        }
        Err(_) => {
            if settings.offline_resilience {
                return failover_to_local_slm(
                    http,
                    &settings.sysd_url,
                    SlmFailoverRequest {
                        is_openai: is_chat,
                        is_gemini,
                        is_stream: effective_stream,
                        target_model: &default_model,
                        parsed_body: Some(&parsed_req),
                        raw_body,
                        reason: "ollama_timeout",
                    },
                )
                .await;
            }
            return (
                StatusCode::GATEWAY_TIMEOUT,
                Json(json!({
                    "error": {
                        "code": 504,
                        "message": format!("Ollama TTFB timed out at {}.", host),
                        "status": "GATEWAY_TIMEOUT"
                    }
                })),
            )
                .into_response();
        }
    };

    let status = StatusCode::from_u16(upstream.status().as_u16()).unwrap_or(StatusCode::BAD_GATEWAY);
    if status.is_server_error() && settings.offline_resilience {
        return failover_to_local_slm(
            http,
            &settings.sysd_url,
            SlmFailoverRequest {
                is_openai: is_chat,
                is_gemini,
                is_stream: effective_stream,
                target_model: &default_model,
                parsed_body: Some(&parsed_req),
                raw_body,
                reason: "ollama_server_error",
            },
        )
        .await;
    }
    if status != StatusCode::OK || is_chat {
        return passthrough_response(status, upstream, "application/json");
    }

    if is_stream {
        return stream_openai_to_gemini_response(upstream);
    }

    let raw_text = upstream.text().await.unwrap_or_default();
    let Ok(rj) = serde_json::from_str::<Value>(&raw_text) else {
        return (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "error": "Failed parsing Ollama JSON", "raw": raw_text })),
        )
            .into_response();
    };
    let msg = rj
        .pointer("/choices/0/message")
        .cloned()
        .unwrap_or_else(|| json!({}));
    let raw_txt = msg.get("content").and_then(|v| v.as_str()).unwrap_or("");
    let think_re = Regex::new(r"(?is)<think>.*?</think>").ok();
    let mut clean_txt = if let Some(re) = think_re {
        re.replace_all(raw_txt, "").trim().to_string()
    } else {
        raw_txt.trim().to_string()
    };
    let reasoning = msg.get("reasoning").and_then(|v| v.as_str()).unwrap_or("");
    let json_re = Regex::new(r"(?s)\{.*?\}").ok();
    if clean_txt.is_empty() && !reasoning.is_empty() {
        if let Some(ref re) = json_re {
            if let Some(m) = re.find(reasoning) {
                clean_txt = m.as_str().to_string();
            }
        }
    }

    let mut is_valid_json = false;
    if !clean_txt.is_empty() {
        if serde_json::from_str::<Value>(&clean_txt).is_ok() {
            is_valid_json = true;
        } else if let Some(ref re) = json_re {
            let haystack = if !clean_txt.is_empty() { &clean_txt } else { reasoning };
            if let Some(m) = re.find(haystack) {
                if serde_json::from_str::<Value>(m.as_str()).is_ok() {
                    clean_txt = m.as_str().to_string();
                    is_valid_json = true;
                }
            }
        }
    }

    if !is_valid_json
        && (parsed_req
            .pointer("/generationConfig/responseMimeType")
            .and_then(|v| v.as_str())
            == Some("application/json")
            || path_and_query.contains("generateContent"))
    {
        clean_txt = json!({ "category": 0, "status": "ok" }).to_string();
    }

    let final_txt = if !clean_txt.is_empty() {
        clean_txt
    } else if !raw_txt.is_empty() {
        raw_txt.to_string()
    } else {
        "OK".to_string()
    };

    let prompt_tok = rj.pointer("/usage/prompt_tokens").and_then(|v| v.as_u64()).unwrap_or(0);
    let cand_tok = rj.pointer("/usage/completion_tokens").and_then(|v| v.as_u64()).unwrap_or(0);
    let tot_tok = rj.pointer("/usage/total_tokens").and_then(|v| v.as_u64()).unwrap_or(0);

    let g_resp = json!({
        "response": {
            "candidates": [{
                "content": { "role": "model", "parts": [{ "text": final_txt }] },
                "finishReason": "STOP"
            }],
            "usageMetadata": {
                "promptTokenCount": prompt_tok,
                "candidatesTokenCount": cand_tok,
                "totalTokenCount": tot_tok
            }
        },
        "candidates": [{
            "content": { "role": "model", "parts": [{ "text": final_txt }] },
            "finishReason": "STOP"
        }],
        "usageMetadata": {
            "promptTokenCount": prompt_tok,
            "candidatesTokenCount": cand_tok,
            "totalTokenCount": tot_tok
        }
    });
    (StatusCode::OK, Json(g_resp)).into_response()
}

pub async fn handle_9router_request(
    http: &Client,
    path_and_query: &str,
    raw_body: &[u8],
    vault: &VaultData,
    cfg_providers: &Value,
) -> Response {
    let providers = get_effective_providers(vault, cfg_providers);
    let r9_cfg = providers.get("9router").cloned().unwrap_or_else(|| json!({}));
    let host = r9_cfg
        .get("host")
        .or_else(|| r9_cfg.get("endpoint"))
        .and_then(|v| v.as_str())
        .unwrap_or("http://127.0.0.1:20128")
        .trim_end_matches('/')
        .to_string();
    let api_key = r9_cfg
        .get("api_key")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();
    let default_model = r9_cfg
        .get("default_model")
        .or_else(|| r9_cfg.get("model"))
        .and_then(|v| v.as_str())
        .unwrap_or("clinepass/cline-pass/glm-5.2")
        .to_string();
    let is_chat = path_and_query.contains("/chat/completions");

    let payload_bytes = match serde_json::from_slice::<Value>(raw_body) {
        Ok(mut p) => {
            if is_chat {
                if let Some(obj) = p.as_object_mut() {
                    if !obj.contains_key("model") {
                        obj.insert("model".to_string(), json!(default_model));
                    }
                }
                serde_json::to_vec(&p).unwrap_or_else(|_| raw_body.to_vec())
            } else {
                let converted = gemini_to_openai(&p, &default_model, false);
                serde_json::to_vec(&converted).unwrap_or_else(|_| raw_body.to_vec())
            }
        }
        Err(_) => raw_body.to_vec(),
    };

    let target_url = if host.ends_with("/v1") {
        format!("{}/chat/completions", host)
    } else {
        format!("{}/v1/chat/completions", host)
    };

    let mut req = http
        .post(&target_url)
        .header("Content-Type", "application/json")
        .body(payload_bytes);
    if !api_key.is_empty() {
        req = req.header("Authorization", format!("Bearer {}", api_key));
    }

    let upstream = match tokio::time::timeout(Duration::from_secs(90), req.send()).await {
        Ok(Ok(r)) => r,
        Ok(Err(e)) => {
            return (
                StatusCode::BAD_GATEWAY,
                Json(json!({
                    "error": {
                        "code": 502,
                        "message": format!("9Router connection failed at {}: {}.", host, e),
                        "status": "BAD_GATEWAY"
                    }
                })),
            )
                .into_response();
        }
        Err(_) => {
            return (
                StatusCode::GATEWAY_TIMEOUT,
                Json(json!({
                    "error": {
                        "code": 504,
                        "message": format!("9Router TTFB timed out at {}.", host),
                        "status": "GATEWAY_TIMEOUT"
                    }
                })),
            )
                .into_response();
        }
    };

    let status = StatusCode::from_u16(upstream.status().as_u16()).unwrap_or(StatusCode::BAD_GATEWAY);
    if status != StatusCode::OK || is_chat {
        return passthrough_response(status, upstream, "application/json");
    }

    stream_openai_to_gemini_response(upstream)
}

pub fn build_sysd_openai_request(
    target_model: &str,
    parsed_body: Option<&Value>,
    raw_body: &[u8],
) -> Value {
    let model_name = if target_model.trim().is_empty() {
        "l0-router"
    } else {
        target_model
    };
    let base_val = parsed_body
        .cloned()
        .or_else(|| serde_json::from_slice::<Value>(raw_body).ok())
        .unwrap_or_else(|| json!({}));

    if base_val
        .get("messages")
        .and_then(|v| v.as_array())
        .map(|a| !a.is_empty())
        .unwrap_or(false)
    {
        let mut req = base_val;
        if let Some(obj) = req.as_object_mut() {
            obj.insert("stream".to_string(), json!(false));
            if !obj.contains_key("model")
                || obj
                    .get("model")
                    .and_then(|v| v.as_str())
                    .map(|s| s.trim().is_empty())
                    .unwrap_or(true)
            {
                obj.insert("model".to_string(), json!(model_name));
            }
        }
        return req;
    }

    if base_val.get("contents").is_some() || base_val.get("request").is_some() {
        let mut conv = gemini_to_openai(&base_val, model_name, true);
        if let Some(obj) = conv.as_object_mut() {
            obj.insert("stream".to_string(), json!(false));
        }
        return conv;
    }

    if let Some(prompt) = base_val.get("prompt").and_then(|v| v.as_str()) {
        return json!({
            "model": model_name,
            "messages": [{ "role": "user", "content": prompt }],
            "stream": false
        });
    }

    let raw_str = String::from_utf8_lossy(raw_body).trim().to_string();
    json!({
        "model": model_name,
        "messages": [{ "role": "user", "content": if raw_str.is_empty() { "health".to_string() } else { raw_str } }],
        "stream": false
    })
}

pub fn format_slm_failover_response(
    sysd_json: &Value,
    is_openai: bool,
    is_gemini: bool,
    is_stream: bool,
    target_model: &str,
    reason: &str,
) -> Response {
    let content = sysd_json
        .pointer("/choices/0/message/content")
        .or_else(|| sysd_json.get("response"))
        .and_then(|v| v.as_str())
        .unwrap_or("L0 SLM standby ready.");
    let used_model = sysd_json
        .get("model")
        .and_then(|v| v.as_str())
        .filter(|s| !s.trim().is_empty())
        .unwrap_or_else(|| {
            if target_model.trim().is_empty() {
                "l0-router"
            } else {
                target_model
            }
        });
    let safe_reason: String = reason
        .chars()
        .map(|c| if matches!(c, '\r' | '\n') { ' ' } else { c })
        .collect();

    let add_failover_headers = |mut builder: axum::http::response::Builder| {
        if let Ok(hv) = HeaderValue::from_str("sysd-l0-slm") {
            builder = builder.header("x-flowork-failover", hv);
        }
        if let Ok(hv) = HeaderValue::from_str(&safe_reason) {
            builder = builder.header("x-flowork-failover-reason", hv);
        }
        builder
    };

    if is_openai {
        if is_stream {
            let hex_id = &Uuid::new_v4().simple().to_string()[..24];
            let completion_id = format!("chatcmpl-{}", hex_id);
            let created = now_ms() / 1000;
            let first = json!({
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": used_model,
                "choices": [{
                    "index": 0,
                    "delta": { "role": "assistant", "content": content },
                    "finish_reason": Value::Null
                }]
            });
            let stop = json!({
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": used_model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            });
            let sse_body = format!("data: {}\n\ndata: {}\n\ndata: [DONE]\n\n", first, stop);
            return add_failover_headers(
                Response::builder()
                    .status(StatusCode::OK)
                    .header("Content-Type", "text/event-stream; charset=utf-8")
                    .header("Cache-Control", "no-cache")
                    .header("Connection", "keep-alive"),
            )
            .body(Body::from(sse_body))
            .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response());
        }

        let mut payload = create_openai_json_response(content, used_model);
        if let Some(obj) = payload.as_object_mut() {
            if let Some(u) = sysd_json.get("usage") {
                obj.insert("usage".to_string(), u.clone());
            }
            for key in [
                "route",
                "confidence",
                "intent",
                "args",
                "normalized_keywords",
                "backend",
                "latency_ms",
                "executed_locally",
                "tool_traces",
            ] {
                if let Some(val) = sysd_json.get(key) {
                    obj.insert(key.to_string(), val.clone());
                }
            }
            obj.insert(
                "failover".to_string(),
                json!({
                    "active": true,
                    "provider": "sysd-l0-slm",
                    "reason": reason
                }),
            );
        }
        return add_failover_headers(
            Response::builder()
                .status(StatusCode::OK)
                .header("Content-Type", "application/json"),
        )
        .body(Body::from(payload.to_string()))
        .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response());
    }

    let prompt_tok = sysd_json
        .pointer("/usage/prompt_tokens")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);
    let cand_tok = sysd_json
        .pointer("/usage/completion_tokens")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);
    let tot_tok = sysd_json
        .pointer("/usage/total_tokens")
        .and_then(|v| v.as_u64())
        .unwrap_or(prompt_tok + cand_tok);

    let candidate = json!({
        "candidates": [{
            "content": { "role": "model", "parts": [{ "text": content }] },
            "finishReason": "STOP"
        }],
        "usageMetadata": {
            "promptTokenCount": prompt_tok,
            "candidatesTokenCount": cand_tok,
            "totalTokenCount": tot_tok
        }
    });

    if is_stream {
        let ev = if is_gemini {
            candidate
        } else {
            json!({ "response": candidate })
        };
        let sse_body = format!("data: {}\n\ndata: [DONE]\n\n", ev);
        return add_failover_headers(
            Response::builder()
                .status(StatusCode::OK)
                .header("Content-Type", "text/event-stream; charset=utf-8")
                .header("Cache-Control", "no-cache")
                .header("Connection", "keep-alive"),
        )
        .body(Body::from(sse_body))
        .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response());
    }

    let json_body = if is_gemini {
        candidate
    } else {
        json!({ "response": candidate })
    };
    add_failover_headers(
        Response::builder()
            .status(StatusCode::OK)
            .header("Content-Type", "application/json"),
    )
    .body(Body::from(json_body.to_string()))
    .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response())
}

pub struct SlmFailoverRequest<'a> {
    pub is_openai: bool,
    pub is_gemini: bool,
    pub is_stream: bool,
    pub target_model: &'a str,
    pub parsed_body: Option<&'a Value>,
    pub raw_body: &'a [u8],
    pub reason: &'a str,
}

pub async fn failover_to_local_slm(
    http: &Client,
    sysd_url: &str,
    req: SlmFailoverRequest<'_>,
) -> Response {
    let endpoint = format!("{}/v1/chat/completions", sysd_url.trim_end_matches('/'));
    let sysd_req = build_sysd_openai_request(req.target_model, req.parsed_body, req.raw_body);

    eprintln!(
        "[Air-Gapped Failover] Routing request to flowork-sysd L0 SLM at {} (reason: {})",
        endpoint, req.reason
    );

    let req_fut = http
        .post(&endpoint)
        .header("Content-Type", "application/json")
        .json(&sysd_req)
        .send();

    let upstream = match tokio::time::timeout(Duration::from_secs(15), req_fut).await {
        Ok(Ok(r)) => r,
        Ok(Err(e)) => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({
                    "error": {
                        "code": 503,
                        "message": format!(
                            "Cloud/Ollama unavailable ({}) and flowork-sysd L0 failover unreachable at {}: {}",
                            req.reason, endpoint, e
                        ),
                        "status": "UNAVAILABLE"
                    }
                })),
            )
                .into_response();
        }
        Err(_) => {
            return (
                StatusCode::GATEWAY_TIMEOUT,
                Json(json!({
                    "error": {
                        "code": 504,
                        "message": format!("Air-gapped failover ({}) timed out contacting {}", req.reason, endpoint),
                        "status": "GATEWAY_TIMEOUT"
                    }
                })),
            )
                .into_response();
        }
    };

    if !upstream.status().is_success() {
        let code = upstream.status().as_u16();
        let body = upstream.text().await.unwrap_or_default();
        return (
            StatusCode::BAD_GATEWAY,
            Json(json!({
                "error": {
                    "code": code,
                    "message": format!("flowork-sysd L0 failover returned HTTP {}: {}", code, body),
                    "status": "BAD_GATEWAY"
                }
            })),
        )
            .into_response();
    }

    match upstream.json::<Value>().await {
        Ok(sysd_json) => format_slm_failover_response(
            &sysd_json,
            req.is_openai,
            req.is_gemini,
            req.is_stream,
            req.target_model,
            req.reason,
        ),
        Err(e) => (
            StatusCode::BAD_GATEWAY,
            Json(json!({
                "error": {
                    "code": 502,
                    "message": format!("Invalid JSON returned by flowork-sysd L0 failover: {}", e),
                    "status": "BAD_GATEWAY"
                }
            })),
        )
            .into_response(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::to_bytes;

    #[test]
    fn builds_sysd_openai_request_from_gemini_and_openai_inputs() {
        let gemini = json!({
            "contents": [{ "role": "user", "parts": [{ "text": "cari tangkapan layar error" }] }]
        });
        let conv = build_sysd_openai_request("gemini-3.8-flash-high", Some(&gemini), b"");
        assert_eq!(conv["stream"], false);
        assert_eq!(conv["messages"][0]["content"], "cari tangkapan layar error");

        let openai = json!({
            "model": "gpt-4o",
            "messages": [{ "role": "user", "content": "cek sistem" }],
            "stream": true
        });
        let req = build_sysd_openai_request("", Some(&openai), b"");
        assert_eq!(req["stream"], false);
        assert_eq!(req["model"], "gpt-4o");
    }

    #[tokio::test]
    async fn formats_slm_failover_for_openai_json_and_gemini_sse() {
        let sysd_json = json!({
            "model": "l0-router-heuristic",
            "choices": [{ "message": { "role": "assistant", "content": "L0 handled screen search" } }],
            "usage": { "prompt_tokens": 4, "completion_tokens": 4, "total_tokens": 8 },
            "route": "local_action",
            "confidence": 0.94,
            "intent": "flowfs_screen_search",
            "normalized_keywords": ["screen", "search"]
        });

        let resp_openai = format_slm_failover_response(
            &sysd_json,
            true,
            false,
            false,
            "l0-router",
            "cloudcode_unavailable",
        );
        assert_eq!(resp_openai.status(), StatusCode::OK);
        assert_eq!(
            resp_openai
                .headers()
                .get("x-flowork-failover")
                .and_then(|v| v.to_str().ok()),
            Some("sysd-l0-slm")
        );
        let bytes = to_bytes(resp_openai.into_body(), 64 * 1024).await.unwrap();
        let val: Value = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(val["choices"][0]["message"]["content"], "L0 handled screen search");
        assert_eq!(val["failover"]["active"], true);
        assert_eq!(val["normalized_keywords"][0], "screen");

        let resp_gemini_sse = format_slm_failover_response(
            &sysd_json,
            false,
            true,
            true,
            "gemini-3.8-flash-high",
            "cloudcode_unavailable",
        );
        assert_eq!(resp_gemini_sse.status(), StatusCode::OK);
        let sse_bytes = to_bytes(resp_gemini_sse.into_body(), 64 * 1024).await.unwrap();
        let sse_str = String::from_utf8(sse_bytes.to_vec()).unwrap();
        assert!(sse_str.contains("L0 handled screen search"));
        assert!(sse_str.contains("[DONE]"));
    }
}

