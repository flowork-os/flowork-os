use sysinfo::{CpuRefreshKind, MemoryRefreshKind, ProcessRefreshKind, RefreshKind, System};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::ai_detector::classify_process;
use crate::gpu::GpuProcess;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessItem {
    pub pid: u32,
    pub name: String,
    pub cpu_pct: f32,
    pub mem_mb: u64,
    pub vram_mb: u64,
    pub ai_tag: Option<String>,
    pub cmdline: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemTelemetry {
    pub host_name: String,
    pub kernel_version: String,
    pub uptime_secs: u64,
    pub cpu_total_pct: f32,
    pub cpu_cores: usize,
    pub mem_total_mb: u64,
    pub mem_used_mb: u64,
    pub swap_total_mb: u64,
    pub swap_used_mb: u64,
    pub processes: Vec<ProcessItem>,
}

pub struct SystemTracker {
    sys: System,
}

impl SystemTracker {
    pub fn new() -> Self {
        let refresh_kind = RefreshKind::nothing()
            .with_cpu(CpuRefreshKind::everything())
            .with_memory(MemoryRefreshKind::everything())
            .with_processes(ProcessRefreshKind::everything());

        let mut sys = System::new_with_specifics(refresh_kind);
        sys.refresh_all();
        Self { sys }
    }

    pub fn snapshot(&mut self, gpu_processes: &[GpuProcess]) -> SystemTelemetry {
        self.sys.refresh_all();

        let host_name = System::host_name().unwrap_or_else(|| "flowork".to_string());
        let kernel_version = System::kernel_version().unwrap_or_else(|| "Linux 7.3.0-flowork-rust".to_string());
        let uptime_secs = System::uptime();

        let cpu_total_pct = self.sys.global_cpu_usage();
        let cpu_cores = self.sys.cpus().len();

        let mem_total_mb = self.sys.total_memory() / (1024 * 1024);
        let mem_used_mb = self.sys.used_memory() / (1024 * 1024);
        let swap_total_mb = self.sys.total_swap() / (1024 * 1024);
        let swap_used_mb = self.sys.used_swap() / (1024 * 1024);

        // Map GPU processes by PID for fast correlation
        let mut gpu_map: HashMap<u32, u64> = HashMap::new();
        for gp in gpu_processes {
            gpu_map.insert(gp.pid, gp.memory_used_mb);
        }

        let mut processes = Vec::new();
        for (pid, proc_) in self.sys.processes() {
            let pid_u32 = pid.as_u32();
            let name = proc_.name().to_string_lossy().to_string();
            let cpu_pct = proc_.cpu_usage();
            let mem_mb = proc_.memory() / (1024 * 1024);
            let vram_mb = gpu_map.get(&pid_u32).copied().unwrap_or(0);

            let ai_tag = classify_process(pid_u32, &name).map(|ai| {
                if let Some(hint) = ai.model_hint {
                    format!("{}: {}", ai.category, hint)
                } else {
                    ai.category
                }
            });

            // Get cmdline preview
            let cmdline = proc_
                .cmd()
                .iter()
                .map(|s| s.to_string_lossy().to_string())
                .collect::<Vec<_>>()
                .join(" ");

            // Include if non-trivial or has GPU/AI or top resource usage
            if cpu_pct > 0.1 || mem_mb > 50 || vram_mb > 0 || ai_tag.is_some() {
                processes.push(ProcessItem {
                    pid: pid_u32,
                    name,
                    cpu_pct,
                    mem_mb,
                    vram_mb,
                    ai_tag,
                    cmdline,
                });
            }
        }

        // Sort initially by VRAM descending, then CPU descending
        processes.sort_by(|a, b| {
            b.vram_mb
                .cmp(&a.vram_mb)
                .then_with(|| b.cpu_pct.partial_cmp(&a.cpu_pct).unwrap_or(std::cmp::Ordering::Equal))
        });

        SystemTelemetry {
            host_name,
            kernel_version,
            uptime_secs,
            cpu_total_pct,
            cpu_cores,
            mem_total_mb,
            mem_used_mb,
            swap_total_mb,
            swap_used_mb,
            processes,
        }
    }
}
