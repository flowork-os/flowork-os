use crate::config::AppConfig;
use regex::Regex;
use rusqlite::{params, Connection, OpenFlags};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::process::Command;
use tokio::time::timeout;

const STOP_WORDS: &[&str] = &[
    "the", "and", "for", "with", "from", "check", "status", "test", "routine", "saying", "just",
    "date", "time", "file", "path", "true", "false", "item", "name", "type", "open", "read",
    "view", "edit", "make", "help", "exec", "run", "command", "system", "code", "list",
    "show", "get", "set", "call", "step", "tool", "args", "data", "info", "find",
    "output", "result", "mode", "base", "rule", "task", "inspect", "debug", "directory",
    "dir", "line", "lines", "count", "string", "text", "clean", "fix", "update", "shell",
    "bash", "cargo", "json", "source", "target", "build", "process", "param", "params",
    "argument", "arguments", "content", "contents", "return", "returns", "value", "values",
    "history", "state", "session", "start", "stop", "action", "actions", "entry", "entries",
];

const LIFECYCLE_STATE_FILE: &str = "/tmp/flowork_lifecycle_state.json";
const ACTIVE_TRIGGER_FILE: &str = "/tmp/flowork_active_trigger.json";

#[derive(Debug, Clone)]
pub struct SkillMeta {
    pub name: String,
    pub description: String,
    pub domain: String,
    #[allow(dead_code)]
    pub keywords: Vec<String>,
    pub path: PathBuf,
    pub token_set: HashSet<String>,
}

#[derive(Debug, Clone)]
pub struct PromptTriggerMeta {
    #[allow(dead_code)]
    pub id: String,
    pub title: String,
    #[allow(dead_code)]
    pub path: PathBuf,
    pub content: String,
    pub keywords_text: String,
    pub token_set: HashSet<String>,
}

#[derive(Debug, Clone, Deserialize, Default)]
struct SystemRuleRegistryEntry {
    pub id: String,
    #[serde(default = "default_true")]
    pub enabled: bool,
    #[serde(default)]
    #[allow(dead_code)]
    pub scope: String,
    #[serde(default)]
    pub rule: String,
    #[serde(default)]
    pub prompt: String,
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
pub struct LifecycleResourceState {
    #[serde(default, rename = "browserOpenPages", alias = "browser_open_pages")]
    pub browser_open_pages: usize,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
pub struct LifecycleState {
    #[serde(default, alias = "turnCount", rename = "turnCount")]
    pub turn_count: usize,
    #[serde(default, alias = "last_turn", rename = "lastTurn")]
    pub last_turn: Option<Value>,
    #[serde(default, alias = "activeKeywords", rename = "activeKeywords")]
    pub active_keywords: Vec<String>,
    #[serde(default, alias = "activeTools", rename = "activeTools")]
    pub active_tools: Vec<String>,
    #[serde(default, alias = "browserActive")]
    pub browser_active: bool,
    #[serde(default, alias = "browserTurnsRemaining")]
    pub browser_turns_remaining: usize,
    #[serde(default, alias = "activeDomain", rename = "activeDomain")]
    pub active_domain: String,
    #[serde(default, alias = "resourceState", rename = "resourceState")]
    pub resource_state: LifecycleResourceState,
    #[serde(default, alias = "lastUpdated")]
    pub last_updated: u64,
}

#[derive(Debug, Clone)]
pub struct SniffedContext {
    #[allow(dead_code)]
    pub cwd: PathBuf,
    pub extensions: HashSet<String>,
    pub file_names: HashSet<String>,
    pub browser_active: bool,
    pub user_prompt_lower: String,
    pub active_keywords: HashSet<String>,
}

/// Lightweight deterministic suffix stemmer for English/Indonesian routing tokens.
pub fn stem_token(raw: &str) -> String {
    let mut w = raw.trim().to_ascii_lowercase();
    if w.len() < 4 {
        return w;
    }
    if w.ends_with("ations") && w.len() > 7 {
        w.truncate(w.len() - 6);
        w.push_str("ate");
    } else if w.ends_with("ities") && w.len() > 7 {
        w.truncate(w.len() - 5);
        w.push_str("ity");
    } else if w.ends_with("ments") && w.len() > 7 {
        w.truncate(w.len() - 1);
    } else if w.ends_with("ings") && w.len() > 6 {
        w.truncate(w.len() - 4);
    } else if w.ends_with("ing") && w.len() > 5 {
        w.truncate(w.len() - 3);
        let bytes = w.as_bytes();
        if bytes.len() >= 2 && bytes[bytes.len() - 1] == bytes[bytes.len() - 2] {
            let last = bytes[bytes.len() - 1];
            if last != b's' && last != b'l' {
                w.pop();
            }
        }
    } else if w.ends_with("ies") && w.len() > 5 {
        w.truncate(w.len() - 3);
        w.push('y');
    } else if (w.ends_with("ches") || w.ends_with("shes") || w.ends_with("xes") || w.ends_with("ses"))
        && w.len() > 5
    {
        w.truncate(w.len() - 2);
    } else if w.ends_with("ed") && w.len() > 4 {
        w.truncate(w.len() - 2);
        let bytes = w.as_bytes();
        if bytes.len() >= 2 && bytes[bytes.len() - 1] == bytes[bytes.len() - 2] {
            let last = bytes[bytes.len() - 1];
            if last != b's' && last != b'l' {
                w.pop();
            }
        }
    } else if w.ends_with("er") && w.len() > 5 {
        w.truncate(w.len() - 2);
    } else if w.ends_with('s') && !w.ends_with("ss") && !w.ends_with("us") && w.len() > 3 {
        w.pop();
    }
    w
}

pub fn tokenize_set(text: &str) -> HashSet<String> {
    let stop: HashSet<&str> = STOP_WORDS.iter().copied().collect();
    let mut out = HashSet::new();
    for raw in text
        .to_ascii_lowercase()
        .split(|c: char| !(c.is_ascii_alphanumeric() || c == '_' || c == '-'))
    {
        if raw.len() < 3 || stop.contains(raw) {
            continue;
        }
        out.insert(raw.to_string());
        let stemmed = stem_token(raw);
        if stemmed.len() >= 3 && !stop.contains(stemmed.as_str()) {
            out.insert(stemmed);
        }
        if raw.contains('_') || raw.contains('-') {
            for part in raw.split(|c| c == '_' || c == '-') {
                if part.len() >= 3 && !stop.contains(part) {
                    out.insert(part.to_string());
                    let ps = stem_token(part);
                    if ps.len() >= 3 && !stop.contains(ps.as_str()) {
                        out.insert(ps);
                    }
                }
            }
        }
    }
    out
}

pub fn discover_skills(config: &AppConfig) -> Vec<SkillMeta> {
    let mut skills = Vec::new();
    let mut seen_names = HashSet::new();
    let disabled: HashSet<String> = config
        .settings
        .disabled_skills
        .iter()
        .map(|s| s.to_ascii_lowercase())
        .collect();

    for dir in &config.paths.skills_dirs {
        let Ok(entries) = fs::read_dir(dir) else {
            continue;
        };
        for entry in entries.flatten() {
            let p = entry.path();
            if !p.is_dir() {
                continue;
            }
            let skill_md = p.join("SKILL.md");
            if !skill_md.is_file() {
                continue;
            }
            let Ok(raw) = fs::read_to_string(&skill_md) else {
                continue;
            };
            let dir_name = p
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("")
                .to_string();
            let (fm_name, desc, domain, kws) = parse_skill_frontmatter(&raw);
            let name = if fm_name.is_empty() {
                dir_name
            } else {
                fm_name
            };
            if name.is_empty()
                || disabled.contains(&name.to_ascii_lowercase())
                || !seen_names.insert(name.clone())
            {
                continue;
            }
            let token_set = tokenize_set(&format!("{} {}", name, kws.join(" ")));
            skills.push(SkillMeta {
                name,
                description: desc,
                domain,
                keywords: kws,
                path: skill_md,
                token_set,
            });
        }
    }
    skills.sort_by(|a, b| a.name.cmp(&b.name));
    skills
}

fn parse_skill_frontmatter(raw: &str) -> (String, String, String, Vec<String>) {
    let Some(stripped) = raw.strip_prefix("---") else {
        return (String::new(), String::new(), String::new(), Vec::new());
    };
    let Some(end_idx) = stripped.find("\n---") else {
        return (String::new(), String::new(), String::new(), Vec::new());
    };
    let yaml = &stripped[..end_idx];
    let mut name = String::new();
    let mut desc = String::new();
    let mut domain = String::new();
    let mut keywords = Vec::new();
    let mut in_keywords = false;

    for line in yaml.lines() {
        let t = line.trim();
        if t.is_empty() || t.starts_with('#') {
            continue;
        }
        if t.starts_with("- ") && in_keywords {
            let item = t[2..].trim().trim_matches('"').trim_matches('\'').to_string();
            if !item.is_empty() {
                keywords.push(item);
            }
            continue;
        }
        if let Some((k, v)) = t.split_once(':') {
            let key = k.trim();
            let val = v.trim();
            in_keywords = false;
            match key {
                "name" => name = val.trim_matches('"').trim_matches('\'').to_string(),
                "description" => desc = val.trim_matches('"').trim_matches('\'').to_string(),
                "domain" => domain = val.trim_matches('"').trim_matches('\'').to_string(),
                "keywords" => {
                    if val.starts_with('[') && val.ends_with(']') {
                        for part in val[1..val.len() - 1].split(',') {
                            let clean = part.trim().trim_matches('"').trim_matches('\'').to_string();
                            if !clean.is_empty() {
                                keywords.push(clean);
                            }
                        }
                    } else if val.is_empty() {
                        in_keywords = true;
                    }
                }
                _ => {}
            }
        }
    }
    (name, desc, domain, keywords)
}

pub fn load_lifecycle_state() -> LifecycleState {
    if let Ok(raw) = fs::read_to_string(LIFECYCLE_STATE_FILE) {
        if let Ok(st) = serde_json::from_str::<LifecycleState>(&raw) {
            return st;
        }
    }
    LifecycleState::default()
}

pub fn save_lifecycle_state(state: &LifecycleState) {
    let mut st = state.clone();
    st.last_updated = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    if let Ok(json) = serde_json::to_string_pretty(&st) {
        let tmp_path = format!("{}.{}.tmp", LIFECYCLE_STATE_FILE, std::process::id());
        if fs::write(&tmp_path, &json).is_ok() {
            if fs::rename(&tmp_path, LIFECYCLE_STATE_FILE).is_err() {
                let _ = fs::remove_file(&tmp_path);
            }
        }
    }
}

pub fn sniff_context(config: &AppConfig, user_prompt: &str) -> SniffedContext {
    let mut extensions = HashSet::new();
    let mut file_names = HashSet::new();
    if let Ok(entries) = fs::read_dir(&config.cwd) {
        for e in entries.flatten().take(250) {
            let p = e.path();
            if let Some(name) = p.file_name().and_then(|s| s.to_str()) {
                file_names.insert(name.to_ascii_lowercase());
            }
            if let Some(ext) = p.extension().and_then(|s| s.to_str()) {
                extensions.insert(format!(".{}", ext.to_ascii_lowercase()));
            }
        }
    }
    let _ = fs::write("/tmp/flowork_current_prompt.txt", user_prompt);

    let state = load_lifecycle_state();
    let lower_prompt = user_prompt.to_ascii_lowercase();
    let word_count = lower_prompt.split_whitespace().count();

    let mut active_keywords = tokenize_set(&lower_prompt);
    // Option C: short response carryover (<= 4 words) preserves previous turn context
    if word_count <= 4 {
        for kw in &state.active_keywords {
            active_keywords.insert(kw.to_ascii_lowercase());
        }
    }

    // Inject active watchdog trigger keywords if fresh
    if let Ok(raw_trig) = fs::read_to_string(ACTIVE_TRIGGER_FILE) {
        let now_secs = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs() as i64)
            .unwrap_or(0);
        if let Ok(v) = serde_json::from_str::<Value>(&raw_trig) {
            let active = v.get("active").and_then(|b| b.as_bool()).unwrap_or(false);
            let fresh = parse_trigger_timestamp_secs(&v)
                .map(|ts| now_secs.saturating_sub(ts) <= ACTIVE_TRIGGER_TTL_SECS)
                .unwrap_or(false);
            if active && fresh {
                if let Some(kws) = v.get("keywords").and_then(|a| a.as_array()) {
                    for k in kws {
                        if let Some(s) = k.as_str() {
                            active_keywords.insert(s.to_ascii_lowercase());
                        }
                    }
                }
            }
        }
    }

