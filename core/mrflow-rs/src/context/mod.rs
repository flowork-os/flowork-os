use crate::config::UserSettings;
use crate::inference::{ChatMessage, ContentPart};
use chrono::Local;
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet, VecDeque};
use std::fs;
use std::path::{Path, PathBuf};

pub const DEFAULT_TOKEN_LIMIT: u64 = 1_048_576;
pub const GEMMA_TOKEN_LIMIT: u64 = 256_000;
pub const LOCAL_SLM_TOKEN_LIMIT: u64 = 131_072;
pub const DEFAULT_COMPRESSION_THRESHOLD: f64 = 0.5;
pub const COMPRESSION_PRESERVE_THRESHOLD: f64 = 0.3;

pub const DEFAULT_MAX_TOOL_OUTPUT_CHARS: usize = 40_000;
pub const COLLAPSE_HISTORY_BYTE_THRESHOLD: usize = 150_000;
pub const RECENT_TURNS_PROTECTED: usize = 3;
pub const EXEMPT_RETRIEVAL_BUDGET_BYTES: usize = 64 * 1024;
pub const FUNCTION_RESPONSE_STRING_COLLAPSE_THRESHOLD: usize = 2048;

pub const MASKING_PROTECTED_TOKENS: usize = 50_000;
pub const MASKING_PRUNABLE_THRESHOLD_TOKENS: usize = 30_000;
pub const MASKING_PREVIEW_HEAD_CHARS: usize = 250;
pub const MASKING_PREVIEW_TAIL_CHARS: usize = 250;

pub const COMPRESSION_PROBE_PROMPT: &str = "Critically evaluate the <state_snapshot> you just created against the entire conversation history. \
Verify that EVERY user goal, technical constraint, file path, symbol name, error trace, empirical verification result, and pending step is preserved accurately without hallucinations or omitted file paths. \
Output ONLY the final refined <state_snapshot>...</state_snapshot> XML block.";

pub const COMPRESSION_INITIAL_PROMPT: &str = "First, reason through the conversation in a private <scratchpad>. \
Then produce the complete, dense <state_snapshot>...</state_snapshot> XML block covering all goals, constraints, facts, file changes, recent tool results, and next steps.";

const BUILTIN_COMPRESSION_SYSTEM_PROMPT: &str = include_str!("/opt/floworkos/system/system_promp/promps/triggers/compression.md");

const EXEMPT_MASKING_TOOLS: &[&str] = &[
    "activate_skill",
    "ask_user",
    "enter_plan_mode",
    "exit_plan_mode",
    "update_topic",
    "complete_task",
];

const EXEMPT_COLLAPSE_RETRIEVAL_TOOLS: &[&str] = &[
    "read_file",
    "view_file",
    "read_many_files",
    "grep_search",
    "glob",
    "list_directory",
];

/// Resolves model context token limit from Flowork Connector `models.json` and known model families.
pub fn get_model_token_limit(model: &str, flowork_root: Option<&Path>) -> u64 {
    let m_lower = model.trim().to_ascii_lowercase();

    if let Some(root) = flowork_root {
        let models_file = root.join("connector/config/models.json");
        if let Ok(raw) = fs::read_to_string(models_file) {
            if let Ok(val) = serde_json::from_str::<Value>(&raw) {
                if let Some(arr) = val.get("available_models").and_then(|a| a.as_array()) {
                    for entry in arr {
                        let id = entry.get("id").and_then(|s| s.as_str()).unwrap_or("");
                        if id.eq_ignore_ascii_case(model) {
                            if let Some(lim) = entry
                                .get("context_window")
                                .or_else(|| entry.get("context_length"))
                                .or_else(|| entry.get("token_limit"))
                                .and_then(|n| n.as_u64())
                            {
                                if lim > 0 {
                                    return lim;
                                }
                            }
                        }
                    }
                }
                if let Some(obj) = val.get("models").and_then(|m| m.as_object()) {
                    if let Some(entry) = obj.get(model) {
                        if let Some(lim) = entry
                            .get("context_window")
                            .or_else(|| entry.get("context_length"))
                            .or_else(|| entry.get("token_limit"))
                            .and_then(|n| n.as_u64())
                        {
                            if lim > 0 {
                                return lim;
                            }
                        }
                    }
                }
            }
        }
    }

    if m_lower.contains("gemma") {
        GEMMA_TOKEN_LIMIT
    } else if m_lower.contains("deepseek") || m_lower.contains("qwen") || m_lower.contains("llama") {
        LOCAL_SLM_TOKEN_LIMIT
    } else {
        DEFAULT_TOKEN_LIMIT
    }
}

/// Resolves configured compression trigger ratio in `(0.1 ..= 0.95)`.
pub fn get_compression_threshold(settings: &UserSettings) -> f64 {
    if let Ok(env_val) = std::env::var("FLOWORK_COMPRESSION_THRESHOLD") {
        if let Ok(parsed) = env_val.trim().parse::<f64>() {
            if parsed.is_finite() {
                return parsed.clamp(0.1, 0.95);
            }
        }
    }
    let from_settings = settings
        .general
        .get("model")
        .and_then(|m| m.get("compressionThreshold"))
        .or_else(|| settings.general.get("compressionThreshold"))
        .and_then(|v| v.as_f64());

    match from_settings {
        Some(v) if v.is_finite() => v.clamp(0.1, 0.95),
        _ => DEFAULT_COMPRESSION_THRESHOLD,
    }
}

