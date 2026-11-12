use crate::resolve_home_dir;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashMap, HashSet, VecDeque};
use std::env;
use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::sync::Notify;
use tokio::task::JoinSet;

pub const SYSTEM_PIPELINES_DIR: &str = "/opt/floworkos/pipelines";

const STRIP_SECRET_ENVS: &[&str] = &[
    "GOOGLE_GEMINI_API_KEY",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "HF_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
];

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
#[serde(rename_all = "snake_case")]
pub enum NodeKind {
    #[default]
    BusCli,
    ToolRunner,
    SysdCdp,
    SysdUinput,
    SlmLocal,
}

impl NodeKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::BusCli => "bus_cli",
            Self::ToolRunner => "tool_runner",
            Self::SysdCdp => "sysd_cdp",
            Self::SysdUinput => "sysd_uinput",
            Self::SlmLocal => "slm_local",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WaitForSpec {
    #[serde(default)]
    pub window_title: Option<String>,
    #[serde(default)]
    pub dom_selector: Option<String>,
    #[serde(default)]
    pub file_exists: Option<String>,
    #[serde(default = "default_wait_timeout_ms")]
    pub timeout_ms: u64,
}

fn default_wait_timeout_ms() -> u64 {
    5000
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxScope {
    #[serde(default = "default_true")]
    pub strip_secrets: bool,
    #[serde(default = "default_profile")]
    pub profile: String,
    #[serde(default)]
    pub allow_network: Option<bool>,
}

impl Default for SandboxScope {
    fn default() -> Self {
        Self {
            strip_secrets: true,
            profile: default_profile(),
            allow_network: None,
        }
    }
}

fn default_true() -> bool {
    true
}

fn default_profile() -> String {
    "standard".to_string()
}

fn default_version() -> String {
    "1.0".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InputParamSpec {
    #[serde(rename = "type", default = "default_input_type")]
    pub param_type: String,
    #[serde(default)]
    pub default: Option<Value>,
    #[serde(default)]
    pub required: bool,
    #[serde(default)]
    pub description: Option<String>,
}

fn default_input_type() -> String {
    "string".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlowpipeNode {
    pub id: String,
    #[serde(default)]
    pub kind: NodeKind,
    #[serde(default)]
    pub app: Option<String>,
    #[serde(default)]
    pub action: Option<String>,
    #[serde(default)]
    pub command: Option<String>,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub params: Map<String, Value>,
    #[serde(default)]
    pub out: Option<String>,
    #[serde(default)]
    pub depends_on: Vec<String>,
    #[serde(default)]
    pub timeout_secs: Option<u64>,
    #[serde(default)]
    pub retry: Option<u32>,
    #[serde(default)]
    pub cache_by_hash: Option<bool>,
    #[serde(default)]
    pub wait_for: Option<WaitForSpec>,
    #[serde(default)]
    pub sandbox: Option<SandboxScope>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlowpipeSpec {
    #[serde(default = "default_version")]
    pub version: String,
    pub id: String,
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub inputs: BTreeMap<String, Value>,
    #[serde(default)]
    pub sandbox: Option<SandboxScope>,
    #[serde(default)]
    pub nodes: Vec<FlowpipeNode>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationReport {
    pub valid: bool,
    pub id: String,
    pub node_count: usize,
    pub topo_layers: Vec<Vec<String>>,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeExecReport {
    pub node_id: String,
    pub kind: String,
    pub status: String,
    pub cache_hit: bool,
    pub attempts: u32,
    pub duration_ms: u64,
    pub layer: usize,
    pub cache_key: String,
    #[serde(default)]
    pub out_path: Option<String>,
    pub output: Value,
    #[serde(default)]
    pub error: Option<String>,
}

#[derive(Debug, Clone)]
pub struct RunControl {
    pub run_id: String,
    pub paused: Arc<AtomicBool>,
    pub cancelled: Arc<AtomicBool>,
    pub notify: Arc<Notify>,
}

impl RunControl {
    pub fn new(run_id: String) -> Self {
        Self {
            run_id,
            paused: Arc::new(AtomicBool::new(false)),
            cancelled: Arc::new(AtomicBool::new(false)),
            notify: Arc::new(Notify::new()),
        }
    }

    pub fn pause(&self) {
        self.paused.store(true, Ordering::SeqCst);
        self.notify.notify_waiters();
    }

    pub fn resume(&self) {
        self.paused.store(false, Ordering::SeqCst);
        self.notify.notify_waiters();
    }

    pub fn cancel(&self) {
        self.cancelled.store(true, Ordering::SeqCst);
        self.paused.store(false, Ordering::SeqCst);
        self.notify.notify_waiters();
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlowpipeRunResult {
    pub status: String,
    pub run_id: String,
    pub pipeline_id: String,
    pub duration_ms: u64,
    pub nodes_completed: usize,
    pub total_nodes: usize,
    pub cache_hits: usize,
    pub llm_calls: usize,
    pub outputs: BTreeMap<String, Value>,
    pub node_reports: Vec<NodeExecReport>,
    #[serde(default)]
    pub error: Option<String>,
}

#[derive(Debug, Clone)]
pub struct PipelineDiscoveryEntry {
    pub id: String,
    pub name: String,
    pub description: String,
    pub path: String,
    pub scope: &'static str,
    pub node_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CachedNodeEntry {
    cache_key: String,
    node_id: String,
    created_at_ms: u128,
    output: Value,
    out_path: Option<String>,
    out_sha256: Option<String>,
}

pub fn user_pipelines_dir() -> PathBuf {
    if let Ok(explicit) = env::var("FLOWORK_PIPELINES_DIR") {
        let t = explicit.trim();
        if !t.is_empty() {
            return PathBuf::from(t);
        }
    }
    resolve_home_dir().join(".flowork").join("pipelines")
}

pub fn cache_root_dir() -> PathBuf {
    if let Ok(explicit) = env::var("FLOWORK_PIPE_CACHE_DIR") {
        let t = explicit.trim();
        if !t.is_empty() {
            return PathBuf::from(t);
        }
    }
    resolve_home_dir()
        .join(".cache")
        .join("flowork")
        .join("flowpipe")
}

pub fn now_ms_u128() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0)
}

pub fn parse_flowpipe_str(raw: &str, hint_path: Option<&Path>) -> Result<FlowpipeSpec, String> {
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        return Err("Empty .flowpipe document".to_string());
    }
    let looks_json = trimmed.starts_with('{')
        || hint_path
            .and_then(|p| p.extension().and_then(|e| e.to_str()))
            .map(|e| e.eq_ignore_ascii_case("json"))
            .unwrap_or(false);

    if looks_json {
        serde_json::from_str::<FlowpipeSpec>(trimmed)
            .or_else(|_| toml::from_str::<FlowpipeSpec>(trimmed))
            .map_err(|e| format!("Failed parsing .flowpipe (JSON): {}", e))
    } else {
        toml::from_str::<FlowpipeSpec>(trimmed)
            .or_else(|toml_err| {
                serde_json::from_str::<FlowpipeSpec>(trimmed).map_err(|json_err| {
                    format!(
                        "Failed parsing .flowpipe (TOML: {}; JSON: {})",
                        toml_err, json_err
                    )
                })
            })
    }
}

pub fn load_flowpipe_from_path_or_id(target: &str) -> Result<(FlowpipeSpec, PathBuf), String> {
    let p = Path::new(target);
    if p.is_file() {
        let content = fs::read_to_string(p)
            .map_err(|e| format!("Cannot read pipeline '{}': {}", p.display(), e))?;
        let spec = parse_flowpipe_str(&content, Some(p))?;
        return Ok((spec, p.to_path_buf()));
    }

    let candidate_names = if target.ends_with(".flowpipe") || target.ends_with(".toml") || target.ends_with(".json") {
        vec![target.to_string()]
    } else {
        vec![
            format!("{}.flowpipe", target),
            format!("{}.toml", target),
            format!("{}.json", target),
        ]
    };

    for dir in [user_pipelines_dir(), PathBuf::from(SYSTEM_PIPELINES_DIR)] {
        for cname in &candidate_names {
            let cand = dir.join(cname);
            if cand.is_file() {
                let content = fs::read_to_string(&cand)
                    .map_err(|e| format!("Cannot read pipeline '{}': {}", cand.display(), e))?;
                let spec = parse_flowpipe_str(&content, Some(&cand))?;
                return Ok((spec, cand));
            }
        }
    }

    for entry in discover_pipelines() {
        if entry.id == target {
            let cand = PathBuf::from(&entry.path);
            let content = fs::read_to_string(&cand)
                .map_err(|e| format!("Cannot read pipeline '{}': {}", cand.display(), e))?;
            let spec = parse_flowpipe_str(&content, Some(&cand))?;
            return Ok((spec, cand));
        }
    }

    Err(format!("Pipeline '{}' not found", target))
}

pub fn discover_pipelines() -> Vec<PipelineDiscoveryEntry> {
    let mut out = Vec::new();
    let mut seen_ids = HashSet::new();

    for (scope, dir) in [
        ("user", user_pipelines_dir()),
        ("system", PathBuf::from(SYSTEM_PIPELINES_DIR)),
    ] {
        if !dir.is_dir() {
            continue;
        }
        let Ok(entries) = fs::read_dir(&dir) else {
            continue;
        };
        let mut files: Vec<PathBuf> = entries
            .flatten()
            .map(|e| e.path())
            .filter(|p| p.is_file())
            .filter(|p| {
                matches!(
                    p.extension().and_then(|e| e.to_str()),
                    Some("flowpipe") | Some("toml") | Some("json")
                )
            })
            .collect();
        files.sort();
        for f in files {
            let Ok(raw) = fs::read_to_string(&f) else {
                continue;
            };
            let Ok(spec) = parse_flowpipe_str(&raw, Some(&f)) else {
                continue;
            };
            if !seen_ids.insert(spec.id.clone()) {
                continue;
            }
            out.push(PipelineDiscoveryEntry {
                id: spec.id.clone(),
                name: spec.name.clone().unwrap_or_else(|| spec.id.clone()),
                description: spec.description.clone().unwrap_or_default(),
                path: f.to_string_lossy().to_string(),
                scope,
                node_count: spec.nodes.len(),
            });
        }
    }
    out
}

pub fn validate_flowpipe(spec: &FlowpipeSpec) -> ValidationReport {
    let mut errors = Vec::new();
    let mut warnings = Vec::new();

    if spec.id.trim().is_empty()
        || !spec
            .id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_' || b == b'.')
    {
        errors.push(format!(
            "Invalid pipeline id '{}': must match [a-zA-Z0-9_.-]+",
            spec.id
        ));
    }

    if spec.nodes.is_empty() {
        errors.push("Pipeline must contain at least one node".to_string());
    }

    let mut id_set = HashSet::new();
    for node in &spec.nodes {
        if node.id.trim().is_empty() {
            errors.push("Node id cannot be empty".to_string());
            continue;
        }
        if !id_set.insert(node.id.as_str()) {
            errors.push(format!("Duplicate node id '{}'", node.id));
        }
        if matches!(node.kind, NodeKind::BusCli)
            && node.app.as_deref().unwrap_or("").trim().is_empty()
            && node.command.as_deref().unwrap_or("").trim().is_empty()
        {
            errors.push(format!(
                "Node '{}' of kind 'bus_cli' requires 'app' or 'command'",
                node.id
            ));
        }
        if node.retry.unwrap_or(0) > 5 {
            warnings.push(format!(
                "Node '{}' retry={} is high; capping at 5 at runtime",
                node.id,
                node.retry.unwrap_or(0)
            ));
        }
    }

    // Kahn's topological layering + cycle detection
    let mut in_degree: HashMap<String, usize> = HashMap::new();
    let mut adj: HashMap<String, Vec<String>> = HashMap::new();

    for node in &spec.nodes {
        in_degree.entry(node.id.clone()).or_insert(0);
        adj.entry(node.id.clone()).or_default();
    }

    for node in &spec.nodes {
        for dep in &node.depends_on {
            if !id_set.contains(dep.as_str()) {
                errors.push(format!(
                    "Node '{}' depends on unknown node '{}'",
                    node.id, dep
                ));
                continue;
            }
            if dep == &node.id {
                errors.push(format!("Node '{}' cannot depend on itself", node.id));
                continue;
            }
            if let Some(d) = in_degree.get_mut(&node.id) {
                *d += 1;
            }
            if let Some(children) = adj.get_mut(dep) {
                children.push(node.id.clone());
            }
        }
    }

    let mut layers = Vec::new();
    let mut queue: VecDeque<String> = in_degree
        .iter()
        .filter(|(_, deg)| **deg == 0)
        .map(|(k, _)| k.clone())
        .collect();
    let mut queue_vec: Vec<String> = queue.drain(..).collect();
    queue_vec.sort();
    queue.extend(queue_vec);

    let mut visited = 0usize;
    while !queue.is_empty() {
        let mut layer = Vec::new();
        let mut next_layer = Vec::new();
        while let Some(nid) = queue.pop_front() {
            visited += 1;
            layer.push(nid.clone());
            if let Some(children) = adj.get(&nid) {
                for child in children {
                    if let Some(deg) = in_degree.get_mut(child) {
                        *deg -= 1;
                        if *deg == 0 {
                            next_layer.push(child.clone());
                        }
                    }
                }
            }
        }
        next_layer.sort();
        queue.extend(next_layer);
        if !layer.is_empty() {
            layers.push(layer);
        }
    }

    if visited != id_set.len() && errors.is_empty() {
        errors.push("Dependency cycle detected in pipeline nodes".to_string());
    }

    ValidationReport {
        valid: errors.is_empty(),
        id: spec.id.clone(),
        node_count: spec.nodes.len(),
        topo_layers: layers,
        errors,
        warnings,
    }
}

pub fn resolve_inputs(
    spec: &FlowpipeSpec,
    overrides: &Map<String, Value>,
) -> Result<Map<String, Value>, String> {
    let mut resolved = Map::new();

    for (key, def_val) in &spec.inputs {
        if let Some(ov) = overrides.get(key) {
            resolved.insert(key.clone(), ov.clone());
            continue;
        }
        if let Some(obj) = def_val.as_object() {
            if let Some(default) = obj.get("default") {
                if !default.is_null() {
                    resolved.insert(key.clone(), default.clone());
                    continue;
                }
            }
            if obj.get("required").and_then(|v| v.as_bool()).unwrap_or(false) {
                return Err(format!("Missing required pipeline input '{}'", key));
            }
        } else if !def_val.is_null() {
            resolved.insert(key.clone(), def_val.clone());
        }
    }

    for (key, val) in overrides {
        resolved.entry(key.clone()).or_insert_with(|| val.clone());
    }

    Ok(resolved)
}

fn value_to_template_str(val: &Value) -> String {
    match val {
        Value::Null => String::new(),
        Value::String(s) => s.clone(),
        Value::Bool(b) => b.to_string(),
        Value::Number(n) => n.to_string(),
        other => serde_json::to_string(other).unwrap_or_default(),
    }
}

fn lookup_node_field(node_out: &Value, field: &str) -> Option<String> {
    if field == "out" {
        if let Some(s) = node_out
            .get("out_path")
            .or_else(|| node_out.get("out"))
            .or_else(|| node_out.get("file"))
            .or_else(|| node_out.get("path"))
            .and_then(|v| v.as_str())
        {
            return Some(s.to_string());
        }
    }
    if let Some(v) = node_out.get(field) {
        return Some(value_to_template_str(v));
    }
    if field == "output" {
        return Some(value_to_template_str(node_out));
    }
    None
}

pub fn render_template_string(
    raw: &str,
    inputs: &Map<String, Value>,
    work_dir: &Path,
    out_dir: &Path,
    node_outputs: &HashMap<String, Value>,
) -> String {
    let mut s = raw
        .replace("{{work}}", &work_dir.to_string_lossy())
        .replace("{{out}}", &out_dir.to_string_lossy());

    let re = Regex::new(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}").expect("valid regex");
    s = re
        .replace_all(&s, |caps: &regex::Captures<'_>| {
            let expr = &caps[1];
            if let Some(input_key) = expr.strip_prefix("inputs.") {
                if let Some(val) = inputs.get(input_key) {
                    return value_to_template_str(val);
                }
            } else if let Some((nid, field)) = expr.split_once('.') {
                if let Some(nval) = node_outputs.get(nid) {
                    if let Some(found) = lookup_node_field(nval, field) {
                        return found;
                    }
                }
            }
            caps[0].to_string()
        })
        .to_string();
    s
}

fn render_template_value(
    val: &Value,
    inputs: &Map<String, Value>,
    work_dir: &Path,
    out_dir: &Path,
    node_outputs: &HashMap<String, Value>,
) -> Value {
    match val {
        Value::String(s) => Value::String(render_template_string(
            s,
            inputs,
            work_dir,
            out_dir,
            node_outputs,
        )),
        Value::Array(arr) => Value::Array(
            arr.iter()
                .map(|v| render_template_value(v, inputs, work_dir, out_dir, node_outputs))
                .collect(),
        ),
        Value::Object(map) => {
            let mut m = Map::new();
            for (k, v) in map {
                m.insert(
                    k.clone(),
                    render_template_value(v, inputs, work_dir, out_dir, node_outputs),
                );
            }
            Value::Object(m)
        }
        other => other.clone(),
    }
}

fn sha256_file_hex(path: &Path) -> Option<String> {
    let bytes = fs::read(path).ok()?;
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    Some(format!("{:x}", hasher.finalize()))
}

fn compute_node_cache_key(
    node: &FlowpipeNode,
    resolved_command: Option<&str>,
    resolved_args: &[String],
    resolved_params: &Map<String, Value>,
    resolved_out: Option<&str>,
    dep_outputs: &[(String, String)],
) -> String {
    let mut hasher = Sha256::new();
    hasher.update(node.id.as_bytes());
    hasher.update(b"|");
    hasher.update(node.kind.as_str().as_bytes());
    hasher.update(b"|");
    hasher.update(node.app.as_deref().unwrap_or("").as_bytes());
    hasher.update(b"|");
    hasher.update(node.action.as_deref().unwrap_or("").as_bytes());
    hasher.update(b"|");
    hasher.update(resolved_command.unwrap_or("").as_bytes());
    hasher.update(b"|");
    for a in resolved_args {
        hasher.update(a.as_bytes());
        hasher.update(b"\0");
        let p = Path::new(a);
        if resolved_out != Some(a.as_str()) && p.is_file() {
            if let Some(fhash) = sha256_file_hex(p) {
                hasher.update(b"F:");
                hasher.update(fhash.as_bytes());
            }
        }
    }
    let sorted_params: BTreeMap<String, Value> = resolved_params
        .iter()
        .map(|(k, v)| (k.clone(), v.clone()))
        .collect();
    if let Ok(json_bytes) = serde_json::to_vec(&sorted_params) {
        hasher.update(&json_bytes);
    }
    for (_, val) in sorted_params {
        if let Some(s) = val.as_str() {
            let p = Path::new(s);
            if resolved_out != Some(s) && p.is_file() {
                if let Some(fhash) = sha256_file_hex(p) {
                    hasher.update(b"PF:");
                    hasher.update(fhash.as_bytes());
                }
            }
        }
    }
    hasher.update(b"|OUT:");
    hasher.update(resolved_out.unwrap_or("").as_bytes());
    for (dep_id, dep_json) in dep_outputs {
        hasher.update(b"|DEP:");
        hasher.update(dep_id.as_bytes());
        hasher.update(b"=");
        hasher.update(dep_json.as_bytes());
    }
    format!("{:x}", hasher.finalize())
}

fn cache_entry_path(cache_key: &str) -> PathBuf {
    cache_root_dir().join("artifacts").join(format!("{}.json", cache_key))
}

fn try_load_cached_node(cache_key: &str) -> Option<CachedNodeEntry> {
    let p = cache_entry_path(cache_key);
    let raw = fs::read_to_string(p).ok()?;
    let entry: CachedNodeEntry = serde_json::from_str(&raw).ok()?;
    if let Some(ref out_p) = entry.out_path {
        let op = Path::new(out_p);
        if !op.is_file() {
            return None;
        }
        if let Some(ref expected_sha) = entry.out_sha256 {
            let actual_sha = sha256_file_hex(op)?;
            if &actual_sha != expected_sha {
                return None;
            }
        }
    }
    Some(entry)
}

fn store_cached_node(entry: &CachedNodeEntry) {
    let p = cache_entry_path(&entry.cache_key);
    if let Some(parent) = p.parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Ok(raw) = serde_json::to_string_pretty(entry) {
        let _ = fs::write(p, raw);
    }
}

pub fn discover_cli_binary(app_name: &str) -> Option<String> {
    if app_name.is_empty()
        || !app_name
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_' || b == b'.')
    {
        return None;
    }
    let is_exec = |p: &Path| -> bool {
        fs::metadata(p)
            .map(|m| m.is_file() && (m.permissions().mode() & 0o111 != 0))
            .unwrap_or(false)
    };
    let candidates = [
        format!("/opt/floworkos/apps/{}/bin/{}-cli", app_name, app_name),
        format!("/opt/floworkos/apps/{}/bin/{}", app_name, app_name),
        format!("/opt/floworkos/bin/{}-cli", app_name),
        format!("/opt/floworkos/bin/{}", app_name),
        format!("/usr/local/bin/{}", app_name),
        format!("/usr/bin/{}", app_name),
    ];
    for c in candidates {
        let p = Path::new(&c);
        if is_exec(p) {
            return Some(c);
        }
    }
    if let Ok(env_path) = env::var("PATH") {
        for dir in env_path.split(':') {
            let full = Path::new(dir).join(app_name);
            if is_exec(&full) {
                return Some(full.to_string_lossy().to_string());
            }
        }
    }
    None
}

async fn run_wait_for(
    spec: &WaitForSpec,
    inputs: &Map<String, Value>,
    work_dir: &Path,
    out_dir: &Path,
    node_outputs: &HashMap<String, Value>,
    sysd_url: &str,
    client: &reqwest::Client,
) -> Result<(), String> {
    let deadline = Instant::now() + Duration::from_millis(spec.timeout_ms.clamp(100, 120_000));
    loop {
        let mut all_satisfied = true;

        if let Some(ref fpat) = spec.file_exists {
            let rendered = render_template_string(fpat, inputs, work_dir, out_dir, node_outputs);
            if !Path::new(&rendered).exists() {
                all_satisfied = false;
            }
        }

        if all_satisfied {
            if let Some(ref wpat) = spec.window_title {
                let target = render_template_string(wpat, inputs, work_dir, out_dir, node_outputs)
                    .to_ascii_lowercase();
                let resp = client
                    .get(format!("{}/api/system/windows", sysd_url.trim_end_matches('/')))
                    .timeout(Duration::from_secs(2))
                    .send()
                    .await;
                let matched = match resp {
                    Ok(r) if r.status().is_success() => {
                        let body = r.text().await.unwrap_or_default().to_ascii_lowercase();
                        body.contains(&target)
                    }
                    _ => false,
                };
                if !matched {
                    all_satisfied = false;
                }
            }
        }

        if all_satisfied {
            if let Some(ref sel) = spec.dom_selector {
                let rendered_sel =
                    render_template_string(sel, inputs, work_dir, out_dir, node_outputs);
                let js_expr = format!(
                    "Boolean(document.querySelector({}))",
                    serde_json::to_string(&rendered_sel).unwrap_or_else(|_| "\"\"".to_string())
                );
                let resp = client
                    .post(format!(
                        "{}/api/agent/browser/eval",
                        sysd_url.trim_end_matches('/')
                    ))
                    .json(&json!({ "expression": js_expr }))
                    .timeout(Duration::from_secs(2))
                    .send()
                    .await;
                let matched = match resp {
                    Ok(r) if r.status().is_success() => {
                        let v: Value = r.json().await.unwrap_or(Value::Null);
                        v.get("result").and_then(|x| x.as_bool()) == Some(true)
                            || v.get("value").and_then(|x| x.as_bool()) == Some(true)
                    }
                    _ => false,
                };
                if !matched {
                    all_satisfied = false;
                }
            }
        }

        if all_satisfied {
            return Ok(());
        }
        if Instant::now() >= deadline {
            return Err("wait_for assertion timed out".to_string());
        }
        tokio::time::sleep(Duration::from_millis(120)).await;
    }
}

fn split_cmd_tokens(raw: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut in_single = false;
    let mut in_double = false;
    let mut escaped = false;

    for ch in raw.chars() {
        if escaped {
            cur.push(ch);
            escaped = false;
            continue;
        }
        if ch == '\\' && !in_single {
            escaped = true;
            continue;
        }
        if ch == '\'' && !in_double {
            in_single = !in_single;
            continue;
        }
        if ch == '"' && !in_single {
            in_double = !in_double;
            continue;
        }
        if ch.is_whitespace() && !in_single && !in_double {
            if !cur.is_empty() {
                out.push(std::mem::take(&mut cur));
            }
        } else {
            cur.push(ch);
        }
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

#[allow(clippy::too_many_arguments)]
async fn execute_single_node(
    node: FlowpipeNode,
    pipeline_id: String,
    run_id: String,
    resolved_command: Option<String>,
    resolved_args: Vec<String>,
    resolved_params: Map<String, Value>,
    resolved_out: Option<String>,
    strip_secrets: bool,
    sysd_url: String,
    client: reqwest::Client,
) -> Result<Value, String> {
    let timeout_secs = node.timeout_secs.unwrap_or(120).clamp(1, 600);

    match node.kind {
        NodeKind::BusCli => {
            let mut argv: Vec<String> = Vec::new();
            let bin_path = if let Some(ref cmd_str) = resolved_command {
                let parts = split_cmd_tokens(cmd_str);
                if parts.is_empty() {
                    return Err(format!("Node '{}' has empty command", node.id));
                }
                let head = &parts[0];
                let resolved_head = if Path::new(head).is_file() {
                    head.clone()
                } else {
                    discover_cli_binary(head).unwrap_or_else(|| head.clone())
                };
                argv.extend(parts.into_iter().skip(1));
                resolved_head
            } else {
                let app = node.app.as_deref().unwrap_or("");
                discover_cli_binary(app)
                    .ok_or_else(|| format!("Headless binary for app '{}' not found", app))?
            };

            if let Some(ref act) = node.action {
                let a = act.trim();
                if !a.is_empty() && a != "run" && a != "default" {
                    argv.push(a.to_string());
                }
            }
            argv.extend(resolved_args);
            for (k, v) in &resolved_params {
                match v {
                    Value::Bool(true) => argv.push(format!("--{}", k)),
                    Value::Bool(false) | Value::Null => {}
                    Value::String(s) => {
                        argv.push(format!("--{}", k));
                        argv.push(s.clone());
                    }
                    other => {
                        argv.push(format!("--{}", k));
                        argv.push(other.to_string());
                    }
                }
            }

            if let Some(ref out_p) = resolved_out {
                if let Some(parent) = Path::new(out_p).parent() {
                    let _ = fs::create_dir_all(parent);
                }
            }

            let nid = node.id.clone();
            let out_p_clone = resolved_out.clone();
            let exec_res = tokio::task::spawn_blocking(move || {
                let mut cmd = Command::new(&bin_path);
                cmd.args(&argv)
                    .env("FLOWORK_PIPELINE_ID", &pipeline_id)
                    .env("FLOWORK_RUN_ID", &run_id)
                    .env("FLOWORK_NODE_ID", &nid)
                    .stdin(Stdio::null())
                    .stdout(Stdio::piped())
                    .stderr(Stdio::piped());
                if strip_secrets {
                    for k in STRIP_SECRET_ENVS {
                        cmd.env_remove(k);
                    }
                    cmd.env("FLOWORK_SANDBOXED", "1");
                }
                cmd.output().map(|o| (o, bin_path))
            });

            let (out, bin_used) = tokio::time::timeout(Duration::from_secs(timeout_secs), exec_res)
                .await
                .map_err(|_| format!("Node '{}' timed out after {}s", node.id, timeout_secs))?
                .map_err(|e| e.to_string())?
                .map_err(|e| format!("Failed spawning node '{}': {}", node.id, e))?;

            if !out.status.success() {
                let err_s = String::from_utf8_lossy(&out.stderr).trim().to_string();
                let out_s = String::from_utf8_lossy(&out.stdout).trim().to_string();
                let msg = if !err_s.is_empty() {
                    err_s
                } else if !out_s.is_empty() {
                    out_s
                } else {
                    format!("Exit code {:?}", out.status.code())
                };
                return Err(msg);
            }

            let raw_stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
            let mut val = serde_json::from_str::<Value>(&raw_stdout)
                .unwrap_or_else(|_| json!({ "output": raw_stdout }));
            if let Some(obj) = val.as_object_mut() {
                obj.entry("binary".to_string())
                    .or_insert_with(|| Value::String(bin_used));
                if let Some(op) = out_p_clone {
                    obj.entry("out".to_string())
                        .or_insert_with(|| Value::String(op.clone()));
                    obj.entry("out_path".to_string())
                        .or_insert_with(|| Value::String(op));
                }
            }
            Ok(val)
        }
        NodeKind::ToolRunner => {
            let tool_name = node
                .app
                .as_deref()
                .or(node.action.as_deref())
                .ok_or_else(|| format!("tool_runner node '{}' requires 'app' (tool name)", node.id))?
                .to_string();
            let runner = "/opt/floworkos/bin/flowork-tool-runner";
            let payload_json = Value::Object(resolved_params).to_string();
            let exec_res = tokio::task::spawn_blocking(move || {
                let mut cmd = Command::new(runner);
                cmd.arg(&tool_name)
                    .arg(&payload_json)
                    .stdin(Stdio::null())
                    .stdout(Stdio::piped())
                    .stderr(Stdio::piped());
                if strip_secrets {
                    for k in STRIP_SECRET_ENVS {
                        cmd.env_remove(k);
                    }
                    cmd.env("FLOWORK_SANDBOXED", "1");
                }
                cmd.output()
            });
            let out = tokio::time::timeout(Duration::from_secs(timeout_secs), exec_res)
                .await
                .map_err(|_| format!("tool_runner '{}' timed out", node.id))?
                .map_err(|e| e.to_string())?
                .map_err(|e| format!("tool_runner spawn error: {}", e))?;
            if !out.status.success() {
                return Err(String::from_utf8_lossy(&out.stderr).trim().to_string());
            }
            let raw = String::from_utf8_lossy(&out.stdout).trim().to_string();
            Ok(serde_json::from_str::<Value>(&raw).unwrap_or_else(|_| json!({ "output": raw })))
        }
        NodeKind::SysdCdp => {
            let action = node.action.as_deref().unwrap_or("status");
            let url = format!(
                "{}/api/agent/browser/{}",
                sysd_url.trim_end_matches('/'),
                action.trim_start_matches('/')
            );
            let resp = client
                .post(url)
                .json(&Value::Object(resolved_params))
                .timeout(Duration::from_secs(timeout_secs))
                .send()
                .await
                .map_err(|e| format!("sysd_cdp '{}' request error: {}", node.id, e))?;
            let status = resp.status();
            let body: Value = resp.json().await.unwrap_or_else(|_| json!({}));
            if !status.is_success() {
                return Err(format!("sysd_cdp '{}' HTTP {}: {}", node.id, status, body));
            }
            Ok(body)
        }
        NodeKind::SysdUinput => {
            let mut body_map = resolved_params;
            if let Some(ref act) = node.action {
                body_map
                    .entry("action".to_string())
                    .or_insert_with(|| Value::String(act.clone()));
            }
            let url = format!("{}/api/agent/app/input", sysd_url.trim_end_matches('/'));
            let resp = client
                .post(url)
                .json(&Value::Object(body_map))
                .timeout(Duration::from_secs(timeout_secs))
                .send()
                .await
                .map_err(|e| format!("sysd_uinput '{}' request error: {}", node.id, e))?;
            let status = resp.status();
            let body: Value = resp.json().await.unwrap_or_else(|_| json!({}));
            if !status.is_success() {
                return Err(format!("sysd_uinput '{}' HTTP {}: {}", node.id, status, body));
            }
            Ok(body)
        }
        NodeKind::SlmLocal => {
            let prompt_txt = resolved_params
                .get("prompt")
                .and_then(|v| v.as_str())
                .map(str::to_string)
                .or_else(|| resolved_args.first().cloned())
                .unwrap_or_default();
            let slm_bin = "/opt/floworkos/bin/flowork-slm";
            if Path::new(slm_bin).is_file() {
                let exec_res = tokio::task::spawn_blocking(move || {
                    Command::new(slm_bin)
                        .arg(&prompt_txt)
                        .arg("--json")
                        .output()
                });
                let out = tokio::time::timeout(Duration::from_secs(timeout_secs), exec_res)
                    .await
                    .map_err(|_| format!("slm_local '{}' timed out", node.id))?
                    .map_err(|e| e.to_string())?
                    .map_err(|e| format!("slm_local spawn error: {}", e))?;
                if !out.status.success() {
                    return Err(String::from_utf8_lossy(&out.stderr).trim().to_string());
                }
                let raw = String::from_utf8_lossy(&out.stdout).trim().to_string();
                Ok(serde_json::from_str::<Value>(&raw).unwrap_or_else(|_| json!({ "output": raw })))
            } else {
                let url = format!("{}/api/agent/l0/triage", sysd_url.trim_end_matches('/'));
                let resp = client
                    .post(url)
                    .json(&json!({ "prompt": prompt_txt }))
                    .timeout(Duration::from_secs(timeout_secs))
                    .send()
                    .await
                    .map_err(|e| format!("slm_local HTTP error: {}", e))?;
                Ok(resp.json().await.unwrap_or_else(|_| json!({})))
            }
        }
    }
}

pub type EventSink = Arc<dyn Fn(Value) + Send + Sync>;

pub async fn execute_flowpipe_dag(
    spec: FlowpipeSpec,
    input_overrides: Map<String, Value>,
    use_cache: bool,
    control: Arc<RunControl>,
    event_sink: Option<EventSink>,
) -> FlowpipeRunResult {
    let t0 = Instant::now();
    let emit = |evt: Value| {
        if let Some(ref sink) = event_sink {
            sink(evt);
        }
    };

    let validation = validate_flowpipe(&spec);
    if !validation.valid {
        let msg = validation.errors.join("; ");
        emit(json!({
            "type": "pipe.run.finished",
            "run_id": control.run_id,
            "pipeline_id": spec.id,
            "status": "error",
            "error": msg
        }));
        return FlowpipeRunResult {
            status: "error".to_string(),
            run_id: control.run_id.clone(),
            pipeline_id: spec.id,
            duration_ms: t0.elapsed().as_millis() as u64,
            nodes_completed: 0,
            total_nodes: spec.nodes.len(),
            cache_hits: 0,
            llm_calls: 0,
            outputs: BTreeMap::new(),
            node_reports: Vec::new(),
            error: Some(msg),
        };
    }

    let resolved_inputs = match resolve_inputs(&spec, &input_overrides) {
        Ok(m) => m,
        Err(msg) => {
            emit(json!({
                "type": "pipe.run.finished",
                "run_id": control.run_id,
                "pipeline_id": spec.id,
                "status": "error",
                "error": msg
            }));
            return FlowpipeRunResult {
                status: "error".to_string(),
                run_id: control.run_id.clone(),
                pipeline_id: spec.id,
                duration_ms: t0.elapsed().as_millis() as u64,
                nodes_completed: 0,
                total_nodes: spec.nodes.len(),
                cache_hits: 0,
                llm_calls: 0,
                outputs: BTreeMap::new(),
                node_reports: Vec::new(),
                error: Some(msg),
            };
        }
    };

    let work_dir = env::var("FLOWORK_PIPE_WORK_DIR")
        .ok()
        .filter(|s| !s.trim().is_empty())
        .map(PathBuf::from)
        .unwrap_or_else(|| cache_root_dir().join("work").join(&spec.id));
    let out_dir = env::var("FLOWORK_PIPE_OUT_DIR")
        .ok()
        .filter(|s| !s.trim().is_empty())
        .map(PathBuf::from)
        .unwrap_or_else(|| cache_root_dir().join("out").join(&spec.id));
    let _ = fs::create_dir_all(&work_dir);
    let _ = fs::create_dir_all(&out_dir);

    let sysd_url = env::var("FLOWORK_SYSD_URL").unwrap_or_else(|_| "http://127.0.0.1:18090".to_string());
    let client = reqwest::Client::new();

    emit(json!({
        "type": "pipe.run.started",
        "run_id": control.run_id,
        "pipeline_id": spec.id,
        "name": spec.name.clone().unwrap_or_else(|| spec.id.clone()),
        "total_nodes": spec.nodes.len(),
        "layers": validation.topo_layers
    }));

    let mut node_map: HashMap<String, FlowpipeNode> = HashMap::new();
    for n in &spec.nodes {
        node_map.insert(n.id.clone(), n.clone());
    }

    let mut node_outputs: HashMap<String, Value> = HashMap::new();
    let mut reports: Vec<NodeExecReport> = Vec::new();
    let mut cache_hits = 0usize;
    let pipeline_strip = spec
        .sandbox
        .as_ref()
        .map(|s| s.strip_secrets)
        .unwrap_or(true);

    for (layer_idx, layer) in validation.topo_layers.iter().enumerate() {
        while control.paused.load(Ordering::SeqCst) && !control.cancelled.load(Ordering::SeqCst) {
            control.notify.notified().await;
        }
        if control.cancelled.load(Ordering::SeqCst) {
            emit(json!({
                "type": "pipe.run.finished",
                "run_id": control.run_id,
                "pipeline_id": spec.id,
                "status": "cancelled"
            }));
            return FlowpipeRunResult {
                status: "cancelled".to_string(),
                run_id: control.run_id.clone(),
                pipeline_id: spec.id,
                duration_ms: t0.elapsed().as_millis() as u64,
                nodes_completed: reports.len(),
                total_nodes: spec.nodes.len(),
                cache_hits,
                llm_calls: 0,
                outputs: node_outputs.into_iter().collect(),
                node_reports: reports,
                error: Some("Cancelled by operator".to_string()),
            };
        }

        let mut join_set: JoinSet<(String, NodeExecReport)> = JoinSet::new();

        for nid in layer {
            let node = node_map[nid].clone();
            let resolved_cmd = node.command.as_ref().map(|c| {
                render_template_string(c, &resolved_inputs, &work_dir, &out_dir, &node_outputs)
            });
            let resolved_args: Vec<String> = node
                .args
                .iter()
                .map(|a| {
                    render_template_string(a, &resolved_inputs, &work_dir, &out_dir, &node_outputs)
                })
                .collect();
            let mut resolved_params = Map::new();
            for (k, v) in &node.params {
                resolved_params.insert(
                    k.clone(),
                    render_template_value(v, &resolved_inputs, &work_dir, &out_dir, &node_outputs),
                );
            }
            let resolved_out = node.out.as_ref().map(|o| {
                render_template_string(o, &resolved_inputs, &work_dir, &out_dir, &node_outputs)
            });

            let dep_outputs: Vec<(String, String)> = node
                .depends_on
                .iter()
                .map(|d| {
                    let v = node_outputs.get(d).cloned().unwrap_or(Value::Null);
                    (d.clone(), serde_json::to_string(&v).unwrap_or_default())
                })
                .collect();

            let cache_key = compute_node_cache_key(
                &node,
                resolved_cmd.as_deref(),
                &resolved_args,
                &resolved_params,
                resolved_out.as_deref(),
                &dep_outputs,
            );

            let node_cacheable = use_cache && node.cache_by_hash.unwrap_or(true);
            let strip_secrets = node
                .sandbox
                .as_ref()
                .map(|s| s.strip_secrets)
                .unwrap_or(pipeline_strip);

            let inputs_clone = resolved_inputs.clone();
            let work_clone = work_dir.clone();
            let out_clone = out_dir.clone();
            let outputs_snapshot = node_outputs.clone();
            let sysd_clone = sysd_url.clone();
            let client_clone = client.clone();
            let pid_clone = spec.id.clone();
            let rid_clone = control.run_id.clone();
            let sink_clone = event_sink.clone();

            if let Some(ref sink) = sink_clone {
                sink(json!({
                    "type": "pipe.node.started",
                    "run_id": rid_clone,
                    "pipeline_id": pid_clone,
                    "node_id": node.id,
                    "kind": node.kind.as_str(),
                    "layer": layer_idx
                }));
            }

            join_set.spawn(async move {
                let nt0 = Instant::now();
                let nid_inner = node.id.clone();
                let kind_str = node.kind.as_str().to_string();

                if node_cacheable {
                    if let Some(hit) = try_load_cached_node(&cache_key) {
                        if let Some(ref sink) = sink_clone {
                            sink(json!({
                                "type": "pipe.node.log",
                                "run_id": rid_clone,
                                "node_id": nid_inner,
                                "line": format!("Cache hit ({})", &cache_key[..12])
                            }));
                        }
                        let rep = NodeExecReport {
                            node_id: nid_inner.clone(),
                            kind: kind_str,
                            status: "ok".to_string(),
                            cache_hit: true,
                            attempts: 0,
                            duration_ms: nt0.elapsed().as_millis() as u64,
                            layer: layer_idx,
                            cache_key,
                            out_path: hit.out_path,
                            output: hit.output,
                            error: None,
                        };
                        return (nid_inner, rep);
                    }
                }

                if let Some(ref wf) = node.wait_for {
                    if let Err(err) = run_wait_for(
                        wf,
                        &inputs_clone,
                        &work_clone,
                        &out_clone,
                        &outputs_snapshot,
                        &sysd_clone,
                        &client_clone,
                    )
                    .await
                    {
                        let rep = NodeExecReport {
                            node_id: nid_inner.clone(),
                            kind: kind_str,
                            status: "error".to_string(),
                            cache_hit: false,
                            attempts: 0,
                            duration_ms: nt0.elapsed().as_millis() as u64,
                            layer: layer_idx,
                            cache_key,
                            out_path: resolved_out,
                            output: Value::Null,
                            error: Some(err),
                        };
                        return (nid_inner, rep);
                    }
                }

                let max_retries = node.retry.unwrap_or(0).min(5);
                let mut attempts = 0u32;
                let mut last_err = None;
                let mut final_val = None;

                for attempt in 0..=max_retries {
                    attempts = attempt + 1;
                    match execute_single_node(
                        node.clone(),
                        pid_clone.clone(),
                        rid_clone.clone(),
                        resolved_cmd.clone(),
                        resolved_args.clone(),
                        resolved_params.clone(),
                        resolved_out.clone(),
                        strip_secrets,
                        sysd_clone.clone(),
                        client_clone.clone(),
                    )
                    .await
                    {
                        Ok(val) => {
                            final_val = Some(val);
                            last_err = None;
                            break;
                        }
                        Err(e) => {
                            last_err = Some(e.clone());
                            if let Some(ref sink) = sink_clone {
                                sink(json!({
                                    "type": "pipe.node.log",
                                    "run_id": rid_clone,
                                    "node_id": nid_inner,
                                    "line": format!("Attempt {}/{} failed: {}", attempts, max_retries + 1, e)
                                }));
                            }
                            if attempt < max_retries {
                                tokio::time::sleep(Duration::from_millis(250 * (attempt as u64 + 1))).await;
                            }
                        }
                    }
                }

                if let Some(out_val) = final_val {
                    let effective_out = resolved_out.clone().or_else(|| {
                        out_val
                            .get("out_path")
                            .or_else(|| out_val.get("out"))
                            .or_else(|| out_val.get("file"))
                            .and_then(|v| v.as_str())
                            .map(str::to_string)
                    });
                    if node_cacheable {
                        let out_sha = effective_out
                            .as_ref()
                            .and_then(|p| sha256_file_hex(Path::new(p)));
                        store_cached_node(&CachedNodeEntry {
                            cache_key: cache_key.clone(),
                            node_id: nid_inner.clone(),
                            created_at_ms: now_ms_u128(),
                            output: out_val.clone(),
                            out_path: effective_out.clone(),
                            out_sha256: out_sha,
                        });
                    }
                    let rep = NodeExecReport {
                        node_id: nid_inner.clone(),
                        kind: kind_str,
                        status: "ok".to_string(),
                        cache_hit: false,
                        attempts,
                        duration_ms: nt0.elapsed().as_millis() as u64,
                        layer: layer_idx,
                        cache_key,
                        out_path: effective_out,
                        output: out_val,
                        error: None,
                    };
                    (nid_inner, rep)
                } else {
                    let rep = NodeExecReport {
                        node_id: nid_inner.clone(),
                        kind: kind_str,
                        status: "error".to_string(),
                        cache_hit: false,
                        attempts,
                        duration_ms: nt0.elapsed().as_millis() as u64,
                        layer: layer_idx,
                        cache_key,
                        out_path: resolved_out,
                        output: Value::Null,
                        error: last_err,
                    };
                    (nid_inner, rep)
                }
            });
        }

        let mut layer_failed: Option<String> = None;
        while let Some(res) = join_set.join_next().await {
            if control.cancelled.load(Ordering::SeqCst) {
                join_set.abort_all();
                emit(json!({
                    "type": "pipe.run.finished",
                    "run_id": control.run_id,
                    "pipeline_id": spec.id,
                    "status": "cancelled"
                }));
                return FlowpipeRunResult {
                    status: "cancelled".to_string(),
                    run_id: control.run_id.clone(),
                    pipeline_id: spec.id,
                    duration_ms: t0.elapsed().as_millis() as u64,
                    nodes_completed: reports.len(),
                    total_nodes: spec.nodes.len(),
                    cache_hits,
                    llm_calls: 0,
                    outputs: node_outputs.into_iter().collect(),
                    node_reports: reports,
                    error: Some("Cancelled by operator".to_string()),
                };
            }

            match res {
                Ok((nid, rep)) => {
                    if rep.cache_hit {
                        cache_hits += 1;
                    }
                    emit(json!({
                        "type": "pipe.node.done",
                        "run_id": control.run_id,
                        "pipeline_id": spec.id,
                        "node_id": nid,
                        "status": rep.status,
                        "cache_hit": rep.cache_hit,
                        "duration_ms": rep.duration_ms,
                        "output": rep.output,
                        "error": rep.error
                    }));
                    if rep.status == "ok" {
                        node_outputs.insert(nid, rep.output.clone());
                    } else if layer_failed.is_none() {
                        layer_failed = rep.error.clone().or_else(|| Some(format!("Node '{}' failed", nid)));
                    }
                    reports.push(rep);
                }
                Err(e) => {
                    if layer_failed.is_none() {
                        layer_failed = Some(format!("Task join error: {}", e));
                    }
                }
            }
        }

        if let Some(err_msg) = layer_failed {
            emit(json!({
                "type": "pipe.run.finished",
                "run_id": control.run_id,
                "pipeline_id": spec.id,
                "status": "error",
                "duration_ms": t0.elapsed().as_millis() as u64,
                "cache_hits": cache_hits,
                "error": err_msg
            }));
            return FlowpipeRunResult {
                status: "error".to_string(),
                run_id: control.run_id.clone(),
                pipeline_id: spec.id,
                duration_ms: t0.elapsed().as_millis() as u64,
                nodes_completed: node_outputs.len(),
                total_nodes: spec.nodes.len(),
                cache_hits,
                llm_calls: 0,
                outputs: node_outputs.into_iter().collect(),
                node_reports: reports,
                error: Some(err_msg),
            };
        }
    }

    let total_ms = t0.elapsed().as_millis() as u64;
    emit(json!({
        "type": "pipe.run.finished",
        "run_id": control.run_id,
        "pipeline_id": spec.id,
        "status": "ok",
        "duration_ms": total_ms,
        "cache_hits": cache_hits,
        "nodes_completed": node_outputs.len(),
        "total_nodes": spec.nodes.len()
    }));

    FlowpipeRunResult {
        status: "ok".to_string(),
        run_id: control.run_id.clone(),
        pipeline_id: spec.id,
        duration_ms: total_ms,
        nodes_completed: node_outputs.len(),
        total_nodes: spec.nodes.len(),
        cache_hits,
        llm_calls: 0,
        outputs: node_outputs.into_iter().collect(),
        node_reports: reports,
        error: None,
    }
}

pub fn synthesize_flowpipe_from_events(name: &str, events: &[Value]) -> FlowpipeSpec {
    let clean_id: String = name
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '-' || c == '_' {
                c
            } else {
                '_'
            }
        })
        .collect();
    let id = if clean_id.is_empty() {
        "recorded_macro".to_string()
    } else {
        clean_id
    };

    let mut nodes = Vec::new();
    let mut prev_id: Option<String> = None;

    for (idx, evt) in events.iter().enumerate() {
        let etype = evt.get("type").and_then(|v| v.as_str()).unwrap_or("");
        if etype == "connected" || etype.starts_with("pipe.") {
            continue;
        }
        let target = evt.get("target").and_then(|v| v.as_str()).unwrap_or("");
        let source = evt.get("source").and_then(|v| v.as_str()).unwrap_or("");
        let action = evt.get("action").and_then(|v| v.as_str()).unwrap_or("run");
        let payload = evt
            .get("payload")
            .and_then(|v| v.as_object())
            .cloned()
            .unwrap_or_default();

        if target.is_empty() && source.is_empty() {
            continue;
        }

        let node_id = format!("step_{}", nodes.len() + 1);
        let kind = if etype.contains("cdp") || source.contains("browser") {
            NodeKind::SysdCdp
        } else if etype.contains("uinput") || action == "key" || action == "click" {
            NodeKind::SysdUinput
        } else {
            NodeKind::BusCli
        };

        let app_name = if !target.is_empty() && target != "*" {
            Some(target.to_string())
        } else if !source.is_empty() && source != "anonymous" {
            Some(source.to_string())
        } else {
            Some(format!("macro_app_{}", idx + 1))
        };

        let mut deps = Vec::new();
        if let Some(prev) = prev_id.take() {
            deps.push(prev);
        }
        prev_id = Some(node_id.clone());

        nodes.push(FlowpipeNode {
            id: node_id,
            kind,
            app: app_name,
            action: Some(action.to_string()),
            command: None,
            args: Vec::new(),
            params: payload,
            out: None,
            depends_on: deps,
            timeout_secs: Some(60),
            retry: Some(0),
            cache_by_hash: Some(true),
            wait_for: None,
            sandbox: None,
        });
    }

    if nodes.is_empty() {
        nodes.push(FlowpipeNode {
            id: "step_1".to_string(),
            kind: NodeKind::BusCli,
            app: Some("echo".to_string()),
            action: None,
            command: None,
            args: vec!["{{inputs.topic}}".to_string()],
            params: Map::new(),
            out: None,
            depends_on: Vec::new(),
            timeout_secs: Some(30),
            retry: Some(0),
            cache_by_hash: Some(true),
            wait_for: None,
            sandbox: None,
        });
    }

    let mut inputs = BTreeMap::new();
    inputs.insert(
        "topic".to_string(),
        json!({ "type": "string", "default": name, "required": false }),
    );

    FlowpipeSpec {
        version: "1.0".to_string(),
        id: id.clone(),
        name: Some(format!("Recorded Macro: {}", name)),
        description: Some("Deterministic cross-app macro captured by flowork-pipe record".to_string()),
        inputs,
        sandbox: Some(SandboxScope::default()),
        nodes,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn tmp_dir(prefix: &str) -> PathBuf {
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0);
        let p = env::temp_dir().join(format!("{}_{}_{}", prefix, std::process::id(), nanos));
        let _ = fs::create_dir_all(&p);
        p
    }

    #[test]
    fn test_validate_detects_cycles_and_layers_dag() {
        let toml_ok = r#"
version = "1.0"
id = "parallel_demo"

[[nodes]]
id = "n1"
kind = "bus_cli"
command = "echo one"

[[nodes]]
id = "n2"
kind = "bus_cli"
command = "echo two"

[[nodes]]
id = "n3"
kind = "bus_cli"
command = "echo merged"
depends_on = ["n1", "n2"]
"#;
        let spec = parse_flowpipe_str(toml_ok, None).expect("parse toml");
        let rep = validate_flowpipe(&spec);
        assert!(rep.valid);
        assert_eq!(rep.topo_layers.len(), 2);
        assert_eq!(rep.topo_layers[0], vec!["n1", "n2"]);
        assert_eq!(rep.topo_layers[1], vec!["n3"]);

        let toml_cyc = r#"
version = "1.0"
id = "cycle_demo"
[[nodes]]
id = "a"
command = "echo a"
depends_on = ["b"]
[[nodes]]
id = "b"
command = "echo b"
depends_on = ["a"]
"#;
        let cyc_spec = parse_flowpipe_str(toml_cyc, None).expect("parse cyc");
        let cyc_rep = validate_flowpipe(&cyc_spec);
        assert!(!cyc_rep.valid);
        assert!(cyc_rep.errors.iter().any(|e| e.contains("cycle")));
    }

    #[tokio::test]
    async fn test_parallel_dag_execution_and_sha256_cache() {
        let sandbox = tmp_dir("flowpipe_test");
        env::set_var("FLOWORK_PIPE_CACHE_DIR", sandbox.join("cache"));
        env::set_var("FLOWORK_PIPE_WORK_DIR", sandbox.join("work"));
        env::set_var("FLOWORK_PIPE_OUT_DIR", sandbox.join("out"));

        let spec_toml = r#"
version = "1.0"
id = "parallel_cache_test"

[inputs.label]
type = "string"
default = "Sovereign"

[[nodes]]
id = "a"
kind = "bus_cli"
command = "sh -c 'sleep 0.25 && echo a_{{inputs.label}} > {{work}}/a.txt'"
out = "{{work}}/a.txt"

[[nodes]]
id = "b"
kind = "bus_cli"
command = "sh -c 'sleep 0.25 && echo b_{{inputs.label}} > {{work}}/b.txt'"
out = "{{work}}/b.txt"

[[nodes]]
id = "c"
kind = "bus_cli"
depends_on = ["a", "b"]
command = "sh -c 'cat {{a.out}} {{b.out}} > {{out}}/final.txt && echo {\"ok\":true}'"
out = "{{out}}/final.txt"
"#;
        let spec = parse_flowpipe_str(spec_toml, None).expect("parse test spec");

        let ctrl1 = Arc::new(RunControl::new("run_1".to_string()));
        let r1 = execute_flowpipe_dag(spec.clone(), Map::new(), true, ctrl1, None).await;
        assert_eq!(r1.status, "ok", "r1 error: {:?}", r1.error);
        assert_eq!(r1.nodes_completed, 3);
        assert_eq!(r1.cache_hits, 0);
        // Parallel execution of two 250ms nodes must be well under 450ms
        assert!(
            r1.duration_ms < 450,
            "expected parallel runtime < 450ms, got {}ms",
            r1.duration_ms
        );
        let merged = fs::read_to_string(sandbox.join("out/final.txt")).expect("merged out");
        assert!(merged.contains("a_Sovereign"));
        assert!(merged.contains("b_Sovereign"));

        // Second run must achieve 3/3 SHA-256 cache hits
        let ctrl2 = Arc::new(RunControl::new("run_2".to_string()));
        let r2 = execute_flowpipe_dag(spec, Map::new(), true, ctrl2, None).await;
        assert_eq!(r2.status, "ok");
        assert_eq!(r2.cache_hits, 3, "expected 3 cache hits on 2nd run");
        assert!(r2.duration_ms < 100, "cached run took {}ms", r2.duration_ms);

        let _ = fs::remove_dir_all(&sandbox);
    }
}
