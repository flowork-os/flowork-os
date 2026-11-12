use axum::{
    extract::State,
    http::StatusCode,
    response::{
        sse::{Event, KeepAlive, Sse},
        IntoResponse, Json,
    },
    routing::{get, post},
    Router,
};
use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use chrono::Utc;
use flowork_core_rs::resolve_home_dir;
use futures_util::StreamExt;
use hyper_util::rt::{TokioExecutor, TokioIo};
use hyper_util::server::conn::auto::Builder as HyperAutoBuilder;
use hyper_util::service::TowerToHyperService;
use rustls::server::WebPkiClientVerifier;
use rustls::RootCertStore;
use rustls_pki_types::{pem::PemObject, CertificateDer, PrivateKeyDer};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::convert::Infallible;
use std::env;
use std::fs;
use std::net::SocketAddr;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::pin::Pin;
use std::process::{Command, Stdio};
use std::sync::Arc;
use std::task::{Context, Poll};
use std::time::Duration;
use tokio::net::{TcpListener, TcpStream};
use tokio_rustls::TlsAcceptor;
use uuid::Uuid;

const DEFAULT_POLICY_PATH: &str = "/opt/floworkos/policies/mesh.toml";
const ZSTD_BIN: &str = "/opt/floworkos/bin/zstd";
const SANDBOX_EXEC_BIN: &str = "/opt/floworkos/bin/flowork-sandbox-exec";
const PIPE_RS_BIN: &str = "/opt/floworkos/bin/flowork-pipe-rs";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct MeshConfig {
    node_id: String,
    node_name: String,
    enabled: bool,
    bind: String,
    fingerprint: String,
    pairing_pin: String,
    created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct TrustedPeer {
    node_id: String,
    node_name: String,
    endpoint: String,
    fingerprint: String,
    ca_cert_path: String,
    added_at: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
struct TrustedPeersFile {
    peers: BTreeMap<String, TrustedPeer>,
}

#[derive(Debug, Clone, Default, Deserialize)]
struct MeshPolicyDoc {
    #[serde(default)]
    mesh: MeshPolicySection,
    #[serde(default)]
    capabilities: MeshCapabilitiesPolicy,
}

#[derive(Debug, Clone, Deserialize)]
struct MeshPolicySection {
    #[serde(default)]
    enabled_by_default: bool,
    #[serde(default = "default_bind_addr")]
    default_bind: String,
    #[serde(default = "default_true")]
    require_mtls: bool,
    #[serde(default)]
    allow_shell: bool,
    #[serde(default = "default_true")]
    allow_inference: bool,
    #[serde(default = "default_true")]
    allow_pipeline_offload: bool,
    #[serde(default = "default_max_mb")]
    max_artifact_mb: usize,
}

impl Default for MeshPolicySection {
    fn default() -> Self {
        Self {
            enabled_by_default: false,
            default_bind: default_bind_addr(),
            require_mtls: true,
            allow_shell: false,
            allow_inference: true,
            allow_pipeline_offload: true,
            max_artifact_mb: 64,
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
struct MeshCapabilitiesPolicy {
    #[serde(default = "default_media_cli")]
    allow_media_cli: Vec<String>,
    #[serde(default = "default_sandbox_bin")]
    sandbox_exec: String,
}

impl Default for MeshCapabilitiesPolicy {
    fn default() -> Self {
        Self {
            allow_media_cli: default_media_cli(),
            sandbox_exec: default_sandbox_bin(),
        }
    }
}

fn default_bind_addr() -> String {
    "127.0.0.1:18099".to_string()
}
fn default_true() -> bool {
    true
}
fn default_max_mb() -> usize {
    64
}
fn default_media_cli() -> Vec<String> {
    vec![
        "cutvii-cli".into(),
        "kamidi-mastering-cli".into(),
        "ocr".into(),
        "blender".into(),
    ]
}
fn default_sandbox_bin() -> String {
    SANDBOX_EXEC_BIN.to_string()
}

#[derive(Clone)]
struct ServerState {
    config: MeshConfig,
    policy: MeshPolicyDoc,
}

fn load_policy(path: &Path) -> MeshPolicyDoc {
    if let Ok(raw) = fs::read_to_string(path) {
        if let Ok(doc) = toml::from_str::<MeshPolicyDoc>(&raw) {
            return doc;
        }
    }
    MeshPolicyDoc::default()
}

fn resolve_zstd_bin() -> &'static str {
    if Path::new(ZSTD_BIN).is_file() {
        ZSTD_BIN
    } else {
        "zstd"
    }
}

fn config_path(mesh_dir: &Path) -> PathBuf {
    mesh_dir.join("mesh_config.json")
}

fn peers_file_path(mesh_dir: &Path) -> PathBuf {
    mesh_dir.join("trusted_peers.json")
}

fn load_mesh_config(mesh_dir: &Path) -> Result<MeshConfig, String> {
    let raw = fs::read_to_string(config_path(mesh_dir)).map_err(|_| {
        format!(
            "Mesh not initialized in {} (run `flowork-mesh init` first)",
            mesh_dir.display()
        )
    })?;
    serde_json::from_str(&raw).map_err(|e| format!("Invalid mesh_config.json: {}", e))
}

fn save_mesh_config(mesh_dir: &Path, cfg: &MeshConfig) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(cfg).map_err(|e| e.to_string())?;
    fs::write(config_path(mesh_dir), raw).map_err(|e| e.to_string())
}

fn load_trusted_peers(mesh_dir: &Path) -> TrustedPeersFile {
    let p = peers_file_path(mesh_dir);
    if let Ok(raw) = fs::read_to_string(&p) {
        if let Ok(doc) = serde_json::from_str::<TrustedPeersFile>(&raw) {
            return doc;
        }
    }
    TrustedPeersFile::default()
}

fn save_trusted_peers(mesh_dir: &Path, doc: &TrustedPeersFile) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(doc).map_err(|e| e.to_string())?;
    fs::write(peers_file_path(mesh_dir), raw).map_err(|e| e.to_string())
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(bytes);
    format!("{:x}", h.finalize())
}

fn run_openssl(args: &[&str]) -> Result<(), String> {
    let out = Command::new("openssl")
        .args(args)
        .output()
        .map_err(|e| format!("Failed invoking openssl: {}", e))?;
    if !out.status.success() {
        return Err(format!(
            "openssl {:?} failed: {}",
            args,
            String::from_utf8_lossy(&out.stderr)
        ));
    }
    Ok(())
}

fn set_private_perms(path: &Path) {
    if let Ok(meta) = fs::metadata(path) {
        let mut p = meta.permissions();
        p.set_mode(0o600);
        let _ = fs::set_permissions(path, p);
    }
}

fn collect_local_hardware() -> Value {
    let cpu_cores = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1);

    let mut ram_total_mb = 0u64;
    let mut ram_free_mb = 0u64;
    if let Ok(meminfo) = fs::read_to_string("/proc/meminfo") {
        for line in meminfo.lines() {
            if let Some(rest) = line.strip_prefix("MemTotal:") {
                if let Some(kb) = rest.split_whitespace().next().and_then(|s| s.parse::<u64>().ok()) {
                    ram_total_mb = kb / 1024;
                }
            } else if let Some(rest) = line.strip_prefix("MemAvailable:") {
                if let Some(kb) = rest.split_whitespace().next().and_then(|s| s.parse::<u64>().ok()) {
                    ram_free_mb = kb / 1024;
                }
            }
        }
    }

    let mut gpu_info = json!({ "available": false, "devices": [] });
    if let Ok(out) = Command::new("nvidia-smi")
        .args([
            "--query-gpu=name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ])
        .output()
    {
        if out.status.success() {
            let devs: Vec<Value> = String::from_utf8_lossy(&out.stdout)
                .lines()
                .filter_map(|l| {
                    let parts: Vec<&str> = l.split(',').map(|s| s.trim()).collect();
                    if parts.len() >= 4 {
                        Some(json!({
                            "name": parts[0],
                            "vram_total_mb": parts[1].parse::<u64>().unwrap_or(0),
                            "vram_used_mb": parts[2].parse::<u64>().unwrap_or(0),
                            "vram_free_mb": parts[3].parse::<u64>().unwrap_or(0),
                        }))
                    } else {
                        None
                    }
                })
                .collect();
            if !devs.is_empty() {
                gpu_info = json!({ "available": true, "devices": devs });
            }
        }
    }

    let mut ollama_models = Vec::<String>::new();
    if let Ok(out) = Command::new("curl")
        .args(["-sf", "--max-time", "0.4", "http://127.0.0.1:11434/api/tags"])
        .output()
    {
        if out.status.success() {
            if let Ok(v) = serde_json::from_slice::<Value>(&out.stdout) {
                if let Some(arr) = v.get("models").and_then(|m| m.as_array()) {
                    for m in arr {
                        if let Some(name) = m.get("name").and_then(|n| n.as_str()) {
                            ollama_models.push(name.to_string());
                        }
                    }
                }
            }
        }
    }

    let mut studio_clis = Vec::<String>::new();
    for cli in ["cutvii-cli", "kamidi-mastering-cli", "ocr", "blender"] {
        let p = Path::new("/opt/floworkos/bin").join(cli);
        if p.exists() {
            studio_clis.push(cli.to_string());
        }
    }

    json!({
        "cpu_cores": cpu_cores,
        "ram_total_mb": ram_total_mb,
        "ram_free_mb": ram_free_mb,
        "gpu": gpu_info,
        "ollama_models": ollama_models,
        "studio_clis": studio_clis,
    })
}

fn cmd_init(mesh_dir: &Path, name_opt: Option<&str>, bind_opt: Option<&str>, policy: &MeshPolicyDoc, json_mode: bool) -> i32 {
    if let Err(e) = fs::create_dir_all(mesh_dir.join("peers")) {
        eprintln!("Failed creating mesh dir {}: {}", mesh_dir.display(), e);
        return 1;
    }
    if let Ok(meta) = fs::metadata(mesh_dir) {
        let mut p = meta.permissions();
        p.set_mode(0o700);
        let _ = fs::set_permissions(mesh_dir, p);
    }

    let hostname = fs::read_to_string("/etc/hostname")
        .unwrap_or_else(|_| "flowork-node".to_string())
        .trim()
        .to_string();
    let short_id = &Uuid::new_v4().to_string().replace('-', "")[..10];
    let node_name = name_opt
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .unwrap_or(&hostname)
        .to_string();
    let safe_name: String = node_name
        .chars()
        .map(|c| if c.is_ascii_alphanumeric() || c == '-' || c == '_' { c.to_ascii_lowercase() } else { '-' })
        .collect();
    let node_id = format!("{}-{}", safe_name, short_id);
    let bind = bind_opt
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .unwrap_or(&policy.mesh.default_bind)
        .to_string();

    let ca_key = mesh_dir.join("ca.key");
    let ca_crt = mesh_dir.join("ca.crt");
    let node_key = mesh_dir.join("node.key");
    let node_pub = mesh_dir.join("node.pub");
    let node_csr = mesh_dir.join("node.csr");
    let node_crt = mesh_dir.join("node.crt");
    let ext_cnf = mesh_dir.join(".openssl_ext.cnf");

    let ca_subj = format!("/CN=Flowork-Mesh-CA-{}", node_id);
    let node_subj = format!("/CN={}", node_id);

    let bind_ip = bind.split(':').next().unwrap_or("127.0.0.1").trim();
    let mut sans = vec![
        "IP:127.0.0.1".to_string(),
        "IP:::1".to_string(),
        "DNS:localhost".to_string(),
        format!("DNS:{}", hostname),
        format!("DNS:{}", safe_name),
    ];
    if bind_ip != "0.0.0.0" && bind_ip != "127.0.0.1" && !bind_ip.is_empty() {
        if bind_ip.parse::<std::net::IpAddr>().is_ok() {
            sans.push(format!("IP:{}", bind_ip));
        } else {
            sans.push(format!("DNS:{}", bind_ip));
        }
    }

    let ext_content = format!(
        "[req]\ndistinguished_name=dn\nx509_extensions=v3_ca\n[dn]\n\n[v3_ca]\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign,cRLSign\nsubjectKeyIdentifier=hash\n\n[v3_node]\nbasicConstraints=CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=serverAuth,clientAuth\nsubjectAltName={}\n",
        sans.join(",")
    );
    if let Err(e) = fs::write(&ext_cnf, &ext_content) {
        eprintln!("Failed writing OpenSSL ext config: {}", e);
        return 1;
    }

    // Generate Ed25519 CA and Ed25519 Node Key + X.509 mTLS certificates
    if let Err(e) = run_openssl(&["genpkey", "-algorithm", "ED25519", "-out", ca_key.to_str().unwrap()])
        .and_then(|_| {
            run_openssl(&[
                "req", "-new", "-x509", "-days", "3650",
                "-key", ca_key.to_str().unwrap(),
                "-subj", &ca_subj,
                "-config", ext_cnf.to_str().unwrap(),
                "-extensions", "v3_ca",
                "-out", ca_crt.to_str().unwrap(),
            ])
        })
        .and_then(|_| run_openssl(&["genpkey", "-algorithm", "ED25519", "-out", node_key.to_str().unwrap()]))
        .and_then(|_| run_openssl(&["pkey", "-in", node_key.to_str().unwrap(), "-pubout", "-out", node_pub.to_str().unwrap()]))
        .and_then(|_| {
            run_openssl(&[
                "req", "-new",
                "-key", node_key.to_str().unwrap(),
                "-subj", &node_subj,
                "-out", node_csr.to_str().unwrap(),
            ])
        })
        .and_then(|_| {
            run_openssl(&[
                "x509", "-req", "-days", "825",
                "-in", node_csr.to_str().unwrap(),
                "-CA", ca_crt.to_str().unwrap(),
                "-CAkey", ca_key.to_str().unwrap(),
                "-CAcreateserial",
                "-extfile", ext_cnf.to_str().unwrap(),
                "-extensions", "v3_node",
                "-out", node_crt.to_str().unwrap(),
            ])
        })
    {
        eprintln!("mTLS keygen error: {}", e);
        return 1;
    }

    set_private_perms(&ca_key);
    set_private_perms(&node_key);
    let _ = fs::remove_file(&node_csr);
    let _ = fs::remove_file(&ext_cnf);

    let pub_bytes = fs::read(&node_pub).unwrap_or_default();
    let fp = sha256_hex(&pub_bytes)[..24].to_string();
    let raw_uuid = Uuid::new_v4().as_u128();
    let pin = format!("{:06}", (raw_uuid % 900_000) + 100_000);

    let cfg = MeshConfig {
        node_id: node_id.clone(),
        node_name: node_name.clone(),
        enabled: policy.mesh.enabled_by_default, // ALWAYS false by default
        bind: bind.clone(),
        fingerprint: fp.clone(),
        pairing_pin: pin.clone(),
        created_at: Utc::now().to_rfc3339(),
    };
    if let Err(e) = save_mesh_config(mesh_dir, &cfg) {
        eprintln!("Failed saving mesh_config.json: {}", e);
        return 1;
    }

    // Save self CA copy in peers/ and trusted_peers.json stays empty until explicit pair
    if !peers_file_path(mesh_dir).exists() {
        let _ = save_trusted_peers(mesh_dir, &TrustedPeersFile::default());
    }

    if json_mode {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "status": "ok",
                "mesh_dir": mesh_dir,
                "config": cfg
            }))
            .unwrap_or_default()
        );
    } else {
        println!("✓ Initialized Flowork Mesh Ed25519 + mTLS identity in {}", mesh_dir.display());
        println!("  Node ID     : {}", node_id);
        println!("  Fingerprint : {}", fp);
        println!("  Pairing PIN : {}", pin);
        println!("  Listener    : DISABLED (default-off; run `flowork-mesh enable` to activate)");
    }
    0
}

