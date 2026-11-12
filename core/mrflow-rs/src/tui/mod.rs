use crate::cognitive::{discover_skills, format_skill_list_summary};
use crate::config::{AppConfig, ApprovalMode};
use crate::engine::{list_agent_profiles_summary, SovereignEngine, UiUpdate};
use crate::inference::TokenUsage;
use crate::memory::load_hierarchical_memory;
use crate::session::list_sessions;
use crate::tools::{AskUserFuture, InteractiveUiBridge};
use crossterm::event::{self, Event, KeyCode, KeyEvent, KeyModifiers};
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
};
use crossterm::ExecutableCommand;
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, List, ListItem, Paragraph, Wrap};
use ratatui::Terminal;
use serde_json::{json, Value};
use std::fs;
use std::io::{self, Write};
use std::path::PathBuf;
use std::process::Command as StdCommand;
use std::sync::atomic::Ordering;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{mpsc, oneshot};

const LIGHTNING_GLYPH: [&str; 4] = [
    "    ▄█  ",
    "  ▟██▀  ",
    "   ▀███▖",
    "     ▀▀ ",
];

const MRFLOW_BANNER: [&str; 4] = [
    "▜██▖▟██▘ ▜███▛▜▙  ▜█████ ▜█▘   ▗█▀▀█▖ ▜█▘  ▜█▘",
    "▐█▝█▛▐█  ▐█  █▛   ▐█▀▀▀  ▐█    ▐█  █▌ ▐█ ▐▌ █▌",
    "▐█   ▐█  ▐█ ▝█▙   ▐█     ▐█ ▗▌ ▐█  █▌ ▐█▝██▘█▌",
    "▀▀▘  ▀▀▘ ▀▀▘ ▀▀▘  ▀▀▘    ▀▀▀▀▘ ▝▀▀▀▀▘ ▝▀▀▘▀▀▘",
];

const BUILTIN_COMMANDS: &[(&str, &str)] = &[
    ("/help", "Show Sovereign HUD commands and shortcuts"),
    ("/about", "Show Mr. Flow v2.0 Clean-Room Rust build info"),
    ("/agents", "List discovered specialist subagents"),
    ("/auth", "Inspect Flowork Connector (:9099) authentication & pool status"),
    ("/bug", "Print environment diagnostic report"),
    ("/chat", "Checkpoint session: /chat save|resume|list <tag>"),
    ("/clear", "Clear display conversation buffer"),
    ("/commands", "List slash commands and skill commands"),
    ("/compress", "Compact older context turns via 2-pass <state_snapshot>"),
    ("/copy", "Copy latest assistant response to system clipboard"),
    ("/directory", "Manage workspace directories: /directory add|show <path>"),
    ("/docs", "Show local Flowork OS architecture documentation"),
    ("/editor", "Compose multiline prompt in external $EDITOR"),
    ("/export", "Export current conversation to markdown file"),
    ("/extensions", "List installed extensions"),
    ("/footer", "Toggle detailed vs compact status footer"),
    ("/gemma", "Inspect local SLM / Ollama model pool"),
    ("/hooks", "Show ~/.flowork/hooks configuration"),
    ("/ide", "Show IDE & terminal integration status"),
    ("/init", "Initialize starter FLOWORK.md in current directory"),
    ("/mcp", "List connected MCP servers, tools, resources & prompts"),
    ("/memory", "Manage FLOWORK.md context: /memory show|refresh"),
    ("/model", "Switch active model (e.g. /model deepseek-v4-9b-uncensored)"),
    ("/permissions", "Display active 5-tier policy evaluation summary"),
    ("/plan", "Toggle Plan Mode (read-only planning workflow)"),
    ("/policies", "List active .toml policy files"),
    ("/privacy", "Display Sovereign local privacy & storage info"),
    ("/quit", "Cleanly shut down MCP servers and exit"),
    ("/exit", "Alias for /quit"),
    ("/restore", "Restore latest session checkpoint"),
    ("/resume", "Resume session: /resume <idx|uuid> or list sessions"),
    ("/rewind", "Drop last turn from active context"),
    ("/settings", "Show ~/.flowork/settings.json summary"),
    ("/shortcuts", "Show keyboard navigation shortcuts"),
    ("/skills", "List discovered Sovereign Skills (use /<skill-name> to invoke)"),
    ("/stats", "Show cumulative session token & tool statistics"),
    ("/tasks", "List running background shell processes"),
    ("/theme", "Cycle HUD accent color theme"),
    ("/tools", "List currently active dynamically sniffed tools"),
    ("/vim", "Toggle Vim input indicator"),
    ("/voice", "Check Earshot audio/voice synthesis status"),
];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum HudTheme {
    SovereignMatrix,
    SovereignCyan,
    AmberTerminal,
}

impl HudTheme {
    fn next(self) -> Self {
        match self {
            Self::SovereignMatrix => Self::SovereignCyan,
            Self::SovereignCyan => Self::AmberTerminal,
            Self::AmberTerminal => Self::SovereignMatrix,
        }
    }

    fn name(self) -> &'static str {
        match self {
            Self::SovereignMatrix => "Sovereign Matrix",
            Self::SovereignCyan => "Sovereign Cyan",
            Self::AmberTerminal => "Amber Phosphor",
        }
    }

    fn primary(self) -> Color {
        match self {
            Self::SovereignMatrix => Color::Rgb(0, 255, 102),
            Self::SovereignCyan => Color::Rgb(0, 255, 255),
            Self::AmberTerminal => Color::Rgb(255, 176, 0),
        }
    }

    fn secondary(self) -> Color {
        match self {
            Self::SovereignMatrix => Color::Rgb(0, 255, 255),
            Self::SovereignCyan => Color::Rgb(0, 255, 102),
            Self::AmberTerminal => Color::Rgb(255, 220, 110),
        }
    }
}

#[derive(Debug, Clone)]
enum TranscriptEntry {
    User(String),
    Assistant {
        text: String,
        thoughts: String,
    },
    ToolCard {
        id: String,
        name: String,
        args_summary: String,
        status: String, // "running" | "success" | "error"
        output: String,
    },
    System(String),
    Error(String),
}

struct ModalPromptRequest {
    questions: Value,
    reply_tx: oneshot::Sender<Result<Value, String>>,
}

struct TuiUiBridge {
    modal_tx: mpsc::UnboundedSender<ModalPromptRequest>,
}

impl InteractiveUiBridge for TuiUiBridge {
    fn ask_user(&self, questions: Value) -> AskUserFuture {
        let tx = self.modal_tx.clone();
        Box::pin(async move {
            let (reply_tx, reply_rx) = oneshot::channel();
            tx.send(ModalPromptRequest { questions, reply_tx })
                .map_err(|_| "TUI modal closed".to_string())?;
            reply_rx
                .await
                .unwrap_or_else(|_| Err("TUI modal cancelled".to_string()))
        })
    }

    fn request_plan_mode(&self, _enter: bool, _reason: String) -> AskUserFuture {
        Box::pin(async move { Ok(json!({ "approved": true })) })
    }
}

struct ActiveModal {
    question_text: String,
    options: Vec<String>,
    selected_idx: usize,
    custom_input: String,
    typing_custom: bool,
    reply_tx: Option<oneshot::Sender<Result<Value, String>>>,
}

struct RawTerminalGuard;
impl Drop for RawTerminalGuard {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let _ = io::stdout().execute(LeaveAlternateScreen);
    }
}

