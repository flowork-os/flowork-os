use crate::config::{resolve_project_slug, AppConfig};
use crate::inference::{ChatMessage, ContentPart, FunctionCallData, TokenUsage};
use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use chrono::Utc;
use serde_json::{json, Value};
use std::collections::{HashMap, VecDeque};
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct SessionSummary {
    pub index: usize,
    pub session_id: String,
    pub path: PathBuf,
    #[allow(dead_code)]
    pub start_time: String,
    pub last_updated: String,
    pub preview: String,
}

#[derive(Debug, Clone)]
pub struct SessionVault {
    pub session_id: String,
    pub slug: String,
    pub path: PathBuf,
    #[allow(dead_code)]
    pub project_hash: String,
}

impl SessionVault {
    pub fn open_or_create(config: &AppConfig) -> Result<(Self, Vec<ChatMessage>), String> {
        let slug = resolve_project_slug(&config.cwd, &config.paths.user_flowork_dir);
        let project_hash = simple_sha_hex(&config.cwd.to_string_lossy());

        if let Some(ref custom_file) = config.session_file {
            if custom_file.is_file() {
                let (sid, history) = load_jsonl_session(custom_file)?;
                let vault = Self {
                    session_id: sid,
                    slug,
                    path: custom_file.clone(),
                    project_hash,
                };
                vault.update_latest_symlink(config);
                return Ok((vault, history));
            }
        }

        if let Some(ref resume_spec) = config.resume {
            let summaries = list_sessions(config);
            if let Some(found) = find_matching_session(config, &summaries, resume_spec) {
                let (sid, history) = load_jsonl_session(&found.path)?;
                let vault = Self {
                    session_id: sid,
                    slug,
                    path: found.path,
                    project_hash,
                };
                vault.update_latest_symlink(config);
                return Ok((vault, history));
            } else if resume_spec != "latest" {
                return Err(format!(
                    "Session '{}' not found in project '{}'. Use --list-sessions to view available sessions.",
                    resume_spec, slug
                ));
            }
        }

        let session_id = config
            .session_id
            .clone()
            .filter(|s| !s.trim().is_empty())
            .unwrap_or_else(|| Uuid::new_v4().to_string());
        let short8: String = session_id.chars().filter(|c| c.is_ascii_hexdigit()).take(8).collect();
        let now = Utc::now();
        let fname = format!(
            "session-{}-{}.jsonl",
            now.format("%Y-%m-%dT%H-%M"),
            if short8.is_empty() { "flowork0".to_string() } else { short8 }
        );

        let dir = config.paths.history_chats_dir.join(&slug);
        fs::create_dir_all(&dir).map_err(|e| format!("Failed creating chat vault dir: {}", e))?;
        let path = dir.join(fname);

        let header = json!({
            "sessionId": session_id,
            "projectHash": project_hash,
            "startTime": now.to_rfc3339_opts(chrono::SecondsFormat::Millis, true),
            "lastUpdated": now.to_rfc3339_opts(chrono::SecondsFormat::Millis, true),
            "kind": "main"
        });
        append_json_line(&path, &header)?;

        let vault = Self {
            session_id,
            slug,
            path,
            project_hash,
        };
        vault.update_latest_symlink(config);
        Ok((vault, Vec::new()))
    }

    pub fn update_latest_symlink(&self, config: &AppConfig) {
        let hist_root = config.paths.user_flowork_dir.join("history");
        let _ = fs::create_dir_all(&hist_root);
        let link = hist_root.join("latest_session");
        let _ = fs::remove_file(&link);
        #[cfg(unix)]
        {
            let _ = std::os::unix::fs::symlink(&self.path, &link);
        }
    }