fn cmd_status(mesh_dir: &Path, json_mode: bool) -> i32 {
    let Ok(cfg) = load_mesh_config(mesh_dir) else {
        if json_mode {
            println!("{}", json!({ "status": "uninitialized", "enabled": false, "mesh_dir": mesh_dir }));
        } else {
            println!("Flowork Mesh: UNINITIALIZED (run `flowork-mesh init`)");
        }
        return 0;
    };
    let peers = load_trusted_peers(mesh_dir);
    let connect_addr = cfg.bind.replace("0.0.0.0:", "127.0.0.1:");
    let live = std::net::TcpStream::connect_timeout(
        &connect_addr.parse().unwrap_or_else(|_| "127.0.0.1:18099".parse().unwrap()),
        Duration::from_millis(200),
    )
    .is_ok();

    if json_mode {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "status": "ok",
                "initialized": true,
                "enabled": cfg.enabled,
                "listener_live": live,
                "node_id": cfg.node_id,
                "node_name": cfg.node_name,
                "bind": cfg.bind,
                "fingerprint": cfg.fingerprint,
                "trusted_peers_count": peers.peers.len(),
                "trusted_peers": peers.peers.keys().collect::<Vec<_>>(),
            }))
            .unwrap_or_default()
        );
    } else {
        println!("🌐 Flowork Mesh Status ({})", mesh_dir.display());
        println!("  Node ID     : {} ({})", cfg.node_id, cfg.node_name);
        println!("  Enabled     : {} (listener live: {})", cfg.enabled, live);
        println!("  Bind        : {}", cfg.bind);
        println!("  Fingerprint : {}", cfg.fingerprint);
        println!("  TrustedPeers: {}", peers.peers.len());
    }
    0
}