pub async fn run_interactive_hud(
    config: AppConfig,
    initial_prompt: Option<String>,
) -> i32 {
    let (modal_tx, mut modal_rx) = mpsc::unbounded_channel::<ModalPromptRequest>();
    let bridge: Arc<dyn InteractiveUiBridge> = Arc::new(TuiUiBridge { modal_tx });

    let engine = match SovereignEngine::initialize(config.clone(), Some(bridge)).await {
        Ok(e) => Arc::new(e),
        Err(err) => {
            eprintln!("Failed initializing Mr. Flow engine: {}", err);
            return 1;
        }
    };

    // Enter Raw Mode + Alternate Screen safely
    if enable_raw_mode().is_err() {
        eprintln!("Failed enabling terminal raw mode.");
        engine.shutdown().await;
        return 1;
    }
    if io::stdout().execute(EnterAlternateScreen).is_err() {
        let _ = disable_raw_mode();
        engine.shutdown().await;
        return 1;
    }
    let _guard = RawTerminalGuard;

    let backend = CrosstermBackend::new(io::stdout());
    let Ok(mut terminal) = Terminal::new(backend) else {
        engine.shutdown().await;
        return 1;
    };

    let (ui_tx, mut ui_rx) = mpsc::unbounded_channel::<UiUpdate>();
    let skills = discover_skills(&config);
    let mut cmd_candidates: Vec<(String, String)> = BUILTIN_COMMANDS
        .iter()
        .map(|(k, d)| (k.to_string(), d.to_string()))
        .collect();
    for sk in &skills {
        cmd_candidates.push((format!("/{}", sk.name), format!("[Skill] {}", sk.description)));
    }

    let mut entries: Vec<TranscriptEntry> = Vec::new();
    let mut input_buf = String::new();
    let mut input_history: Vec<String> = Vec::new();
    let mut hist_cursor: Option<usize> = None;
    let mut scroll_offset_from_bottom: u16 = 0;
    let mut show_details = false;
    let mut compact_footer = false;
    let mut vim_mode = false;
    let mut theme = HudTheme::SovereignMatrix;
    let mut running_turn = false;
    let mut current_turn_num = 0usize;
    let mut max_turns = config.max_turns;
    let mut latest_tokens = TokenUsage::default();
    let mut context_tokens: u64 = *engine.last_prompt_tokens.lock().await;
    let mut current_mode = config.approval_mode;
    let mut active_model = config.model.clone();
    let mut session_id = engine.vault.lock().await.session_id.clone();
    let mut spin_tick = 0usize;
    let mut turn_started_at = Instant::now();
    let mut active_task_handle: Option<tokio::task::JoinHandle<()>> = None;
    let mut active_modal: Option<ActiveModal> = None;
    let mut popup_selected = 0usize;
    let mut ctrl_c_armed_at: Option<Instant> = None;

    // If -i / positional initial query provided, dispatch automatically
    if let Some(p) = initial_prompt {
        let trimmed = p.trim().to_string();
        if !trimmed.is_empty() {
            entries.push(TranscriptEntry::User(trimmed.clone()));
            input_history.push(trimmed.clone());
            running_turn = true;
            turn_started_at = Instant::now();
            let eng = Arc::clone(&engine);
            let tx_c = ui_tx.clone();
            active_task_handle = Some(tokio::spawn(async move {
                let _ = eng.run_prompt_turn(&trimmed, Some(tx_c)).await;
            }));
        }
    }

    loop {
        spin_tick = spin_tick.wrapping_add(1);

        // Drain UI updates non-blocking
        while let Ok(upd) = ui_rx.try_recv() {
            match upd {
                UiUpdate::SessionInit {
                    session_id: sid,
                    model,
                } => {
                    session_id = sid;
                    active_model = model;
                }
                UiUpdate::ThoughtDelta(th) => {
                    if let Some(TranscriptEntry::Assistant { thoughts, .. }) = entries.last_mut() {
                        thoughts.push_str(&th);
                    } else {
                        entries.push(TranscriptEntry::Assistant {
                            text: String::new(),
                            thoughts: th,
                        });
                    }
                    scroll_offset_from_bottom = 0;
                }
                UiUpdate::TextDelta(txt) => {
                    if let Some(TranscriptEntry::Assistant { text, .. }) = entries.last_mut() {
                        text.push_str(&txt);
                    } else {
                        entries.push(TranscriptEntry::Assistant {
                            text: txt,
                            thoughts: String::new(),
                        });
                    }
                    scroll_offset_from_bottom = 0;
                }
                UiUpdate::ToolUse { id, name, args } => {
                    let args_summary = summarize_args(&args);
                    entries.push(TranscriptEntry::ToolCard {
                        id,
                        name,
                        args_summary,
                        status: "running".to_string(),
                        output: String::new(),
                    });
                    scroll_offset_from_bottom = 0;
                }
                UiUpdate::ToolResult {
                    id,
                    name: _,
                    success,
                    output,
                } => {
                    for ent in entries.iter_mut().rev() {
                        if let TranscriptEntry::ToolCard {
                            id: cid,
                            status,
                            output: cout,
                            ..
                        } = ent
                        {
                            if *cid == id {
                                *status = if success { "success" } else { "error" }.to_string();
                                *cout = output;
                                break;
                            }
                        }
                    }
                    scroll_offset_from_bottom = 0;
                }
                UiUpdate::StatsUpdate {
                    turn,
                    max_turns: mt,
                    tokens,
                    mode,
                    context_tokens: ctx_tok,
                } => {
                    current_turn_num = turn;
                    max_turns = mt;
                    latest_tokens = tokens;
                    current_mode = mode;
                    context_tokens = ctx_tok;
                }
                UiUpdate::SystemNotice(msg) => {
                    entries.push(TranscriptEntry::System(msg));
                    scroll_offset_from_bottom = 0;
                }
                UiUpdate::Error(e) => {
                    entries.push(TranscriptEntry::Error(e));
                    running_turn = false;
                }
                UiUpdate::Finished { tokens, .. } => {
                    latest_tokens = tokens;
                    running_turn = false;
                }
            }
        }

        if running_turn {
            if let Some(ref handle) = active_task_handle {
                if handle.is_finished() {
                    running_turn = false;
                    active_task_handle = None;
                }
            }
        }

        // Check modal requests from engine
        if active_modal.is_none() {
            if let Ok(req) = modal_rx.try_recv() {
                let first_q = req
                    .questions
                    .as_array()
                    .and_then(|a| a.first())
                    .cloned()
                    .unwrap_or_else(|| json!({ "question": "Confirm action?" }));
                let qtext = first_q
                    .get("question")
                    .and_then(|s| s.as_str())
                    .unwrap_or("Confirm action?")
                    .to_string();
                let mut opts: Vec<String> = first_q
                    .get("options")
                    .and_then(|o| o.as_array())
                    .map(|arr| {
                        arr.iter()
                            .filter_map(|v| v.as_str().map(str::to_string))
                            .collect()
                    })
                    .unwrap_or_default();
                if opts.is_empty() {
                    opts = vec!["Allow / Yes".to_string(), "Deny / No".to_string()];
                }
                opts.push("Custom write-in...".to_string());
                active_modal = Some(ActiveModal {
                    question_text: qtext,
                    options: opts,
                    selected_idx: 0,
                    custom_input: String::new(),
                    typing_custom: false,
                    reply_tx: Some(req.reply_tx),
                });
            }
        }

        // Build autocomplete matches if input starts with / or contains @
        let popup_items = compute_autocomplete_items(&input_buf, &cmd_candidates, &config.cwd);
        if !popup_items.is_empty() && popup_selected >= popup_items.len() {
            popup_selected = popup_items.len() - 1;
        }

        // Render Sovereign Glass HUD frame
        let draw_res = terminal.draw(|f| {
            let area = f.area();
            let input_height = (input_buf.lines().count().max(1) as u16 + 2).min(7);
            let footer_height = if compact_footer { 1 } else { 2 };
            let banner_height = if area.height >= 16 { 6 } else { 2 };

            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(banner_height),
                    Constraint::Min(4),
                    Constraint::Length(input_height),
                    Constraint::Length(footer_height),
                ])
                .split(area);

            // 1. Header / Lightning Glyph + MRFLOW Banner
            render_banner(f, chunks[0], theme, &active_model, current_mode, &session_id);

            // 2. Scrollable Transcript Canvas
            render_transcript(
                f,
                chunks[1],
                &entries,
                theme,
                show_details,
                running_turn,
                spin_tick,
                turn_started_at.elapsed().as_secs(),
                scroll_offset_from_bottom,
            );

            // 3. Sovereign Prompt Input Box
            let border_color = match current_mode {
                ApprovalMode::Sovereign => theme.primary(),
                ApprovalMode::Plan => Color::Rgb(255, 176, 0),
                ApprovalMode::AutoEdit => theme.secondary(),
                ApprovalMode::Default => Color::Rgb(160, 170, 185),
            };
            let title_tag = if running_turn {
                " ❯ Streaming... (Ctrl+C to stop) "
            } else if vim_mode {
                " ❯ Prompt [VIM] (Enter send | Shift+Tab mode | !shell | /help) "
            } else {
                " ❯ Prompt (Enter send | Shift+Enter newline | Shift+Tab mode | /help) "
            };
            let input_block = Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(border_color).bg(Color::Reset))
                .title(Span::styled(
                    title_tag,
                    Style::default().fg(border_color).add_modifier(Modifier::BOLD),
                ))
                .style(Style::default().bg(Color::Reset));
            let prompt_para = Paragraph::new(format!("› {}", input_buf))
                .block(input_block)
                .style(Style::default().fg(Color::Rgb(255, 255, 255)).bg(Color::Reset))
                .wrap(Wrap { trim: false });
            f.render_widget(prompt_para, chunks[2]);

            // 4. Footer HUD
            render_footer(
                f,
                chunks[3],
                theme,
                &config.cwd,
                &config.paths.flowork_root,
                current_mode,
                &active_model,
                current_turn_num,
                max_turns,
                context_tokens,
                &latest_tokens,
                compact_footer,
            );

            // 5. Autocomplete popup above input box
            if !popup_items.is_empty() && active_modal.is_none() && !running_turn {
                let h = (popup_items.len().min(8) as u16) + 2;
                let w = chunks[2].width.min(78);
                let y = chunks[2].y.saturating_sub(h);
                let pop_rect = Rect::new(chunks[2].x + 1, y, w.saturating_sub(2), h);
                f.render_widget(Clear, pop_rect);
                let items: Vec<ListItem> = popup_items
                    .iter()
                    .take(8)
                    .enumerate()
                    .map(|(i, (label, desc))| {
                        let sel = i == popup_selected;
                        let st = if sel {
                            Style::default()
                                .fg(Color::Rgb(0, 0, 0))
                                .bg(theme.primary())
                                .add_modifier(Modifier::BOLD)
                        } else {
                            Style::default().fg(Color::Rgb(235, 240, 245)).bg(Color::Reset)
                        };
                        ListItem::new(Line::from(vec![
                            Span::styled(format!(" {} ", label), st),
                            Span::styled(
                                format!(" {}", desc.chars().take(48).collect::<String>()),
                                Style::default().fg(Color::Rgb(255, 255, 255)),
                            ),
                        ]))
                    })
                    .collect();
                let list = List::new(items).block(
                    Block::default()
                        .borders(Borders::ALL)
                        .border_style(Style::default().fg(theme.secondary()))
                        .title(" Autocomplete (Tab/Enter) "),
                );
                f.render_widget(list, pop_rect);
            }

            // 6. Interactive Modal Dialog (`ask_user` / confirmation)
            if let Some(ref m) = active_modal {
                render_modal(f, area, m, theme);
            }
        });
        if draw_res.is_err() {
            break;
        }

        // Poll crossterm events cleanly (35ms cadence, draining queued fast input/paste in one frame)
        let mut quit_requested = false;
        let mut poll_timeout = Duration::from_millis(35);
        for _ in 0..64 {
            if !event::poll(poll_timeout).unwrap_or(false) {
                break;
            }
            poll_timeout = Duration::ZERO;
            if let Ok(Event::Key(key)) = event::read() {
                if let Some(ref mut modal) = active_modal {
                    if handle_modal_key(key, modal) {
                        active_modal = None;
                    }
                    continue;
                }

                let cur_popup = compute_autocomplete_items(&input_buf, &cmd_candidates, &config.cwd);
                if !cur_popup.is_empty() && popup_selected >= cur_popup.len() {
                    popup_selected = cur_popup.len() - 1;
                }

                match (key.code, key.modifiers) {
                    (KeyCode::Char('c'), KeyModifiers::CONTROL) => {
                        if running_turn {
                            engine.abort_flag.store(true, Ordering::SeqCst);
                            engine.proc_reg.lock().await.kill_all_active();
                            if let Some(h) = active_task_handle.take() {
                                h.abort();
                            }
                            running_turn = false;
                            entries.push(TranscriptEntry::System(
                                "⏹ Turn interrupted by Ctrl+C (PGIDs terminated cleanly).".to_string(),
                            ));
                        } else if !input_buf.is_empty() {
                            input_buf.clear();
                            popup_selected = 0;
                            ctrl_c_armed_at = None;
                        } else if ctrl_c_armed_at
                            .map(|t| t.elapsed() < Duration::from_secs(2))
                            .unwrap_or(false)
                        {
                            quit_requested = true;
                            break;
                        } else {
                            ctrl_c_armed_at = Some(Instant::now());
                            entries.push(TranscriptEntry::System(
                                "Press Ctrl+C again within 2s (or type /quit) to exit Mr. Flow.".to_string(),
                            ));
                        }
                    }
                    (KeyCode::Char('d'), KeyModifiers::CONTROL) if input_buf.is_empty() => {
                        quit_requested = true;
                        break;
                    }
                    (KeyCode::Char('o'), KeyModifiers::CONTROL) | (KeyCode::F(2), _) => {
                        show_details = !show_details;
                    }
                    (KeyCode::BackTab, _) => {
                        current_mode = current_mode.cycle_next();
                        engine.config.lock().await.approval_mode = current_mode;
                        entries.push(TranscriptEntry::System(format!(
                            "Approval mode switched -> {}",
                            current_mode.display_label()
                        )));
                    }
                    (KeyCode::PageUp, _) => {
                        scroll_offset_from_bottom = scroll_offset_from_bottom.saturating_add(6);
                    }
                    (KeyCode::PageDown, _) => {
                        scroll_offset_from_bottom = scroll_offset_from_bottom.saturating_sub(6);
                    }
                    (KeyCode::Tab, _) if !cur_popup.is_empty() && !running_turn => {
                        let chosen = &cur_popup[popup_selected].0;
                        apply_autocomplete(&mut input_buf, chosen);
                        popup_selected = 0;
                    }
                    (KeyCode::Up, _) if !cur_popup.is_empty() && !running_turn => {
                        popup_selected = popup_selected.saturating_sub(1);
                    }
                    (KeyCode::Down, _) if !cur_popup.is_empty() && !running_turn => {
                        if popup_selected + 1 < cur_popup.len() {
                            popup_selected += 1;
                        }
                    }
                    (KeyCode::Up, _) if !input_history.is_empty() && cur_popup.is_empty() => {
                        let next_idx = match hist_cursor {
                            None => input_history.len() - 1,
                            Some(i) => i.saturating_sub(1),
                        };
                        hist_cursor = Some(next_idx);
                        input_buf = input_history[next_idx].clone();
                    }
                    (KeyCode::Down, _) if hist_cursor.is_some() && cur_popup.is_empty() => {
                        let idx = hist_cursor.unwrap();
                        if idx + 1 < input_history.len() {
                            hist_cursor = Some(idx + 1);
                            input_buf = input_history[idx + 1].clone();
                        } else {
                            hist_cursor = None;
                            input_buf.clear();
                        }
                    }
                    (KeyCode::Enter, mods)
                        if mods.contains(KeyModifiers::SHIFT)
                            || mods.contains(KeyModifiers::ALT) =>
                    {
                        input_buf.push('\n');
                    }
                    (KeyCode::Char('j'), KeyModifiers::CONTROL) => {
                        input_buf.push('\n');
                    }
                    (KeyCode::Enter, _) => {
                        if !cur_popup.is_empty() && input_buf.starts_with('/') && !input_buf.contains(' ') {
                            let chosen = cur_popup[popup_selected].0.clone();
                            input_buf = chosen;
                        }
                        let raw = input_buf.trim().to_string();
                        if raw.is_empty() || running_turn {
                            continue;
                        }
                        input_buf.clear();
                        popup_selected = 0;
                        hist_cursor = None;
                        ctrl_c_armed_at = None;
                        input_history.push(raw.clone());

                        if let Some(shell_cmd) = raw.strip_prefix('!') {
                            let cmd = shell_cmd.trim();
                            entries.push(TranscriptEntry::User(format!("!{}", cmd)));
                            if !cmd.is_empty() {
                                let out = run_direct_shell(&config.cwd, cmd);
                                entries.push(TranscriptEntry::System(out));
                            }
                            scroll_offset_from_bottom = 0;
                            continue;
                        }

                        if raw.starts_with('/') {
                            let should_quit = handle_slash_command(
                                &raw,
                                &engine,
                                &mut entries,
                                &mut active_model,
                                &mut current_mode,
                                &mut session_id,
                                &mut context_tokens,
                                &mut compact_footer,
                                &mut vim_mode,
                                &mut theme,
                                &mut running_turn,
                                &mut turn_started_at,
                                &mut active_task_handle,
                                &ui_tx,
                                &mut input_buf,
                            )
                            .await;
                            if should_quit {
                                quit_requested = true;
                                break;
                            }
                            scroll_offset_from_bottom = 0;
                            continue;
                        }

                        entries.push(TranscriptEntry::User(raw.clone()));
                        running_turn = true;
                        turn_started_at = Instant::now();
                        scroll_offset_from_bottom = 0;
                        let eng = Arc::clone(&engine);
                        let tx_c = ui_tx.clone();
                        active_task_handle = Some(tokio::spawn(async move {
                            let _ = eng.run_prompt_turn(&raw, Some(tx_c)).await;
                        }));
                    }
                    (KeyCode::Backspace, _) => {
                        input_buf.pop();
                        popup_selected = 0;
                    }
                    (KeyCode::Esc, _) => {
                        if running_turn {
                            engine.abort_flag.store(true, Ordering::SeqCst);
                            engine.proc_reg.lock().await.kill_all_active();
                            if let Some(h) = active_task_handle.take() {
                                h.abort();
                            }
                            running_turn = false;
                            entries.push(TranscriptEntry::System("⏹ Stopped by Esc.".to_string()));
                        } else {
                            input_buf.clear();
                            popup_selected = 0;
                        }
                    }
                    (KeyCode::Char(c), mods)
                        if !mods.contains(KeyModifiers::CONTROL) && !mods.contains(KeyModifiers::ALT) =>
                    {
                        input_buf.push(c);
                        popup_selected = 0;
                    }
                    _ => {}
                }
            }
        }
        if quit_requested {
            break;
        }
    }

    if let Some(h) = active_task_handle.take() {
        h.abort();
    }
    engine.shutdown().await;
    0
}

