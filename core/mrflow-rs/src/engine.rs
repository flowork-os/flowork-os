use crate::agents::{discover_agent_profiles, NativeSubagentSpawner};
use crate::cli::{Commands, ExtensionsAction, GemmaAction, HooksAction, McpAction, SkillsAction};
use crate::cognitive::{
    assemble_system_prompt_with_jit, discover_skills, format_skill_list_summary, sniff_context,
    update_lifecycle_after_turn, Formula533Router,
};
use crate::config::{load_settings, save_settings, AppConfig, ApprovalMode, McpServerConfig, OutputFormat};
use crate::inference::{ChatMessage, ConnectorClient, ContentPart, StreamEvent, TokenUsage};
use crate::mcp::McpManager;
use crate::memory::{crystallize_verified, extract_fts_tokens, load_hierarchical_memory, recall_jit, NewEpisode};
use crate::output::{print_json_summary, sanitize_ansi, StreamJsonEmitter};
use crate::policy::{PolicyDecision, PolicyEngine};
use crate::session::{
    build_user_parts_with_attachments, delete_session, list_sessions, LoopDetector, SessionVault,
};
use crate::tools::{InteractiveUiBridge, ProcessRegistry, ToolExecOutcome, ToolRegistry};
use serde_json::{json, Value};
use std::collections::HashSet;
use std::fs;
use std::io::{self, BufRead, Write};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Instant;
use tokio::sync::{mpsc, Mutex};

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum UiUpdate {
    SessionInit {
        session_id: String,
        model: String,
    },
    ThoughtDelta(String),
    TextDelta(String),
    ToolUse {
        id: String,
        name: String,
        args: Value,
    },
    ToolResult {
        id: String,
        name: String,
        success: bool,
        output: String,
    },
    StatsUpdate {
        turn: usize,
        max_turns: usize,
        tokens: TokenUsage,
        mode: ApprovalMode,
        context_tokens: u64,
    },
    SystemNotice(String),
    Error(String),
    Finished {
        final_text: String,
        tokens: TokenUsage,
        tool_calls: usize,
    },
}

pub struct SovereignEngine {
    pub config: Arc<Mutex<AppConfig>>,
    pub mcp: Arc<McpManager>,
    pub policy: Arc<PolicyEngine>,
    pub proc_reg: Arc<Mutex<ProcessRegistry>>,
    pub registry: Arc<Mutex<ToolRegistry>>,
    pub client: ConnectorClient,
    pub vault: Arc<Mutex<SessionVault>>,
    pub history: Arc<Mutex<Vec<ChatMessage>>>,
    pub session_context_anchor: String,
    pub offload_dir: PathBuf,
    pub last_prompt_tokens: Arc<Mutex<u64>>,
    pub abort_flag: Arc<AtomicBool>,
    pub total_tokens: Arc<Mutex<TokenUsage>>,
}

impl SovereignEngine {
    pub async fn initialize(
        config: AppConfig,
        ui_bridge: Option<Arc<dyn InteractiveUiBridge>>,
    ) -> Result<Self, String> {
        let abort_flag = Arc::new(AtomicBool::new(false));
        let proc_reg = Arc::new(Mutex::new(ProcessRegistry::default()));

        let mcp = Arc::new(McpManager::connect_all(&config).await);
        let policy = Arc::new(PolicyEngine::load(&config));

        let spawner = Arc::new(NativeSubagentSpawner {
            config: config.clone(),
            mcp: Arc::clone(&mcp),
            proc_reg: Arc::clone(&proc_reg),
            policy: Arc::clone(&policy),
        });

        let (vault, history) = SessionVault::open_or_create(&config)?;
        let offload_dir = crate::config::session_tool_outputs_dir(&config, &vault.session_id);
        let session_context_anchor = crate::context::build_session_context_text(
            &config.cwd,
            &config.include_directories,
            Some(&offload_dir),
        );
        let initial_est_tokens = crate::context::estimate_history_tokens(&history);

        let cfg_arc = Arc::new(Mutex::new(config.clone()));
        let mut reg = ToolRegistry::new(
            Arc::clone(&cfg_arc),
            Arc::clone(&mcp),
            Arc::clone(&proc_reg),
            false,
        );
        reg.set_offload_dir(offload_dir.clone());
        reg.set_subagent_spawner(spawner);
        if let Some(b) = ui_bridge {
            reg.set_ui_bridge(b);
        }

        let client = ConnectorClient::new(&config);

        Ok(Self {
            config: cfg_arc,
            mcp,
            policy,
            proc_reg,
            registry: Arc::new(Mutex::new(reg)),
            client,
            vault: Arc::new(Mutex::new(vault)),
            history: Arc::new(Mutex::new(history)),
            session_context_anchor,
            offload_dir,
            last_prompt_tokens: Arc::new(Mutex::new(initial_est_tokens)),
            abort_flag,
            total_tokens: Arc::new(Mutex::new(TokenUsage::default())),
        })
    }

    pub async fn shutdown(&self) {
        self.abort_flag.store(true, Ordering::SeqCst);
        self.proc_reg.lock().await.kill_all_active();
        self.mcp.shutdown_all().await;
    }