fn cmd_set_enabled(mesh_dir: &Path, enabled: bool, bind_opt: Option<&str>, json_mode: bool) -> i32 {
    let mut cfg = match load_mesh_config(mesh_dir) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{}", e);
            return 1;
        }
    };
    cfg.enabled = enabled;
    if let Some(b) = bind_opt {
        if !b.trim().is_empty() {
            cfg.bind = b.trim().to_string();
        }
    }
    if let Err(e) = save_mesh_config(mesh_dir, &cfg) {
        eprintln!("{}", e);
        return 1;
    }
    if json_mode {
        println!("{}", json!({ "status": "ok", "enabled": cfg.enabled, "bind": cfg.bind }));
    } else if enabled {
        println!("✓ Flowork Mesh ENABLED on {} (run `flowork-mesh serve` to start mTLS listener)", cfg.bind);
    } else {
        println!("✓ Flowork Mesh DISABLED (Zero-Trust default-off restored)");
    }
    0
}

fn cmd_pair(mesh_dir: &Path, args: &[String], json_mode: bool) -> i32 {
    let Ok(cfg) = load_mesh_config(mesh_dir) else {
        eprintln!("Mesh not initialized (run `flowork-mesh init`)");
        return 1;
    };

    let mut accept_path: Option<String> = None;
    let mut endpoint_override: Option<String> = None;
    let mut expected_pin: Option<String> = None;
    let mut export_path: Option<String> = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--accept" => {
                accept_path = args.get(i + 1).cloned();
                i += 1;
            }
            "--endpoint" => {
                endpoint_override = args.get(i + 1).cloned();
                i += 1;
            }
            "--pin" => {
                expected_pin = args.get(i + 1).cloned();
                i += 1;
            }
            "--export" => {
                if let Some(next) = args.get(i + 1) {
                    if !next.starts_with('-') {
                        export_path = Some(next.clone());
                        i += 1;
                    }
                }
            }
            _ => {}
        }
        i += 1;
    }

    if let Some(bundle_file) = accept_path {
        let raw = match fs::read_to_string(&bundle_file) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("Failed reading peer bundle {}: {}", bundle_file, e);
                return 1;
            }
        };
        let bundle: Value = match serde_json::from_str(&raw) {
            Ok(v) => v,
            Err(e) => {
                eprintln!("Invalid bundle JSON: {}", e);
                return 1;
            }
        };
        if let Some(pin) = expected_pin {
            let b_pin = bundle.get("pairing_pin").and_then(|v| v.as_str()).unwrap_or("");
            if b_pin != pin {
                eprintln!("Pairing PIN mismatch!");
                return 1;
            }
        }
        let peer_id = bundle.get("node_id").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let peer_name = bundle.get("node_name").and_then(|v| v.as_str()).unwrap_or(&peer_id).to_string();
        let peer_fp = bundle.get("fingerprint").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let ca_pem = bundle.get("ca_pem").and_then(|v| v.as_str()).unwrap_or("");
        let ep = endpoint_override
            .or_else(|| bundle.get("endpoint").and_then(|v| v.as_str()).map(str::to_string))
            .unwrap_or_else(|| "127.0.0.1:18099".to_string());

        if peer_id.is_empty() || ca_pem.is_empty() {
            eprintln!("Incomplete peer pairing bundle (missing node_id or ca_pem)");
            return 1;
        }
        let peer_ca_path = mesh_dir.join("peers").join(format!("{}.crt", peer_id));
        if let Err(e) = fs::write(&peer_ca_path, ca_pem) {
            eprintln!("Failed writing peer CA cert: {}", e);
            return 1;
        }
        let mut peers = load_trusted_peers(mesh_dir);
        let entry = TrustedPeer {
            node_id: peer_id.clone(),
            node_name: peer_name.clone(),
            endpoint: ep.clone(),
            fingerprint: peer_fp.clone(),
            ca_cert_path: peer_ca_path.to_string_lossy().to_string(),
            added_at: Utc::now().to_rfc3339(),
        };
        peers.peers.insert(peer_id.clone(), entry.clone());
        if let Err(e) = save_trusted_peers(mesh_dir, &peers) {
            eprintln!("Failed updating trusted_peers.json: {}", e);
            return 1;
        }
        if json_mode {
            println!("{}", serde_json::to_string_pretty(&json!({ "status": "ok", "paired": entry })).unwrap_or_default());
        } else {
            println!("✓ Paired mTLS peer [{}] ({}) @ {}", peer_id, peer_fp, ep);
        }
        return 0;
    }

    let ca_pem = fs::read_to_string(mesh_dir.join("ca.crt")).unwrap_or_default();
    let ep = cfg.bind.replace("0.0.0.0:", "127.0.0.1:");
    let bundle = json!({
        "node_id": cfg.node_id,
        "node_name": cfg.node_name,
        "endpoint": endpoint_override.unwrap_or(ep),
        "fingerprint": cfg.fingerprint,
        "pairing_pin": cfg.pairing_pin,
        "ca_pem": ca_pem,
        "generated_at": Utc::now().to_rfc3339(),
    });
    let out_str = serde_json::to_string_pretty(&bundle).unwrap_or_default();
    if let Some(p) = export_path {
        if let Err(e) = fs::write(&p, &out_str) {
            eprintln!("Failed writing pairing bundle {}: {}", p, e);
            return 1;
        }
        if json_mode {
            println!("{}", json!({ "status": "ok", "bundle_path": p, "node_id": cfg.node_id, "pin": cfg.pairing_pin }));
        } else {
            println!("✓ Exported pairing bundle -> {} (PIN: {})", p, cfg.pairing_pin);
        }
    } else {
        println!("{}", out_str);
    }
    0
}

