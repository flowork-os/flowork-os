use std::process::{Command, exit};

fn main() {
    // Probe active window title via xdotool if available
    if let Ok(res) = Command::new("xdotool").args(["getwindowfocus", "getwindowname"]).output() {
        let title = String::from_utf8_lossy(&res.stdout).to_lowercase();
        if title.contains("word")
            || title.contains("writer")
            || title.contains("document")
            || title.contains("libreoffice")
            || title.contains("notepad")
        {
            exit(0);
        }
    }

    // Fallback: probe active document processes
    #[cfg(unix)]
    {
        if let Ok(res) = Command::new("pgrep").args(["-f", "soffice.bin|libreoffice|wps|winword"]).output() {
            if res.status.success() && !res.stdout.is_empty() {
                exit(0);
            }
        }
    }

    exit(1);
}
