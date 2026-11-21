use crate::resolve_home_dir;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::env;
use std::fs;
use std::io::Write as _;
use std::os::fd::AsRawFd;
use std::os::unix::fs::OpenOptionsExt;
use std::os::unix::net::UnixStream;
use std::path::{Path, PathBuf};

// x86_64 Linux Landlock Syscall Numbers
pub const SYS_LANDLOCK_CREATE_RULESET: libc::c_long = 444;
pub const SYS_LANDLOCK_ADD_RULE: libc::c_long = 445;
pub const SYS_LANDLOCK_RESTRICT_SELF: libc::c_long = 446;

pub const LANDLOCK_CREATE_RULESET_VERSION: u32 = 1 << 0;
pub const LANDLOCK_RULE_PATH_BENEATH: u32 = 1;

// Filesystem Access Flags (ABI v1..v5)
pub const ACCESS_FS_EXECUTE: u64 = 1 << 0;
pub const ACCESS_FS_WRITE_FILE: u64 = 1 << 1;
pub const ACCESS_FS_READ_FILE: u64 = 1 << 2;
pub const ACCESS_FS_READ_DIR: u64 = 1 << 3;
pub const ACCESS_FS_REMOVE_DIR: u64 = 1 << 4;
pub const ACCESS_FS_REMOVE_FILE: u64 = 1 << 5;
pub const ACCESS_FS_MAKE_CHAR: u64 = 1 << 6;
pub const ACCESS_FS_MAKE_DIR: u64 = 1 << 7;
pub const ACCESS_FS_MAKE_REG: u64 = 1 << 8;
pub const ACCESS_FS_MAKE_SOCK: u64 = 1 << 9;
pub const ACCESS_FS_MAKE_FIFO: u64 = 1 << 10;
pub const ACCESS_FS_MAKE_BLOCK: u64 = 1 << 11;
pub const ACCESS_FS_MAKE_SYM: u64 = 1 << 12;
pub const ACCESS_FS_REFER: u64 = 1 << 13;
pub const ACCESS_FS_TRUNCATE: u64 = 1 << 14;

// Network Access Flags (ABI v4 TCP, ABI v10 UDP)
pub const ACCESS_NET_BIND_TCP: u64 = 1 << 0;
pub const ACCESS_NET_CONNECT_TCP: u64 = 1 << 1;
pub const ACCESS_NET_BIND_UDP: u64 = 1 << 2;
pub const ACCESS_NET_CONNECT_SEND_UDP: u64 = 1 << 3;

const FILE_ONLY_FS_MASK: u64 =
    ACCESS_FS_EXECUTE | ACCESS_FS_WRITE_FILE | ACCESS_FS_READ_FILE | ACCESS_FS_TRUNCATE;

pub const STRIP_SENSITIVE_ENVS: &[&str] = &[
    "GOOGLE_GEMINI_API_KEY",
    "GEMINI_API_KEY",
    "FLOWORK_TOKEN",
    "VAULT_SECRET",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "HF_TOKEN",
    "SSH_AUTH_SOCK",
];

#[repr(C)]
struct LandlockRulesetAttrV1 {
    handled_access_fs: u64,
}

#[repr(C)]
struct LandlockRulesetAttrV4 {
    handled_access_fs: u64,
    handled_access_net: u64,
}

#[repr(C)]
struct LandlockPathBeneathAttr {
    allowed_access: u64,
    parent_fd: i32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "snake_case")]
pub enum CapabilityProfile {
    #[default]
    Strict,
    Standard,
    NetworkOff,
    UnrestrictedTrusted,
}