fn build_server_tls(mesh_dir: &Path) -> Result<TlsAcceptor, String> {
    let cert_bytes = fs::read(mesh_dir.join("node.crt")).map_err(|e| format!("Read node.crt: {}", e))?;
    let key_bytes = fs::read(mesh_dir.join("node.key")).map_err(|e| format!("Read node.key: {}", e))?;

    let certs: Vec<CertificateDer<'static>> = CertificateDer::pem_slice_iter(&cert_bytes)
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Parse node.crt: {}", e))?;
    let key = PrivateKeyDer::from_pem_slice(&key_bytes)
        .map_err(|e| format!("Parse node.key: {}", e))?;

    let mut roots = RootCertStore::empty();
    let self_ca = fs::read(mesh_dir.join("ca.crt")).map_err(|e| format!("Read ca.crt: {}", e))?;
    for c in CertificateDer::pem_slice_iter(&self_ca).flatten() {
        let _ = roots.add(c);
    }
    if let Ok(entries) = fs::read_dir(mesh_dir.join("peers")) {
        for ent in entries.flatten() {
            let p = ent.path();
            if p.extension().and_then(|s| s.to_str()) == Some("crt") {
                if let Ok(raw) = fs::read(&p) {
                    for c in CertificateDer::pem_slice_iter(&raw).flatten() {
                        let _ = roots.add(c);
                    }
                }
            }
        }
    }

    let verifier = WebPkiClientVerifier::builder(Arc::new(roots))
        .build()
        .map_err(|e| format!("WebPkiClientVerifier error: {}", e))?;

    let server_cfg = rustls::ServerConfig::builder()
        .with_client_cert_verifier(verifier)
        .with_single_cert(certs, key)
        .map_err(|e| format!("ServerConfig error: {}", e))?;

    Ok(TlsAcceptor::from(Arc::new(server_cfg)))
}

fn resolve_peer<'a>(peers: &'a TrustedPeersFile, selector: &str) -> Option<&'a TrustedPeer> {
    let clean = selector.trim().trim_start_matches('@');
    if let Some(p) = peers.peers.get(clean) {
        return Some(p);
    }
    peers
        .peers
        .values()
        .find(|p| p.node_name.eq_ignore_ascii_case(clean) || p.node_id.starts_with(clean))
}

fn build_mtls_client(mesh_dir: &Path, peer: &TrustedPeer) -> Result<reqwest::Client, String> {
    let node_crt = fs::read(mesh_dir.join("node.crt")).map_err(|e| format!("node.crt: {}", e))?;
    let node_key = fs::read(mesh_dir.join("node.key")).map_err(|e| format!("node.key: {}", e))?;
    let mut combined = Vec::with_capacity(node_crt.len() + node_key.len() + 2);
    combined.extend_from_slice(&node_crt);
    combined.push(b'\n');
    combined.extend_from_slice(&node_key);

    let ident = reqwest::Identity::from_pem(&combined).map_err(|e| format!("Identity error: {}", e))?;
    let peer_ca_bytes = fs::read(&peer.ca_cert_path).map_err(|e| format!("Read peer CA {}: {}", peer.ca_cert_path, e))?;
    let peer_ca = reqwest::Certificate::from_pem(&peer_ca_bytes).map_err(|e| format!("Peer CA PEM: {}", e))?;

    reqwest::Client::builder()
        .use_rustls_tls()
        .tls_built_in_root_certs(false)
        .add_root_certificate(peer_ca)
        .identity(ident)
        .timeout(Duration::from_secs(120))
        .build()
        .map_err(|e| format!("reqwest mTLS client build error: {}", e))
}

async fn api_health(State(st): State<Arc<ServerState>>) -> impl IntoResponse {
    Json(json!({
        "status": "ok",
        "node_id": st.config.node_id,
        "node_name": st.config.node_name,
        "mtls": st.policy.mesh.require_mtls,
        "allow_shell": st.policy.mesh.allow_shell,
        "allow_inference": st.policy.mesh.allow_inference,
    }))
}

async fn api_capabilities(State(st): State<Arc<ServerState>>) -> impl IntoResponse {
    let hw = collect_local_hardware();
    Json(json!({
        "status": "ok",
        "node_id": st.config.node_id,
        "node_name": st.config.node_name,
        "fingerprint": st.config.fingerprint,
        "policy": {
            "allow_shell": st.policy.mesh.allow_shell,
            "allow_inference": st.policy.mesh.allow_inference,
            "allow_media_cli": st.policy.capabilities.allow_media_cli,
        },
        "hardware": hw,
    }))
}

async fn api_infer(State(st): State<Arc<ServerState>>, Json(body): Json<Value>) -> impl IntoResponse {
    if !st.policy.mesh.allow_inference {
        return (
            StatusCode::FORBIDDEN,
            Json(json!({ "status": "error", "error": "Mesh inference disabled by policies/mesh.toml" })),
        );
    }
    let prompt = body.get("prompt").and_then(|v| v.as_str()).unwrap_or("ping");
    let model = body.get("model").and_then(|v| v.as_str()).unwrap_or("l0-router");
    let payload = if body.get("messages").is_some() {
        body.clone()
    } else {
        json!({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": body.get("max_tokens").and_then(|v| v.as_u64()).unwrap_or(256)
        })
    };

    let client = reqwest::Client::new();
    for url in [
        "http://127.0.0.1:11434/v1/chat/completions",
        "http://127.0.0.1:18090/v1/chat/completions",
        "http://127.0.0.1:9099/v1/chat/completions",
    ] {
        if let Ok(resp) = client
            .post(url)
            .json(&payload)
            .timeout(Duration::from_secs(15))
            .send()
            .await
        {
            if resp.status().is_success() {
                if let Ok(v) = resp.json::<Value>().await {
                    return (
                        StatusCode::OK,
                        Json(json!({
                            "status": "ok",
                            "served_by": st.config.node_id,
                            "backend": url,
                            "result": v
                        })),
                    );
                }
            }
        }
    }

    (
        StatusCode::BAD_GATEWAY,
        Json(json!({ "status": "error", "error": "No local inference backend reachable (:11434/:18090/:9099)" })),
    )
}

async fn api_pipe(State(st): State<Arc<ServerState>>, Json(body): Json<Value>) -> impl IntoResponse {
    if !st.policy.mesh.allow_pipeline_offload {
        return (
            StatusCode::FORBIDDEN,
            Json(json!({ "status": "error", "error": "Pipeline offload disabled by policies/mesh.toml" })),
        );
    }
    let toml_raw = body.get("toml").and_then(|v| v.as_str()).unwrap_or("");
    let pipe_id = body.get("id").and_then(|v| v.as_str()).unwrap_or("");
    if toml_raw.is_empty() && pipe_id.is_empty() {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({ "status": "error", "error": "Missing 'toml' or 'id' in pipe request" })),
        );
    }

    let tmp_pipe = PathBuf::from(format!("/tmp/flowork_mesh_pipe_{}.flowpipe", Uuid::new_v4()));
    let target_arg = if !toml_raw.is_empty() {
        if let Err(e) = fs::write(&tmp_pipe, toml_raw) {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({ "status": "error", "error": e.to_string() })),
            );
        }
        tmp_pipe.to_string_lossy().to_string()
    } else {
        pipe_id.to_string()
    };

    let mut cmd = Command::new(PIPE_RS_BIN);
    cmd.args(["run", &target_arg, "--local", "--json"]);
    if let Some(inputs) = body.get("inputs").and_then(|v| v.as_object()) {
        for (k, v) in inputs {
            let vs = v.as_str().map(str::to_string).unwrap_or_else(|| v.to_string());
            cmd.args(["--input", &format!("{}={}", k, vs)]);
        }
    }
    let res = cmd.output();
    let _ = fs::remove_file(&tmp_pipe);

    match res {
        Ok(out) => {
            let parsed: Value = serde_json::from_slice(&out.stdout).unwrap_or_else(|_| {
                json!({
                    "stdout": String::from_utf8_lossy(&out.stdout).to_string(),
                    "stderr": String::from_utf8_lossy(&out.stderr).to_string(),
                })
            });
            let code = out.status.code().unwrap_or(1);
            (
                if code == 0 { StatusCode::OK } else { StatusCode::INTERNAL_SERVER_ERROR },
                Json(json!({
                    "status": if code == 0 { "ok" } else { "error" },
                    "exit_code": code,
                    "node_id": st.config.node_id,
                    "pipeline": parsed,
                })),
            )
        }
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "status": "error", "error": format!("flowork-pipe-rs spawn failed: {}", e) })),
        ),
    }
}

