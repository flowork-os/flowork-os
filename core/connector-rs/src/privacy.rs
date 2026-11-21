// =============================================================================
// Flowork Sovereign Connector — Pre-Egress Privacy Shield Middleware
// Delegates to flowork-sysd /api/agent/privacy/redact with local fail-safe
// =============================================================================

use regex::Regex;
use reqwest::Client;
use serde_json::{json, Map, Value};
use std::collections::BTreeSet;
use std::sync::OnceLock;
use std::time::Duration;

#[derive(Debug, Clone)]
pub struct PreEgressRedactOutcome {
    pub payload: Value,
    pub redacted: bool,
    pub findings_count: usize,
    pub categories: Vec<String>,
    pub via_sysd: bool,
}

pub async fn redact_outbound_payload(
    http: &Client,
    sysd_url: &str,
    payload: &Value,
) -> PreEgressRedactOutcome {
    let endpoint = format!("{}/api/agent/privacy/redact", sysd_url.trim_end_matches('/'));
    let req_fut = http
        .post(&endpoint)
        .json(&json!({ "payload": payload }))
        .timeout(Duration::from_millis(400))
        .send();

    if let Ok(resp) = req_fut.await {
        if resp.status().is_success() {
            if let Ok(v) = resp.json::<Value>().await {
                if let Some(sanitized) = v.get("sanitized_payload") {
                    let redacted = v.get("redacted").and_then(|b| b.as_bool()).unwrap_or(false);
                    let findings_count =
                        v.get("findings_count").and_then(|n| n.as_u64()).unwrap_or(0) as usize;
                    let categories = v
                        .get("categories")
                        .and_then(|a| a.as_array())
                        .map(|arr| {
                            arr.iter()
                                .filter_map(|x| x.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                        .unwrap_or_default();
                    return PreEgressRedactOutcome {
                        payload: sanitized.clone(),
                        redacted,
                        findings_count,
                        categories,
                        via_sysd: true,
                    };
                }
            }
        }
    }

    // Fail-safe in-process scanner if sysd is momentarily restarting or unreachable.
    redact_json_local(payload)
}

pub fn redact_text_local(input: &str) -> (String, usize, Vec<String>) {
    if input.is_empty() {
        return (String::new(), 0, Vec::new());
    }

    static SIMPLE_RULES: OnceLock<Vec<(&'static str, Regex, &'static str)>> = OnceLock::new();
    let compiled = SIMPLE_RULES.get_or_init(|| {
        let defs: &[(&str, &str, &str)] = &[
            (
                "pem_private_key",
                r"(?s)-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
                "[REDACTED_PRIVATE_KEY_BLOCK]",
            ),
            (
                "google_oauth_token",
                r"\bya29\.[A-Za-z0-9._-]{8,}\b",
                "[REDACTED_GOOGLE_OAUTH_TOKEN]",
            ),
            (
                "google_api_key",
                r"\bAIza[0-9A-Za-z_-]{20,}\b",
                "[REDACTED_GOOGLE_API_KEY]",
            ),
            (
                "github_token",
                r"\b(?:gh[pous]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b",
                "[REDACTED_GITHUB_TOKEN]",
            ),
            (
                "api_secret_key",
                r"\b(?:sk-ant-[A-Za-z0-9_-]{16,}|sk-proj-[A-Za-z0-9_-]{16,}|sk-[A-Za-z0-9_-]{20,}|flw_(?:live|secret)_[A-Za-z0-9_-]{12,})\b",
                "[REDACTED_API_KEY]",
            ),
            (
                "aws_access_key",
                r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
                "[REDACTED_AWS_KEY]",
            ),
            (
                "jwt_token",
                r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b",
                "[REDACTED_JWT_TOKEN]",
            ),
            (
                "private_lan_ip",
                r"\b(?:10\.(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){2}|192\.168(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){2})\b",
                "[REDACTED_PRIVATE_IP]",
            ),
            (
                "sensitive_home_path",
                r"/home/[A-Za-z0-9._-]+/(\.(?:ssh|gnupg|aws|config/gcloud|netrc)|flowork\.dev)",
                "/home/[REDACTED_USER]/$1",
            ),
        ];
        defs.iter()
            .filter_map(|(cat, pat, rep)| Regex::new(pat).ok().map(|re| (*cat, re, *rep)))
            .collect()
    });

    // Never corrupt base64 data URIs (e.g. OpenAI image_url attachments)
    let trimmed_inp = input.trim_start();
    if trimmed_inp.starts_with("data:") && trimmed_inp[..trimmed_inp.len().min(96)].contains(";base64,") {
        return (input.to_string(), 0, Vec::new());
    }

    let mut text = input.to_string();
    let mut cats = BTreeSet::new();
    let mut hits = 0usize;

    for (cat, re, rep) in compiled {
        let count = re.find_iter(&text).count();
        if count > 0 {
            text = re.replace_all(&text, *rep).into_owned();
            cats.insert((*cat).to_string());
            hits += count;
        }
    }

    static REFRESH_RE: OnceLock<Regex> = OnceLock::new();
    let refresh_re = REFRESH_RE.get_or_init(|| {
        Regex::new(r"(^|[^A-Za-z0-9_/+=-])(1//[A-Za-z0-9_-]{12,})").expect("valid refresh regex")
    });
    let refresh_hits = refresh_re.find_iter(&text).count();
    if refresh_hits > 0 {
        text = refresh_re
            .replace_all(&text, "${1}[REDACTED_GOOGLE_REFRESH_TOKEN]")
            .into_owned();
        cats.insert("google_refresh_token".to_string());
        hits += refresh_hits;
    }

    static BEARER_RE: OnceLock<Regex> = OnceLock::new();
    let bearer_re = BEARER_RE.get_or_init(|| {
        Regex::new(r"(?i)\b(Bearer)\s+([A-Za-z0-9._~+/=-]{16,})").expect("valid bearer regex")
    });
    let mut bearer_hits = 0usize;
    let replaced_bearer = bearer_re.replace_all(&text, |caps: &regex::Captures| {
        let tok = caps.get(2).map(|m| m.as_str()).unwrap_or("");
        if tok.starts_with("[REDACTED_") {
            caps.get(0).map(|m| m.as_str()).unwrap_or("").to_string()
        } else {
            bearer_hits += 1;
            format!("{} [REDACTED_BEARER_TOKEN]", &caps[1])
        }
    });
    if bearer_hits > 0 {
        text = replaced_bearer.into_owned();
        cats.insert("bearer_secret".to_string());
        hits += bearer_hits;
    }

    (text, hits, cats.into_iter().collect())
}

pub fn redact_json_local(payload: &Value) -> PreEgressRedactOutcome {
    let mut cats = BTreeSet::new();
    let mut findings = 0usize;
    let sanitized = scrub_json(payload, None, &mut cats, &mut findings);
    PreEgressRedactOutcome {
        payload: sanitized,
        redacted: findings > 0,
        findings_count: findings,
        categories: cats.into_iter().collect(),
        via_sysd: false,
    }
}

fn is_structural_key(k: &str) -> bool {
    matches!(
        k,
        "role"
            | "model"
            | "project"
            | "type"
            | "mimeType"
            | "mime_type"
            | "finishReason"
            | "finish_reason"
            | "object"
            | "id"
            | "name"
            | "thoughtSignature"
            | "thought_signature"
            | "signature"
            | "toolCallId"
            | "tool_call_id"
            | "call_id"
            | "fileUri"
            | "file_uri"
            | "b64_json"
            | "imageBytes"
            | "image_bytes"
    )
}

fn is_opaque_subtree_key(k: &str) -> bool {
    matches!(
        k,
        "tools"
            | "functionDeclarations"
            | "function_declarations"
            | "parameters"
            | "inlineData"
            | "inline_data"
            | "fileData"
            | "file_data"
    )
}

fn scrub_json(
    val: &Value,
    parent_key: Option<&str>,
    cats: &mut BTreeSet<String>,
    findings: &mut usize,
) -> Value {
    match val {
        Value::String(s) => {
            if parent_key.map(is_structural_key).unwrap_or(false) {
                return Value::String(s.clone());
            }
            let (out, n, found_cats) = redact_text_local(s);
            if n > 0 {
                *findings += n;
                for c in found_cats {
                    cats.insert(c);
                }
            }
            Value::String(out)
        }
        Value::Array(arr) => Value::Array(
            arr.iter()
                .map(|x| scrub_json(x, parent_key, cats, findings))
                .collect(),
        ),
        Value::Object(map) => {
            if parent_key.map(is_opaque_subtree_key).unwrap_or(false) {
                return Value::Object(map.clone());
            }
            let mut out = Map::new();
            for (k, v) in map {
                out.insert(k.clone(), scrub_json(v, Some(k.as_str()), cats, findings));
            }
            Value::Object(out)
        }
        other => other.clone(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn redacts_bearer_ya29_and_keys_before_egress() {
        let gh_tok = format!("{}_{}", "ghp", "0123456789abcdefghij");
        let input = json!({
            "messages": [{
                "role": "user",
                "content": format!("Here is Authorization: Bearer ya29.test_secret_token and {}", gh_tok)
            }]
        });
        let out = redact_json_local(&input);
        assert!(out.redacted);
        let msg = out.payload["messages"][0]["content"].as_str().unwrap();
        assert!(!msg.contains("ya29.test_secret_token"));
        assert!(!msg.contains(&gh_tok));
        assert!(msg.contains("REDACTED_GOOGLE_OAUTH_TOKEN"));
        assert!(msg.contains("REDACTED_GITHUB_TOKEN"));
    }

    #[test]
    fn preserves_inline_data_base64_and_thought_signatures() {
        let b64_png = format!("foQDypTyg9jjsc6jlQwLzk+e2fQKkt{}//nv2afI60lUeAnnIDEzZucZMqhxRr4Kd3Ih", "1");
        let sig = format!("AAAA{}//nv2afI60lUeAnnIDEzZucZMqhxRr4", "1");
        let ref_tok = format!("{}//{}", "1", "04refresh_secret_abcdef12");
        let input = json!({
            "contents": [{
                "role": "model",
                "parts": [{
                    "text": format!("Token {}", ref_tok),
                    "thoughtSignature": sig
                }]
            }, {
                "role": "user",
                "parts": [{
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": b64_png
                    }
                }]
            }]
        });
        let out = redact_json_local(&input);
        assert!(out.redacted);
        assert_eq!(out.payload["contents"][0]["parts"][0]["thoughtSignature"], sig);
        assert_eq!(out.payload["contents"][1]["parts"][0]["inlineData"]["data"], b64_png);
        assert!(out.payload["contents"][0]["parts"][0]["text"]
            .as_str()
            .unwrap()
            .contains("REDACTED_GOOGLE_REFRESH_TOKEN"));
    }
}