#[allow(clippy::too_many_arguments)]
async fn handle_slash_command(
    raw: &str,
    engine: &Arc<SovereignEngine>,
    entries: &mut Vec<TranscriptEntry>,
    active_model: &mut String,
    current_mode: &mut ApprovalMode,
    session_id: &mut String,
    context_tokens: &mut u64,
    compact_footer: &mut bool,
    vim_mode: &mut bool,
    theme: &mut HudTheme,
    running_turn: &mut bool,
    turn_started_at: &mut Instant,
    active_task_handle: &mut Option<tokio::task::JoinHandle<()>>,
    ui_tx: &mpsc::UnboundedSender<UiUpdate>,
    draft_buf: &mut String,
) -> bool {
    let mut split = raw.splitn(2, char::is_whitespace);
    let cmd = split.next().unwrap_or("").to_ascii_lowercase();
    let arg = split.next().unwrap_or("").trim();
    let cfg = engine.config.lock().await.clone();

    match cmd.as_str() {
        "/quit" | "/exit" => return true,
        "/clear" => {
            entries.clear();
        }
        "/help" => {
            let mut msg = String::from("⚡ Flowork OS Mr. Flow Sovereign Slash Commands:\n");
            for quad in BUILTIN_COMMANDS.chunks(5) {
                let row: Vec<String> = quad.iter().map(|(c, _)| format!("{:<13}", c)).collect();
                msg.push_str(&format!("  {}\n", row.join(" ")));
            }
            msg.push_str("Keys: Shift+Tab=Mode | Ctrl+O=Details | !cmd=Shell | /commands=Descriptions | /<skill>=Run skill");
            entries.push(TranscriptEntry::System(msg));
        }
        "/commands" => {
            let mut msg = String::from("⚡ Mr. Flow Full Command Reference:\n");
            for pair in BUILTIN_COMMANDS.chunks(2) {
                let left = format!("{:<12} {}", pair[0].0, pair[0].1.chars().take(34).collect::<String>());
                if pair.len() == 2 {
                    let right = format!("{:<12} {}", pair[1].0, pair[1].1.chars().take(34).collect::<String>());
                    msg.push_str(&format!("  {:<49} | {}\n", left, right));
                } else {
                    msg.push_str(&format!("  {}\n", left));
                }
            }
            msg.push_str("Tip: Run `/skills` or type `/<skill-name> <goal>` to invoke any Flowork skill.");
            entries.push(TranscriptEntry::System(msg));
        }
        "/about" => {
            entries.push(TranscriptEntry::System(format!(
                "Mr. Flow v2.0.0-sovereign (Clean-Room Native Rust Engine)\nRoot: {}\nModel: {}\nSession: {}",
                cfg.paths.flowork_root.display(),
                active_model,
                session_id
            )));
        }
        "/agents" => {
            entries.push(TranscriptEntry::System(format!(
                "Available Subagents:\n{}",
                list_agent_profiles_summary(&cfg)
            )));
        }
        "/skills" => {
            let skills = discover_skills(&cfg);
            entries.push(TranscriptEntry::System(format!(
                "Discovered {} Sovereign Skills:\n{}\n\nRun `/<skill-name> [task]` to execute with that skill.",
                skills.len(),
                format_skill_list_summary(&skills)
            )));
        }
        "/mcp" => {
            let servers = engine.mcp.server_statuses();
            let resources = engine.mcp.list_resources(None).await;
            let prompts = engine.mcp.list_prompts(None).await;
            let mut msg = format!(
                "MCP Status: {} server(s), {} tool(s), {} resource(s), {} prompt(s)\n",
                servers.len(),
                engine.mcp.tools.len(),
                resources.len(),
                prompts.len()
            );
            for s in servers {
                msg.push_str(&format!(
                    "  [{}] transport={} tools={} {}\n",
                    s.name,
                    s.transport,
                    s.tool_count,
                    if s.trusted { "(trusted)" } else { "" }
                ));
            }
            if !engine.mcp.tools.is_empty() {
                msg.push_str("Tools:\n");
                for t in engine.mcp.tools.iter().take(24) {
                    msg.push_str(&format!("  - {} ({})\n", t.qualified_name, t.server_name));
                }
            }
            if !prompts.is_empty() {
                msg.push_str("Prompts:\n");
                for p in prompts.iter().take(12) {
                    let desc = p.description.as_deref().unwrap_or("");
                    let arg_names: Vec<&str> = p
                        .arguments
                        .iter()
                        .filter_map(|a| a.get("name").and_then(|v| v.as_str()))
                        .collect();
                    let args_str = if arg_names.is_empty() {
                        String::new()
                    } else {
                        format!(" [args: {}]", arg_names.join(", "))
                    };
                    msg.push_str(&format!("  - {}/{}{} {}\n", p.server, p.name, args_str, desc));
                }
            }
            if !resources.is_empty() {
                msg.push_str("Resources:\n");
                for r in resources.iter().take(12) {
                    msg.push_str(&format!("  - [{}] {} ({})\n", r.server, r.name, r.uri));
                }
            }
            entries.push(TranscriptEntry::System(msg.trim_end().to_string()));
        }
        "/tools" => {
            let reg = engine.registry.lock().await;
            let mut names: Vec<String> = reg.manifest_tools.keys().cloned().collect();
            names.sort();
            entries.push(TranscriptEntry::System(format!(
                "Manifest Tools ({}): {}",
                names.len(),
                names.join(", ")
            )));
        }
        "/model" => {
            if arg.is_empty() {
                entries.push(TranscriptEntry::System(format!("Current model: {}. Usage: /model <model-id>", active_model)));
            } else {
                *active_model = arg.to_string();
                engine.config.lock().await.model = arg.to_string();
                entries.push(TranscriptEntry::System(format!("Switched active model -> {}", active_model)));
            }
        }
        "/plan" => {
            let next = if *current_mode == ApprovalMode::Plan {
                ApprovalMode::Sovereign
            } else {
                ApprovalMode::Plan
            };
            *current_mode = next;
            engine.config.lock().await.approval_mode = next;
            entries.push(TranscriptEntry::System(format!("Mode switched -> {}", next.display_label())));
        }
        "/memory" => {
            if arg.starts_with("refresh") {
                let mem = load_hierarchical_memory(&cfg);
                entries.push(TranscriptEntry::System(format!(
                    "Reloaded FLOWORK.md hierarchy ({} chars).",
                    mem.len()
                )));
            } else {
                let mem = load_hierarchical_memory(&cfg);
                entries.push(TranscriptEntry::System(if mem.is_empty() {
                    "No FLOWORK.md or .flowork/MEMORY.md found in hierarchy.".to_string()
                } else {
                    mem.chars().take(4000).collect()
                }));
            }
        }
        "/init" => {
            let target = cfg.cwd.join("FLOWORK.md");
            if target.exists() {
                entries.push(TranscriptEntry::System(format!("FLOWORK.md already exists at {}", target.display())));
            } else {
                let starter = "# Project Instructions (FLOWORK.md)\n\n- Maintain clean architecture and verify changes with tests (Exit Code 0).\n";
                match fs::write(&target, starter) {
                    Ok(()) => entries.push(TranscriptEntry::System(format!("Initialized {}", target.display()))),
                    Err(e) => entries.push(TranscriptEntry::Error(e.to_string())),
                }
            }
        }
        "/chat" => {
            let mut parts = arg.splitn(2, char::is_whitespace);
            let sub = parts.next().unwrap_or("list");
            let tag = parts.next().unwrap_or("checkpoint").trim();
            let v = engine.vault.lock().await;
            let hist = engine.history.lock().await.clone();
            match sub {
                "save" => match v.save_checkpoint(&cfg, tag, &hist) {
                    Ok(p) => entries.push(TranscriptEntry::System(format!("Saved checkpoint -> {}", p.display()))),
                    Err(e) => entries.push(TranscriptEntry::Error(e)),
                },
                "resume" | "restore" => match v.restore_checkpoint(&cfg, tag) {
                    Ok(restored) => {
                        let est = crate::context::estimate_history_tokens(&restored);
                        *engine.history.lock().await = restored;
                        *engine.last_prompt_tokens.lock().await = est;
                        *context_tokens = est;
                        entries.push(TranscriptEntry::System(format!("Restored checkpoint '{}'.", tag)));
                    }
                    Err(e) => entries.push(TranscriptEntry::Error(e)),
                },
                _ => {
                    let list = v.list_checkpoints(&cfg);
                    entries.push(TranscriptEntry::System(if list.is_empty() {
                        "No checkpoints saved yet. Use `/chat save <tag>`.".to_string()
                    } else {
                        format!("Saved checkpoints: {}", list.join(", "))
                    }));
                }
            }
        }
        "/restore" => {
            let v = engine.vault.lock().await;
            let cps = v.list_checkpoints(&cfg);
            if let Some(last) = cps.last() {
                if let Ok(restored) = v.restore_checkpoint(&cfg, last) {
                    let est = crate::context::estimate_history_tokens(&restored);
                    *engine.history.lock().await = restored;
                    *engine.last_prompt_tokens.lock().await = est;
                    *context_tokens = est;
                    entries.push(TranscriptEntry::System(format!("Restored checkpoint '{}'.", last)));
                }
            } else {
                entries.push(TranscriptEntry::System("No checkpoints found to restore.".to_string()));
            }
        }
        "/rewind" => {
            let mut hist = engine.history.lock().await;
            if hist.len() >= 2 {
                hist.pop();
                hist.pop();
                let keep_len = hist.len();
                let est = crate::context::estimate_history_tokens(&hist);
                drop(hist);
                *engine.last_prompt_tokens.lock().await = est;
                *context_tokens = est;
                let _ = engine.vault.lock().await.append_rewind(keep_len);
                entries.push(TranscriptEntry::System(format!(
                    "Rewound last turn (keepCount={}; lossless trail preserved on disk).",
                    keep_len
                )));
            } else {
                entries.push(TranscriptEntry::System("History too short to rewind.".to_string()));
            }
        }
        "/compress" => {
            entries.push(TranscriptEntry::System(
                "⏳ Compressing context history via 2-pass <state_snapshot> refinement...".to_string(),
            ));
            *running_turn = true;
            *turn_started_at = Instant::now();
            let eng = Arc::clone(engine);
            let tx_c = ui_tx.clone();
            *active_task_handle = Some(tokio::spawn(async move {
                match eng.compress_history(true, Some(&tx_c)).await {
                    Ok((false, msg)) => {
                        let _ = tx_c.send(UiUpdate::SystemNotice(msg));
                    }
                    Ok((true, _)) => {}
                    Err(e) => {
                        let _ = tx_c.send(UiUpdate::Error(format!("Compression failed: {}", e)));
                    }
                }
            }));
        }
        "/resume" => {
            let sessions = list_sessions(&cfg);
            if arg.is_empty() {
                let preview: Vec<String> = sessions
                    .iter()
                    .take(10)
                    .map(|s| format!("  [{}] {} | {}", s.index, &s.session_id[..8.min(s.session_id.len())], s.preview))
                    .collect();
                entries.push(TranscriptEntry::System(format!(
                    "Recent sessions (run `mrflow --resume <id>`):\n{}",
                    preview.join("\n")
                )));
            } else {
                entries.push(TranscriptEntry::System(format!("Tip: launch `mrflow --resume {}` to reopen that vault.", arg)));
            }
        }
        "/stats" => {
            let tot = engine.total_tokens.lock().await;
            let limit = crate::context::get_model_token_limit(
                active_model,
                Some(&cfg.paths.flowork_root),
            )
            .max(1);
            let pct = (*context_tokens as f64 / limit as f64) * 100.0;
            entries.push(TranscriptEntry::System(format!(
                "Session Token Statistics:\n  Gateway: {} | Model: {}\n  Active Context: ~{} / {} ({:.1}%)\n  Input: {} | Output: {} | Cached: {} | Thoughts: {} | Total: {}",
                engine.client.base_url(), active_model, *context_tokens, limit, pct, tot.input, tot.output, tot.cached, tot.thoughts, tot.total
            )));
        }
        "/tasks" => {
            let reg = engine.registry.lock().await;
            let res = reg.execute("list_background_processes", &json!({})).await;
            entries.push(TranscriptEntry::System(res.display_text));
        }
        "/copy" => {
            let last_txt = entries
                .iter()
                .rev()
                .find_map(|e| match e {
                    TranscriptEntry::Assistant { text, .. } if !text.is_empty() => Some(text.clone()),
                    _ => None,
                })
                .unwrap_or_default();
            if last_txt.is_empty() {
                entries.push(TranscriptEntry::System("No assistant response to copy yet.".to_string()));
            } else if copy_to_clipboard(&last_txt) {
                entries.push(TranscriptEntry::System(format!("Copied {} chars to clipboard.", last_txt.len())));
            } else {
                entries.push(TranscriptEntry::Error("No clipboard utility (xclip/wl-copy) available.".to_string()));
            }
        }
        "/export" => {
            let out_path = if arg.is_empty() {
                cfg.cwd.join("mrflow_export.md")
            } else {
                PathBuf::from(arg)
            };
            let mut md = format!("# Mr. Flow Session `{}`\n\n", session_id);
            for ent in entries.iter() {
                match ent {
                    TranscriptEntry::User(u) => md.push_str(&format!("## User\n{}\n\n", u)),
                    TranscriptEntry::Assistant { text, .. } => md.push_str(&format!("## Mr. Flow\n{}\n\n", text)),
                    _ => {}
                }
            }
            match fs::write(&out_path, md) {
                Ok(()) => entries.push(TranscriptEntry::System(format!("Exported session -> {}", out_path.display()))),
                Err(e) => entries.push(TranscriptEntry::Error(e.to_string())),
            }
        }
        "/directory" => {
            if let Some(p) = arg.strip_prefix("add ").map(str::trim) {
                engine.config.lock().await.include_directories.push(PathBuf::from(p));
                entries.push(TranscriptEntry::System(format!("Included workspace dir: {}", p)));
            } else {
                let dirs = cfg.allowed_workspace_roots();
                let list: Vec<String> = dirs.iter().map(|d| d.display().to_string()).collect();
                entries.push(TranscriptEntry::System(format!("Workspace roots:\n  {}", list.join("\n  "))));
            }
        }
        "/footer" => {
            *compact_footer = !*compact_footer;
        }
        "/vim" => {
            *vim_mode = !*vim_mode;
            entries.push(TranscriptEntry::System(format!("Vim indicator: {}", if *vim_mode { "ON" } else { "OFF" })));
        }
        "/theme" => {
            *theme = theme.next();
            entries.push(TranscriptEntry::System(format!("Theme switched -> {}", theme.name())));
        }
        "/auth" | "/gemma" => {
            let out = run_direct_shell(&cfg.cwd, &format!("curl -s {}/api/router/status | head -c 1200", cfg.connector_url));
            entries.push(TranscriptEntry::System(format!("Connector Status ({}):\n{}", cfg.connector_url, out)));
        }
        "/policies" | "/permissions" => {
            entries.push(TranscriptEntry::System(format!(
                "Active Approval Mode: {} | Policy search dirs: {}",
                current_mode.display_label(),
                cfg.paths.policies_dirs.iter().map(|p| p.display().to_string()).collect::<Vec<_>>().join(", ")
            )));
        }
        "/settings" | "/privacy" | "/hooks" | "/extensions" | "/ide" | "/docs" | "/bug" | "/shortcuts" | "/voice" => {
            entries.push(TranscriptEntry::System(format!(
                "Flowork Home: {}\nVault: {}\nShortcuts: Enter=Send | Shift+Enter=Newline | Shift+Tab=Mode | Ctrl+O=Toggle Details | Ctrl+C=Stop/Exit | !cmd=Shell",
                cfg.paths.user_flowork_dir.display(),
                cfg.paths.history_chats_dir.display()
            )));
        }
        "/editor" => {
            *draft_buf = String::from("# Write your multiline prompt here");
            entries.push(TranscriptEntry::System("Draft prompt buffer primed (Shift+Enter for newlines).".to_string()));
        }
        _ => {
            // Check custom `/<skill-name>` invocation
            let skill_name = cmd.trim_start_matches('/');
            let skills = discover_skills(&cfg);
            if let Some(sk) = skills.into_iter().find(|s| s.name.eq_ignore_ascii_case(skill_name)) {
                let invoked_prompt = if arg.is_empty() {
                    format!("Activate skill '{}' and follow its SKILL.md workflow.", sk.name)
                } else {
                    format!("Activate skill '{}' via activate_skill first and complete: {}", sk.name, arg)
                };
                entries.push(TranscriptEntry::User(format!("/{} {}", sk.name, arg).trim().to_string()));
                *running_turn = true;
                *turn_started_at = Instant::now();
                let eng = Arc::clone(engine);
                let tx_c = ui_tx.clone();
                *active_task_handle = Some(tokio::spawn(async move {
                    let _ = eng.run_prompt_turn(&invoked_prompt, Some(tx_c)).await;
                }));
            } else {
                entries.push(TranscriptEntry::Error(format!(
                    "Unknown slash command '{}'. Type /help or /skills.",
                    cmd
                )));
            }
        }
    }
    false
}

