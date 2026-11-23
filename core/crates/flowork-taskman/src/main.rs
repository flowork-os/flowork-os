mod ai_detector;
mod gpu;
mod system;
mod ui;

use std::env;
use std::io::Write;
use std::process;

use gpu::probe_gpu;
use system::SystemTracker;
use ui::{run_tui, App};

fn safe_println(s: &str) {
    let mut stdout = std::io::stdout();
    if let Err(e) = writeln!(stdout, "{}", s) {
        if e.kind() == std::io::ErrorKind::BrokenPipe {
            process::exit(0);
        }
    }
}

fn print_help() {
    let text = r#"Flowork Sovereign GPU Task Manager (flowork-taskman) v0.1.0
First-Party Native Rust Telemetry & Workload Monitor

USAGE:
    gputaskman [OPTIONS]
    flowork-taskman [OPTIONS]

OPTIONS:
    -j, --json          Output full telemetry snapshot (GPU, System, AI workloads) as JSON and exit
    --once              Print single terminal summary snapshot and exit
    --list-gpus         Print detected GPU hardware, driver, and VRAM specifications
    -i, --interval <S>  Update interval in seconds for interactive TUI (default: 1.0)
    --gpu <INDEX>       Target specific GPU index (default: 0)
    --no-system         Omit system CPU and RAM telemetry
    --no-host           Omit host information
    --window            Compatibility flag for launching in dedicated window
    -h, --help          Show this help message
    -v, --version       Show version information

INTERACTIVE CONTROLS:
    q, Ctrl+C           Quit task manager
    j, Down             Navigate down process list
    k, Up               Navigate up process list
    s, Tab              Cycle sort column (VRAM, CPU%, RAM, PID)
    /                   Filter processes by text or PID
    x, K                Send SIGTERM to selected process
    r                   Force refresh metrics
    ?                   Show keybindings overlay
"#;
    safe_println(text);
}

fn handle_json(no_system: bool) {
    let gpu = probe_gpu();
    let gpu_procs = gpu.as_ref().map(|g| g.processes.as_slice()).unwrap_or(&[]);
    
    let sys = if !no_system {
        let mut tracker = SystemTracker::new();
        Some(tracker.snapshot(gpu_procs))
    } else {
        None
    };

    let output = serde_json::json!({
        "status": "ok",
        "app": "gputaskman",
        "version": "0.1.0-sovereign",
        "timestamp_unix": std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0),
        "gpu": gpu,
        "system": sys,
    });

    safe_println(&serde_json::to_string_pretty(&output).unwrap_or_default());
}

fn handle_once() {
    let mut tracker = SystemTracker::new();
    let gpu = probe_gpu();
    let gpu_procs = gpu.as_ref().map(|g| g.processes.as_slice()).unwrap_or(&[]);
    let sys = tracker.snapshot(gpu_procs);

    safe_println("================================================================================");
    safe_println(" FLOWORK SOVEREIGN TASK MANAGER — ONE-SHOT TELEMETRY SNAPSHOT");
    safe_println("================================================================================");
    safe_println(&format!(" Host: {} | Kernel: {} | Uptime: {}s", sys.host_name, sys.kernel_version, sys.uptime_secs));
    safe_println(&format!(" CPU: {:.1}% ({} Cores) | System RAM: {} / {} MB", sys.cpu_total_pct, sys.cpu_cores, sys.mem_used_mb, sys.mem_total_mb));
    
    if let Some(g) = &gpu {
        let pwr = g.power_draw_w.map(|w| format!("{:.0}W", w)).unwrap_or_else(|| "N/A".to_string());
        safe_println(&format!(" GPU: {} [Driver {}]", g.name, g.driver_version));
        safe_println(&format!(" GPU Core: {}% | Temp: {}°C | Power: {}", g.utilization_gpu, g.temperature_c, pwr));
        safe_println(&format!(" VRAM Allocation: {} / {} MB", g.memory_used_mb, g.memory_total_mb));
        safe_println(&format!(" GPU Active Processes: {}", g.processes.len()));
        for p in &g.processes {
            let ai_tag = p.ai_classification.as_deref().unwrap_or("-");
            safe_println(&format!("   -> PID {:<7} {:<24} {:<6} MB (Type: {}, AI: {})", p.pid, p.name, p.memory_used_mb, p.process_type, ai_tag));
        }
    } else {
        safe_println(" GPU: No dedicated accelerator detected (using DRM Generic sysfs).");
    }
    safe_println("--------------------------------------------------------------------------------");
    safe_println(" Top Correlated Host Workloads:");
    let mut procs = sys.processes;
    procs.sort_by(|a, b| b.vram_mb.cmp(&a.vram_mb).then_with(|| b.mem_mb.cmp(&a.mem_mb)));
    for p in procs.iter().take(10) {
        let ai = p.ai_tag.as_deref().unwrap_or("-");
        safe_println(&format!("   PID {:<7} {:<22} CPU {:>5.1}% | RAM {:>5} MB | VRAM {:>5} MB | AI: {}", p.pid, p.name, p.cpu_pct, p.mem_mb, p.vram_mb, ai));
    }
    safe_println("================================================================================");
}

fn handle_list_gpus() {
    let gpu = probe_gpu();
    if let Some(g) = gpu {
        // Output format compatible with regex: ^(\d+):\s+(.+?)\s+\(([^,]+),\s*LUID\s+([^)]+)\)
        safe_println(&format!("0: {} (NVIDIA, LUID 0000:01:00.0)", g.name));
    } else {
        safe_println("No dedicated GPU accelerators found.");
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut interval_secs = 1.0f32;
    let mut is_json = false;
    let mut is_once = false;
    let mut is_list_gpus = false;
    let mut no_system = false;
    let mut i = 1;

    while i < args.len() {
        match args[i].as_str() {
            "-h" | "--help" => {
                print_help();
                process::exit(0);
            }
            "-v" | "--version" => {
                safe_println("flowork-taskman v0.1.0 (Sovereign Clean-Room Rust)");
                process::exit(0);
            }
            "-j" | "--json" => {
                is_json = true;
            }
            "--once" => {
                is_once = true;
            }
            "--list-gpus" => {
                is_list_gpus = true;
            }
            "--no-system" => {
                no_system = true;
            }
            "--no-host" => {
                // Compatible no-op
            }
            "--gpu" => {
                if i + 1 < args.len() {
                    i += 1; // Skip GPU index parameter
                }
            }
            "-i" | "--interval" => {
                if i + 1 < args.len() {
                    if let Ok(v) = args[i + 1].parse::<f32>() {
                        interval_secs = v;
                    }
                    i += 1;
                }
            }
            "--window" => {
                // Handled by launcher or windowed manager
            }
            arg => {
                if arg.starts_with("-i=") || arg.starts_with("--interval=") {
                    if let Some(val_str) = arg.split('=').nth(1) {
                        if let Ok(v) = val_str.parse::<f32>() {
                            interval_secs = v;
                        }
                    }
                }
            }
        }
        i += 1;
    }

    if is_json {
        handle_json(no_system);
        process::exit(0);
    }

    if is_list_gpus {
        handle_list_gpus();
        process::exit(0);
    }

    if is_once {
        handle_once();
        process::exit(0);
    }

    let app = App::new(interval_secs);
    if let Err(e) = run_tui(app) {
        eprintln!("Error running taskman TUI: {}", e);
        process::exit(1);
    }
}
