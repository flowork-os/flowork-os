use std::process::Command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GpuProcess {
    pub pid: u32,
    pub name: String,
    pub process_type: String,
    pub memory_used_mb: u64,
    pub ai_classification: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GpuTelemetry {
    pub name: String,
    pub driver_version: String,
    pub utilization_gpu: u32,
    pub memory_used_mb: u64,
    pub memory_total_mb: u64,
    pub temperature_c: u32,
    pub power_draw_w: Option<f32>,
    pub fan_speed_pct: Option<u32>,
    pub processes: Vec<GpuProcess>,
}

pub fn probe_gpu() -> Option<GpuTelemetry> {
    // 1. Try NVIDIA SMI
    if let Some(telemetry) = probe_nvidia() {
        return Some(telemetry);
    }

    // 2. Try AMD / Intel via DRM Sysfs
    if let Some(telemetry) = probe_drm_sysfs() {
        return Some(telemetry);
    }

    None
}

fn probe_nvidia() -> Option<GpuTelemetry> {
    // Fast query for GPU metrics
    let output = Command::new("nvidia-smi")
        .args([
            "--query-gpu=name,driver_version,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,fan.speed",
            "--format=csv,noheader,nounits",
        ])
        .output()
        .ok()?;

    if !output.status.success() {
        return None;
    }

    let text = String::from_utf8_lossy(&output.stdout);
    let line = text.lines().next()?;
    let parts: Vec<&str> = line.split(',').map(|s| s.trim()).collect();
    if parts.len() < 8 {
        return None;
    }

    let name = parts[0].to_string();
    let driver_version = parts[1].to_string();
    let utilization_gpu = parts[2].parse::<u32>().unwrap_or(0);
    let memory_used_mb = parts[3].parse::<u64>().unwrap_or(0);
    let memory_total_mb = parts[4].parse::<u64>().unwrap_or(0);
    let temperature_c = parts[5].parse::<u32>().unwrap_or(0);
    let power_draw_w = parts[6].parse::<f32>().ok();
    let fan_speed_pct = parts[7].parse::<u32>().ok();

    // Query processes
    let processes = probe_nvidia_processes();

    Some(GpuTelemetry {
        name,
        driver_version,
        utilization_gpu,
        memory_used_mb,
        memory_total_mb,
        temperature_c,
        power_draw_w,
        fan_speed_pct,
        processes,
    })
}

fn probe_nvidia_processes() -> Vec<GpuProcess> {
    let mut results = Vec::new();

    // Parse XML dump which contains both Compute (C) and Graphics (G) processes with VRAM usage
    if let Ok(output) = Command::new("nvidia-smi").args(["-q", "-x"]).output() {
        if output.status.success() {
            let xml = String::from_utf8_lossy(&output.stdout);
            return parse_nvidia_xml_processes(&xml);
        }
    }

    // Fallback: query compute apps
    if let Ok(output) = Command::new("nvidia-smi")
        .args(["--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader,nounits"])
        .output()
    {
        let text = String::from_utf8_lossy(&output.stdout);
        for line in text.lines() {
            let parts: Vec<&str> = line.split(',').map(|s| s.trim()).collect();
            if parts.len() >= 3 {
                if let Ok(pid) = parts[0].parse::<u32>() {
                    let name = parts[1].to_string();
                    let mem = parts[2].replace("MiB", "").trim().parse::<u64>().unwrap_or(0);
                    results.push(GpuProcess {
                        pid,
                        name,
                        process_type: "C".to_string(),
                        memory_used_mb: mem,
                        ai_classification: None,
                    });
                }
            }
        }
    }

    results
}

fn parse_nvidia_xml_processes(xml: &str) -> Vec<GpuProcess> {
    let mut procs = Vec::new();
    let mut cursor = xml;

    while let Some(proc_start) = cursor.find("<process_info>") {
        let after_start = &cursor[proc_start + "<process_info>".len()..];
        if let Some(proc_end) = after_start.find("</process_info>") {
            let block = &after_start[..proc_end];
            cursor = &after_start[proc_end + "</process_info>".len()..];

            let pid_str = extract_xml_tag(block, "pid");
            let type_str = extract_xml_tag(block, "type").unwrap_or_else(|| "G".to_string());
            let name_str = extract_xml_tag(block, "process_name").unwrap_or_else(|| "unknown".to_string());
            let mem_str = extract_xml_tag(block, "used_memory").unwrap_or_default();

            if let Some(p) = pid_str.and_then(|s| s.parse::<u32>().ok()) {
                let mem_mb = mem_str
                    .replace("MiB", "")
                    .replace("MB", "")
                    .trim()
                    .parse::<u64>()
                    .unwrap_or(0);

                procs.push(GpuProcess {
                    pid: p,
                    name: name_str,
                    process_type: type_str,
                    memory_used_mb: mem_mb,
                    ai_classification: None,
                });
            }
        } else {
            break;
        }
    }

    procs
}

fn extract_xml_tag(xml: &str, tag: &str) -> Option<String> {
    let open_tag = format!("<{}>", tag);
    let close_tag = format!("</{}>", tag);

    let start = xml.find(&open_tag)? + open_tag.len();
    let end = xml[start..].find(&close_tag)? + start;
    Some(xml[start..end].trim().to_string())
}

fn probe_drm_sysfs() -> Option<GpuTelemetry> {
    let drm_dir = std::fs::read_dir("/sys/class/drm").ok()?;

    for entry in drm_dir.flatten() {
        let path = entry.path();
        let file_name = path.file_name()?.to_string_lossy();
        if file_name.starts_with("card") && !file_name.contains('-') {
            let device_dir = path.join("device");
            if !device_dir.exists() {
                continue;
            }

            // Check GPU busy percent
            let busy_file = device_dir.join("gpu_busy_percent");
            let util = if let Ok(content) = std::fs::read_to_string(busy_file) {
                content.trim().parse::<u32>().unwrap_or(0)
            } else {
                0
            };

            // Check VRAM
            let vram_used_file = device_dir.join("mem_info_vram_used");
            let vram_total_file = device_dir.join("mem_info_vram_total");

            let vram_used = std::fs::read_to_string(vram_used_file)
                .ok()
                .and_then(|s| s.trim().parse::<u64>().ok())
                .map(|b| b / (1024 * 1024))
                .unwrap_or(0);

            let vram_total = std::fs::read_to_string(vram_total_file)
                .ok()
                .and_then(|s| s.trim().parse::<u64>().ok())
                .map(|b| b / (1024 * 1024))
                .unwrap_or(0);

            // Read temperature if available
            let mut temp_c = 0;
            if let Ok(hwmon_entries) = std::fs::read_dir(device_dir.join("hwmon")) {
                for hw in hwmon_entries.flatten() {
                    let temp_file = hw.path().join("temp1_input");
                    if let Ok(c) = std::fs::read_to_string(temp_file) {
                        if let Ok(millideg) = c.trim().parse::<u32>() {
                            temp_c = millideg / 1000;
                            break;
                        }
                    }
                }
            }

            return Some(GpuTelemetry {
                name: format!("DRM {}", file_name),
                driver_version: "Linux DRM Kernel Driver".to_string(),
                utilization_gpu: util,
                memory_used_mb: vram_used,
                memory_total_mb: vram_total,
                temperature_c: temp_c,
                power_draw_w: None,
                fan_speed_pct: None,
                processes: Vec::new(),
            });
        }
    }

    None
}
