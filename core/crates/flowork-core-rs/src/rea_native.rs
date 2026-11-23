use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::Read;
use std::path::Path;
use std::process::Command;

fn command_exists(bin: &str) -> bool {
    Command::new("which")
        .arg(bin)
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

fn run_util(bin: &str, args: &[&str]) -> Result<String, String> {
    let out = Command::new(bin)
        .args(args)
        .output()
        .map_err(|e| format!("Failed to launch {}: {}", bin, e))?;
    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
        return Err(if stderr.is_empty() {
            format!("{} exited with status {:?}", bin, out.status.code())
        } else {
            stderr
        });
    }
    Ok(String::from_utf8_lossy(&out.stdout).to_string())
}

fn parse_magic_header(prefix: &[u8]) -> Value {
    if prefix.len() >= 4 && &prefix[0..4] == b"\x7fELF" {
        let class = match prefix.get(4).copied() {
            Some(1) => "ELF32",
            Some(2) => "ELF64",
            _ => "ELF",
        };
        let endian = match prefix.get(5).copied() {
            Some(1) => "little-endian",
            Some(2) => "big-endian",
            _ => "unknown-endian",
        };
        let etype = if prefix.len() >= 18 {
            let val = if prefix.get(5).copied() == Some(2) {
                u16::from_be_bytes([prefix[16], prefix[17]])
            } else {
                u16::from_le_bytes([prefix[16], prefix[17]])
            };
            match val {
                1 => "ET_REL",
                2 => "ET_EXEC",
                3 => "ET_DYN",
                4 => "ET_CORE",
                _ => "ET_OTHER",
            }
        } else {
            "unknown"
        };
        return json!({
            "format": class,
            "endianness": endian,
            "elf_type": etype,
        });
    }
    if prefix.len() >= 2 && &prefix[0..2] == b"MZ" {
        return json!({ "format": "PE/MZ" });
    }
    if prefix.len() >= 4 && (&prefix[0..4] == b"\xfe\xed\xfa\xcf" || &prefix[0..4] == b"\xcf\xfa\xed\xfe") {
        return json!({ "format": "Mach-O" });
    }
    if prefix.len() >= 4 && &prefix[0..4] == b"\x00asm" {
        return json!({ "format": "WebAssembly" });
    }
    json!({ "format": "unknown_or_data" })
}

fn extract_ascii_strings(bytes: &[u8], min_len: usize, limit: usize) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = Vec::new();
    for &b in bytes {
        if b.is_ascii_graphic() || b == b' ' || b == b'\t' {
            cur.push(b);
        } else {
            if cur.len() >= min_len {
                if let Ok(s) = std::str::from_utf8(&cur) {
                    out.push(s.to_string());
                    if out.len() >= limit {
                        return out;
                    }
                }
            }
            cur.clear();
        }
    }
    if cur.len() >= min_len && out.len() < limit {
        if let Ok(s) = std::str::from_utf8(&cur) {
            out.push(s.to_string());
        }
    }
    out
}

fn ensure_readable_target(target: &str) -> Result<Vec<u8>, String> {
    if target.is_empty() {
        return Err("Error: 'target' binary path is required.".to_string());
    }
    let p = Path::new(target);
    let meta = fs::metadata(p).map_err(|e| format!("Cannot stat '{}': {}", target, e))?;
    if !meta.is_file() {
        return Err(format!("Target '{}' is not a regular file.", target));
    }
    let mut f = File::open(p).map_err(|e| format!("Permission or read error on '{}': {}", target, e))?;
    let cap = meta.len().min(32 * 1024 * 1024) as usize;
    let mut buf = Vec::with_capacity(cap);
    (&mut f)
        .take(32 * 1024 * 1024)
        .read_to_end(&mut buf)
        .map_err(|e| format!("Read failed on '{}': {}", target, e))?;
    Ok(buf)
}

