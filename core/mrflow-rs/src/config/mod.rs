use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{HashMap, HashSet};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ApprovalMode {
    Default,
    AutoEdit,
    Sovereign,
    Plan,
}

impl ApprovalMode {
    pub fn from_str_lossy(s: &str) -> Self {
        match s.trim().to_ascii_lowercase().as_str() {
            "sovereign" | "yolo" => Self::Sovereign,
            "auto_edit" | "autoedit" => Self::AutoEdit,
            "plan" => Self::Plan,
            _ => Self::Default,
        }
    }

    pub fn as_policy_mode(&self) -> &'static str {
        match self {
            Self::Default => "default",
            Self::AutoEdit => "autoEdit",
            Self::Sovereign => "sovereign",
            Self::Plan => "plan",
        }
    }

    pub fn display_label(&self) -> &'static str {
        match self {
            Self::Default => "DEFAULT",
            Self::AutoEdit => "AUTO_EDIT",
            Self::Sovereign => "SOVEREIGN",
            Self::Plan => "PLAN",
        }
    }

    pub fn cycle_next(&self) -> Self {
        match self {
            Self::Default => Self::AutoEdit,
            Self::AutoEdit => Self::Sovereign,
            Self::Sovereign => Self::Plan,
            Self::Plan => Self::Default,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OutputFormat {
    Text,
    Json,
    StreamJson,
}

impl OutputFormat {
    pub fn from_str_lossy(s: &str) -> Self {
        match s.trim().to_ascii_lowercase().as_str() {
            "stream-json" | "stream_json" => Self::StreamJson,
            "json" => Self::Json,
            _ => Self::Text,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct McpServerConfig {
    pub command: Option<String>,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub env: HashMap<String, String>,
    pub cwd: Option<String>,
    pub url: Option<String>,
    #[serde(rename = "httpUrl")]
    pub http_url: Option<String>,
    #[serde(rename = "type")]
    pub transport_type: Option<String>,
    #[serde(default)]
    pub headers: HashMap<String, String>,
    pub timeout: Option<u64>,
    #[serde(default)]
    pub trust: bool,
    #[serde(default, rename = "includeTools")]
    pub include_tools: Vec<String>,
    #[serde(default, rename = "excludeTools")]
    pub exclude_tools: Vec<String>,
    pub description: Option<String>,
    #[serde(default)]
    pub disabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct UserSettings {
    #[serde(default)]
    pub general: Value,
    #[serde(default, rename = "mcpServers")]
    pub mcp_servers: HashMap<String, McpServerConfig>,
    #[serde(default)]
    pub security: Value,
    #[serde(default, rename = "disabledSkills")]
    pub disabled_skills: Vec<String>,
    #[serde(default, rename = "disabledMcpServers")]
    pub disabled_mcp_servers: Vec<String>,
    #[serde(default, rename = "disabledExtensions")]
    pub disabled_extensions: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct AppPaths {
    pub home_dir: PathBuf,
    pub flowork_root: PathBuf,
    pub user_flowork_dir: PathBuf,
    pub history_chats_dir: PathBuf,
    pub checkpoints_dir: PathBuf,
    pub prompts_dir: PathBuf,
    pub passive_system_dir: PathBuf,
    pub tools_dir: PathBuf,
    pub skills_dirs: Vec<PathBuf>,
    pub mcp_dir: PathBuf,
    pub policies_dirs: Vec<PathBuf>,
    pub agents_dirs: Vec<PathBuf>,
    pub screenshots_dir: PathBuf,
    pub user_screenshots_dir: PathBuf,
    pub system_md_override: Option<PathBuf>,
}

#[derive(Debug, Clone)]
pub struct AppConfig {
    pub cwd: PathBuf,
    pub model: String,
    pub connector_url: String,
    pub api_key: String,
    pub approval_mode: ApprovalMode,
    pub interactive: bool,
    pub debug: bool,
    pub sandbox: bool,
    pub skip_trust: bool,
    pub raw_output: bool,
    #[allow(dead_code)]
    pub accept_raw_output_risk: bool,
    #[allow(dead_code)]
    pub screen_reader: bool,
    pub output_format: OutputFormat,
    pub max_turns: usize,
    pub subagent_max_turns: usize,
    pub loop_threshold: usize,
    pub content_loop_threshold: usize,
    #[allow(dead_code)]
    pub llm_check_after_turns: usize,
    #[allow(dead_code)]
    pub llm_check_interval: usize,
    pub include_directories: Vec<PathBuf>,
    pub extra_policy_paths: Vec<PathBuf>,
    pub extra_admin_policy_paths: Vec<PathBuf>,
    pub allowed_mcp_server_names: Option<HashSet<String>>,
    pub allowed_tools: HashSet<String>,
    #[allow(dead_code)]
    pub extensions: Vec<String>,
    pub session_id: Option<String>,
    pub resume: Option<String>,
    pub session_file: Option<PathBuf>,
    pub paths: AppPaths,
    pub settings: UserSettings,
}

pub fn parse_env_file(path: &Path) -> HashMap<String, String> {
    let mut map = HashMap::new();
    let Ok(content) = fs::read_to_string(path) else {
        return map;
    };
    for raw_line in content.lines() {
        let mut line = raw_line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some(rest) = line.strip_prefix("export ") {
            line = rest.trim();
        }
        if let Some((k, v)) = line.split_once('=') {
            let key = k.trim().to_string();
            let val = v.trim();
            let unquoted = if (val.starts_with('"') && val.ends_with('"') && val.len() >= 2)
                || (val.starts_with('\'') && val.ends_with('\'') && val.len() >= 2)
            {
                val[1..val.len() - 1].to_string()
            } else {
                val.to_string()
            };
            if !key.is_empty() {
                map.insert(key, unquoted);
            }
        }
    }
    map
}

pub fn detect_connector_default_model(flowork_root: &Path) -> String {
    let models_path = flowork_root.join("connector/config/models.json");
    if let Ok(raw) = fs::read_to_string(&models_path) {
        if let Ok(v) = serde_json::from_str::<Value>(&raw) {
            if let Some(m) = v.get("default_model").and_then(|s| s.as_str()) {
                if !m.trim().is_empty() {
                    return m.trim().to_string();
                }
            }
        }
    }
    "gemini-3.8-flash-high".to_string()
}

pub fn load_settings(user_flowork_dir: &Path) -> UserSettings {
    let path = user_flowork_dir.join("settings.json");
    if let Ok(raw) = fs::read_to_string(&path) {
        if let Ok(parsed) = serde_json::from_str::<UserSettings>(&raw) {
            return parsed;
        }
    }
    UserSettings::default()
}

pub fn save_settings(user_flowork_dir: &Path, settings: &UserSettings) -> Result<(), String> {
    fs::create_dir_all(user_flowork_dir).map_err(|e| e.to_string())?;
    let path = user_flowork_dir.join("settings.json");
    let json = serde_json::to_string_pretty(settings).map_err(|e| e.to_string())?;
    fs::write(path, json).map_err(|e| e.to_string())
}

pub fn resolve_project_slug(cwd: &Path, user_flowork_dir: &Path) -> String {
    let projects_path = user_flowork_dir.join("projects.json");
    let canon_cwd = fs::canonicalize(cwd).unwrap_or_else(|_| cwd.to_path_buf());
    let cwd_str = canon_cwd.to_string_lossy().to_string();

    if let Ok(raw) = fs::read_to_string(&projects_path) {
        if let Ok(v) = serde_json::from_str::<Value>(&raw) {
            if let Some(map) = v.get("projects").and_then(|p| p.as_object()) {
                if let Some(slug) = map.get(&cwd_str).and_then(|s| s.as_str()) {
                    if !slug.is_empty() {
                        return slug.to_string();
                    }
                }
                // Longest prefix match inside projects.json
                let mut best: Option<(usize, String)> = None;
                for (proj_path, slug_val) in map {
                    if cwd_str == *proj_path
                        || cwd_str.starts_with(&format!("{}/", proj_path.trim_end_matches('/')))
                    {
                        if let Some(slug) = slug_val.as_str() {
                            if best.as_ref().map(|b| proj_path.len() > b.0).unwrap_or(true) {
                                best = Some((proj_path.len(), slug.to_string()));
                            }
                        }
                    }
                }
                if let Some((_, slug)) = best {
                    return slug;
                }
            }
        }
    }

    canon_cwd
        .file_name()
        .and_then(|n| n.to_str())
        .map(|s| {
            s.chars()
                .map(|c| {
                    if c.is_ascii_alphanumeric() || c == '-' || c == '_' {
                        c
                    } else {
                        '-'
                    }
                })
                .collect()
        })
        .filter(|s: &String| !s.is_empty())
        .unwrap_or_else(|| "default".to_string())
}

pub fn session_tool_outputs_dir(config: &AppConfig, session_id: &str) -> PathBuf {
    let slug = resolve_project_slug(&config.cwd, &config.paths.user_flowork_dir);
    let short8: String = session_id
        .chars()
        .filter(|c| c.is_ascii_alphanumeric() || *c == '-' || *c == '_')
        .take(12)
        .collect();
    let folder = if short8.is_empty() {
        "session-active".to_string()
    } else {
        format!("session-{}", short8)
    };
    config
        .paths
        .user_flowork_dir
        .join("tmp")
        .join(slug)
        .join("tool-outputs")
        .join(folder)
}

#[derive(Debug, Clone, Default)]
pub struct CliOverrides {
    pub model: Option<String>,
    pub sovereign: bool,
    pub approval_mode: Option<String>,
    pub interactive: bool,
    pub debug: bool,
    pub sandbox: bool,
    pub skip_trust: bool,
    pub raw_output: bool,
    pub accept_raw_output_risk: bool,
    pub screen_reader: bool,
    pub output_format: Option<String>,
    pub include_directories: Vec<PathBuf>,
    pub policy: Vec<PathBuf>,
    pub admin_policy: Vec<PathBuf>,
    pub allowed_mcp_server_names: Option<Vec<String>>,
    pub allowed_tools: Vec<String>,
    pub extensions: Vec<String>,
    pub session_id: Option<String>,
    pub resume: Option<String>,
    pub session_file: Option<PathBuf>,
}

impl AppConfig {
    pub fn build(overrides: CliOverrides) -> Self {
        let cwd = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        let home_dir = dirs::home_dir()
            .or_else(|| env::var("HOME").ok().map(PathBuf::from))
            .unwrap_or_else(|| PathBuf::from("/tmp"));

        let flowork_root = env::var("FLOWORK_OS_ROOT")
            .ok()
            .filter(|s| !s.is_empty())
            .map(PathBuf::from)
            .or_else(|| {
                let home_root = home_dir.join("floworkos");
                if home_root.is_dir() {
                    Some(home_root)
                } else {
                    Some(PathBuf::from("/opt/floworkos"))
                }
            })
            .unwrap_or_else(|| PathBuf::from("/opt/floworkos"));

        let user_flowork_dir = home_dir.join(".flowork");

        // Cascading env: Fallback -> /opt/floworkos/system/mrflow.env -> process env -> ~/.flowork/mrflow.env -> CLI
        let sys_env = parse_env_file(&flowork_root.join("system/mrflow.env"));
        let user_env = parse_env_file(&user_flowork_dir.join("mrflow.env"));

        let resolve_var = |keys: &[&str], default: &str| -> String {
            for k in keys {
                if let Some(v) = user_env.get(*k) {
                    if !v.is_empty() {
                        return v.clone();
                    }
                }
            }
            for k in keys {
                if let Ok(v) = env::var(*k) {
                    if !v.is_empty() {
                        return v;
                    }
                }
            }
            for k in keys {
                if let Some(v) = sys_env.get(*k) {
                    if !v.is_empty() {
                        return v.clone();
                    }
                }
            }
            default.to_string()
        };

        let resolve_usize = |keys: &[&str], default: usize| -> usize {
            resolve_var(keys, &default.to_string())
                .parse::<usize>()
                .unwrap_or(default)
        };

        let settings = load_settings(&user_flowork_dir);

        let default_mode_from_settings = settings
            .general
            .get("defaultApprovalMode")
            .and_then(|v| v.as_str())
            .unwrap_or("sovereign");

        let mut approval_mode = if overrides.sovereign {
            ApprovalMode::Sovereign
        } else if let Some(ref m) = overrides.approval_mode {
            ApprovalMode::from_str_lossy(m)
        } else {
            ApprovalMode::from_str_lossy(default_mode_from_settings)
        };

        // Ensure interactive=false non-interactive runs with --sovereign behave consistently
        if overrides.sovereign {
            approval_mode = ApprovalMode::Sovereign;
        }

        let default_model = detect_connector_default_model(&flowork_root);
        let model = overrides
            .model
            .filter(|m| !m.trim().is_empty())
            .unwrap_or_else(|| resolve_var(&["FLOWORK_MODEL", "MRFLOW_MODEL"], &default_model));

        let connector_url = resolve_var(
            &["FLOWORK_CONNECTOR_URL", "GOOGLE_GEMINI_BASE_URL"],
            "http://127.0.0.1:9099",
        );
        let api_key = resolve_var(&["FLOWORK_API_KEY"], "flowork-sovereign-token");

        let trust_env = resolve_var(
            &["FLOWORK_TRUST_WORKSPACE", "FLOWORK_CLI_TRUST_WORKSPACE"],
            "true",
        );
        let skip_trust = overrides.skip_trust || trust_env.eq_ignore_ascii_case("true");

        let history_chats_dir = env::var("FLOWORK_HISTORY_DIR")
            .ok()
            .filter(|s| !s.is_empty())
            .map(PathBuf::from)
            .unwrap_or_else(|| user_flowork_dir.join("history/chats"));

        let checkpoints_dir = user_flowork_dir.join("history/checkpoints");
        let prompts_dir = env::var("FLOWORK_PROMPTS_DIR")
            .ok()
            .filter(|s| !s.is_empty())
            .map(PathBuf::from)
            .unwrap_or_else(|| flowork_root.join("system/system_promp/promps"));
        let passive_system_dir = flowork_root.join("system/system_promp");
        let tools_dir = flowork_root.join("tools");
        let skills_dirs = vec![
            flowork_root.join("skills"),
            user_flowork_dir.join("skills"),
            cwd.join(".flowork/skills"),
        ];
        let mcp_dir = flowork_root.join("mcp");
        let policies_dirs = vec![
            flowork_root.join("policies"),
            cwd.join(".flowork/policies"),
            user_flowork_dir.join("policies"),
            PathBuf::from("/etc/flowork/policies"),
        ];
        let agents_dirs = vec![
            flowork_root.join("agents"),
            user_flowork_dir.join("agents"),
            cwd.join(".flowork/agents"),
        ];

        let system_md_override = resolve_var(&["FLOWORK_SYSTEM_MD"], "")
            .trim()
            .is_empty()
            .then(|| None)
            .unwrap_or_else(|| Some(PathBuf::from(resolve_var(&["FLOWORK_SYSTEM_MD"], ""))));

        let paths = AppPaths {
            home_dir: home_dir.clone(),
            flowork_root: flowork_root.clone(),
            user_flowork_dir,
            history_chats_dir,
            checkpoints_dir,
            prompts_dir,
            passive_system_dir,
            tools_dir,
            skills_dirs,
            mcp_dir,
            policies_dirs,
            agents_dirs,
            screenshots_dir: flowork_root.join("screenshots"),
            user_screenshots_dir: home_dir.join("Pictures/Screenshots"),
            system_md_override,
        };

        let output_format = overrides
            .output_format
            .as_deref()
            .map(OutputFormat::from_str_lossy)
            .unwrap_or(OutputFormat::Text);

        let allowed_mcp_server_names = overrides
            .allowed_mcp_server_names
            .map(|v| v.into_iter().collect());

        Self {
            cwd,
            model,
            connector_url,
            api_key,
            approval_mode,
            interactive: overrides.interactive,
            debug: overrides.debug,
            sandbox: overrides.sandbox,
            skip_trust,
            raw_output: overrides.raw_output,
            accept_raw_output_risk: overrides.accept_raw_output_risk,
            screen_reader: overrides.screen_reader,
            output_format,
            max_turns: resolve_usize(&["FLOWORK_MAX_TURNS"], 300),
            subagent_max_turns: resolve_usize(&["FLOWORK_SUBAGENT_MAX_TURNS"], 300),
            loop_threshold: resolve_usize(&["FLOWORK_LOOP_THRESHOLD"], 5),
            content_loop_threshold: resolve_usize(&["FLOWORK_CONTENT_LOOP_THRESHOLD"], 10),
            llm_check_after_turns: resolve_usize(&["FLOWORK_LLM_CHECK_AFTER_TURNS"], 30),
            llm_check_interval: resolve_usize(&["FLOWORK_LLM_CHECK_INTERVAL"], 10),
            include_directories: overrides.include_directories,
            extra_policy_paths: overrides.policy,
            extra_admin_policy_paths: overrides.admin_policy,
            allowed_mcp_server_names,
            allowed_tools: overrides.allowed_tools.into_iter().collect(),
            extensions: overrides.extensions,
            session_id: overrides.session_id,
            resume: overrides.resume,
            session_file: overrides.session_file,
            paths,
            settings,
        }
    }

    pub fn allowed_workspace_roots(&self) -> Vec<PathBuf> {
        let mut roots = vec![
            self.cwd.clone(),
            self.paths.screenshots_dir.clone(),
            self.paths.user_screenshots_dir.clone(),
            self.paths.user_flowork_dir.join("tmp"),
        ];
        if !self.sandbox {
            roots.push(self.paths.flowork_root.clone());
            roots.push(PathBuf::from("/tmp"));
        } else if let Ok(tmpdir) = std::env::var("TMPDIR") {
            let p = PathBuf::from(tmpdir.trim());
            if !p.as_os_str().is_empty() && p != Path::new("/tmp") {
                roots.push(p);
            }
        }
        roots.extend(self.include_directories.iter().cloned());
        roots
    }

    pub fn is_path_in_workspace(&self, target: &Path) -> bool {
        let abs = if target.is_absolute() {
            target.to_path_buf()
        } else {
            self.cwd.join(target)
        };
        let resolved = fs::canonicalize(&abs).unwrap_or_else(|_| {
            // Canonicalize parent directory if file doesn't exist yet
            if let Some(parent) = abs.parent() {
                if let Ok(p) = fs::canonicalize(parent) {
                    if let Some(name) = abs.file_name() {
                        return p.join(name);
                    }
                }
            }
            abs.clone()
        });

        for root in self.allowed_workspace_roots() {
            let root_res = fs::canonicalize(&root).unwrap_or(root);
            if resolved == root_res || resolved.starts_with(&root_res) {
                return true;
            }
        }
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_env_cascade_defaults() {
        let cfg = AppConfig::build(CliOverrides::default());
        assert_eq!(cfg.max_turns, 300);
        assert_eq!(cfg.subagent_max_turns, 300);
        assert_eq!(cfg.loop_threshold, 5);
        assert!(!cfg.connector_url.is_empty());
    }

    #[test]
    fn test_approval_mode_parsing() {
        assert_eq!(ApprovalMode::from_str_lossy("sovereign"), ApprovalMode::Sovereign);
        assert_eq!(ApprovalMode::from_str_lossy("yolo"), ApprovalMode::Sovereign);
        assert_eq!(ApprovalMode::from_str_lossy("auto_edit"), ApprovalMode::AutoEdit);
        assert_eq!(ApprovalMode::from_str_lossy("plan"), ApprovalMode::Plan);
    }
}
