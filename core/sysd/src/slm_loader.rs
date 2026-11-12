// =============================================================================
// Flowork Sovereign OS — L0 SLM Lazy Loader, Memory Guard & GBNF Inference
// =============================================================================

use serde_json::{json, Value};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};
use std::time::{Duration, Instant};

#[cfg(feature = "embedded-slm")]
use llama_cpp_2::context::params::LlamaContextParams;
#[cfg(feature = "embedded-slm")]
use llama_cpp_2::llama_backend::LlamaBackend;
#[cfg(feature = "embedded-slm")]
use llama_cpp_2::llama_batch::LlamaBatch;
#[cfg(feature = "embedded-slm")]
use llama_cpp_2::model::params::LlamaModelParams;
#[cfg(feature = "embedded-slm")]
use llama_cpp_2::model::{LlamaChatMessage, LlamaModel};
#[cfg(feature = "embedded-slm")]
use llama_cpp_2::sampling::LlamaSampler;
#[cfg(feature = "embedded-slm")]
use std::num::NonZeroU32;

pub const MODELS_DIR: &str = "/opt/floworkos/models";
pub const DEFAULT_MODEL_FILENAME: &str = "l0-router.gguf";
pub const MEM_PRESSURE_DISABLE_MB: u64 = 1200;
pub const MEM_IDLE_UNLOAD_THRESHOLD_MB: u64 = 2048;
pub const IDLE_UNLOAD_TIMEOUT_SECS: u64 = 600; // 10 minutes

/// GBNF grammar constraining GGUF output strictly to Flowork L0 triage JSON.
pub const L0_TRIAGE_GBNF: &str = r#"root ::= "{" ws "\"route\"" ws ":" ws route "," ws "\"confidence\"" ws ":" ws number "," ws "\"intent\"" ws ":" ws intent "," ws "\"args\"" ws ":" ws args_obj "," ws "\"normalized_keywords\"" ws ":" ws str_arr ws "}"
route ::= "\"local_action\"" | "\"delegate_cloud\""
intent ::= "\"flowfs_screen_search\"" | "\"flowfs_search\"" | "\"flowpkg_remix\"" | "\"flowork_launch\"" | "\"sentinel_audit\"" | "\"audio_control\"" | "\"window_tile\"" | "\"system_status\"" | "\"delegate_cloud\""
args_obj ::= "{" ws ( pair ( ws "," ws pair )* )? ws "}"
pair ::= string ws ":" ws ( string | number )
str_arr ::= "[" ws ( string ( ws "," ws string )* )? ws "]"
string ::= "\"" ( [^"\\\x7F\x00-\x1F] | "\\" ["\\/bfnrt] )* "\""
number ::= "0" ( "." [0-9]+ )? | [1-9] [0-9]* ( "." [0-9]+ )?
ws ::= [ \t\n\r]*
"#;

/// Parse `MemAvailable` (in MB) from `/proc/meminfo`.
pub fn parse_meminfo_available_mb(content: &str) -> Option<u64> {
    for line in content.lines() {
        if let Some(rest) = line.strip_prefix("MemAvailable:") {
            let kb_str = rest.split_whitespace().next()?;
            if let Ok(kb) = kb_str.parse::<u64>() {
                return Some(kb / 1024);
            }
        }
    }
    None
}

pub fn read_mem_available_mb() -> u64 {
    fs::read_to_string("/proc/meminfo")
        .ok()
        .and_then(|c| parse_meminfo_available_mb(&c))
        .unwrap_or(4096)
}

pub fn check_memory_pressure(mem_available_mb: u64) -> bool {
    mem_available_mb < MEM_PRESSURE_DISABLE_MB
}