fn render_banner(
    f: &mut ratatui::Frame,
    area: Rect,
    theme: HudTheme,
    model: &str,
    mode: ApprovalMode,
    session_id: &str,
) {
    let cols = area.width;
    let short_sid = &session_id[..session_id.len().min(8)];

    if cols >= 56 && area.height >= 5 {
        let mut lines = Vec::new();
        for row in 0..4 {
            lines.push(Line::from(vec![
                Span::styled(
                    format!(" {} ", LIGHTNING_GLYPH[row]),
                    Style::default()
                        .fg(Color::Rgb(0, 255, 102))
                        .add_modifier(Modifier::BOLD),
                ),
                Span::styled(
                    MRFLOW_BANNER[row],
                    Style::default()
                        .fg(theme.primary())
                        .add_modifier(Modifier::BOLD),
                ),
            ]));
        }
        lines.push(Line::from(vec![
            Span::styled(
                " ⚡ FLOWORK OS SOVEREIGN ENGINE ",
                Style::default().fg(Color::Rgb(255, 255, 255)).add_modifier(Modifier::BOLD),
            ),
            Span::styled(
                format!("| Model: {} | Mode: {} | Vault: {}", model, mode.display_label(), short_sid),
                Style::default().fg(Color::Rgb(255, 255, 255)),
            ),
        ]));
        let p = Paragraph::new(lines)
            .block(
                Block::default()
                    .borders(Borders::BOTTOM)
                    .border_style(Style::default().fg(theme.primary())),
            )
            .style(Style::default().bg(Color::Reset));
        f.render_widget(p, area);
    } else {
        let line = Line::from(vec![
            Span::styled("⚡ MRFLOW ", Style::default().fg(theme.primary()).add_modifier(Modifier::BOLD)),
            Span::styled(
                format!("v2.0 | {} | {}", model, mode.display_label()),
                Style::default().fg(Color::Rgb(255, 255, 255)),
            ),
        ]);
        f.render_widget(Paragraph::new(line).style(Style::default().bg(Color::Reset)), area);
    }
}