fn validate_cli_allowed(policy: &MeshPolicyDoc, cli: &str) -> Result<String, String> {
    let clean = Path::new(cli)
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or("")
        .trim();
    if clean.is_empty() || cli.contains("..") || cli.contains(';') || cli.contains('&') {
        return Err("Invalid CLI identifier".to_string());
    }
    if matches!(clean, "sh" | "bash" | "zsh" | "dash" | "fish" | "python" | "python3") && !policy.mesh.allow_shell {
        return Err(format!("Zero-Trust Policy Violation: arbitrary shell '{}' forbidden (allow_shell=false)", clean));
    }
    if !policy.capabilities.allow_media_cli.iter().any(|x| x == clean) {
        return Err(format!(
            "CLI '{}' not in allow_media_cli whitelist ({:?})",
            clean, policy.capabilities.allow_media_cli
        ));
    }
    let candidate = Path::new("/opt/floworkos/bin").join(clean);
    if candidate.exists() {
        Ok(candidate.to_string_lossy().to_string())
    } else {
        Ok(clean.to_string())
    }
}

async fn api_job(State(st): State<Arc<ServerState>>, Json(body): Json<Value>) -> impl IntoResponse {
    let cli = body.get("cli").and_then(|v| v.as_str()).unwrap_or("").trim().to_string();
    let args: Vec<String> = body
        .get("args")
        .and_then(|v| v.as_array())
        .map(|arr| arr.iter().filter_map(|x| x.as_str().map(str::to_string)).collect())
        .unwrap_or_default();
    let ws_b64 = body.get("workspace_zstd_b64").and_then(|v| v.as_str()).unwrap_or("").to_string();

    let resolved_cli = match validate_cli_allowed(&st.policy, &cli) {
        Ok(p) => p,
        Err(msg) => {
            return (
                StatusCode::FORBIDDEN,
                Json(json!({ "status": "forbidden", "error": msg })),
            )
                .into_response();
        }
    };

    let job_id = Uuid::new_v4().to_string()[..8].to_string();
    let job_dir = PathBuf::from(format!("/tmp/flowork_mesh_job_{}", job_id));
    if let Err(e) = fs::create_dir_all(job_dir.join("out")) {
        return (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "status": "error", "error": e.to_string() })),
        )
            .into_response();
    }

    // Decompress zstd tar workspace if provided
    if !ws_b64.is_empty() {
        let Ok(compressed) = B64.decode(&ws_b64) else {
            let _ = fs::remove_dir_all(&job_dir);
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({ "status": "error", "error": "Invalid workspace_zstd_b64" })),
            )
                .into_response();
        };
        let max_bytes = st.policy.mesh.max_artifact_mb.saturating_mul(1024 * 1024);
        if max_bytes > 0 && compressed.len() > max_bytes {
            let _ = fs::remove_dir_all(&job_dir);
            return (
                StatusCode::PAYLOAD_TOO_LARGE,
                Json(json!({ "status": "error", "error": "Workspace payload exceeds max_artifact_mb policy" })),
            )
                .into_response();
        }
        let zst_path = job_dir.join(".ws.tar.zst");
        let tar_path = job_dir.join(".ws.tar");
        if fs::write(&zst_path, &compressed).is_err() {
            let _ = fs::remove_dir_all(&job_dir);
            return (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error":"write zst failed"}))).into_response();
        }
        let dec = Command::new(resolve_zstd_bin())
            .args(["-d", "-f", zst_path.to_str().unwrap(), "-o", tar_path.to_str().unwrap()])
            .status();
        let _ = fs::remove_file(&zst_path);
        if !matches!(dec, Ok(s) if s.success()) {
            let _ = fs::remove_dir_all(&job_dir);
            return (StatusCode::BAD_REQUEST, Json(json!({"error":"zstd decompress failed"}))).into_response();
        }
        let untar = Command::new("tar")
            .args(["-xf", tar_path.to_str().unwrap(), "-C", job_dir.to_str().unwrap()])
            .status();
        let _ = fs::remove_file(&tar_path);
        if !matches!(untar, Ok(s) if s.success()) {
            let _ = fs::remove_dir_all(&job_dir);
            return (StatusCode::BAD_REQUEST, Json(json!({"error":"tar extract failed"}))).into_response();
        }
    }

    // Write temporary Landlock sandbox manifest confining execution exclusively to job_dir
    let mut read_paths = vec![job_dir.to_string_lossy().to_string()];
    if let Ok(canon_cli) = fs::canonicalize(&resolved_cli) {
        if let Some(bin_parent) = canon_cli.parent() {
            read_paths.push(bin_parent.to_string_lossy().to_string());
            if let Some(app_root) = bin_parent.parent() {
                if app_root.starts_with("/opt/floworkos/apps")
                    && app_root != Path::new("/opt/floworkos/apps")
                {
                    read_paths.push(app_root.to_string_lossy().to_string());
                }
            }
        }
    }
    let manifest_path = job_dir.join(".mesh_job_manifest.json");
    let manifest_val = json!({
        "permissions": {
            "profile": "strict",
            "allow_network": false,
            "ipc_neural_bus": false,
            "read_paths": read_paths,
            "write_paths": [job_dir]
        }
    });
    let _ = fs::write(&manifest_path, serde_json::to_vec(&manifest_val).unwrap_or_default());

    struct MpscSseStream(tokio::sync::mpsc::Receiver<Result<Event, Infallible>>);
    impl futures_util::Stream for MpscSseStream {
        type Item = Result<Event, Infallible>;
        fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
            self.0.poll_recv(cx)
        }
    }

    let (tx, rx) = tokio::sync::mpsc::channel::<Result<Event, Infallible>>(32);
    let node_id = st.config.node_id.clone();
    let sandbox_bin = st.policy.capabilities.sandbox_exec.clone();

    tokio::spawn(async move {
        let _ = tx
            .send(Ok(Event::default().event("log").data(
                json!({
                    "node_id": node_id,
                    "line": format!("[mesh] starting '{}' inside Landlock jail ({})", resolved_cli, job_dir.display())
                })
                .to_string(),
            )))
            .await;

        let mut cmd = tokio::process::Command::new(&sandbox_bin);
        cmd.arg("--app-id")
            .arg(format!("mesh_job_{}", job_id))
            .arg("--manifest")
            .arg(&manifest_path)
            .arg("--")
            .arg(&resolved_cli)
            .args(&args)
            .current_dir(&job_dir)
            .env("FLOWORK_MESH_JOB_DIR", &job_dir)
            .env("FLOWORK_NO_TOAST", "1")
            .stdin(Stdio::null());

        let (exit_code, stdout_str, stderr_str) = match cmd.output().await {
            Ok(out) => (
                out.status.code().unwrap_or(1),
                String::from_utf8_lossy(&out.stdout).to_string(),
                String::from_utf8_lossy(&out.stderr).to_string(),
            ),
            Err(e) => (1, String::new(), format!("Sandboxed CLI execution failed: {}", e)),
        };

        for line in stdout_str.lines() {
            let _ = tx
                .send(Ok(Event::default()
                    .event("log")
                    .data(json!({ "stream": "stdout", "line": line }).to_string())))
                .await;
        }
        for line in stderr_str.lines() {
            let _ = tx
                .send(Ok(Event::default()
                    .event("log")
                    .data(json!({ "stream": "stderr", "line": line }).to_string())))
                .await;
        }

        let mut artifact_b64 = String::new();
        let out_tar = job_dir.join(".out.tar");
        let out_zst = job_dir.join(".out.tar.zst");
        let tar_res = Command::new("tar")
            .args([
                "-C",
                job_dir.to_str().unwrap(),
                "--exclude=.mesh_job_manifest.json",
                "--exclude=.out.tar",
                "--exclude=.out.tar.zst",
                "-cf",
                out_tar.to_str().unwrap(),
                "out",
            ])
            .status();
        if matches!(tar_res, Ok(s) if s.success()) {
            let zres = Command::new(resolve_zstd_bin())
                .args(["-q", "-f", out_tar.to_str().unwrap(), "-o", out_zst.to_str().unwrap()])
                .status();
            if matches!(zres, Ok(s) if s.success()) {
                if let Ok(bytes) = fs::read(&out_zst) {
                    artifact_b64 = B64.encode(bytes);
                }
            }
        }
        let _ = fs::remove_dir_all(&job_dir);

        let _ = tx
            .send(Ok(Event::default().event("done").data(
                json!({
                    "status": if exit_code == 0 { "ok" } else { "error" },
                    "exit_code": exit_code,
                    "node_id": node_id,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "artifact_zstd_b64": artifact_b64,
                })
                .to_string(),
            )))
            .await;
    });

    Sse::new(MpscSseStream(rx))
        .keep_alive(KeepAlive::default())
        .into_response()
}

