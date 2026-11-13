use std::fs;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct AiClassification {
    pub category: String, // e.g. "LLM", "Vision", "PyTorch", "Embedding", "Inference"
    pub model_hint: Option<String>,
}

pub fn classify_process(pid: u32, process_name: &str) -> Option<AiClassification> {
    let lower_name = process_name.to_lowercase();

    // Check process name triggers
    if lower_name.contains("ollama") {
        return Some(AiClassification {
            category: "Ollama LLM Engine".to_string(),
            model_hint: find_model_hint_in_cmdline(pid),
        });
    }

    if lower_name.contains("llama") || lower_name.contains("vllm") || lower_name.contains("tgi") {
        return Some(AiClassification {
            category: "LLM Inference Server".to_string(),
            model_hint: find_model_hint_in_cmdline(pid),
        });
    }

    if lower_name.contains("comfyui") || lower_name.contains("webui") {
        return Some(AiClassification {
            category: "Diffusion / Vision Pipeline".to_string(),
            model_hint: find_model_hint_in_cmdline(pid),
        });
    }

    if lower_name.contains("whisper") {
        return Some(AiClassification {
            category: "Audio / Speech Model".to_string(),
            model_hint: find_model_hint_in_cmdline(pid),
        });
    }

    // Inspect command line for Python/Node/Rust AI engines
    let cmdline_path = format!("/proc/{}/cmdline", pid);
    if let Ok(bytes) = fs::read(&cmdline_path) {
        let cmd = String::from_utf8_lossy(&bytes).replace('\0', " ");
        let cmd_lower = cmd.to_lowercase();

        if cmd_lower.contains("torch") || cmd_lower.contains("transformers") || cmd_lower.contains("accelerate") {
            return Some(AiClassification {
                category: "PyTorch Deep Learning".to_string(),
                model_hint: find_model_hint_in_cmdline(pid),
            });
        }

        if cmd_lower.contains("onnx") || cmd_lower.contains("tensorrt") {
            return Some(AiClassification {
                category: "Optimized Neural Runtime".to_string(),
                model_hint: find_model_hint_in_cmdline(pid),
            });
        }

        if cmd_lower.contains(".gguf") || cmd_lower.contains(".safetensors") || cmd_lower.contains(".bin") || cmd_lower.contains(".pt") {
            return Some(AiClassification {
                category: "Model Weight Mapped".to_string(),
                model_hint: extract_weight_filename(&cmd),
            });
        }

        if cmd_lower.contains("mrflow") || cmd_lower.contains("flowork-sysd") {
            return Some(AiClassification {
                category: "Sovereign Flowork Agent Core".to_string(),
                model_hint: Some("Autonomous Neural Node".to_string()),
            });
        }
    }

    None
}

fn find_model_hint_in_cmdline(pid: u32) -> Option<String> {
    let cmdline_path = format!("/proc/{}/cmdline", pid);
    let bytes = fs::read(cmdline_path).ok()?;
    let cmd = String::from_utf8_lossy(&bytes).replace('\0', " ");
    extract_weight_filename(&cmd)
}

fn extract_weight_filename(cmd: &str) -> Option<String> {
    for part in cmd.split_whitespace() {
        if part.ends_with(".gguf") || part.ends_with(".safetensors") || part.ends_with(".pt") || part.ends_with(".onnx") {
            if let Some(file_name) = Path::new(part).file_name() {
                return Some(file_name.to_string_lossy().to_string());
            }
        }
    }
    None
}