#[allow(clippy::too_many_arguments)]
fn render_transcript(
    f: &mut ratatui::Frame,
    area: Rect,
    entries: &[TranscriptEntry],
    theme: HudTheme,
    show_details: bool,
    running: bool,
    tick: usize,
    elapsed_secs: u64,
    scroll_from_bottom: u16,
) {
    let mut lines: Vec<Line> = Vec::new();
    if entries.is_empty() {
        lines.push(Line::from(""));
        lines.push(Line::from(Span::styled(
            " Ready for autonomous Sovereign execution on Flowork OS.",
            Style::default().fg(Color::Rgb(255, 255, 255)),
        )));
        lines.push(Line::from(Span::styled(
            " Use @path to attach files/images, /skills to browse skills, !cmd for shell, Shift+Tab to switch mode.",
            Style::default().fg(Color::Rgb(255, 255, 255)),
        )));
    } else {
        for ent in entries {
            match ent {
                TranscriptEntry::User(u) => {
                    lines.push(Line::from(""));
                    lines.push(Line::from(vec![
                        Span::styled("❯ YOU ", Style::default().fg(theme.primary()).add_modifier(Modifier::BOLD)),
                        Span::styled(u.clone(), Style::default().fg(Color::Rgb(255, 255, 255)).add_modifier(Modifier::BOLD)),
                    ]));
                }
                TranscriptEntry::Assistant { text, thoughts } => {
                    if show_details && !thoughts.trim().is_empty() {
                        for tl in thoughts.lines().take(24) {
                            lines.push(Line::from(Span::styled(
                                format!("  💭 {}", tl),
                                Style::default().fg(theme.secondary()).add_modifier(Modifier::ITALIC),
                            )));
                        }
                    }
                    if !text.is_empty() {
                        lines.push(Line::from(""));
                        for l in text.lines() {
                            let st = if l.starts_with('#') {
                                Style::default().fg(theme.secondary()).add_modifier(Modifier::BOLD)
                            } else if l.trim_start().starts_with("```") {
                                Style::default().fg(theme.primary())
                            } else {
                                Style::default().fg(Color::Rgb(255, 255, 255))
                            };
                            lines.push(Line::from(Span::styled(format!(" {}", l), st)));
                        }
                    }
                }
                TranscriptEntry::ToolCard {
                    name,
                    args_summary,
                    status,
                    output,
                    ..
                } => {
                    let (icon, color) = match status.as_str() {
                        "running" => ("⚙", Color::Rgb(255, 176, 0)),
                        "success" => ("✔", Color::Rgb(0, 255, 102)),
                        _ => ("✖", Color::Rgb(255, 68, 102)),
                    };
                    lines.push(Line::from(vec![
                        Span::styled(format!("  {} [{}]", icon, name), Style::default().fg(color).add_modifier(Modifier::BOLD)),
                        Span::styled(format!(" {}", args_summary), Style::default().fg(Color::Rgb(255, 255, 255))),
                    ]));
                    if show_details && !output.is_empty() {
                        for ol in output.lines().take(12) {
                            lines.push(Line::from(Span::styled(
                                format!("     │ {}", ol),
                                Style::default().fg(Color::Rgb(255, 255, 255)),
                            )));
                        }
                    }
                }
                TranscriptEntry::System(s) => {
                    for sl in s.lines() {
                        lines.push(Line::from(Span::styled(
                            format!(" • {}", sl),
                            Style::default().fg(theme.secondary()),
                        )));
                    }
                }
                TranscriptEntry::Error(e) => {
                    lines.push(Line::from(Span::styled(
                        format!(" ✖ ERROR: {}", e),
                        Style::default().fg(Color::Rgb(255, 68, 102)).add_modifier(Modifier::BOLD),
                    )));
                }
            }
        }
    }

    if running {
        let frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
        let sp = frames[tick % frames.len()];
        lines.push(Line::from(Span::styled(
            format!(" {} Thinking & executing autonomously... ({}s)", sp, elapsed_secs),
            Style::default().fg(theme.primary()),
        )));
    }

    // Approximate wrapped line count cleanly
    let w = area.width.max(1) as usize;
    let total_visual_lines: usize = lines
        .iter()
        .map(|l| l.width().max(1).div_ceil(w))
        .sum();
    let max_scroll = total_visual_lines.saturating_sub(area.height as usize) as u16;
    let clamped_from_bottom = scroll_from_bottom.min(max_scroll);
    let scroll_y = max_scroll.saturating_sub(clamped_from_bottom);

    let p = Paragraph::new(lines)
        .scroll((scroll_y, 0))
        .wrap(Wrap { trim: false })
        .style(Style::default().bg(Color::Reset));
    f.render_widget(p, area);
}