pub fn execute_rea(command: &str, target: Option<&str>, args: &[String]) -> Result<Value, String> {
    match command {
        "capabilities" => Ok(json!({
            "engine": "flowork-rea-native-rust",
            "version": "2.0.0-sovereign",
            "zero_node": true,
            "commands": [
                "capabilities",
                "doctor",
                "inspect-artifact",
                "inspect-binary-layout",
                "analyze",
                "xrefs",
                "search",
                "function",
                "decompile"
            ],
            "backends": {
                "elf_parser": true,
                "readelf": command_exists("readelf"),
                "objdump": command_exists("objdump"),
                "nm": command_exists("nm"),
                "strings": command_exists("strings"),
                "file": command_exists("file"),
            }
        })),
        "doctor" => Ok(json!({
            "status": "healthy",
            "runtime": "native-rust",
            "tools": {
                "readelf": command_exists("readelf"),
                "objdump": command_exists("objdump"),
                "nm": command_exists("nm"),
                "strings": command_exists("strings"),
                "file": command_exists("file"),
            }
        })),
        "inspect-artifact" | "inspect-binary-layout" | "analyze" => {
            let t = target.unwrap_or("");
            let bytes = ensure_readable_target(t)?;
            let mut hasher = Sha256::new();
            hasher.update(&bytes);
            let sha256 = format!("{:x}", hasher.finalize());
            let magic = parse_magic_header(&bytes[..bytes.len().min(64)]);
            let file_desc = run_util("file", &["-b", t]).unwrap_or_else(|_| "unknown".to_string());
            let sections = run_util("readelf", &["-S", "-W", t])
                .map(|s| s.lines().take(80).collect::<Vec<_>>().join("\n"))
                .unwrap_or_default();
            let symbols = run_util("nm", &["-D", t])
                .or_else(|_| run_util("nm", &[t]))
                .map(|s| s.lines().take(120).collect::<Vec<_>>().join("\n"))
                .unwrap_or_default();
            let strings_sample = extract_ascii_strings(&bytes, 6, 80);

            Ok(json!({
                "status": "ok",
                "command": command,
                "target": t,
                "size_bytes": fs::metadata(t).map(|m| m.len()).unwrap_or(bytes.len() as u64),
                "sha256_prefix_window": sha256,
                "magic": magic,
                "file_description": file_desc.trim(),
                "sections_summary": sections,
                "symbols_summary": symbols,
                "strings_sample": strings_sample,
            }))
        }
        "search" => {
            let t = target.unwrap_or("");
            let bytes = ensure_readable_target(t)?;
            let query = args.first().map(|s| s.as_str()).unwrap_or("");
            let all_strings = extract_ascii_strings(&bytes, 4, 2000);
            let matches: Vec<String> = if query.is_empty() {
                all_strings.into_iter().take(100).collect()
            } else {
                let q = query.to_ascii_lowercase();
                all_strings
                    .into_iter()
                    .filter(|s| s.to_ascii_lowercase().contains(&q))
                    .take(100)
                    .collect()
            };
            Ok(json!({
                "status": "ok",
                "target": t,
                "query": query,
                "match_count": matches.len(),
                "matches": matches,
            }))
        }
        "xrefs" => {
            let t = target.unwrap_or("");
            let _bytes = ensure_readable_target(t)?;
            let sym = args.first().map(|s| s.as_str()).unwrap_or("");
            let dis = run_util("objdump", &["-d", "--no-show-raw-insn", t])
                .map_err(|e| format!("objdump failed: {}", e))?;
            let hits: Vec<&str> = dis
                .lines()
                .filter(|line| sym.is_empty() || line.contains(sym))
                .take(80)
                .collect();
            Ok(json!({
                "status": "ok",
                "target": t,
                "symbol": sym,
                "hits": hits,
            }))
        }
        "function" | "decompile" => {
            let t = target.unwrap_or("");
            let _bytes = ensure_readable_target(t)?;
            let sym = args.first().map(|s| s.as_str()).unwrap_or("");
            let dis = run_util("objdump", &["-d", "-C", t])
                .map_err(|e| format!("objdump failed: {}", e))?;
            let mut snippet = Vec::new();
            let mut capturing = sym.is_empty();
            for line in dis.lines() {
                if !sym.is_empty() && line.contains(&format!("<{}>:", sym)) {
                    capturing = true;
                } else if capturing && !sym.is_empty() && line.trim().is_empty() && !snippet.is_empty() {
                    break;
                }
                if capturing {
                    snippet.push(line);
                    if snippet.len() >= 150 {
                        break;
                    }
                }
            }
            Ok(json!({
                "status": "ok",
                "command": command,
                "target": t,
                "function": sym,
                "disassembly": snippet.join("\n"),
            }))
        }
        other => Err(format!("Unsupported rea command '{}'", other)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rea_capabilities_works_offline_without_node() {
        let res = execute_rea("capabilities", None, &[]).expect("capabilities");
        assert_eq!(res["engine"], "flowork-rea-native-rust");
        assert_eq!(res["zero_node"], true);
    }

    #[test]
    fn rea_rejects_missing_or_unreadable_file() {
        let res = execute_rea("analyze", Some("/nonexistent/flowork_missing_bin"), &[]);
        assert!(res.is_err());
    }
}
