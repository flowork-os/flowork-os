// =============================================================================
// Flowork Sovereign OS — Pre-Egress Privacy & Secret Shield (Pure Rust)
// Scrubs OAuth tokens, API keys, JWTs, PEM blocks, private LAN IPs, & user PII
// =============================================================================

use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use std::collections::BTreeSet;
use std::sync::OnceLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RedactReport {
    pub sanitized_text: String,
    pub redacted: bool,
    pub findings_count: usize,
    pub categories: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JsonRedactReport {
    pub sanitized_payload: Value,
    pub redacted: bool,
    pub findings_count: usize,
    pub categories: Vec<String>,
}

struct CompiledRules {
    rules: Vec<(&'static str, Regex, &'static str)>,
}

static RULES: OnceLock<CompiledRules> = OnceLock::new();

fn rules() -> &'static CompiledRules {
    RULES.get_or_init(|| {
        let defs: Vec<(&'static str, &'static str, &'static str)> = vec![
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
                "google_refresh_token",
                r"1//[A-Za-z0-9_-]{12,}",
                "[REDACTED_GOOGLE_REFRESH_TOKEN]",
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

        // Standard Rust regex doesn't support negative lookahead (?!...), so handle patterns without lookahead cleanly.
        let mut compiled = Vec::new();
        for (cat, pat, rep) in defs {
            if let Ok(re) = Regex::new(pat) {
                compiled.push((cat, re, rep));
            }
        }
        CompiledRules { rules: compiled }
    })
}

pub struct PrivacyShield;

impl PrivacyShield {
    pub fn redact_text(input: &str) -> RedactReport {
        if input.is_empty() {
            return RedactReport {
                sanitized_text: String::new(),
                redacted: false,
                findings_count: 0,
                categories: Vec::new(),
            };
        }

        let mut text = input.to_string();
        let mut categories = BTreeSet::new();
        let mut total_hits = 0usize;

        for (cat, re, replacement) in &rules().rules {
            let count = re.find_iter(&text).count();
            if count > 0 {
                text = re.replace_all(&text, *replacement).into_owned();
                categories.insert((*cat).to_string());
                total_hits += count;
            }
        }

        // Handle generic Bearer <long_secret> without overwriting already [REDACTED_...] markers
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
            categories.insert("bearer_secret".to_string());
            total_hits += bearer_hits;
        }

        // Handle sensitive ENV/config key assignments safely without lookahead
        static ENV_RE: OnceLock<Regex> = OnceLock::new();
        let env_re = ENV_RE.get_or_init(|| {
            Regex::new(r"(?i)\b(AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_API_KEY|CLIENT_SECRET|REFRESH_TOKEN|ACCESS_TOKEN|DB_PASSWORD|SECRET_KEY)\s*([:=])\s*([^\s,;}\]]{8,})")
                .expect("valid env regex")
        });
        let mut env_hits = 0usize;
        let replaced_env = env_re.replace_all(&text, |caps: &regex::Captures| {
            let raw_val = caps.get(3).map(|m| m.as_str()).unwrap_or("");
            let trimmed = raw_val.trim_matches(|c| c == '"' || c == '\'');
            if trimmed.starts_with("[REDACTED_") || trimmed.is_empty() {
                caps.get(0).map(|m| m.as_str()).unwrap_or("").to_string()
            } else {
                env_hits += 1;
                format!("{}{} \"[REDACTED_CREDENTIAL]\"", &caps[1], &caps[2])
            }
        });
        if env_hits > 0 {
            text = replaced_env.into_owned();
            categories.insert("env_secret_assignment".to_string());
            total_hits += env_hits;
        }

        RedactReport {
            sanitized_text: text,
            redacted: total_hits > 0,
            findings_count: total_hits,
            categories: categories.into_iter().collect(),
        }
    }

    pub fn redact_json(payload: &Value) -> JsonRedactReport {
        let mut categories = BTreeSet::new();
        let mut findings = 0usize;
        let sanitized = scrub_value(payload, None, &mut categories, &mut findings);
        JsonRedactReport {
            sanitized_payload: sanitized,
            redacted: findings > 0,
            findings_count: findings,
            categories: categories.into_iter().collect(),
        }
    }
}

