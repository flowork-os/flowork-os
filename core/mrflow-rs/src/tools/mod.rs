use crate::cognitive::{discover_skills, is_manifest_tool_active, SkillMeta, SniffedContext};
use crate::config::{AppConfig, ApprovalMode};
use crate::inference::{InlineBlob, ToolDeclaration};
use crate::mcp::{inject_intercept_gate_fields, McpManager};
use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use glob::Pattern;
use ignore::WalkBuilder;
use regex::RegexBuilder;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::future::Future;
use std::path::PathBuf;
use std::pin::Pin;
use std::process::Stdio;
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWriteExt};
use tokio::process::{Child, Command};
use tokio::sync::Mutex;
use tokio::time::timeout;

const MAX_TOOL_OUTPUT_CHARS: usize = crate::context::DEFAULT_MAX_TOOL_OUTPUT_CHARS;

pub type SubagentFuture = Pin<Box<dyn Future<Output = ToolExecOutcome> + Send>>;
pub trait SubagentSpawner: Send + Sync {
    fn spawn_subagent(&self, agent_name: String, task: String) -> SubagentFuture;
}

pub type AskUserFuture = Pin<Box<dyn Future<Output = Result<Value, String>> + Send>>;
pub trait InteractiveUiBridge: Send + Sync {
    fn ask_user(&self, questions: Value) -> AskUserFuture;
    fn request_plan_mode(&self, enter: bool, reason: String) -> AskUserFuture;
}

#[derive(Debug, Clone)]
pub struct ToolExecOutcome {
    pub success: bool,
    pub output_json: Value,
    pub display_text: String,
    pub inline_blobs: Vec<InlineBlob>,
    pub refreshed_mode: Option<ApprovalMode>,
    pub needs_tool_rescan: bool,
}

impl ToolExecOutcome {
    pub fn ok_json(val: Value, display: impl Into<String>) -> Self {
        Self {
            success: true,
            output_json: val,
            display_text: display.into(),
            inline_blobs: Vec::new(),
            refreshed_mode: None,
            needs_tool_rescan: false,
        }
    }

