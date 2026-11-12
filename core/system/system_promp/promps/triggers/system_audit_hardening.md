# SYSTEM AUDIT & HARDENING INVARIANTS

## 1. Context & Activation Scope
Triggered during Flowork OS security audits, permission hardening, firmware diagnostics, systemd unit verification, or package registry cleanup.

## 2. Mandatory Behavioral Invariants
- **Atomic Credential Modes:** Enforce `0600` (`OpenOptionsExt::mode(0o600)` + `set_permissions`) before atomic renames on `vault.json`; never rely on process umask. Mirror `600 1000:1000` in ISO pseudo-files and `chmod 600` in `flowork-session.sh`.
- **Empirical Bug Triage:** Verify root causes directly against running kernel config (`/boot/config-*`), unit files (`systemd-analyze verify`), and live services before editing.
- **Registry & Lock Hygiene:** Exclude WebExtensions (`manifest_version` without `app.json`) and deduplicate symlinked app directories in `flowpkg`/`flow-app`; clear only dead-PID unlocked Gecko profile locks.
- **Desktop, Script & OTA Hygiene:** Normalize `.desktop` categories (`X-Flowork;`, `X-Design;`), keep `Actions=` inside `[Desktop Entry]`, validate with `desktop-file-validate`, forbid CRLF endings, self-loop symlinks, or Python stdlib shadows (`tokenize.py`/`token.py`), and track symlinks + sub-manifests in `flowork-manifest-gen`.
- **FUSE & Firmware Guards:** Guard `xdg-document-portal` with `ConditionPathExists=/dev/fuse` drop-ins; decompress `.fw.zst` when `CONFIG_FW_LOADER_COMPRESS` is disabled.
- **Transport, Archive & IPC Hardening:** Forbid `ssl._create_unverified_context()`, validate tar escapes, enforce centralized SSRF DNS-pinning/redirect guards (`ssrf.rs`), use `mktemp -d` or `0700` `~/.flowork` paths over predictable `/tmp`, and set `1777` sticky `/run/flowork`.

## 3. Strict Prohibitions
- Never view or dump `vault.json` or credential tokens, nor sweep `/usr/lib/python3` for `*token*`/`*.pem`.
- Never restore Node.js/npm to silence legacy audit hits, nor parse GNOME Shell CSS as GTK3.
- Never modify locked base prompts (`00_`, `01_`, `02_`).