/// Conservative token estimator tuned for Flowork Sovereign context budgeting:
/// ASCII ~4 chars/token, non-ASCII ~1.5 bytes/token, binary blobs ~2500 tokens unless small.
pub fn estimate_text_tokens(text: &str) -> u64 {
    if text.is_empty() {
        return 0;
    }
    let mut ascii_bytes = 0usize;
    let mut non_ascii_bytes = 0usize;
    for b in text.as_bytes() {
        if *b < 128 {
            ascii_bytes += 1;
        } else {
            non_ascii_bytes += 1;
        }
    }
    let ascii_toks = (ascii_bytes as f64) / 4.0;
    let non_ascii_toks = (non_ascii_bytes as f64) / 1.5;
    (ascii_toks + non_ascii_toks).ceil() as u64
}

pub fn estimate_part_tokens(part: &ContentPart) -> u64 {
    let mut sum = 0u64;
    if let Some(ref txt) = part.text {
        sum += estimate_text_tokens(txt);
    }
    if let Some(ref fc) = part.function_call {
        sum += estimate_text_tokens(&fc.name) + estimate_text_tokens(&fc.args.to_string()) + 12;
    }
    if let Some(ref fr) = part.function_response {
        sum += estimate_text_tokens(&fr.to_string()) + 12;
    }
    if let Some(ref blob) = part.inline_data {
        // Multimodal assets weigh ~258-2500 tokens even when compressed, plus wire cost
        sum += if blob.mime_type.starts_with("image/") {
            1800
        } else {
            ((blob.data.len() as u64) / 128).clamp(512, 8192)
        };
    }
    sum
}

pub fn estimate_message_tokens(msg: &ChatMessage) -> u64 {
    let part_sum: u64 = msg.parts.iter().map(estimate_part_tokens).sum();
    part_sum + 8
}

pub fn estimate_history_tokens(history: &[ChatMessage]) -> u64 {
    history.iter().map(estimate_message_tokens).sum()
}

pub fn should_auto_compress(
    model: &str,
    flowork_root: Option<&Path>,
    last_prompt_tokens: u64,
    history: &[ChatMessage],
    threshold: f64,
) -> bool {
    if history.len() < 4 {
        return false;
    }
    let limit = get_model_token_limit(model, flowork_root) as f64;
    let trigger_at = (limit * threshold.clamp(0.1, 0.95)) as u64;
    let estimated = estimate_history_tokens(history);
    let effective = last_prompt_tokens.max(estimated);
    effective >= trigger_at
}

/// Layer 1: Truncate huge live tool output (20% head + 80% tail) and offload complete output to disk.
pub fn truncate_and_offload_output(
    output: &str,
    max_chars: usize,
    tool_name: &str,
    call_id: &str,
    offload_dir: Option<&Path>,
) -> String {
    if output.len() <= max_chars {
        return output.to_string();
    }

    let safe_max = max_chars.max(2048);
    let head_budget = (safe_max / 5).max(512);
    let tail_budget = safe_max.saturating_sub(head_budget).max(1024);

    let mut h_end = head_budget.min(output.len());
    while h_end > 0 && !output.is_char_boundary(h_end) {
        h_end -= 1;
    }
    let mut t_start = output.len().saturating_sub(tail_budget);
    while t_start < output.len() && !output.is_char_boundary(t_start) {
        t_start += 1;
    }

    let total_lines = output.lines().count();
    let saved_note = if let Some(dir) = offload_dir {
        if let Some(saved_path) = write_offload_file(dir, tool_name, call_id, output) {
            format!(
                "Full output ({} bytes, {} lines) saved to: {} (use read_file with start_line/end_line to inspect omitted sections)",
                output.len(),
                total_lines,
                saved_path.display()
            )
        } else {
            format!(
                "{} bytes / {} lines total omitted from middle",
                output.len().saturating_sub(h_end + (output.len() - t_start)),
                total_lines
            )
        }
    } else {
        format!(
            "{} bytes omitted by Flowork anti-bloat guard",
            output.len().saturating_sub(h_end + (output.len() - t_start))
        )
    };

    format!(
        "{}\n\n[... TRUNCATED: {} ...]\n\n{}",
        &output[..h_end],
        saved_note,
        &output[t_start..]
    )
}

fn write_offload_file(dir: &Path, tool_name: &str, call_id: &str, content: &str) -> Option<PathBuf> {
    fs::create_dir_all(dir).ok()?;
    let safe_tool: String = tool_name
        .chars()
        .map(|c| if c.is_ascii_alphanumeric() || c == '-' || c == '_' { c } else { '_' })
        .collect();
    let safe_id: String = call_id
        .chars()
        .filter(|c| c.is_ascii_alphanumeric() || *c == '-' || *c == '_')
        .take(24)
        .collect();
    let fname = if safe_id.is_empty() {
        format!("{}_{}.txt", safe_tool, chrono::Utc::now().timestamp_millis())
    } else {
        format!("{}_{}.txt", safe_tool, safe_id)
    };
    let dest = dir.join(fname);
    fs::write(&dest, content).ok()?;
    Some(dest)
}