    pub fn err(msg: impl Into<String>) -> Self {
        let m = msg.into();
        Self {
            success: false,
            output_json: json!({ "error": m }),
            display_text: m,
            inline_blobs: Vec::new(),
            refreshed_mode: None,
            needs_tool_rescan: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackgroundProcessInfo {
    pub id: String,
    pub pid: u32,
    pub command: String,
    pub log_path: PathBuf,
    pub started_at: u64,
    pub running: bool,
}

#[derive(Default)]
pub struct ProcessRegistry {
    bg: HashMap<String, BackgroundProcessInfo>,
    active_fg_pgids: HashSet<i32>,
}

impl ProcessRegistry {
    pub fn register_fg(&mut self, pgid: i32) {
        self.active_fg_pgids.insert(pgid);
    }

    pub fn unregister_fg(&mut self, pgid: i32) {
        self.active_fg_pgids.remove(&pgid);
    }

    pub fn kill_all_active(&mut self) {
        #[cfg(unix)]
        {
            for &pgid in &self.active_fg_pgids {
                unsafe {
                    libc::kill(-pgid, libc::SIGTERM);
                    libc::kill(-pgid, libc::SIGKILL);
                }
            }
            for info in self.bg.values_mut() {
                if info.running {
                    unsafe {
                        libc::kill(-(info.pid as i32), libc::SIGTERM);
                    }
                    info.running = false;
                }
            }
        }
        self.active_fg_pgids.clear();
    }
}

#[derive(Debug, Clone)]
pub struct LoadedManifestTool {
    pub name: String,
    pub description: String,
    pub parameters_schema: Value,
    pub dir: PathBuf,
    pub manifest_raw: Value,
    pub entrypoint: Option<String>,
    pub skill_file: Option<PathBuf>,
    pub keywords: Vec<String>,
}

pub struct ToolRegistry {
    pub config: Arc<Mutex<AppConfig>>,
    pub mcp: Arc<McpManager>,
    pub proc_reg: Arc<Mutex<ProcessRegistry>>,
    pub manifest_tools: HashMap<String, LoadedManifestTool>,
    pub activated_tool_skills: Mutex<HashSet<String>>,
    pub is_subagent: bool,
    pub offload_dir: Option<PathBuf>,
    pub subagent_spawner: Option<Arc<dyn SubagentSpawner>>,
    pub ui_bridge: Option<Arc<dyn InteractiveUiBridge>>,
}

impl ToolRegistry {
    pub fn new(
        config: Arc<Mutex<AppConfig>>,
        mcp: Arc<McpManager>,
        proc_reg: Arc<Mutex<ProcessRegistry>>,
        is_subagent: bool,
    ) -> Self {
        let mut reg = Self {
            config,
            mcp,
            proc_reg,
            manifest_tools: HashMap::new(),
            activated_tool_skills: Mutex::new(HashSet::new()),
            is_subagent,
            offload_dir: None,
            subagent_spawner: None,
            ui_bridge: None,
        };
        reg.rescan_disk_manifests_blocking();
        reg
    }

    pub fn set_offload_dir(&mut self, dir: PathBuf) {
        self.offload_dir = Some(dir);
    }

    pub fn set_subagent_spawner(&mut self, spawner: Arc<dyn SubagentSpawner>) {
        self.subagent_spawner = Some(spawner);
    }

    pub fn set_ui_bridge(&mut self, bridge: Arc<dyn InteractiveUiBridge>) {
        self.ui_bridge = Some(bridge);
    }

    pub fn build_execution_path(cfg: &AppConfig) -> String {
        let cur_path = std::env::var("PATH").unwrap_or_default();
        let flowork_bin = cfg.paths.flowork_root.join("bin");
        let cargo_bin = cfg.paths.home_dir.join(".cargo/bin");
        let local_bin = cfg.paths.home_dir.join(".local/bin");
        let usr_local_bin = PathBuf::from("/usr/local/bin");
        let mut path_entries = Vec::new();
        if flowork_bin.is_dir() {
            path_entries.push(flowork_bin.to_string_lossy().to_string());
        }
        if cargo_bin.is_dir() {
            path_entries.push(cargo_bin.to_string_lossy().to_string());
        }
        if local_bin.is_dir() {
            path_entries.push(local_bin.to_string_lossy().to_string());
        }
        if usr_local_bin.is_dir() {
            path_entries.push(usr_local_bin.to_string_lossy().to_string());
        }
        if !cur_path.is_empty() {
            path_entries.push(cur_path);
        }
        path_entries.join(":")
    }

    fn format_large_output(&self, tool_name: &str, call_id: &str, text: &str) -> String {
        if let Some(ref dir) = self.offload_dir {
            crate::context::truncate_and_offload_output(
                text,
                MAX_TOOL_OUTPUT_CHARS,
                tool_name,
                if call_id.is_empty() { tool_name } else { call_id },
                Some(dir.as_path()),
            )
        } else {
            truncate_output(text)
        }
    }

    pub fn rescan_disk_manifests_blocking(&mut self) {
        let scan_dirs = if let Ok(cfg) = self.config.try_lock() {
            vec![
                cfg.paths.tools_dir.clone(),
                cfg.paths.user_flowork_dir.join("tools"),
                cfg.cwd.join(".flowork/tools"),
            ]
        } else {
            vec![PathBuf::from("/opt/floworkos/tools")]
        };

        let mut map = HashMap::new();
        for tools_dir in scan_dirs {
            let Ok(entries) = fs::read_dir(&tools_dir) else {
                continue;
            };
            for entry in entries.flatten() {
                let p = entry.path();
                if !p.is_dir() {
                    continue;
                }
                let mf = p.join("manifest.json");
                if !mf.is_file() {
                    continue;
                }
                let Ok(raw) = fs::read_to_string(&mf) else {
                    continue;
                };
                let Ok(val) = serde_json::from_str::<Value>(&raw) else {
                    continue;
                };
                let Some(name) = val.get("name").and_then(|s| s.as_str()).map(str::to_string) else {
                    continue;
                };
                let Some(desc) = val.get("description").and_then(|s| s.as_str()).map(str::to_string) else {
                    continue;
                };
                let mut schema = val
                    .get("parametersJsonSchema")
                    .or_else(|| val.get("parameters"))
                    .cloned()
                    .unwrap_or_else(|| json!({ "type": "object", "properties": {}, "required": [] }));
                inject_intercept_gate_fields(&mut schema);

                let entrypoint = val
                    .get("entrypoint")
                    .or_else(|| val.get("runner"))
                    .and_then(|s| s.as_str())
                    .map(str::to_string);
                let skill_rel = val.get("skill").and_then(|s| s.as_str()).unwrap_or("SKILL.md");
                let skill_candidate = p.join(skill_rel);
                let skill_file = skill_candidate.is_file().then_some(skill_candidate);

                let mut keywords: Vec<String> = val
                    .get("triggers")
                    .and_then(|t| t.get("keywords"))
                    .and_then(|a| a.as_array())
                    .map(|arr| {
                        arr.iter()
                            .filter_map(|x| x.as_str().map(str::to_string))
                            .collect()
                    })
                    .unwrap_or_default();
                if let Some(top_kws) = val.get("keywords").and_then(|a| a.as_array()) {
                    for k in top_kws {
                        if let Some(s) = k.as_str() {
                            if !keywords.iter().any(|existing| existing == s) {
                                keywords.push(s.to_string());
                            }
                        }
                    }
                }

                map.insert(
                    name.clone(),
                    LoadedManifestTool {
                        name,
                        description: desc,
                        parameters_schema: schema,
                        dir: p,
                        manifest_raw: val,
                        entrypoint,
                        skill_file,
                        keywords,
                    },
                );
            }
        }
        self.manifest_tools = map;
    }

    pub async fn active_declarations(&self, sniffed: &SniffedContext) -> Vec<ToolDeclaration> {
        let mut decls = Vec::new();
        let mut seen = HashSet::new();

        // 1. Manifest-backed tools filtered by ContextSniffer rules (`always` / `conditional`)
        let mut keys: Vec<&String> = self.manifest_tools.keys().collect();
        keys.sort();
        for name in keys {
            if self.is_subagent && name == "invoke_agent" {
                continue;
            }
            let tool = &self.manifest_tools[name];
            if !is_manifest_tool_active(&tool.manifest_raw, sniffed) {
                continue;
            }
            seen.insert(name.clone());
            decls.push(ToolDeclaration {
                name: tool.name.clone(),
                description: tool.description.clone(),
                parameters_json_schema: tool.parameters_schema.clone(),
            });
        }

        // 2. Ensure core native tools exist even if a disk manifest directory is absent
        for (core_name, core_desc, mut core_schema) in core_fallback_definitions() {
            if self.is_subagent && core_name == "invoke_agent" {
                continue;
            }
            if seen.insert(core_name.to_string()) {
                inject_intercept_gate_fields(&mut core_schema);
                decls.push(ToolDeclaration {
                    name: core_name.to_string(),
                    description: core_desc.to_string(),
                    parameters_json_schema: core_schema,
                });
            }
        }

        // 3. Connected MCP tools (JIT intent-filtered)
        for mcp_decl in self.mcp.declarations_with_intercept_gate() {
            if !Self::is_mcp_tool_active_for_turn(&mcp_decl.name, sniffed) {
                continue;
            }
            if seen.insert(mcp_decl.name.clone()) {
                decls.push(mcp_decl);
            }
        }

        decls
    }

fn is_mcp_tool_active_for_turn(name: &str, sniffed: &SniffedContext) -> bool {
    let p = &sniffed.user_prompt_lower;
    if name.starts_with("mcp_downflow_") {
        return p.contains("download")
            || p.contains("downflow")
            || p.contains("unduh")
            || p.contains("torrent")
            || p.contains("magnet")
            || p.contains("aria2")
            || p.contains("queue")
            || sniffed.active_keywords.iter().any(|k| {
                matches!(k.as_str(), "download" | "downflow" | "unduh" | "torrent" | "magnet" | "queue")
            });
    }
    if name.starts_with("mcp_earshot_") {
        return p.contains("earshot")
            || p.contains("audio")
            || p.contains("sound")
            || p.contains("sfx")
            || p.contains("wav")
            || p.contains("mp3")
            || p.contains("suara")
            || p.contains("musik")
            || p.contains("lagu")
            || sniffed.active_keywords.iter().any(|k| {
                matches!(k.as_str(), "earshot" | "audio" | "sound" | "sfx" | "wav" | "mp3" | "suara")
            });
    }
    if name.starts_with("browser_") {
        return sniffed.browser_active
            || p.contains("browser")
            || p.contains("cdp")
            || p.contains("chrome")
            || p.contains("web")
            || p.contains("url")
            || p.contains("http")
            || p.contains("scrape")
            || sniffed.active_keywords.iter().any(|k| {
                matches!(k.as_str(), "browser" | "cdp" | "chrome" | "web" | "scrape")
            });
    }
    true
}

    pub fn router_catalog(&self) -> Vec<(String, String, Vec<String>)> {
        let mut out = Vec::new();
        for t in self.manifest_tools.values() {
            out.push((t.name.clone(), t.description.clone(), t.keywords.clone()));
        }
        for mt in &self.mcp.tools {
            out.push((
                mt.qualified_name.clone(),
                mt.description.clone(),
                vec![mt.server_name.clone(), mt.tool_name.clone()],
            ));
        }
        out
    }

    pub fn validate_intercept_gate(args: &Value) -> Result<(String, Vec<String>, String), String> {
        let Some(obj) = args.as_object() else {
            return Err("Tool arguments must be a JSON object.".to_string());
        };
        let reason = obj
            .get("reason")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .unwrap_or("")
            .to_string();
        if reason.is_empty() {
            return Err("Tool Intercept Gate violation: 'reason' (non-empty string <= 160 chars) is required.".to_string());
        }
        let keywords: Vec<String> = obj
            .get("keywords")
            .and_then(|v| v.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|x| x.as_str().map(str::trim))
                    .filter(|s| !s.is_empty())
                    .map(str::to_string)
                    .collect()
            })
            .unwrap_or_default();
        if keywords.len() < 5 {
            return Err(format!(
                "Tool Intercept Gate violation: 'keywords' requires at least 5 English semantic keywords (got {}).",
                keywords.len()
            ));
        }
        let goal = obj
            .get("goal")
            .and_then(|v| v.as_str())
            .map(str::trim)
            .unwrap_or("")
            .to_string();
        Ok((reason, keywords, goal))
    }

    pub async fn execute(&self, tool_name: &str, args: &Value) -> ToolExecOutcome {
        self.execute_with_id("", tool_name, args).await
    }

    pub async fn execute_with_id(&self, call_id: &str, tool_name: &str, args: &Value) -> ToolExecOutcome {
        // Dispatch MCP tools first if registered
        if self.mcp.is_mcp_tool(tool_name).is_some() {
            return match self.mcp.call_tool(tool_name, args).await {
                Ok(val) => {
                    let display = serde_json::to_string_pretty(&val).unwrap_or_else(|_| val.to_string());
                    let formatted = self.format_large_output(tool_name, call_id, &display);
                    ToolExecOutcome::ok_json(val, formatted)
                }
                Err(e) => ToolExecOutcome::err(e),
            };
        }

        let cfg_snapshot = self.config.lock().await.clone();

        // Dispatch Sovereign Native Built-ins
        let mut outcome = match tool_name {
            "read_file" | "view_file" => self.exec_read_file(&cfg_snapshot, call_id, args),
            "read_many_files" => self.exec_read_many_files(&cfg_snapshot, call_id, args),
            "write_file" | "write_to_file" => self.exec_write_file(&cfg_snapshot, args),
            "replace" | "replace_file_content" => self.exec_replace(&cfg_snapshot, args),
            "list_directory" => self.exec_list_directory(&cfg_snapshot, call_id, args),
            "glob" => self.exec_glob(&cfg_snapshot, call_id, args),
            "grep_search" => self.exec_grep_search(&cfg_snapshot, call_id, args),
            "run_shell_command" | "run_command" => self.exec_shell(&cfg_snapshot, call_id, args).await,
            "list_background_processes" => self.exec_list_bg().await,
            "read_background_output" => self.exec_read_bg(call_id, args).await,
            "write_todos" => self.exec_write_todos(&cfg_snapshot, args),
            "tracker_create_task" => self.exec_tracker_create(&cfg_snapshot, args),
            "tracker_update_task" => self.exec_tracker_update(&cfg_snapshot, args),
            "tracker_get_task" => self.exec_tracker_get(&cfg_snapshot, args),
            "tracker_list_tasks" => self.exec_tracker_list(&cfg_snapshot, args),
            "tracker_add_dependency" => self.exec_tracker_dep(&cfg_snapshot, args),
            "tracker_visualize" => self.exec_tracker_vis(&cfg_snapshot),
            "activate_skill" => self.exec_activate_skill(&cfg_snapshot, args).await,
            "web_fetch" => self.exec_web_fetch(call_id, args).await,
            "flowork_web_search" => self.exec_web_search(call_id, args).await,
            "list_mcp_resources" => self.exec_list_mcp_resources(args).await,
            "read_mcp_resource" => self.exec_read_mcp_resource(call_id, args).await,
            "ask_user" => self.exec_ask_user(args).await,
            "enter_plan_mode" => self.exec_plan_mode(true, args).await,
            "exit_plan_mode" => self.exec_plan_mode(false, args).await,
            "invoke_agent" => self.exec_invoke_agent(args).await,
            "complete_task" => {
                let res = args
                    .get("result")
                    .or_else(|| args.get("summary"))
                    .cloned()
                    .unwrap_or(json!("Task completed"));
                let display = res.as_str().unwrap_or("Task completed.").to_string();
                ToolExecOutcome::ok_json(
                    json!({ "status": "completed", "result": res.clone(), "summary": res }),
                    display,
                )
            }
            "update_topic" => ToolExecOutcome::ok_json(
                json!({ "status": "ok", "topic": args.get("topic").cloned().unwrap_or(json!("")) }),
                "Topic updated.",
            ),
            _ => self.exec_disk_tool(&cfg_snapshot, call_id, tool_name, args).await,
        };

        // Trigger dynamic rescan if tool_foundry ran successfully
        if tool_name == "tool_foundry" && outcome.success {
            outcome.needs_tool_rescan = true;
        }

        // Inject self-contained tool SKILL.md on first successful invocation (zero token bloat on repeat calls)
        if outcome.success {
            if let Some(m) = self.manifest_tools.get(tool_name) {
                if let Some(ref sk_path) = m.skill_file {
                    let mut activated = self.activated_tool_skills.lock().await;
                    if activated.insert(tool_name.to_string()) {
                        if let Ok(skill_md) = fs::read_to_string(sk_path) {
                            let tag = format!(
                                "\n<flowork_tool_skill tool=\"{}\">\n{}\n</flowork_tool_skill>",
                                tool_name,
                                skill_md.trim()
                            );
                            if let Some(obj) = outcome.output_json.as_object_mut() {
                                obj.insert("_tool_skill_guidance".to_string(), json!(tag));
                            }
                            outcome.display_text.push_str(&tag);
                        }
                    }
                }
            }
        }

        outcome
    }

    fn resolve_path(cfg: &AppConfig, raw: &str) -> PathBuf {
        let expanded = if let Some(rest) = raw.strip_prefix("~/") {
            cfg.paths.home_dir.join(rest)
        } else {
            PathBuf::from(raw)
        };
        if expanded.is_absolute() {
            expanded
        } else {
            cfg.cwd.join(expanded)
        }
    }

    fn exec_read_file(&self, cfg: &AppConfig, call_id: &str, args: &Value) -> ToolExecOutcome {
        let Some(fp) = args
            .get("file_path")
            .or_else(|| args.get("AbsolutePath"))
            .or_else(|| args.get("path"))
            .and_then(|s| s.as_str())
        else {
            return ToolExecOutcome::err("Error: 'file_path' argument is required.");
        };

        let path = Self::resolve_path(cfg, fp);
        if cfg.sandbox && !cfg.is_path_in_workspace(&path) {
            return ToolExecOutcome::err(format!("Sandbox error: '{}' is outside allowed workspace.", path.display()));
        }
        if !path.exists() {
            return ToolExecOutcome::err(format!("Error: File not found: {}", path.display()));
        }
        if path.is_dir() {
            return ToolExecOutcome::err(format!("Error: '{}' is a directory; use list_directory.", path.display()));
        }

        let ext = path
            .extension()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .to_ascii_lowercase();

        let binary_mime = match ext.as_str() {
            "png" => Some("image/png"),
            "jpg" | "jpeg" => Some("image/jpeg"),
            "webp" => Some("image/webp"),
            "gif" => Some("image/gif"),
            "pdf" => Some("application/pdf"),
            "wav" => Some("audio/wav"),
            "mp3" => Some("audio/mp3"),
            "ogg" => Some("audio/ogg"),
            _ => None,
        };

        if let Some(mime) = binary_mime {
            let Ok(bytes) = fs::read(&path) else {
                return ToolExecOutcome::err(format!("Failed reading binary file '{}'", path.display()));
            };
            if bytes.len() > 20 * 1024 * 1024 {
                return ToolExecOutcome::err(format!(
                    "Multimodal file '{}' exceeds 20 MB limit ({} bytes).",
                    path.display(),
                    bytes.len()
                ));
            }
            let b64 = B64.encode(&bytes);
            let mut out = ToolExecOutcome::ok_json(
                json!({
                    "file_path": path.to_string_lossy(),
                    "mime_type": mime,
                    "size_bytes": bytes.len(),
                    "multimodal": true
                }),
                format!("Attached multimodal asset {} ({}, {} bytes).", path.display(), mime, bytes.len()),
            );
            out.inline_blobs.push(InlineBlob {
                mime_type: mime.to_string(),
                data: b64,
            });
            return out;
        }

        let Ok(raw_bytes) = fs::read(&path) else {
            return ToolExecOutcome::err(format!("Failed reading file '{}'", path.display()));
        };
        let raw = String::from_utf8_lossy(&raw_bytes);
        let lines: Vec<&str> = raw.lines().collect();
        let total = lines.len().max(1);
        let start = args
            .get("start_line")
            .or_else(|| args.get("StartLine"))
            .and_then(|v| v.as_u64())
            .map(|n| (n as usize).max(1))
            .unwrap_or(1);
        let default_end = total.min(start + 799);
        let end = args
            .get("end_line")
            .or_else(|| args.get("EndLine"))
            .and_then(|v| v.as_u64())
            .map(|n| (n as usize).min(total))
            .unwrap_or(default_end);

        let mut sliced = Vec::new();
        if !lines.is_empty() && start <= lines.len() {
            for idx in (start - 1)..end.min(lines.len()) {
                sliced.push(format!("{}: {}", idx + 1, lines[idx]));
            }
        }
        let body = self.format_large_output("read_file", call_id, &sliced.join("\n"));
        ToolExecOutcome::ok_json(
            json!({
                "file_path": path.to_string_lossy(),
                "total_lines": total,
                "showing_lines": format!("{}-{}", start, end),
                "content": body
            }),
            body,
        )
    }

    fn exec_read_many_files(&self, cfg: &AppConfig, call_id: &str, args: &Value) -> ToolExecOutcome {
        let patterns: Vec<String> = args
            .get("paths")
            .or_else(|| args.get("include"))
            .and_then(|v| v.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|s| s.as_str().map(str::to_string))
                    .collect()
            })
            .unwrap_or_default();

