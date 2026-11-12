use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashSet;
use std::fs;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

pub const STATE_FILE: &str = "/tmp/flowork_lifecycle_state.json";
pub const CURRENT_PROMPT_FILE: &str = "/tmp/flowork_current_prompt.txt";
pub const ACTIVE_TRIGGER_FILE: &str = "/tmp/flowork_active_trigger.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct LastTurn {
    #[serde(default)]
    pub user_text: String,
    #[serde(default = "default_domain")]
    pub domain: String,
    #[serde(default)]
    pub is_short_response: bool,
    #[serde(default)]
    pub timestamp: u64,
}

fn default_domain() -> String {
    "general".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct ResourceState {
    #[serde(default)]
    pub browser_open_pages: u64,
    #[serde(default)]
    pub last_browser_activity: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct LifecycleState {
    #[serde(default)]
    pub last_turn: LastTurn,
    #[serde(default)]
    pub active_goal: Option<String>,
    #[serde(default)]
    pub active_reason: Option<String>,
    #[serde(default)]
    pub active_keywords: Vec<String>,
    #[serde(default)]
    pub active_tools: Vec<String>,
    #[serde(default)]
    pub active_skills: Vec<String>,
    #[serde(default)]
    pub active_prompts: Vec<String>,
    #[serde(default)]
    pub resource_state: ResourceState,
}

#[derive(Debug, Clone, Default)]
pub struct SniffedContext {
    pub text: String,
    pub domains: Vec<String>,
    pub extensions: Vec<String>,
    pub files: Vec<String>,
    pub cwd: String,
}

pub fn now_millis() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis() as u64)
        .unwrap_or(0)
}

pub fn load_state() -> LifecycleState {
    if let Ok(raw) = fs::read_to_string(STATE_FILE) {
        if let Ok(parsed) = serde_json::from_str::<LifecycleState>(&raw) {
            return parsed;
        }
    }
    LifecycleState {
        last_turn: LastTurn {
            domain: "general".to_string(),
            ..Default::default()
        },
        ..Default::default()
    }
}

pub fn save_state(state: &LifecycleState) {
    if let Ok(raw) = serde_json::to_string_pretty(state) {
        let nanos = now_millis();
        let pid = std::process::id();
        let tmp_path = format!("{}.{}.{}.tmp", STATE_FILE, pid, nanos);
        if fs::write(&tmp_path, raw).is_ok() {
            if fs::rename(&tmp_path, STATE_FILE).is_err() {
                let _ = fs::remove_file(&tmp_path);
            }
        }
    }
}

pub fn is_browser_state_open(state: &LifecycleState) -> bool {
    let pages = state.resource_state.browser_open_pages;
    let last_active = state.resource_state.last_browser_activity;
    let now = now_millis();
    pages > 0 && now.saturating_sub(last_active) < 1_800_000
}

pub fn on_tool_executed(tool_name: &str, params: &Value) {
    if tool_name.is_empty() {
        return;
    }
    let mut state = load_state();
    if tool_name.starts_with("browser_") || tool_name.starts_with("mcp_browser_") {
        if tool_name.contains("new_page") {
            state.resource_state.browser_open_pages =
                state.resource_state.browser_open_pages.saturating_add(1).max(1);
        } else if tool_name.contains("close_page") {
            state.resource_state.browser_open_pages =
                state.resource_state.browser_open_pages.saturating_sub(1);
        } else {
            state.resource_state.browser_open_pages =
                state.resource_state.browser_open_pages.max(1);
        }
        state.resource_state.last_browser_activity = now_millis();
    }

    if !state.active_tools.iter().any(|t| t == tool_name) {
        state.active_tools.push(tool_name.to_string());
    }
    if let Some(reason) = params.get("reason").and_then(|v| v.as_str()) {
        state.active_reason = Some(reason.to_string());
    }
    if let Some(goal) = params.get("goal").and_then(|v| v.as_str()) {
        state.active_goal = Some(goal.to_string());
    }
    if let Some(arr) = params.get("keywords").and_then(|v| v.as_array()) {
        let kws: Vec<String> = arr
            .iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect();
        if !kws.is_empty() {
            state.active_keywords = kws;
        }
    }

    save_state(&state);

    let trigger = json!({
        "goal": state.active_goal,
        "reason": state.active_reason,
        "keywords": state.active_keywords,
        "tool": tool_name,
        "timestamp": chrono::Utc::now().to_rfc3339(),
    });
    if let Ok(raw) = serde_json::to_string_pretty(&trigger) {
        let _ = fs::write(ACTIVE_TRIGGER_FILE, raw);
    }
}