    pub fn append_user_prompt(&self, text: &str) -> Result<(), String> {
        let ts = Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true);
        let rec = json!({
            "id": Uuid::new_v4().to_string(),
            "timestamp": ts,
            "type": "user",
            "content": [{ "text": text }]
        });
        append_json_line(&self.path, &rec)?;
        self.touch_updated(&ts)
    }

    pub fn append_tool_responses(&self, parts: &[ContentPart]) -> Result<(), String> {
        let ts = Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true);
        let rec = json!({
            "id": Uuid::new_v4().to_string(),
            "timestamp": ts,
            "type": "user",
            "content": parts
        });
        append_json_line(&self.path, &rec)?;
        self.touch_updated(&ts)
    }

    pub fn append_model_turn(
        &self,
        model: &str,
        text: &str,
        thoughts: &[String],
        tokens: &TokenUsage,
        tool_calls_log: &[Value],
        raw_parts: &[ContentPart],
    ) -> Result<(), String> {
        let ts = Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true);
        let thought_objs: Vec<Value> = thoughts
            .iter()
            .filter(|t| !t.trim().is_empty())
            .map(|t| {
                json!({
                    "subject": "",
                    "description": t
                })
            })
            .collect();

        let coalesced_raw = crate::context::coalesce_parts(raw_parts.to_vec());

        let mut rec = json!({
            "id": Uuid::new_v4().to_string(),
            "timestamp": ts,
            "type": "gemini",
            "content": text,
            "thoughts": thought_objs,
            "tokens": {
                "input": tokens.input,
                "output": tokens.output,
                "cached": tokens.cached,
                "thoughts": tokens.thoughts,
                "tool": 0,
                "total": tokens.total
            },
            "model": model,
            "rawParts": coalesced_raw
        });
        if !tool_calls_log.is_empty() {
            rec["toolCalls"] = json!(tool_calls_log);
        }
        append_json_line(&self.path, &rec)?;
        self.touch_updated(&ts)
    }

    /// Appends a dual compact checkpoint into the append-only JSONL ledger without deleting original turns.
    /// Original turns stay intact ("versi utuh") for forensics & Sidebar; `--resume` loads the compressed anchor.
    pub fn append_compression_snapshot(
        &self,
        snapshot_text: &str,
        preserved_tail: &[ChatMessage],
        original_token_count: u64,
        new_token_count: u64,
    ) -> Result<(), String> {
        let ts = Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true);
        let rec = json!({
            "id": Uuid::new_v4().to_string(),
            "timestamp": ts,
            "type": "compression_snapshot",
            "snapshot": snapshot_text,
            "preservedTail": preserved_tail,
            "originalTokenCount": original_token_count,
            "newTokenCount": new_token_count
        });
        append_json_line(&self.path, &rec)?;
        self.touch_updated(&ts)
    }

    pub fn append_summary(&self, summary: &str) -> Result<(), String> {
        let clean: String = summary.trim().chars().take(120).collect();
        if clean.is_empty() {
            return Ok(());
        }
        append_json_line(&self.path, &json!({ "$set": { "summary": clean } }))
    }

    pub fn append_rewind(&self, keep_history_len: usize) -> Result<(), String> {
        let ts = Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true);
        append_json_line(
            &self.path,
            &json!({
                "timestamp": ts,
                "$rewind": { "keepCount": keep_history_len }
            }),
        )?;
        self.touch_updated(&ts)
    }

    fn touch_updated(&self, ts: &str) -> Result<(), String> {
        append_json_line(
            &self.path,
            &json!({ "$set": { "lastUpdated": ts } }),
        )
    }

    pub fn save_checkpoint(&self, config: &AppConfig, tag: &str, history: &[ChatMessage]) -> Result<PathBuf, String> {
        let dir = config.paths.checkpoints_dir.join(&self.slug);
        fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
        let safe_tag: String = tag
            .chars()
            .map(|c| if c.is_ascii_alphanumeric() || c == '-' || c == '_' { c } else { '_' })
            .collect();
        let file = dir.join(format!("{}.json", if safe_tag.is_empty() { "default" } else { &safe_tag }));
        let data = serde_json::to_string_pretty(&json!({
            "tag": tag,
            "session_id": self.session_id,
            "saved_at": Utc::now().to_rfc3339(),
            "history": history
        }))
        .map_err(|e| e.to_string())?;
        fs::write(&file, data).map_err(|e| e.to_string())?;
        Ok(file)
    }

    pub fn restore_checkpoint(&self, config: &AppConfig, tag: &str) -> Result<Vec<ChatMessage>, String> {
        let dir = config.paths.checkpoints_dir.join(&self.slug);
        let safe_tag: String = tag
            .chars()
            .map(|c| if c.is_ascii_alphanumeric() || c == '-' || c == '_' { c } else { '_' })
            .collect();
        let file = dir.join(format!("{}.json", if safe_tag.is_empty() { "default" } else { &safe_tag }));
        let raw = fs::read_to_string(&file).map_err(|e| format!("Checkpoint '{}' not found: {}", tag, e))?;
        let val: Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
        let hist: Vec<ChatMessage> = serde_json::from_value(val.get("history").cloned().unwrap_or(json!([])))
            .map_err(|e| e.to_string())?;
        Ok(hist)
    }

    pub fn list_checkpoints(&self, config: &AppConfig) -> Vec<String> {
        let dir = config.paths.checkpoints_dir.join(&self.slug);
        let Ok(entries) = fs::read_dir(dir) else {
            return Vec::new();
        };
        let mut names: Vec<String> = entries
            .flatten()
            .filter_map(|e| {
                let p = e.path();
                if p.extension().and_then(|s| s.to_str()) == Some("json") {
                    p.file_stem().and_then(|s| s.to_str()).map(str::to_string)
                } else {
                    None
                }
            })
            .collect();
        names.sort();
        names
    }
}