        if patterns.is_empty() {
            return ToolExecOutcome::err("Error: 'paths' array is required.");
        }

        let mut files = Vec::new();
        for pat in &patterns {
            let candidate = Self::resolve_path(cfg, pat);
            if candidate.is_file() {
                if cfg.sandbox && !cfg.is_path_in_workspace(&candidate) {
                    return ToolExecOutcome::err(format!(
                        "Sandbox error: '{}' is outside allowed workspace.",
                        candidate.display()
                    ));
                }
                files.push(candidate);
            } else if let Ok(glob_pat) = Pattern::new(pat) {
                for entry in WalkBuilder::new(&cfg.cwd).build().flatten() {
                    if entry.file_type().map(|t| t.is_file()).unwrap_or(false) {
                        if cfg.sandbox && !cfg.is_path_in_workspace(entry.path()) {
                            continue;
                        }
                        let rel = entry.path().strip_prefix(&cfg.cwd).unwrap_or(entry.path());
                        if glob_pat.matches_path(rel) || glob_pat.matches_path(entry.path()) {
                            files.push(entry.path().to_path_buf());
                            if files.len() >= 30 {
                                break;
                            }
                        }
                    }
                }
            }
        }

        let mut chunks = Vec::new();
        for p in files.into_iter().take(25) {
            if let Ok(content) = fs::read_to_string(&p) {
                let preview = truncate_str(&content, 4000);
                chunks.push(format!("=== {} ===\n{}", p.display(), preview));
            }
        }
        let combined = self.format_large_output("read_many_files", call_id, &chunks.join("\n\n"));
        ToolExecOutcome::ok_json(json!({ "content": combined }), combined)
    }

    fn exec_write_file(&self, cfg: &AppConfig, args: &Value) -> ToolExecOutcome {
        let Some(fp) = args
            .get("file_path")
            .or_else(|| args.get("TargetFile"))
            .and_then(|s| s.as_str())
        else {
            return ToolExecOutcome::err("Error: 'file_path' is required.");
        };
        let content = args
            .get("content")
            .or_else(|| args.get("CodeContent"))
            .and_then(|s| s.as_str())
            .unwrap_or("");

        let path = Self::resolve_path(cfg, fp);
        if cfg.sandbox && !cfg.is_path_in_workspace(&path) {
            return ToolExecOutcome::err(format!("Sandbox error: '{}' is outside allowed workspace.", path.display()));
        }
        if let Some(parent) = path.parent() {
            if let Err(e) = fs::create_dir_all(parent) {
                return ToolExecOutcome::err(format!("Failed creating directory '{}': {}", parent.display(), e));
            }
        }
        match fs::write(&path, content) {
            Ok(()) => ToolExecOutcome::ok_json(
                json!({
                    "status": "ok",
                    "file_path": path.to_string_lossy(),
                    "bytes_written": content.len()
                }),
                format!("Wrote {} bytes to {}", content.len(), path.display()),
            ),
            Err(e) => ToolExecOutcome::err(format!("Failed writing '{}': {}", path.display(), e)),
        }
    }

    fn exec_replace(&self, cfg: &AppConfig, args: &Value) -> ToolExecOutcome {
        let Some(fp) = args
            .get("file_path")
            .or_else(|| args.get("TargetFile"))
            .and_then(|s| s.as_str())
        else {
            return ToolExecOutcome::err("Error: 'file_path' is required.");
        };
        let old_str = args
            .get("old_string")
            .or_else(|| args.get("TargetContent"))
            .and_then(|s| s.as_str())
            .unwrap_or("");
        let new_str = args
            .get("new_string")
            .or_else(|| args.get("ReplacementContent"))
            .and_then(|s| s.as_str())
            .unwrap_or("");
        let allow_multiple = args
            .get("allow_multiple")
            .or_else(|| args.get("AllowMultiple"))
            .and_then(|v| v.as_bool())
            .unwrap_or(false);

        if old_str.is_empty() {
            return ToolExecOutcome::err("Error: 'old_string' must be non-empty.");
        }

        let path = Self::resolve_path(cfg, fp);
        if cfg.sandbox && !cfg.is_path_in_workspace(&path) {
            return ToolExecOutcome::err(format!("Sandbox error: '{}' is outside allowed workspace.", path.display()));
        }
        let Ok(original) = fs::read_to_string(&path) else {
            return ToolExecOutcome::err(format!("Error: Cannot read file '{}'", path.display()));
        };

        let count = original.matches(old_str).count();
        if count == 0 {
            return ToolExecOutcome::err(format!("Error: Target 'old_string' not found in {}", path.display()));
        }

        let updated = if allow_multiple {
            original.replace(old_str, new_str)
        } else {
            original.replacen(old_str, new_str, 1)
        };

        match fs::write(&path, updated) {
            Ok(()) => ToolExecOutcome::ok_json(
                json!({
                    "status": "ok",
                    "file_path": path.to_string_lossy(),
                    "occurrences_matched": count,
                    "replaced": if allow_multiple { count } else { 1 }
                }),
                format!("Successfully updated {} ({} replacement(s)).", path.display(), if allow_multiple { count } else { 1 }),
            ),
            Err(e) => ToolExecOutcome::err(format!("Failed writing '{}': {}", path.display(), e)),
        }
    }

    fn exec_list_directory(&self, cfg: &AppConfig, call_id: &str, args: &Value) -> ToolExecOutcome {
        let dir_str = args
            .get("path")
            .or_else(|| args.get("dir_path"))
            .and_then(|s| s.as_str())
            .unwrap_or(".");
        let path = Self::resolve_path(cfg, dir_str);
        if cfg.sandbox && !cfg.is_path_in_workspace(&path) {
            return ToolExecOutcome::err(format!("Sandbox error: '{}' is outside allowed workspace.", path.display()));
        }
        if !path.is_dir() {
            return ToolExecOutcome::err(format!("Error: '{}' is not a directory.", path.display()));
        }

        let ignore_pats: Vec<String> = args
            .get("ignore")
            .and_then(|v| v.as_array())
            .map(|arr| arr.iter().filter_map(|x| x.as_str().map(str::to_string)).collect())
            .unwrap_or_default();

        let Ok(entries) = fs::read_dir(&path) else {
            return ToolExecOutcome::err(format!("Failed reading directory '{}'", path.display()));
        };
        let mut items = Vec::new();
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if ignore_pats.iter().any(|p| p == &name) {
                continue;
            }
            let meta = entry.metadata().ok();
            let is_dir = meta.as_ref().map(|m| m.is_dir()).unwrap_or(false);
            let size = meta.as_ref().map(|m| m.len()).unwrap_or(0);
            items.push((!is_dir, name, size));
        }
        items.sort_by(|a, b| a.0.cmp(&b.0).then_with(|| a.1.cmp(&b.1)));

        let lines: Vec<String> = items
            .iter()
            .map(|(is_file, name, sz)| {
                if *is_file {
                    format!("[FILE] {} ({} B)", name, sz)
                } else {
                    format!("[DIR]  {}/", name)
                }
            })
            .collect();
        let text = self.format_large_output("list_directory", call_id, &lines.join("\n"));
        ToolExecOutcome::ok_json(
            json!({ "path": path.to_string_lossy(), "count": items.len(), "entries": text }),
            text,
        )
    }

    fn exec_glob(&self, cfg: &AppConfig, call_id: &str, args: &Value) -> ToolExecOutcome {
        let Some(pat_str) = args.get("pattern").and_then(|s| s.as_str()) else {
            return ToolExecOutcome::err("Error: 'pattern' is required.");
        };
        let root_str = args
            .get("path")
            .or_else(|| args.get("dir_path"))
            .and_then(|s| s.as_str())
            .unwrap_or(".");
        let root = Self::resolve_path(cfg, root_str);
        if cfg.sandbox && !cfg.is_path_in_workspace(&root) {
            return ToolExecOutcome::err(format!("Sandbox error: '{}' is outside allowed workspace.", root.display()));
        }

        let pat = match Pattern::new(pat_str) {
            Ok(p) => p,
            Err(e) => return ToolExecOutcome::err(format!("Invalid glob pattern: {}", e)),
        };

        let mut matches = Vec::new();
        for entry in WalkBuilder::new(&root).hidden(false).build().flatten() {
            let p = entry.path();
            if p == root {
                continue;
            }
            if cfg.sandbox && !cfg.is_path_in_workspace(p) {
                continue;
            }
            let rel = p.strip_prefix(&root).unwrap_or(p);
            if pat.matches_path(rel) || pat.matches_path(p) || pat.matches(p.file_name().and_then(|n| n.to_str()).unwrap_or("")) {
                matches.push(p.to_string_lossy().to_string());
                if matches.len() >= 300 {
                    break;
                }
            }
        }
        matches.sort();
        let body = self.format_large_output("glob", call_id, &matches.join("\n"));
        ToolExecOutcome::ok_json(json!({ "count": matches.len(), "files": matches }), body)
    }

    fn exec_grep_search(&self, cfg: &AppConfig, call_id: &str, args: &Value) -> ToolExecOutcome {
        let Some(pat_str) = args
            .get("pattern")
            .or_else(|| args.get("query"))
            .and_then(|s| s.as_str())
        else {
            return ToolExecOutcome::err("Error: 'pattern' is required.");
        };
        let root_str = args
            .get("path")
            .or_else(|| args.get("dir_path"))
            .and_then(|s| s.as_str())
            .unwrap_or(".");
        let root = Self::resolve_path(cfg, root_str);
        if cfg.sandbox && !cfg.is_path_in_workspace(&root) {
            return ToolExecOutcome::err(format!("Sandbox error: '{}' is outside allowed workspace.", root.display()));
        }
        let case_insensitive = args
            .get("case_insensitive")
            .and_then(|b| b.as_bool())
            .unwrap_or(false);
        let include_glob = args
            .get("include_pattern")
            .or_else(|| args.get("include"))
            .and_then(|s| s.as_str())
            .and_then(|g| Pattern::new(g).ok());

        let regex = match RegexBuilder::new(pat_str).case_insensitive(case_insensitive).build() {
            Ok(r) => r,
            Err(e) => return ToolExecOutcome::err(format!("Invalid regex '{}': {}", pat_str, e)),
        };

        let mut hits = Vec::new();
        for entry in WalkBuilder::new(&root).build().flatten() {
            if !entry.file_type().map(|t| t.is_file()).unwrap_or(false) {
                continue;
            }
            let p = entry.path();
            if cfg.sandbox && !cfg.is_path_in_workspace(p) {
                continue;
            }
            if let Some(ref ig) = include_glob {
                let rel = p.strip_prefix(&root).unwrap_or(p);
                let fname = p.file_name().and_then(|n| n.to_str()).unwrap_or("");
                if !ig.matches_path(rel) && !ig.matches(fname) {
                    continue;
                }
            }
            let Ok(bytes) = fs::read(p) else {
                continue;
            };
            if bytes.len() > 2 * 1024 * 1024 || bytes.contains(&0) {
                continue;
            }
            let txt = String::from_utf8_lossy(&bytes);
            for (idx, line) in txt.lines().enumerate() {
                if regex.is_match(line) {
                    hits.push(format!("{}:{}: {}", p.display(), idx + 1, truncate_str(line, 240)));
                    if hits.len() >= 200 {
                        break;
                    }
                }
            }
            if hits.len() >= 200 {
                break;
            }
        }
        let body = self.format_large_output("grep_search", call_id, &hits.join("\n"));
        ToolExecOutcome::ok_json(json!({ "matches": hits.len(), "output": body }), body)
    }

    async fn exec_shell(&self, cfg: &AppConfig, call_id: &str, args: &Value) -> ToolExecOutcome {
        let Some(command_str) = args.get("command").and_then(|s| s.as_str()) else {
            return ToolExecOutcome::err("Error: 'command' is required.");
        };
        let is_bg = args.get("is_background").and_then(|b| b.as_bool()).unwrap_or(false);
        let workdir = args
            .get("dir_path")
            .or_else(|| args.get("cwd"))
            .and_then(|s| s.as_str())
            .map(|d| Self::resolve_path(cfg, d))
            .unwrap_or_else(|| cfg.cwd.clone());
        if cfg.sandbox && !cfg.is_path_in_workspace(&workdir) {
            return ToolExecOutcome::err(format!("Sandbox error: '{}' is outside allowed workspace.", workdir.display()));
        }
        let timeout_ms = args
            .get("timeout_ms")
            .and_then(|v| v.as_u64())
            .unwrap_or(120_000)
            .min(600_000);

        let exec_path = Self::build_execution_path(cfg);

        if is_bg {
            let id = format!("bg_{}", chrono::Utc::now().timestamp_millis());
            let log_dir = cfg.paths.user_flowork_dir.join("logs");
            let _ = fs::create_dir_all(&log_dir);
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let _ = fs::set_permissions(&log_dir, fs::Permissions::from_mode(0o700));
            }
            let log_path = log_dir.join(format!("flowork_{}.log", id));
            #[cfg(unix)]
            let log_file_res = {
                use std::os::unix::fs::OpenOptionsExt;
                fs::OpenOptions::new()
                    .create(true)
                    .write(true)
                    .truncate(true)
                    .mode(0o600)
                    .open(&log_path)
            };
            #[cfg(not(unix))]
            let log_file_res = fs::File::create(&log_path);
            let Ok(log_file) = log_file_res else {
                return ToolExecOutcome::err("Failed creating background log file.");
            };
            let log_err = log_file.try_clone().unwrap_or_else(|_| fs::File::create("/dev/null").unwrap());

            let mut cmd = std::process::Command::new("/bin/bash");
            cmd.args(["-c", command_str])
                .current_dir(&workdir)
                .env("PATH", &exec_path)
                .env("PAGER", "cat")
                .stdin(Stdio::null())
                .stdout(Stdio::from(log_file))
                .stderr(Stdio::from(log_err));

            #[cfg(unix)]
            unsafe {
                use std::os::unix::process::CommandExt;
                cmd.pre_exec(|| {
                    libc::setsid();
                    Ok(())
                });
            }

            return match cmd.spawn() {
                Ok(child) => {
                    let pid = child.id();
                    let info = BackgroundProcessInfo {
                        id: id.clone(),
                        pid,
                        command: command_str.to_string(),
                        log_path: log_path.clone(),
                        started_at: SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0),
                        running: true,
                    };
                    self.proc_reg.lock().await.bg.insert(id.clone(), info);
                    ToolExecOutcome::ok_json(
                        json!({
                            "status": "running_background",
                            "process_id": id,
                            "pid": pid,
                            "log_path": log_path.to_string_lossy()
                        }),
                        format!("Started background process {} (PID {})", id, pid),
                    )
                }
                Err(e) => ToolExecOutcome::err(format!("Failed starting background process: {}", e)),
            };
        }

        let mut cmd = Command::new("/bin/bash");
        cmd.args(["-c", command_str])
            .current_dir(&workdir)
            .env("PATH", &exec_path)
            .env("PAGER", "cat")
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .kill_on_drop(true);

        #[cfg(unix)]
        unsafe {
            cmd.pre_exec(|| {
                libc::setpgid(0, 0);
                Ok(())
            });
        }

        let child = match cmd.spawn() {
            Ok(c) => c,
            Err(e) => return ToolExecOutcome::err(format!("Failed spawning shell command: {}", e)),
        };

        let pgid = child.id().map(|p| p as i32);
        match collect_child_output_with_timeout(
            child,
            Duration::from_millis(timeout_ms),
            pgid,
            &self.proc_reg,
        )
        .await
        {
            Ok(Ok((status, out_bytes, err_bytes))) => {
                let exit_code = status.code().unwrap_or(-1);
                let stdout_raw = String::from_utf8_lossy(&out_bytes);
                let stderr_raw = String::from_utf8_lossy(&err_bytes);
                let stdout = self.format_large_output("run_shell_command_stdout", call_id, &stdout_raw);
                let stderr = self.format_large_output("run_shell_command_stderr", call_id, &stderr_raw);
                let display = if stderr.is_empty() {
                    format!("Exit Code: {}\n{}", exit_code, stdout)
                } else {
                    format!("Exit Code: {}\nSTDOUT:\n{}\nSTDERR:\n{}", exit_code, stdout, stderr)
                };
                ToolExecOutcome {
                    success: exit_code == 0,
                    output_json: json!({
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": exit_code
                    }),
                    display_text: display,
                    inline_blobs: Vec::new(),
                    refreshed_mode: None,
                    needs_tool_rescan: false,
                }
            }
            Ok(Err(e)) => ToolExecOutcome::err(format!("Shell wait error: {}", e)),
            Err(_) => ToolExecOutcome::err(format!("Shell command timed out after {} ms", timeout_ms)),
        }
    }

    async fn exec_list_bg(&self) -> ToolExecOutcome {
        let mut reg = self.proc_reg.lock().await;
        let mut list = Vec::new();
        for info in reg.bg.values_mut() {
            #[cfg(unix)]
            {
                let alive = unsafe { libc::kill(info.pid as i32, 0) } == 0;
                info.running = alive;
            }
            list.push(info.clone());
        }
        ToolExecOutcome::ok_json(
            json!({ "processes": list }),
            format!("Tracked {} background process(es).", list.len()),
        )
    }

    async fn exec_read_bg(&self, call_id: &str, args: &Value) -> ToolExecOutcome {
        let Some(pid_or_id) = args
            .get("process_id")
            .or_else(|| args.get("id"))
            .and_then(|s| s.as_str())
        else {
            return ToolExecOutcome::err("Error: 'process_id' is required.");
        };
        let reg = self.proc_reg.lock().await;
        let Some(info) = reg.bg.get(pid_or_id) else {
            return ToolExecOutcome::err(format!("Background process '{}' not found.", pid_or_id));
        };
        let content = fs::read_to_string(&info.log_path).unwrap_or_default();
        let trimmed = self.format_large_output("read_background_output", call_id, &content);
        ToolExecOutcome::ok_json(
            json!({ "process_id": info.id, "running": info.running, "output": trimmed }),
            trimmed,
        )
    }

    fn exec_write_todos(&self, cfg: &AppConfig, args: &Value) -> ToolExecOutcome {
        let todos = args.get("todos").cloned().unwrap_or_else(|| json!([]));
        let dir = cfg.cwd.join(".flowork");
        let _ = fs::create_dir_all(&dir);
        let _ = fs::write(
            dir.join("todos.json"),
            serde_json::to_string_pretty(&todos).unwrap_or_default(),
        );
        let count = todos.as_array().map(|a| a.len()).unwrap_or(0);
        ToolExecOutcome::ok_json(
            json!({ "status": "todos_saved", "count": count, "todos": todos }),
            format!("Saved {} todo item(s).", count),
        )
    }

    fn tracker_path(cfg: &AppConfig) -> PathBuf {
        cfg.cwd.join(".flowork/tracker/tasks.json")
    }

    fn load_tracker(cfg: &AppConfig) -> Vec<Value> {
        let p = Self::tracker_path(cfg);
        fs::read_to_string(p)
            .ok()
            .and_then(|r| serde_json::from_str(&r).ok())
            .unwrap_or_default()
    }

    fn save_tracker(cfg: &AppConfig, tasks: &[Value]) {
        let p = Self::tracker_path(cfg);
        if let Some(parent) = p.parent() {
            let _ = fs::create_dir_all(parent);
        }
        let _ = fs::write(p, serde_json::to_string_pretty(tasks).unwrap_or_default());
    }

    fn exec_tracker_create(&self, cfg: &AppConfig, args: &Value) -> ToolExecOutcome {
        let mut tasks = Self::load_tracker(cfg);
        let id = format!("task_{}", tasks.len() + 1);
        let title = args.get("title").and_then(|s| s.as_str()).unwrap_or("Untitled task");
        let desc = args.get("description").and_then(|s| s.as_str()).unwrap_or("");
        let entry = json!({
            "id": id,
            "title": title,
            "description": desc,
            "status": "pending",
            "dependencies": []
        });
        tasks.push(entry.clone());
        Self::save_tracker(cfg, &tasks);
        ToolExecOutcome::ok_json(entry, format!("Created tracker task '{}'.", id))
    }

    fn exec_tracker_update(&self, cfg: &AppConfig, args: &Value) -> ToolExecOutcome {
        let id = args.get("task_id").or_else(|| args.get("id")).and_then(|s| s.as_str()).unwrap_or("");
        let status = args.get("status").and_then(|s| s.as_str()).unwrap_or("in_progress");
        let mut tasks = Self::load_tracker(cfg);
        let mut updated_entry: Option<Value> = None;
        for t in &mut tasks {
            if t.get("id").and_then(|s| s.as_str()) == Some(id) {
                if let Some(obj) = t.as_object_mut() {
                    obj.insert("status".to_string(), json!(status));
                    updated_entry = Some(t.clone());
                    break;
                }
            }
        }
        if let Some(entry) = updated_entry {
            Self::save_tracker(cfg, &tasks);
            return ToolExecOutcome::ok_json(entry, format!("Updated {} -> {}", id, status));
        }
        ToolExecOutcome::err(format!("Task '{}' not found.", id))
    }

    fn exec_tracker_get(&self, cfg: &AppConfig, args: &Value) -> ToolExecOutcome {
        let id = args.get("task_id").or_else(|| args.get("id")).and_then(|s| s.as_str()).unwrap_or("");
        let tasks = Self::load_tracker(cfg);
        for t in tasks {
            if t.get("id").and_then(|s| s.as_str()) == Some(id) {
                return ToolExecOutcome::ok_json(t.clone(), t.to_string());
            }
        }
        ToolExecOutcome::err(format!("Task '{}' not found.", id))
    }

    fn exec_tracker_list(&self, cfg: &AppConfig, _args: &Value) -> ToolExecOutcome {
        let tasks = Self::load_tracker(cfg);
        ToolExecOutcome::ok_json(json!({ "tasks": tasks }), format!("Listed {} task(s).", tasks.len()))
    }

    fn exec_tracker_dep(&self, cfg: &AppConfig, args: &Value) -> ToolExecOutcome {
        let id = args.get("task_id").and_then(|s| s.as_str()).unwrap_or("");
        let dep = args.get("depends_on").and_then(|s| s.as_str()).unwrap_or("");
        let mut tasks = Self::load_tracker(cfg);
        let mut updated_entry: Option<Value> = None;
        for t in &mut tasks {
            if t.get("id").and_then(|s| s.as_str()) == Some(id) {
                if let Some(arr) = t.get_mut("dependencies").and_then(|d| d.as_array_mut()) {
                    arr.push(json!(dep));
                    updated_entry = Some(t.clone());
                    break;
                }
            }
        }
        if let Some(entry) = updated_entry {
            Self::save_tracker(cfg, &tasks);
            return ToolExecOutcome::ok_json(entry, format!("Linked {} -> depends on {}", id, dep));
        }
        ToolExecOutcome::err(format!("Task '{}' not found.", id))
    }

    fn exec_tracker_vis(&self, cfg: &AppConfig) -> ToolExecOutcome {
        let tasks = Self::load_tracker(cfg);
        let lines: Vec<String> = tasks
            .iter()
            .map(|t| {
                format!(
                    "[{}] {} - {}",
                    t.get("status").and_then(|s| s.as_str()).unwrap_or("?"),
                    t.get("id").and_then(|s| s.as_str()).unwrap_or("?"),
                    t.get("title").and_then(|s| s.as_str()).unwrap_or("")
                )
            })
            .collect();
        let vis = lines.join("\n");
        ToolExecOutcome::ok_json(json!({ "graph": vis }), vis)
    }

    async fn exec_activate_skill(&self, cfg: &AppConfig, args: &Value) -> ToolExecOutcome {
        let Some(name) = args.get("name").and_then(|s| s.as_str()) else {
            return ToolExecOutcome::err("Error: 'name' argument required.");
        };
        let skills: Vec<SkillMeta> = discover_skills(cfg);
        let found = skills
            .into_iter()
            .find(|s| s.name.eq_ignore_ascii_case(name) || s.path.parent().and_then(|p| p.file_name()).and_then(|n| n.to_str()) == Some(name));

        let Some(sk) = found else {
            return ToolExecOutcome::err(format!("Skill '{}' not found in configured skills directories.", name));
        };
        let Ok(body) = fs::read_to_string(&sk.path) else {
            return ToolExecOutcome::err(format!("Failed reading skill at '{}'", sk.path.display()));
        };

        let mut resources_list = Vec::new();
        if let Some(skill_dir) = sk.path.parent() {
            // Register skill directory in allowed workspace include_directories for sandboxed read_file
            {
                let mut guard = self.config.lock().await;
                if !guard.include_directories.iter().any(|p| p == skill_dir) {
                    guard.include_directories.push(skill_dir.to_path_buf());
                }
            }
            for entry in WalkBuilder::new(skill_dir).max_depth(Some(3)).build().flatten() {
                let ep = entry.path();
                if ep == skill_dir || ep == sk.path {
                    continue;
                }
                if let Ok(rel) = ep.strip_prefix(skill_dir) {
                    let suffix = if ep.is_dir() { "/" } else { "" };
                    resources_list.push(format!("  {}{}", rel.display(), suffix));
                }
                if resources_list.len() >= 80 {
                    break;
                }
            }
            resources_list.sort();
        }
        let resources_xml = if resources_list.is_empty() {
            String::new()
        } else {
            format!("\n<available_resources>\n{}\n</available_resources>", resources_list.join("\n"))
        };

        let payload = format!(
            "<activated_skill name=\"{}\">\n<directory>{}</directory>\n<instructions>\n{}\n</instructions>{}\n</activated_skill>",
            sk.name,
            sk.path.parent().map(|p| p.to_string_lossy().to_string()).unwrap_or_default(),
            body.trim(),
            resources_xml
        );
        ToolExecOutcome::ok_json(
            json!({
                "status": "skill_activated",
                "skill": sk.name,
                "path": sk.path.to_string_lossy(),
                "instructions": payload
            }),
            payload,
        )
    }

    async fn exec_web_fetch(&self, call_id: &str, args: &Value) -> ToolExecOutcome {
        let Some(url) = args.get("url").and_then(|s| s.as_str()) else {
            return ToolExecOutcome::err("Error: 'url' is required.");
        };

        match flowork_core_rs::ssrf::safe_http_get(
            url,
            "MrFlow-Sovereign/2.0 (FloworkOS)",
            Duration::from_secs(15),
        )
        .await
        {
            Ok((code, final_url, body)) => {
                let truncated = self.format_large_output("web_fetch", call_id, &body);
                ToolExecOutcome::ok_json(
                    json!({ "url": final_url, "http_status": code, "content": truncated }),
                    truncated,
                )
            }
            Err(e) => ToolExecOutcome::err(format!("web_fetch blocked/error for '{}': {}", url, e)),
        }
    }

    async fn exec_web_search(&self, call_id: &str, args: &Value) -> ToolExecOutcome {
        let Some(query) = args.get("query").and_then(|s| s.as_str()) else {
            return ToolExecOutcome::err("Error: 'query' is required.");
        };
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(12))
            .user_agent("Mozilla/5.0 (X11; Linux x86_64) MrFlow/2.0")
            .build()
            .unwrap_or_else(|_| reqwest::Client::new());
        let url = format!("https://html.duckduckgo.com/html/?q={}", urlencoding::encode(query));
        match client.get(&url).send().await {
            Ok(resp) => {
                let html = resp.text().await.unwrap_or_default();
                let mut results = Vec::new();
                let title_re = regex::Regex::new(r#"class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>"#).unwrap();
                for cap in title_re.captures_iter(&html).take(8) {
                    let href = cap.get(1).map(|m| m.as_str()).unwrap_or("");
                    let title = strip_html_tags(cap.get(2).map(|m| m.as_str()).unwrap_or(""));
                    results.push(json!({ "title": title, "url": href }));
                }
                let raw = serde_json::to_string_pretty(&results).unwrap_or_default();
                let text = self.format_large_output("flowork_web_search", call_id, &raw);
                ToolExecOutcome::ok_json(json!({ "query": query, "results": results }), text)
            }
            Err(e) => ToolExecOutcome::err(format!("Web search HTTP error: {}", e)),
        }
    }

    async fn exec_list_mcp_resources(&self, args: &Value) -> ToolExecOutcome {
        let srv = args.get("server").and_then(|s| s.as_str());
        let res = self.mcp.list_resources(srv).await;
        let items: Vec<Value> = res
            .into_iter()
            .map(|r| json!({ "server": r.server, "uri": r.uri, "name": r.name, "mimeType": r.mime_type }))
            .collect();
        let text = serde_json::to_string_pretty(&items).unwrap_or_default();
        ToolExecOutcome::ok_json(json!({ "resources": items }), text)
    }

    async fn exec_read_mcp_resource(&self, call_id: &str, args: &Value) -> ToolExecOutcome {
        let srv = args.get("server").and_then(|s| s.as_str());
        let Some(uri) = args.get("uri").and_then(|s| s.as_str()) else {
            return ToolExecOutcome::err("Error: 'uri' is required.");
        };
        match self.mcp.read_resource(srv, uri).await {
            Ok(val) => {
                let pretty = serde_json::to_string_pretty(&val).unwrap_or_default();
                let disp = self.format_large_output("read_mcp_resource", call_id, &pretty);
                ToolExecOutcome::ok_json(val, disp)
            }
            Err(e) => ToolExecOutcome::err(e),
        }
    }

    async fn exec_ask_user(&self, args: &Value) -> ToolExecOutcome {
        if let Some(ref bridge) = self.ui_bridge {
            let qs = args.get("questions").cloned().unwrap_or_else(|| json!([]));
            match bridge.ask_user(qs).await {
                Ok(ans) => {
                    let s = serde_json::to_string_pretty(&ans).unwrap_or_default();
                    ToolExecOutcome::ok_json(ans, s)
                }
                Err(e) => ToolExecOutcome::err(e),
            }
        } else {
            ToolExecOutcome::err("ask_user is not supported in non-interactive headless mode.")
        }
    }

    async fn exec_plan_mode(&self, enter: bool, args: &Value) -> ToolExecOutcome {
        let new_mode = if enter {
            ApprovalMode::Plan
        } else {
            ApprovalMode::Sovereign
        };
        if let Some(ref bridge) = self.ui_bridge {
            let reason = args.get("reason").and_then(|s| s.as_str()).unwrap_or("").to_string();
            let _ = bridge.request_plan_mode(enter, reason).await;
        }
        self.config.lock().await.approval_mode = new_mode;
        let mut out = ToolExecOutcome::ok_json(
            json!({ "status": "ok", "approval_mode": new_mode.display_label() }),
            format!("Switched mode to {}", new_mode.display_label()),
        );
        out.refreshed_mode = Some(new_mode);
        out
    }

    async fn exec_invoke_agent(&self, args: &Value) -> ToolExecOutcome {
        if self.is_subagent {
            return ToolExecOutcome::err("Recursion guard: subagents cannot spawn child subagents.");
        }
        let Some(ref spawner) = self.subagent_spawner else {
            return ToolExecOutcome::err("Subagent spawner not initialized.");
        };
        let agent_name = args
            .get("agent_name")
            .and_then(|s| s.as_str())
            .unwrap_or("codebase_investigator")
            .to_string();
        let task = args
            .get("task")
            .or_else(|| args.get("prompt"))
            .and_then(|s| s.as_str())
            .unwrap_or("")
            .to_string();
        if task.is_empty() {
            return ToolExecOutcome::err("Error: 'task' argument is required for invoke_agent.");
        }
        spawner.spawn_subagent(agent_name, task).await
    }

    async fn exec_disk_tool(&self, cfg: &AppConfig, call_id: &str, tool_name: &str, args: &Value) -> ToolExecOutcome {
        let Some(meta) = self.manifest_tools.get(tool_name) else {
            return ToolExecOutcome::err(format!("Unknown tool '{}'", tool_name));
        };

        // Locate runner in priority order: manifest.(entrypoint|runner) -> run -> run.sh -> run.py
        let mut candidate_files: Vec<String> = Vec::new();
        if let Some(ref ep) = meta.entrypoint {
            candidate_files.push(ep.clone());
        }
        candidate_files.extend(["run", "run.sh", "run.py"].iter().map(|s| s.to_string()));

        let mut chosen: Option<PathBuf> = None;
        let canon_meta_dir = fs::canonicalize(&meta.dir).unwrap_or_else(|_| meta.dir.clone());
        for f in candidate_files {
            if f.contains("..") {
                continue;
            }
            let p = meta.dir.join(&f);
            if p.is_file() {
                if let Ok(cp) = fs::canonicalize(&p) {
                    if cp.starts_with(&canon_meta_dir) {
                        chosen = Some(cp);
                        break;
                    }
                }
            }
        }
        let Some(script_path) = chosen else {
            return ToolExecOutcome::err(format!(
                "No executable runner (run, run.sh, run.py) found safely inside tool directory for '{}'",
                tool_name
            ));
        };

        let ext = script_path.extension().and_then(|s| s.to_str()).unwrap_or("");
        let (bin, cmd_args): (PathBuf, Vec<String>) = match ext {
            "py" => (PathBuf::from("/usr/bin/python3"), vec![script_path.to_string_lossy().to_string()]),
            "sh" => (PathBuf::from("/bin/bash"), vec![script_path.to_string_lossy().to_string()]),
            _ => (script_path.clone(), Vec::new()),
        };

        let mut cmd = Command::new(bin);
        cmd.args(cmd_args)
            .current_dir(&cfg.cwd)
            .env("FLOWORK_TOOL_NAME", tool_name)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        #[cfg(unix)]
        unsafe {
            cmd.pre_exec(|| {
                libc::setpgid(0, 0);
                Ok(())
            });
        }

        let mut child = match cmd.spawn() {
            Ok(c) => c,
            Err(e) => return ToolExecOutcome::err(format!("Failed spawning tool '{}': {}", tool_name, e)),
        };

        if let Some(mut stdin) = child.stdin.take() {
            let json_in = serde_json::to_string(args).unwrap_or_else(|_| "{}".to_string());
            let _ = stdin.write_all(json_in.as_bytes()).await;
            let _ = stdin.flush().await;
            drop(stdin);
        }

        let pgid = child.id().map(|p| p as i32);
        match collect_child_output_with_timeout(
            child,
            Duration::from_secs(90),
            pgid,
            &self.proc_reg,
        )
        .await
        {
            Ok(Ok((status, out_bytes, err_bytes))) => {
                let code = status.code().unwrap_or(-1);
                let stdout_raw = String::from_utf8_lossy(&out_bytes).to_string();
                let stderr_raw = String::from_utf8_lossy(&err_bytes).to_string();
                if code != 0 {
                    let msg = if !stderr_raw.trim().is_empty() {
                        self.format_large_output(tool_name, call_id, &stderr_raw)
                    } else if !stdout_raw.trim().is_empty() {
                        self.format_large_output(tool_name, call_id, &stdout_raw)
                    } else {
                        format!("Tool '{}' exited with code {}", tool_name, code)
                    };
                    return ToolExecOutcome {
                        success: false,
                        output_json: json!({ "error": msg, "exit_code": code }),
                        display_text: msg,
                        inline_blobs: Vec::new(),
                        refreshed_mode: None,
                        needs_tool_rescan: false,
                    };
                }
                let trimmed = stdout_raw.trim();
                let formatted = self.format_large_output(tool_name, call_id, trimmed);
                let parsed = serde_json::from_str::<Value>(trimmed)
                    .unwrap_or_else(|_| json!({ "status": "ok", "output": formatted }));
                let mut outcome = ToolExecOutcome::ok_json(parsed.clone(), formatted);

                // Auto-attach multimodal screenshot image when tool emits a valid screenshot file_path
                let attach_req = tool_name.contains("screenshot")
                    || parsed.get("attach_image").and_then(|b| b.as_bool()) == Some(true);
                if attach_req {
                    if let Some(fp) = parsed.get("file_path").and_then(|s| s.as_str()) {
                        let img_path = Self::resolve_path(cfg, fp);
                        if img_path.is_file() {
                            let img_ext = img_path
                                .extension()
                                .and_then(|s| s.to_str())
                                .unwrap_or("")
                                .to_ascii_lowercase();
                            let mime = match img_ext.as_str() {
                                "png" => Some("image/png"),
                                "jpg" | "jpeg" => Some("image/jpeg"),
                                "webp" => Some("image/webp"),
                                _ => None,
                            };
                            if let Some(m) = mime {
                                if let Ok(bytes) = fs::read(&img_path) {
                                    if bytes.len() <= 8 * 1024 * 1024 {
                                        outcome.inline_blobs.push(InlineBlob {
                                            mime_type: m.to_string(),
                                            data: B64.encode(&bytes),
                                        });
                                    }
                                }
                            }
                        }
                    }
                }
                outcome
            }
            Ok(Err(e)) => ToolExecOutcome::err(format!("Tool '{}' wait error: {}", tool_name, e)),
            Err(_) => ToolExecOutcome::err(format!("Tool '{}' timed out after 90s", tool_name)),
        }
    }
}