pub fn sniff_context(cwd: &Path, override_prompt: Option<&str>) -> SniffedContext {
    let mut last_prompt = override_prompt.unwrap_or("").to_string();

    if last_prompt.is_empty() {
        if let Ok(raw) = fs::read_to_string(ACTIVE_TRIGGER_FILE) {
            if let Ok(trigger_data) = serde_json::from_str::<Value>(&raw) {
                let reason = trigger_data
                    .get("reason")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                if !reason.is_empty() {
                    let goal = trigger_data
                        .get("goal")
                        .and_then(|v| v.as_str())
                        .unwrap_or("");
                    let kws: Vec<&str> = trigger_data
                        .get("keywords")
                        .and_then(|v| v.as_array())
                        .map(|a| a.iter().filter_map(|x| x.as_str()).collect())
                        .unwrap_or_default();
                    last_prompt = format!("{} {} {}", goal, reason, kws.join(" "));
                }
            }
        }
    }

    if let Ok(current_prompt) = fs::read_to_string(CURRENT_PROMPT_FILE) {
        let trimmed = current_prompt.trim();
        if !trimmed.is_empty() {
            if last_prompt.is_empty() {
                last_prompt = trimmed.to_string();
            } else {
                last_prompt = format!("{} {}", trimmed, last_prompt);
            }
        }
    }

    let mut seen_domains = HashSet::new();
    let mut domains = Vec::new();

    if let Ok(url_re) = Regex::new(r"(?i)https?://([a-z0-9.-]+)") {
        for caps in url_re.captures_iter(&last_prompt) {
            if let Some(host) = caps.get(1) {
                let d = host.as_str().trim_end_matches('.').to_ascii_lowercase();
                if !d.is_empty() && seen_domains.insert(d.clone()) {
                    domains.push(d);
                }
            }
        }
    }

    if let Ok(plain_re) = Regex::new(r"(?i)\b([a-z0-9-]+(?:\.[a-z0-9-]+)+)\b") {
        for caps in plain_re.captures_iter(&last_prompt) {
            if let Some(m) = caps.get(1) {
                let d = m.as_str().to_ascii_lowercase();
                if d.contains('.') && !d.ends_with('.') && seen_domains.insert(d.clone()) {
                    domains.push(d);
                }
            }
        }
    }

    let mut exts_set = HashSet::new();
    let mut extensions = Vec::new();
    let mut files = Vec::new();

    if let Ok(entries) = fs::read_dir(cwd) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_file() {
                if let Some(name) = entry.file_name().to_str() {
                    files.push(name.to_string());
                    if let Some(ext) = Path::new(name).extension().and_then(|e| e.to_str()) {
                        let norm = format!(".{}", ext.to_ascii_lowercase());
                        if exts_set.insert(norm.clone()) {
                            extensions.push(norm);
                        }
                    }
                }
            }
        }
    }

    SniffedContext {
        text: last_prompt.to_ascii_lowercase(),
        domains,
        extensions,
        files,
        cwd: cwd.to_string_lossy().to_string(),
    }
}