fn append_json_line(path: &Path, val: &Value) -> Result<(), String> {
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|e| format!("Open session JSONL error: {}", e))?;
    let line = serde_json::to_string(val).map_err(|e| e.to_string())?;
    writeln!(file, "{}", line).map_err(|e| format!("Write session JSONL error: {}", e))?;
    Ok(())
}

pub fn load_jsonl_session(path: &Path) -> Result<(String, Vec<ChatMessage>), String> {
    let file = File::open(path).map_err(|e| format!("Cannot open session file: {}", e))?;
    let reader = BufReader::new(file);
    let mut session_id = String::new();
    let mut history: Vec<ChatMessage> = Vec::new();

    for line in reader.lines().flatten() {
        let t = line.trim();
        if t.is_empty() {
            continue;
        }
        let Ok(v) = serde_json::from_str::<Value>(t) else {
            continue;
        };
        if let Some(sid) = v.get("sessionId").and_then(|s| s.as_str()) {
            session_id = sid.to_string();
            continue;
        }
        if v.get("$set").is_some() {
            continue;
        }
        if let Some(rw) = v.get("$rewind") {
            if let Some(keep) = rw.get("keepCount").and_then(|k| k.as_u64()) {
                history.truncate(keep as usize);
            }
            continue;
        }
        match v.get("type").and_then(|s| s.as_str()) {
            Some("compression_snapshot") => {
                if let Some(snap) = v.get("snapshot").and_then(|s| s.as_str()) {
                    history.clear();
                    history.push(ChatMessage {
                        role: "user".to_string(),
                        parts: vec![ContentPart::text(snap.to_string())],
                    });
                    history.push(ChatMessage {
                        role: "model".to_string(),
                        parts: vec![ContentPart::text(
                            "Understood. Continuing seamlessly from the compressed state snapshot.",
                        )],
                    });
                    if let Some(tail) = v.get("preservedTail").and_then(|t| t.as_array()) {
                        for item in tail {
                            if let Ok(msg) = serde_json::from_value::<ChatMessage>(item.clone()) {
                                history.push(msg);
                            }
                        }
                    }
                }
            }
            Some("user") => {
                if let Some(arr) = v.get("content").and_then(|c| c.as_array()) {
                    let mut parts = Vec::new();
                    for item in arr {
                        if let Ok(mut p) = serde_json::from_value::<ContentPart>(item.clone()) {
                            if let Some(ref mut fr) = p.function_response {
                                if let Some(resp) = fr.get_mut("response") {
                                    if !resp.is_object() {
                                        *resp = json!({ "output": resp.clone() });
                                    }
                                }
                            }
                            if let Some(ref txt) = p.text {
                                // Skip verbose internal system telemetry wrappers on resume, keep real user prompts
                                if txt.starts_with("<session_context>") {
                                    continue;
                                }
                            }
                            parts.push(p);
                        } else if let Some(txt) = item.get("text").and_then(|s| s.as_str()) {
                            parts.push(ContentPart::text(txt));
                        }
                    }
                    if !parts.is_empty() {
                        history.push(ChatMessage {
                            role: "user".to_string(),
                            parts,
                        });
                    }
                } else if let Some(txt) = v.get("content").and_then(|c| c.as_str()) {
                    history.push(ChatMessage {
                        role: "user".to_string(),
                        parts: vec![ContentPart::text(txt)],
                    });
                }
            }
            Some("gemini") => {
                if let Some(raw_arr) = v.get("rawParts").and_then(|c| c.as_array()) {
                    let mut parts = Vec::new();
                    for item in raw_arr {
                        if let Ok(p) = serde_json::from_value::<ContentPart>(item.clone()) {
                            parts.push(p);
                        }
                    }
                    if !parts.is_empty() {
                        history.push(ChatMessage {
                            role: "model".to_string(),
                            parts,
                        });
                        continue;
                    }
                }
                // Backward-compatible reconstruction from legacy JSONL
                let mut parts = Vec::new();
                if let Some(txt) = v.get("content").and_then(|c| c.as_str()) {
                    if !txt.is_empty() {
                        parts.push(ContentPart::text(txt));
                    }
                }
                if let Some(tcs) = v.get("toolCalls").and_then(|a| a.as_array()) {
                    for tc in tcs {
                        let id = tc.get("id").and_then(|s| s.as_str()).unwrap_or("call_0").to_string();
                        let name = tc.get("name").and_then(|s| s.as_str()).unwrap_or("").to_string();
                        let args = tc.get("args").cloned().unwrap_or_else(|| json!({}));
                        if !name.is_empty() {
                            parts.push(ContentPart {
                                text: None,
                                thought: None,
                                thought_signature: None,
                                function_call: Some(FunctionCallData { id, name, args }),
                                function_response: None,
                                inline_data: None,
                            });
                        }
                    }
                }
                if !parts.is_empty() {
                    history.push(ChatMessage {
                        role: "model".to_string(),
                        parts,
                    });
                }
            }
            _ => {}
        }
    }

    if session_id.is_empty() {
        session_id = Uuid::new_v4().to_string();
    }
    Ok((session_id, history))
}