const MAX_PIPE_CAPTURE_BYTES: usize = 2 * 1024 * 1024;
const PIPE_DRAIN_GRACE: Duration = Duration::from_millis(150);

fn spawn_bounded_pipe_reader<R: AsyncRead + Unpin + Send + 'static>(
    opt_reader: Option<R>,
    max_bytes: usize,
) -> (Arc<std::sync::Mutex<Vec<u8>>>, tokio::task::JoinHandle<()>) {
    let shared = Arc::new(std::sync::Mutex::new(Vec::new()));
    let buf_ref = Arc::clone(&shared);
    let handle = tokio::spawn(async move {
        let Some(mut reader) = opt_reader else {
            return;
        };
        let mut chunk = [0u8; 8192];
        loop {
            match reader.read(&mut chunk).await {
                Ok(0) => break,
                Ok(n) => {
                    if let Ok(mut guard) = buf_ref.lock() {
                        if guard.len() < max_bytes {
                            let take = (max_bytes - guard.len()).min(n);
                            guard.extend_from_slice(&chunk[..take]);
                        }
                    }
                }
                Err(_) => break,
            }
        }
    });
    (shared, handle)
}

async fn collect_child_output_with_timeout(
    mut child: Child,
    wait_limit: Duration,
    pgid: Option<i32>,
    proc_reg: &Arc<Mutex<ProcessRegistry>>,
) -> Result<Result<(std::process::ExitStatus, Vec<u8>, Vec<u8>), std::io::Error>, ()> {
    let (out_buf, mut out_h) = spawn_bounded_pipe_reader(child.stdout.take(), MAX_PIPE_CAPTURE_BYTES);
    let (err_buf, mut err_h) = spawn_bounded_pipe_reader(child.stderr.take(), MAX_PIPE_CAPTURE_BYTES);

    if let Some(pg) = pgid {
        proc_reg.lock().await.register_fg(pg);
    }

    let wait_res = timeout(wait_limit, child.wait()).await;

    if let Some(pg) = pgid {
        proc_reg.lock().await.unregister_fg(pg);
        #[cfg(unix)]
        if wait_res.is_err() {
            unsafe {
                libc::kill(-pg, libc::SIGKILL);
            }
        }
    }

    match wait_res {
        Ok(Ok(status)) => {
            // Allow normal exited processes to hit pipe EOF; return swiftly if a background child kept FDs open.
            let _ = timeout(PIPE_DRAIN_GRACE, async {
                let _ = tokio::join!(&mut out_h, &mut err_h);
            })
            .await;
            out_h.abort();
            err_h.abort();
            let stdout_bytes = out_buf.lock().map(|g| g.clone()).unwrap_or_default();
            let stderr_bytes = err_buf.lock().map(|g| g.clone()).unwrap_or_default();
            Ok(Ok((status, stdout_bytes, stderr_bytes)))
        }
        Ok(Err(e)) => {
            out_h.abort();
            err_h.abort();
            Ok(Err(e))
        }
        Err(_) => {
            let _ = child.kill().await;
            let _ = timeout(Duration::from_millis(50), async {
                let _ = tokio::join!(&mut out_h, &mut err_h);
            })
            .await;
            out_h.abort();
            err_h.abort();
            Err(())
        }
    }
}

