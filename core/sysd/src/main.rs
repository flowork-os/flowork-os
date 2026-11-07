// [FL_INDEX: sysd_eager_uinput_init, main_rs, uinput_ctrl, rust_daemon, hardware_init | COT: Eagerly initialize persistent global virtual USB HID device in kernel upon sysd daemon startup.| AT: 2026-11-01T16:31:45Z]
// =============================================================================
// 🚀 Flowork Sovereign OS — System Daemon (flowork-sysd in Pure Rust)
// Native D-Bus, X11, persistent Chrome CDP & kernel synergy on port 18090
// =============================================================================

mod cdp_pool;
mod chat_store;
mod dbus_ctrl;
mod drm_capture;
mod flowork_agent_bridge;
mod kernel_surveillance;
mod landlock_sandbox;
mod reflex;
mod routes;
mod scratch_janitor;
mod sidebar_geometry;
mod terminal_exec;
mod uinput_ctrl;
mod x11_ctrl;

use std::net::SocketAddr;
use tokio::signal;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let port: u16 = std::env::var("FLOWORK_SYSD_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(18090);

    let host = std::env::var("FLOWORK_SYSD_HOST").unwrap_or_else(|_| "127.0.0.1".to_string());
    let addr: SocketAddr = format!("{}:{}", host, port).parse()?;

    println!("=============================================================================");
    println!("  ⚡ Flowork Sovereign OS — Core System Daemon (Pure Rust)");
    println!("  Listening on: http://{}", addr);
    println!("  Subsystems: D-Bus (zbus) | X11 (x11rb) | Chrome CDP | Kernel Synergy");
    println!("  Kernel Features: uinput HID | Netlink Surveillance | DRM/KMS | Landlock");
    println!("=============================================================================");

    // Eagerly initialize persistent virtual USB HID hardware in the kernel
    let _ = uinput_ctrl::get_global_uinput();

    // Start autonomous scratchpad hygiene janitor
    scratch_janitor::start_scratch_janitor().await;

    let app = routes::create_router();

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }

    println!("[flowork-sysd] Gracefully shutting down...");
}
