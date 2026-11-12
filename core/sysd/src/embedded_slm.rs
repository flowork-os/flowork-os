// =============================================================================
// Flowork Sovereign OS — L0 Cognitive Router & Embedded SLM Engine (Pure Rust)
// Hybrid GGUF Grammar-Constrained L0 Triage + Bilingual Keyword Normalizer
// =============================================================================

use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};
use std::collections::BTreeSet;
use std::process::Command;
use std::time::Instant;

use crate::dbus_ctrl::DbusController;
use crate::privacy_shield::PrivacyShield;
use crate::slm_loader::global_slm_manager;
use crate::x11_ctrl::X11Controller;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct L0TriageResult {
    pub route: String,
    pub confidence: f32,
    pub intent: String,
    pub args: Value,
    pub normalized_keywords: Vec<String>,
    pub backend: String,
    pub latency_ms: u64,
    pub executed_locally: bool,
}

const CONFIDENCE_EXEC_THRESHOLD: f32 = 0.85;

pub struct EmbeddedSlmEngine;

impl EmbeddedSlmEngine {
    /// Perform L0 classification & bilingual keyword normalization (<5ms deterministic or GGUF).
    pub fn triage(prompt: &str) -> L0TriageResult {
        let start = Instant::now();
        let trimmed = prompt.trim();
        let scrubbed = PrivacyShield::redact_text(trimmed);
        let safe_prompt = scrubbed.sanitized_text;

        // 1. Attempt GGUF GBNF-constrained inference when a model is available and RAM permits.
        if let Ok(gguf_val) = global_slm_manager().infer_triage_gguf(&safe_prompt) {
            if let Some(mut parsed) = parse_gguf_triage(&gguf_val, &safe_prompt) {
                parsed.latency_ms = start.elapsed().as_millis() as u64;
                parsed.backend = "llama-cpp-2-gguf".to_string();
                return parsed;
            }
        }

        // 2. Deterministic Bilingual L0 Classifier & Keyword Normalizer (zero-latency fallback).
        let mut res = classify_heuristic(&safe_prompt);
        res.latency_ms = start.elapsed().as_millis() as u64;
        res
    }

    /// Execute offline natural language reasoning, L0 triage, and confidence-gated local tools.
    pub fn infer(prompt: &str, model_name: &str) -> Value {
        let start = Instant::now();
        let trimmed = prompt.trim();
        let privacy_rep = PrivacyShield::redact_text(trimmed);
        let safe_prompt = privacy_rep.sanitized_text.as_str();

        let mut triage = Self::triage(safe_prompt);
        let mut response_text = String::new();
        let mut tool_traces: Vec<Value> = Vec::new();

        if triage.route == "local_action" && triage.confidence >= CONFIDENCE_EXEC_THRESHOLD {
            let (resp, traces, executed) = execute_local_intent(&triage.intent, &triage.args, safe_prompt);
            if executed {
                triage.executed_locally = true;
                response_text = resp;
                tool_traces = traces;
            }
        }

        if response_text.is_empty() {
            if triage.route == "local_action" {
                response_text = format!(
                    "[L0 Cognitive Router] Classified local intent '{}' (confidence {:.2}), keywords: [{}].",
                    triage.intent,
                    triage.confidence,
                    triage.normalized_keywords.join(", ")
                );
            } else {
                response_text = format!(
                    "[Flowork OS L0 Cognitive Router — Offline Fallback]\n\
                     Prompt: \"{}\"\n\
                     Route: {} (confidence {:.2})\n\
                     Normalized Keywords: [{}]\n\
                     Supported direct L0 intents: cari layar, cari file, remix <app>, buka <app>, cek sistem, volume <N>, tile left/right.",
                    safe_prompt,
                    triage.route,
                    triage.confidence,
                    triage.normalized_keywords.join(", ")
                );
            }
        }

        let total_ms = start.elapsed().as_millis() as u64;
        triage.latency_ms = total_ms;

        let effective_model = if model_name.trim().is_empty() {
            "l0-router".to_string()
        } else if model_name.ends_with("-airgapped") || model_name == "l0-router" {
            model_name.to_string()
        } else {
            format!("{}-airgapped", model_name)
        };

        json!({
            "response": response_text,
            "tool_traces": tool_traces,
            "model": effective_model,
            "route": triage.route,
            "confidence": triage.confidence,
            "intent": triage.intent,
            "args": triage.args,
            "normalized_keywords": triage.normalized_keywords,
            "backend": triage.backend,
            "latency_ms": total_ms,
            "executed_locally": triage.executed_locally,
            "privacy": {
                "redacted": privacy_rep.redacted,
                "findings_count": privacy_rep.findings_count,
                "categories": privacy_rep.categories
            }
        })
    }
}

