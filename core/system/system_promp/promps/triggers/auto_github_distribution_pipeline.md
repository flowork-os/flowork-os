# GITHUB DISTRIBUTION & VERSIONED RELEASE PROTOCOL

## 1. Context & Activation Scope
Activated during GitHub repository synchronization, OTA manifest updates, or GitHub Releases ISO publishing (`upload-flowork-os.sh`, `release-iso.sh`, `build-live-iso.sh`).

## 2. Mandatory Behavioral Invariants
- **Strict Zero-Leak Audit:** Exclude `vault.json`, PAT tokens, SSH keys, browser `user_data`, and chat histories (`history/chats/`) before staging commits; restore remote `origin` to clean HTTPS post-push.
- **GitHub Asset Caps & Streaming Upload:** Keep repo objects `< 95 MB`. Split `> 2 GiB` Live ISOs into `1800 MiB` (`< 1.8 GiB`) `.part` files, verify reassembled SHA-256 bit-for-bit, and stream uploads with `curl -X POST -T <file> -H "Content-Length: ..."` (`--http1.1`).
- **Atomic & Non-Destructive Releases:** Create releases as `draft: true`, verify every asset `state == "uploaded"` and exact byte `size`, then publish (`draft: false`). Never overwrite published release tags or delete prior releases.
- **OTA Sync Completeness:** Sync compiled system daemons (`flowork-sysd`, `mrflow`) and their Rust sources before generating `manifest.json.gz`.

## 3. Strict Prohibitions
- Never use `curl --data-binary @<large_file>` on multi-gigabyte release parts (causes OOM).
- Never hardcode `git tag -f` or `git push --force` on existing release tags inside distribution sync scripts.