pub fn resolve_model_path_in_dir(dir: &Path) -> Option<PathBuf> {
    if let Ok(env_path) = std::env::var("FLOWORK_L0_MODEL") {
        let trimmed = env_path.trim();
        if !trimmed.is_empty() {
            let p = PathBuf::from(trimmed);
            if p.is_file() {
                return Some(p);
            }
        }
    }

    let preferred = dir.join(DEFAULT_MODEL_FILENAME);
    if preferred.is_file() {
        return Some(preferred);
    }

    let mut ggufs: Vec<(u64, PathBuf)> = Vec::new();
    if let Ok(entries) = fs::read_dir(dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_file()
                && path
                    .extension()
                    .and_then(|s| s.to_str())
                    .map(|ext| ext.eq_ignore_ascii_case("gguf"))
                    == Some(true)
            {
                let size = entry.metadata().map(|m| m.len()).unwrap_or(u64::MAX);
                ggufs.push((size, path));
            }
        }
    }
    ggufs.sort_by(|a, b| a.0.cmp(&b.0).then_with(|| a.1.cmp(&b.1)));
    ggufs.into_iter().next().map(|(_, p)| p)
}

#[cfg(feature = "embedded-slm")]
struct LoadedSlm {
    backend: LlamaBackend,
    model: LlamaModel,
    model_path: PathBuf,
    loaded_at: Instant,
    last_used_at: Instant,
    load_duration_ms: u64,
    inference_count: u64,
}

#[cfg(not(feature = "embedded-slm"))]
struct LoadedSlm {
    model_path: PathBuf,
    loaded_at: Instant,
    last_used_at: Instant,
    load_duration_ms: u64,
    inference_count: u64,
}

pub struct SlmManager {
    state: Mutex<Option<LoadedSlm>>,
    last_error: Mutex<Option<String>>,
}

static SLM_MANAGER: OnceLock<SlmManager> = OnceLock::new();

pub fn global_slm_manager() -> &'static SlmManager {
    SLM_MANAGER.get_or_init(|| SlmManager {
        state: Mutex::new(None),
        last_error: Mutex::new(None),
    })
}

pub async fn start_idle_reaper() {
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(60));
        loop {
            interval.tick().await;
            global_slm_manager().unload_if_pressured_or_idle();
        }
    });
}

impl SlmManager {
    pub fn unload_if_pressured_or_idle(&self) -> bool {
        let mem_mb = read_mem_available_mb();
        let Ok(mut guard) = self.state.lock() else {
            return false;
        };
        let Some(ref loaded) = *guard else {
            return false;
        };

        let idle_secs = loaded.last_used_at.elapsed().as_secs();
        let under_hard_pressure = check_memory_pressure(mem_mb);
        let idle_under_soft_cap =
            mem_mb < MEM_IDLE_UNLOAD_THRESHOLD_MB && idle_secs >= IDLE_UNLOAD_TIMEOUT_SECS;

        if under_hard_pressure || idle_under_soft_cap {
            eprintln!(
                "[flowork-sysd][L0-SLM] Unloading GGUF model (MemAvailable={}MB, idle={}s)",
                mem_mb, idle_secs
            );
            *guard = None;
            return true;
        }
        false
    }

    pub fn force_unload(&self) {
        if let Ok(mut guard) = self.state.lock() {
            *guard = None;
        }
    }

    pub fn status_json(&self) -> Value {
        let mem_mb = read_mem_available_mb();
        let memory_pressure_blocked = check_memory_pressure(mem_mb);
        let candidate_model = resolve_model_path_in_dir(Path::new(MODELS_DIR));
        let last_err = self.last_error.lock().ok().and_then(|g| g.clone());

        if let Ok(guard) = self.state.lock() {
            if let Some(ref loaded) = *guard {
                return json!({
                    "feature_embedded_slm": cfg!(feature = "embedded-slm"),
                    "backend": if cfg!(feature = "embedded-slm") { "llama-cpp-2-gguf" } else { "deterministic-l0-heuristic" },
                    "model_loaded": true,
                    "model_path": loaded.model_path.display().to_string(),
                    "candidate_model": candidate_model.as_ref().map(|p| p.display().to_string()),
                    "load_duration_ms": loaded.load_duration_ms,
                    "uptime_secs": loaded.loaded_at.elapsed().as_secs(),
                    "idle_secs": loaded.last_used_at.elapsed().as_secs(),
                    "inference_count": loaded.inference_count,
                    "mem_available_mb": mem_mb,
                    "memory_pressure_blocked": memory_pressure_blocked,
                    "mem_disable_threshold_mb": MEM_PRESSURE_DISABLE_MB,
                    "last_error": last_err
                });
            }
        }

        json!({
            "feature_embedded_slm": cfg!(feature = "embedded-slm"),
            "backend": "deterministic-l0-heuristic",
            "model_loaded": false,
            "model_path": Value::Null,
            "candidate_model": candidate_model.as_ref().map(|p| p.display().to_string()),
            "mem_available_mb": mem_mb,
            "memory_pressure_blocked": memory_pressure_blocked,
            "mem_disable_threshold_mb": MEM_PRESSURE_DISABLE_MB,
            "last_error": last_err
        })
    }