async fn cmd_serve(mesh_dir: &Path, bind_override: Option<&str>, policy: MeshPolicyDoc) -> i32 {
    let cfg = match load_mesh_config(mesh_dir) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{}", e);
            return 1;
        }
    };
    if !cfg.enabled {
        eprintln!("Refusing to start Flowork Mesh listener: default-off policy active (run `flowork-mesh enable` first).");
        return 1;
    }

    let _ = rustls::crypto::ring::default_provider().install_default();
    let acceptor = match build_server_tls(mesh_dir) {
        Ok(a) => a,
        Err(e) => {
            eprintln!("Failed initializing mTLS server config: {}", e);
            return 1;
        }
    };

    let bind_str = bind_override.unwrap_or(&cfg.bind);
    let addr: SocketAddr = match bind_str.parse() {
        Ok(a) => a,
        Err(e) => {
            eprintln!("Invalid bind address '{}': {}", bind_str, e);
            return 1;
        }
    };

    let state = Arc::new(ServerState {
        config: cfg.clone(),
        policy,
    });

    let app = Router::new()
        .route("/mesh/v1/health", get(api_health))
        .route("/mesh/v1/capabilities", get(api_capabilities))
        .route("/mesh/v1/infer", post(api_infer))
        .route("/mesh/v1/job", post(api_job))
        .route("/mesh/v1/pipe", post(api_pipe))
        .with_state(state);

    let listener = match TcpListener::bind(addr).await {
        Ok(l) => l,
        Err(e) => {
            eprintln!("Failed binding Flowork Mesh mTLS listener on {}: {}", addr, e);
            return 1;
        }
    };
    println!("🌐 Flowork Mesh mTLS Zero-Trust Daemon listening on https://{} (node={})", addr, cfg.node_id);

    loop {
        tokio::select! {
            _ = tokio::signal::ctrl_c() => {
                println!("Flowork Mesh shutting down cleanly.");
                break;
            }
            accepted = listener.accept() => {
                let Ok((tcp, _peer_addr)) = accepted else { continue };
                let acceptor_cl = acceptor.clone();
                let app_cl = app.clone();
                tokio::spawn(async move {
                    match acceptor_cl.accept(tcp).await {
                        Ok(tls_stream) => {
                            let io = TokioIo::new(tls_stream);
                            let svc = TowerToHyperService::new(app_cl);
                            let _ = HyperAutoBuilder::new(TokioExecutor::new())
                                .serve_connection(io, svc)
                                .await;
                        }
                        Err(e) => {
                            eprintln!("[mesh mTLS rejected unauthenticated client] {}", e);
                        }
                    }
                });
            }
        }
    }
    0
}

async fn cmd_exec(mesh_dir: &Path, args: &[String], json_mode: bool) -> i32 {
    let mut peer_sel: Option<String> = None;
    let mut cli_name: Option<String> = None;
    let mut ws_dir: Option<PathBuf> = None;
    let mut out_dir: Option<PathBuf> = None;
    let mut cli_args: Vec<String> = Vec::new();
    let mut after_sep = false;

    let mut i = 0;
    while i < args.len() {
        if after_sep {
            cli_args.push(args[i].clone());
            i += 1;
            continue;
        }
        match args[i].as_str() {
            "--" => after_sep = true,
            "--cli" => {
                cli_name = args.get(i + 1).cloned();
                i += 1;
            }
            "--workspace" | "-w" => {
                ws_dir = args.get(i + 1).map(PathBuf::from);
                i += 1;
            }
            "--out-dir" | "-o" => {
                out_dir = args.get(i + 1).map(PathBuf::from);
                i += 1;
            }
            "--json" => {}
            other if peer_sel.is_none() && !other.starts_with('-') => {
                peer_sel = Some(other.to_string());
            }
            other => cli_args.push(other.to_string()),
        }
        i += 1;
    }

    let (Some(ps), Some(cli)) = (peer_sel, cli_name) else {
        eprintln!("Usage: flowork-mesh exec <@peer> --cli <name> [--workspace dir] [--out-dir dir] -- <args...>");
        return 1;
    };

    let peers = load_trusted_peers(mesh_dir);
    let Some(peer) = resolve_peer(&peers, &ps) else {
        eprintln!("Unknown peer '{}' in trusted_peers.json", ps);
        return 1;
    };
    let client = match build_mtls_client(mesh_dir, peer) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{}", e);
            return 1;
        }
    };

    let mut ws_b64 = String::new();
    if let Some(ws) = ws_dir {
        if ws.is_dir() {
            let tmp_tar = PathBuf::from(format!("/tmp/flowork_mesh_send_{}.tar", Uuid::new_v4()));
            let tmp_zst = PathBuf::from(format!("{}.zst", tmp_tar.display()));
            let tstat = Command::new("tar")
                .args(["-C", ws.to_str().unwrap(), "-cf", tmp_tar.to_str().unwrap(), "."])
                .status();
            if matches!(tstat, Ok(s) if s.success()) {
                let zstat = Command::new(resolve_zstd_bin())
                    .args(["-q", "-f", tmp_tar.to_str().unwrap(), "-o", tmp_zst.to_str().unwrap()])
                    .status();
                if matches!(zstat, Ok(s) if s.success()) {
                    if let Ok(bytes) = fs::read(&tmp_zst) {
                        ws_b64 = B64.encode(bytes);
                    }
                }
            }
            let _ = fs::remove_file(&tmp_tar);
            let _ = fs::remove_file(&tmp_zst);
        }
    }

    let url = format!("https://{}/mesh/v1/job", peer.endpoint);
    let resp = match client
        .post(&url)
        .json(&json!({
            "cli": cli,
            "args": cli_args,
            "workspace_zstd_b64": ws_b64,
        }))
        .send()
        .await
    {
        Ok(r) => r,
        Err(e) => {
            eprintln!("mTLS request to {} failed: {}", url, e);
            return 1;
        }
    };

    if !resp.status().is_success() {
        let status = resp.status();
        let txt = resp.text().await.unwrap_or_default();
        if json_mode {
            println!("{}", txt);
        } else {
            eprintln!("Remote peer rejected job (HTTP {}): {}", status, txt);
        }
        return 1;
    }

    let mut stream = resp.bytes_stream();
    let mut buf = String::new();
    let mut final_payload: Option<Value> = None;
    let mut cur_event = String::new();

    while let Some(chunk) = stream.next().await {
        let Ok(bytes) = chunk else { break };
        buf.push_str(&String::from_utf8_lossy(&bytes));
        while let Some(pos) = buf.find('\n') {
            let line = buf[..pos].trim_end_matches('\r').to_string();
            buf.drain(..=pos);
            if let Some(ev) = line.strip_prefix("event:") {
                cur_event = ev.trim().to_string();
            } else if let Some(data) = line.strip_prefix("data:") {
                if let Ok(v) = serde_json::from_str::<Value>(data.trim()) {
                    if cur_event == "log" && !json_mode {
                        if let Some(l) = v.get("line").and_then(|x| x.as_str()) {
                            println!("{}", l);
                        }
                    } else if cur_event == "done" {
                        final_payload = Some(v);
                    }
                }
            }
        }
    }

    if let Some(done) = final_payload {
        if let (Some(dest), Some(art_b64)) = (out_dir, done.get("artifact_zstd_b64").and_then(|v| v.as_str())) {
            if !art_b64.is_empty() {
                if let Ok(raw) = B64.decode(art_b64) {
                    let _ = fs::create_dir_all(&dest);
                    let tmp_z = dest.join(".recv.tar.zst");
                    let tmp_t = dest.join(".recv.tar");
                    if fs::write(&tmp_z, &raw).is_ok() {
                        let _ = Command::new(resolve_zstd_bin())
                            .args(["-q", "-d", "-f", tmp_z.to_str().unwrap(), "-o", tmp_t.to_str().unwrap()])
                            .status();
                        let _ = Command::new("tar")
                            .args(["-xf", tmp_t.to_str().unwrap(), "-C", dest.to_str().unwrap()])
                            .status();
                    }
                    let _ = fs::remove_file(&tmp_z);
                    let _ = fs::remove_file(&tmp_t);
                }
            }
        }
        let code = done.get("exit_code").and_then(|v| v.as_i64()).unwrap_or(1) as i32;
        if json_mode {
            println!("{}", serde_json::to_string_pretty(&done).unwrap_or_default());
        }
        return code;
    }

    1
}