pub fn list_sessions(config: &AppConfig) -> Vec<SessionSummary> {
    let slug = resolve_project_slug(&config.cwd, &config.paths.user_flowork_dir);
    let project_dir = config.paths.history_chats_dir.join(&slug);
    let mut files = Vec::new();
    if let Ok(entries) = fs::read_dir(&project_dir) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.extension().and_then(|s| s.to_str()) == Some("jsonl") {
                files.push(p);
            }
        }
    }

    // Sort newest first by filename/mtime
    files.sort_by(|a, b| {
        let ma = fs::metadata(a).and_then(|m| m.modified()).ok();
        let mb = fs::metadata(b).and_then(|m| m.modified()).ok();
        mb.cmp(&ma).then_with(|| b.cmp(a))
    });

    let mut out = Vec::new();
    for (idx, p) in files.into_iter().enumerate() {
        if let Some(sum) = summarize_session_file(idx + 1, &p) {
            out.push(sum);
        }
    }
    out
}

fn summarize_session_file(index: usize, path: &Path) -> Option<SessionSummary> {
    let file = File::open(path).ok()?;
    let reader = BufReader::new(file);
    let mut sid = String::new();
    let mut start_time = String::new();
    let mut last_updated = String::new();
    let mut explicit_summary = String::new();
    let mut first_user_preview = String::new();

    for line in reader.lines().flatten() {
        let Ok(v) = serde_json::from_str::<Value>(line.trim()) else {
            continue;
        };
        if let Some(s) = v.get("sessionId").and_then(|x| x.as_str()) {
            sid = s.to_string();
            start_time = v.get("startTime").and_then(|x| x.as_str()).unwrap_or("").to_string();
            last_updated = v.get("lastUpdated").and_then(|x| x.as_str()).unwrap_or(&start_time).to_string();
            if let Some(sum) = v.get("summary").and_then(|x| x.as_str()) {
                if !sum.trim().is_empty() {
                    explicit_summary = sum.trim().to_string();
                }
            }
        }
        if let Some(set_obj) = v.get("$set") {
            if let Some(lu) = set_obj.get("lastUpdated").and_then(|x| x.as_str()) {
                last_updated = lu.to_string();
            }
            if let Some(sum) = set_obj.get("summary").and_then(|x| x.as_str()) {
                if !sum.trim().is_empty() {
                    explicit_summary = sum.trim().to_string();
                }
            }
        }
        if first_user_preview.is_empty() && v.get("type").and_then(|s| s.as_str()) == Some("user") {
            if let Some(arr) = v.get("content").and_then(|c| c.as_array()) {
                for item in arr {
                    if let Some(txt) = item.get("text").and_then(|s| s.as_str()) {
                        if !crate::context::is_ignored_user_content(txt) {
                            first_user_preview = txt.lines().next().unwrap_or("").chars().take(72).collect();
                            break;
                        }
                    }
                }
            }
        }
    }

    if sid.is_empty() {
        return None;
    }
    let preview = if !explicit_summary.is_empty() {
        explicit_summary
    } else {
        first_user_preview
    };
    Some(SessionSummary {
        index,
        session_id: sid,
        path: path.to_path_buf(),
        start_time,
        last_updated,
        preview,
    })
}

