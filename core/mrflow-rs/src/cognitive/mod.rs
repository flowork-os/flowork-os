use crate::config::AppConfig;
use regex::Regex;
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
    #[serde(default, alias = "lastTurn", rename = "lastTurn")]
    pub turn_count: usize,
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

pub fn tokenize_set(text: &str) -> HashSet<String> {
    let stop: HashSet<&str> = STOP_WORDS.iter().copied().collect();
    text.to_ascii_lowercase()
        .split(|c: char| !(c.is_ascii_alphanumeric() || c == '_' || c == '-'))
        .filter(|w| w.len() >= 3 && !stop.contains(w))
        .map(|s| s.to_string())
        .collect()
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
        let _ = fs::write(LIFECYCLE_STATE_FILE, json);
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
    let parts: Vec<&str> = pattern_lower.split('*').filter(|s| !s.is_empty()).collect();
    if parts.is_empty() {
        return true;
    }
    let mut pos = 0usize;
    for part in parts {
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
            "isHookContextEnabled" => "false".to_string(),
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
pub async fn assemble_system_prompt(
    config: &AppConfig,
    enabled_tool_names: &HashSet<String>,
    skills: &[SkillMeta],
    user_message: &str,
    extra_memory: &str,
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
        user_message_lower: lower_msg,
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
    let structural_checks: Vec<(bool, &str)> = vec![
        (
            enabled_tool_names.contains("write_file") || enabled_tool_names.contains("replace"),
            "triggers/code_engineering.md",
        ),
        (
            enabled_tool_names.contains("grep_search")
                || enabled_tool_names.contains("glob")
                || enabled_tool_names.contains("read_many_files"),
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
                "js" | "mjs" => {
                    let mut c = Command::new("node");
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

/// Native Rust port of Formula 5-3-3 Sliding Router (`router.js`).
pub struct Formula533Router {
    tool_tokens: Vec<(String, String, HashSet<String>)>,
    skills: Vec<SkillMeta>,
    prompts: Vec<PromptTriggerMeta>,
    last_keywords_hash: String,
    emitted_prompt_ids: HashSet<String>,
}

impl Formula533Router {
    pub fn build(config: &AppConfig, tools: &[(String, String, Vec<String>)], skills: Vec<SkillMeta>) -> Self {
        let tool_tokens = tools
            .iter()
            .map(|(name, desc, kws)| {
                let raw = format!("{} {}", name, kws.join(" "));
                (name.clone(), desc.clone(), tokenize_set(&raw))
            })
            .collect();

        let prompts = load_conditional_prompts(config);

        Self {
            tool_tokens,
            skills,
            prompts,
            last_keywords_hash: String::new(),
            emitted_prompt_ids: HashSet::new(),
        }
    }

    pub fn route(&mut self, keywords: &[String], goal: &str, reason: &str) -> String {
        let hash_key = format!("{}|{}|{}", keywords.join(","), goal, reason);
        if hash_key == self.last_keywords_hash {
            return String::new();
        }
        self.last_keywords_hash = hash_key;

        let kw_lower: Vec<String> = keywords
            .iter()
            .map(|k| k.trim().to_ascii_lowercase())
            .filter(|k| k.len() >= 3 && !STOP_WORDS.contains(&k.as_str()))
            .collect();
        if kw_lower.is_empty() {
            return String::new();
        }

        let score = |set: &HashSet<String>| -> usize {
            kw_lower.iter().filter(|k| set.contains(k.as_str())).count() * 5
        };

        // Top 5 tools (strict threshold: at least 2 distinct semantic matches)
        let mut matched_tools: Vec<_> = self
            .tool_tokens
            .iter()
            .filter_map(|(n, d, set)| {
                let s = score(set);
                if s >= 10 { Some((s, n.clone(), d.clone())) } else { None }
            })
            .collect();
        matched_tools.sort_by(|a, b| b.0.cmp(&a.0));
        matched_tools.truncate(5);

        // Top 3 skills (strict threshold: at least 2 distinct semantic matches)
        let mut matched_skills: Vec<_> = self
            .skills
            .iter()
            .filter_map(|sk| {
                let s = score(&sk.token_set);
                if s >= 10 { Some((s, sk.clone())) } else { None }
            })
            .collect();
        matched_skills.sort_by(|a, b| b.0.cmp(&a.0));
        matched_skills.truncate(3);

        // Top 3 conditional prompts: deduplicated per session so directives are never repeated!
        let mut matched_prompts: Vec<_> = self
            .prompts
            .iter()
            .filter_map(|pr| {
                if self.emitted_prompt_ids.contains(&pr.id) {
                    return None;
                }
                let s = score(&pr.token_set);
                if s >= 10 { Some((s, pr.clone())) } else { None }
            })
            .collect();
        matched_prompts.sort_by(|a, b| b.0.cmp(&a.0));
        matched_prompts.truncate(3);

        // Record newly emitted prompt IDs
        for (_, pr) in &matched_prompts {
            self.emitted_prompt_ids.insert(pr.id.clone());
        }

        if matched_tools.is_empty() && matched_skills.is_empty() && matched_prompts.is_empty() {
            return String::new();
        }

        let mut sections = Vec::new();

        if !matched_tools.is_empty() {
            let mut lines = vec![
                "[FLOWORK VERIFIED TOOLS — SYSTEM RECOMMENDATIONS]".to_string(),
                "⚡ Active sovereign tools matched to your operational goal and keywords:".to_string(),
            ];
            for (i, (_, name, desc)) in matched_tools.iter().enumerate() {
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
            for (i, (_, sk)) in matched_skills.iter().enumerate() {
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
            for (i, (_, pr)) in matched_prompts.iter().enumerate() {
                lines.push(format!("\n--- [DIRECTIVE {}: {}] ---", i + 1, pr.title));
                lines.push(pr.content.clone());
            }
            lines.push("\n</flowork_system_directive>".to_string());
            sections.push(lines.join("\n"));
        }

        sections.join(&format!("\n\n{}\n\n", "=".repeat(70)))
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
        let raw_tok = format!("{} {}", id, extracted.join(" "));
        out.push(PromptTriggerMeta {
            id: id.to_string(),
            title: id.replace('_', " ").to_ascii_uppercase(),
            path: full,
            content: content.trim().to_string(),
            token_set: tokenize_set(&raw_tok),
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
}
