use std::io;
use std::time::{Duration, Instant};

use crossterm::{
    event::{self, Event, KeyCode, KeyEventKind, KeyModifiers},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{
        Block, BorderType, Borders, Cell, Gauge, Paragraph, Row, Table, TableState,
    },
    Frame, Terminal,
};

use crate::gpu::{probe_gpu, GpuTelemetry};
use crate::system::{ProcessItem, SystemTelemetry, SystemTracker};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SortMode {
    Vram,
    Cpu,
    Mem,
    Pid,
}

impl SortMode {
    pub fn next(&self) -> Self {
        match self {
            SortMode::Vram => SortMode::Cpu,
            SortMode::Cpu => SortMode::Mem,
            SortMode::Mem => SortMode::Pid,
            SortMode::Pid => SortMode::Vram,
        }
    }

    pub fn label(&self) -> &'static str {
        match self {
            SortMode::Vram => "VRAM",
            SortMode::Cpu => "CPU%",
            SortMode::Mem => "RAM",
            SortMode::Pid => "PID",
        }
    }
}

pub struct App {
    pub tracker: SystemTracker,
    pub gpu: Option<GpuTelemetry>,
    pub sys: SystemTelemetry,
    pub table_state: TableState,
    pub sort_mode: SortMode,
    pub filter: String,
    pub is_filtering: bool,
    pub status_msg: Option<(String, Instant)>,
    pub interval: Duration,
    pub should_quit: bool,
}

impl App {
    pub fn new(interval_secs: f32) -> Self {
        let mut tracker = SystemTracker::new();
        let gpu = probe_gpu();
        let gpu_procs = gpu.as_ref().map(|g| g.processes.as_slice()).unwrap_or(&[]);
        let sys = tracker.snapshot(gpu_procs);

        let mut table_state = TableState::default();
        table_state.select(Some(0));

        Self {
            tracker,
            gpu,
            sys,
            table_state,
            sort_mode: SortMode::Vram,
            filter: String::new(),
            is_filtering: false,
            status_msg: Some((
                "Flowork Sovereign Taskman ready. Press '?' for help.".to_string(),
                Instant::now(),
            )),
            interval: Duration::from_secs_f32(interval_secs.max(0.2)),
            should_quit: false,
        }
    }

    pub fn refresh(&mut self) {
        self.gpu = probe_gpu();
        let gpu_procs = self.gpu.as_ref().map(|g| g.processes.as_slice()).unwrap_or(&[]);
        self.sys = self.tracker.snapshot(gpu_procs);
    }

    pub fn filtered_processes(&self) -> Vec<ProcessItem> {
        let mut list = self.sys.processes.clone();

        // Apply text filter if any
        if !self.filter.is_empty() {
            let q = self.filter.to_lowercase();
            list.retain(|p| {
                p.name.to_lowercase().contains(&q)
                    || p.pid.to_string().contains(&q)
                    || p.ai_tag.as_deref().unwrap_or("").to_lowercase().contains(&q)
                    || p.cmdline.to_lowercase().contains(&q)
            });
        }

        // Apply sorting
        match self.sort_mode {
            SortMode::Vram => list.sort_by(|a, b| b.vram_mb.cmp(&a.vram_mb)),
            SortMode::Cpu => list.sort_by(|a, b| b.cpu_pct.partial_cmp(&a.cpu_pct).unwrap_or(std::cmp::Ordering::Equal)),
            SortMode::Mem => list.sort_by(|a, b| b.mem_mb.cmp(&a.mem_mb)),
            SortMode::Pid => list.sort_by(|a, b| a.pid.cmp(&b.pid)),
        }

        list
    }

    pub fn select_next(&mut self) {
        let count = self.filtered_processes().len();
        if count == 0 {
            return;
        }
        let i = match self.table_state.selected() {
            Some(i) => {
                if i + 1 >= count {
                    0
                } else {
                    i + 1
                }
            }
            None => 0,
        };
        self.table_state.select(Some(i));
    }

    pub fn select_prev(&mut self) {
        let count = self.filtered_processes().len();
        if count == 0 {
            return;
        }
        let i = match self.table_state.selected() {
            Some(i) => {
                if i == 0 {
                    count - 1
                } else {
                    i - 1
                }
            }
            None => 0,
        };
        self.table_state.select(Some(i));
    }

    pub fn kill_selected(&mut self) {
        let procs = self.filtered_processes();
        if let Some(idx) = self.table_state.selected() {
            if let Some(target) = procs.get(idx) {
                let pid = target.pid;
                let res = unsafe { libc::kill(pid as libc::pid_t, libc::SIGTERM) };
                if res == 0 {
                    self.set_status(format!("Sent SIGTERM to PID {} ({})", pid, target.name));
                    self.refresh();
                } else {
                    let err = io::Error::last_os_error();
                    self.set_status(format!("Failed to kill PID {}: {}", pid, err));
                }
            }
        }
    }

