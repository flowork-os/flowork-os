use axum::body::Body;
use axum::http::{HeaderMap, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::Json;
use bytes::Bytes;
use futures_util::StreamExt;
use regex::Regex;
use reqwest::Client;
use serde_json::{json, Value};
use std::time::Duration;

use crate::config::default_providers_value;
use crate::translator::{gemini_to_openai, OpenAiToGeminiState};
use crate::vault::VaultData;

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
    let payload_bytes = if is_chat {
        let mut p = parsed_req.clone();
        if let Some(obj) = p.as_object_mut() {
            if !obj.contains_key("model") {
                obj.insert("model".to_string(), json!(default_model));
            }
            if !obj.contains_key("options") {
                obj.insert("options".to_string(), json!({ "num_ctx": 8192 }));
            }
        }
        serde_json::to_vec(&p).unwrap_or_else(|_| raw_body.to_vec())
    } else {
        let mut p = gemini_to_openai(&parsed_req, &default_model, true);
        if let Some(obj) = p.as_object_mut() {
            if !is_stream {
                obj.insert("stream".to_string(), json!(false));
            }
            obj.insert("options".to_string(), json!({ "num_ctx": 8192 }));
        }
        serde_json::to_vec(&p).unwrap_or_else(|_| raw_body.to_vec())
    };

    let target_url = format!("{}/v1/chat/completions", host);
    let send_fut = http
        .post(&target_url)
        .header("Content-Type", "application/json")
        .body(payload_bytes)
        .send();
    let upstream = match tokio::time::timeout(Duration::from_secs(120), send_fut).await {
        Ok(Ok(r)) => r,
        Ok(Err(e)) => {
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