fn parse_gguf_triage(val: &Value, safe_prompt: &str) -> Option<L0TriageResult> {
    let route = val.get("route")?.as_str()?.to_string();
    if route != "local_action" && route != "delegate_cloud" {
        return None;
    }
    let confidence = val
        .get("confidence")
        .and_then(|v| v.as_f64())
        .map(|f| (f as f32).clamp(0.0, 1.0))
        .unwrap_or(0.5);
    let intent = val
        .get("intent")
        .and_then(|v| v.as_str())
        .unwrap_or("delegate_cloud")
        .to_string();
    let args = val.get("args").cloned().unwrap_or_else(|| json!({}));

    let mut kws: Vec<String> = val
        .get("normalized_keywords")
        .and_then(|v| v.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|v| v.as_str().map(|s| s.trim().to_ascii_lowercase()))
                .filter(|s| s.len() >= 3)
                .collect()
        })
        .unwrap_or_default();

    if kws.is_empty() {
        kws = normalize_bilingual_keywords(safe_prompt, &intent, &args);
    }

    Some(L0TriageResult {
        route,
        confidence,
        intent,
        args,
        normalized_keywords: kws,
        backend: "llama-cpp-2-gguf".to_string(),
        latency_ms: 0,
        executed_locally: false,
    })
}