/// Checks if a user text message represents internal wrapper/system syntax rather than a real user preview.
pub fn is_ignored_user_content(text: &str) -> bool {
    let trimmed = text.trim();
    if trimmed.is_empty() {
        return true;
    }
    trimmed.starts_with("<session_context>")
        || trimmed.starts_with("<environment_details>")
        || trimmed.starts_with("<hook_context>")
        || trimmed.starts_with("<system_reminder>")
        || trimmed.starts_with("<CONTEXT_SUMMARY>")
        || trimmed.starts_with("This is a summary of our conversation so far:")
        || trimmed.starts_with('/')
        || trimmed.starts_with('?')
}

/// Builds deterministic `<session_context>` anchor matching upstream `environmentContext.ts` + `folderStructure.ts`.
pub fn build_session_context_text(
    cwd: &Path,
    include_dirs: &[PathBuf],
    tool_output_dir: Option<&Path>,
) -> String {
    let date_str = Local::now().format("%A, %B %d, %Y").to_string();
    let kernel_ver = fs::read_to_string("/proc/sys/kernel/osrelease")
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|_| "7.3.0".to_string());
    let os_info = format!("{} ({}, Linux {})", std::env::consts::OS, std::env::consts::ARCH, kernel_ver);
    let tree = build_folder_tree(cwd, 3, 45);
    let extra_dirs = include_dirs
        .iter()
        .filter(|p| p.as_path() != cwd && p.is_dir())
        .map(|p| format!("  - {}", p.display()))
        .collect::<Vec<_>>();
    let offload_str = tool_output_dir
        .map(|p| p.display().to_string())
        .unwrap_or_else(|| "/tmp".to_string());

    let mut out = format!(
        "<session_context>\n\
         This is context about the current Flowork OS workspace environment.\n\n\
         - Current Date: {}\n\
         - Operating System: {}\n\
         - Primary Workspace Directory: {}\n\
         - Offloaded Tool Outputs Directory: {}\n",
        date_str,
        os_info,
        cwd.display(),
        offload_str
    );
    if !extra_dirs.is_empty() {
        out.push_str("- Included Directories:\n");
        out.push_str(&extra_dirs.join("\n"));
        out.push('\n');
    }
    if !tree.is_empty() {
        out.push_str("\nWorkspace Folder Structure (truncated):\n");
        out.push_str(&tree);
        out.push('\n');
    }
    out.push_str("</session_context>");
    out
}

fn build_folder_tree(root: &Path, max_depth: usize, max_entries: usize) -> String {
    let skip_dirs: HashSet<&str> = [
        ".git",
        "node_modules",
        "target",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        ".next",
    ]
    .into_iter()
    .collect();

    let mut queue: VecDeque<(PathBuf, usize, String)> = VecDeque::new();
    queue.push_back((root.to_path_buf(), 0, String::new()));

    let mut lines = Vec::new();
    while let Some((dir, depth, indent)) = queue.pop_front() {
        if lines.len() >= max_entries {
            lines.push(format!("{}... (further entries omitted)", indent));
            break;
        }
        let Ok(rd) = fs::read_dir(&dir) else {
            continue;
        };
        let mut children: Vec<(bool, String, PathBuf)> = rd
            .flatten()
            .filter_map(|e| {
                let p = e.path();
                let name = e.file_name().to_string_lossy().to_string();
                let is_dir = p.is_dir();
                if is_dir && skip_dirs.contains(name.as_str()) {
                    return None;
                }
                Some((!is_dir, name, p))
            })
            .collect();
        children.sort_by(|a, b| a.0.cmp(&b.0).then_with(|| a.1.cmp(&b.1)));

        for (is_file, name, path) in children {
            if lines.len() >= max_entries {
                break;
            }
            if is_file {
                lines.push(format!("{}{}", indent, name));
            } else {
                lines.push(format!("{}{}/", indent, name));
                if depth + 1 < max_depth {
                    queue.push_back((path, depth + 1, format!("{}  ", indent)));
                }
            }
        }
    }
    lines.join("\n")
}

/// Coalesces adjacent plain non-thought text parts inside a turn and removes empty dead text parts.
pub fn coalesce_parts(parts: Vec<ContentPart>) -> Vec<ContentPart> {
    let mut out: Vec<ContentPart> = Vec::with_capacity(parts.len());

    for part in parts {
        let is_plain_text = part.function_call.is_none()
            && part.function_response.is_none()
            && part.inline_data.is_none()
            && part.thought_signature.is_none()
            && !part.thought.unwrap_or(false)
            && part.text.is_some();

        if is_plain_text {
            let txt = part.text.as_deref().unwrap_or("");
            if txt.is_empty() {
                continue;
            }
            if let Some(prev) = out.last_mut() {
                let prev_is_plain = prev.function_call.is_none()
                    && prev.function_response.is_none()
                    && prev.inline_data.is_none()
                    && prev.thought_signature.is_none()
                    && !prev.thought.unwrap_or(false)
                    && prev.text.is_some();
                if prev_is_plain {
                    if let Some(ref mut prev_txt) = prev.text {
                        prev_txt.push_str(txt);
                        continue;
                    }
                }
            }
        }

        let is_empty_dead_part = part.text.as_deref().map(|s| s.is_empty()).unwrap_or(true)
            && part.function_call.is_none()
            && part.function_response.is_none()
            && part.inline_data.is_none()
            && part.thought_signature.is_none();

        if !is_empty_dead_part {
            out.push(part);
        }
    }

    out
}

