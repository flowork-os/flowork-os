use crate::cognitive::{discover_skills, sniff_context, Formula533Router};
use crate::config::{session_tool_outputs_dir, AppConfig};
use crate::inference::{ChatMessage, ConnectorClient, ContentPart, StreamEvent};
use crate::memory::load_hierarchical_memory;
use crate::policy::{PolicyDecision, PolicyEngine};
use crate::tools::{
    ProcessRegistry, SubagentFuture, SubagentInvocation, SubagentSpawner, ToolExecOutcome,
    ToolRegistry,
};
use serde_json::{json, Value};
use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct AgentProfile {
    pub name: String,
    #[allow(dead_code)]
    pub display_name: Option<String>,
    pub description: String,
    pub system_prompt: String,
    pub tools: Vec<String>,
    pub model: Option<String>,
    pub max_turns: Option<usize>,
    #[allow(dead_code)]
    pub kind: String,
    #[allow(dead_code)]
    pub source_path: Option<PathBuf>,
}

pub fn discover_agent_profiles(config: &AppConfig) -> Vec<AgentProfile> {
    let mut profiles = vec![
        AgentProfile {
            name: "codebase_investigator".to_string(),
            display_name: Some("Codebase Investigator".to_string()),
            description: "Deep codebase exploration, dependency tracing, and architecture discovery.".to_string(),
            system_prompt: "You are codebase_investigator, a specialist subagent operating inside an isolated context. Thoroughly search, inspect relevant files using read_file/glob/grep_search/list_directory, verify symbols empirically, and return a concise, high-density structured technical report with file paths and line numbers.".to_string(),
            tools: vec![
                "read_file".to_string(),
                "read_many_files".to_string(),
                "list_directory".to_string(),
                "glob".to_string(),
                "grep_search".to_string(),
                "complete_task".to_string(),
            ],
            model: None,
            max_turns: None,
            kind: "local".to_string(),
            source_path: None,
        },
        AgentProfile {
            name: "cli_help".to_string(),
            display_name: Some("CLI Help Agent".to_string()),
            description: "Assists with Mr. Flow CLI usage, slash commands, configuration, and Flowork OS troubleshooting.".to_string(),
            system_prompt: "You are cli_help, an authoritative Flowork OS CLI & runtime configuration specialist. Inspect /opt/floworkos documentation and return crisp actionable guidance.".to_string(),
            tools: vec![
                "read_file".to_string(),
                "list_directory".to_string(),
                "glob".to_string(),
                "grep_search".to_string(),
                "complete_task".to_string(),
            ],
            model: None,
            max_turns: None,
            kind: "local".to_string(),
            source_path: None,
        },
        AgentProfile {
            name: "kernel_sentinel".to_string(),
            display_name: Some("Kernel Sentinel".to_string()),
            description: "Linux 7.3.0 Rust Kernel telemetry, dmesg diagnostics, Landlock LSM audit, and hardware/GPU surveillance.".to_string(),
            system_prompt: "You are kernel_sentinel, a sovereign ring-0 diagnostics operative for Flowork OS. Run non-destructive read-only inspection commands and report exact empirical findings.".to_string(),
            tools: vec![
                "run_shell_command".to_string(),
                "read_file".to_string(),
                "glob".to_string(),
                "grep_search".to_string(),
                "list_directory".to_string(),
                "complete_task".to_string(),
            ],
            model: None,
            max_turns: None,
            kind: "local".to_string(),
            source_path: None,
        },
    ];

    let mut seen: HashSet<String> = profiles.iter().map(|p| p.name.clone()).collect();

    for dir in &config.paths.agents_dirs {
        let Ok(entries) = fs::read_dir(dir) else {
            continue;
        };
        for entry in entries.flatten() {
            let p = entry.path();
            if p.extension().and_then(|s| s.to_str()) != Some("md") {
                continue;
            }
            let fname = p
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("")
                .to_string();
            if fname.eq_ignore_ascii_case("readme") || fname.is_empty() {
                continue;
            }
            let Ok(raw) = fs::read_to_string(&p) else {
                continue;
            };
            let parsed = parse_agent_markdown(&fname, &raw, p);
            if seen.insert(parsed.name.clone()) {
                profiles.push(parsed);
            }
        }
    }

    profiles
}