fn truncate_str(s: &str, max_bytes: usize) -> String {
    if s.len() <= max_bytes {
        return s.to_string();
    }
    let mut end = max_bytes;
    while end > 0 && !s.is_char_boundary(end) {
        end -= 1;
    }
    format!("{}...", &s[..end])
}

pub fn truncate_output(s: &str) -> String {
    if s.len() <= MAX_TOOL_OUTPUT_CHARS {
        return s.to_string();
    }
    let head = MAX_TOOL_OUTPUT_CHARS / 5;
    let tail = MAX_TOOL_OUTPUT_CHARS.saturating_sub(head);
    let mut h_end = head;
    while h_end > 0 && !s.is_char_boundary(h_end) {
        h_end -= 1;
    }
    let mut t_start = s.len().saturating_sub(tail);
    while t_start < s.len() && !s.is_char_boundary(t_start) {
        t_start += 1;
    }
    format!(
        "{}\n\n[... {} bytes truncated by Flowork anti-bloat guard ...]\n\n{}",
        &s[..h_end],
        s.len() - h_end - (s.len() - t_start),
        &s[t_start..]
    )
}

fn strip_html_tags(s: &str) -> String {
    let re = regex::Regex::new(r"<[^>]+>").unwrap();
    re.replace_all(s, "").trim().to_string()
}