    pub fn set_status(&mut self, msg: String) {
        self.status_msg = Some((msg, Instant::now()));
    }
}

pub fn run_tui(mut app: App) -> io::Result<()> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut last_tick = Instant::now();

    let res = loop {
        terminal.draw(|f| render_ui(f, &mut app))?;

        let timeout = app
            .interval
            .checked_sub(last_tick.elapsed())
            .unwrap_or_else(|| Duration::from_millis(0));

        if event::poll(timeout)? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    if app.is_filtering {
                        match key.code {
                            KeyCode::Enter | KeyCode::Esc => {
                                app.is_filtering = false;
                            }
                            KeyCode::Backspace => {
                                app.filter.pop();
                            }
                            KeyCode::Char(c) => {
                                app.filter.push(c);
                            }
                            _ => {}
                        }
                    } else {
                        match key.code {
                            KeyCode::Char('q') | KeyCode::Char('Q') => {
                                app.should_quit = true;
                            }
                            KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                                app.should_quit = true;
                            }
                            KeyCode::Down | KeyCode::Char('j') => {
                                app.select_next();
                            }
                            KeyCode::Up | KeyCode::Char('k') => {
                                app.select_prev();
                            }
                            KeyCode::Char('s') | KeyCode::Tab => {
                                app.sort_mode = app.sort_mode.next();
                                app.set_status(format!("Sort mode: {}", app.sort_mode.label()));
                            }
                            KeyCode::Char('/') => {
                                app.is_filtering = true;
                                app.filter.clear();
                            }
                            KeyCode::Char('r') => {
                                app.refresh();
                                app.set_status("Metrics refreshed.".to_string());
                            }
                            KeyCode::Char('x') | KeyCode::Char('K') => {
                                app.kill_selected();
                            }
                            KeyCode::Char('?') => {
                                app.set_status("Keys: [q] Quit  [↑/↓] Select  [s/Tab] Sort  [x] Terminate  [/] Filter  [r] Refresh".to_string());
                            }
                            _ => {}
                        }
                    }
                }
            }
        }

        if last_tick.elapsed() >= app.interval {
            app.refresh();
            last_tick = Instant::now();
        }

        if app.should_quit {
            break Ok(());
        }
    };

    // Restore terminal
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;

    res
}

fn render_ui(f: &mut Frame, app: &mut App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header bar
            Constraint::Length(8),  // Telemetry Dashboard (Gpu, Vram, Cpu, Ram)
            Constraint::Min(8),     // Process table
            Constraint::Length(3),  // Status & Keybind Footer
        ])
        .split(f.area());

    render_header(f, app, chunks[0]);
    render_metrics(f, app, chunks[1]);
    render_processes(f, app, chunks[2]);
    render_footer(f, app, chunks[3]);
}

fn render_header(f: &mut Frame, app: &App, area: Rect) {
    let host = &app.sys.host_name;
    let kernel = &app.sys.kernel_version;
    let uptime_hrs = app.sys.uptime_secs / 3600;
    let uptime_mins = (app.sys.uptime_secs % 3600) / 60;

    let gpu_title = if let Some(g) = &app.gpu {
        format!("{} [Driver {}]", g.name, g.driver_version)
    } else {
        "No Dedicated GPU Detected (DRM Generic Sysfs)".to_string()
    };

    let title = Line::from(vec![
        Span::styled(" FLOWORK ", Style::default().fg(Color::Black).bg(Color::Cyan).add_modifier(Modifier::BOLD)),
        Span::raw(" "),
        Span::styled("SOVEREIGN TASKMAN", Style::default().fg(Color::White).add_modifier(Modifier::BOLD)),
        Span::raw(" | "),
        Span::styled(gpu_title, Style::default().fg(Color::Yellow)),
        Span::raw(" | "),
        Span::styled(format!("{host} ({kernel})"), Style::default().fg(Color::DarkGray)),
        Span::raw(" | "),
        Span::styled(format!("Up: {uptime_hrs}h {uptime_mins}m"), Style::default().fg(Color::Green)),
    ]);

    let block = Block::default()
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded)
        .border_style(Style::default().fg(Color::Cyan));

    let p = Paragraph::new(title).block(block).alignment(Alignment::Left);
    f.render_widget(p, area);
}

