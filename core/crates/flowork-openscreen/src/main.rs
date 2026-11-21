mod assets;
mod ipc;
mod recorder;
mod server;

use ipc::AppState;
use server::EmbeddedServer;
use std::{
    path::PathBuf,
    sync::Arc,
};
use tao::{
    dpi::LogicalSize,
    event::{Event, StartCause, WindowEvent},
    event_loop::{ControlFlow, EventLoopBuilder},
    platform::unix::WindowExtUnix,
    window::WindowBuilder,
};
use wry::{WebViewBuilder, WebViewBuilderExtUnix};

const BRIDGE_JS: &str = include_str!("bridge.js");

#[derive(Debug)]
enum UserEvent {
    IpcCallback(String),
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Fix WebKitGTK DMA-BUF rendering on NVIDIA proprietary drivers
    std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    println!("[Flowork OS] Starting Sovereign OpenScreen Native Shell...");

    let app_root = PathBuf::from("/opt/floworkos/apps/openscreen");
    let web_dir = app_root.join("web");
    let resources_dir = app_root.join("resources");
    let recordings_dir = dirs::video_dir()
        .unwrap_or_else(|| dirs::home_dir().unwrap().join("Videos"))
        .join("OpenScreen");
    let helper_path = resources_dir.join("bin/openscreen-pipewire-helper");

    let server = EmbeddedServer::start(web_dir.clone(), resources_dir.clone(), recordings_dir.clone())?;
    println!("[Flowork OS] Embedded HTTP server running on port {}", server.port);

    let app_state = Arc::new(AppState::new(recordings_dir.clone(), helper_path));

    let event_loop = EventLoopBuilder::<UserEvent>::with_user_event().build();
    let proxy = event_loop.create_proxy();

    let window = WindowBuilder::new()
        .with_title("OpenScreen — Flowork OS")
        .with_inner_size(LogicalSize::new(1400.0, 900.0))
        .with_min_inner_size(LogicalSize::new(800.0, 600.0))
        .build(&event_loop)?;

    let app_state_ipc = app_state.clone();
    let app_url = format!("http://127.0.0.1:{}/index.html?windowType=editor", server.port);

    let builder = WebViewBuilder::new()
        .with_initialization_script(BRIDGE_JS)
        .with_ipc_handler(move |request| {
            let body = request.body();
            if let Some(res) = app_state_ipc.handle_ipc(body) {
                let script = format!(
                    "window.__openscreen_callback({}, {}, {}, {});",
                    res.id,
                    res.success,
                    res.result.map(|v| v.to_string()).unwrap_or_else(|| "null".into()),
                    res.error.map(|e| serde_json::to_string(&e).unwrap()).unwrap_or_else(|| "null".into())
                );
                let _ = proxy.send_event(UserEvent::IpcCallback(script));
            }
        })
        .with_url(&app_url)
        .with_devtools(true);

    use gtk::prelude::*;
    let vbox = window.default_vbox().expect("Failed to get default vbox from Tao window");
    let webview = builder.build_gtk(vbox)?;
    vbox.show_all();
    window.gtk_window().show_all();

    println!("[Flowork OS] Sovereign OpenScreen Shell initialized and running.");

    event_loop.run(move |event, _, control_flow| {
        *control_flow = ControlFlow::Wait;

        match event {
            Event::NewEvents(StartCause::Init) => {
                println!("[Flowork OS] OpenScreen EventLoop initialized.");
            }
            Event::UserEvent(UserEvent::IpcCallback(script)) => {
                if let Err(e) = webview.evaluate_script(&script) {
                    eprintln!("[IPC] evaluate_script error: {}", e);
                }
            }
            Event::WindowEvent {
                event: WindowEvent::CloseRequested,
                ..
            } => {
                println!("[Flowork OS] OpenScreen window close requested.");
                *control_flow = ControlFlow::Exit;
            }
            _ => (),
        }
    });
}