fn is_valid_content(msg: &ChatMessage) -> bool {
    !msg.parts.is_empty()
        && msg.parts.iter().any(|p| {
            p.function_call.is_some()
                || p.function_response.is_some()
                || p.inline_data.is_some()
                || p.thought_signature.is_some()
                || p.text.as_deref().map(|t| !t.is_empty()).unwrap_or(false)
        })
}

/// Extracts curated turn-coalesced conversation history for model replay.
pub fn extract_curated_history(comprehensive: &[ChatMessage]) -> Vec<ChatMessage> {
    if comprehensive.is_empty() {
        return Vec::new();
    }
    let mut curated: Vec<ChatMessage> = Vec::with_capacity(comprehensive.len());
    let mut i = 0usize;
    while i < comprehensive.len() {
        let cur = &comprehensive[i];
        if cur.role == "user" {
            let parts = coalesce_parts(cur.parts.clone());
            if !parts.is_empty() {
                curated.push(ChatMessage {
                    role: "user".to_string(),
                    parts,
                });
            }
            i += 1;
        } else {
            let mut model_output = Vec::new();
            let mut is_valid = true;
            while i < comprehensive.len() && comprehensive[i].role == "model" {
                let m = &comprehensive[i];
                if !is_valid_content(m) {
                    is_valid = false;
                }
                model_output.extend(coalesce_parts(m.parts.clone()));
                i += 1;
            }
            if is_valid {
                let coalesced = coalesce_parts(model_output);
                if !coalesced.is_empty() {
                    curated.push(ChatMessage {
                        role: "model".to_string(),
                        parts: coalesced,
                    });
                }
            }
        }
    }
    curated
}

/// Strips thoughts cleanly (if requested) and guarantees first `functionCall` in each `model` turn has `thoughtSignature`.
fn sanitize_thoughts_and_signatures(history: &mut Vec<ChatMessage>, strip_thoughts: bool) {
    for msg in history.iter_mut() {
        if strip_thoughts {
            msg.parts.retain(|p| !p.thought.unwrap_or(false));
        }
        if msg.role == "model" {
            let mut found_first_fc = false;
            for part in msg.parts.iter_mut() {
                if part.function_call.is_some() {
                    if !found_first_fc {
                        found_first_fc = true;
                        if part
                            .thought_signature
                            .as_deref()
                            .map(|s| s.trim().is_empty())
                            .unwrap_or(true)
                        {
                            part.thought_signature =
                                Some("skip_thought_signature_validator".to_string());
                        }
                    }
                }
            }
        }
    }
    history.retain(|m| is_valid_content(m));
}

/// Coalesces consecutive turns with the same role into single multi-part turns.
fn coalesce_consecutive_turns(history: Vec<ChatMessage>) -> Vec<ChatMessage> {
    let mut out: Vec<ChatMessage> = Vec::with_capacity(history.len());
    for msg in history {
        if msg.parts.is_empty() {
            continue;
        }
        if let Some(last) = out.last_mut() {
            if last.role == msg.role {
                last.parts.extend(msg.parts);
                last.parts = coalesce_parts(std::mem::take(&mut last.parts));
                continue;
            }
        }
        out.push(ChatMessage {
            role: msg.role,
            parts: coalesce_parts(msg.parts),
        });
    }
    out
}

/// Mirrors `historyHardening.ts`: closes unanswered function calls & drops orphaned function responses,
/// and orders `functionResponse` parts to match the preceding `functionCall` sequence before trailing text/blobs.
fn repair_and_refine_tool_turns(history: Vec<ChatMessage>) -> Vec<ChatMessage> {
    let mut out: Vec<ChatMessage> = Vec::with_capacity(history.len() + 2);

    // Never start conversation with a model turn
    let start_idx = history
        .iter()
        .position(|m| m.role == "user")
        .unwrap_or(history.len());
    let slice = &history[start_idx..];

    let mut i = 0usize;
    while i < slice.len() {
        let cur = &slice[i];
        if cur.role == "model" {
            let fc_list: Vec<(String, String)> = cur
                .parts
                .iter()
                .filter_map(|p| {
                    p.function_call
                        .as_ref()
                        .map(|fc| (fc.id.clone(), fc.name.clone()))
                })
                .collect();

            out.push(cur.clone());

            if !fc_list.is_empty() {
                if i + 1 < slice.len() && slice[i + 1].role == "user" {
                    let next_user = &slice[i + 1];
                    let has_fr = next_user.parts.iter().any(|p| p.function_response.is_some());
                    if has_fr {
                        // Refine order to match fc_list strictly and backfill any missing call IDs
                        let refined = refine_tool_response_turn(&fc_list, next_user);
                        out.push(refined);
                        i += 2;
                        continue;
                    }
                }
                // Unanswered tool call turn (interrupted/aborted mid-turn): close with synthetic cancelled response
                let synthetic: Vec<ContentPart> = fc_list
                    .iter()
                    .map(|(id, name)| {
                        ContentPart::function_response(
                            id,
                            name,
                            json!({ "error": "Tool execution interrupted before completion." }),
                        )
                    })
                    .collect();
                out.push(ChatMessage {
                    role: "user".to_string(),
                    parts: synthetic,
                });
            }
            i += 1;
        } else {
            // User turn: ensure no orphaned functionResponse exists if previous turn wasn't matching model functionCall
            let prev_is_model_fc = out
                .last()
                .map(|m| m.role == "model" && m.parts.iter().any(|p| p.function_call.is_some()))
                .unwrap_or(false);
            if !prev_is_model_fc {
                let mut filtered_parts: Vec<ContentPart> = cur
                    .parts
                    .iter()
                    .filter(|p| p.function_response.is_none())
                    .cloned()
                    .collect();
                if filtered_parts.is_empty() {
                    filtered_parts.push(ContentPart::text("[Continued session turn]"));
                }
                out.push(ChatMessage {
                    role: "user".to_string(),
                    parts: filtered_parts,
                });
            } else {
                out.push(cur.clone());
            }
            i += 1;
        }
    }

    coalesce_consecutive_turns(out)
}