fn render_metrics(f: &mut Frame, app: &App, area: Rect) {
    let metric_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(25), // GPU Core
            Constraint::Percentage(25), // VRAM
            Constraint::Percentage(25), // CPU
            Constraint::Percentage(25), // RAM
        ])
        .split(area);

    // 1. GPU Gauge
    let (gpu_pct, gpu_label) = if let Some(g) = &app.gpu {
        let temp_str = format!("{}°C", g.temperature_c);
        let power_str = g.power_draw_w.map(|w| format!("{:.0}W", w)).unwrap_or_else(|| "N/A".to_string());
        (
            g.utilization_gpu.min(100) as u16,
            format!("GPU Core: {}% | {} | {}", g.utilization_gpu, temp_str, power_str),
        )
    } else {
        (0, "GPU: N/A".to_string())
    };

    let gpu_color = if gpu_pct > 80 {
        Color::Red
    } else if gpu_pct > 50 {
        Color::Yellow
    } else {
        Color::Cyan
    };

    let gpu_gauge = Gauge::default()
        .block(Block::default().title(" GPU Core ").borders(Borders::ALL).border_type(BorderType::Rounded))
        .gauge_style(Style::default().fg(gpu_color).bg(Color::Black))
        .percent(gpu_pct)
        .label(gpu_label);
    f.render_widget(gpu_gauge, metric_chunks[0]);

    // 2. VRAM Gauge
    let (vram_pct, vram_label) = if let Some(g) = &app.gpu {
        let pct = if g.memory_total_mb > 0 {
            ((g.memory_used_mb as f64 / g.memory_total_mb as f64) * 100.0) as u16
        } else {
            0
        };
        (
            pct.min(100),
            format!("VRAM: {} / {} MB ({}%)", g.memory_used_mb, g.memory_total_mb, pct),
        )
    } else {
        (0, "VRAM: 0 MB".to_string())
    };

    let vram_color = if vram_pct > 85 {
        Color::Red
    } else if vram_pct > 65 {
        Color::Magenta
    } else {
        Color::Green
    };

    let vram_gauge = Gauge::default()
        .block(Block::default().title(" VRAM Allocation ").borders(Borders::ALL).border_type(BorderType::Rounded))
        .gauge_style(Style::default().fg(vram_color).bg(Color::Black))
        .percent(vram_pct)
        .label(vram_label);
    f.render_widget(vram_gauge, metric_chunks[1]);

    // 3. CPU Total
    let cpu_pct = app.sys.cpu_total_pct.min(100.0) as u16;
    let cpu_color = if cpu_pct > 85 {
        Color::Red
    } else if cpu_pct > 60 {
        Color::Yellow
    } else {
        Color::Blue
    };

    let cpu_gauge = Gauge::default()
        .block(Block::default().title(format!(" CPU ({} Cores) ", app.sys.cpu_cores)).borders(Borders::ALL).border_type(BorderType::Rounded))
        .gauge_style(Style::default().fg(cpu_color).bg(Color::Black))
        .percent(cpu_pct)
        .label(format!("CPU Total: {:.1}%", app.sys.cpu_total_pct));
    f.render_widget(cpu_gauge, metric_chunks[2]);

    // 4. System RAM
    let mem_pct = if app.sys.mem_total_mb > 0 {
        ((app.sys.mem_used_mb as f64 / app.sys.mem_total_mb as f64) * 100.0) as u16
    } else {
        0
    };
    let ram_color = if mem_pct > 85 {
        Color::Red
    } else if mem_pct > 70 {
        Color::Yellow
    } else {
        Color::LightGreen
    };

    let ram_gauge = Gauge::default()
        .block(Block::default().title(" System RAM ").borders(Borders::ALL).border_type(BorderType::Rounded))
        .gauge_style(Style::default().fg(ram_color).bg(Color::Black))
        .percent(mem_pct)
        .label(format!("RAM: {} / {} MB ({}%)", app.sys.mem_used_mb, app.sys.mem_total_mb, mem_pct));
    f.render_widget(ram_gauge, metric_chunks[3]);
}