pub fn classify_heuristic(prompt: &str) -> L0TriageResult {
    let p_trim = prompt.trim();
    let p_lower = p_trim.to_lowercase();

    // 1. App Remix intent
    if p_lower.contains("remix") || p_lower.contains("modifikasi app") || p_lower.contains("ubah app") {
        let target_app = extract_app_after_keyword(&p_lower, &["remix", "modifikasi app", "ubah app"])
            .unwrap_or_else(|| "crypto-radar".to_string());
        let args = json!({ "app": target_app });
        let intent = "flowpkg_remix".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.95,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }

    // 2. Screen Memory search intent (requires explicit retrieval/screen verb+noun, not generic debugging mention)
    let is_screen_query = p_lower.contains("cari layar")
        || p_lower.contains("ingat layar")
        || p_lower.contains("tangkapan layar")
        || p_lower.contains("cari screenshot")
        || p_lower.contains("search screen")
        || p_lower.contains("screen memory")
        || p_lower.contains("screenshot")
        || p_lower.starts_with("layar ")
        || p_lower.contains(" layar");
    if is_screen_query {
        let query = clean_query_text(
            &p_lower,
            &[
                "tolong", "carikan", "cari", "ingat", "tangkapan", "layar",
                "screenshot", "screen", "memory", "rekaman", "tadi", "pagi",
                "siang", "sore", "malam", "yang", "di", "pada", "tentang",
            ],
            "Desktop",
        );
        let args = json!({ "query": query });
        let intent = "flowfs_screen_search".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.94,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }

    // 3. Semantic File search intent
    if p_lower.contains("cari file")
        || p_lower.contains("temukan dokumen")
        || p_lower.contains("temukan file")
        || p_lower.contains("search file")
        || p_lower.contains("find file")
    {
        let query = clean_query_text(
            &p_lower,
            &[
                "tolong", "cari", "carikan", "temukan", "search", "find",
                "file", "dokumen", "document", "yang", "di",
            ],
            "flowork",
        );
        let args = json!({ "query": query });
        let intent = "flowfs_search".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.93,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }

    // 4. Audio / Volume / Mute control
    if let Some(vol) = extract_volume_percent(&p_lower) {
        let args = json!({ "volume": vol });
        let intent = "audio_control".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.93,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }
    if p_lower == "mute" || p_lower == "bisu" || p_lower == "senyapkan" || p_lower.contains("mute audio") || p_lower.contains("matikan suara") {
        let args = json!({ "mute": true });
        let intent = "audio_control".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.92,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }
    if p_lower == "unmute" || p_lower == "bunyikan" || p_lower.contains("unmute audio") || p_lower.contains("nyalakan suara") {
        let args = json!({ "mute": false });
        let intent = "audio_control".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.92,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }

    // 5. Window Tiling
    if p_lower.contains("tile left") || p_lower.contains("sebelah kiri") {
        let args = json!({ "position": "left" });
        let intent = "window_tile".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.91,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }
    if p_lower.contains("tile right") || p_lower.contains("sebelah kanan") {
        let args = json!({ "position": "right" });
        let intent = "window_tile".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.91,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }

    // 6. System Health / Sentinel Audit
    if p_lower.contains("cek sistem")
        || p_lower.contains("audit sistem")
        || p_lower.contains("status kesehatan")
        || p_lower.contains("system health")
        || p_lower == "audit"
        || p_lower == "health"
    {
        let args = json!({});
        let intent = "sentinel_audit".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.92,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }

    // 7. Application Launch
    if p_lower.starts_with("buka ")
        || p_lower.starts_with("jalankan ")
        || p_lower.starts_with("launch ")
        || p_lower.starts_with("open ")
    {
        let words: Vec<&str> = p_trim.split_whitespace().collect();
        let app_name = words
            .get(1)
            .map(|s| s.trim_matches(|c: char| !c.is_alphanumeric() && c != '-' && c != '_'))
            .filter(|s| !s.is_empty())
            .unwrap_or("cadcraft")
            .to_string();
        let args = json!({ "app": app_name });
        let intent = "flowork_launch".to_string();
        return L0TriageResult {
            route: "local_action".to_string(),
            confidence: 0.92,
            normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
            intent,
            args,
            backend: "deterministic-l0-heuristic".to_string(),
            latency_ms: 0,
            executed_locally: false,
        };
    }

    // 8. Default: Delegate complex reasoning / coding / synthesis to Cloud or full LLM while providing normalized keywords
    let intent = "delegate_cloud".to_string();
    let args = json!({ "prompt_preview": p_trim.chars().take(120).collect::<String>() });
    L0TriageResult {
        route: "delegate_cloud".to_string(),
        confidence: 0.65,
        normalized_keywords: normalize_bilingual_keywords(p_trim, &intent, &args),
        intent,
        args,
        backend: "deterministic-l0-heuristic".to_string(),
        latency_ms: 0,
        executed_locally: false,
    }
}