fn find_matching_session(config: &AppConfig, summaries: &[SessionSummary], spec: &str) -> Option<SessionSummary> {
    if spec == "latest" {
        return summaries.first().cloned();
    }
    if let Ok(num) = spec.parse::<usize>() {
        if num >= 1 {
            if let Some(found) = summaries.iter().find(|s| s.index == num) {
                return Some(found.clone());
            }
        }
    }
    if let Some(found) = summaries.iter().find(|s| s.session_id == spec || s.session_id.starts_with(spec)) {
        return Some(found.clone());
    }
    // Search all slugs if UUID specified across projects
    if let Ok(slugs) = fs::read_dir(&config.paths.history_chats_dir) {
        for slug_entry in slugs.flatten() {
            let sp = slug_entry.path();
            if !sp.is_dir() {
                continue;
            }
            if let Ok(files) = fs::read_dir(sp) {
                for f in files.flatten() {
                    let fp = f.path();
                    if fp.extension().and_then(|s| s.to_str()) == Some("jsonl") {
                        if let Some(sum) = summarize_session_file(1, &fp) {
                            if sum.session_id == spec || sum.session_id.starts_with(spec) {
                                return Some(sum);
                            }
                        }
                    }
                }
            }
        }
    }
    None
}

pub fn delete_session(config: &AppConfig, spec: &str) -> Result<String, String> {
    let summaries = list_sessions(config);
    let Some(target) = find_matching_session(config, &summaries, spec) else {
        return Err(format!("Session '{}' not found.", spec));
    };
    fs::remove_file(&target.path).map_err(|e| format!("Failed deleting session: {}", e))?;
    Ok(target.session_id)
}