    let browser_words = ["browser", "chrome", "webpage", "dom", "click", "url", "http://", "https://", "screenshot"];
    let prompt_mentions_browser = browser_words.iter().any(|w| lower_prompt.contains(w));
    let browser_active = state.browser_active
        || state.browser_turns_remaining > 0
        || state.resource_state.browser_open_pages > 0
        || prompt_mentions_browser;

    SniffedContext {
        cwd: config.cwd.clone(),
        extensions,
        file_names,
        browser_active,
        user_prompt_lower: lower_prompt,
        active_keywords,
    }
}

/// Evaluates whether a tool manifest in /opt/floworkos/tools/*/manifest.json (and ~/.flowork/tools) should be active.
/// Supports both structured `triggers: { keywords, exclude_keywords, behavior }` and flat `keywords` / `exclude_keywords` schemas.
pub fn is_manifest_tool_active(manifest: &Value, ctx: &SniffedContext) -> bool {
    let name = manifest.get("name").and_then(|s| s.as_str()).unwrap_or("");
    let activation = manifest
        .get("activation")
        .and_then(|s| s.as_str())
        .unwrap_or("conditional");

    // Check exclude_keywords in both `triggers.exclude_keywords` and top-level `exclude_keywords`
    for excl_arr in [
        manifest
            .get("triggers")
            .and_then(|t| t.get("exclude_keywords"))
            .and_then(|a| a.as_array()),
        manifest.get("exclude_keywords").and_then(|a| a.as_array()),
    ]
    .into_iter()
    .flatten()
    {
        for ek in excl_arr {
            if let Some(s) = ek.as_str() {
                if !s.is_empty() && ctx.user_prompt_lower.contains(&s.to_ascii_lowercase()) {
                    return false;
                }
            }
        }
    }

    if activation == "always" {
        return true;
    }

    if name.starts_with("browser_") && ctx.browser_active {
        return true;
    }

    if let Some(exts) = manifest
        .get("triggers")
        .and_then(|t| t.get("behavior"))
        .and_then(|b| b.get("file_extensions"))
        .and_then(|a| a.as_array())
    {
        for ext in exts {
            if let Some(e) = ext.as_str() {
                let norm = if e.starts_with('.') {
                    e.to_ascii_lowercase()
                } else {
                    format!(".{}", e.to_ascii_lowercase())
                };
                if ctx.extensions.contains(&norm) {
                    return true;
                }
            }
        }
    }

    if let Some(files) = manifest
        .get("triggers")
        .and_then(|t| t.get("behavior"))
        .and_then(|b| b.get("files"))
        .and_then(|a| a.as_array())
    {
        for f in files {
            if let Some(fname) = f.as_str() {
                if ctx.file_names.contains(&fname.to_ascii_lowercase()) {
                    return true;
                }
            }
        }
    }

    // Check keywords in both `triggers.keywords` and top-level `keywords` (e.g., similarweb)
    for kw_arr in [
        manifest
            .get("triggers")
            .and_then(|t| t.get("keywords"))
            .and_then(|a| a.as_array()),
        manifest.get("keywords").and_then(|a| a.as_array()),
    ]
    .into_iter()
    .flatten()
    {
        for kw in kw_arr {
            if let Some(k) = kw.as_str() {
                let kl = k.to_ascii_lowercase();
                if !kl.is_empty()
                    && (ctx.user_prompt_lower.contains(&kl) || ctx.active_keywords.contains(&kl))
                {
                    return true;
                }
            }
        }
    }

    false
}

/// Evaluation state for external `prompts_dir/triggers.json` DSL conditions.
struct TriggerEvalContext<'a> {
    config: &'a AppConfig,
    enabled_tool_names: &'a HashSet<String>,
    skills: &'a [SkillMeta],
    has_subagents: bool,
    is_git_repo: bool,
    user_message_lower: String,
    active_keywords: HashSet<String>,
    cwd_entries: Vec<String>,
}

fn split_top_level_op<'a>(expr: &'a str, op: &str) -> Vec<&'a str> {
    let mut parts = Vec::new();
    let bytes = expr.as_bytes();
    let op_bytes = op.as_bytes();
    let mut in_single = false;
    let mut in_double = false;
    let mut depth_paren = 0usize;
    let mut depth_bracket = 0usize;
    let mut last = 0usize;
    let mut i = 0usize;

    while i < bytes.len() {
        let b = bytes[i];
        if b == b'\\' && (in_single || in_double) {
            i += 2;
            continue;
        }
        if b == b'\'' && !in_double {
            in_single = !in_single;
            i += 1;
            continue;
        }
        if b == b'"' && !in_single {
            in_double = !in_double;
            i += 1;
            continue;
        }
        if !in_single && !in_double {
            match b {
                b'(' => depth_paren += 1,
                b')' => depth_paren = depth_paren.saturating_sub(1),
                b'[' => depth_bracket += 1,
                b']' => depth_bracket = depth_bracket.saturating_sub(1),
                _ => {}
            }
            if depth_paren == 0
                && depth_bracket == 0
                && i + op_bytes.len() <= bytes.len()
                && &bytes[i..i + op_bytes.len()] == op_bytes
            {
                parts.push(expr[last..i].trim());
                i += op_bytes.len();
                last = i;
                continue;
            }
        }
        i += 1;
    }
    parts.push(expr[last..].trim());
    parts
}