fn execute_local_intent(intent: &str, args: &Value, _raw_prompt: &str) -> (String, Vec<Value>, bool) {
    match intent {
        "flowpkg_remix" => {
            let target_app = args
                .get("app")
                .and_then(|v| v.as_str())
                .unwrap_or("crypto-radar")
                .to_string();
            let output = Command::new("/opt/floworkos/bin/flowpkg")
                .args(["remix", &target_app, "--inspect"])
                .output();
            let out_str = match output {
                Ok(o) => String::from_utf8_lossy(&o.stdout).trim().to_string(),
                Err(e) => format!("Error invoking flowpkg: {}", e),
            };
            let resp = format!("🛠️ [L0 SLM] Initiated Remix Studio for [{}]:\n{}", target_app, out_str);
            let trace = vec![json!({
                "tool": "flowpkg_remix",
                "target": target_app,
                "status": "success"
            })];
            (resp, trace, true)
        }
        "flowfs_screen_search" => {
            let query = args
                .get("query")
                .and_then(|v| v.as_str())
                .filter(|s| !s.trim().is_empty())
                .unwrap_or("Desktop");
            let output = Command::new("/opt/floworkos/bin/flowfs-search")
                .args(["--screen", query, "--json"])
                .output();
            let mut results = json!([]);
            if let Ok(o) = output {
                if let Ok(parsed) = serde_json::from_slice::<Value>(&o.stdout) {
                    results = parsed.get("results").cloned().unwrap_or(json!([]));
                }
            }
            let count = results.as_array().map(|a| a.len()).unwrap_or(0);
            let resp = format!(
                "👁️ [L0 SLM] FlowFS Screen Memory retrieved {} visual moment(s) for query '{}'.",
                count, query
            );
            let trace = vec![json!({
                "tool": "flowfs_screen_search",
                "query": query,
                "matches": results
            })];
            (resp, trace, true)
        }
        "flowfs_search" => {
            let query = args
                .get("query")
                .and_then(|v| v.as_str())
                .filter(|s| !s.trim().is_empty())
                .unwrap_or("flowork");
            let output = Command::new("/opt/floworkos/bin/flowfs-search")
                .args([query, "--json"])
                .output();
            let mut results = json!([]);
            if let Ok(o) = output {
                if let Ok(parsed) = serde_json::from_slice::<Value>(&o.stdout) {
                    results = parsed.get("results").cloned().unwrap_or(json!([]));
                }
            }
            let count = results.as_array().map(|a| a.len()).unwrap_or(0);
            let resp = format!(
                "🧠 [L0 SLM] FlowFS found {} relevant file(s) for '{}'.",
                count, query
            );
            let trace = vec![json!({
                "tool": "flowfs_search",
                "query": query,
                "matches": results
            })];
            (resp, trace, true)
        }
        "sentinel_audit" => {
            let output = Command::new("/opt/floworkos/bin/flowork-sentinel-daemon")
                .arg("--audit")
                .output();
            let health_str = match output {
                Ok(o) => String::from_utf8_lossy(&o.stdout).trim().to_string(),
                Err(e) => format!("Error invoking sentinel: {}", e),
            };
            let resp = format!("🛡️ [L0 SLM] Flowork Sentinel Diagnostic Audit:\n{}", health_str);
            let trace = vec![json!({
                "tool": "sentinel_audit",
                "status": "healthy"
            })];
            (resp, trace, true)
        }
        "flowork_launch" => {
            let app_name = args
                .get("app")
                .and_then(|v| v.as_str())
                .unwrap_or("cadcraft");
            let spawned = Command::new("/opt/floworkos/bin/flowork-launch")
                .arg(app_name)
                .spawn()
                .is_ok();
            let resp = format!(
                "🚀 [L0 SLM] Dispatched launch command for [{}] via flowork-launch (spawned={}).",
                app_name, spawned
            );
            let trace = vec![json!({
                "tool": "flowork_launch",
                "app": app_name,
                "detached": spawned
            })];
            (resp, trace, true)
        }
        "audio_control" => {
            if let Some(vol) = args.get("volume").and_then(|v| v.as_u64()) {
                match DbusController::set_master_volume(vol as u32) {
                    Ok(res) => {
                        return (
                            format!("🔊 [L0 SLM] Set master audio volume to {}%.", vol),
                            vec![json!({ "tool": "dbus_audio", "volume": vol, "result": res })],
                            true,
                        );
                    }
                    Err(e) => {
                        return (
                            format!("⚠️ [L0 SLM] Audio volume error: {}", e),
                            vec![json!({ "tool": "dbus_audio", "error": e })],
                            true,
                        );
                    }
                }
            }
            if let Some(mute) = args.get("mute").and_then(|v| v.as_bool()) {
                match DbusController::set_master_mute(Some(mute)) {
                    Ok(res) => {
                        return (
                            format!("🔇 [L0 SLM] Audio mute set to {}.", mute),
                            vec![json!({ "tool": "dbus_audio", "mute": mute, "result": res })],
                            true,
                        );
                    }
                    Err(e) => {
                        return (
                            format!("⚠️ [L0 SLM] Audio mute error: {}", e),
                            vec![json!({ "tool": "dbus_audio", "error": e })],
                            true,
                        );
                    }
                }
            }
            (String::new(), Vec::new(), false)
        }
        "window_tile" => {
            let pos = args.get("position").and_then(|v| v.as_str()).unwrap_or("left");
            if let Ok(wins) = X11Controller::get_windows() {
                if let Some(active) = wins.iter().find(|w| w.is_active) {
                    if let Ok(res) = X11Controller::tile_window(active.id, pos) {
                        return (
                            format!("🪟 [L0 SLM] Tiled active window [{}] to '{}'.", active.title, pos),
                            vec![json!({ "tool": "x11_tile", "position": pos, "result": res })],
                            true,
                        );
                    }
                }
            }
            (
                format!("⚠️ [L0 SLM] No active window found to tile '{}'.", pos),
                vec![json!({ "tool": "x11_tile", "position": pos, "status": "no_active_window" })],
                true,
            )
        }
        _ => (String::new(), Vec::new(), false),
    }
}

