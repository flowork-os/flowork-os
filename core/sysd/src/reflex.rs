// =============================================================================
// 🚀 Flowork Sovereign OS — Fast-Path Reflex Engine (Pure Rust)
// Zero-LLM sub-millisecond intent evaluation & execution
// =============================================================================

use crate::cdp_pool::CdpController;
use crate::dbus_ctrl::DbusController;
use crate::x11_ctrl::X11Controller;
use regex::Regex;
use serde_json::{json, Value};
use std::time::Instant;

pub struct ReflexEngine;

impl ReflexEngine {
    /// Evaluate intent string against deterministic fast-path matchers
    pub async fn evaluate_intent(intent: &str) -> Option<Value> {
        let clean = intent.trim().to_lowercase();
        let start_time = Instant::now();

        // 1. Audio Volume: volume 70% / set volume to 80
        let re_vol = Regex::new(r"(?:volume|vol)\s*(?:ke|to|=)?\s*(\d+)%?").ok()?;
        if let Some(caps) = re_vol.captures(&clean) {
            if let Some(vol_match) = caps.get(1) {
                if let Ok(vol) = vol_match.as_str().parse::<u32>() {
                    let res = DbusController::set_master_volume(vol).ok()?;
                    let elapsed_ms = start_time.elapsed().as_millis();
                    return Some(json!({
                        "handled": true,
                        "type": "audio_volume",
                        "elapsed_ms": elapsed_ms,
                        "result": res
                    }));
                }
            }
        }

        // 2. Audio Mute / Unmute
        if clean == "mute" || clean == "bisu" || clean == "senyapkan" {
            let res = DbusController::set_master_mute(Some(true)).ok()?;
            let elapsed_ms = start_time.elapsed().as_millis();
            return Some(json!({
                "handled": true,
                "type": "audio_mute",
                "elapsed_ms": elapsed_ms,
                "result": res
            }));
        }
        if clean == "unmute" || clean == "bunyikan" {
            let res = DbusController::set_master_mute(Some(false)).ok()?;
            let elapsed_ms = start_time.elapsed().as_millis();
            return Some(json!({
                "handled": true,
                "type": "audio_unmute",
                "elapsed_ms": elapsed_ms,
                "result": res
            }));
        }

        // 3. Media Controls
        if clean == "play" || clean == "putar" {
            let res = DbusController::media_control("play", None).await.ok()?;
            let elapsed_ms = start_time.elapsed().as_millis();
            return Some(json!({
                "handled": true,
                "type": "media_play",
                "elapsed_ms": elapsed_ms,
                "result": res
            }));
        }
        if clean == "pause" || clean == "jeda" {
            let res = DbusController::media_control("pause", None).await.ok()?;
            let elapsed_ms = start_time.elapsed().as_millis();
            return Some(json!({
                "handled": true,
                "type": "media_pause",
                "elapsed_ms": elapsed_ms,
                "result": res
            }));
        }
        if clean == "next song" || clean == "lagu berikutnya" || clean == "next track" {
            let res = DbusController::media_control("next", None).await.ok()?;
            let elapsed_ms = start_time.elapsed().as_millis();
            return Some(json!({
                "handled": true,
                "type": "media_next",
                "elapsed_ms": elapsed_ms,
                "result": res
            }));
        }

        // 4. Chrome Tabs Listing
        if clean == "list tabs" || clean == "daftar tab" || clean == "tabs" {
            let tabs = CdpController::list_tabs().await.ok()?;
            let elapsed_ms = start_time.elapsed().as_millis();
            return Some(json!({
                "handled": true,
                "type": "browser_tabs",
                "elapsed_ms": elapsed_ms,
                "count": tabs.len(),
                "tabs": tabs
            }));
        }

        // 5. Window List
        if clean == "list windows" || clean == "daftar jendela" || clean == "windows" {
            let wins = X11Controller::get_windows().ok()?;
            let elapsed_ms = start_time.elapsed().as_millis();
            return Some(json!({
                "handled": true,
                "type": "x11_windows",
                "elapsed_ms": elapsed_ms,
                "count": wins.len(),
                "windows": wins
            }));
        }

        // 6. Window Tiling
        if clean.contains("tile left") || clean.contains("sebelah kiri") {
            let wins = X11Controller::get_windows().ok()?;
            if let Some(active) = wins.iter().find(|w| w.is_active) {
                let res = X11Controller::tile_window(active.id, "left").ok()?;
                let elapsed_ms = start_time.elapsed().as_millis();
                return Some(json!({
                    "handled": true,
                    "type": "tile_window_left",
                    "elapsed_ms": elapsed_ms,
                    "result": res
                }));
            }
        }
        if clean.contains("tile right") || clean.contains("sebelah kanan") {
            let wins = X11Controller::get_windows().ok()?;
            if let Some(active) = wins.iter().find(|w| w.is_active) {
                let res = X11Controller::tile_window(active.id, "right").ok()?;
                let elapsed_ms = start_time.elapsed().as_millis();
                return Some(json!({
                    "handled": true,
                    "type": "tile_window_right",
                    "elapsed_ms": elapsed_ms,
                    "result": res
                }));
            }
        }

        // 7. System Quick Status
        if clean == "status pc" || clean == "system status" || clean == "status" {
            let audio = DbusController::get_master_audio().unwrap_or(Value::Null);
            let cdp_port = CdpController::get_active_cdp_port().await;
            let wins = X11Controller::get_windows().unwrap_or_default();
            let elapsed_ms = start_time.elapsed().as_millis();

            return Some(json!({
                "handled": true,
                "type": "system_status",
                "elapsed_ms": elapsed_ms,
                "audio": audio,
                "cdp_port": cdp_port,
                "window_count": wins.len(),
                "active_window": wins.iter().find(|w| w.is_active).map(|w| &w.title)
            }));
        }

        None
    }
}