#[derive(Debug, Default)]
pub struct LoopDetector {
    recent_calls: VecDeque<String>,
    counts: HashMap<String, usize>,
    last_text_chunk: String,
    repeated_chunk_count: usize,
    pub tool_threshold: usize,
    pub content_threshold: usize,
}

impl LoopDetector {
    pub fn new(tool_threshold: usize, content_threshold: usize) -> Self {
        Self {
            tool_threshold: tool_threshold.max(2),
            content_threshold: content_threshold.max(3),
            ..Default::default()
        }
    }

    pub fn record_tool_call(&mut self, name: &str, args: &Value) -> bool {
        let mut norm = args.clone();
        if let Some(obj) = norm.as_object_mut() {
            obj.remove("reason");
            obj.remove("keywords");
            obj.remove("goal");
        }
        let sig = format!("{}:{}", name, norm);
        let c = self.counts.entry(sig.clone()).or_insert(0);
        *c += 1;
        let count = *c;
        self.recent_calls.push_back(sig);
        if self.recent_calls.len() > 24 {
            if let Some(old) = self.recent_calls.pop_front() {
                if let Some(cnt) = self.counts.get_mut(&old) {
                    *cnt = cnt.saturating_sub(1);
                }
            }
        }
        count >= self.tool_threshold
    }

    pub fn record_text_delta(&mut self, chunk: &str) -> bool {
        let trimmed = chunk.trim();
        if trimmed.len() < 12 {
            return false;
        }
        if trimmed == self.last_text_chunk {
            self.repeated_chunk_count += 1;
        } else {
            self.last_text_chunk = trimmed.to_string();
            self.repeated_chunk_count = 1;
        }
        self.repeated_chunk_count >= self.content_threshold
    }
}

/// Expands `@path/to/file` mentions in user prompts into inline text or base64 multimodal blobs.
pub fn build_user_parts_with_attachments(config: &AppConfig, prompt: &str) -> Vec<ContentPart> {
    let mut parts = vec![ContentPart::text(prompt.to_string())];
    let mut extra_notes = Vec::new();
    let mut seen = std::collections::HashSet::new();

    for token in prompt.split_whitespace() {
        let Some(raw_ref) = token.strip_prefix('@') else {
            continue;
        };
        let clean = raw_ref.trim_matches(|c: char| matches!(c, ',' | ';' | ')' | ']' | '"' | '\''));
        if clean.is_empty() {
            continue;
        }
        let candidate = if let Some(rest) = clean.strip_prefix("~/") {
            config.paths.home_dir.join(rest)
        } else {
            let p = Path::new(clean);
            if p.is_absolute() {
                p.to_path_buf()
            } else {
                config.cwd.join(p)
            }
        };
        if !candidate.is_file() || !seen.insert(candidate.clone()) {
            continue;
        }
        let ext = candidate
            .extension()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .to_ascii_lowercase();
        let mime = match ext.as_str() {
            "png" => Some("image/png"),
            "jpg" | "jpeg" => Some("image/jpeg"),
            "webp" => Some("image/webp"),
            "gif" => Some("image/gif"),
            "pdf" => Some("application/pdf"),
            "wav" => Some("audio/wav"),
            "mp3" => Some("audio/mp3"),
            _ => None,
        };
        if let Some(m) = mime {
            if let Ok(bytes) = fs::read(&candidate) {
                if bytes.len() <= 16 * 1024 * 1024 {
                    parts.push(ContentPart::inline_data(m, B64.encode(bytes)));
                    extra_notes.push(format!("[Attached multimodal file @{} ({})]", clean, m));
                }
            }
        } else if let Ok(txt) = fs::read_to_string(&candidate) {
            let sliced: String = txt.chars().take(32_000).collect();
            extra_notes.push(format!(
                "<attached_file path=\"{}\">\n{}\n</attached_file>",
                candidate.display(),
                sliced
            ));
        }
    }

    if !extra_notes.is_empty() {
        parts.push(ContentPart::text(extra_notes.join("\n\n")));
    }
    parts
}