fn refine_tool_response_turn(fc_list: &[(String, String)], user_turn: &ChatMessage) -> ChatMessage {
    let mut fr_by_id: HashMap<String, ContentPart> = HashMap::new();
    let mut extras: Vec<ContentPart> = Vec::new();
    let mut fallback_anon: VecDeque<ContentPart> = VecDeque::new();

    for p in &user_turn.parts {
        if let Some(ref fr) = p.function_response {
            let id = fr.get("id").and_then(|s| s.as_str()).unwrap_or("");
            if !id.is_empty() {
                fr_by_id.insert(id.to_string(), p.clone());
            } else {
                fallback_anon.push_back(p.clone());
            }
        } else {
            extras.push(p.clone());
        }
    }

    let mut ordered = Vec::with_capacity(user_turn.parts.len());
    for (id, name) in fc_list {
        if let Some(p) = fr_by_id.remove(id) {
            ordered.push(p);
        } else if let Some(p) = fallback_anon.pop_front() {
            ordered.push(p);
        } else {
            ordered.push(ContentPart::function_response(
                id,
                name,
                json!({ "error": "Tool call did not emit a response." }),
            ));
        }
    }
    // Keep extras cleanly after ordered functionResponses
    ordered.extend(extras);
    ChatMessage {
        role: "user".to_string(),
        parts: ordered,
    }
}

/// Layer 3: Backward-scanned Hybrid FIFO Tool Output Masking (`toolOutputMaskingService.ts`).
pub fn mask_old_tool_outputs(history: &mut Vec<ChatMessage>, offload_dir: Option<&Path>) {
    if history.is_empty() {
        return;
    }

    // Never mask the latest turn
    let search_end = history.len().saturating_sub(1);
    let mut kept_tokens = 0usize;
    let mut prunable_indices: Vec<(usize, usize)> = Vec::new(); // (msg_idx, part_idx)
    let mut prunable_tokens = 0usize;

    // Backward scan from newest before latest turn
    for m_idx in (0..search_end).rev() {
        let parts_len = history[m_idx].parts.len();
        for p_idx in (0..parts_len).rev() {
            let part = &history[m_idx].parts[p_idx];
            let Some(ref fr) = part.function_response else {
                continue;
            };
            let tool_name = fr.get("name").and_then(|s| s.as_str()).unwrap_or("");
            if EXEMPT_MASKING_TOOLS.contains(&tool_name) {
                continue;
            }
            let Some(resp_val) = fr.get("response") else {
                continue;
            };
            if let Some(out_s) = resp_val.get("output").and_then(|s| s.as_str()) {
                if out_s.starts_with("<tool_output_masked>") {
                    continue;
                }
            }
            let toks = estimate_text_tokens(&resp_val.to_string()) as usize;
            if kept_tokens + toks <= MASKING_PROTECTED_TOKENS {
                kept_tokens += toks;
            } else {
                prunable_tokens += toks;
                prunable_indices.push((m_idx, p_idx));
            }
        }
    }

    if prunable_tokens <= MASKING_PRUNABLE_THRESHOLD_TOKENS {
        return;
    }

    for (m_idx, p_idx) in prunable_indices {
        let part = &mut history[m_idx].parts[p_idx];
        let Some(ref mut fr) = part.function_response else {
            continue;
        };
        let tool_name = fr
            .get("name")
            .and_then(|s| s.as_str())
            .unwrap_or("tool")
            .to_string();
        let call_id = fr
            .get("id")
            .and_then(|s| s.as_str())
            .unwrap_or("masked")
            .to_string();
        let Some(resp_val) = fr.get("response") else {
            continue;
        };
        let serialized = serde_json::to_string_pretty(resp_val).unwrap_or_else(|_| resp_val.to_string());
        if serialized.len() <= 1024 {
            continue;
        }
        let preview = create_masked_preview(&serialized);
        let file_hint = if let Some(dir) = offload_dir {
            if let Some(p) = write_offload_file(dir, &tool_name, &call_id, &serialized) {
                format!("Full output ({} bytes) available at: {}\nRead specific lines with read_file.", serialized.len(), p.display())
            } else {
                format!("Original output ({} bytes) omitted to conserve context.", serialized.len())
            }
        } else {
            format!("Original output ({} bytes) omitted to conserve context.", serialized.len())
        };

        let masked_str = format!(
            "<tool_output_masked>\n{}\n\n{}\n</tool_output_masked>",
            preview, file_hint
        );
        if let Some(obj) = fr.as_object_mut() {
            obj.insert("response".to_string(), json!({ "output": masked_str }));
        }
    }
}