fn is_structural_key(key: &str) -> bool {
    matches!(
        key,
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
    )
}

fn scrub_value(
    val: &Value,
    parent_key: Option<&str>,
    categories: &mut BTreeSet<String>,
    findings: &mut usize,
) -> Value {
    match val {
        Value::String(s) => {
            if parent_key.map(is_structural_key).unwrap_or(false) {
                return Value::String(s.clone());
            }
            let report = PrivacyShield::redact_text(s);
            if report.redacted {
                *findings += report.findings_count;
                for c in report.categories {
                    categories.insert(c);
                }
            }
            Value::String(report.sanitized_text)
        }
        Value::Array(arr) => Value::Array(
            arr.iter()
                .map(|item| scrub_value(item, parent_key, categories, findings))
                .collect(),
        ),
        Value::Object(map) => {
            // Preserve JSON schema / functionDeclarations definitions verbatim so API contracts don't shift
            if parent_key == Some("tools") || parent_key == Some("functionDeclarations") || parent_key == Some("parameters") {
                return Value::Object(map.clone());
            }
            let mut out = Map::new();
            for (k, v) in map {
                out.insert(k.clone(), scrub_value(v, Some(k.as_str()), categories, findings));
            }
            Value::Object(out)
        }
        other => other.clone(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn redacts_google_oauth_jwt_github_pem_and_private_ip() {
        let gh_tok = format!("{}_{}", "ghp", "1234567890abcdefghijklmnop");
        let pem_begin = format!("{}{}", "-----BEGIN ", "RSA PRIVATE KEY-----");
        let pem_end = format!("{}{}", "-----END ", "RSA PRIVATE KEY-----");
        let jwt_tok = format!("{}.{}.{}", "eyJhbGciOiJIUzI1NiJ9", "eyJzdWIiOiIxMjM0NTY3ODkwIn0", "testsig12345678");
        let raw = format!(
            "Authorization: Bearer ya29.test_secret_token\n\
             GITHUB_TOKEN={}\n\
             JWT {}\n\
             DB host 192.168.10.42 localhost 127.0.0.1\n\
             {}\nMIIEowIBAAK\n{}",
            gh_tok, jwt_tok, pem_begin, pem_end
        );
        let rep = PrivacyShield::redact_text(&raw);
        assert!(rep.redacted);
        assert!(!rep.sanitized_text.contains("ya29.test_secret_token"));
        assert!(!rep.sanitized_text.contains(&gh_tok));
        assert!(!rep.sanitized_text.contains("192.168.10.42"));
        assert!(!rep.sanitized_text.contains("MIIEowIBAAK"));
        assert!(rep.sanitized_text.contains("127.0.0.1")); // Keep loopback intact
        assert!(rep.categories.contains(&"google_oauth_token".to_string()));
        assert!(rep.categories.contains(&"private_lan_ip".to_string()));
        assert!(rep.categories.contains(&"pem_private_key".to_string()));
    }

    #[test]
    fn redacts_json_prompts_while_preserving_tool_schemas() {
        let sk_tok = format!("{}-{}", "sk-ant", "secretvalue1234567890");
        let payload = json!({
            "model": "gemini-3.8-flash-high",
            "request": {
                "contents": [{
                    "role": "user",
                    "parts": [{ "text": format!("Debug token Bearer ya29.test_secret_token and key {}", sk_tok) }]
                }],
                "tools": [{
                    "functionDeclarations": [{
                        "name": "run_command",
                        "description": "Runs tool on 10.0.0.1"
                    }]
                }]
            }
        });
        let rep = PrivacyShield::redact_json(&payload);
        assert!(rep.redacted);
        let text = rep.sanitized_payload["request"]["contents"][0]["parts"][0]["text"]
            .as_str()
            .unwrap();
        assert!(!text.contains("ya29.test_secret_token"));
        assert!(!text.contains("secretvalue1234567890"));
        // Tool declarations untouched
        assert_eq!(
            rep.sanitized_payload["request"]["tools"][0]["functionDeclarations"][0]["name"],
            "run_command"
        );
    }
}
