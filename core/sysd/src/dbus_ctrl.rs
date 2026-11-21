// =============================================================================
// 🚀 Flowork Sovereign OS — Native D-Bus & Audio Controller (Pure Rust)
// Zero-process D-Bus IPC for MPRIS2 media, desktop notifications & audio
// =============================================================================

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::process::Command;
use zbus::zvariant;
use zbus::Connection;

#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MediaPlayerInfo {
    pub name: String,
    pub identity: String,
    pub playback_status: String,
    pub track_title: Option<String>,
    pub artist: Option<String>,
}

pub struct DbusController;

impl DbusController {
    /// Send desktop notification directly via org.freedesktop.Notifications
    pub async fn send_notification(
        app_name: &str,
        summary: &str,
        body: &str,
        icon: &str,
        expire_timeout_ms: i32,
    ) -> Result<u32, String> {
        let connection = Connection::session()
            .await
            .map_err(|e| format!("Failed to connect to session D-Bus: {}", e))?;

        let hints: HashMap<&str, zvariant::Value> = HashMap::new();
        let actions: Vec<&str> = Vec::new();

        let reply: u32 = connection
            .call_method(
                Some("org.freedesktop.Notifications"),
                "/org/freedesktop/Notifications",
                Some("org.freedesktop.Notifications"),
                "Notify",
                &(
                    app_name,
                    0u32, // replaces_id
                    icon,
                    summary,
                    body,
                    actions,
                    hints,
                    expire_timeout_ms,
                ),
            )
            .await
            .map_err(|e| format!("D-Bus Notify call failed: {}", e))?
            .body()
            .deserialize()
            .map_err(|e| format!("Failed to parse notification ID: {}", e))?;

        Ok(reply)
    }

    /// List active MPRIS2 media players on session bus
    pub async fn list_media_players() -> Result<Vec<String>, String> {
        let connection = Connection::session()
            .await
            .map_err(|e| format!("Failed to connect to session D-Bus: {}", e))?;

        let names: Vec<String> = connection
            .call_method(
                Some("org.freedesktop.DBus"),
                "/org/freedesktop/DBus",
                Some("org.freedesktop.DBus"),
                "ListNames",
                &(),
            )
            .await
            .map_err(|e| format!("Failed to list D-Bus names: {}", e))?
            .body()
            .deserialize()
            .map_err(|e| format!("Failed to deserialize names: {}", e))?;

        let mpris_players: Vec<String> = names
            .into_iter()
            .filter(|name| name.starts_with("org.mpris.MediaPlayer2."))
            .collect();

        Ok(mpris_players)
    }

    /// Control MPRIS2 media player (Play, Pause, PlayPause, Next, Previous, Stop)
    pub async fn media_control(action: &str, player_name: Option<&str>) -> Result<Value, String> {
        let players = Self::list_media_players().await?;
        if players.is_empty() {
            return Err("No active MPRIS2 media players found on D-Bus".to_string());
        }

        let target_player = if let Some(p) = player_name {
            if p.starts_with("org.mpris.MediaPlayer2.") {
                p.to_string()
            } else {
                format!("org.mpris.MediaPlayer2.{}", p)
            }
        } else {
            players[0].clone()
        };

        let method_name = match action.to_lowercase().as_str() {
            "playpause" | "play_pause" | "toggle" => "PlayPause",
            "play" => "Play",
            "pause" => "Pause",
            "next" => "Next",
            "previous" | "prev" => "Previous",
            "stop" => "Stop",
            other => return Err(format!("Unknown media action: {}", other)),
        };

        let connection = Connection::session()
            .await
            .map_err(|e| format!("Failed to connect to session D-Bus: {}", e))?;

        connection
            .call_method(
                Some(target_player.as_str()),
                "/org/mpris/MediaPlayer2",
                Some("org.mpris.MediaPlayer2.Player"),
                method_name,
                &(),
            )
            .await
            .map_err(|e| format!("MPRIS2 call {} failed on {}: {}", method_name, target_player, e))?;

        Ok(json!({
            "status": "SUCCESS",
            "action": action,
            "player": target_player
        }))
    }