fn extract_quoted_list(inner: &str) -> Vec<String> {
    let quote_re = Regex::new(r#"["']([^"']+)["']"#).unwrap();
    quote_re
        .captures_iter(inner)
        .filter_map(|c| c.get(1).map(|m| m.as_str().to_string()))
        .collect()
}

fn glob_star_match(pattern_lower: &str, candidate_lower: &str) -> bool {
    if pattern_lower == "*" {
        return true;
    }
    if !pattern_lower.contains('*') {
        return candidate_lower == pattern_lower || candidate_lower.contains(pattern_lower);
    }
    let anchor_start = !pattern_lower.starts_with('*');
    let anchor_end = !pattern_lower.ends_with('*');
    let parts: Vec<&str> = pattern_lower.split('*').filter(|s| !s.is_empty()).collect();
    if parts.is_empty() {
        return true;
    }
    let mut pos = 0usize;
    for (idx, part) in parts.iter().enumerate() {
        if idx == 0 && anchor_start {
            if !candidate_lower.starts_with(part) {
                return false;
            }
            pos = part.len();
            continue;
        }
        if idx + 1 == parts.len() && anchor_end {
            return candidate_lower[pos..].ends_with(part);
        }
        if let Some(found) = candidate_lower[pos..].find(part) {
            pos += found + part.len();
        } else {
            return false;
        }
    }
    true
}

fn eval_trigger_condition(expr: &str, ctx: &TriggerEvalContext<'_>) -> bool {
    let trimmed = expr.trim();
    if trimmed.is_empty() {
        return false;
    }

    let or_branches = split_top_level_op(trimmed, "||");
    if or_branches.len() > 1 {
        return or_branches.into_iter().any(|b| eval_trigger_condition(b, ctx));
    }

    let and_branches = split_top_level_op(trimmed, "&&");
    if and_branches.len() > 1 {
        return and_branches.into_iter().all(|b| eval_trigger_condition(b, ctx));
    }

    if let Some(rest) = trimmed.strip_prefix('!') {
        if !rest.starts_with('=') {
            return !eval_trigger_condition(rest, ctx);
        }
    }

    if trimmed.starts_with('(') && trimmed.ends_with(')') && trimmed.len() >= 2 {
        return eval_trigger_condition(&trimmed[1..trimmed.len() - 1], ctx);
    }

    let eval_atom_str = |ident: &str| -> String {
        match ident.trim() {
            "approvalMode" => ctx.config.approval_mode.as_policy_mode().to_ascii_lowercase(),
            "sandboxMode" => {
                if ctx.config.sandbox {
                    "inside".to_string()
                } else {
                    "outside".to_string()
                }
            }
            "interactive" => ctx.config.interactive.to_string(),
            "isGitRepository(cwd)" => ctx.is_git_repo.to_string(),
            "isHookContextEnabled" => (ctx.user_message_lower.contains("<hook_context>")
                || std::env::var("FLOWORK_HOOK_CONTEXT").ok().as_deref() == Some("1"))
            .to_string(),
            other => other.trim_matches('\'').trim_matches('"').to_ascii_lowercase(),
        }
    };

    if let Some((lhs, rhs)) = trimmed.split_once("!==") {
        return eval_atom_str(lhs) != eval_atom_str(rhs);
    }
    if let Some((lhs, rhs)) = trimmed.split_once("===") {
        return eval_atom_str(lhs) == eval_atom_str(rhs);
    }

    match trimmed {
        "always" | "true" => return true,
        "false" => return false,
        "interactive" => return ctx.config.interactive,
        "hasAgentTool" => return ctx.enabled_tool_names.contains("invoke_agent"),
        "subagents.length > 0" => return ctx.has_subagents,
        "skills.length > 0" => return !ctx.skills.is_empty(),
        "isTrackerEnabled" => {
            return ctx.enabled_tool_names.contains("tracker_create_task")
                || ctx.config.cwd.join(".flowork/tracker").exists()
        }
        "isHookContextEnabled" => return ctx.user_message_lower.contains("<hook_context>"),
        _ => {}
    }

    if let Some(rest) = trimmed.strip_prefix("fs.existsSync(").and_then(|s| s.strip_suffix(')')) {
        let items = extract_quoted_list(rest);
        return items.into_iter().any(|rel| {
            let p = Path::new(&rel);
            if p.is_absolute() {
                p.exists()
            } else {
                ctx.config.cwd.join(p).exists()
            }
        });
    }

    if let Some(rest) = trimmed.strip_prefix("isToolEnabled(").and_then(|s| s.strip_suffix(')')) {
        return extract_quoted_list(rest)
            .into_iter()
            .any(|t| ctx.enabled_tool_names.contains(&t));
    }

    if let Some(rest) = trimmed.strip_prefix("hasKeywords(").and_then(|s| s.strip_suffix(')')) {
        return extract_quoted_list(rest).into_iter().any(|kw| {
            let kl = kw.to_ascii_lowercase();
            ctx.user_message_lower.contains(&kl) || ctx.active_keywords.contains(&kl)
        });
    }

    if let Some(rest) = trimmed.strip_prefix("promptContains(").and_then(|s| s.strip_suffix(')')) {
        return extract_quoted_list(rest)
            .into_iter()
            .any(|sub| ctx.user_message_lower.contains(&sub.to_ascii_lowercase()));
    }

    if let Some(rest) = trimmed.strip_prefix("workspaceContains(").and_then(|s| s.strip_suffix(')')) {
        let patterns = extract_quoted_list(rest);
        let cwd_lower = ctx.config.cwd.to_string_lossy().to_ascii_lowercase();
        return patterns.into_iter().any(|pat| {
            let pl = pat.to_ascii_lowercase();
            glob_star_match(&pl, &cwd_lower)
                || ctx.cwd_entries.iter().any(|entry| glob_star_match(&pl, entry))
        });
    }

    false
}

/// Native Rust port of engine.js: dynamically evaluates `prompts/triggers.json` DSL + parallel rules/.bin/* + watchdog.
#[allow(dead_code)]
pub async fn assemble_system_prompt(
    config: &AppConfig,
    enabled_tool_names: &HashSet<String>,
    skills: &[SkillMeta],
    user_message: &str,
    extra_memory: &str,
) -> String {
    assemble_system_prompt_with_jit(
        config,
        enabled_tool_names,
        skills,
        user_message,
        extra_memory,
        None,
    )
    .await
}

pub async fn assemble_system_prompt_with_jit(
    config: &AppConfig,
    enabled_tool_names: &HashSet<String>,
    skills: &[SkillMeta],
    user_message: &str,
    extra_memory: &str,
    episodic_jit: Option<&str>,
) -> String {
    let mut sections = Vec::new();
    let search_dirs = get_prompt_search_dirs(config);
    let mut loaded_files: HashSet<PathBuf> = HashSet::new();

    let resolve_prompt_file = |rel: &str| -> Option<(PathBuf, String)> {
        for dir in &search_dirs {
            let p = dir.join(rel);
            if let Ok(raw) = fs::read_to_string(&p) {
                let trimmed = raw.trim();
                if !trimmed.is_empty() {
                    let canon = fs::canonicalize(&p).unwrap_or(p);
                    return Some((canon, trimmed.to_string()));
                }
            }
        }
        None
    };

    // Build dynamic evaluation context for triggers.json DSL
    let has_subagents = config.paths.agents_dirs.iter().any(|d| {
        fs::read_dir(d)
            .map(|mut rd| rd.any(|_| true))
            .unwrap_or(false)
    });
    let mut cwd_entries = Vec::new();
    if let Ok(rd) = fs::read_dir(&config.cwd) {
        for e in rd.flatten().take(150) {
            if let Some(name) = e.file_name().to_str() {
                cwd_entries.push(name.to_ascii_lowercase());
            }
        }
    }
    let state = load_lifecycle_state();
    let lower_msg = user_message.to_ascii_lowercase();
    let mut active_kws = tokenize_set(&lower_msg);
    if lower_msg.split_whitespace().count() <= 4 {
        for kw in &state.active_keywords {
            active_kws.insert(kw.to_ascii_lowercase());
        }
    }

    let eval_ctx = TriggerEvalContext {
        config,
        enabled_tool_names,
        skills,
        has_subagents,
        is_git_repo: is_git_repo(&config.cwd),
        user_message_lower: lower_msg.clone(),
        active_keywords: active_kws,
        cwd_entries,
    };

    // Load prompts/triggers.json dynamically across search dirs
    let mut base_loaded = false;
    let mut passive_triggers = Vec::new();

    for dir in &search_dirs {
        let tpath = dir.join("triggers.json");
        let Ok(raw) = fs::read_to_string(&tpath) else {
            continue;
        };
        let Ok(tjson) = serde_json::from_str::<Value>(&raw) else {
            continue;
        };

        if let Some(base_arr) = tjson.get("base_prompts").and_then(|v| v.as_array()) {
            for item in base_arr {
                let cond = item.get("condition").and_then(|s| s.as_str()).unwrap_or("always");
                let Some(file_rel) = item.get("file").and_then(|s| s.as_str()) else {
                    continue;
                };
                if eval_trigger_condition(cond, &eval_ctx) {
                    if let Some((canon, content)) = resolve_prompt_file(file_rel) {
                        if loaded_files.insert(canon) {
                            sections.push(content);
                            base_loaded = true;
                        }
                    }
                }
            }
        }

        for arr_key in ["passive_triggers", "triggers"] {
            if let Some(arr) = tjson.get(arr_key).and_then(|v| v.as_array()) {
                for item in arr {
                    let cond = item.get("condition").and_then(|s| s.as_str()).unwrap_or("");
                    let Some(file_rel) = item.get("file").and_then(|s| s.as_str()) else {
                        continue;
                    };
                    if eval_trigger_condition(cond, &eval_ctx) {
                        if let Some((canon, content)) = resolve_prompt_file(file_rel) {
                            if loaded_files.insert(canon) {
                                passive_triggers.push(content);
                            }
                        }
                    }
                }
            }
        }
    }

    // Fallback base anchors if triggers.json had none
    if !base_loaded {
        for bf in &["00_preamble.md", "01_core_mandates.md", "02_operational_guidelines.md"] {
            if let Some((canon, content)) = resolve_prompt_file(bf) {
                if loaded_files.insert(canon) {
                    sections.push(content);
                }
            }
        }
    }

    // Structural engineering/search/memory triggers (deduplicated via loaded_files)
    let is_code_intent = lower_msg.contains("code")
        || lower_msg.contains("refactor")
        || lower_msg.contains("test")
        || lower_msg.contains("fix")
        || lower_msg.contains("bug")
        || lower_msg.contains("build")
        || lower_msg.contains("implement")
        || lower_msg.contains("buat")
        || lower_msg.contains("bikin")
        || lower_msg.contains("perbaiki")
        || lower_msg.contains("ubah")
        || lower_msg.contains("tulis")
        || lower_msg.contains("edit")
        || lower_msg.contains("patch");

    let is_search_intent = lower_msg.contains("search")
        || lower_msg.contains("grep")
        || lower_msg.contains("find")
        || lower_msg.contains("locate")
        || lower_msg.contains("cari")
        || lower_msg.contains("temukan");

    let structural_checks: Vec<(bool, &str)> = vec![
        (
            is_code_intent && (enabled_tool_names.contains("write_file") || enabled_tool_names.contains("replace")),
            "triggers/code_engineering.md",
        ),
        (
            is_search_intent
                && (enabled_tool_names.contains("grep_search")
                    || enabled_tool_names.contains("glob")
                    || enabled_tool_names.contains("read_many_files")),
            "triggers/search_efficiency.md",
        ),
        (
            config.cwd.join("FLOWORK.md").exists() || config.cwd.join(".flowork/MEMORY.md").exists(),
            "triggers/memory_routing.md",
        ),
        (
            enabled_tool_names.contains("list_mcp_resources")
                || enabled_tool_names.contains("read_mcp_resource"),
            "triggers/untrusted_context.md",
        ),
    ];
    for (cond, rel) in structural_checks {
        if cond {
            if let Some((canon, content)) = resolve_prompt_file(rel) {
                if loaded_files.insert(canon) {
                    passive_triggers.push(content);
                }
            }
        }
    }

    // Optional explicit FLOWORK_SYSTEM_MD override
    if let Some(ref sys_md) = config.paths.system_md_override {
        if sys_md.is_file() {
            if let Ok(raw) = fs::read_to_string(sys_md) {
                let trimmed = raw.trim();
                if !trimmed.is_empty() && !sections.iter().any(|s| s == trimmed) {
                    sections.push(trimmed.to_string());
                }
            }
        }
    }

    // Parallel compiled rules/.bin/* and interpreted .sh/.py/.js rules (<50ms each)
    let rule_injections = evaluate_compiled_rules(config, user_message).await;
    passive_triggers.extend(rule_injections);

    // Active watchdog alert (/tmp/flowork_active_trigger.json)
    if let Some(alert) = read_active_watchdog_trigger() {
        passive_triggers.push(alert);
    }

    if !passive_triggers.is_empty() {
        sections.push(format!(
            "\n---\n# ⚡ CONTEXTUAL PASSIVE & ACTIVE TRIGGERS INJECTED:\n\n{}",
            passive_triggers.join("\n\n")
        ));
    }

    // Hierarchical FLOWORK.md & .flowork/MEMORY.md
    if !extra_memory.trim().is_empty() {
        sections.push(format!(
            "# 🧠 WORKSPACE SOVEREIGN MEMORY (`FLOWORK.md`)\n\n{}",
            extra_memory.trim()
        ));
    }

    // Just-In-Time Zero-Bloat Episodic Memory Recall (SQLite FTS5)
    if let Some(ej) = episodic_jit {
        let trimmed = ej.trim();
        if !trimmed.is_empty() {
            sections.push(trimmed.to_string());
        }
    }

    if sections.is_empty() {
        sections.push(
            "# 👑 Flowork OS Sovereign AI Agent\nYou are Mr. Flow, the sovereign autonomous agent for Flowork OS."
                .to_string(),
        );
    }

    sections.join("\n\n---\n\n")
}

fn get_prompt_search_dirs(config: &AppConfig) -> Vec<PathBuf> {
    let mut dirs = Vec::new();
    if config.paths.prompts_dir.is_dir() {
        dirs.push(config.paths.prompts_dir.clone());
    }
    let user_p = config.paths.user_flowork_dir.join("prompts");
    if user_p.is_dir() && user_p != config.paths.prompts_dir {
        dirs.push(user_p);
    }
    dirs
}

fn is_git_repo(start: &Path) -> bool {
    let mut cur = Some(start);
    while let Some(d) = cur {
        if d.join(".git").exists() {
            return true;
        }
        cur = d.parent();
    }
    false
}

async fn evaluate_compiled_rules(config: &AppConfig, user_message: &str) -> Vec<String> {
    let reg_path = config.paths.passive_system_dir.join("triggers.json");
    let Ok(raw) = fs::read_to_string(&reg_path) else {
        return Vec::new();
    };
    let Ok(entries) = serde_json::from_str::<Vec<SystemRuleRegistryEntry>>(&raw) else {
        return Vec::new();
    };

    let mut handles = Vec::new();
    for item in entries {
        if !item.enabled || item.rule.is_empty() || item.prompt.is_empty() {
            continue;
        }
        let exec_path = if item.rule.ends_with(".rs") {
            let base = Path::new(&item.rule)
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            config
                .paths
                .passive_system_dir
                .join("rules/.bin")
                .join(base)
        } else {
            config.paths.passive_system_dir.join(&item.rule)
        };
        if !exec_path.is_file() {
            continue;
        }
        let prompt_path = config.paths.passive_system_dir.join(&item.prompt);
        let id = item.id.clone();
        let cwd = config.cwd.clone();
        let umsg = user_message.to_string();
        let mode_str = config.approval_mode.as_policy_mode().to_string();

        handles.push(tokio::spawn(async move {
            let ext = exec_path.extension().and_then(|s| s.to_str()).unwrap_or("");
            let mut cmd = match ext {
                "sh" => {
                    let mut c = Command::new("/bin/bash");
                    c.arg(&exec_path);
                    c
                }
                "py" => {
                    let mut c = Command::new("/usr/bin/python3");
                    c.arg(&exec_path);
                    c
                }
                _ => Command::new(&exec_path),
            };
            cmd.current_dir(&cwd)
                .env("FLOWORK_CWD", cwd.to_string_lossy().as_ref())
                .env("FLOWORK_USER_MSG", &umsg)
                .env("FLOWORK_APPROVAL_MODE", &mode_str)
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null());

            let res = timeout(Duration::from_millis(50), cmd.status()).await;
            if let Ok(Ok(status)) = res {
                if status.success() {
                    if let Ok(p_content) = fs::read_to_string(&prompt_path) {
                        let trimmed = p_content.trim();
                        if !trimmed.is_empty() {
                            return Some(format!(
                                "<PASSIVE_ENVIRONMENTAL_INSTINCT id=\"{}\">\n{}\n</PASSIVE_ENVIRONMENTAL_INSTINCT>",
                                id, trimmed
                            ));
                        }
                    }
                }
            }
            None
        }));
    }

    let mut out = Vec::new();
    for h in handles {
        if let Ok(Some(s)) = h.await {
            out.push(s);
        }
    }
    out
}