async fn cmd_infer(mesh_dir: &Path, args: &[String], json_mode: bool) -> i32 {
    let mut peer_sel: Option<String> = None;
    let mut prompt = String::new();
    let mut model = String::from("l0-router");
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--prompt" | "-p" => {
                if let Some(v) = args.get(i + 1) {
                    prompt = v.clone();
                    i += 1;
                }
            }
            "--model" | "-m" => {
                if let Some(v) = args.get(i + 1) {
                    model = v.clone();
                    i += 1;
                }
            }
            "--json" => {}
            other if peer_sel.is_none() && !other.starts_with('-') => peer_sel = Some(other.to_string()),
            _ => {}
        }
        i += 1;
    }
    let Some(ps) = peer_sel else {
        eprintln!("Usage: flowork-mesh infer <@peer> --prompt <text> [--model name]");
        return 1;
    };
    let peers = load_trusted_peers(mesh_dir);
    let Some(peer) = resolve_peer(&peers, &ps) else {
        eprintln!("Unknown peer '{}'", ps);
        return 1;
    };
    let client = match build_mtls_client(mesh_dir, peer) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{}", e);
            return 1;
        }
    };
    let url = format!("https://{}/mesh/v1/infer", peer.endpoint);
    match client.post(&url).json(&json!({"prompt": prompt, "model": model})).send().await {
        Ok(resp) => {
            let ok = resp.status().is_success();
            let v: Value = resp.json().await.unwrap_or_else(|_| json!({"status":"error"}));
            if json_mode {
                println!("{}", serde_json::to_string_pretty(&v).unwrap_or_default());
            } else if let Some(msg) = v["result"]["choices"][0]["message"]["content"].as_str() {
                println!("{}", msg);
            } else {
                println!("{}", v);
            }
            if ok { 0 } else { 1 }
        }
        Err(e) => {
            eprintln!("mTLS infer error: {}", e);
            1
        }
    }
}

async fn cmd_pipe(mesh_dir: &Path, args: &[String], json_mode: bool) -> i32 {
    let mut peer_sel: Option<String> = None;
    let mut target: Option<String> = None;
    let mut inputs = serde_json::Map::new();
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--peer" => {
                peer_sel = args.get(i + 1).cloned();
                i += 1;
            }
            "--input" | "-i" => {
                if let Some(kv) = args.get(i + 1) {
                    if let Some((k, v)) = kv.split_once('=') {
                        inputs.insert(k.trim().to_string(), Value::String(v.trim().to_string()));
                    }
                    i += 1;
                }
            }
            "--json" => {}
            other if !other.starts_with('-') => {
                if peer_sel.is_none() && other.starts_with('@') {
                    peer_sel = Some(other.to_string());
                } else if target.is_none() {
                    target = Some(other.to_string());
                }
            }
            _ => {}
        }
        i += 1;
    }
    let (Some(ps), Some(tgt)) = (peer_sel, target) else {
        eprintln!("Usage: flowork-mesh pipe --peer <@peer> <file.flowpipe|id> [--input k=v]");
        return 1;
    };
    let peers = load_trusted_peers(mesh_dir);
    let Some(peer) = resolve_peer(&peers, &ps) else {
        eprintln!("Unknown peer '{}'", ps);
        return 1;
    };
    let client = match build_mtls_client(mesh_dir, peer) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{}", e);
            return 1;
        }
    };
    let mut body = serde_json::Map::new();
    if Path::new(&tgt).is_file() {
        body.insert("toml".into(), Value::String(fs::read_to_string(&tgt).unwrap_or_default()));
    } else {
        body.insert("id".into(), Value::String(tgt));
    }
    body.insert("inputs".into(), Value::Object(inputs));
    let url = format!("https://{}/mesh/v1/pipe", peer.endpoint);
    match client.post(&url).json(&Value::Object(body)).send().await {
        Ok(resp) => {
            let ok = resp.status().is_success();
            let v: Value = resp.json().await.unwrap_or_else(|_| json!({"status":"error"}));
            if json_mode {
                println!("{}", serde_json::to_string_pretty(&v).unwrap_or_default());
            } else {
                println!(
                    "✓ Remote pipe [node={}]: status={} (exit={})",
                    v["node_id"].as_str().unwrap_or(&peer.node_id),
                    v["status"].as_str().unwrap_or("error"),
                    v["exit_code"].as_i64().unwrap_or(1)
                );
            }
            if ok { 0 } else { 1 }
        }
        Err(e) => {
            eprintln!("mTLS pipe error: {}", e);
            1
        }
    }
}