    #[cfg(feature = "embedded-slm")]
    pub fn infer_triage_gguf(&self, prompt: &str) -> Result<Value, String> {
        let mem_mb = read_mem_available_mb();
        if check_memory_pressure(mem_mb) {
            self.force_unload();
            return Err(format!(
                "Memory-pressure guard active: MemAvailable={}MB < {}MB",
                mem_mb, MEM_PRESSURE_DISABLE_MB
            ));
        }

        let Some(model_path) = resolve_model_path_in_dir(Path::new(MODELS_DIR)) else {
            return Err("No GGUF model found under /opt/floworkos/models".to_string());
        };

        let mut guard = self
            .state
            .lock()
            .map_err(|_| "SLM mutex poisoned".to_string())?;

        if guard
            .as_ref()
            .map(|l| l.model_path != model_path)
            .unwrap_or(true)
        {
            let t0 = Instant::now();
            let mut backend = LlamaBackend::init().map_err(|e| format!("LlamaBackend init: {e}"))?;
            backend.void_logs();

            let n_gpu_layers: u32 = std::env::var("FLOWORK_L0_GPU_LAYERS")
                .ok()
                .and_then(|s| s.parse().ok())
                .unwrap_or(0);

            let mparams = LlamaModelParams::default()
                .with_use_mmap(true)
                .with_n_gpu_layers(n_gpu_layers);

            let model = LlamaModel::load_from_file(&backend, &model_path, &mparams)
                .map_err(|e| format!("GGUF load failed ({}): {e}", model_path.display()))?;

            let elapsed = t0.elapsed().as_millis() as u64;
            let now = Instant::now();
            *guard = Some(LoadedSlm {
                backend,
                model,
                model_path: model_path.clone(),
                loaded_at: now,
                last_used_at: now,
                load_duration_ms: elapsed,
                inference_count: 0,
            });
        }

        let loaded = guard.as_mut().ok_or("Loaded model unavailable")?;
        loaded.last_used_at = Instant::now();
        loaded.inference_count = loaded.inference_count.saturating_add(1);

        let system_directive = concat!(
            "You are Flowork OS L0 Cognitive Triage Router. ",
            "Classify the user prompt into strict JSON with keys: ",
            "route ('local_action' or 'delegate_cloud'), confidence (0.0-1.0), ",
            "intent ('flowfs_screen_search'|'flowfs_search'|'flowpkg_remix'|'flowork_launch'|'sentinel_audit'|'audio_control'|'window_tile'|'system_status'|'delegate_cloud'), ",
            "args (object with query/app/position/volume), and normalized_keywords (3-6 lowercase English technical keywords). Output ONLY JSON."
        );

        let formatted_prompt = match loaded.model.chat_template(None) {
            Ok(tmpl) => {
                let msgs = [
                    LlamaChatMessage::new("system".to_string(), system_directive.to_string())
                        .map_err(|e| format!("chat message error: {e}"))?,
                    LlamaChatMessage::new("user".to_string(), prompt.to_string())
                        .map_err(|e| format!("chat message error: {e}"))?,
                ];
                loaded
                    .model
                    .apply_chat_template(&tmpl, &msgs, true)
                    .unwrap_or_else(|_| {
                        format!(
                            "<|im_start|>system\n{}<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n",
                            system_directive, prompt
                        )
                    })
            }
            Err(_) => format!(
                "<|im_start|>system\n{}<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n",
                system_directive, prompt
            ),
        };

        let threads = std::thread::available_parallelism()
            .map(|n| n.get().clamp(1, 6) as i32)
            .unwrap_or(4);

        let ctx_params = LlamaContextParams::default()
            .with_n_ctx(NonZeroU32::new(1536))
            .with_n_batch(512)
            .with_n_threads(threads)
            .with_n_threads_batch(threads);

        let mut ctx = loaded
            .model
            .new_context(&loaded.backend, ctx_params)
            .map_err(|e| format!("Context init failed: {e}"))?;

        let vocab = loaded.model.vocab();
        let tokens = vocab.tokenize(formatted_prompt.as_bytes(), true, true);
        if tokens.is_empty() || tokens.len() > 1280 {
            return Err(format!("Prompt token count out of L0 bounds: {}", tokens.len()));
        }

        let mut batch = LlamaBatch::new(1536, 1);
        batch
            .add_sequence(&tokens, 0, false)
            .map_err(|e| format!("Batch add sequence failed: {e}"))?;
        ctx.decode(&mut batch)
            .map_err(|e| format!("Prompt decode failed: {e}"))?;

        let grammar_sampler = LlamaSampler::grammar(&loaded.model, L0_TRIAGE_GBNF, "root")
            .map_err(|e| format!("GBNF grammar init failed: {e}"))?;
        let mut sampler = LlamaSampler::chain_simple([
            grammar_sampler,
            LlamaSampler::temp(0.0),
            LlamaSampler::greedy(),
        ]);

        let max_gen = 160;
        let mut raw_bytes: Vec<u8> = Vec::new();
        let mut idx = (tokens.len() as i32) - 1;

        for n_cur in (tokens.len() as i32..).take(max_gen) {
            let token = sampler.sample(&ctx, idx);
            sampler.accept(token);
            if vocab.is_eog(token) {
                break;
            }
            vocab.token_to_piece_into(token, &mut raw_bytes, false, None);

            batch.clear();
            batch
                .add(token, n_cur, &[0], true)
                .map_err(|e| format!("Next batch add failed: {e}"))?;
            ctx.decode(&mut batch)
                .map_err(|e| format!("Decode step failed: {e}"))?;
            idx = 0;

            if raw_bytes.ends_with(b"}") && serde_json::from_slice::<Value>(&raw_bytes).is_ok() {
                break;
            }
        }

        let out_str = String::from_utf8_lossy(&raw_bytes).trim().to_string();
        match serde_json::from_str::<Value>(&out_str) {
            Ok(v) => {
                if let Ok(mut err_g) = self.last_error.lock() {
                    *err_g = None;
                }
                Ok(v)
            }
            Err(e) => {
                let msg = format!("GGUF output not valid JSON: {e} ({out_str})");
                if let Ok(mut err_g) = self.last_error.lock() {
                    *err_g = Some(msg.clone());
                }
                Err(msg)
            }
        }
    }