const ACTIVE_TRIGGER_TTL_SECS: i64 = 300;

fn parse_trigger_timestamp_secs(v: &Value) -> Option<i64> {
    if let Some(ts) = v.get("timestamp").and_then(|t| t.as_i64()) {
        return Some(if ts > 1_000_000_000_000 { ts / 1000 } else { ts });
    }
    if let Some(ts_f) = v.get("timestamp").and_then(|t| t.as_f64()) {
        let ts = ts_f as i64;
        return Some(if ts > 1_000_000_000_000 { ts / 1000 } else { ts });
    }
    if let Some(ts_str) = v.get("timestamp").and_then(|t| t.as_str()) {
        if let Ok(dt) = chrono::DateTime::parse_from_rfc3339(ts_str) {
            return Some(dt.timestamp());
        }
    }
    None
}

pub fn parse_active_watchdog_trigger(raw: &str, now_secs: i64) -> Option<String> {
    let v = serde_json::from_str::<Value>(raw).ok()?;
    let active = v.get("active").and_then(|b| b.as_bool()).unwrap_or(false);
    let instruction = v.get("instruction").and_then(|s| s.as_str()).unwrap_or("");
    if !active || instruction.is_empty() {
        return None;
    }
    let ts_secs = parse_trigger_timestamp_secs(&v)?;
    if now_secs.saturating_sub(ts_secs) > ACTIVE_TRIGGER_TTL_SECS {
        return None;
    }
    let source = v.get("source").and_then(|s| s.as_str()).unwrap_or("SYSTEM");
    Some(format!(
        "\n# 🚨 ACTIVE WATCHDOG SIGNAL [{}]\n{}\n",
        source, instruction
    ))
}