fn parse_agent_markdown(fallback_name: &str, raw: &str, path: PathBuf) -> AgentProfile {
    let mut name = fallback_name.to_string();
    let mut display_name = None;
    let mut desc = format!("Custom specialist agent '{}'", fallback_name);
    let mut tools = Vec::new();
    let mut model = None;
    let mut max_turns = None;
    let mut kind = "local".to_string();
    let mut body = raw.trim().to_string();

    if let Some(stripped) = raw.strip_prefix("---") {
        if let Some(end_idx) = stripped.find("\n---") {
            let yaml = &stripped[..end_idx];
            body = stripped[end_idx + 4..].trim().to_string();
            let mut in_tools_list = false;

            for line in yaml.lines() {
                let t = line.trim();
                if t.is_empty() || t.starts_with('#') {
                    continue;
                }
                if t.starts_with("- ") && in_tools_list {
                    let item = t[2..].trim().trim_matches('"').trim_matches('\'').to_string();
                    if !item.is_empty() {
                        tools.push(item);
                    }
                    continue;
                }
                if let Some((k, v)) = t.split_once(':') {
                    in_tools_list = false;
                    let key = k.trim();
                    let val = v.trim();
                    let clean_val = val.trim_matches('"').trim_matches('\'');
                    match key {
                        "name" if !clean_val.is_empty() => name = clean_val.to_string(),
                        "display_name" | "displayName" if !clean_val.is_empty() => {
                            display_name = Some(clean_val.to_string());
                        }
                        "description" if !clean_val.is_empty() => desc = clean_val.to_string(),
                        "kind" if !clean_val.is_empty() => kind = clean_val.to_string(),
                        "model" if !clean_val.is_empty() && !clean_val.eq_ignore_ascii_case("inherit") => {
                            model = Some(clean_val.to_string());
                        }
                        "max_turns" | "maxTurns" => {
                            if let Ok(n) = clean_val.parse::<usize>() {
                                if n > 0 {
                                    max_turns = Some(n);
                                }
                            }
                        }
                        "tools" => {
                            if val.starts_with('[') && val.ends_with(']') {
                                for part in val[1..val.len() - 1].split(',') {
                                    let c = part.trim().trim_matches('"').trim_matches('\'');
                                    if !c.is_empty() {
                                        tools.push(c.to_string());
                                    }
                                }
                            } else if val.is_empty() {
                                in_tools_list = true;
                            } else {
                                for part in clean_val.split(',') {
                                    let c = part.trim();
                                    if !c.is_empty() {
                                        tools.push(c.to_string());
                                    }
                                }
                            }
                        }
                        _ => {}
                    }
                }
            }
        }
    }

    AgentProfile {
        name,
        display_name,
        description: desc,
        system_prompt: body,
        tools,
        model,
        max_turns,
        kind,
        source_path: Some(path),
    }
}

pub struct NativeSubagentSpawner {
    pub config: AppConfig,
    pub mcp: Arc<crate::mcp::McpManager>,
    pub proc_reg: Arc<Mutex<ProcessRegistry>>,
    pub policy: Arc<PolicyEngine>,
}

impl SubagentSpawner for NativeSubagentSpawner {
    fn spawn_subagent(&self, invocation: SubagentInvocation) -> SubagentFuture {
        let cfg = self.config.clone();
        let mcp = Arc::clone(&self.mcp);
        let proc_reg = Arc::clone(&self.proc_reg);
        let policy = Arc::clone(&self.policy);

        Box::pin(async move {
            run_isolated_subagent(cfg, mcp, proc_reg, policy, invocation).await
        })
    }
}

