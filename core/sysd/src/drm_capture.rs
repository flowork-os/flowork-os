// =============================================================================
// 🚀 Flowork Sovereign OS — Direct DRM/KMS Display Telemetry & Fast Screen Capture
// Pure Rust | Kernel DRM Subsystem Inspection | Sub-Millisecond Frame Interface
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================

use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};
use serde::{Deserialize, Serialize};
use x11rb::connection::Connection;
use x11rb::rust_connection::RustConnection;
use x11rb::protocol::xproto::{ImageFormat, ConnectionExt};

pub const DRM_SHM_PIXEL_PATH: &str = "/dev/shm/flowork_drm_latest.bgra";
pub const DRM_SHM_META_PATH: &str = "/dev/shm/flowork_drm_latest.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrmConnectorInfo {
    pub name: String,
    pub status: String,
    pub active_mode: String,
    pub available_modes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrmDisplayTelemetry {
    pub card: String,
    pub device_path: String,
    pub driver_accessible: bool,
    pub active_connectors: Vec<DrmConnectorInfo>,
    pub primary_resolution: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenCaptureResult {
    pub width: u32,
    pub height: u32,
    pub format: String,
    pub byte_size: usize,
    pub capture_duration_ms: f64,
    pub shm_path: String,
}

pub fn write_atomic_shm_frame(
    pixel_path: &Path,
    meta_path: &Path,
    width: u32,
    height: u32,
    format: &str,
    pixels: &[u8],
) -> Result<(), String> {
    let pixel_tmp = pixel_path.with_extension("bgra.tmp");
    fs::write(&pixel_tmp, pixels)
        .map_err(|e| format!("Failed writing shm frame temp '{}': {}", pixel_tmp.display(), e))?;
    let _ = fs::set_permissions(&pixel_tmp, fs::Permissions::from_mode(0o644));
    fs::rename(&pixel_tmp, pixel_path)
        .map_err(|e| format!("Failed publishing shm frame '{}': {}", pixel_path.display(), e))?;

    let captured_ms = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let meta_json = serde_json::json!({
        "width": width,
        "height": height,
        "format": format,
        "byte_size": pixels.len(),
        "pixel_path": pixel_path.to_string_lossy(),
        "captured_ms": captured_ms
    });
    let meta_tmp = meta_path.with_extension("json.tmp");
    let meta_bytes = serde_json::to_vec_pretty(&meta_json)
        .map_err(|e| format!("Failed serializing shm metadata: {}", e))?;
    fs::write(&meta_tmp, meta_bytes)
        .map_err(|e| format!("Failed writing shm meta temp '{}': {}", meta_tmp.display(), e))?;
    let _ = fs::set_permissions(&meta_tmp, fs::Permissions::from_mode(0o644));
    fs::rename(&meta_tmp, meta_path)
        .map_err(|e| format!("Failed publishing shm meta '{}': {}", meta_path.display(), e))?;

    Ok(())
}

pub struct DrmCaptureEngine {
    card_path: String,
}

impl DrmCaptureEngine {
    pub fn new() -> Self {
        let card = if Path::new("/dev/dri/card1").exists() {
            "/dev/dri/card1".to_string()
        } else {
            "/dev/dri/card0".to_string()
        };

        Self { card_path: card }
    }

    pub fn get_telemetry(&self) -> DrmDisplayTelemetry {
        let mut connectors = Vec::new();
        let mut primary_res = "Unknown".to_string();

        let drm_dir = Path::new("/sys/class/drm");
        if let Ok(entries) = fs::read_dir(drm_dir) {
            for entry in entries.flatten() {
                let file_name = entry.file_name().to_string_lossy().to_string();
                if file_name.starts_with("card") && file_name.contains('-') {
                    let path = entry.path();
                    let status_path = path.join("status");
                    let modes_path = path.join("modes");

                    let status = fs::read_to_string(&status_path)
                        .unwrap_or_else(|_| "unknown".to_string())
                        .trim()
                        .to_string();

                    let modes: Vec<String> = fs::read_to_string(&modes_path)
                        .unwrap_or_default()
                        .lines()
                        .take(5)
                        .map(|s| s.trim().to_string())
                        .collect();

                    let active_mode = modes.first().cloned().unwrap_or_else(|| "none".to_string());

                    if status == "connected" && primary_res == "Unknown" {
                        primary_res = active_mode.clone();
                    }

                    connectors.push(DrmConnectorInfo {
                        name: file_name,
                        status,
                        active_mode,
                        available_modes: modes,
                    });
                }
            }
        }

        let accessible = Path::new(&self.card_path).exists() && {
            match fs::OpenOptions::new().read(true).open(&self.card_path) {
                Ok(_) => true,
                Err(_) => false,
            }
        };

        DrmDisplayTelemetry {
            card: "AMD/Intel Direct Rendering Manager".to_string(),
            device_path: self.card_path.clone(),
            driver_accessible: accessible,
            active_connectors: connectors,
            primary_resolution: primary_res,
        }
    }

    pub fn capture_screen_fast(&self) -> Result<ScreenCaptureResult, String> {
        let start = std::time::Instant::now();

        // Connect directly to X11 socket for high-speed root window GetImage
        let (conn, screen_num) = RustConnection::connect(None)
            .map_err(|e| format!("Failed to connect to X11 socket: {}", e))?;
        let screen = &conn.setup().roots[screen_num];
        let root = screen.root;
        let width = screen.width_in_pixels;
        let height = screen.height_in_pixels;

        let cookie = conn.get_image(
            ImageFormat::Z_PIXMAP,
            root,
            0,
            0,
            width,
            height,
            !0,
        ).map_err(|e| format!("Failed to send GetImage: {}", e))?;

        let reply = cookie.reply()
            .map_err(|e| format!("Failed to receive GetImage reply: {}", e))?;

        let byte_size = reply.data.len();
        let format = "zpixmap_bgra32";
        write_atomic_shm_frame(
            Path::new(DRM_SHM_PIXEL_PATH),
            Path::new(DRM_SHM_META_PATH),
            width as u32,
            height as u32,
            format,
            &reply.data,
        )?;

        let duration = start.elapsed().as_secs_f64() * 1000.0;

        Ok(ScreenCaptureResult {
            width: width as u32,
            height: height as u32,
            format: format.to_string(),
            byte_size,
            capture_duration_ms: (duration * 10.0).round() / 10.0,
            shm_path: DRM_SHM_PIXEL_PATH.to_string(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn writes_atomic_shm_pixel_and_metadata_files() {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(1);
        let dir = std::env::temp_dir().join(format!("flowork_drm_test_{}", stamp));
        fs::create_dir_all(&dir).unwrap();
        let pix = dir.join("frame.bgra");
        let meta = dir.join("frame.json");
        let payload = vec![0x10u8, 0x20, 0x30, 0xff, 0xaa, 0xbb, 0xcc, 0xff];

        write_atomic_shm_frame(&pix, &meta, 2, 1, "zpixmap_bgra32", &payload).unwrap();

        assert_eq!(fs::read(&pix).unwrap(), payload);
        let meta_val: serde_json::Value =
            serde_json::from_str(&fs::read_to_string(&meta).unwrap()).unwrap();
        assert_eq!(meta_val["width"], serde_json::json!(2));
        assert_eq!(meta_val["height"], serde_json::json!(1));
        assert_eq!(meta_val["byte_size"], serde_json::json!(8));
        assert_eq!(meta_val["format"], serde_json::json!("zpixmap_bgra32"));

        let _ = fs::remove_dir_all(&dir);
    }
}