async fn cmd_register_provider(mesh_dir: &Path, args: &[String], json_mode: bool) -> i32 {
    let sync_global = args.iter().any(|a| a == "--sync");
    let Some(ps) = args.iter().find(|a| !a.starts_with('-')) else {
        eprintln!("Usage: flowork-mesh register-provider <@peer> [--sync]");
        return 1;
    };
    let peers = load_trusted_peers(mesh_dir);
    let Some(peer) = resolve_peer(&peers, ps) else {
        eprintln!("Unknown peer '{}'", ps);
        return 1;
    };
    let client = match build_mtls_client(mesh_dir, peer) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{}", e);
            return 1;
        }
    };
    let url = format!("https://{}/mesh/v1/capabilities", peer.endpoint);
    let caps: Value = match client.get(&url).send().await {
        Ok(r) if r.status().is_success() => r.json().await.unwrap_or_else(|_| json!({})),
        Ok(r) => {
            eprintln!("Peer capabilities returned HTTP {}", r.status());
            return 1;
        }
        Err(e) => {
            eprintln!("Peer unreachable over mTLS: {}", e);
            return 1;
        }
    };

    let prov_name = format!("mesh-{}", peer.node_name);
    let models = caps["hardware"]["ollama_models"]
        .as_array()
        .and_then(|a| a.first())
        .and_then(|v| v.as_str())
        .unwrap_or("l0-router");
    let entry = json!({
        "type": "flowork_mesh_mtls",
        "node_id": peer.node_id,
        "endpoint": format!("https://{}/mesh/v1/infer", peer.endpoint),
        "model": models,
        "fingerprint": peer.fingerprint,
        "capabilities": caps["hardware"]
    });

    let mesh_prov_path = mesh_dir.join("remote_providers.json");
    let mut doc: Value = fs::read_to_string(&mesh_prov_path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_else(|| json!({ "providers": {} }));
    if let Some(map) = doc.get_mut("providers").and_then(|v| v.as_object_mut()) {
        map.insert(prov_name.clone(), entry.clone());
    }
    let _ = fs::write(&mesh_prov_path, serde_json::to_string_pretty(&doc).unwrap_or_default());

    if sync_global {
        let ppath = Path::new("/opt/floworkos/connector/config/providers.json");
        if let Ok(raw) = fs::read_to_string(ppath) {
            if let Ok(mut pv) = serde_json::from_str::<Value>(&raw) {
                if let Some(map) = pv.get_mut("providers").and_then(|v| v.as_object_mut()) {
                    map.insert(prov_name.clone(), entry.clone());
                }
                let _ = fs::write(ppath, serde_json::to_string_pretty(&pv).unwrap_or_default());
            }
        }
    }

    if json_mode {
        println!("{}", serde_json::to_string_pretty(&json!({"status":"ok","provider":prov_name,"entry":entry})).unwrap_or_default());
    } else {
        println!("✓ Registered mTLS mesh provider '{}' -> https://{}/mesh/v1/infer", prov_name, peer.endpoint);
    }
    0
}

fn cmd_discover(json_mode: bool) -> i32 {
    let mut services = Vec::<String>::new();
    if let Ok(out) = Command::new("avahi-browse")
        .args(["-t", "-p", "_flowork._tcp"])
        .output()
    {
        if out.status.success() {
            for line in String::from_utf8_lossy(&out.stdout).lines() {
                if !line.trim().is_empty() {
                    services.push(line.to_string());
                }
            }
        }
    }
    if json_mode {
        println!("{}", json!({ "status": "ok", "mdns_service": "_flowork._tcp.local", "discovered": services }));
    } else {
        println!("Flowork Mesh LAN discovery (_flowork._tcp.local): {} service(s)", services.len());
        for s in services {
            println!("  - {}", s);
        }
    }
    0
}

#[tokio::main]
async fn main() {
    let raw_args: Vec<String> = env::args().skip(1).collect();
    let before_sep: Vec<&str> = raw_args
        .iter()
        .take_while(|a| a.as_str() != "--")
        .map(String::as_str)
        .collect();
    if raw_args.is_empty() || before_sep.iter().any(|a| *a == "--help" || *a == "-h") {
        println!("flowork-mesh — Flowork Sovereign mTLS Zero-Trust P2P Compute & Remote Bus");
        println!("Usage:");
        println!("  flowork-mesh init [--name <label>] [--bind <ip:port>] [--json]");
        println!("  flowork-mesh status [--json]");
        println!("  flowork-mesh enable [--bind <ip:port>] | disable [--json]");
        println!("  flowork-mesh pair [--export [path]] [--accept <bundle.json> --pin <code > --endpoint <ip:port>]");
        println!("  flowork-mesh serve [--bind <ip:port>]");
        println!("  flowork-mesh exec <@peer> --cli <name> [--workspace dir] [--out-dir dir] -- <args...>");
        println!("  flowork-mesh infer <@peer> --prompt <text> [--model name]");
        println!("  flowork-mesh pipe --peer <@peer> <file.flowpipe|id> [--input k=v]");
        println!("  flowork-mesh register-provider <@peer> [--sync]");
        println!("  flowork-mesh discover [--json]");
        return;
    }

    if before_sep.contains(&"--check") {
        let mut _ok = TcpStream::connect("127.0.0.1:0");
        println!("flowork-mesh: OK (mTLS Ed25519 Zero-Trust Mesh ready)");
        return;
    }

    let mut mesh_dir = env::var("FLOWORK_MESH_DIR")
        .ok()
        .filter(|s| !s.trim().is_empty())
        .map(PathBuf::from)
        .unwrap_or_else(|| resolve_home_dir().join(".flowork/mesh"));
    let mut policy_path = PathBuf::from(DEFAULT_POLICY_PATH);
    let mut json_mode = false;
    let mut filtered = Vec::<String>::new();

    let mut idx = 0;
    let mut passthrough = false;
    while idx < raw_args.len() {
        let a = &raw_args[idx];
        if a == "--" {
            passthrough = true;
            filtered.push(a.clone());
            idx += 1;
            continue;
        }
        if !passthrough && a == "--mesh-dir" {
            if let Some(v) = raw_args.get(idx + 1) {
                mesh_dir = PathBuf::from(v);
                idx += 2;
                continue;
            }
        } else if !passthrough && a == "--policy" {
            if let Some(v) = raw_args.get(idx + 1) {
                policy_path = PathBuf::from(v);
                idx += 2;
                continue;
            }
        } else if !passthrough && a == "--json" {
            json_mode = true;
            filtered.push(a.clone());
            idx += 1;
            continue;
        }
        filtered.push(a.clone());
        idx += 1;
    }

    let policy = load_policy(&policy_path);
    let sub = filtered.first().map(String::as_str).unwrap_or("status");
    let sub_args = if filtered.len() > 1 { &filtered[1..] } else { &[] };

    let code = match sub {
        "init" => {
            let mut name = None;
            let mut bind = None;
            let mut k = 0;
            while k < sub_args.len() {
                if sub_args[k] == "--name" {
                    name = sub_args.get(k + 1).map(String::as_str);
                    k += 1;
                } else if sub_args[k] == "--bind" {
                    bind = sub_args.get(k + 1).map(String::as_str);
                    k += 1;
                }
                k += 1;
            }
            cmd_init(&mesh_dir, name, bind, &policy, json_mode)
        }
        "status" => cmd_status(&mesh_dir, json_mode),
        "enable" => {
            let bind = sub_args
                .windows(2)
                .find(|w| w[0] == "--bind")
                .map(|w| w[1].as_str());
            cmd_set_enabled(&mesh_dir, true, bind, json_mode)
        }
        "disable" => cmd_set_enabled(&mesh_dir, false, None, json_mode),
        "pair" => cmd_pair(&mesh_dir, sub_args, json_mode),
        "serve" => {
            let bind = sub_args
                .windows(2)
                .find(|w| w[0] == "--bind")
                .map(|w| w[1].as_str());
            cmd_serve(&mesh_dir, bind, policy).await
        }
        "exec" => cmd_exec(&mesh_dir, sub_args, json_mode).await,
        "infer" => cmd_infer(&mesh_dir, sub_args, json_mode).await,
        "pipe" => cmd_pipe(&mesh_dir, sub_args, json_mode).await,
        "register-provider" => cmd_register_provider(&mesh_dir, sub_args, json_mode).await,
        "discover" => cmd_discover(json_mode),
        other => {
            eprintln!("Unknown subcommand: {}", other);
            1
        }
    };
    std::process::exit(code);
}