async fn run_isolated_subagent(
    mut config: AppConfig,
    mcp: Arc<crate::mcp::McpManager>,
    proc_reg: Arc<Mutex<ProcessRegistry>>,
    policy: Arc<PolicyEngine>,
    invocation: SubagentInvocation,
) -> ToolExecOutcome {
    let task = invocation.prompt.clone();
    let agent_name = invocation.name.clone();

    // Handle workspace isolation mode: "inherit" | "branch" | "share"
    let is_branch = invocation.workspace_mode.eq_ignore_ascii_case("branch");
    let branch_dir = if is_branch {
        let safe_name: String = agent_name
            .chars()
            .map(|c| if c.is_alphanumeric() || c == '_' { c } else { '_' })
            .collect();
        let bdir = std::env::temp_dir().join(format!(
            "flowork_branch_{}_{}",
            safe_name,
            chrono::Utc::now().timestamp_millis()
        ));
        let _ = fs::create_dir_all(&bdir);
        config.cwd = bdir.clone();
        config.include_directories.push(bdir.clone());
        Some(bdir)
    } else {
        None
    };

    let profiles = discover_agent_profiles(&config);
    let profile = profiles
        .into_iter()
        .find(|p| p.name.eq_ignore_ascii_case(&agent_name))
        .unwrap_or(AgentProfile {
            name: agent_name.clone(),
            display_name: None,
            description: "Specialized Flowork subagent".to_string(),
            system_prompt: format!(
                "You are subagent '{}'. Complete the delegated task thoroughly and return a crisp technical report.",
                agent_name
            ),
            tools: Vec::new(),
            model: invocation.model.clone(),
            max_turns: None,
            kind: "local".to_string(),
            source_path: None,
        });

    let conv_id = format!("subagent-{}", &Uuid::new_v4().to_string()[..8]);
    {
        let mut pr = proc_reg.lock().await;
        pr.register_subagent(
            conv_id.clone(),
            profile.display_name.clone().unwrap_or_else(|| profile.name.clone()),
            profile.name.clone(),
        );
    }

    // Recursion guard: is_subagent = true disables `invoke_agent` inside ToolRegistry
    let sub_cfg = Arc::new(Mutex::new(config.clone()));
    let sub_proc_reg = Arc::clone(&proc_reg);
    let mut registry = ToolRegistry::new(sub_cfg, mcp, sub_proc_reg, true);
    let offload_dir = session_tool_outputs_dir(
        &config,
        &format!("sub_{}_{}", profile.name, chrono::Utc::now().timestamp()),
    );
    registry.set_offload_dir(offload_dir.clone());

    let skills = discover_skills(&config);
    let sniffed = sniff_context(&config, &task);
    let allowed_tool_set: Option<HashSet<String>> = if profile.tools.is_empty() {
        None
    } else {
        Some(profile.tools.iter().cloned().collect())
    };

    let filter_decls = |decls: Vec<crate::inference::ToolDeclaration>| -> Vec<crate::inference::ToolDeclaration> {
        let Some(ref allow) = allowed_tool_set else {
            return decls;
        };
        decls
            .into_iter()
            .filter(|d| allow.contains(&d.name) || d.name == "complete_task")
            .collect()
    };

    let decls = filter_decls(registry.active_declarations(&sniffed).await);
    let enabled_names: HashSet<String> = decls.iter().map(|d| d.name.clone()).collect();
    let memory = load_hierarchical_memory(&config);
    let episodic_jit = crate::memory::recall_jit(&config, &task, 2, 800);

    let base_sys = crate::cognitive::assemble_system_prompt_with_jit(
        &config,
        &enabled_names,
        &skills,
        &task,
        &memory,
        episodic_jit.as_deref(),
    )
    .await;
    let sys_prompt = format!(
        "{}\n\n# SUBAGENT ROLE: {}\n{}\n\nComplete the assigned task autonomously and return clear empirical evidence.",
        base_sys, profile.name, profile.system_prompt
    );

    let active_model = profile.model.clone().unwrap_or_else(|| config.model.clone());
    let mut router = Formula533Router::build(&config, &registry.router_catalog(), skills);
    let client = ConnectorClient::new(&config);
    let mut history = vec![ChatMessage {
        role: "user".to_string(),
        parts: vec![ContentPart::text(task.clone())],
    }];

    let max_turns = profile
        .max_turns
        .unwrap_or(config.subagent_max_turns)
        .max(1)
        .min(300);
    let mut final_text = String::new();
    let mut tool_calls_count = 0usize;

    for _turn in 0..max_turns {
        {
            let mut pr = proc_reg.lock().await;
            pr.update_subagent_state(&conv_id, "running", &format!("Turn {}/{} active", _turn + 1, max_turns));
        }
        let cur_decls = filter_decls(registry.active_declarations(&sniffed).await);
        let prepared_history = crate::context::prepare_history_for_api(
            &history,
            None,
            false,
            Some(offload_dir.as_path()),
        );
        let (tx, mut rx) = mpsc::unbounded_channel();
        let req_client = client.stream_generate(
            &active_model,
            &sys_prompt,
            &prepared_history,
            &cur_decls,
            tx,
        );

        let mut model_parts = Vec::new();
        let mut pending_calls = Vec::new();
        let mut turn_text = String::new();
        let mut stream_err: Option<String> = None;

        let recv_fut = async {
            while let Some(ev) = rx.recv().await {
                match ev {
                    StreamEvent::TextDelta(t) => turn_text.push_str(&t),
                    StreamEvent::ModelPart(p) => model_parts.push(p),
                    StreamEvent::ToolCall(fc) => pending_calls.push(fc),
                    StreamEvent::Error(e) => stream_err = Some(e),
                    StreamEvent::ThoughtDelta(_) | StreamEvent::Usage(_) | StreamEvent::Finish(_) => {}
                }
            }
        };

        let (gen_res, _) = tokio::join!(req_client, recv_fut);
        if let Err(e) = gen_res {
            let err_msg = format!("Subagent '{}' error: {}", profile.name, e);
            proc_reg.lock().await.complete_subagent(&conv_id, false, &err_msg);
            return ToolExecOutcome::err(err_msg);
        }
        if let Some(e) = stream_err {
            let err_msg = format!("Subagent '{}' stream error: {}", profile.name, e);
            proc_reg.lock().await.complete_subagent(&conv_id, false, &err_msg);
            return ToolExecOutcome::err(err_msg);
        }

        let coalesced_parts = crate::context::coalesce_parts(model_parts);
        if !coalesced_parts.is_empty() {
            history.push(ChatMessage {
                role: "model".to_string(),
                parts: coalesced_parts,
            });
        }

        if pending_calls.is_empty() {
            final_text = turn_text;
            break;
        }

        let mut response_parts = Vec::new();
        let mut needs_rescan = false;
        let mut completed_via_tool = false;
        for fc in pending_calls {
            tool_calls_count += 1;
            if let Some(ref allow) = allowed_tool_set {
                if !allow.contains(&fc.name) && fc.name != "complete_task" {
                    response_parts.push(ContentPart::function_response(
                        &fc.id,
                        &fc.name,
                        json!({ "error": format!("Tool '{}' is not permitted for subagent '{}'.", fc.name, profile.name) }),
                    ));
                    continue;
                }
            }
            let mut resp_val: Value = match ToolRegistry::validate_intercept_gate(&fc.args) {
                Err(e) => json!({ "error": e }),
                Ok((reason, keywords, goal)) => {
                    let is_mcp = registry.mcp.is_mcp_tool(&fc.name).is_some();
                    let mcp_srv = registry.mcp.is_mcp_tool(&fc.name);
                    let pol = policy.evaluate_with_subagent(
                        &config,
                        &fc.name,
                        &fc.args,
                        is_mcp,
                        mcp_srv,
                        Some(&profile.name),
                    );
                    if pol.decision != PolicyDecision::Allow {
                        let default_msg = if pol.decision == PolicyDecision::AskUser {
                            "Requires interactive user approval (unavailable inside autonomous subagent)."
                        } else {
                            "Denied by policy."
                        };
                        json!({ "error": pol.reason.unwrap_or_else(|| default_msg.to_string()) })
                    } else {
                        let out = registry.execute_with_id(&fc.id, &fc.name, &fc.args).await;
                        if out.needs_tool_rescan {
                            needs_rescan = true;
                        }
                        if fc.name == "complete_task" && out.success {
                            completed_via_tool = true;
                            if let Some(val) = fc.args.get("result").or_else(|| fc.args.get("summary")) {
                                if let Some(txt) = val.as_str() {
                                    if !txt.trim().is_empty() {
                                        final_text = txt.to_string();
                                    }
                                } else if !val.is_null() {
                                    final_text = val.to_string();
                                }
                            }
                        }
                        let activated_sk = if fc.name == "activate_skill" && out.success {
                            out.output_json
                                .get("skill")
                                .and_then(|s| s.as_str())
                                .or_else(|| fc.args.get("name").and_then(|s| s.as_str()))
                        } else {
                            None
                        };
                        router.record_activation(&fc.name, activated_sk);
                        let route_inj = router.route(&keywords, &goal, &reason);
                        let mut val = out.output_json;
                        if !route_inj.is_empty() {
                            if let Some(obj) = val.as_object_mut() {
                                obj.insert("_flowork_router_guidance".to_string(), json!(route_inj));
                            }
                        }
                        val
                    }
                }
            };
            if resp_val.is_null() {
                resp_val = json!({ "status": "ok" });
            }
            response_parts.push(ContentPart::function_response(&fc.id, &fc.name, resp_val));
        }
        if needs_rescan {
            registry.rescan_disk_manifests_blocking();
        }
        history.push(ChatMessage {
            role: "user".to_string(),
            parts: response_parts,
        });
        if completed_via_tool {
            break;
        }
    }
    if final_text.is_empty() {
        final_text = format!(
            "Subagent '{}' finished after {} tool calls without trailing summary text.",
            profile.name, tool_calls_count
        );
    }

    let summary_with_ws = if let Some(ref bdir) = branch_dir {
        format!("Workspace: branched ({})\n\n{}", bdir.display(), final_text)
    } else {
        final_text
    };

    proc_reg.lock().await.complete_subagent(&conv_id, true, "Completed");

    ToolExecOutcome::ok_json(
        json!({
            "status": "completed",
            "agent_name": profile.name,
            "workspace": if is_branch { "branch" } else { "inherit" },
            "branch_dir": branch_dir.map(|p| p.to_string_lossy().to_string()),
            "model": active_model,
            "tool_calls": tool_calls_count,
            "report": summary_with_ws
        }),
        summary_with_ws,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_agent_yaml_frontmatter_tools_model_and_max_turns() {
        let md = r#"---
name: security_auditor
display_name: Security Auditor
description: Audits security posture
model: gemini-3.1-pro
max_turns: 45
tools:
  - read_file
  - grep_search
---
Inspect all routes carefully."#;
        let parsed = parse_agent_markdown("fallback", md, PathBuf::from("/tmp/sec.md"));
        assert_eq!(parsed.name, "security_auditor");
        assert_eq!(parsed.display_name.as_deref(), Some("Security Auditor"));
        assert_eq!(parsed.model.as_deref(), Some("gemini-3.1-pro"));
        assert_eq!(parsed.max_turns, Some(45));
        assert_eq!(parsed.tools, vec!["read_file", "grep_search"]);
        assert_eq!(parsed.system_prompt, "Inspect all routes carefully.");
    }

    #[test]
    fn extracts_result_over_summary_in_complete_task() {
        let args_result = json!({ "result": "Detailed audit found 0 flaws" });
        let val = args_result.get("result").or_else(|| args_result.get("summary"));
        assert_eq!(val.and_then(|v| v.as_str()), Some("Detailed audit found 0 flaws"));

        let args_summary = json!({ "summary": "Legacy fallback" });
        let val2 = args_summary.get("result").or_else(|| args_summary.get("summary"));
        assert_eq!(val2.and_then(|v| v.as_str()), Some("Legacy fallback"));
    }
}
