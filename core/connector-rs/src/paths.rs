use std::fs::{self, OpenOptions};
use std::path::{Path, PathBuf};

#[derive(Clone, Debug)]
pub struct ConnectorPaths {
    #[allow(dead_code)]
    pub base_dir: PathBuf,
    pub config_dir: PathBuf,
    pub data_dir: PathBuf,
    pub logs_dir: PathBuf,
    pub gui_dir: PathBuf,
}

fn is_dir_writable(dir: &Path) -> bool {
    if !dir.is_dir() {
        return false;
    }
    let probe = dir.join(format!(".write_probe_{}", std::process::id()));
    match OpenOptions::new().create(true).write(true).truncate(true).open(&probe) {
        Ok(_) => {
            let _ = fs::remove_file(&probe);
            true
        }
        Err(_) => false,
    }
}

impl ConnectorPaths {
    pub fn resolve() -> Self {
        let base_dir = Self::resolve_base_dir();
        let config_dir = base_dir.join("config");
        let data_dir = base_dir.join("data");
        let logs_dir = base_dir.join("logs");

        let gui_dir = std::env::var("FLOWORK_GUI_DIR")
            .ok()
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .map(PathBuf::from)
            .unwrap_or_else(|| {
                let candidate = base_dir.join("gui");
                if candidate.is_dir() {
                    candidate
                } else {
                    PathBuf::from("/opt/floworkos/connector/gui")
                }
            });

        let paths = Self {
            base_dir,
            config_dir,
            data_dir,
            logs_dir,
            gui_dir,
        };
        paths.ensure_structure();
        paths
    }

    fn resolve_base_dir() -> PathBuf {
        for var in ["FLOWORK_CONNECTOR_DIR", "MRFLOW_CONNECTOR_DIR"] {
            if let Ok(val) = std::env::var(var) {
                let trimmed = val.trim();
                if !trimmed.is_empty() {
                    return PathBuf::from(trimmed);
                }
            }
        }

        if let Ok(root) = std::env::var("FLOWORK_PORTABLE_ROOT") {
            let trimmed = root.trim();
            if !trimmed.is_empty() {
                return PathBuf::from(trimmed).join("connector");
            }
        }

        if let Ok(app_dir) = std::env::var("FLOWORK_APP_DIR") {
            let p = PathBuf::from(app_dir.trim());
            if p.is_dir() && is_dir_writable(&p) {
                return p.join("connector");
            }
        }

        // Preserve portable /opt/floworkos/connector placement when running as /opt/floworkos/connector/bin/flowork-connector
        if let Ok(exe) = std::env::current_exe() {
            if let Some(bin_dir) = exe.parent() {
                if bin_dir.file_name().and_then(|s| s.to_str()) == Some("bin") {
                    if let Some(parent) = bin_dir.parent() {
                        if (parent.join("data").is_dir() || parent.join("config").is_dir())
                            && is_dir_writable(parent)
                        {
                            return parent.to_path_buf();
                        }
                    }
                }
            }
        }

        let canonical = PathBuf::from("/opt/floworkos/connector");
        if canonical.join("data").join("vault.json").exists() && is_dir_writable(&canonical.join("data")) {
            return canonical;
        }

        let home = dirs::home_dir()
            .or_else(|| std::env::var("HOME").ok().filter(|s| !s.is_empty()).map(PathBuf::from))
            .unwrap_or_else(|| PathBuf::from("/tmp"));
        home.join(".flowork").join("connector")
    }

    pub fn ensure_structure(&self) {
        for dir in [&self.config_dir, &self.data_dir, &self.logs_dir] {
            if let Err(e) = fs::create_dir_all(dir) {
                eprintln!("[Paths] Warning initializing {:?}: {}", dir, e);
            }
        }
    }

    pub fn config_file(&self, name: &str) -> PathBuf {
        self.ensure_structure();
        self.config_dir.join(name)
    }

    pub fn data_file(&self, name: &str) -> PathBuf {
        self.ensure_structure();
        self.data_dir.join(name)
    }

    #[allow(dead_code)]
    pub fn log_file(&self, name: &str) -> PathBuf {
        self.ensure_structure();
        self.logs_dir.join(name)
    }
}