fn core_fallback_definitions() -> Vec<(&'static str, &'static str, Value)> {
    vec![
        (
            "read_file",
            "Read file contents with line numbers or attach images/PDF/audio cleanly.",
            json!({
                "type": "object",
                "properties": {
                    "file_path": { "type": "string", "description": "File path to read" },
                    "start_line": { "type": "integer", "description": "Optional 1-indexed start line" },
                    "end_line": { "type": "integer", "description": "Optional 1-indexed end line" }
                },
                "required": ["file_path"]
            }),
        ),
        (
            "write_file",
            "Create or overwrite a file on disk.",
            json!({
                "type": "object",
                "properties": {
                    "file_path": { "type": "string" },
                    "content": { "type": "string" }
                },
                "required": ["file_path", "content"]
            }),
        ),
        (
            "replace",
            "Replace exact string occurrences inside an existing file.",
            json!({
                "type": "object",
                "properties": {
                    "file_path": { "type": "string" },
                    "old_string": { "type": "string" },
                    "new_string": { "type": "string" },
                    "allow_multiple": { "type": "boolean" }
                },
                "required": ["file_path", "old_string", "new_string"]
            }),
        ),
        (
            "run_shell_command",
            "Execute a bash shell command on the host Linux system.",
            json!({
                "type": "object",
                "properties": {
                    "command": { "type": "string" },
                    "is_background": { "type": "boolean" }
                },
                "required": ["command"]
            }),
        ),
        (
            "glob",
            "Find files matching a wildcard glob pattern.",
            json!({
                "type": "object",
                "properties": {
                    "pattern": { "type": "string" },
                    "path": { "type": "string" }
                },
                "required": ["pattern"]
            }),
        ),
        (
            "grep_search",
            "Search text across workspace files using regex.",
            json!({
                "type": "object",
                "properties": {
                    "pattern": { "type": "string" },
                    "path": { "type": "string" },
                    "include_pattern": { "type": "string" }
                },
                "required": ["pattern"]
            }),
        ),
        (
            "list_directory",
            "List directory entries.",
            json!({
                "type": "object",
                "properties": {
                    "path": { "type": "string" }
                }
            }),
        ),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Instant;

    #[tokio::test]
    async fn collect_child_output_returns_immediately_when_background_child_keeps_pipe_open() {
        let reg = Arc::new(Mutex::new(ProcessRegistry::default()));
        let mut cmd = Command::new("/bin/bash");
        cmd.args(["-c", "sleep 4 & echo detached_ok"])
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        #[cfg(unix)]
        unsafe {
            cmd.pre_exec(|| {
                libc::setpgid(0, 0);
                Ok(())
            });
        }

        let child = cmd.spawn().expect("spawn bash");
        let pgid = child.id().map(|p| p as i32);
        let t0 = Instant::now();
        let res = collect_child_output_with_timeout(child, Duration::from_secs(10), pgid, &reg).await;
        let elapsed = t0.elapsed();

        if let Some(pg) = pgid {
            #[cfg(unix)]
            unsafe {
                libc::kill(-pg, libc::SIGKILL);
            }
        }

        assert!(elapsed < Duration::from_millis(1200), "stalled waiting on background pipe: {:?}", elapsed);
        let (status, out, _err) = res.expect("not timeout").expect("ok exit");
        assert!(status.success());
        let text = String::from_utf8_lossy(&out);
        assert!(text.contains("detached_ok"), "unexpected stdout: {:?}", text);
    }

    #[tokio::test]
    async fn collect_child_output_handles_timeout_and_captures_normal_output() {
        let reg = Arc::new(Mutex::new(ProcessRegistry::default()));
        let mut ok_cmd = Command::new("/bin/bash");
        ok_cmd
            .args(["-c", "echo hello_out; echo hello_err >&2; exit 3"])
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        let ok_child = ok_cmd.spawn().unwrap();
        let (status, out, err) = collect_child_output_with_timeout(ok_child, Duration::from_secs(5), None, &reg)
            .await
            .unwrap()
            .unwrap();
        assert_eq!(status.code(), Some(3));
        assert!(String::from_utf8_lossy(&out).contains("hello_out"));
        assert!(String::from_utf8_lossy(&err).contains("hello_err"));

        let mut slow_cmd = Command::new("/bin/bash");
        slow_cmd
            .args(["-c", "sleep 5"])
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        #[cfg(unix)]
        unsafe {
            slow_cmd.pre_exec(|| {
                libc::setpgid(0, 0);
                Ok(())
            });
        }
        let slow_child = slow_cmd.spawn().unwrap();
        let pg = slow_child.id().map(|p| p as i32);
        let timed = collect_child_output_with_timeout(slow_child, Duration::from_millis(200), pg, &reg).await;
        assert!(timed.is_err());
    }
}
