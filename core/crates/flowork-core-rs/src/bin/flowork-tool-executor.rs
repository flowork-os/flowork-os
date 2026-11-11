use flowork_core_rs::DEFAULT_TOOLS_DIR;
use std::env;
use std::io::{Read, Write};
use std::path::PathBuf;
use std::process::{self, Command, Stdio};

fn print_help() {
    println!("flowork-tool-executor — Sovereign Native Tool Dispatcher");
    println!("Usage: flowork-tool-executor [--check] [--help] <tool_name>");
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if let Some(first) = args.first() {
        match first.as_str() {
            "--help" | "-h" => {
                print_help();
                return;
            }
            "--check" => {
                println!("flowork-tool-executor: OK (native Rust)");
                return;
            }
            _ => {}
        }
    }

    let tool_name = args
        .first()
        .cloned()
        .or_else(|| env::var("FLOWORK_TOOL_NAME").ok())
        .unwrap_or_default();

    if tool_name.is_empty() {
        eprintln!("Error: Tool name argument missing.");
        process::exit(1);
    }

    let mut input_data = String::new();
    let _ = std::io::stdin().read_to_string(&mut input_data);
    if input_data.is_empty() {
        input_data = "{}".to_string();
    }

    let tools_dir = env::var("FLOWORK_TOOLS_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from(DEFAULT_TOOLS_DIR));
    let tool_dir = tools_dir.join(&tool_name);
    if !tool_dir.exists() {
        eprintln!(
            "Error: Tool '{}' not found in {}",
            tool_name,
            tools_dir.display()
        );
        process::exit(1);
    }

    let bin_run = tool_dir.join("run");
    let sh_run = tool_dir.join("run.sh");
    let py_run = tool_dir.join("run.py");

    let (cmd, cmd_args): (String, Vec<String>) = if bin_run.is_file() {
        (bin_run.to_string_lossy().to_string(), vec![])
    } else if sh_run.is_file() {
        (
            "/bin/bash".to_string(),
            vec![sh_run.to_string_lossy().to_string()],
        )
    } else if py_run.is_file() {
        (
            "/usr/bin/python3".to_string(),
            vec![py_run.to_string_lossy().to_string()],
        )
    } else {
        eprintln!(
            "Error: No executable handler (run, run.sh, run.py) found for tool '{}'.",
            tool_name
        );
        process::exit(1);
    };

    let mut child = match Command::new(&cmd)
        .args(&cmd_args)
        .env("FLOWORK_TOOL_NAME", &tool_name)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(c) => c,
        Err(e) => {
            eprintln!("Execution error: {}", e);
            process::exit(1);
        }
    };

    if let Some(mut stdin) = child.stdin.take() {
        let _ = stdin.write_all(input_data.as_bytes());
    }

    let out = match child.wait_with_output() {
        Ok(o) => o,
        Err(e) => {
            eprintln!("Fatal dispatch error: {}", e);
            process::exit(1);
        }
    };

    let code = out.status.code().unwrap_or(1);
    if !out.status.success() && !out.stderr.is_empty() {
        let _ = std::io::stderr().write_all(&out.stderr);
        process::exit(code);
    }

    if out.stdout.is_empty() {
        print!("{{\"status\": \"ok\"}}");
    } else {
        let _ = std::io::stdout().write_all(&out.stdout);
    }
    if !out.status.success() {
        process::exit(code);
    }
}