#[allow(clippy::too_many_arguments)]
fn render_footer(
    f: &mut ratatui::Frame,
    area: Rect,
    theme: HudTheme,
    cwd: &std::path::Path,
    flowork_root: &std::path::Path,
    mode: ApprovalMode,
    model: &str,
    turn: usize,
    max_turns: usize,
    context_tokens: u64,
    tokens: &TokenUsage,
    compact: bool,
) {
    let limit = crate::context::get_model_token_limit(model, Some(flowork_root)).max(1);
    let ctx_pct = ((context_tokens as f64 / limit as f64) * 100.0).min(100.0);
    let ctx_color = if ctx_pct >= 75.0 {
        Color::Rgb(255, 68, 102)
    } else if ctx_pct >= 45.0 {
        Color::Rgb(255, 176, 0)
    } else {
        Color::Rgb(0, 255, 102)
    };
    let line = Line::from(vec![
        Span::styled(
            format!(" [{}] ", mode.display_label()),
            Style::default().fg(Color::Rgb(0, 0, 0)).bg(theme.primary()).add_modifier(Modifier::BOLD),
        ),
        Span::styled(format!(" {} ", model), Style::default().fg(theme.secondary())),
        Span::styled(
            format!("| Ctx: {:.0}% ", ctx_pct),
            Style::default().fg(ctx_color).add_modifier(Modifier::BOLD),
        ),
        Span::styled(
            if compact {
                format!("| tok: {}", tokens.total)
            } else {
                format!(
                    "| dir: {} | turn: {}/{} | tokens: {} (in:{} out:{} cache:{})",
                    cwd.display(),
                    turn,
                    max_turns,
                    tokens.total,
                    tokens.input,
                    tokens.output,
                    tokens.cached
                )
            },
            Style::default().fg(Color::Rgb(255, 255, 255)),
        ),
    ]);
    f.render_widget(Paragraph::new(line).style(Style::default().bg(Color::Reset)), area);
}