fn create_masked_preview(text: &str) -> String {
    if text.len() <= MASKING_PREVIEW_HEAD_CHARS + MASKING_PREVIEW_TAIL_CHARS + 32 {
        return text.to_string();
    }
    let mut h_end = MASKING_PREVIEW_HEAD_CHARS.min(text.len());
    while h_end > 0 && !text.is_char_boundary(h_end) {
        h_end -= 1;
    }
    let mut t_start = text.len().saturating_sub(MASKING_PREVIEW_TAIL_CHARS);
    while t_start < text.len() && !text.is_char_boundary(t_start) {
        t_start += 1;
    }
    format!("{}...\n...\n...{}", &text[..h_end], &text[t_start..])
}

/// Layer 2: Collapses older tool responses > 2KB and evicts older `inlineData` binaries when total serialized history >= 150KB.
pub fn collapse_older_function_responses(history: &mut Vec<ChatMessage>) {
    let serialized_size = serde_json::to_string(history).map(|s| s.len()).unwrap_or(0);
    if serialized_size < COLLAPSE_HISTORY_BYTE_THRESHOLD {
        return;
    }

    // Indices of turns containing functionResponse
    let fr_turn_indices: Vec<usize> = history
        .iter()
        .enumerate()
        .filter(|(_, m)| m.parts.iter().any(|p| p.function_response.is_some()))
        .map(|(i, _)| i)
        .collect();

    let protected_turn_start = if fr_turn_indices.len() > RECENT_TURNS_PROTECTED {
        fr_turn_indices[fr_turn_indices.len() - RECENT_TURNS_PROTECTED]
    } else {
        usize::MAX
    };

    // Binary eviction boundary: keep inline_data only in the newest 3 turns overall
    let binary_protect_from = history.len().saturating_sub(RECENT_TURNS_PROTECTED);

    // Exempt retrieval tool budget scanned newest -> oldest among older turns
    let mut exempt_budget_remaining = EXEMPT_RETRIEVAL_BUDGET_BYTES;
    let mut protected_exempt_parts: HashSet<(usize, usize)> = HashSet::new();

    for m_idx in (0..history.len()).rev() {
        if m_idx >= protected_turn_start {
            continue;
        }
        for (p_idx, part) in history[m_idx].parts.iter().enumerate().rev() {
            if let Some(ref fr) = part.function_response {
                let tname = fr.get("name").and_then(|s| s.as_str()).unwrap_or("");
                if EXEMPT_COLLAPSE_RETRIEVAL_TOOLS.contains(&tname) {
                    let size = fr.get("response").map(|r| r.to_string().len()).unwrap_or(0);
                    if size <= exempt_budget_remaining {
                        exempt_budget_remaining -= size;
                        protected_exempt_parts.insert((m_idx, p_idx));
                    }
                }
            }
        }
    }

    for (m_idx, msg) in history.iter_mut().enumerate() {
        let evict_binaries_here = m_idx < binary_protect_from;
        let collapse_fr_here = m_idx < protected_turn_start;

        let mut new_parts = Vec::with_capacity(msg.parts.len());
        for (p_idx, mut part) in std::mem::take(&mut msg.parts).into_iter().enumerate() {
            if evict_binaries_here {
                if let Some(blob) = part.inline_data.take() {
                    new_parts.push(ContentPart::text(format!(
                        "[Binary content ({}, {} base64 bytes) omitted from previous turn to conserve memory]",
                        blob.mime_type,
                        blob.data.len()
                    )));
                    continue;
                }
            }
            if collapse_fr_here && !protected_exempt_parts.contains(&(m_idx, p_idx)) {
                if let Some(ref mut fr) = part.function_response {
                    if let Some(resp) = fr.get_mut("response") {
                        collapse_json_strings_in_place(resp);
                    }
                }
            }
            new_parts.push(part);
        }
        msg.parts = coalesce_parts(new_parts);
    }
}

fn collapse_json_strings_in_place(val: &mut Value) {
    match val {
        Value::String(s) => {
            if s.len() > FUNCTION_RESPONSE_STRING_COLLAPSE_THRESHOLD
                && !s.starts_with("<tool_output_masked>")
            {
                let len = s.len();
                *s = format!(
                    "... [Tool output collapsed from previous turn: {} bytes omitted to conserve memory] ...",
                    len
                );
            }
        }
        Value::Array(arr) => {
            for item in arr.iter_mut() {
                collapse_json_strings_in_place(item);
            }
        }
        Value::Object(obj) => {
            for (_, v) in obj.iter_mut() {
                collapse_json_strings_in_place(v);
            }
        }
        _ => {}
    }
}