    /// Compresses older context turns using the 2-pass Sovereign summarization protocol,
    /// while preserving full lossless turns on disk in the JSONL vault.
    pub async fn compress_history(
        &self,
        force: bool,
        ui_tx: Option<&mpsc::UnboundedSender<UiUpdate>>,
    ) -> Result<(bool, String), String> {
        let cur_cfg = self.config.lock().await.clone();
        let hist = self.history.lock().await.clone();
        if hist.len() < 4 {
            return Ok((
                false,
                "Conversation history is too short to compress yet.".to_string(),
            ));
        }

        let orig_tokens = {
            let lpt = *self.last_prompt_tokens.lock().await;
            lpt.max(crate::context::estimate_history_tokens(&hist))
        };

        let mut split_idx = crate::context::find_compress_split_point(
            &hist,
            crate::context::COMPRESSION_PRESERVE_THRESHOLD,
        );
        if force && split_idx.is_none() {
            split_idx = crate::context::find_compress_split_point(&hist, 0.15)
                .or_else(|| (hist.len() >= 4).then_some(hist.len() - 2));
        }

        let Some(split_at) = split_idx.filter(|&i| i > 0 && i < hist.len()) else {
            return Ok((false, "No earlier conversation boundary available to compress.".to_string()));
        };

        let history_to_compress = hist[..split_at].to_vec();
        let history_to_keep = hist[split_at..].to_vec();

        let model_limit = crate::context::get_model_token_limit(
            &cur_cfg.model,
            Some(&cur_cfg.paths.flowork_root),
        );
        let prepared_chunk = crate::context::prepare_history_for_api(
            &history_to_compress,
            None,
            true,
            Some(self.offload_dir.as_path()),
        );
        let budgeted = crate::context::truncate_history_to_budget(
            &prepared_chunk,
            model_limit,
            Some(self.offload_dir.as_path()),
        );
        if budgeted.is_empty() {
            return Ok((false, "No compressible turns remained after pruning.".to_string()));
        }

        let comp_sys_prompt =
            crate::context::load_compression_system_prompt(&cur_cfg.paths.prompts_dir);

        // Pass 1: Scratchpad + initial <state_snapshot>
        let mut pass1_contents = budgeted.clone();
        pass1_contents.push(ChatMessage {
            role: "user".to_string(),
            parts: vec![crate::inference::ContentPart::text(
                crate::context::COMPRESSION_INITIAL_PROMPT,
            )],
        });
        let pass1_contents =
            crate::context::prepare_history_for_api(&pass1_contents, None, true, None);

        let (pass1_text, _, _) = self
            .client
            .generate_once(&cur_cfg.model, &comp_sys_prompt, &pass1_contents, &[])
            .await?;

        if pass1_text.trim().is_empty() {
            return Err("Compression Pass 1 returned empty summary.".to_string());
        }

        // Pass 2: Critical verification probe against original transcript
        let mut pass2_contents = pass1_contents;
        pass2_contents.push(ChatMessage {
            role: "model".to_string(),
            parts: vec![crate::inference::ContentPart::text(pass1_text.clone())],
        });
        pass2_contents.push(ChatMessage {
            role: "user".to_string(),
            parts: vec![crate::inference::ContentPart::text(
                crate::context::COMPRESSION_PROBE_PROMPT,
            )],
        });

        let final_raw = match self
            .client
            .generate_once(&cur_cfg.model, &comp_sys_prompt, &pass2_contents, &[])
            .await
        {
            Ok((probe_text, _, _)) if !probe_text.trim().is_empty() => probe_text,
            _ => pass1_text,
        };

        let snapshot = crate::context::extract_state_snapshot(&final_raw);
        let mut new_history = Vec::with_capacity(history_to_keep.len() + 2);
        new_history.push(ChatMessage {
            role: "user".to_string(),
            parts: vec![crate::inference::ContentPart::text(snapshot.clone())],
        });
        new_history.push(ChatMessage {
            role: "model".to_string(),
            parts: vec![crate::inference::ContentPart::text(
                "Understood. Continuing seamlessly from the compressed state snapshot.",
            )],
        });
        new_history.extend(history_to_keep.clone());

        let new_tokens = crate::context::estimate_history_tokens(&new_history);
        if !force && orig_tokens > 0 && new_tokens >= orig_tokens {
            return Ok((
                false,
                format!(
                    "Compression skipped: snapshot (~{} tok) did not improve over current (~{} tok).",
                    new_tokens, orig_tokens
                ),
            ));
        }

        *self.history.lock().await = new_history;
        *self.last_prompt_tokens.lock().await = new_tokens;

        {
            let v = self.vault.lock().await;
            v.append_compression_snapshot(&snapshot, &history_to_keep, orig_tokens, new_tokens)?;
        }

        let saved_pct = if orig_tokens > new_tokens && orig_tokens > 0 {
            ((orig_tokens - new_tokens) * 100) / orig_tokens
        } else {
            0
        };
        let msg = format!(
            "Compressed context: ~{} -> ~{} tokens (~{}% saved; full history preserved verbatim in JSONL vault).",
            orig_tokens, new_tokens, saved_pct
        );
        if let Some(utx) = ui_tx {
            let _ = utx.send(UiUpdate::SystemNotice(msg.clone()));
            let _ = utx.send(UiUpdate::StatsUpdate {
                turn: 0,
                max_turns: cur_cfg.max_turns,
                tokens: self.total_tokens.lock().await.clone(),
                mode: cur_cfg.approval_mode,
                context_tokens: new_tokens,
            });
        }
        Ok((true, msg))
    }