fn render_processes(f: &mut Frame, app: &mut App, area: Rect) {
    let procs = app.filtered_processes();

    let header_cells = [
        "PID",
        "PROCESS NAME",
        "AI / WORKLOAD ROLE",
        "CPU %",
        "RAM",
        "VRAM",
    ]
    .iter()
    .map(|h| {
        let is_active_sort = match (*h, app.sort_mode) {
            ("VRAM", SortMode::Vram) => true,
            ("CPU %", SortMode::Cpu) => true,
            ("RAM", SortMode::Mem) => true,
            ("PID", SortMode::Pid) => true,
            _ => false,
        };
        let style = if is_active_sort {
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD | Modifier::UNDERLINED)
        } else {
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)
        };
        Cell::from(*h).style(style)
    });

    let header = Row::new(header_cells)
        .style(Style::default().bg(Color::Rgb(20, 25, 35)))
        .height(1);

    let rows: Vec<Row> = procs
        .iter()
        .map(|p| {
            let pid_str = p.pid.to_string();
            let cpu_str = format!("{:.1}%", p.cpu_pct);
            let mem_str = format!("{} MB", p.mem_mb);
            let vram_str = if p.vram_mb > 0 {
                format!("{} MB", p.vram_mb)
            } else {
                "-".to_string()
            };

            let ai_role = p.ai_tag.clone().unwrap_or_else(|| {
                if p.vram_mb > 0 {
                    "GPU Accelerated".to_string()
                } else {
                    "System".to_string()
                }
            });

            let role_style = if p.ai_tag.is_some() {
                Style::default().fg(Color::Magenta).add_modifier(Modifier::BOLD)
            } else if p.vram_mb > 0 {
                Style::default().fg(Color::Yellow)
            } else {
                Style::default().fg(Color::DarkGray)
            };

            let vram_style = if p.vram_mb > 1000 {
                Style::default().fg(Color::Red).add_modifier(Modifier::BOLD)
            } else if p.vram_mb > 0 {
                Style::default().fg(Color::Yellow)
            } else {
                Style::default().fg(Color::DarkGray)
            };

            let cells = vec![
                Cell::from(pid_str).style(Style::default().fg(Color::White)),
                Cell::from(p.name.clone()).style(Style::default().fg(Color::White).add_modifier(Modifier::BOLD)),
                Cell::from(ai_role).style(role_style),
                Cell::from(cpu_str).style(Style::default().fg(Color::LightBlue)),
                Cell::from(mem_str).style(Style::default().fg(Color::LightGreen)),
                Cell::from(vram_str).style(vram_style),
            ];

            Row::new(cells).height(1)
        })
        .collect();

    let widths = [
        Constraint::Length(8),          // PID
        Constraint::Percentage(25),     // Name
        Constraint::Percentage(30),     // AI / Workload
        Constraint::Length(10),         // CPU %
        Constraint::Length(12),         // RAM
        Constraint::Length(12),         // VRAM
    ];

    let filter_indicator = if !app.filter.is_empty() {
        format!(" [Filter: \"{}\"]", app.filter)
    } else {
        "".to_string()
    };

    let title = format!(
        " Active Workloads & GPU Processes ({} found) [Sorted by: {}]{} ",
        procs.len(),
        app.sort_mode.label(),
        filter_indicator
    );

    let table = Table::new(rows, widths)
        .header(header)
        .block(
            Block::default()
                .title(title)
                .borders(Borders::ALL)
                .border_type(BorderType::Rounded)
                .border_style(Style::default().fg(Color::Cyan)),
        )
        .row_highlight_style(
            Style::default()
                .bg(Color::Rgb(35, 45, 65))
                .fg(Color::White)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol("▶ ");

    f.render_stateful_widget(table, area, &mut app.table_state);
}

fn render_footer(f: &mut Frame, app: &App, area: Rect) {
    let keybinds = if app.is_filtering {
        Line::from(vec![
            Span::styled("FILTER MODE: ", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::styled(&app.filter, Style::default().fg(Color::White).add_modifier(Modifier::BOLD)),
            Span::styled("█", Style::default().fg(Color::Cyan)),
            Span::raw(" (Press [Enter] or [Esc] to confirm)"),
        ])
    } else {
        Line::from(vec![
            Span::styled("[q]", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw(" Quit  "),
            Span::styled("[↑/↓]", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw(" Navigate  "),
            Span::styled("[s/Tab]", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw(format!(" Sort ({})  ", app.sort_mode.label())),
            Span::styled("[x]", Style::default().fg(Color::Red).add_modifier(Modifier::BOLD)),
            Span::raw(" Kill Proc  "),
            Span::styled("[/]", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw(" Filter  "),
            Span::styled("[r]", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw(" Refresh  "),
            Span::styled("[?]", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw(" Help"),
        ])
    };

    let status_text = if let Some((msg, time)) = &app.status_msg {
        if time.elapsed() < Duration::from_secs(5) {
            format!(" | {}", msg)
        } else {
            "".to_string()
        }
    } else {
        "".to_string()
    };

    let full_line = Line::from(vec![
        Span::raw(keybinds.to_string()),
        Span::styled(status_text, Style::default().fg(Color::Green).add_modifier(Modifier::ITALIC)),
    ]);

    let block = Block::default()
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded)
        .border_style(Style::default().fg(Color::DarkGray));

    let p = Paragraph::new(full_line).block(block).alignment(Alignment::Left);
    f.render_widget(p, area);
}