impl CapabilityProfile {
    pub fn parse_str(s: &str) -> Self {
        match s.trim().to_ascii_lowercase().as_str() {
            "standard" => Self::Standard,
            "network_off" | "offline" => Self::NetworkOff,
            "unrestricted_trusted" | "trusted" => Self::UnrestrictedTrusted,
            _ => Self::Strict,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Strict => "strict",
            Self::Standard => "standard",
            Self::NetworkOff => "network_off",
            Self::UnrestrictedTrusted => "unrestricted_trusted",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppPermissions {
    #[serde(default)]
    pub profile: CapabilityProfile,
    #[serde(default)]
    pub allow_network: bool,
    #[serde(default = "default_true")]
    pub ipc_neural_bus: bool,
    #[serde(default)]
    pub bus_topics_allow: Vec<String>,
    #[serde(default)]
    pub read_paths: Vec<String>,
    #[serde(default)]
    pub write_paths: Vec<String>,
}

fn default_true() -> bool {
    true
}

impl Default for AppPermissions {
    fn default() -> Self {
        Self {
            profile: CapabilityProfile::Strict,
            allow_network: false,
            ipc_neural_bus: true,
            bus_topics_allow: Vec::new(),
            read_paths: Vec::new(),
            write_paths: Vec::new(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct SandboxPlan {
    pub app_id: String,
    pub app_dir: Option<PathBuf>,
    pub data_dir: PathBuf,
    pub tmp_dir: PathBuf,
    pub permissions: AppPermissions,
    pub read_only_paths: Vec<PathBuf>,
    pub read_write_paths: Vec<PathBuf>,
    pub rejected_paths: Vec<String>,
    pub hard_deny_paths: Vec<PathBuf>,
    pub abi: i64,
    pub block_network: bool,
}

pub fn probe_landlock_abi() -> i64 {
    unsafe {
        libc::syscall(
            SYS_LANDLOCK_CREATE_RULESET,
            std::ptr::null::<LandlockRulesetAttrV1>(),
            0,
            LANDLOCK_CREATE_RULESET_VERSION,
        ) as i64
    }
}

pub fn handled_fs_for_abi(abi: i64) -> u64 {
    if abi <= 0 {
        return 0;
    }
    let mut mask = ACCESS_FS_EXECUTE
        | ACCESS_FS_WRITE_FILE
        | ACCESS_FS_READ_FILE
        | ACCESS_FS_READ_DIR
        | ACCESS_FS_REMOVE_DIR
        | ACCESS_FS_REMOVE_FILE
        | ACCESS_FS_MAKE_CHAR
        | ACCESS_FS_MAKE_DIR
        | ACCESS_FS_MAKE_REG
        | ACCESS_FS_MAKE_SOCK
        | ACCESS_FS_MAKE_FIFO
        | ACCESS_FS_MAKE_BLOCK
        | ACCESS_FS_MAKE_SYM;
    if abi >= 2 {
        mask |= ACCESS_FS_REFER;
    }
    if abi >= 3 {
        mask |= ACCESS_FS_TRUNCATE;
    }
    mask
}

pub fn handled_net_for_abi(abi: i64) -> u64 {
    if abi >= 10 {
        ACCESS_NET_BIND_TCP
            | ACCESS_NET_CONNECT_TCP
            | ACCESS_NET_BIND_UDP
            | ACCESS_NET_CONNECT_SEND_UDP
    } else if abi >= 4 {
        ACCESS_NET_BIND_TCP | ACCESS_NET_CONNECT_TCP
    } else {
        0
    }
}

pub fn hard_deny_invariants(home: &Path) -> Vec<PathBuf> {
    vec![
        PathBuf::from("/opt/floworkos/connector/data"),
        PathBuf::from("/opt/floworkos/connector/data/vault.json"),
        home.join(".ssh"),
        home.join(".gnupg"),
        home.join(".aws"),
        home.join("Downloads/token"),
        home.join(".git-credentials"),
    ]
}

fn expand_sandbox_path(raw: &str, home: &Path, app_dir: Option<&Path>, data_dir: &Path) -> PathBuf {
    let mut s = raw.trim().to_string();
    if let Some(rest) = s.strip_prefix("~/") {
        s = home.join(rest).to_string_lossy().to_string();
    } else if s == "~" {
        s = home.to_string_lossy().to_string();
    }
    s = s.replace("$HOME", &home.to_string_lossy());
    s = s.replace("$DATA_DIR", &data_dir.to_string_lossy());
    if let Some(ad) = app_dir {
        s = s.replace("$APP_DIR", &ad.to_string_lossy());
    }
    PathBuf::from(s)
}

fn is_hard_denied(candidate: &Path, deny_list: &[PathBuf]) -> bool {
    let cand_norm = fs::canonicalize(candidate).unwrap_or_else(|_| candidate.to_path_buf());
    for deny in deny_list {
        let deny_norm = fs::canonicalize(deny).unwrap_or_else(|_| deny.clone());
        // Block if candidate equals/is inside denied dir, or is an ancestor like $HOME or /opt/floworkos that would expose it
        if cand_norm == deny_norm
            || cand_norm.starts_with(&deny_norm)
            || deny_norm.starts_with(&cand_norm)
        {
            return true;
        }
    }
    false
}

pub fn load_app_permissions(
    app_id: &str,
    manifest_override: Option<&Path>,
    profile_override: Option<CapabilityProfile>,
) -> (AppPermissions, Option<PathBuf>) {
    let default_app_dir = PathBuf::from("/opt/floworkos/apps").join(app_id);
    let mut app_dir = if default_app_dir.is_dir() {
        Some(default_app_dir.clone())
    } else {
        None
    };

    let manifest_candidates: Vec<PathBuf> = if let Some(ov) = manifest_override {
        if let Some(p) = ov.parent() {
            if app_dir.is_none() && p.is_dir() {
                app_dir = Some(p.to_path_buf());
            }
        }
        vec![ov.to_path_buf()]
    } else {
        vec![
            default_app_dir.join("manifest.json"),
            default_app_dir.join("app.json"),
        ]
    };

    let mut perms = AppPermissions::default();

    for mp in manifest_candidates {
        if !mp.is_file() {
            continue;
        }
        if let Ok(raw) = fs::read_to_string(&mp) {
            if let Ok(val) = serde_json::from_str::<Value>(&raw) {
                let block = val.get("permissions").or_else(|| val.get("sandbox"));
                if let Some(obj) = block.and_then(|v| v.as_object()) {
                    if let Some(pstr) = obj.get("profile").and_then(|v| v.as_str()) {
                        perms.profile = CapabilityProfile::parse_str(pstr);
                    }
                    if let Some(net) = obj.get("allow_network").and_then(|v| v.as_bool()) {
                        perms.allow_network = net;
                    }
                    if let Some(ipc) = obj.get("ipc_neural_bus").and_then(|v| v.as_bool()) {
                        perms.ipc_neural_bus = ipc;
                    }
                    if let Some(arr) = obj.get("bus_topics_allow").and_then(|v| v.as_array()) {
                        perms.bus_topics_allow = arr
                            .iter()
                            .filter_map(|v| v.as_str().map(str::to_string))
                            .collect();
                    }
                    if let Some(arr) = obj.get("read_paths").and_then(|v| v.as_array()) {
                        perms.read_paths = arr
                            .iter()
                            .filter_map(|v| v.as_str().map(str::to_string))
                            .collect();
                    }
                    if let Some(arr) = obj.get("write_paths").and_then(|v| v.as_array()) {
                        perms.write_paths = arr
                            .iter()
                            .filter_map(|v| v.as_str().map(str::to_string))
                            .collect();
                    }
                    break;
                } else {
                    // Manifest present without explicit permissions: enforce strict by default
                    perms.profile = CapabilityProfile::Strict;
                }
            }
        }
    }

    if let Some(prof) = profile_override {
        perms.profile = prof;
    }

    if perms.profile == CapabilityProfile::NetworkOff {
        perms.allow_network = false;
    }

    // Merge Tier-5 admin deny overrides from /etc/flowork/policies/*.toml or /opt/floworkos/policies/sandbox-default.toml
    for pol in [
        Path::new("/etc/flowork/policies/sandbox.toml"),
        Path::new("/opt/floworkos/policies/sandbox-default.toml"),
    ] {
        if let Ok(raw) = fs::read_to_string(pol) {
            if let Ok(doc) = toml::from_str::<toml::Value>(&raw) {
                let top_force = doc.get("force_allow_network").and_then(|v| v.as_bool());
                let sub_force = doc
                    .get("sandbox")
                    .and_then(|s| s.get("force_allow_network"))
                    .and_then(|v| v.as_bool());
                if top_force == Some(false) || sub_force == Some(false) {
                    perms.allow_network = false;
                }
            }
        }
    }

    (perms, app_dir)
}

pub fn build_sandbox_plan(
    app_id: &str,
    manifest_override: Option<&Path>,
    profile_override: Option<CapabilityProfile>,
) -> SandboxPlan {
    let home = resolve_home_dir();
    let (perms, app_dir) = load_app_permissions(app_id, manifest_override, profile_override);

    let safe_id: String = app_id
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '-' || c == '_' {
                c
            } else {
                '_'
            }
        })
        .collect();
    let data_dir = home.join(".flowork/data").join(&safe_id);
    let tmp_dir = PathBuf::from(format!("/tmp/flowork_app_{}", safe_id));
    let _ = fs::create_dir_all(&data_dir);
    let _ = fs::create_dir_all(&tmp_dir);
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = fs::set_permissions(&data_dir, fs::Permissions::from_mode(0o700));
        let _ = fs::set_permissions(&tmp_dir, fs::Permissions::from_mode(0o700));
    }

    let hard_deny = hard_deny_invariants(&home);
    let abi = probe_landlock_abi();

    let mut ro_paths: Vec<PathBuf> = vec![
        PathBuf::from("/usr"),
        PathBuf::from("/bin"),
        PathBuf::from("/sbin"),
        PathBuf::from("/lib"),
        PathBuf::from("/lib64"),
        PathBuf::from("/lib32"),
        PathBuf::from("/etc"),
        PathBuf::from("/proc"),
        PathBuf::from("/sys"),
        PathBuf::from("/var/cache/fontconfig"),
        PathBuf::from("/var/lib/dbus"),
        PathBuf::from("/run/dbus"),
        PathBuf::from("/run/udev"),
        PathBuf::from("/run/systemd/resolve"),
        PathBuf::from("/opt/floworkos/bin"),
        PathBuf::from("/opt/floworkos/lib"),
        PathBuf::from("/opt/floworkos/theme"),
        PathBuf::from("/opt/floworkos/icons"),
        PathBuf::from("/opt/floworkos/system"),
        PathBuf::from("/opt/floworkos/connector/flowfs_core.py"),
        home.join(".Xauthority"),
        home.join(".config/fontconfig"),
        home.join(".config/gtk-3.0"),
        home.join(".local/share/icons"),
        home.join(".local/share/fonts"),
        home.join(".themes"),
    ];

    if let Ok(xauth) = env::var("XAUTHORITY") {
        let p = PathBuf::from(xauth.trim());
        if p.exists() && !is_hard_denied(&p, &hard_deny) {
            ro_paths.push(p);
        }
    }

    if let Some(ref ad) = app_dir {
        ro_paths.push(ad.clone());
    }

    let webkit_data = home.join(".local/share/webkitgtk");
    let webkit_cfg = home.join(".config/webkitgtk");
    let gst_cache = home.join(".local/share/gstreamer-1.0");
    let nv_cache = home.join(".nv");
    let _ = fs::create_dir_all(&webkit_data);
    let _ = fs::create_dir_all(&webkit_cfg);

    let mut rw_paths: Vec<PathBuf> = vec![
        data_dir.clone(),
        tmp_dir.clone(),
        PathBuf::from("/tmp/.X11-unix"),
        PathBuf::from("/tmp/.XIM-unix"),
        PathBuf::from("/tmp/.ICE-unix"),
        PathBuf::from("/dev/null"),
        PathBuf::from("/dev/zero"),
        PathBuf::from("/dev/full"),
        PathBuf::from("/dev/urandom"),
        PathBuf::from("/dev/random"),
        PathBuf::from("/dev/shm"),
        PathBuf::from("/dev/dri"),
        PathBuf::from("/dev/nvidia0"),
        PathBuf::from("/dev/nvidia1"),
        PathBuf::from("/dev/nvidiactl"),
        PathBuf::from("/dev/nvidia-modeset"),
        PathBuf::from("/dev/nvidia-uvm"),
        PathBuf::from("/dev/nvidia-uvm-tools"),
        PathBuf::from("/dev/nvidia-caps"),
        PathBuf::from("/dev/dma_heap"),
        PathBuf::from("/dev/udmabuf"),
        PathBuf::from("/dev/tty"),
        PathBuf::from("/dev/pts"),
        home.join(".cache"),
        home.join(".config/dconf"),
        webkit_data,
        webkit_cfg,
        gst_cache,
        nv_cache,
    ];

    if let Ok(xdg_rt) = env::var("XDG_RUNTIME_DIR") {
        let p = PathBuf::from(xdg_rt.trim());
        if p.exists() && !is_hard_denied(&p, &hard_deny) {
            rw_paths.push(p);
        }
    }

    if perms.ipc_neural_bus {
        rw_paths.push(PathBuf::from("/run/flowork"));
        rw_paths.push(home.join(".flowork/bus.sock"));
    }

    if perms.profile == CapabilityProfile::Standard {
        // Standard apps can read shared non-secret asset roots
        ro_paths.push(PathBuf::from("/opt/floworkos/pipelines"));
    }

    let mut rejected = Vec::new();
    for raw_r in &perms.read_paths {
        let expanded = expand_sandbox_path(raw_r, &home, app_dir.as_deref(), &data_dir);
        if is_hard_denied(&expanded, &hard_deny) {
            rejected.push(format!("read_path denied: {}", raw_r));
        } else if expanded.exists() {
            if let Ok(canon) = fs::canonicalize(&expanded) {
                if !is_hard_denied(&canon, &hard_deny) {
                    ro_paths.push(canon);
                } else {
                    rejected.push(format!("symlink escape denied: {}", raw_r));
                }
            }
        }
    }

    for raw_w in &perms.write_paths {
        let expanded = expand_sandbox_path(raw_w, &home, app_dir.as_deref(), &data_dir);
        if is_hard_denied(&expanded, &hard_deny) {
            rejected.push(format!("write_path denied: {}", raw_w));
        } else {
            if !expanded.exists() {
                let _ = fs::create_dir_all(&expanded);
            }
            if let Ok(canon) = fs::canonicalize(&expanded) {
                if !is_hard_denied(&canon, &hard_deny) {
                    rw_paths.push(canon);
                } else {
                    rejected.push(format!("symlink write escape denied: {}", raw_w));
                }
            }
        }
    }

    // Deduplicate existing canonical paths while enforcing hard-deny filter
    ro_paths.retain(|p| p.exists() && !is_hard_denied(p, &hard_deny));
    rw_paths.retain(|p| p.exists() && !is_hard_denied(p, &hard_deny));

    let block_network = !perms.allow_network && perms.profile != CapabilityProfile::UnrestrictedTrusted;

    SandboxPlan {
        app_id: safe_id,
        app_dir,
        data_dir,
        tmp_dir,
        permissions: perms,
        read_only_paths: ro_paths,
        read_write_paths: rw_paths,
        rejected_paths: rejected,
        hard_deny_paths: hard_deny,
        abi,
        block_network,
    }
}

fn add_path_rule_raw(ruleset_fd: i32, path: &Path, dir_access: u64, handled_fs: u64) {
    if !path.exists() {
        return;
    }
    let effective = if path.is_dir() {
        dir_access & handled_fs
    } else {
        dir_access & FILE_ONLY_FS_MASK & handled_fs
    };
    if effective == 0 {
        return;
    }
    if let Ok(file) = fs::OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_PATH | libc::O_CLOEXEC)
        .open(path)
    {
        let attr = LandlockPathBeneathAttr {
            allowed_access: effective,
            parent_fd: file.as_raw_fd(),
        };
        unsafe {
            libc::syscall(
                SYS_LANDLOCK_ADD_RULE,
                ruleset_fd,
                LANDLOCK_RULE_PATH_BENEATH,
                &attr as *const _,
                0,
            );
        }
    }
}

pub fn create_ruleset_for_plan(plan: &SandboxPlan) -> Result<Option<i32>, String> {
    if plan.permissions.profile == CapabilityProfile::UnrestrictedTrusted {
        return Ok(None);
    }
    if plan.abi <= 0 {
        return Err(format!(
            "Kernel Landlock LSM unsupported (abi={})",
            plan.abi
        ));
    }

    let handled_fs = handled_fs_for_abi(plan.abi);
    let handled_net = if plan.block_network {
        handled_net_for_abi(plan.abi)
    } else {
        0
    };

    let ruleset_fd = if plan.abi >= 4 && handled_net != 0 {
        let attr = LandlockRulesetAttrV4 {
            handled_access_fs: handled_fs,
            handled_access_net: handled_net,
        };
        unsafe {
            libc::syscall(
                SYS_LANDLOCK_CREATE_RULESET,
                &attr as *const _,
                std::mem::size_of::<LandlockRulesetAttrV4>(),
                0,
            ) as i32
        }
    } else {
        let attr = LandlockRulesetAttrV1 {
            handled_access_fs: handled_fs,
        };
        unsafe {
            libc::syscall(
                SYS_LANDLOCK_CREATE_RULESET,
                &attr as *const _,
                std::mem::size_of::<LandlockRulesetAttrV1>(),
                0,
            ) as i32
        }
    };

    if ruleset_fd < 0 {
        return Err(format!(
            "landlock_create_ruleset failed: {}",
            std::io::Error::last_os_error()
        ));
    }

    let ro_mask = ACCESS_FS_EXECUTE | ACCESS_FS_READ_FILE | ACCESS_FS_READ_DIR;
    for p in &plan.read_only_paths {
        add_path_rule_raw(ruleset_fd, p, ro_mask, handled_fs);
    }
    for p in &plan.read_write_paths {
        add_path_rule_raw(ruleset_fd, p, handled_fs, handled_fs);
    }

    Ok(Some(ruleset_fd))
}

/// Apply Landlock ruleset inside child `pre_exec` hook (async-signal-safe).
///
/// # Safety
/// Must only be called in single-threaded child context before `execve`.
pub unsafe fn restrict_self_raw(ruleset_fd: i32) -> Result<(), i32> {
    if libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0 {
        return Err(*libc::__errno_location());
    }
    if libc::syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0) < 0 {
        return Err(*libc::__errno_location());
    }
    libc::close(ruleset_fd);
    Ok(())
}

pub fn publish_sandbox_violation(app_id: &str, profile: &str, detail: &str) {
    let home = resolve_home_dir();
    let home_sock = home.join(".flowork/bus.sock");
    let msg = json!({
        "type": "security.sandbox.denied",
        "source": "flowork-sandbox-exec",
        "target": app_id,
        "action": "landlock_denied",
        "payload": {
            "app_id": app_id,
            "profile": profile,
            "detail": detail.chars().take(300).collect::<String>()
        }
    });
    let line = format!("{}\n", msg);

    for cand in [
        Path::new("/run/flowork/bus.sock"),
        Path::new("/tmp/flowork-neural-bus.sock"),
        home_sock.as_path(),
    ] {
        if cand.exists() {
            if let Ok(mut stream) = UnixStream::connect(cand) {
                let _ = stream.write_all(line.as_bytes());
                break;
            }
        }
    }

    if env::var("DISPLAY").is_ok() && env::var("FLOWORK_NO_TOAST").is_err() {
        let _ = std::process::Command::new("notify-send")
            .args([
                "-u",
                "normal",
                "-i",
                "security-high",
                "Flowork Kernel Landlock Jail",
                &format!(
                    "App '{}' attempted restricted access and was blocked by kernel (profile={}).",
                    app_id, profile
                ),
            ])
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .spawn();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hard_deny_prevents_vault_and_ssh_exposure() {
        let home = resolve_home_dir();
        let deny = hard_deny_invariants(&home);
        assert!(is_hard_denied(
            Path::new("/opt/floworkos/connector/data/vault.json"),
            &deny
        ));
        assert!(is_hard_denied(Path::new("/opt/floworkos"), &deny));
        assert!(is_hard_denied(&home.join(".ssh"), &deny));
        assert!(is_hard_denied(&home, &deny));
        assert!(!is_hard_denied(Path::new("/opt/floworkos/bin"), &deny));
        assert!(!is_hard_denied(&home.join(".flowork/data/test_app"), &deny));
    }

    #[test]
    fn test_strict_plan_defaults_for_unknown_app() {
        let plan = build_sandbox_plan("unknown_crafted_app", None, None);
        assert_eq!(plan.permissions.profile, CapabilityProfile::Strict);
        assert!(!plan.permissions.allow_network);
        assert!(plan.block_network);
        assert!(!plan
            .read_only_paths
            .iter()
            .any(|p| p == Path::new("/opt/floworkos/connector/data")));
    }
}
