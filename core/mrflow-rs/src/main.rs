mod agents;
mod cli;
mod cognitive;
mod config;
mod context;
mod engine;
mod inference;
mod mcp;
mod memory;
mod output;
mod policy;
mod session;
mod tools;
mod tui;

use clap::Parser;
use cli::{Cli, OutputFormatArg};
use config::{AppConfig, CliOverrides};
use engine::{
    handle_session_management_flags, handle_subcommand, list_extensions_summary, run_acp_mode,
    run_headless,
};
use std::io::{self, IsTerminal, Read};
use std::process::ExitCode;

#[tokio::main]
async fn main() -> ExitCode {
    let parsed = Cli::parse();

    let output_format = parsed.output_format.map(|o| match o {
        OutputFormatArg::Text => "text".to_string(),
        OutputFormatArg::Json => "json".to_string(),
        OutputFormatArg::StreamJson => "stream-json".to_string(),
    });

    // Determine interactive vs headless:
    // `-p/--prompt` or `--acp` runs headless/protocol; interactive otherwise unless piped without `-i`.
    let has_piped_stdin = !io::stdin().is_terminal();
    let is_acp = parsed.acp || parsed.experimental_acp;
    let is_headless_prompt = parsed.prompt.is_some() || (!is_acp && has_piped_stdin && parsed.prompt_interactive.is_none() && parsed.command.is_none() && !parsed.list_sessions && !parsed.list_extensions && parsed.delete_session.is_none());
    let interactive = !is_headless_prompt && !is_acp;

    let overrides = CliOverrides {
        model: parsed.model.clone(),
        sovereign: parsed.sovereign,
        approval_mode: parsed.approval_mode.clone(),
        interactive,
        debug: parsed.debug,
        sandbox: parsed.sandbox,
        skip_trust: parsed.skip_trust,
        raw_output: parsed.raw_output,
        accept_raw_output_risk: parsed.accept_raw_output_risk,
        screen_reader: parsed.screen_reader,
        output_format,
        include_directories: parsed.include_directories.clone(),
        policy: parsed.policy.clone(),
        admin_policy: parsed.admin_policy.clone(),
        allowed_mcp_server_names: parsed.allowed_mcp_server_names.clone(),
        allowed_tools: parsed.allowed_tools.clone(),
        extensions: parsed.extensions.clone(),
        session_id: parsed.session_id.clone(),
        resume: parsed.resume.clone(),
        session_file: parsed.session_file.clone(),
    };

    let cfg = AppConfig::build(overrides);

    if let Some(subcmd) = parsed.command {
        let code = handle_subcommand(&cfg, subcmd);
        return ExitCode::from(code as u8);
    }

    if parsed.list_extensions {
        list_extensions_summary(&cfg);
        return ExitCode::SUCCESS;
    }

    if parsed.router_audit {
        let code = engine::run_router_audit(cfg);
        return ExitCode::from(code as u8);
    }

    if let Some(ref route_prompt) = parsed.dry_run_route {
        let code = engine::run_dry_run_route(cfg, route_prompt.clone()).await;
        return ExitCode::from(code as u8);
    }

    if let Some(code) = handle_session_management_flags(
        &cfg,
        parsed.list_sessions,
        parsed.delete_session.as_deref(),
    ) {
        return ExitCode::from(code as u8);
    }

    if is_acp {
        let code = run_acp_mode(cfg).await;
        return ExitCode::from(code as u8);
    }

    // Read piped stdin if any (appended/prefixed cleanly for `-p`)
    let mut stdin_buf = String::new();
    if has_piped_stdin {
        let _ = io::stdin().read_to_string(&mut stdin_buf);
    }
    let stdin_trimmed = stdin_buf.trim();

    if let Some(ref p) = parsed.prompt {
        let full_prompt = if stdin_trimmed.is_empty() {
            p.clone()
        } else if p.trim().is_empty() {
            stdin_trimmed.to_string()
        } else {
            format!("{}\n\n{}", p, stdin_trimmed)
        };
        let code = run_headless(cfg, full_prompt).await;
        return ExitCode::from(code as u8);
    }

    if is_headless_prompt {
        let positional = parsed.query.join(" ");
        let full_prompt = match (positional.trim().is_empty(), stdin_trimmed.is_empty()) {
            (false, false) => format!("{}\n\n{}", positional, stdin_trimmed),
            (false, true) => positional,
            (true, false) => stdin_trimmed.to_string(),
            (true, true) => String::new(),
        };
        if full_prompt.is_empty() {
            eprintln!("Error: No prompt provided via -p or stdin.");
            return ExitCode::from(1);
        }
        let code = run_headless(cfg, full_prompt).await;
        return ExitCode::from(code as u8);
    }

    // Interactive TUI entrypoint (Phase 6 Sovereign Glass HUD)
    let initial_prompt = parsed
        .prompt_interactive
        .or_else(|| {
            let q = parsed.query.join(" ");
            (!q.trim().is_empty()).then_some(q)
        });

    let code = tui::run_interactive_hud(cfg, initial_prompt).await;
    ExitCode::from(code as u8)
}