fn simple_sha_hex(input: &str) -> String {
    // Deterministic FNV-1a 256-bit style hex tag without extra crypto crate dependency
    let mut h1: u64 = 0xcbf29ce484222325;
    let mut h2: u64 = 0x84222325cbf29ce4;
    for &b in input.as_bytes() {
        h1 ^= b as u64;
        h1 = h1.wrapping_mul(0x100000001b3);
        h2 ^= (b as u64).wrapping_add(17);
        h2 = h2.wrapping_mul(0x100000001b3);
    }
    format!("{:016x}{:016x}", h1, h2)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dual_lossless_and_compression_snapshot_replay_works() {
        let tmp_path = std::env::temp_dir().join(format!("mrflow_sess_test_{}.jsonl", Uuid::new_v4()));
        let vault = SessionVault {
            session_id: "test-sid-1234".to_string(),
            slug: "test".to_string(),
            path: tmp_path.clone(),
            project_hash: "0000".to_string(),
        };
        append_json_line(
            &tmp_path,
            &json!({ "sessionId": "test-sid-1234", "startTime": "2026-11-11T00:00:00Z", "lastUpdated": "2026-11-11T00:00:00Z", "kind": "main" }),
        )
        .unwrap();

        vault.append_user_prompt("first prompt").unwrap();
        vault
            .append_model_turn(
                "gemini-3.8-flash-high",
                "first answer",
                &[],
                &TokenUsage::default(),
                &[],
                &[ContentPart::text("first "), ContentPart::text("answer")],
            )
            .unwrap();
        vault.append_user_prompt("second prompt").unwrap();
        vault
            .append_model_turn(
                "gemini-3.8-flash-high",
                "second answer",
                &[],
                &TokenUsage::default(),
                &[],
                &[ContentPart::text("second answer")],
            )
            .unwrap();

        let tail = vec![ChatMessage {
            role: "user".to_string(),
            parts: vec![ContentPart::text("preserved tail question")],
        }];
        vault
            .append_compression_snapshot("<state_snapshot>compact state</state_snapshot>", &tail, 5000, 300)
            .unwrap();
        vault.append_user_prompt("third prompt").unwrap();
        vault.append_summary("Dual snapshot & rewind test").unwrap();

        // Full lossless lines remain in file ("versi utuh")
        let raw_content = fs::read_to_string(&tmp_path).unwrap();
        assert!(raw_content.contains("first prompt"));
        assert!(raw_content.contains("second prompt"));

        // Resume reconstructs compact anchor + tail + subsequent prompt ("yang diringkas")
        let (sid, resumed) = load_jsonl_session(&tmp_path).unwrap();
        assert_eq!(sid, "test-sid-1234");
        assert_eq!(resumed.len(), 4);
        assert!(resumed[0].parts[0].text.as_deref().unwrap().contains("<state_snapshot>compact state</state_snapshot>"));
        assert_eq!(resumed[2].parts[0].text.as_deref(), Some("preserved tail question"));
        assert_eq!(resumed[3].parts[0].text.as_deref(), Some("third prompt"));

        // Rewind to keep_count=3 drops "third prompt" while retaining lossless history on disk
        vault.append_rewind(3).unwrap();
        let (_, rewound) = load_jsonl_session(&tmp_path).unwrap();
        assert_eq!(rewound.len(), 3);

        // Explicit summary appears in summarize_session_file
        let summary = summarize_session_file(1, &tmp_path).unwrap();
        assert_eq!(summary.preview, "Dual snapshot & rewind test");

        let _ = fs::remove_file(&tmp_path);
    }
}