    /// Get detailed status from target MPRIS2 player
    pub async fn get_media_status(player_name: Option<&str>) -> Result<Value, String> {
        let players = Self::list_media_players().await?;
        if players.is_empty() {
            return Ok(json!({
                "has_player": false,
                "players": []
            }));
        }

        let target_player = if let Some(p) = player_name {
            if p.starts_with("org.mpris.MediaPlayer2.") {
                p.to_string()
            } else {
                format!("org.mpris.MediaPlayer2.{}", p)
            }
        } else {
            players[0].clone()
        };

        let connection = Connection::session()
            .await
            .map_err(|e| format!("Failed to connect to session D-Bus: {}", e))?;

        // Query PlaybackStatus property
        let playback_status: String = match connection
            .call_method(
                Some(target_player.as_str()),
                "/org/mpris/MediaPlayer2",
                Some("org.freedesktop.DBus.Properties"),
                "Get",
                &("org.mpris.MediaPlayer2.Player", "PlaybackStatus"),
            )
            .await
        {
            Ok(msg) => {
                let body = msg.body();
                if let Ok(val) = body.deserialize::<zvariant::OwnedValue>() {
                    val.to_string().trim_matches('"').to_string()
                } else {
                    "Unknown".to_string()
                }
            }
            Err(_) => "Unknown".to_string(),
        };

        Ok(json!({
            "has_player": true,
            "player": target_player,
            "all_players": players,
            "playback_status": playback_status
        }))
    }

    /// Audio Control: Get Master Volume & Mute state
    pub fn get_master_audio() -> Result<Value, String> {
        let output = Command::new("pactl")
            .args(["get-sink-volume", "@DEFAULT_SINK@"])
            .output()
            .map_err(|e| format!("pactl command failed: {}", e))?;

        let vol_str = String::from_utf8_lossy(&output.stdout);
        let mut volume_percent = 50;

        for part in vol_str.split_whitespace() {
            if part.ends_with('%') {
                if let Ok(v) = part.trim_end_matches('%').parse::<u32>() {
                    volume_percent = v;
                    break;
                }
            }
        }

        let mute_out = Command::new("pactl")
            .args(["get-sink-mute", "@DEFAULT_SINK@"])
            .output()
            .map_err(|e| format!("pactl mute check failed: {}", e))?;

        let mute_str = String::from_utf8_lossy(&mute_out.stdout);
        let is_muted = mute_str.to_lowercase().contains("yes");

        Ok(json!({
            "volume": volume_percent,
            "muted": is_muted
        }))
    }

    /// Audio Control: Set Master Volume
    pub fn set_master_volume(percent: u32) -> Result<Value, String> {
        let capped = percent.min(100);
        let target = format!("{}%", capped);

        let output = Command::new("pactl")
            .args(["set-sink-volume", "@DEFAULT_SINK@", &target])
            .output()
            .map_err(|e| format!("Failed to set volume: {}", e))?;

        if !output.status.success() {
            return Err(String::from_utf8_lossy(&output.stderr).to_string());
        }

        Ok(json!({
            "status": "SUCCESS",
            "volume": capped
        }))
    }

    /// Audio Control: Set Master Mute
    pub fn set_master_mute(mute: Option<bool>) -> Result<Value, String> {
        let arg = match mute {
            Some(true) => "1",
            Some(false) => "0",
            None => "toggle",
        };

        let output = Command::new("pactl")
            .args(["set-sink-mute", "@DEFAULT_SINK@", arg])
            .output()
            .map_err(|e| format!("Failed to set mute: {}", e))?;

        if !output.status.success() {
            return Err(String::from_utf8_lossy(&output.stderr).to_string());
        }

        let state = Self::get_master_audio()?;
        Ok(json!({
            "status": "SUCCESS",
            "audio": state
        }))
    }
}