pub fn read_active_watchdog_trigger() -> Option<String> {
    let raw = fs::read_to_string(ACTIVE_TRIGGER_FILE).ok()?;
    let now_secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0);
    parse_active_watchdog_trigger(&raw, now_secs)
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
struct AliasFile {
    #[serde(default)]
    synonym_groups: Vec<AliasGroup>,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
struct AliasGroup {
    #[serde(default)]
    id: String,
    #[serde(default)]
    triggers: Vec<String>,
    #[serde(default)]
    canonical: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
struct PillarGraphFile {
    #[serde(default)]
    rules: Vec<PillarGraphRule>,
}

#[derive(Debug, Clone, Deserialize, Serialize, Default)]
struct PillarGraphRule {
    source: String,
    #[serde(default = "default_bonus")]
    bonus: usize,
    #[serde(default)]
    tools: Vec<String>,
    #[serde(default)]
    skills: Vec<String>,
    #[serde(default)]
    triggers: Vec<String>,
}

fn default_bonus() -> usize {
    7
}

#[derive(Debug, Clone, Serialize)]
pub struct ScoredRouteEntry {
    pub id: String,
    pub kind: String,
    pub total_score: usize,
    pub layer1_exact: usize,
    pub layer2_alias_bm25: usize,
    pub layer3_affinity: usize,
    pub signals: usize,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct RouteReport {
    pub query_tokens: Vec<String>,
    pub alias_expanded_tokens: Vec<String>,
    pub active_nodes: Vec<String>,
    pub top_tools: Vec<ScoredRouteEntry>,
    pub top_skills: Vec<ScoredRouteEntry>,
    pub top_prompts: Vec<ScoredRouteEntry>,
}

#[derive(Debug, Clone, Serialize)]
pub struct RouterAuditItem {
    pub kind: String,
    pub id: String,
    pub recommendations: usize,
    pub hits: usize,
    pub hit_rate_pct: f64,
    pub avg_score: f64,
}

#[derive(Debug, Clone, Serialize)]
pub struct RouterAuditReport {
    pub db_path: String,
    pub total_recommendations: usize,
    pub total_hits: usize,
    pub overall_hit_rate_pct: f64,
    pub top_items: Vec<RouterAuditItem>,
    pub noisy_triggers: Vec<RouterAuditItem>,
    pub dead_triggers: Vec<String>,
    pub dead_skills: Vec<String>,
}

fn default_alias_groups() -> Vec<AliasGroup> {
    vec![
        AliasGroup {
            id: "audio_mastering".to_string(),
            triggers: [
                "suara", "musik", "lagu", "podcast", "rekaman", "vokal", "mic", "noise",
                "jernih", "bersihin", "kompres", "mastering", "audio", "sound", "equalizer",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
            canonical: [
                "audio", "sound", "mastering", "dsp", "earshot", "kamidi", "compressor",
                "limiter", "noise", "audit",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        },
        AliasGroup {
            id: "security_bugbounty_re".to_string(),
            triggers: [
                "kerentanan", "celah", "keamanan", "bugbounty", "bounty", "exploit", "dekompilasi",
                "biner", "apk", "elf", "reverse", "disassemble", "pentest",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
            canonical: [
                "vulnerability", "security", "audit", "triage", "semgrep", "reverse",
                "decompile", "elf", "apk", "binary", "rea",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        },
        AliasGroup {
            id: "video_animation".to_string(),
            triggers: [
                "video", "klip", "film", "animasi", "pendek", "reels", "shorts", "subtitle",
                "stikman", "stickman", "montase",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
            canonical: [
                "video", "animation", "cutvii", "render", "ffmpeg", "stickman", "line",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        },
        AliasGroup {
            id: "seo_geo_analytics".to_string(),
            triggers: [
                "seo", "geo", "peringkat", "trafik", "website", "keyword", "sitemap", "schema",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
            canonical: [
                "seo", "geo", "search_engine_optimization", "sitemap", "schema_jsonld",
                "traffic", "similarweb", "ubersuggest", "vidiq", "audit",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        },
    ]
}

pub fn detect_cwd_affinity_nodes(cwd: &Path) -> Vec<String> {
    let mut nodes = Vec::new();
    let lower = cwd.to_string_lossy().to_ascii_lowercase();
    for app in [
        "cutvii",
        "kamidi-mastering",
        "seoflow",
        "reviewflow",
        "flowork-stealth",
        "downflow",
        "sysd",
        "connector-rs",
        "mrflow-rs",
        "iso-builder",
        "sherlockcraft",
        "gputaskman",
        "openscreen",
    ] {
        if lower.contains(app) {
            nodes.push(format!("app:{}", app));
        }
    }
    nodes
}

pub fn resolve_router_metrics_db_path(config: &AppConfig) -> PathBuf {
    if let Ok(explicit) = std::env::var("FLOWORK_ROUTER_METRICS_DB") {
        let trimmed = explicit.trim();
        if !trimmed.is_empty() {
            return PathBuf::from(trimmed);
        }
    }
    let sys_db = config.paths.flowork_root.join("history/router_metrics.db");
    if let Some(parent) = sys_db.parent() {
        if parent.is_dir()
            && Connection::open_with_flags(
                &sys_db,
                OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE,
            )
            .is_ok()
        {
            return sys_db;
        }
    }
    config.paths.user_flowork_dir.join("history/router_metrics.db")
}

fn open_metrics_conn(db_path: &Path) -> Option<Connection> {
    if let Some(parent) = db_path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let conn = Connection::open(db_path).ok()?;
    let _ = conn.execute_batch(
        "PRAGMA journal_mode=WAL;
         PRAGMA busy_timeout=1500;
         CREATE TABLE IF NOT EXISTS router_events (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             ts INTEGER NOT NULL,
             session_id TEXT NOT NULL,
             kind TEXT NOT NULL,
             item_id TEXT NOT NULL,
             score INTEGER NOT NULL,
             layer1 INTEGER NOT NULL,
             layer2 INTEGER NOT NULL,
             layer3 INTEGER NOT NULL,
             hit INTEGER NOT NULL DEFAULT 0,
             query_sample TEXT
         );
         CREATE INDEX IF NOT EXISTS idx_router_events_session_item ON router_events(session_id, kind, item_id);
         CREATE INDEX IF NOT EXISTS idx_router_events_kind_item ON router_events(kind, item_id);",
    );
    Some(conn)
}

fn sanitize_fts_word(s: &str) -> Option<String> {
    let clean: String = s
        .chars()
        .map(|c| if c.is_ascii_alphanumeric() { c.to_ascii_lowercase() } else { ' ' })
        .collect();
    let trimmed = clean.trim();
    if trimmed.len() >= 3 {
        Some(trimmed.to_string())
    } else {
        None
    }
}

/// Native Rust Formula 5-3-3 Hybrid Router v2 (Exact/Stemmed + FTS5 BM25 + Synonym Aliases + Cross-Pillar Graph + Telemetry).
pub struct Formula533Router {
    tool_tokens: Vec<(String, String, Vec<String>, HashSet<String>)>,
    skills: Vec<SkillMeta>,
    prompts: Vec<PromptTriggerMeta>,
    fts_conn: Option<Connection>,
    aliases_paths: Vec<PathBuf>,
    aliases_mtimes: Vec<Option<SystemTime>>,
    aliases: Vec<AliasGroup>,
    graph_paths: Vec<PathBuf>,
    graph_mtimes: Vec<Option<SystemTime>>,
    graph_rules: Vec<PillarGraphRule>,
    active_nodes: HashSet<String>,
    session_id: String,
    metrics_db_path: PathBuf,
    telemetry_enabled: bool,
    last_keywords_hash: String,
    emitted_prompt_ids: HashSet<String>,
}

impl Formula533Router {
    pub fn build(config: &AppConfig, tools: &[(String, String, Vec<String>)], skills: Vec<SkillMeta>) -> Self {
        let tool_tokens: Vec<(String, String, Vec<String>, HashSet<String>)> = tools
            .iter()
            .map(|(name, desc, kws)| {
                let raw = format!("{} {}", name, kws.join(" "));
                (name.clone(), desc.clone(), kws.clone(), tokenize_set(&raw))
            })
            .collect();

        let prompts = load_conditional_prompts(config);

        let fts_conn = Self::build_fts_index(&tool_tokens, &skills, &prompts);

        let aliases_paths = vec![
            config.paths.passive_system_dir.join("router_aliases.json"),
            config.paths.user_flowork_dir.join("router_aliases.json"),
        ];
        let graph_paths = vec![
            config.paths.passive_system_dir.join("pillar_graph.json"),
            config.paths.user_flowork_dir.join("pillar_graph.json"),
        ];

        let mut active_nodes = HashSet::new();
        for n in detect_cwd_affinity_nodes(&config.cwd) {
            active_nodes.insert(n);
        }

        let mut router = Self {
            tool_tokens,
            skills,
            prompts,
            fts_conn,
            aliases_paths,
            aliases_mtimes: vec![None, None],
            aliases: Vec::new(),
            graph_paths,
            graph_mtimes: vec![None, None],
            graph_rules: Vec::new(),
            active_nodes,
            session_id: "ephemeral".to_string(),
            metrics_db_path: resolve_router_metrics_db_path(config),
            telemetry_enabled: true,
            last_keywords_hash: String::new(),
            emitted_prompt_ids: HashSet::new(),
        };
        router.reload_configs_if_changed(true);
        router
    }

    pub fn set_session_id(&mut self, sid: &str) {
        if !sid.trim().is_empty() {
            self.session_id = sid.trim().to_string();
        }
    }

    pub fn set_telemetry_enabled(&mut self, enabled: bool) {
        self.telemetry_enabled = enabled;
    }

    pub fn add_active_node(&mut self, node: &str) {
        let norm = node.trim().to_ascii_lowercase();
        if !norm.is_empty() {
            self.active_nodes.insert(norm);
        }
    }

    pub fn record_activation(&mut self, tool_name: &str, activated_skill: Option<&str>) {
        let t_norm = tool_name.trim().to_ascii_lowercase();
        if !t_norm.is_empty() {
            self.add_active_node(&format!("tool:{}", t_norm));
        }
        if let Some(sk) = activated_skill {
            let s_norm = sk.trim().to_ascii_lowercase();
            if !s_norm.is_empty() {
                self.add_active_node(&format!("skill:{}", s_norm));
            }
        }
        if !self.telemetry_enabled {
            return;
        }
        if let Some(conn) = open_metrics_conn(&self.metrics_db_path) {
            let _ = conn.execute(
                "UPDATE router_events SET hit = 1 WHERE session_id = ?1 AND kind = 'tool' AND lower(item_id) = ?2",
                params![self.session_id, t_norm],
            );
            if let Some(sk) = activated_skill {
                let s_norm = sk.trim().to_ascii_lowercase();
                let _ = conn.execute(
                    "UPDATE router_events SET hit = 1 WHERE session_id = ?1 AND kind = 'skill' AND lower(item_id) = ?2",
                    params![self.session_id, s_norm],
                );
            }
        }
    }

    fn build_fts_index(
        tools: &[(String, String, Vec<String>, HashSet<String>)],
        skills: &[SkillMeta],
        prompts: &[PromptTriggerMeta],
    ) -> Option<Connection> {
        let conn = Connection::open_in_memory().ok()?;
        conn.execute_batch(
            "CREATE VIRTUAL TABLE router_index USING fts5(
                item_id UNINDEXED,
                kind UNINDEXED,
                name,
                keywords,
                description,
                tokenize='porter unicode61'
            );",
        )
        .ok()?;

        let mut stmt = conn
            .prepare("INSERT INTO router_index(item_id, kind, name, keywords, description) VALUES (?1, ?2, ?3, ?4, ?5)")
            .ok()?;

        for (name, desc, kws, _) in tools {
            let clean_name = name.replace('_', " ").replace('-', " ");
            let clean_kws = kws.join(" ").replace('_', " ").replace('-', " ");
            let _ = stmt.execute(params![name, "tool", clean_name, clean_kws, desc]);
        }
        for sk in skills {
            let clean_name = sk.name.replace('_', " ").replace('-', " ");
            let clean_kws = sk.keywords.join(" ").replace('_', " ").replace('-', " ");
            let _ = stmt.execute(params![sk.name, "skill", clean_name, clean_kws, sk.description]);
        }
        for pr in prompts {
            let clean_id = pr.id.replace('_', " ").replace('-', " ");
            let header: String = pr.content.lines().take(6).collect::<Vec<_>>().join(" ");
            let _ = stmt.execute(params![pr.id, "prompt", clean_id, pr.keywords_text, header]);
        }
        drop(stmt);
        Some(conn)
    }

    fn reload_configs_if_changed(&mut self, force: bool) {
        let mut aliases_dirty = force;
        for (idx, p) in self.aliases_paths.iter().enumerate() {
            let mt = fs::metadata(p).and_then(|m| m.modified()).ok();
            if idx < self.aliases_mtimes.len() && self.aliases_mtimes[idx] != mt {
                self.aliases_mtimes[idx] = mt;
                aliases_dirty = true;
            }
        }
        if aliases_dirty {
            let mut merged = Vec::new();
            let mut loaded_any = false;
            for p in &self.aliases_paths {
                if let Ok(raw) = fs::read_to_string(p) {
                    if let Ok(parsed) = serde_json::from_str::<AliasFile>(&raw) {
                        merged.extend(parsed.synonym_groups);
                        loaded_any = true;
                    }
                }
            }
            if !loaded_any {
                merged = default_alias_groups();
            }
            self.aliases = merged;
        }

        let mut graph_dirty = force;
        for (idx, p) in self.graph_paths.iter().enumerate() {
            let mt = fs::metadata(p).and_then(|m| m.modified()).ok();
            if idx < self.graph_mtimes.len() && self.graph_mtimes[idx] != mt {
                self.graph_mtimes[idx] = mt;
                graph_dirty = true;
            }
        }
        if graph_dirty {
            let mut merged = Vec::new();
            for p in &self.graph_paths {
                if let Ok(raw) = fs::read_to_string(p) {
                    if let Ok(parsed) = serde_json::from_str::<PillarGraphFile>(&raw) {
                        merged.extend(parsed.rules);
                    }
                }
            }
            self.graph_rules = merged;
        }
    }

    fn expand_query_tokens(&self, raw_inputs: &[String]) -> (HashSet<String>, HashSet<String>) {
        let stop: HashSet<&str> = STOP_WORDS.iter().copied().collect();
        let mut orig_tokens = HashSet::new();
        for inp in raw_inputs {
            for tok in tokenize_set(inp) {
                orig_tokens.insert(tok);
            }
        }

        let mut alias_tokens = HashSet::new();
        if orig_tokens.is_empty() {
            return (orig_tokens, alias_tokens);
        }

        for grp in &self.aliases {
            let matched = grp.triggers.iter().any(|t| {
                let tl = t.trim().to_ascii_lowercase();
                let ts = stem_token(&tl);
                orig_tokens.contains(&tl) || orig_tokens.contains(&ts)
            });
            if matched {
                for can in &grp.canonical {
                    for part in tokenize_set(can) {
                        if !orig_tokens.contains(&part) && !stop.contains(part.as_str()) {
                            alias_tokens.insert(part);
                        }
                    }
                }
            }
        }

        (orig_tokens, alias_tokens)
    }

    fn query_fts5_scores(&self, kind: &str, query_tokens: &HashSet<String>) -> HashMap<String, usize> {
        let mut out = HashMap::new();
        let Some(ref conn) = self.fts_conn else {
            return out;
        };
        let mut fts_terms: Vec<String> = Vec::new();
        let mut seen = HashSet::new();
        for tok in query_tokens {
            for piece in tok.split(|c| c == '_' || c == '-') {
                if let Some(clean) = sanitize_fts_word(piece) {
                    if seen.insert(clean.clone()) {
                        fts_terms.push(format!("\"{}\"", clean));
                    }
                }
            }
        }
        if fts_terms.is_empty() {
            return out;
        }
        fts_terms.truncate(32);
        let match_expr = fts_terms.join(" OR ");
        let Ok(mut stmt) = conn.prepare(
            "SELECT item_id, -bm25(router_index) AS score
             FROM router_index
             WHERE kind = ?1 AND router_index MATCH ?2
             ORDER BY bm25(router_index)
             LIMIT 16",
        ) else {
            return out;
        };
        let Ok(rows) = stmt.query_map(params![kind, match_expr], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, f64>(1)?))
        }) else {
            return out;
        };
        let mut raw_hits: Vec<(String, f64)> = rows.flatten().collect();
        if raw_hits.is_empty() {
            return out;
        }
        let max_score = raw_hits
            .iter()
            .map(|(_, s)| *s)
            .fold(0.0f64, f64::max)
            .max(0.001);
        for (id, s) in raw_hits.drain(..) {
            if s > 0.0 {
                let norm = ((s / max_score) * 4.0).round().clamp(1.0, 4.0) as usize;
                out.insert(id, norm);
            }
        }
        out
    }

    fn collect_affinity_boosts(
        &self,
        extra_nodes: &[String],
    ) -> (HashMap<String, usize>, HashMap<String, usize>, HashMap<String, usize>) {
        let mut tool_boosts = HashMap::new();
        let mut skill_boosts = HashMap::new();
        let mut trigger_boosts = HashMap::new();

        for rule in &self.graph_rules {
            let src_lower = rule.source.trim().to_ascii_lowercase();
            let active = self.active_nodes.contains(&src_lower)
                || extra_nodes.iter().any(|n| n == &src_lower);
            if !active {
                continue;
            }
            let bonus = rule.bonus.clamp(1, 10);
            for t in &rule.tools {
                let entry = tool_boosts.entry(t.clone()).or_insert(0usize);
                *entry = (*entry).max(bonus);
            }
            for s in &rule.skills {
                let entry = skill_boosts.entry(s.clone()).or_insert(0usize);
                *entry = (*entry).max(bonus);
            }
            for tr in &rule.triggers {
                let entry = trigger_boosts.entry(tr.clone()).or_insert(0usize);
                *entry = (*entry).max(bonus);
            }
        }
        (tool_boosts, skill_boosts, trigger_boosts)
    }

    pub fn route(&mut self, keywords: &[String], goal: &str, reason: &str) -> String {
        let (guidance, _) = self.route_with_report(keywords, goal, reason, None);
        guidance
    }

    pub fn route_with_report(
        &mut self,
        keywords: &[String],
        goal: &str,
        reason: &str,
        extra_context_text: Option<&str>,
    ) -> (String, RouteReport) {
        self.reload_configs_if_changed(false);

        let hash_key = format!(
            "{}|{}|{}|{}",
            keywords.join(","),
            goal,
            reason,
            extra_context_text.unwrap_or("")
        );
        if self.telemetry_enabled && hash_key == self.last_keywords_hash {
            return (String::new(), RouteReport::default());
        }
        self.last_keywords_hash = hash_key;

        let mut inputs: Vec<String> = keywords.to_vec();
        if !goal.trim().is_empty() {
            inputs.push(goal.to_string());
        }
        if !reason.trim().is_empty() {
            inputs.push(reason.to_string());
        }
        if let Some(extra) = extra_context_text {
            if !extra.trim().is_empty() {
                inputs.push(extra.to_string());
            }
        }

        let (orig_tokens, alias_tokens) = self.expand_query_tokens(&inputs);
        if orig_tokens.is_empty() && self.active_nodes.is_empty() {
            return (String::new(), RouteReport::default());
        }

        let mut all_query_tokens = orig_tokens.clone();
        all_query_tokens.extend(alias_tokens.iter().cloned());

        let fts_tools = self.query_fts5_scores("tool", &all_query_tokens);
        let fts_skills = self.query_fts5_scores("skill", &all_query_tokens);
        let fts_prompts = self.query_fts5_scores("prompt", &all_query_tokens);

        let (base_tool_boosts, base_skill_boosts, base_trigger_boosts) =
            self.collect_affinity_boosts(&[]);

        let score_item = |token_set: &HashSet<String>, fts_pt: usize, l3: usize| -> (usize, usize, usize, usize) {
            let mut l1_hits = 0usize;
            for tok in &orig_tokens {
                if token_set.contains(tok) {
                    l1_hits += 1;
                }
            }
            let l1 = l1_hits * 5;

            let mut alias_hits = 0usize;
            for tok in &alias_tokens {
                if token_set.contains(tok) {
                    alias_hits += 1;
                }
            }
            // Cap alias linear growth to keep scores balanced with FTS5 BM25
            let alias_pts = (alias_hits * 4).min(12);
            let signals = l1_hits + alias_hits;
            // FTS5 BM25 only boosts when corroborated by >= 1 lexical hit or >= 6 affinity boost (Zero-Bloat guard)
            let bm25_pts = if signals >= 1 || l3 >= 6 { fts_pt } else { 0 };
            let l2 = alias_pts + bm25_pts;
            let total = l1 + l2 + l3;

            let qualifies = l1 >= 10
                || (signals >= 2 && total >= 10)
                || (l3 >= 6 && (signals >= 1 || bm25_pts >= 2) && total >= 10);

            if qualifies {
                (total, l1, l2, signals)
            } else {
                (0, l1, l2, signals)
            }
        };

        // Pass 1: Score Skills (so co-activated skill becomes a Layer-3 hub for tools!)
        let mut matched_skills: Vec<(usize, SkillMeta, usize, usize, usize, usize)> = self
            .skills
            .iter()
            .filter_map(|sk| {
                let l3 = base_skill_boosts.get(&sk.name).copied().unwrap_or(0);
                let (total, l1, l2, sig) = score_item(&sk.token_set, fts_skills.get(&sk.name).copied().unwrap_or(0), l3);
                if total >= 10 {
                    Some((total, sk.clone(), l1, l2, l3, sig))
                } else {
                    None
                }
            })
            .collect();
        matched_skills.sort_by(|a, b| b.0.cmp(&a.0).then_with(|| a.1.name.cmp(&b.1.name)));
        matched_skills.truncate(3);

        // Pass 2: Add top matched skills as ephemeral Layer-3 hubs for tool enrichment
        let hub_nodes: Vec<String> = matched_skills
            .iter()
            .map(|(_, sk, _, _, _, _)| format!("skill:{}", sk.name.to_ascii_lowercase()))
            .collect();
        let (tool_boosts, _, trigger_boosts) = self.collect_affinity_boosts(&hub_nodes);

        // Top 5 Tools
        let mut matched_tools: Vec<(usize, String, String, usize, usize, usize, usize)> = self
            .tool_tokens
            .iter()
            .filter_map(|(n, d, _, set)| {
                let l3 = tool_boosts
                    .get(n)
                    .copied()
                    .or_else(|| base_tool_boosts.get(n).copied())
                    .unwrap_or(0);
                let fts_pt = fts_tools.get(n).copied().unwrap_or(0);
                let (total, l1, l2, sig) = score_item(set, fts_pt, l3);
                if total >= 10 {
                    Some((total, n.clone(), d.clone(), l1, l2, l3, sig))
                } else {
                    None
                }
            })
            .collect();
        matched_tools.sort_by(|a, b| b.0.cmp(&a.0).then_with(|| a.1.cmp(&b.1)));
        matched_tools.truncate(5);

        // Top 3 Conditional Prompts (session-deduped in live mode)
        let mut matched_prompts: Vec<(usize, PromptTriggerMeta, usize, usize, usize, usize)> = self
            .prompts
            .iter()
            .filter_map(|pr| {
                if self.telemetry_enabled && self.emitted_prompt_ids.contains(&pr.id) {
                    return None;
                }
                let l3 = trigger_boosts
                    .get(&pr.id)
                    .copied()
                    .or_else(|| base_trigger_boosts.get(&pr.id).copied())
                    .unwrap_or(0);
                let fts_pt = fts_prompts.get(&pr.id).copied().unwrap_or(0);
                let (total, l1, l2, sig) = score_item(&pr.token_set, fts_pt, l3);
                if total >= 10 {
                    Some((total, pr.clone(), l1, l2, l3, sig))
                } else {
                    None
                }
            })
            .collect();
        matched_prompts.sort_by(|a, b| b.0.cmp(&a.0).then_with(|| a.1.id.cmp(&b.1.id)));
        matched_prompts.truncate(3);

        if self.telemetry_enabled {
            for (_, pr, _, _, _, _) in &matched_prompts {
                self.emitted_prompt_ids.insert(pr.id.clone());
            }
        }

        let mut q_vec: Vec<String> = orig_tokens.into_iter().collect();
        q_vec.sort();
        let mut a_vec: Vec<String> = alias_tokens.into_iter().collect();
        a_vec.sort();
        let mut node_vec: Vec<String> = self.active_nodes.iter().cloned().collect();
        for h in hub_nodes {
            if !node_vec.contains(&h) {
                node_vec.push(h);
            }
        }
        node_vec.sort();

        let report = RouteReport {
            query_tokens: q_vec,
            alias_expanded_tokens: a_vec,
            active_nodes: node_vec,
            top_tools: matched_tools
                .iter()
                .map(|(tot, name, desc, l1, l2, l3, sig)| ScoredRouteEntry {
                    id: name.clone(),
                    kind: "tool".to_string(),
                    total_score: *tot,
                    layer1_exact: *l1,
                    layer2_alias_bm25: *l2,
                    layer3_affinity: *l3,
                    signals: *sig,
                    detail: desc.lines().next().unwrap_or("").to_string(),
                })
                .collect(),
            top_skills: matched_skills
                .iter()
                .map(|(tot, sk, l1, l2, l3, sig)| ScoredRouteEntry {
                    id: sk.name.clone(),
                    kind: "skill".to_string(),
                    total_score: *tot,
                    layer1_exact: *l1,
                    layer2_alias_bm25: *l2,
                    layer3_affinity: *l3,
                    signals: *sig,
                    detail: sk.path.display().to_string(),
                })
                .collect(),
            top_prompts: matched_prompts
                .iter()
                .map(|(tot, pr, l1, l2, l3, sig)| ScoredRouteEntry {
                    id: pr.id.clone(),
                    kind: "prompt".to_string(),
                    total_score: *tot,
                    layer1_exact: *l1,
                    layer2_alias_bm25: *l2,
                    layer3_affinity: *l3,
                    signals: *sig,
                    detail: pr.title.clone(),
                })
                .collect(),
        };

        if self.telemetry_enabled && (!report.top_tools.is_empty() || !report.top_skills.is_empty() || !report.top_prompts.is_empty()) {
            self.write_telemetry(&report, &inputs.join(" "));
        }

        if matched_tools.is_empty() && matched_skills.is_empty() && matched_prompts.is_empty() {
            return (String::new(), report);
        }

        let mut sections = Vec::new();

        if !matched_tools.is_empty() {
            let mut lines = vec![
                "[FLOWORK VERIFIED TOOLS — SYSTEM RECOMMENDATIONS]".to_string(),
                "⚡ Active sovereign tools matched to your operational goal and keywords:".to_string(),
            ];
            for (i, (_, name, desc, _, _, _, _)) in matched_tools.iter().enumerate() {
                let first_line = desc.lines().next().unwrap_or("");
                lines.push(format!("{}. `{}`: {}", i + 1, name, first_line));
            }
            sections.push(lines.join("\n"));
        }

        if !matched_skills.is_empty() {
            let mut lines = vec![
                "[FLOWORK SOVEREIGN SKILLS — MANUAL INSPECTION REQUIRED]".to_string(),
                "⚠️ DO NOT RELY ON OUTDATED PRE-TRAINING DATA!".to_string(),
                "The system detected relevant Flowork OS skills for your objective. Read the authoritative SKILL.md via `read_file` before acting:".to_string(),
            ];
            for (i, (_, sk, _, _, _, _)) in matched_skills.iter().enumerate() {
                lines.push(format!("{}. **{}** -> Path: `{}`", i + 1, sk.name, sk.path.display()));
            }
            sections.push(lines.join("\n"));
        }

        if !matched_prompts.is_empty() {
            let mut lines = vec![
                "<flowork_system_directive type=\"passive_trigger\">".to_string(),
                "[FLOWORK SYSTEM DIRECTIVE — SYSTEM ORIGINATED, NOT USER]".to_string(),
                "🔔 NOTICE: This is an authoritative SYSTEM directive from Flowork OS triggered by task keywords:".to_string(),
            ];
            for (i, (_, pr, _, _, _, _)) in matched_prompts.iter().enumerate() {
                lines.push(format!("\n--- [DIRECTIVE {}: {}] ---", i + 1, pr.title));
                lines.push(pr.content.clone());
            }
            lines.push("\n</flowork_system_directive>".to_string());
            sections.push(lines.join("\n"));
        }

        (
            sections.join(&format!("\n\n{}\n\n", "=".repeat(70))),
            report,
        )
    }

    fn write_telemetry(&self, report: &RouteReport, query_sample: &str) {
        let Some(conn) = open_metrics_conn(&self.metrics_db_path) else {
            return;
        };
        let ts = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs() as i64)
            .unwrap_or(0);
        let clipped_q: String = query_sample.chars().take(180).collect();
        let Ok(mut stmt) = conn.prepare(
            "INSERT INTO router_events(ts, session_id, kind, item_id, score, layer1, layer2, layer3, hit, query_sample)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, 0, ?9)",
        ) else {
            return;
        };
        for entry in report
            .top_tools
            .iter()
            .chain(report.top_skills.iter())
            .chain(report.top_prompts.iter())
        {
            let _ = stmt.execute(params![
                ts,
                self.session_id,
                entry.kind,
                entry.id,
                entry.total_score as i64,
                entry.layer1_exact as i64,
                entry.layer2_alias_bm25 as i64,
                entry.layer3_affinity as i64,
                clipped_q
            ]);
        }
    }

    pub fn audit_metrics(&self) -> RouterAuditReport {
        let db_path_str = self.metrics_db_path.display().to_string();
        let mut items: Vec<RouterAuditItem> = Vec::new();
        let mut total_recs = 0usize;
        let mut total_hits = 0usize;
        let mut seen_prompts = HashSet::new();
        let mut seen_skills = HashSet::new();

        if self.metrics_db_path.is_file() {
            if let Ok(conn) = Connection::open_with_flags(&self.metrics_db_path, OpenFlags::SQLITE_OPEN_READ_ONLY) {
                if let Ok(mut stmt) = conn.prepare(
                    "SELECT kind, item_id, COUNT(*) as recs, SUM(hit) as hits, AVG(score) as avg_s
                     FROM router_events
                     GROUP BY kind, item_id
                     ORDER BY recs DESC, hits DESC",
                ) {
                    if let Ok(rows) = stmt.query_map([], |row| {
                        Ok((
                            row.get::<_, String>(0)?,
                            row.get::<_, String>(1)?,
                            row.get::<_, i64>(2)?,
                            row.get::<_, Option<i64>>(3)?.unwrap_or(0),
                            row.get::<_, Option<f64>>(4)?.unwrap_or(0.0),
                        ))
                    }) {
                        for row in rows.flatten() {
                            let (kind, id, recs_i, hits_i, avg_s) = row;
                            let recs = recs_i.max(0) as usize;
                            let hits = hits_i.max(0) as usize;
                            total_recs += recs;
                            total_hits += hits;
                            if kind == "prompt" {
                                seen_prompts.insert(id.clone());
                            } else if kind == "skill" {
                                seen_skills.insert(id.clone());
                            }
                            let rate = if recs > 0 { (hits as f64 * 100.0) / recs as f64 } else { 0.0 };
                            items.push(RouterAuditItem {
                                kind,
                                id,
                                recommendations: recs,
                                hits,
                                hit_rate_pct: (rate * 10.0).round() / 10.0,
                                avg_score: (avg_s * 10.0).round() / 10.0,
                            });
                        }
                    }
                }
            }
        }

        let noisy_triggers: Vec<RouterAuditItem> = items
            .iter()
            .filter(|it| it.kind == "prompt" && it.recommendations >= 5 && it.hits == 0)
            .cloned()
            .collect();
        let dead_triggers: Vec<String> = self
            .prompts
            .iter()
            .map(|p| p.id.clone())
            .filter(|id| !seen_prompts.contains(id))
            .collect();
        let dead_skills: Vec<String> = self
            .skills
            .iter()
            .map(|s| s.name.clone())
            .filter(|name| !seen_skills.contains(name))
            .collect();

        let overall = if total_recs > 0 {
            ((total_hits as f64 * 100.0) / total_recs as f64 * 10.0).round() / 10.0
        } else {
            0.0
        };

        RouterAuditReport {
            db_path: db_path_str,
            total_recommendations: total_recs,
            total_hits,
            overall_hit_rate_pct: overall,
            top_items: items.into_iter().take(20).collect(),
            noisy_triggers,
            dead_triggers,
            dead_skills,
        }
    }
}

fn load_conditional_prompts(config: &AppConfig) -> Vec<PromptTriggerMeta> {
    let tjson = config.paths.prompts_dir.join("triggers.json");
    let Ok(raw) = fs::read_to_string(&tjson) else {
        return Vec::new();
    };
    let Ok(data) = serde_json::from_str::<Value>(&raw) else {
        return Vec::new();
    };
    let quote_re = Regex::new(r#"["']([^"']+)["']"#).unwrap();
    let mut entries = Vec::new();
    for arr_key in &["passive_triggers", "triggers"] {
        if let Some(arr) = data.get(arr_key).and_then(|v| v.as_array()) {
            entries.extend(arr.iter().cloned());
        }
    }

    let mut out = Vec::new();
    for pt in entries {
        let Some(id) = pt.get("id").and_then(|s| s.as_str()) else {
            continue;
        };
        let Some(file_rel) = pt.get("file").and_then(|s| s.as_str()) else {
            continue;
        };
        let full = config.paths.prompts_dir.join(file_rel);
        let Ok(content) = fs::read_to_string(&full) else {
            continue;
        };
        let cond = pt.get("condition").and_then(|s| s.as_str()).unwrap_or("");
        let mut extracted = Vec::new();
        if let Some(kws) = pt.get("keywords").and_then(|k| k.as_array()) {
            for k in kws {
                if let Some(s) = k.as_str() {
                    extracted.push(s.to_ascii_lowercase());
                }
            }
        }
        for cap in quote_re.captures_iter(cond) {
            if let Some(m) = cap.get(1) {
                let clean = m.as_str().trim().trim_start_matches("*.").trim_start_matches('*');
                if !clean.is_empty() {
                    extracted.push(clean.to_ascii_lowercase());
                }
            }
        }
        let keywords_text = extracted.join(" ").replace('_', " ").replace('-', " ");
        let mut p_tokens = tokenize_set(id);
        for item in &extracted {
            let clean = item.trim().to_ascii_lowercase();
            if clean.len() >= 3 && !STOP_WORDS.contains(&clean.as_str()) {
                p_tokens.insert(clean.clone());
                let st = stem_token(&clean);
                if st.len() >= 3 && !STOP_WORDS.contains(&st.as_str()) {
                    p_tokens.insert(st);
                }
            }
            // Only split space-separated trigger phrases into individual words; preserve underscore identifiers intact
            if clean.contains(' ') {
                for tok in tokenize_set(&clean) {
                    p_tokens.insert(tok);
                }
            }
        }
        out.push(PromptTriggerMeta {
            id: id.to_string(),
            title: id.replace('_', " ").to_ascii_uppercase(),
            path: full,
            content: content.trim().to_string(),
            keywords_text,
            token_set: p_tokens,
        });
    }
    out
}

pub fn update_lifecycle_after_turn(
    tool_names: &[String],
    last_keywords: &[String],
) {
    let mut state = load_lifecycle_state();
    state.turn_count += 1;
    if !last_keywords.is_empty() {
        state.active_keywords = last_keywords.iter().take(12).cloned().collect();
    }
    let used_browser = tool_names.iter().any(|n| n.starts_with("browser_") || n == "agent_browser");
    if used_browser {
        state.browser_active = true;
        state.browser_turns_remaining = 3;
        state.resource_state.browser_open_pages = state.resource_state.browser_open_pages.max(1);
    } else if state.browser_turns_remaining > 0 {
        state.browser_turns_remaining -= 1;
        if state.browser_turns_remaining == 0 {
            state.browser_active = false;
            state.resource_state.browser_open_pages = 0;
        }
    }
    state.active_tools = tool_names.to_vec();
    save_lifecycle_state(&state);
}

pub fn format_skill_list_summary(skills: &[SkillMeta]) -> String {
    let mut map: HashMap<String, Vec<&SkillMeta>> = HashMap::new();
    for s in skills {
        map.entry(s.domain.clone()).or_default().push(s);
    }
    let mut out = Vec::new();
    for sk in skills {
        out.push(format!("- {} [{}]: {}", sk.name, sk.domain, sk.description));
    }
    out.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{ApprovalMode, CliOverrides};

    #[test]
    fn watchdog_trigger_respects_ttl_and_active_flag() {
        let now = 1_762_860_000i64;
        let fresh_epoch = format!(
            r#"{{"active": true, "source": "TEST", "timestamp": {}, "instruction": "Check memory"}}"#,
            now - 10
        );
        let parsed = parse_active_watchdog_trigger(&fresh_epoch, now);
        assert!(parsed.is_some());
        assert!(parsed.unwrap().contains("Check memory"));

        let stale_epoch = format!(
            r#"{{"active": true, "source": "TEST", "timestamp": {}, "instruction": "Old alert"}}"#,
            now - 301
        );
        assert!(parse_active_watchdog_trigger(&stale_epoch, now).is_none());

        let inactive = format!(
            r#"{{"active": false, "source": "TEST", "timestamp": {}, "instruction": "Should ignore"}}"#,
            now
        );
        assert!(parse_active_watchdog_trigger(&inactive, now).is_none());

        let rfc_now = chrono::DateTime::from_timestamp(now, 0).unwrap();
        let fresh_rfc = format!(
            r#"{{"active": true, "source": "KERNEL", "timestamp": "{}", "instruction": "RFC fresh"}}"#,
            rfc_now.to_rfc3339()
        );
        assert!(parse_active_watchdog_trigger(&fresh_rfc, now + 60).is_some());
        assert!(parse_active_watchdog_trigger(&fresh_rfc, now + 600).is_none());
    }

    #[test]
    fn evaluates_external_trigger_dsl_and_flat_manifest_keywords() {
        let mut cfg = AppConfig::build(CliOverrides::default());
        cfg.approval_mode = ApprovalMode::Sovereign;
        cfg.interactive = true;

        let mut tools = HashSet::new();
        tools.insert("invoke_agent".to_string());
        let eval_ctx = TriggerEvalContext {
            config: &cfg,
            enabled_tool_names: &tools,
            skills: &[],
            has_subagents: true,
            is_git_repo: true,
            user_message_lower: "please audit cargo rust code and review code".to_string(),
            active_keywords: ["rust", "cargo"].into_iter().map(str::to_string).collect(),
            cwd_entries: vec!["Cargo.toml".to_ascii_lowercase()],
        };

        assert!(eval_trigger_condition("always", &eval_ctx));
        assert!(eval_trigger_condition("approvalMode !== 'plan'", &eval_ctx));
        assert!(eval_trigger_condition("approvalMode === 'sovereign' && interactive === true", &eval_ctx));
        assert!(eval_trigger_condition("hasAgentTool && subagents.length > 0", &eval_ctx));
        assert!(eval_trigger_condition("workspaceContains([\"*mrflow-rs*\", \"Cargo.toml\"]) || hasKeywords([\"mrflow_rs\"])", &eval_ctx));
        assert!(eval_trigger_condition("hasKeywords([\"seo\"]) || promptContains([\"review code\"])", &eval_ctx));
        assert!(!eval_trigger_condition("approvalMode === 'plan'", &eval_ctx));

        let flat_manifest = serde_json::json!({
            "name": "similarweb",
            "activation": "conditional",
            "keywords": ["traffic", "similarweb"]
        });
        let sniff = SniffedContext {
            cwd: cfg.cwd.clone(),
            extensions: HashSet::new(),
            file_names: HashSet::new(),
            browser_active: false,
            user_prompt_lower: "analyze similarweb traffic".to_string(),
            active_keywords: HashSet::new(),
        };
        assert!(is_manifest_tool_active(&flat_manifest, &sniff));
    }

    #[test]
    fn stemmer_and_compound_tokenization_handle_suffixes_and_underscores() {
        assert_eq!(stem_token("running"), "run");
        assert_eq!(stem_token("editing"), "edit");
        assert_eq!(stem_token("containers"), "container");
        assert_eq!(stem_token("vulnerabilities"), "vulnerability");
        let toks = tokenize_set("audio_mastering vulnerability_audit encrypting");
        assert!(toks.contains("audio"));
        assert!(toks.contains("mastering"));
        assert!(toks.contains("vulnerability"));
        assert!(toks.contains("encrypt"));
    }

    #[test]
    fn router_v2_matches_bilingual_aliases_fts5_and_graph_affinity_zero_bloat() {
        let cfg = AppConfig::build(CliOverrides::default());
        let skills = vec![
            SkillMeta {
                name: "kamidi-mastering".to_string(),
                description: "Professional audio mastering suite with parametric EQ and limiter".to_string(),
                domain: "shell_system".to_string(),
                keywords: vec![
                    "audio_mastering".to_string(),
                    "dsp_engine".to_string(),
                    "sound_engineering".to_string(),
                    "audio_limiter".to_string(),
                ],
                path: PathBuf::from("/opt/floworkos/skills/kamidi-mastering/SKILL.md"),
                token_set: tokenize_set("kamidi-mastering audio_mastering dsp_engine sound_engineering audio_limiter"),
            },
            SkillMeta {
                name: "agentic-seo-auditor".to_string(),
                description: "Autonomous SEO and GEO audit playbook".to_string(),
                domain: "browser".to_string(),
                keywords: vec!["seo".to_string(), "sitemap".to_string(), "schema_jsonld".to_string()],
                path: PathBuf::from("/opt/floworkos/skills/agentic-seo-auditor/SKILL.md"),
                token_set: tokenize_set("agentic-seo-auditor seo sitemap schema_jsonld"),
            },
        ];
        let tools = vec![
            (
                "mcp_earshot_audio_audit".to_string(),
                "Audit an audio WAV file for clipping, DC offset, and noise dynamic range".to_string(),
                vec!["earshot".to_string(), "audio_audit".to_string()],
            ),
            (
                "similarweb".to_string(),
                "Inspect domain traffic and competitor analytics".to_string(),
                vec!["traffic".to_string(), "similarweb".to_string()],
            ),
        ];

        let mut router = Formula533Router::build(&cfg, &tools, skills);
        router.set_telemetry_enabled(false);
        let kws: Vec<String> = vec![
            "tolong".into(),
            "bersihin".into(),
            "noise".into(),
            "rekaman".into(),
            "suara".into(),
            "podcast".into(),
        ];
        let (guidance, report) = router.route_with_report(
            &kws,
            "Clean background noise from podcast voice recording",
            "User asked in Indonesian to clean podcast audio recording noise",
            Some("tolong bersihin noise rekaman suara podcast"),
        );

        assert!(
            report.top_skills.iter().any(|s| s.id == "kamidi-mastering"),
            "Expected kamidi-mastering skill to match bilingual audio query; report={:?}",
            report
        );
        assert!(
            !report.top_skills.iter().any(|s| s.id == "agentic-seo-auditor"),
            "Zero-bloat invariant violated: unrelated SEO skill leaked!"
        );
        assert!(
            report.top_tools.iter().any(|t| t.id == "mcp_earshot_audio_audit"),
            "Expected earshot tool via alias + FTS5 + Cross-Pillar affinity boost; report={:?}",
            report
        );
        assert!(!report.top_tools.iter().any(|t| t.id == "similarweb"));
        assert!(guidance.contains("kamidi-mastering"));
    }

    #[test]
    fn router_v2_records_metrics_and_audits_hits() {
        let cfg = AppConfig::build(CliOverrides::default());
        let tmp_db = std::env::temp_dir().join(format!(
            "flowork_router_metrics_test_{}.db",
            std::process::id()
        ));
        let _ = fs::remove_file(&tmp_db);

        let skills = vec![SkillMeta {
            name: "kamidi-mastering".to_string(),
            description: "Audio mastering DSP".to_string(),
            domain: "shell_system".to_string(),
            keywords: vec!["audio_mastering".into(), "dsp_engine".into()],
            path: PathBuf::from("/opt/floworkos/skills/kamidi-mastering/SKILL.md"),
            token_set: tokenize_set("kamidi-mastering audio_mastering dsp_engine"),
        }];
        let tools = vec![(
            "mcp_earshot_audio_audit".to_string(),
            "Audit WAV audio file".to_string(),
            vec!["earshot".into(), "audio_audit".into()],
        )];

        let mut router = Formula533Router::build(&cfg, &tools, skills);
        router.metrics_db_path = tmp_db.clone();
        router.set_session_id("test-session-telemetry");
        let kws: Vec<String> = vec!["audio".into(), "mastering".into(), "podcast".into(), "noise".into(), "sound".into()];
        let (_, rep) = router.route_with_report(&kws, "master audio", "audio task", None);
        assert!(!rep.top_skills.is_empty());

        router.record_activation("mcp_earshot_audio_audit", Some("kamidi-mastering"));
        let audit = router.audit_metrics();
        assert!(audit.total_recommendations >= 1);
        assert!(audit.total_hits >= 1);
        let _ = fs::remove_file(&tmp_db);
    }
}