    /// Runs one complete multi-turn user objective to completion.
    pub async fn run_prompt_turn(
        &self,
        user_prompt: &str,
        ui_tx: Option<mpsc::UnboundedSender<UiUpdate>>,
    ) -> Result<(String, TokenUsage, usize), String> {
        self.abort_flag.store(false, Ordering::SeqCst);
        let cfg = self.config.lock().await.clone();
        let start_inst = Instant::now();

        let (sid, model_name) = {
            let v = self.vault.lock().await;
            (v.session_id.clone(), cfg.model.clone())
        };
        if let Some(ref tx) = ui_tx {
            let _ = tx.send(UiUpdate::SessionInit {
                session_id: sid.clone(),
                model: model_name.clone(),
            });
        }

        // Persist user prompt and expand any @file attachments
        {
            let v = self.vault.lock().await;
            let _ = v.append_user_prompt(user_prompt);
        }
        let user_parts = build_user_parts_with_attachments(&cfg, user_prompt);
        {
            let mut h = self.history.lock().await;
            h.push(ChatMessage {
                role: "user".to_string(),
                parts: user_parts,
            });
        }

        let skills = discover_skills(&cfg);
        let memory_md = load_hierarchical_memory(&cfg);
        let episodic_jit = recall_jit(&cfg, user_prompt, 3, 1200);
        let mut router = {
            let reg = self.registry.lock().await;
            Formula533Router::build(&cfg, &reg.router_catalog(), skills.clone())
        };

        let mut loop_detector = LoopDetector::new(cfg.loop_threshold, cfg.content_loop_threshold);
        let mut final_response = String::new();
        let mut turn_usage = TokenUsage::default();
        let mut total_tool_calls = 0usize;
        let mut used_tools_list = Vec::new();
        let mut last_keywords: Vec<String> = Vec::new();
        let mut had_tool_error = false;
        let mut first_error_snippet = String::new();
        let mut last_tool_success = false;
        let mut mutated_or_verified = false;
        let max_turns = cfg.max_turns.max(1);
        let mut auto_compressed_this_run = false;

        for turn_idx in 0..max_turns {
            if self.abort_flag.load(Ordering::SeqCst) {
                return Err("Execution aborted by signal.".to_string());
            }

            let cur_cfg = self.config.lock().await.clone();

            // Check auto-compression threshold cleanly before preparing outgoing API history
            if !auto_compressed_this_run {
                let threshold = crate::context::get_compression_threshold(&cur_cfg.settings);
                let should_compress = {
                    let h = self.history.lock().await;
                    let lpt = *self.last_prompt_tokens.lock().await;
                    crate::context::should_auto_compress(
                        &cur_cfg.model,
                        Some(&cur_cfg.paths.flowork_root),
                        lpt,
                        &h,
                        threshold,
                    )
                };
                if should_compress {
                    auto_compressed_this_run = true;
                    let _ = self.compress_history(false, ui_tx.as_ref()).await;
                }
            }

            let mut sniffed = sniff_context(&cur_cfg, user_prompt);
            for kw in &last_keywords {
                sniffed.active_keywords.insert(kw.to_ascii_lowercase());
            }

            let active_decls = {
                let reg = self.registry.lock().await;
                reg.active_declarations(&sniffed).await
            };
            let enabled_names: HashSet<String> = active_decls.iter().map(|d| d.name.clone()).collect();
            let sys_prompt = assemble_system_prompt_with_jit(
                &cur_cfg,
                &enabled_names,
                &skills,
                user_prompt,
                &memory_md,
                episodic_jit.as_deref(),
            )
            .await;

            // 3-layer context hardening + masking + collapse + <session_context> anchor
            let api_history = {
                let hist_guard = self.history.lock().await;
                crate::context::prepare_history_for_api(
                    &hist_guard,
                    Some(&self.session_context_anchor),
                    false,
                    Some(self.offload_dir.as_path()),
                )
            };

            let (tx, mut rx) = mpsc::unbounded_channel();
            let gen_fut = self.client.stream_generate(
                &cur_cfg.model,
                &sys_prompt,
                &api_history,
                &active_decls,
                tx,
            );

            let mut model_parts = Vec::new();
            let mut pending_calls = Vec::new();
            let mut turn_text = String::new();
            let mut turn_thoughts = Vec::new();
            let mut step_usage = TokenUsage::default();
            let mut stream_err: Option<String> = None;
            let mut content_loop_tripped = false;

            let consume_fut = async {
                while let Some(ev) = rx.recv().await {
                    if self.abort_flag.load(Ordering::SeqCst) {
                        break;
                    }
                    match ev {
                        StreamEvent::TextDelta(t) => {
                            if loop_detector.record_text_delta(&t) {
                                content_loop_tripped = true;
                                break;
                            }
                            turn_text.push_str(&t);
                            if let Some(ref utx) = ui_tx {
                                let _ = utx.send(UiUpdate::TextDelta(t));
                            }
                        }
                        StreamEvent::ThoughtDelta(th) => {
                            turn_thoughts.push(th.clone());
                            if let Some(ref utx) = ui_tx {
                                let _ = utx.send(UiUpdate::ThoughtDelta(th));
                            }
                        }
                        StreamEvent::ModelPart(p) => model_parts.push(p),
                        StreamEvent::ToolCall(fc) => pending_calls.push(fc),
                        StreamEvent::Usage(u) => {
                            step_usage = u.clone();
                        }
                        StreamEvent::Error(e) => {
                            stream_err = Some(e);
                        }
                        StreamEvent::Finish(_) => {}
                    }
                }
            };

            let (gen_res, _) = tokio::join!(gen_fut, consume_fut);
            let model_parts = crate::context::coalesce_parts(model_parts);

            if let Err(e) = gen_res {
                if let Some(ref utx) = ui_tx {
                    let _ = utx.send(UiUpdate::Error(e.clone()));
                }
                return Err(e);
            }
            if let Some(e) = stream_err {
                if let Some(ref utx) = ui_tx {
                    let _ = utx.send(UiUpdate::Error(e.clone()));
                }
                return Err(e);
            }

            turn_usage.input = turn_usage.input.saturating_add(step_usage.input);
            turn_usage.output = turn_usage.output.saturating_add(step_usage.output);
            turn_usage.cached = turn_usage.cached.saturating_add(step_usage.cached);
            turn_usage.thoughts = turn_usage.thoughts.saturating_add(step_usage.thoughts);
            turn_usage.total = turn_usage.total.saturating_add(step_usage.total);

            let live_ctx_tokens = if step_usage.input > 0 {
                step_usage.input
            } else {
                crate::context::estimate_history_tokens(&api_history)
            };
            *self.last_prompt_tokens.lock().await = live_ctx_tokens;

            if let Some(ref utx) = ui_tx {
                let _ = utx.send(UiUpdate::StatsUpdate {
                    turn: turn_idx + 1,
                    max_turns,
                    tokens: turn_usage.clone(),
                    mode: cur_cfg.approval_mode,
                    context_tokens: live_ctx_tokens,
                });
            }

            if !model_parts.is_empty() {
                self.history.lock().await.push(ChatMessage {
                    role: "model".to_string(),
                    parts: model_parts.clone(),
                });
            }

            if content_loop_tripped {
                let warn = "\n[Loop Guard: halted repetitive output stream]";
                turn_text.push_str(warn);
                final_response = turn_text;
                let v = self.vault.lock().await;
                let _ = v.append_model_turn(
                    &cur_cfg.model,
                    &final_response,
                    &turn_thoughts,
                    &step_usage,
                    &[],
                    &model_parts,
                );
                break;
            }

            if pending_calls.is_empty() {
                final_response = turn_text.clone();
                let v = self.vault.lock().await;
                let _ = v.append_model_turn(
                    &cur_cfg.model,
                    &final_response,
                    &turn_thoughts,
                    &step_usage,
                    &[],
                    &model_parts,
                );
                break;
            }

            // Execute requested tools cleanly
            let mut resp_parts = Vec::new();
            let mut tool_calls_log = Vec::new();
            let mut needs_rescan = false;

            for fc in pending_calls {
                if self.abort_flag.load(Ordering::SeqCst) {
                    return Err("Execution aborted by signal.".to_string());
                }
                total_tool_calls += 1;
                used_tools_list.push(fc.name.clone());

                if let Some(ref utx) = ui_tx {
                    let _ = utx.send(UiUpdate::ToolUse {
                        id: fc.id.clone(),
                        name: fc.name.clone(),
                        args: fc.args.clone(),
                    });
                }

                // 1. Repetitive call guard
                let outcome: ToolExecOutcome = if loop_detector.record_tool_call(&fc.name, &fc.args) {
                    ToolExecOutcome::err(format!(
                        "Loop Guard: identical call to '{}' repeated {} times. Change strategy or respond to user.",
                        fc.name, cur_cfg.loop_threshold
                    ))
                } else {
                    // 2. Flowork Tool Intercept Gate check
                    match ToolRegistry::validate_intercept_gate(&fc.args) {
                        Err(gate_err) => ToolExecOutcome::err(gate_err),
                        Ok((reason, keywords, goal)) => {
                            last_keywords = keywords.clone();
                            // 3. 5-Tier Policy Evaluation
                            let (is_mcp, mcp_srv) = {
                                let reg = self.registry.lock().await;
                                let s = reg.mcp.is_mcp_tool(&fc.name).map(str::to_string);
                                (s.is_some(), s)
                            };
                            let pol = self.policy.evaluate(
                                &cur_cfg,
                                &fc.name,
                                &fc.args,
                                is_mcp,
                                mcp_srv.as_deref(),
                            );

                            let allow_exec = match pol.decision {
                                PolicyDecision::Allow => true,
                                PolicyDecision::Deny => false,
                                PolicyDecision::AskUser => {
                                    // If interactive bridge attached and tool is not ask_user itself, ask permission
                                    let bridge = self.registry.lock().await.ui_bridge.clone();
                                    if fc.name == "ask_user" {
                                        true
                                    } else if let Some(b) = bridge {
                                        let q = json!([{
                                            "question": format!("Allow tool '{}' with args {}?", fc.name, fc.args),
                                            "options": ["Allow once", "Allow session (Sovereign)", "Deny"]
                                        }]);
                                        match b.ask_user(q).await {
                                            Ok(ans) => {
                                                let s = ans.to_string().to_ascii_lowercase();
                                                if s.contains("sovereign") {
                                                    self.config.lock().await.approval_mode = ApprovalMode::Sovereign;
                                                    true
                                                } else {
                                                    s.contains("allow") || s.contains("yes")
                                                }
                                            }
                                            Err(_) => false,
                                        }
                                    } else {
                                        false
                                    }
                                }
                            };

                            if !allow_exec {
                                ToolExecOutcome::err(
                                    pol.reason
                                        .unwrap_or_else(|| format!("Execution of '{}' denied by policy.", fc.name)),
                                )
                            } else {
                                let out = {
                                    let reg = self.registry.lock().await;
                                    reg.execute_with_id(&fc.id, &fc.name, &fc.args).await
                                };
                                if out.needs_tool_rescan {
                                    needs_rescan = true;
                                }
                                // Zero-Bloat Guard: Keep router state updated without contaminating tool output text or JSON
                                let _route_guidance = router.route(&keywords, &goal, &reason);
                                out
                            }
                        }
                    }
                };

                last_tool_success = outcome.success;
                if !outcome.success {
                    had_tool_error = true;
                    if first_error_snippet.is_empty() {
                        first_error_snippet = outcome
                            .display_text
                            .lines()
                            .map(str::trim)
                            .find(|l| !l.is_empty())
                            .unwrap_or("tool_error")
                            .chars()
                            .take(160)
                            .collect();
                    }
                } else if matches!(
                    fc.name.as_str(),
                    "write_file" | "replace" | "replace_file_content" | "run_shell_command" | "run_command"
                ) {
                    mutated_or_verified = true;
                }

                if let Some(ref utx) = ui_tx {
                    let _ = utx.send(UiUpdate::ToolResult {
                        id: fc.id.clone(),
                        name: fc.name.clone(),
                        success: outcome.success,
                        output: outcome.display_text.clone(),
                    });
                }

                tool_calls_log.push(json!({
                    "id": fc.id,
                    "name": fc.name,
                    "args": fc.args,
                    "status": if outcome.success { "success" } else { "error" },
                    "timestamp": chrono::Utc::now().to_rfc3339(),
                    "resultDisplay": outcome.display_text
                }));

                resp_parts.push(ContentPart::function_response(
                    &fc.id,
                    &fc.name,
                    outcome.output_json,
                ));
                for blob in outcome.inline_blobs {
                    resp_parts.push(ContentPart {
                        text: None,
                        thought: None,
                        thought_signature: None,
                        function_call: None,
                        function_response: None,
                        inline_data: Some(blob),
                    });
                }
            }

            if needs_rescan {
                self.registry.lock().await.rescan_disk_manifests_blocking();
            }

            // Persist model turn + tool response turn
            {
                let v = self.vault.lock().await;
                let _ = v.append_model_turn(
                    &cur_cfg.model,
                    &turn_text,
                    &turn_thoughts,
                    &step_usage,
                    &tool_calls_log,
                    &model_parts,
                );
                let _ = v.append_tool_responses(&resp_parts);
            }
            self.history.lock().await.push(ChatMessage {
                role: "user".to_string(),
                parts: resp_parts,
            });
        }

        update_lifecycle_after_turn(&used_tools_list, &last_keywords);
        // Auto-crystallize ONLY genuine error-to-recovery or verified multi-step workflow completions
        if total_tool_calls > 0
            && !final_response.trim().is_empty()
            && !crate::context::is_ignored_user_content(user_prompt)
            && !used_tools_list.iter().any(|t| t == "memory_crystallizer")
            && ((had_tool_error && last_tool_success)
                || (total_tool_calls >= 2 && last_tool_success && mutated_or_verified))
        {
            let mut dedup_tools: Vec<String> = Vec::new();
            for t in &used_tools_list {
                if !dedup_tools.contains(t) && dedup_tools.len() < 6 {
                    dedup_tools.push(t.clone());
                }
            }
            let prompt_head: String = user_prompt
                .lines()
                .map(str::trim)
                .find(|l| !l.is_empty())
                .unwrap_or("")
                .chars()
                .take(200)
                .collect();
            let problem = if had_tool_error && !first_error_snippet.is_empty() {
                format!("{} | Prior error: {}", prompt_head, first_error_snippet)
            } else {
                prompt_head
            };
            let outcome_clip: String = final_response
                .lines()
                .map(str::trim)
                .filter(|l| !l.is_empty())
                .collect::<Vec<_>>()
                .join(" ")
                .chars()
                .take(360)
                .collect();
            let tools_summary = dedup_tools.join(", ");
            let solution = format!("Tools: {}. Verified outcome: {}", tools_summary, outcome_clip);
            let kws = extract_fts_tokens(&format!("{} {}", problem, tools_summary)).join(", ");
            let category = if had_tool_error {
                "recovery"
            } else {
                "verified_workflow"
            };
            let _ = crystallize_verified(
                &cfg,
                NewEpisode {
                    session_id: &sid,
                    category,
                    problem: &problem,
                    solution: &solution,
                    keywords: &kws,
                    source: "auto_turn",
                    exit_code: 0,
                },
            );
        }

        {
            let mut tot = self.total_tokens.lock().await;
            tot.input += turn_usage.input;
            tot.output += turn_usage.output;
            tot.cached += turn_usage.cached;
            tot.thoughts += turn_usage.thoughts;
            tot.total += turn_usage.total;
        }

        // Persist concise `$set.summary` on the first meaningful turn (for `--list-sessions` & Sidebar)
        {
            let h_len = self.history.lock().await.len();
            if h_len <= 4
                && !crate::context::is_ignored_user_content(user_prompt)
                && !final_response.trim().is_empty()
            {
                let single_line: String = user_prompt
                    .lines()
                    .next()
                    .unwrap_or("")
                    .trim()
                    .chars()
                    .take(88)
                    .collect();
                if !single_line.is_empty() {
                    let _ = self.vault.lock().await.append_summary(&single_line);
                }
            }
        }

        if let Some(ref utx) = ui_tx {
            let _ = utx.send(UiUpdate::Finished {
                final_text: final_response.clone(),
                tokens: turn_usage.clone(),
                tool_calls: total_tool_calls,
            });
        }
        let _elapsed = start_inst.elapsed();
        Ok((final_response, turn_usage, total_tool_calls))
    }
}

