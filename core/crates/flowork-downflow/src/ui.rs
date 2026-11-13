// 👑 FLOWORK OS SOVEREIGN DOWNFLOW - RATATUI TUI DASHBOARD
// Clean-room TUI interface under Apache-2.0

use crate::models::{DownloadItem, DownloadStatus, StateManager};
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::{Backend, CrosstermBackend},
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Cell, Gauge, Paragraph, Row, Table, TableState},
    Frame, Terminal,
};
use std::io;
use std::time::Duration;

pub struct TuiApp {
    state: StateManager,
    table_state: TableState,
    should_quit: bool,
}

impl TuiApp {
    pub fn new(state: StateManager) -> Self {
        let mut table_state = TableState::default();
        table_state.select(Some(0));
        Self {
            state,
            table_state,
            should_quit: false,
        }
    }

    pub async fn run(&mut self) -> Result<(), io::Error> {
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
        let backend = CrosstermBackend::new(stdout);
        let mut terminal = Terminal::new(backend)?;

        let res = self.run_loop(&mut terminal).await;

        disable_raw_mode()?;
        execute!(
            terminal.backend_mut(),
            LeaveAlternateScreen,
            DisableMouseCapture
        )?;
        terminal.show_cursor()?;

        res
    }

    async fn run_loop<B: Backend>(&mut self, terminal: &mut Terminal<B>) -> Result<(), io::Error> {
        while !self.should_quit {
            let items = self.state.list();
            terminal.draw(|f| self.draw(f, &items))?;

            if event::poll(Duration::from_millis(250))? {
                if let Event::Key(key) = event::read()? {
                    match key.code {
                        KeyCode::Char('q') | KeyCode::Esc => self.should_quit = true,
                        KeyCode::Down | KeyCode::Char('j') => {
                            let i = match self.table_state.selected() {
                                Some(i) => {
                                    if items.is_empty() {
                                        0
                                    } else if i >= items.len() - 1 {
                                        0
                                    } else {
                                        i + 1
                                    }
                                }
                                None => 0,
                            };
                            self.table_state.select(Some(i));
                        }
                        KeyCode::Up | KeyCode::Char('k') => {
                            let i = match self.table_state.selected() {
                                Some(i) => {
                                    if items.is_empty() {
                                        0
                                    } else if i == 0 {
                                        items.len().saturating_sub(1)
                                    } else {
                                        i - 1
                                    }
                                }
                                None => 0,
                            };
                            self.table_state.select(Some(i));
                        }
                        KeyCode::Char('p') => {
                            if let Some(i) = self.table_state.selected() {
                                if let Some(item) = items.get(i) {
                                    if item.status == DownloadStatus::Downloading {
                                        self.state.update_status(item.id, DownloadStatus::Paused, None);
                                    } else if item.status == DownloadStatus::Paused {
                                        self.state.update_status(item.id, DownloadStatus::Queued, None);
                                    }
                                }
                            }
                        }
                        KeyCode::Char('d') | KeyCode::Delete => {
                            if let Some(i) = self.table_state.selected() {
                                if let Some(item) = items.get(i) {
                                    self.state.remove(item.id, false);
                                }
                            }
                        }
                        _ => {}
                    }
                }
            }
        }
        Ok(())
    }

    fn draw(&mut self, f: &mut Frame, items: &[DownloadItem]) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .margin(1)
            .constraints([
                Constraint::Length(3),
                Constraint::Min(8),
                Constraint::Length(3),
            ])
            .split(f.area());

        // Header
        let title = Paragraph::new(Line::from(vec![
            Span::styled("⚡ FLOWORK DOWNFLOW ", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
            Span::styled("— Sovereign Multi-Part Download Engine", Style::default().fg(Color::White)),
        ]))
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::ALL).style(Style::default().fg(Color::Cyan)));
        f.render_widget(title, chunks[0]);

        // Table
        let rows = items.iter().map(|it| {
            let status_style = match it.status {
                DownloadStatus::Downloading => Style::default().fg(Color::Green).add_modifier(Modifier::BOLD),
                DownloadStatus::Queued => Style::default().fg(Color::Yellow),
                DownloadStatus::Paused => Style::default().fg(Color::Magenta),
                DownloadStatus::Complete => Style::default().fg(Color::Blue),
                DownloadStatus::Error => Style::default().fg(Color::Red),
            };

            let progress = format!("{:.1}% ({}/{})",
                it.progress_pct(),
                format_size(it.downloaded),
                if it.size > 0 { format_size(it.size) } else { "Unknown".to_string() }
            );

            let speed = if it.status == DownloadStatus::Downloading && it.speed_bytes_per_sec > 0 {
                format!("{}/s", format_size(it.speed_bytes_per_sec))
            } else {
                "-".to_string()
            };

            Row::new(vec![
                Cell::from(it.id.to_string()),
                Cell::from(it.file_name.clone()),
                Cell::from(it.status.to_string()).style(status_style),
                Cell::from(progress),
                Cell::from(speed),
                Cell::from(it.category.clone()),
            ])
        });

        let table = Table::new(
            rows,
            [
                Constraint::Length(5),
                Constraint::Percentage(35),
                Constraint::Length(14),
                Constraint::Length(25),
                Constraint::Length(14),
                Constraint::Length(12),
            ],
        )
        .header(
            Row::new(vec!["ID", "File Name", "Status", "Progress", "Speed", "Category"])
                .style(Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))
                .bottom_margin(1),
        )
        .block(Block::default().title(" Active Downloads ").borders(Borders::ALL))
        .highlight_style(Style::default().bg(Color::DarkGray).add_modifier(Modifier::BOLD));

        f.render_stateful_widget(table, chunks[1], &mut self.table_state);

        // Footer
        let footer = Paragraph::new(Line::from(vec![
            Span::styled(" [p] ", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw("Pause/Resume | "),
            Span::styled(" [d] ", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw("Delete | "),
            Span::styled(" [q] ", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw("Quit"),
        ]))
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::ALL));
        f.render_widget(footer, chunks[2]);
    }
}

fn format_size(bytes: u64) -> String {
    const KB: u64 = 1024;
    const MB: u64 = KB * 1024;
    const GB: u64 = MB * 1024;

    if bytes >= GB {
        format!("{:.2} GB", bytes as f64 / GB as f64)
    } else if bytes >= MB {
        format!("{:.1} MB", bytes as f64 / MB as f64)
    } else if bytes >= KB {
        format!("{:.0} KB", bytes as f64 / KB as f64)
    } else {
        format!("{} B", bytes)
    }
}
