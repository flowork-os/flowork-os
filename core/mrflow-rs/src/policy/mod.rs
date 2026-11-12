use crate::config::{AppConfig, ApprovalMode};
use regex::Regex;
use serde_json::Value;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};
use toml::Value as TomlValue;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PolicyDecision {
    Allow,
    Deny,
    AskUser,
}

#[derive(Debug, Clone)]
pub struct PolicyResult {
    pub decision: PolicyDecision,
    pub reason: Option<String>,
    #[allow(dead_code)]
    pub matched_rule: Option<String>,
}

#[derive(Debug, Clone)]
struct ParsedRule {
    name: Option<String>,
    tier: i64,
    priority: i64,
    tool_patterns: Vec<String>,
    modes: Option<Vec<String>>,
    interactive: Option<bool>,
    mcp_name: Option<String>,
    subagent: Option<String>,
    args_regex: Option<Regex>,
    command_prefixes: Vec<String>,
    command_regex: Option<Regex>,
    allow_redirection: Option<bool>,
    allow_command_substitution: Option<bool>,
    read_only_hint: Option<bool>,
    decision: PolicyDecision,
    deny_message: Option<String>,
    source: String,
}

#[derive(Debug, Clone)]
struct SafetyCheckerRule {
    tool_patterns: Vec<String>,
    modes: Option<Vec<String>>,
    checker_name: String,
    #[allow(dead_code)]
    priority: i64,
}

#[derive(Debug, Clone)]
pub struct PolicyEngine {
    rules: Vec<ParsedRule>,
    safety_checkers: Vec<SafetyCheckerRule>,
}

impl PolicyEngine {
    pub fn load(config: &AppConfig) -> Self {
        let mut rules = Vec::new();
        let mut safety_checkers = Vec::new();

        // Tier mapping:
        // Tier 1: System / Project policies (/opt/floworkos/policies, .flowork/policies)
        // Tier 2: User policies (~/.flowork/policies) and CLI --policy
        // Tier 5: Admin policies (/etc/flowork/policies) and CLI --admin-policy
        let mut sources: Vec<(PathBuf, i64)> = Vec::new();
        for dir in &config.paths.policies_dirs {
            let s = dir.to_string_lossy();
            let tier = if s.starts_with("/etc/") {
                5
            } else if dir == &config.paths.user_flowork_dir.join("policies") {
                2
            } else {
                1
            };
            sources.push((dir.clone(), tier));
        }
        for p in &config.extra_policy_paths {
            sources.push((p.clone(), 2));
        }
        for p in &config.extra_admin_policy_paths {
            sources.push((p.clone(), 5));
        }

        let mut loaded_files = HashSet::new();
        for (path, tier) in sources {
            if path.is_dir() {
                if let Ok(entries) = fs::read_dir(&path) {
                    let mut paths: Vec<PathBuf> = entries
                        .flatten()
                        .map(|e| e.path())
                        .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("toml"))
                        .collect();
                    paths.sort();
                    for fp in paths {
                        if let Ok(canon) = fs::canonicalize(&fp) {
                            if loaded_files.insert(canon) {
                                Self::parse_file(&fp, tier, &mut rules, &mut safety_checkers);
                            }
                        }
                    }
                }
            } else if path.is_file() {
                if let Ok(canon) = fs::canonicalize(&path) {
                    if loaded_files.insert(canon) {
                        Self::parse_file(&path, tier, &mut rules, &mut safety_checkers);
                    }
                }
            }
        }

        // Highest (tier, priority) first
        rules.sort_by(|a, b| {
            b.tier
                .cmp(&a.tier)
                .then_with(|| b.priority.cmp(&a.priority))
        });