pub fn is_tool_active(tool_name: &str, manifest: &Value, context: &SniffedContext, state: Option<&LifecycleState>) -> bool {
    if manifest.get("activation").and_then(|v| v.as_str()) == Some("always") {
        return true;
    }

    let triggers = manifest.get("triggers").cloned().unwrap_or_else(|| json!({}));
    let ctx_text = &context.text;

    if let Some(excludes) = triggers.get("exclude_keywords").and_then(|v| v.as_array()) {
        for ex in excludes {
            if let Some(raw) = ex.as_str() {
                let ex_lower = raw.trim().to_ascii_lowercase();
                if ex_lower.is_empty() {
                    continue;
                }
                if ctx_text.contains(&ex_lower) {
                    return false;
                }
                if context
                    .domains
                    .iter()
                    .any(|d| d == &ex_lower || d.ends_with(&format!(".{}", ex_lower)))
                {
                    return false;
                }
            }
        }
    }

    let owned_state;
    let st = match state {
        Some(s) => s,
        None => {
            owned_state = load_state();
            &owned_state
        }
    };

    if (tool_name.starts_with("browser_") || tool_name.starts_with("mcp_browser_"))
        && is_browser_state_open(st)
    {
        return true;
    }

    if st.last_turn.is_short_response {
        if st.active_tools.iter().any(|t| t == tool_name) {
            return true;
        }
        if st.last_turn.domain == "browser" && tool_name.starts_with("browser_") {
            return true;
        }
    }

    if let Some(keywords) = triggers.get("keywords").and_then(|v| v.as_array()) {
        for kw in keywords {
            if let Some(raw) = kw.as_str() {
                let kw_lower = raw.trim().to_ascii_lowercase();
                if kw_lower.is_empty() {
                    continue;
                }
                if ctx_text.contains(&kw_lower) {
                    return true;
                }
                if context
                    .domains
                    .iter()
                    .any(|d| d.contains(&kw_lower) || kw_lower.contains(d.as_str()))
                {
                    return true;
                }
            }
        }
    }

    let behavior = triggers.get("behavior").cloned().unwrap_or_else(|| json!({}));
    if let Some(file_exts) = behavior.get("file_extensions").and_then(|v| v.as_array()) {
        for ext in file_exts {
            if let Some(raw) = ext.as_str() {
                let lower = raw.trim().to_ascii_lowercase();
                let norm = if lower.starts_with('.') {
                    lower
                } else {
                    format!(".{}", lower)
                };
                if context.extensions.iter().any(|e| e == &norm) || ctx_text.contains(&norm) {
                    return true;
                }
            }
        }
    }

    if let Some(doms) = behavior.get("domains").and_then(|v| v.as_array()) {
        for dom in doms {
            if let Some(raw) = dom.as_str() {
                let dom_lower = raw.trim().to_ascii_lowercase();
                if dom_lower == "*" {
                    if !context.domains.is_empty()
                        || ctx_text.contains("http")
                        || ctx_text.contains("www.")
                    {
                        return true;
                    }
                    continue;
                }
                if context.domains.iter().any(|d| d.contains(&dom_lower))
                    || ctx_text.contains(&dom_lower)
                {
                    return true;
                }
            }
        }
    }

    if let Some(files) = behavior.get("files").and_then(|v| v.as_array()) {
        for f in files {
            if let Some(raw) = f.as_str() {
                let f_lower = raw.to_ascii_lowercase();
                if context.files.iter().any(|cf| cf == raw) || ctx_text.contains(&f_lower) {
                    return true;
                }
            }
        }
    }

    false
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn context_sniffer_rules_respect_exclude_veto_and_domains() {
        let test_tool = json!({
            "name": "flowork_web_search",
            "activation": "conditional",
            "triggers": {
                "keywords": ["search", "google", "web", "internet"],
                "exclude_keywords": ["offline", "localhost", "127.0.0.1"],
                "behavior": {
                    "domains": ["google.com", "bing.com"]
                }
            }
        });
        let empty_state = LifecycleState::default();
        let ctx1 = SniffedContext {
            text: "please search documentation online".to_string(),
            domains: vec!["google.com".to_string()],
            extensions: vec![],
            files: vec![],
            cwd: "/tmp".to_string(),
        };
        let ctx2 = SniffedContext {
            text: "run search on localhost server".to_string(),
            domains: vec!["localhost".to_string()],
            extensions: vec![],
            files: vec![],
            cwd: "/tmp".to_string(),
        };
        let ctx3 = SniffedContext {
            text: "edit this python script".to_string(),
            domains: vec![],
            extensions: vec![".py".to_string()],
            files: vec![],
            cwd: "/tmp".to_string(),
        };

        assert!(is_tool_active("flowork_web_search", &test_tool, &ctx1, Some(&empty_state)));
        assert!(!is_tool_active("flowork_web_search", &test_tool, &ctx2, Some(&empty_state)));
        assert!(!is_tool_active("flowork_web_search", &test_tool, &ctx3, Some(&empty_state)));
    }
}