fn render_modal(f: &mut ratatui::Frame, area: Rect, m: &ActiveModal, theme: HudTheme) {
    let w = area.width.saturating_sub(8).min(72);
    let h = (m.options.len() as u16 + 6).min(area.height.saturating_sub(4));
    let x = (area.width.saturating_sub(w)) / 2;
    let y = (area.height.saturating_sub(h)) / 2;
    let rect = Rect::new(x, y, w, h);
    f.render_widget(Clear, rect);

    let mut lines = vec![
        Line::from(Span::styled(
            m.question_text.clone(),
            Style::default().fg(Color::Rgb(255, 255, 255)).add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
    ];
    for (i, opt) in m.options.iter().enumerate() {
        let sel = i == m.selected_idx;
        let prefix = if sel { " ▸ " } else { "   " };
        let st = if sel {
            Style::default().fg(Color::Rgb(0, 0, 0)).bg(theme.primary()).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::Rgb(210, 220, 230))
        };
        lines.push(Line::from(Span::styled(format!("{}{}", prefix, opt), st)));
    }
    if m.typing_custom {
        lines.push(Line::from(""));
        lines.push(Line::from(Span::styled(
            format!("Write-in: {}▌", m.custom_input),
            Style::default().fg(theme.secondary()),
        )));
    }
    let block = Block::default()
        .borders(Borders::ALL)
        .border_style(Style::default().fg(theme.primary()))
        .title(" Sovereign Confirmation (↑↓/Enter/Esc) ");
    f.render_widget(Paragraph::new(lines).block(block).wrap(Wrap { trim: false }), rect);
}

fn handle_modal_key(key: KeyEvent, m: &mut ActiveModal) -> bool {
    if m.typing_custom {
        match key.code {
            KeyCode::Enter => {
                if let Some(tx) = m.reply_tx.take() {
                    let _ = tx.send(Ok(json!({ "answer": m.custom_input })));
                }
                return true;
            }
            KeyCode::Esc => {
                m.typing_custom = false;
                return false;
            }
            KeyCode::Backspace => {
                m.custom_input.pop();
            }
            KeyCode::Char(c) => m.custom_input.push(c),
            _ => {}
        }
        return false;
    }

    match key.code {
        KeyCode::Up => m.selected_idx = m.selected_idx.saturating_sub(1),
        KeyCode::Down => {
            if m.selected_idx + 1 < m.options.len() {
                m.selected_idx += 1;
            }
        }
        KeyCode::Esc => {
            if let Some(tx) = m.reply_tx.take() {
                let _ = tx.send(Ok(json!({ "answer": "Deny" })));
            }
            return true;
        }
        KeyCode::Enter => {
            if m.selected_idx + 1 == m.options.len() {
                m.typing_custom = true;
                return false;
            }
            let chosen = m.options[m.selected_idx].clone();
            if let Some(tx) = m.reply_tx.take() {
                let _ = tx.send(Ok(json!({ "answer": chosen })));
            }
            return true;
        }
        _ => {}
    }
    false
}

fn compute_autocomplete_items(
    input: &str,
    cmds: &[(String, String)],
    cwd: &std::path::Path,
) -> Vec<(String, String)> {
    if input.starts_with('/') && !input.contains(' ') {
        let needle = input.to_ascii_lowercase();
        return cmds
            .iter()
            .filter(|(c, _)| c.starts_with(&needle))
            .cloned()
            .collect();
    }
    if let Some(last_tok) = input.split_whitespace().last() {
        if let Some(partial) = last_tok.strip_prefix('@') {
            let mut files = Vec::new();
            if let Ok(entries) = fs::read_dir(cwd) {
                for e in entries.flatten().take(40) {
                    let name = e.file_name().to_string_lossy().to_string();
                    if partial.is_empty() || name.starts_with(partial) {
                        files.push((format!("@{}", name), "workspace file".to_string()));
                    }
                }
            }
            files.sort_by(|a, b| a.0.cmp(&b.0));
            return files;
        }
    }
    Vec::new()
}

fn apply_autocomplete(input: &mut String, chosen: &str) {
    if input.starts_with('/') && !input.contains(' ') {
        *input = format!("{} ", chosen);
    } else if let Some(idx) = input.rfind('@') {
        input.truncate(idx);
        input.push_str(chosen);
        input.push(' ');
    }
}

fn summarize_args(args: &Value) -> String {
    let mut keys = Vec::new();
    for k in &["file_path", "command", "pattern", "path", "name", "agent_name", "url", "query"] {
        if let Some(v) = args.get(*k).and_then(|x| x.as_str()) {
            let short: String = v.chars().take(52).collect();
            keys.push(format!("{}={}", k, short));
        }
    }
    if keys.is_empty() {
        args.get("reason")
            .and_then(|x| x.as_str())
            .unwrap_or("")
            .chars()
            .take(56)
            .collect()
    } else {
        keys.join(" ")
    }
}

fn run_direct_shell(cwd: &std::path::Path, cmd: &str) -> String {
    let out = StdCommand::new("/bin/bash")
        .args(["-c", cmd])
        .current_dir(cwd)
        .output();
    match out {
        Ok(o) => {
            let mut s = String::from_utf8_lossy(&o.stdout).to_string();
            let e = String::from_utf8_lossy(&o.stderr);
            if !e.trim().is_empty() {
                s.push_str("\n[stderr] ");
                s.push_str(&e);
            }
            if s.trim().is_empty() {
                format!("Exit code: {}", o.status.code().unwrap_or(0))
            } else {
                s.chars().take(4000).collect()
            }
        }
        Err(e) => format!("Shell error: {}", e),
    }
}

fn copy_to_clipboard(text: &str) -> bool {
    for (bin, args) in [("xclip", &["-selection", "clipboard"][..]), ("xsel", &["--clipboard", "--input"][..]), ("wl-copy", &[][..])] {
        if let Ok(mut child) = StdCommand::new(bin)
            .args(args)
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .spawn()
        {
            if let Some(mut sin) = child.stdin.take() {
                let _ = sin.write_all(text.as_bytes());
            }
            if matches!(child.wait(), Ok(st) if st.success()) {
                return true;
            }
        }
    }
    false
}