        Self {
            rules,
            safety_checkers,
        }
    }

    fn parse_file(
        path: &Path,
        tier: i64,
        out_rules: &mut Vec<ParsedRule>,
        out_checkers: &mut Vec<SafetyCheckerRule>,
    ) {
        let Ok(raw) = fs::read_to_string(path) else {
            return;
        };
        let Ok(doc) = raw.parse::<TomlValue>() else {
            return;
        };
        let src_name = path
            .file_name()
            .and_then(|s| s.to_str())
            .unwrap_or("policy.toml")
            .to_string();

        for key in &["rule", "rules"] {
            if let Some(arr) = doc.get(key).and_then(|v| v.as_array()) {
                for item in arr {
                    if let Some(r) = Self::parse_single_rule(item, tier, &src_name) {
                        out_rules.push(r);
                    }
                }
            }
        }

        if let Some(arr) = doc
            .get("commands")
            .and_then(|c| c.get("rules"))
            .and_then(|v| v.as_array())
        {
            for item in arr {
                if let Some(r) = Self::parse_single_rule(item, tier, &src_name) {
                    out_rules.push(r);
                }
            }
        }

        if let Some(arr) = doc.get("safety_checker").and_then(|v| v.as_array()) {
            for item in arr {
                let tool_patterns = Self::extract_string_or_array(item.get("toolName"));
                if tool_patterns.is_empty() {
                    continue;
                }
                let modes = item
                    .get("modes")
                    .and_then(|v| v.as_array())
                    .map(|a| {
                        a.iter()
                            .filter_map(|x| x.as_str().map(|s| s.to_string()))
                            .collect::<Vec<_>>()
                    });
                let checker_name = item
                    .get("checker")
                    .and_then(|c| c.get("name"))
                    .and_then(|s| s.as_str())
                    .unwrap_or("")
                    .to_string();
                let priority = item
                    .get("priority")
                    .and_then(|p| p.as_integer())
                    .unwrap_or(50);
                if !checker_name.is_empty() {
                    out_checkers.push(SafetyCheckerRule {
                        tool_patterns,
                        modes,
                        checker_name,
                        priority,
                    });
                }
            }
        }
    }

    fn parse_single_rule(val: &TomlValue, tier: i64, source: &str) -> Option<ParsedRule> {
        let decision_str = val.get("decision")?.as_str()?;
        let decision = match decision_str.trim().to_ascii_lowercase().as_str() {
            "allow" => PolicyDecision::Allow,
            "deny" => PolicyDecision::Deny,
            "ask_user" | "ask" => PolicyDecision::AskUser,
            _ => return None,
        };
        let mut tool_patterns = Self::extract_string_or_array(
            val.get("toolName").or_else(|| val.get("tool_name")),
        );
        let command_prefixes = Self::extract_string_or_array(
            val.get("commandPrefix").or_else(|| val.get("command_prefix")),
        );
        let command_regex = val
            .get("commandRegex")
            .or_else(|| val.get("command_regex"))
            .and_then(|s| s.as_str())
            .and_then(|pat| Regex::new(pat).ok());

        if tool_patterns.is_empty() {
            if !command_prefixes.is_empty() || command_regex.is_some() {
                tool_patterns = vec!["run_shell_command".to_string(), "run_command".to_string()];
            } else {
                tool_patterns.push("*".to_string());
            }
        }
        let priority = val
            .get("priority")
            .and_then(|p| p.as_integer())
            .unwrap_or(50);
        let modes = val
            .get("modes")
            .and_then(|v| v.as_array())
            .map(|a| {
                a.iter()
                    .filter_map(|x| x.as_str().map(|s| s.to_string()))
                    .collect()
            });
        let interactive = val.get("interactive").and_then(|b| b.as_bool());
        let mcp_name = val
            .get("mcpName")
            .or_else(|| val.get("mcp_name"))
            .and_then(|s| s.as_str())
            .map(|s| s.to_string());
        let subagent = val
            .get("subagent")
            .and_then(|s| s.as_str())
            .map(|s| s.to_string());
        let allow_redirection = val
            .get("allowRedirection")
            .or_else(|| val.get("allow_redirection"))
            .and_then(|b| b.as_bool());
        let allow_command_substitution = val
            .get("allowCommandSubstitution")
            .or_else(|| val.get("allow_command_substitution"))
            .and_then(|b| b.as_bool());
        let read_only_hint = val
            .get("toolAnnotations")
            .and_then(|a| a.get("readOnlyHint"))
            .and_then(|b| b.as_bool());
        let deny_message = val
            .get("denyMessage")
            .or_else(|| val.get("deny_message"))
            .and_then(|s| s.as_str())
            .map(|s| s.to_string());
        let name = val
            .get("name")
            .and_then(|s| s.as_str())
            .map(|s| s.to_string());

        let args_regex = val
            .get("argsPattern")
            .or_else(|| val.get("args_pattern"))
            .and_then(|s| s.as_str())
            .and_then(|pat| {
                // TOML policies sometimes embed \x00 boundary assertions; normalize safely for Rust regex
                let cleaned = pat.replace("\\x00", "").replace('\0', "");
                Regex::new(&cleaned).ok()
            });

        Some(ParsedRule {
            name,
            tier,
            priority,
            tool_patterns,
            modes,
            interactive,
            mcp_name,
            subagent,
            args_regex,
            command_prefixes,
            command_regex,
            allow_redirection,
            allow_command_substitution,
            read_only_hint,
            decision,
            deny_message,
            source: source.to_string(),
        })
    }

    fn extract_string_or_array(val: Option<&TomlValue>) -> Vec<String> {
        let Some(v) = val else {
            return Vec::new();
        };
        if let Some(s) = v.as_str() {
            return vec![s.to_string()];
        }
        if let Some(arr) = v.as_array() {
            return arr
                .iter()
                .filter_map(|x| x.as_str().map(|s| s.to_string()))
                .collect();
        }
        Vec::new()
    }

    fn matches_tool(patterns: &[String], tool_name: &str) -> bool {
        for pat in patterns {
            if pat == "*" || pat == tool_name {
                return true;
            }
            if let Some(prefix) = pat.strip_suffix('*') {
                if tool_name.starts_with(prefix) {
                    return true;
                }
            }
        }
        false
    }

    fn is_read_only_tool(tool_name: &str) -> bool {
        matches!(
            tool_name,
            "read_file"
                | "view_file"
                | "read_many_files"
                | "glob"
                | "grep_search"
                | "list_directory"
                | "list_mcp_resources"
                | "read_mcp_resource"
                | "tracker_get_task"
                | "tracker_list_tasks"
                | "tracker_visualize"
                | "list_background_processes"
                | "read_background_output"
        )
    }

    fn has_shell_redirection(command: &str) -> bool {
        let mut in_single = false;
        let mut in_double = false;
        let mut escaped = false;
        for c in command.chars() {
            if escaped {
                escaped = false;
                continue;
            }
            if c == '\\' && !in_single {
                escaped = true;
                continue;
            }
            if c == '\'' && !in_double {
                in_single = !in_single;
                continue;
            }
            if c == '"' && !in_single {
                in_double = !in_double;
                continue;
            }
            if !in_single && !in_double && matches!(c, '>' | '<' | '|' | ';' | '&' | '\n' | '\r') {
                return true;
            }
        }
        false
    }

    fn has_command_substitution(command: &str) -> bool {
        let mut in_single = false;
        let mut in_double = false;
        let mut escaped = false;
        let chars: Vec<char> = command.chars().collect();
        for i in 0..chars.len() {
            let c = chars[i];
            if escaped {
                escaped = false;
                continue;
            }
            if c == '\\' && !in_single {
                escaped = true;
                continue;
            }
            if c == '\'' && !in_double {
                in_single = !in_single;
                continue;
            }
            if c == '"' && !in_single {
                in_double = !in_double;
                continue;
            }
            if !in_single {
                if c == '`' {
                    return true;
                }
                if (c == '$' || c == '<' || c == '>') && i + 1 < chars.len() && chars[i + 1] == '(' {
                    return true;
                }
            }
        }
        false
    }

    fn matches_command_prefix(cmd: &str, prefixes: &[String]) -> bool {
        let trimmed = cmd.trim_start();
        prefixes.iter().any(|pref| {
            let p = pref.trim();
            !p.is_empty()
                && (trimmed == p
                    || trimmed.starts_with(&format!("{} ", p))
                    || trimmed.starts_with(&format!("{}\t", p)))
        })
    }

    pub fn evaluate(
        &self,
        config: &AppConfig,
        tool_name: &str,
        args: &Value,
        is_mcp_tool: bool,
        mcp_server_name: Option<&str>,
    ) -> PolicyResult {
        self.evaluate_with_subagent(config, tool_name, args, is_mcp_tool, mcp_server_name, None)
    }

    pub fn evaluate_with_subagent(
        &self,
        config: &AppConfig,
        tool_name: &str,
        args: &Value,
        is_mcp_tool: bool,
        mcp_server_name: Option<&str>,
        subagent_name: Option<&str>,
    ) -> PolicyResult {
        // Explicit CLI --allowed-tools override (unless Tier-5 admin denies below)
        let cli_explicitly_allowed = config.allowed_tools.contains(tool_name);
        let current_mode = config.approval_mode.as_policy_mode();
        let args_compact = serde_json::to_string(args).unwrap_or_else(|_| "{}".to_string());
        let shell_cmd = args.get("command").and_then(|c| c.as_str()).unwrap_or("");

        // 1. Evaluate admin / TOML policy rules in (tier DESC, priority DESC) order
        let mut chosen: Option<&ParsedRule> = None;
        for rule in &self.rules {
            if config.approval_mode == ApprovalMode::Plan
                && rule.tier < 5
                && rule.modes.is_none()
                && rule.decision == PolicyDecision::Allow
                && rule.tool_patterns.iter().any(|p| p == "*")
            {
                continue;
            }
            if !Self::matches_tool(&rule.tool_patterns, tool_name) {
                continue;
            }
            if let Some(ref req_sub) = rule.subagent {
                if subagent_name != Some(req_sub.as_str()) {
                    continue;
                }
            }
            if let Some(ro) = rule.read_only_hint {
                if ro && !Self::is_read_only_tool(tool_name) {
                    continue;
                }
            }
            if let Some(ref modes) = rule.modes {
                if !modes.iter().any(|m| m.eq_ignore_ascii_case(current_mode)) {
                    continue;
                }
            }
            if let Some(req_inter) = rule.interactive {
                if req_inter != config.interactive {
                    continue;
                }
            }
            if let Some(ref req_mcp) = rule.mcp_name {
                if !is_mcp_tool {
                    continue;
                }
                if req_mcp != "*" && mcp_server_name != Some(req_mcp.as_str()) {
                    continue;
                }
            }
            if let Some(ref rx) = rule.args_regex {
                if !rx.is_match(&args_compact) {
                    continue;
                }
            }
            if !rule.command_prefixes.is_empty() && !Self::matches_command_prefix(shell_cmd, &rule.command_prefixes) {
                continue;
            }
            if let Some(ref crx) = rule.command_regex {
                if !crx.is_match(shell_cmd) {
                    continue;
                }
            }
            if (tool_name == "run_shell_command" || tool_name == "run_command") && rule.decision == PolicyDecision::Allow {
                let is_scoped_cmd = !rule.command_prefixes.is_empty()
                    || rule.command_regex.is_some()
                    || rule.args_regex.is_some();
                if Self::has_shell_redirection(shell_cmd)
                    && (rule.allow_redirection == Some(false)
                        || (is_scoped_cmd
                            && config.approval_mode != ApprovalMode::Sovereign
                            && rule.allow_redirection != Some(true)))
                    {
                        continue;
                    }
                if Self::has_command_substitution(shell_cmd) {
                    let explicit_deny = rule.allow_command_substitution == Some(false)
                        || (rule.allow_command_substitution.is_none()
                            && rule.allow_redirection == Some(false));
                    let scoped_missing_opt_in = is_scoped_cmd
                        && config.approval_mode != ApprovalMode::Sovereign
                        && rule.allow_command_substitution != Some(true);
                    let catch_all_blocked = !is_scoped_cmd
                        && config.approval_mode != ApprovalMode::Sovereign
                        && rule.allow_command_substitution != Some(true)
                        && rule.allow_redirection != Some(true);
                    if explicit_deny || scoped_missing_opt_in || catch_all_blocked {
                        continue;
                    }
                }
            }
            chosen = Some(rule);
            break;
        }

        if let Some(rule) = chosen {
            // Admin deny always overrides CLI --allowed-tools
            if rule.tier >= 5 && rule.decision == PolicyDecision::Deny {
                return PolicyResult {
                    decision: PolicyDecision::Deny,
                    reason: rule.deny_message.clone().or_else(|| {
                        Some(format!(
                            "Blocked by Tier-{} admin policy ({})",
                            rule.tier, rule.source
                        ))
                    }),
                    matched_rule: rule.name.clone().or_else(|| Some(rule.source.clone())),
                };
            }

            if cli_explicitly_allowed && rule.decision != PolicyDecision::Deny {
                if config.sandbox {
                    if let Some(block_msg) = self.check_allowed_path(config, tool_name, args) {
                        return PolicyResult {
                            decision: PolicyDecision::Deny,
                            reason: Some(block_msg),
                            matched_rule: Some("cli:--allowed-tools + sandbox".to_string()),
                        };
                    }
                }
                if let Some(block_msg) =
                    self.run_safety_checkers(config, tool_name, args, current_mode)
                {
                    return PolicyResult {
                        decision: PolicyDecision::Deny,
                        reason: Some(block_msg),
                        matched_rule: Some("cli:--allowed-tools + safety_checker".to_string()),
                    };
                }
                return PolicyResult {
                    decision: PolicyDecision::Allow,
                    reason: None,
                    matched_rule: Some("cli:--allowed-tools".to_string()),
                };
            }

            // Safety checker verification for allowed-path / conseca
            if rule.decision == PolicyDecision::Allow {
                if let Some(block_msg) =
                    self.run_safety_checkers(config, tool_name, args, current_mode)
                {
                    return PolicyResult {
                        decision: PolicyDecision::Deny,
                        reason: Some(block_msg),
                        matched_rule: Some(format!("{} + safety_checker", rule.source)),
                    };
                }
            }

            return PolicyResult {
                decision: rule.decision,
                reason: rule.deny_message.clone(),
                matched_rule: rule.name.clone().or_else(|| Some(rule.source.clone())),
            };
        }

        // Sandbox strict check if enabled
        if config.sandbox {
            if let Some(block_msg) = self.check_allowed_path(config, tool_name, args) {
                return PolicyResult {
                    decision: PolicyDecision::Deny,
                    reason: Some(block_msg),
                    matched_rule: Some("sandbox".to_string()),
                };
            }
        }

        // Mode fallback
        if cli_explicitly_allowed {
            if let Some(block_msg) = self.run_safety_checkers(config, tool_name, args, current_mode)
            {
                return PolicyResult {
                    decision: PolicyDecision::Deny,
                    reason: Some(block_msg),
                    matched_rule: Some("cli:--allowed-tools + safety_checker".to_string()),
                };
            }
            return PolicyResult {
                decision: PolicyDecision::Allow,
                reason: None,
                matched_rule: Some("cli:--allowed-tools".to_string()),
            };
        }

        match config.approval_mode {
            ApprovalMode::Sovereign => {
                if !config.interactive && tool_name == "ask_user" {
                    PolicyResult {
                        decision: PolicyDecision::Deny,
                        reason: Some("ask_user is unavailable in non-interactive mode.".to_string()),
                        matched_rule: Some("default:non-interactive".to_string()),
                    }
                } else {
                    PolicyResult {
                        decision: PolicyDecision::Allow,
                        reason: None,
                        matched_rule: Some("mode:sovereign".to_string()),
                    }
                }
            }
            ApprovalMode::Plan => {
                let read_tools = [
                    "read_file",
                    "view_file",
                    "read_many_files",
                    "glob",
                    "grep_search",
                    "list_directory",
                    "activate_skill",
                    "exit_plan_mode",
                    "list_mcp_resources",
                    "read_mcp_resource",
                ];
                if read_tools.contains(&tool_name) {
                    PolicyResult {
                        decision: PolicyDecision::Allow,
                        reason: None,
                        matched_rule: Some("mode:plan:read".to_string()),
                    }
                } else {
                    PolicyResult {
                        decision: PolicyDecision::Deny,
                        reason: Some(format!(
                            "Tool '{}' is restricted in Plan Mode.",
                            tool_name
                        )),
                        matched_rule: Some("mode:plan".to_string()),
                    }
                }
            }
            ApprovalMode::AutoEdit | ApprovalMode::Default => {
                if config.interactive {
                    PolicyResult {
                        decision: PolicyDecision::AskUser,
                        reason: None,
                        matched_rule: Some("mode:default".to_string()),
                    }
                } else {
                    PolicyResult {
                        decision: PolicyDecision::Deny,
                        reason: Some(format!(
                            "Tool '{}' requires confirmation in non-interactive mode (use --sovereign or --allowed-tools).",
                            tool_name
                        )),
                        matched_rule: Some("mode:non-interactive".to_string()),
                    }
                }
            }
        }
    }

    fn run_safety_checkers(
        &self,
        config: &AppConfig,
        tool_name: &str,
        args: &Value,
        current_mode: &str,
    ) -> Option<String> {
        // Explicit --sandbox enforces path boundary on file mutations/reads
        if config.sandbox {
            if let Some(msg) = self.check_allowed_path(config, tool_name, args) {
                return Some(msg);
            }
        }

        for sc in &self.safety_checkers {
            if !Self::matches_tool(&sc.tool_patterns, tool_name) {
                continue;
            }
            if let Some(ref modes) = sc.modes {
                if !modes.iter().any(|m| m.eq_ignore_ascii_case(current_mode)) {
                    continue;
                }
            }
            if sc.checker_name == "allowed-path"
                && !config.skip_trust
                && config.approval_mode != ApprovalMode::Sovereign
            {
                if let Some(msg) = self.check_allowed_path(config, tool_name, args) {
                    return Some(msg);
                }
            } else if sc.checker_name == "conseca" {
                // ConSeca secret guard: prevent writing/exfiltrating gha-creds or raw credential vaults
                let compact = args.to_string();
                if compact.contains("gha-creds-") && compact.contains(".json") {
                    return Some("Access to CI credentials file is denied by safety policy.".to_string());
                }
            }
        }
        None
    }

    fn check_allowed_path(
        &self,
        config: &AppConfig,
        tool_name: &str,
        args: &Value,
    ) -> Option<String> {
        let fs_tool = matches!(
            tool_name,
            "write_file"
                | "write_to_file"
                | "replace"
                | "replace_file_content"
                | "read_file"
                | "view_file"
                | "read_many_files"
                | "list_directory"
                | "glob"
                | "grep_search"
        );
        if !fs_tool {
            return None;
        }
        for key in &["file_path", "TargetFile", "AbsolutePath", "path", "dir_path", "directory", "target_file"] {
            if let Some(p_str) = args.get(*key).and_then(|v| v.as_str()) {
                let p = Path::new(p_str);
                if !config.is_path_in_workspace(p) {
                    return Some(format!(
                        "Path not in workspace: '{}' resolves outside allowed directories.",
                        p_str
                    ));
                }
            }
        }
        for arr_key in &["paths", "include"] {
            if let Some(arr) = args.get(*arr_key).and_then(|v| v.as_array()) {
                for item in arr {
                    if let Some(p_str) = item.as_str() {
                        if !p_str.contains('*') && !p_str.contains('?') {
                            let p = Path::new(p_str);
                            if !config.is_path_in_workspace(p) {
                                return Some(format!(
                                    "Path not in workspace: '{}' resolves outside allowed directories.",
                                    p_str
                                ));
                            }
                        }
                    }
                }
            }
        }
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::CliOverrides;
    use serde_json::json;

    #[test]
    fn test_sovereign_policy_allows_tools_except_noninteractive_ask() {
        let mut ov = CliOverrides::default();
        ov.sovereign = true;
        ov.interactive = false;
        let cfg = AppConfig::build(ov);
        let eng = PolicyEngine::load(&cfg);

        let r1 = eng.evaluate(&cfg, "read_file", &json!({"file_path": "/etc/os-release"}), false, None);
        assert_eq!(r1.decision, PolicyDecision::Allow);

        let r2 = eng.evaluate(&cfg, "ask_user", &json!({"questions": []}), false, None);
        assert_eq!(r2.decision, PolicyDecision::Deny);
    }

    #[test]
    fn test_plan_mode_blocks_arbitrary_write_allows_plan_md() {
        let mut ov = CliOverrides::default();
        ov.approval_mode = Some("plan".to_string());
        ov.interactive = false;
        let cfg = AppConfig::build(ov);
        let eng = PolicyEngine::load(&cfg);

        let r_src = eng.evaluate(&cfg, "write_file", &json!({"file_path": "src/main.rs"}), false, None);
        assert_eq!(r_src.decision, PolicyDecision::Deny);

        let r_plan = eng.evaluate(&cfg, "write_file", &json!({"file_path": "plans/architecture.md"}), false, None);
        assert_eq!(r_plan.decision, PolicyDecision::Allow);
    }

    #[test]
    fn test_redirection_command_substitution_and_prefix_rules() {
        assert!(PolicyEngine::has_shell_redirection("echo hi > out.txt"));
        assert!(PolicyEngine::has_shell_redirection("ls | grep foo"));
        assert!(PolicyEngine::has_shell_redirection("git status & rm -rf /tmp/x"));
        assert!(PolicyEngine::has_shell_redirection("git status\nrm -rf /tmp/x"));
        assert!(!PolicyEngine::has_shell_redirection("echo 'a > b'"));
        assert!(PolicyEngine::has_command_substitution("echo $(whoami)"));
        assert!(PolicyEngine::has_command_substitution("echo \"'$(whoami)'\""));
        assert!(!PolicyEngine::has_command_substitution("echo '$(whoami)'"));
        assert!(PolicyEngine::matches_command_prefix("git status -sb", &["git status".to_string()]));
        assert!(!PolicyEngine::matches_command_prefix("git_status_fake", &["git status".to_string()]));
    }

    #[test]
    fn test_sovereign_allows_subst_and_scoped_prefix_blocks_redirection_and_subst() {
        let mut ov = CliOverrides::default();
        ov.sovereign = true;
        ov.interactive = false;
        let sov_cfg = AppConfig::build(ov);
        let sov_eng = PolicyEngine::load(&sov_cfg);
        let sov_res = sov_eng.evaluate(
            &sov_cfg,
            "run_shell_command",
            &json!({"command": "echo $(date) > /tmp/ok.txt"}),
            false,
            None,
        );
        assert_eq!(sov_res.decision, PolicyDecision::Allow);

        // Isolated TOML rule test with commandPrefix + allowRedirection = false in Default mode
        let tmp_toml = std::env::temp_dir().join(format!("flowork_pol_test_{}.toml", uuid::Uuid::new_v4()));
        fs::write(
            &tmp_toml,
            "[[rule]]\ntoolName = \"run_shell_command\"\ncommandPrefix = \"git status\"\ndecision = \"allow\"\nallowRedirection = false\npriority = 100\n",
        )
        .unwrap();
        let mut rules = Vec::new();
        let mut checkers = Vec::new();
        PolicyEngine::parse_file(&tmp_toml, 2, &mut rules, &mut checkers);
        let _ = fs::remove_file(&tmp_toml);

        let isolated = PolicyEngine {
            rules,
            safety_checkers: checkers,
        };
        let mut def_ov = CliOverrides::default();
        def_ov.approval_mode = Some("default".to_string());
        def_ov.interactive = true;
        let mut def_cfg = AppConfig::build(def_ov);
        def_cfg.approval_mode = ApprovalMode::Default;

        let ok = isolated.evaluate(&def_cfg, "run_shell_command", &json!({"command": "git status -s"}), false, None);
        assert_eq!(ok.decision, PolicyDecision::Allow);

        let redir = isolated.evaluate(&def_cfg, "run_shell_command", &json!({"command": "git status > /tmp/x"}), false, None);
        assert_eq!(redir.decision, PolicyDecision::AskUser);

        let bg_op = isolated.evaluate(&def_cfg, "run_shell_command", &json!({"command": "git status & id"}), false, None);
        assert_eq!(bg_op.decision, PolicyDecision::AskUser);

        let subst = isolated.evaluate(&def_cfg, "run_shell_command", &json!({"command": "git status $(whoami)"}), false, None);
        assert_eq!(subst.decision, PolicyDecision::AskUser);
    }

    #[test]
    fn test_sandbox_blocks_list_directory_and_cli_allow_outside_workspace() {
        let mut ov = CliOverrides::default();
        ov.sandbox = true;
        ov.sovereign = true;
        ov.allowed_tools = vec!["list_directory".to_string()];
        let cfg = AppConfig::build(ov);
        let eng = PolicyEngine::load(&cfg);
        let denied = eng.evaluate(&cfg, "list_directory", &json!({"path": "/etc"}), false, None);
        assert_eq!(denied.decision, PolicyDecision::Deny);
    }
}