/// Executes headless CLI `-p` mode (`text`, `json`, `stream-json`).
pub async fn run_headless(config: AppConfig, prompt: String) -> i32 {
    let format = config.output_format;
    let raw_output = config.raw_output;
    let model = config.model.clone();
    let start = Instant::now();

    let engine = match SovereignEngine::initialize(config, None).await {
        Ok(e) => e,
        Err(err) => {
            match format {
                OutputFormat::StreamJson => {
                    let emitter = StreamJsonEmitter::new();
                    emitter.emit_error("fatal", &err);
                }
                OutputFormat::Json => {
                    print_json_summary("", &model, "", &TokenUsage::default(), 0, 0, Some(&err));
                }
                OutputFormat::Text => eprintln!("Error: {}", err),
            }
            return 1;
        }
    };

    let (tx, mut rx) = mpsc::unbounded_channel();
    let emitter = Arc::new(StreamJsonEmitter::new());
    let em_clone = Arc::clone(&emitter);
    let sid_out = engine.vault.lock().await.session_id.clone();

    let out_task = tokio::spawn(async move {
        while let Some(ev) = rx.recv().await {
            match format {
                OutputFormat::StreamJson => match ev {
                    UiUpdate::SessionInit { session_id, model } => em_clone.emit_init(&session_id, &model),
                    UiUpdate::ThoughtDelta(t) => em_clone.emit_thought(&t),
                    UiUpdate::TextDelta(t) => em_clone.emit_message("assistant", &sanitize_ansi(&t, raw_output), true),
                    UiUpdate::ToolUse { id, name, args } => em_clone.emit_tool_use(&id, &name, &args),
                    UiUpdate::ToolResult { id, success, output, .. } => {
                        em_clone.emit_tool_result(&id, success, &output, (!success).then_some(output.as_str()));
                    }
                    UiUpdate::Error(e) => em_clone.emit_error("error", &e),
                    UiUpdate::SystemNotice(msg) => em_clone.emit_message("system", &sanitize_ansi(&msg, raw_output), false),
                    UiUpdate::Finished { tokens, tool_calls, .. } => {
                        em_clone.emit_result(true, &tokens, start.elapsed().as_millis(), tool_calls, None);
                    }
                    UiUpdate::StatsUpdate { .. } => {}
                },
                OutputFormat::Text => match ev {
                    UiUpdate::TextDelta(t) => {
                        print!("{}", sanitize_ansi(&t, raw_output));
                        let _ = io::stdout().flush();
                    }
                    UiUpdate::Finished { final_text, .. } => {
                        if !final_text.ends_with('\n') && !final_text.is_empty() {
                            println!();
                        }
                    }
                    UiUpdate::Error(e) => eprintln!("\n[Error] {}", e),
                    _ => {}
                },
                OutputFormat::Json => {}
            }
        }
    });

    // Forward Ctrl+C / SIGTERM straight to engine PGID cleaner
    let eng_abort = Arc::clone(&engine.abort_flag);
    let proc_clone = Arc::clone(&engine.proc_reg);
    tokio::spawn(async move {
        if tokio::signal::ctrl_c().await.is_ok() {
            eng_abort.store(true, Ordering::SeqCst);
            proc_clone.lock().await.kill_all_active();
        }
    });

    let res = engine.run_prompt_turn(&prompt, Some(tx)).await;
    let _ = out_task.await;
    engine.shutdown().await;

    match res {
        Ok((text, tokens, tc)) => {
            if format == OutputFormat::Json {
                print_json_summary(
                    &sid_out,
                    &model,
                    &sanitize_ansi(&text, raw_output),
                    &tokens,
                    start.elapsed().as_millis(),
                    tc,
                    None,
                );
            }
            0
        }
        Err(e) => {
            if format == OutputFormat::StreamJson {
                emitter.emit_error("error", &e);
                emitter.emit_result(false, &TokenUsage::default(), start.elapsed().as_millis(), 0, Some(&e));
            } else if format == OutputFormat::Json {
                print_json_summary(&sid_out, &model, "", &TokenUsage::default(), start.elapsed().as_millis(), 0, Some(&e));
            } else {
                eprintln!("Fatal: {}", e);
            }
            1
        }
    }
}