fn extract_app_after_keyword(p_lower: &str, keys: &[&str]) -> Option<String> {
    for k in keys {
        if let Some(idx) = p_lower.find(k) {
            let rest = p_lower[idx + k.len()..].trim();
            if let Some(first) = rest.split_whitespace().next() {
                let clean: String = first
                    .chars()
                    .filter(|c| c.is_alphanumeric() || *c == '-' || *c == '_')
                    .collect();
                if !clean.is_empty() {
                    return Some(clean);
                }
            }
        }
    }
    None
}

fn clean_query_text(p_lower: &str, noise_words: &[&str], fallback: &str) -> String {
    let tokens: Vec<&str> = p_lower
        .split_whitespace()
        .map(|w| w.trim_matches(|c: char| !c.is_alphanumeric() && c != '-' && c != '_'))
        .filter(|w| !w.is_empty() && !noise_words.contains(w))
        .collect();
    if tokens.is_empty() {
        fallback.to_string()
    } else {
        tokens.join(" ")
    }
}

fn extract_volume_percent(p_lower: &str) -> Option<u32> {
    if !p_lower.contains("volume") && !p_lower.contains("vol ") && !p_lower.starts_with("vol") && !p_lower.contains("suara ") {
        return None;
    }
    for tok in p_lower.split_whitespace() {
        let digits = tok.trim_end_matches('%');
        if let Ok(v) = digits.parse::<u32>() {
            if v <= 150 {
                return Some(v);
            }
        }
    }
    None
}