    #[cfg(not(feature = "embedded-slm"))]
    pub fn infer_triage_gguf(&self, _prompt: &str) -> Result<Value, String> {
        Err("Compiled without embedded-slm feature".to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn meminfo_parser_and_pressure_guard() {
        let sample = "MemTotal:       16384000 kB\nMemFree:         1024000 kB\nMemAvailable:    1048576 kB\n";
        let mb = parse_meminfo_available_mb(sample).unwrap();
        assert_eq!(mb, 1024);
        assert!(check_memory_pressure(mb));
        assert!(!check_memory_pressure(1500));
    }

    #[test]
    fn missing_model_returns_none_gracefully() {
        let tmp = std::env::temp_dir().join("flowork_empty_models_test_dir");
        let _ = fs::remove_dir_all(&tmp);
        fs::create_dir_all(&tmp).unwrap();
        let resolved = resolve_model_path_in_dir(&tmp);
        assert!(resolved.is_none());
        let _ = fs::remove_dir_all(&tmp);
    }

    #[test]
    fn gbnf_grammar_has_root_and_expected_fields() {
        assert!(L0_TRIAGE_GBNF.contains("root ::="));
        assert!(L0_TRIAGE_GBNF.contains("normalized_keywords"));
        assert!(L0_TRIAGE_GBNF.contains("local_action"));
        assert!(L0_TRIAGE_GBNF.contains("delegate_cloud"));
    }
}