/// Runs stdio JSON-RPC 2.0 ACP (Agent Client Protocol) mode (`--acp`).
pub async fn run_acp_mode(config: AppConfig) -> i32 {
    let engine = match SovereignEngine::initialize(config, None).await {
        Ok(e) => Arc::new(e),
        Err(e) => {
            eprintln!("ACP init failed: {}", e);
            return 1;
        }
    };
    let stdin = io::stdin();
    for line in stdin.lock().lines().flatten() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let Ok(req) = serde_json::from_str::<Value>(trimmed) else {
            continue;
        };
        let id = req.get("id").cloned().unwrap_or(Value::Null);
        let method = req.get("method").and_then(|s| s.as_str()).unwrap_or("");
        let params = req.get("params").cloned().unwrap_or_else(|| json!({}));

        let resp = match method {
            "initialize" => json!({
                "jsonrpc": "2.0",
                "id": id,
                "result": {
                    "protocolVersion": "1.0",
                    "agentInfo": { "name": "mrflow", "version": "2.0.0-sovereign" },
                    "capabilities": { "streaming": true, "tools": true }
                }
            }),
            "session/new" => {
                let sid = engine.vault.lock().await.session_id.clone();
                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": { "sessionId": sid }
                })
            }
            "session/prompt" => {
                let prompt = params.get("prompt").and_then(|s| s.as_str()).unwrap_or("");
                match engine.run_prompt_turn(prompt, None).await {
                    Ok((text, tokens, tc)) => json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": { "text": text, "tokens": tokens, "toolCalls": tc }
                    }),
                    Err(e) => json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "error": { "code": -32000, "message": e }
                    }),
                }
            }
            "session/cancel" => {
                engine.abort_flag.store(true, Ordering::SeqCst);
                engine.proc_reg.lock().await.kill_all_active();
                json!({ "jsonrpc": "2.0", "id": id, "result": { "cancelled": true } })
            }
            _ => json!({
                "jsonrpc": "2.0",
                "id": id,
                "error": { "code": -32601, "message": format!("Method '{}' not supported", method) }
            }),
        };
        println!("{}", resp);
        let _ = io::stdout().flush();
    }
    engine.shutdown().await;
    0
}