/// Complete preparation pipeline run right before sending `history` to LLM inference:
/// curation -> part coalescing -> thought signature hardening -> role coalescing -> tool call repair ->
/// `<session_context>` anchor injection -> masking -> collapse & binary eviction.
pub fn prepare_history_for_api(
    raw_history: &[ChatMessage],
    session_context_text: Option<&str>,
    strip_thoughts: bool,
    tmp_tool_dir: Option<&Path>,
) -> Vec<ChatMessage> {
    let mut prepared = extract_curated_history(raw_history);
    sanitize_thoughts_and_signatures(&mut prepared, strip_thoughts);
    prepared = coalesce_consecutive_turns(prepared);
    prepared = repair_and_refine_tool_turns(prepared);

    if let Some(ctx_txt) = session_context_text.filter(|s| !s.trim().is_empty()) {
        let already_anchored = prepared
            .first()
            .and_then(|m| m.parts.first())
            .and_then(|p| p.text.as_deref())
            .map(|t| t.starts_with("<session_context>"))
            .unwrap_or(false);

        if !already_anchored {
            if let Some(first_user) = prepared.first_mut().filter(|m| m.role == "user") {
                first_user.parts.insert(0, ContentPart::text(ctx_txt.to_string()));
            } else {
                prepared.insert(
                    0,
                    ChatMessage {
                        role: "user".to_string(),
                        parts: vec![ContentPart::text(ctx_txt.to_string())],
                    },
                );
            }
        }
    }

    mask_old_tool_outputs(&mut prepared, tmp_tool_dir);
    collapse_older_function_responses(&mut prepared);
    prepared
}

/// Mirrors `chatCompressionService.ts:findCompressSplitPoint` (keeps newest ~30% cleanly on a real user turn boundary).
pub fn find_compress_split_point(history: &[ChatMessage], preserve_fraction: f64) -> Option<usize> {
    let fraction = 1.0 - preserve_fraction.clamp(0.1, 0.8); // preserve_fraction=0.3 -> compress earliest 0.7
    if history.len() < 4 {
        return None;
    }

    let char_counts: Vec<usize> = history
        .iter()
        .map(|m| serde_json::to_string(m).map(|s| s.len()).unwrap_or(0))
        .collect();
    let total_chars: usize = char_counts.iter().sum();
    if total_chars == 0 {
        return None;
    }
    let target_chars = ((total_chars as f64) * fraction) as usize;

    let mut cumulative = 0usize;
    let mut last_valid_split: Option<usize> = None;

    for (idx, msg) in history.iter().enumerate() {
        let is_user = msg.role == "user";
        let is_function_response = msg.parts.iter().any(|p| p.function_response.is_some());
        if is_user && !is_function_response && idx >= 2 {
            if cumulative >= target_chars {
                return Some(idx);
            }
            last_valid_split = Some(idx);
        }
        cumulative += char_counts[idx];
    }

    last_valid_split
}

/// Prepares `history_to_compress` to fit comfortably inside the summarizer call budget.
pub fn truncate_history_to_budget(
    history: &[ChatMessage],
    model_limit: u64,
    tmp_tool_dir: Option<&Path>,
) -> Vec<ChatMessage> {
    let mut copy = history.to_vec();
    // Always evict binaries in compression summarization input
    for msg in &mut copy {
        let mut rebuilt = Vec::with_capacity(msg.parts.len());
        for mut part in std::mem::take(&mut msg.parts) {
            if let Some(blob) = part.inline_data.take() {
                rebuilt.push(ContentPart::text(format!(
                    "[Binary asset ({}, {} bytes) referenced earlier]",
                    blob.mime_type,
                    blob.data.len()
                )));
                continue;
            }
            rebuilt.push(part);
        }
        msg.parts = coalesce_parts(rebuilt);
    }

    mask_old_tool_outputs(&mut copy, tmp_tool_dir);
    collapse_older_function_responses(&mut copy);

    // If still above 65% of model limit, trim oldest messages iteratively until within safe margin
    let budget_tokens = ((model_limit as f64) * 0.65) as u64;
    while copy.len() > 2 && estimate_history_tokens(&copy) > budget_tokens {
        copy.remove(0);
        if copy.first().map(|m| m.role == "model").unwrap_or(false) {
            copy.remove(0);
        }
    }
    copy
}

pub fn load_compression_system_prompt(prompts_dir: &Path) -> String {
    let custom = prompts_dir.join("triggers/compression.md");
    if let Ok(raw) = fs::read_to_string(custom) {
        let trimmed = raw.trim();
        if !trimmed.is_empty() {
            return trimmed.to_string();
        }
    }
    BUILTIN_COMPRESSION_SYSTEM_PROMPT.trim().to_string()
}