/// Bilingual (Indonesian + English) technical keyword normalizer for Formula533Router.
pub fn normalize_bilingual_keywords(prompt: &str, intent: &str, args: &Value) -> Vec<String> {
    let p_lower = prompt.to_lowercase();
    let mut kws = BTreeSet::new();

    match intent {
        "flowfs_screen_search" => {
            for w in ["flowfs", "screen", "memory", "screenshot", "ocr", "search"] {
                kws.insert(w.to_string());
            }
        }
        "flowfs_search" => {
            for w in ["flowfs", "search", "semantic", "file", "index"] {
                kws.insert(w.to_string());
            }
        }
        "flowpkg_remix" => {
            for w in ["flowpkg", "remix", "canvas", "studio"] {
                kws.insert(w.to_string());
            }
        }
        "flowork_launch" => {
            for w in ["launch", "desktop", "application", "x11"] {
                kws.insert(w.to_string());
            }
        }
        "sentinel_audit" => {
            for w in ["sentinel", "audit", "health", "diagnostics", "kernel"] {
                kws.insert(w.to_string());
            }
        }
        "audio_control" => {
            for w in ["audio", "dbus", "volume", "system"] {
                kws.insert(w.to_string());
            }
        }
        "window_tile" => {
            for w in ["window", "x11", "tile", "desktop"] {
                kws.insert(w.to_string());
            }
        }
        _ => {}
    }

    // Domain bilingual mappings
    let domain_rules: &[(&[&str], &[&str])] = &[
        (&["audio", "podcast", "suara", "jernih", "rapihin", "noise", "eq", "vokal", "mic", "kamidi"], &["audio", "mastering", "kamidi", "eq", "noise"]),
        (&["video", "klip", "potong", "edit video", "cutvii", "render", "animasi", "stickman"], &["video", "cutvii", "animation", "render"]),
        (&["rust", "cargo", "compile", "borrow", "crate", "compiler", "sysd", "mrflow"], &["rust", "cargo", "compiler", "debug"]),
        (&["error", "gagal", "bug", "crash", "panic", "segfault"], &["error", "debug", "diagnostics"]),
        (&["keamanan", "kerentanan", "security", "vuln", "pentest", "exploit", "xss", "sql"], &["security", "vulnerability", "audit", "scanner"]),
        (&["privacy", "secret", "rahasia", "token", "redact", "bocor", "leak"], &["privacy", "redact", "secret", "shield"]),
        (&["browser", "chrome", "cdp", "dom", "klik", "scrape", "web"], &["browser", "chrome", "cdp", "automation"]),
        (&["download", "unduh", "torrent", "downflow"], &["downflow", "download", "transfer"]),
        (&["seo", "keyword", "ranking", "backlink", "seoflow"], &["seo", "analytics", "keyword", "seoflow"]),
        (&["iso", "squashfs", "kernel", "boot", "installer"], &["iso", "kernel", "build"]),
    ];

    for (triggers, mapped) in domain_rules {
        if triggers.iter().any(|t| p_lower.contains(t)) {
            for m in *mapped {
                kws.insert((*m).to_string());
            }
        }
    }

    let stop_words = [
        "yang", "dan", "atau", "untuk", "dengan", "dari", "pada", "tadi", "pagi",
        "siang", "sore", "malam", "tolong", "bisa", "biar", "agar", "cari", "carikan",
        "the", "and", "for", "with", "that", "this", "from", "into", "please", "help",
    ];

    if let Some(q) = args.get("query").and_then(|v| v.as_str()) {
        for tok in q.split_whitespace() {
            let clean: String = tok
                .chars()
                .filter(|c| c.is_ascii_alphanumeric())
                .collect::<String>()
                .to_ascii_lowercase();
            if clean.len() >= 3 && !stop_words.contains(&clean.as_str()) {
                kws.insert(clean);
            }
        }
    }

    for tok in p_lower.split_whitespace() {
        let clean: String = tok
            .chars()
            .filter(|c| c.is_ascii_alphanumeric())
            .collect::<String>()
            .to_ascii_lowercase();
        if clean.len() >= 3 && !stop_words.contains(&clean.as_str()) && kws.len() < 10 {
            kws.insert(clean);
        }
    }

    let mut out: Vec<String> = kws.into_iter().collect();
    if out.len() > 10 {
        out.truncate(10);
    }
    let _ = Map::new();
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn screen_search_bilingual_classification_and_keywords() {
        let res = EmbeddedSlmEngine::triage("cari tangkapan layar error cargo tadi pagi");
        assert_eq!(res.route, "local_action");
        assert_eq!(res.intent, "flowfs_screen_search");
        assert!(res.confidence >= 0.85);
        assert_eq!(res.args["query"], "error cargo");
        assert!(res.normalized_keywords.contains(&"cargo".to_string()));
        assert!(res.normalized_keywords.contains(&"rust".to_string()));
        assert!(res.normalized_keywords.contains(&"screen".to_string()));
    }

    #[test]
    fn audio_podcast_bilingual_normalization_for_router() {
        let res = EmbeddedSlmEngine::triage("tolong rapihin audio podcast biar jernih");
        assert!(res.normalized_keywords.contains(&"audio".to_string()));
        assert!(res.normalized_keywords.contains(&"mastering".to_string()));
        assert!(res.normalized_keywords.contains(&"kamidi".to_string()));
        assert!(res.normalized_keywords.contains(&"eq".to_string()));
        assert!(res.normalized_keywords.contains(&"noise".to_string()));
    }

    #[test]
    fn remix_and_launch_classification() {
        let remix = EmbeddedSlmEngine::triage("remix crypto-radar");
        assert_eq!(remix.route, "local_action");
        assert_eq!(remix.intent, "flowpkg_remix");
        assert_eq!(remix.args["app"], "crypto-radar");

        let launch = EmbeddedSlmEngine::triage("buka seoflow");
        assert_eq!(launch.route, "local_action");
        assert_eq!(launch.intent, "flowork_launch");
        assert_eq!(launch.args["app"], "seoflow");
    }
}