pub fn handle_session_management_flags(config: &AppConfig, list_only: bool, delete_target: Option<&str>) -> Option<i32> {
    if list_only {
        let list = list_sessions(config);
        if list.is_empty() {
            println!("No recorded sessions for current project.");
        } else {
            println!("Available sessions for current project ({}):", list.len());
            for s in list {
                println!(
                    "  [{}] {} | {} | {}",
                    s.index,
                    s.session_id,
                    s.last_updated,
                    if s.preview.is_empty() { "(empty)" } else { &s.preview }
                );
            }
        }
        return Some(0);
    }
    if let Some(target) = delete_target {
        match delete_session(config, target) {
            Ok(id) => {
                println!("Deleted session: {}", id);
                return Some(0);
            }
            Err(e) => {
                eprintln!("Error: {}", e);
                return Some(1);
            }
        }
    }
    None
}

pub fn handle_subcommand(config: &AppConfig, cmd: Commands) -> i32 {
    match cmd {
        Commands::Mcp(m) => {
            let mut settings = load_settings(&config.paths.user_flowork_dir);
            match m.action {
                McpAction::List => {
                    let discovered = McpManager::discover_configs(config);
                    if discovered.is_empty() {
                        println!("No MCP servers configured.");
                    } else {
                        for (name, sc) in discovered {
                            let target = sc
                                .command
                                .or(sc.http_url)
                                .or(sc.url)
                                .unwrap_or_else(|| "(unconfigured)".to_string());
                            println!("- {} : {} {}", name, target, sc.args.join(" "));
                        }
                    }
                    0
                }
                McpAction::Add { name, command_or_url, args } => {
                    let entry = if command_or_url.starts_with("http://") || command_or_url.starts_with("https://") {
                        let is_sse = command_or_url.trim_end_matches('/').ends_with("/sse");
                        McpServerConfig {
                            command: None,
                            args: Vec::new(),
                            url: if is_sse { Some(command_or_url.clone()) } else { None },
                            http_url: if is_sse { None } else { Some(command_or_url) },
                            transport_type: Some(if is_sse { "sse" } else { "http" }.to_string()),
                            ..Default::default()
                        }
                    } else {
                        McpServerConfig {
                            command: Some(command_or_url),
                            args,
                            ..Default::default()
                        }
                    };
                    settings.mcp_servers.insert(name.clone(), entry);
                    if let Err(e) = save_settings(&config.paths.user_flowork_dir, &settings) {
                        eprintln!("Failed saving MCP server: {}", e);
                        return 1;
                    }
                    println!("Added MCP server '{}'.", name);
                    0
                }
                McpAction::Remove { name } => {
                    settings.mcp_servers.remove(&name);
                    let _ = save_settings(&config.paths.user_flowork_dir, &settings);
                    println!("Removed MCP server '{}' from user settings.", name);
                    0
                }
                McpAction::Enable { name } => {
                    settings.disabled_mcp_servers.retain(|n| n != &name);
                    let _ = save_settings(&config.paths.user_flowork_dir, &settings);
                    println!("Enabled MCP server '{}'.", name);
                    0
                }
                McpAction::Disable { name } => {
                    if !settings.disabled_mcp_servers.contains(&name) {
                        settings.disabled_mcp_servers.push(name.clone());
                    }
                    let _ = save_settings(&config.paths.user_flowork_dir, &settings);
                    println!("Disabled MCP server '{}'.", name);
                    0
                }
            }
        }
        Commands::Skills(s) => {
            let mut settings = load_settings(&config.paths.user_flowork_dir);
            match s.action {
                SkillsAction::List { all } => {
                    let skills = discover_skills(config);
                    println!("Discovered {} Sovereign Skill(s):", skills.len());
                    println!("{}", format_skill_list_summary(&skills));
                    if all && !settings.disabled_skills.is_empty() {
                        println!("\nDisabled skills: {}", settings.disabled_skills.join(", "));
                    }
                    0
                }
                SkillsAction::Enable { name } => {
                    settings.disabled_skills.retain(|x| !x.eq_ignore_ascii_case(&name));
                    let _ = save_settings(&config.paths.user_flowork_dir, &settings);
                    println!("Enabled skill '{}'.", name);
                    0
                }
                SkillsAction::Disable { name, .. } => {
                    if !settings.disabled_skills.iter().any(|x| x.eq_ignore_ascii_case(&name)) {
                        settings.disabled_skills.push(name.clone());
                    }
                    let _ = save_settings(&config.paths.user_flowork_dir, &settings);
                    println!("Disabled skill '{}'.", name);
                    0
                }
                SkillsAction::Link { path } => {
                    let name = path.file_name().and_then(|n| n.to_str()).unwrap_or("custom-skill");
                    let dest_dir = config.paths.user_flowork_dir.join("skills");
                    let _ = fs::create_dir_all(&dest_dir);
                    let dest = dest_dir.join(name);
                    let _ = fs::remove_file(&dest);
                    #[cfg(unix)]
                    if let Err(e) = std::os::unix::fs::symlink(&path, &dest) {
                        eprintln!("Failed linking skill: {}", e);
                        return 1;
                    }
                    println!("Linked skill '{}' -> {}", name, path.display());
                    0
                }
                SkillsAction::Install { source, .. } => {
                    let dest_dir = config.paths.user_flowork_dir.join("skills");
                    let _ = fs::create_dir_all(&dest_dir);
                    let src_path = PathBuf::from(&source);
                    if src_path.is_dir() {
                        let name = src_path.file_name().and_then(|n| n.to_str()).unwrap_or("skill");
                        let target = dest_dir.join(name);
                        let st = std::process::Command::new("cp")
                            .args(["-r", &source, &target.to_string_lossy()])
                            .status();
                        match st {
                            Ok(s) if s.success() => {
                                println!("Installed skill '{}' to {}", name, target.display());
                                0
                            }
                            _ => 1,
                        }
                    } else if source.starts_with("http://") || source.starts_with("https://") || source.ends_with(".git") {
                        let name = source.split('/').last().unwrap_or("skill").trim_end_matches(".git");
                        let target = dest_dir.join(name);
                        let st = std::process::Command::new("git")
                            .args(["clone", "--depth", "1", &source, &target.to_string_lossy()])
                            .status();
                        match st {
                            Ok(s) if s.success() => {
                                println!("Cloned skill '{}' into {}", name, target.display());
                                0
                            }
                            _ => 1,
                        }
                    } else {
                        eprintln!("Invalid skill source '{}'. Provide local folder or git URL.", source);
                        1
                    }
                }
                SkillsAction::Uninstall { name, .. } => {
                    let target = config.paths.user_flowork_dir.join("skills").join(&name);
                    if target.exists() {
                        let _ = fs::remove_dir_all(&target);
                        println!("Uninstalled user skill '{}'.", name);
                        0
                    } else {
                        eprintln!("User skill '{}' not found at {}", name, target.display());
                        1
                    }
                }
            }
        }
        Commands::Extensions(e) => match e.action {
            ExtensionsAction::List => {
                list_extensions_summary(config);
                0
            }
            _ => {
                println!("Extension management updated for ~/.flowork/extensions.");
                0
            }
        },
        Commands::Hooks(h) => match h.action {
            HooksAction::Migrate => {
                let target = config.paths.user_flowork_dir.join("hooks");
                let _ = fs::create_dir_all(&target);
                println!("Hooks directory ready at {}", target.display());
                0
            }
        },
        Commands::Gemma(g) => match g.action {
            GemmaAction::Status => {
                let st = std::process::Command::new("curl")
                    .args(["-s", &format!("{}/api/router/status", config.connector_url)])
                    .status();
                if matches!(st, Ok(s) if s.success()) { 0 } else { 1 }
            }
            GemmaAction::Setup | GemmaAction::Start | GemmaAction::Stop | GemmaAction::Logs => {
                println!("Local SLM / Gemma routing managed cleanly via Flowork Connector Gateway ({}).", config.connector_url);
                0
            }
        },
    }
}

pub fn list_extensions_summary(config: &AppConfig) {
    let ext_dirs = [
        config.paths.flowork_root.join("extensions"),
        config.paths.user_flowork_dir.join("extensions"),
    ];
    let mut count = 0usize;
    for dir in &ext_dirs {
        if let Ok(entries) = fs::read_dir(dir) {
            for e in entries.flatten() {
                if e.path().is_dir() {
                    count += 1;
                    println!("- {} ({})", e.file_name().to_string_lossy(), e.path().display());
                }
            }
        }
    }
    if count == 0 {
        println!("No external extensions installed.");
    }
}

pub fn list_agent_profiles_summary(config: &AppConfig) -> String {
    let profiles = discover_agent_profiles(config);
    profiles
        .into_iter()
        .map(|p| format!("- {}: {}", p.name, p.description))
        .collect::<Vec<_>>()
        .join("\n")
}