pub fn extract_state_snapshot(raw: &str) -> String {
    if let (Some(start), Some(end)) = (raw.find("<state_snapshot>"), raw.rfind("</state_snapshot>")) {
        if end >= start {
            return raw[start..end + "</state_snapshot>".len()].trim().to_string();
        }
    }
    // Strip any <scratchpad>...</scratchpad> if closing snapshot tag missing
    let mut cleaned = raw.to_string();
    if let (Some(s1), Some(s2)) = (cleaned.find("<scratchpad>"), cleaned.find("</scratchpad>")) {
        if s2 >= s1 {
            cleaned.replace_range(s1..s2 + "</scratchpad>".len(), "");
        }
    }
    let trimmed = cleaned.trim();
    if trimmed.starts_with("<state_snapshot>") {
        format!("{}\n</state_snapshot>", trimmed)
    } else {
        format!("<state_snapshot>\n{}\n</state_snapshot>", trimmed)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn coalesces_adjacent_text_parts_and_strips_empty() {
        let parts = vec![
            ContentPart::text("Hello "),
            ContentPart::text(""),
            ContentPart::text("Flowork"),
            ContentPart::text(" OS!"),
        ];
        let merged = coalesce_parts(parts);
        assert_eq!(merged.len(), 1);
        assert_eq!(merged[0].text.as_deref(), Some("Hello Flowork OS!"));
    }

    #[test]
    fn injects_thought_signature_and_repairs_unanswered_calls() {
        let raw = vec![
            ChatMessage {
                role: "user".to_string(),
                parts: vec![ContentPart::text("check disk")],
            },
            ChatMessage {
                role: "model".to_string(),
                parts: vec![ContentPart {
                    text: None,
                    thought: None,
                    thought_signature: None,
                    function_call: Some(crate::inference::FunctionCallData {
                        id: "c1".to_string(),
                        name: "read_file".to_string(),
                        args: json!({"file_path": "/etc/hostname"}),
                    }),
                    function_response: None,
                    inline_data: None,
                }],
            },
        ];

        let prepared = prepare_history_for_api(&raw, Some("<session_context>env</session_context>"), false, None);
        assert_eq!(prepared.len(), 3);
        assert_eq!(prepared[0].role, "user");
        assert!(prepared[0].parts[0].text.as_deref().unwrap().starts_with("<session_context>"));
        assert_eq!(
            prepared[1].parts[0].thought_signature.as_deref(),
            Some("skip_thought_signature_validator")
        );
        assert_eq!(prepared[2].role, "user");
        assert!(prepared[2].parts[0].function_response.is_some());
    }

    #[test]
    fn collapses_old_function_responses_and_evicts_old_binaries() {
        let mut hist = Vec::new();
        let big = "X".repeat(12_000);
        // 6 turns so early ones exceed threshold & fall outside newest 3 turns
        for i in 0..8 {
            hist.push(ChatMessage {
                role: "user".to_string(),
                parts: vec![
                    ContentPart::text(format!("prompt {}", i)),
                    ContentPart::inline_data("image/jpeg", "A".repeat(25_000)),
                ],
            });
            hist.push(ChatMessage {
                role: "model".to_string(),
                parts: vec![ContentPart {
                    text: Some(format!("ans {}", i)),
                    thought: None,
                    thought_signature: Some("sig".to_string()),
                    function_call: Some(crate::inference::FunctionCallData {
                        id: format!("id_{}", i),
                        name: "run_shell_command".to_string(),
                        args: json!({"command": "echo hi"}),
                    }),
                    function_response: None,
                    inline_data: None,
                }],
            });
            hist.push(ChatMessage {
                role: "user".to_string(),
                parts: vec![ContentPart::function_response(
                    &format!("id_{}", i),
                    "run_shell_command",
                    json!({ "stdout": big }),
                )],
            });
        }

        collapse_older_function_responses(&mut hist);
        // Earliest binary must be evicted into compact text note
        assert!(hist[0].parts.iter().all(|p| p.inline_data.is_none()));
        // Earliest tool response must be collapsed
        let early_resp = hist[2].parts[0].function_response.as_ref().unwrap()["response"]["stdout"]
            .as_str()
            .unwrap();
        assert!(early_resp.contains("Tool output collapsed from previous turn"));
        // Newest tool response stays intact
        let latest_resp = hist.last().unwrap().parts[0].function_response.as_ref().unwrap()["response"]["stdout"]
            .as_str()
            .unwrap();
        assert_eq!(latest_resp.len(), 12_000);
    }

    #[test]
    fn truncate_and_offload_saves_full_output_to_disk() {
        let tmp = std::env::temp_dir().join(format!("mrflow_test_offload_{}", uuid::Uuid::new_v4()));
        let big = "Line data 1234567890\n".repeat(3000);
        let res = truncate_and_offload_output(&big, 8_000, "grep_search", "call_99", Some(&tmp));
        assert!(res.contains("Full output"));
        let saved = tmp.join("grep_search_call_99.txt");
        assert!(saved.is_file());
        assert_eq!(fs::read_to_string(&saved).unwrap().len(), big.len());
        let _ = fs::remove_dir_all(&tmp);
    }

    #[test]
    fn find_compress_split_point_lands_on_non_fr_user_turn() {
        let mut hist = Vec::new();
        for i in 0..5 {
            hist.push(ChatMessage {
                role: "user".to_string(),
                parts: vec![ContentPart::text(format!("question {} {}", i, "x".repeat(400)))],
            });
            hist.push(ChatMessage {
                role: "model".to_string(),
                parts: vec![ContentPart::text(format!("answer {} {}", i, "y".repeat(400)))],
            });
        }
        let split = find_compress_split_point(&hist, 0.3).expect("split found");
        assert_eq!(hist[split].role, "user");
        assert!(hist[split].parts.iter().all(|p| p.function_response.is_none()));
        assert!(split >= 2 && split < hist.len());
    }
}
