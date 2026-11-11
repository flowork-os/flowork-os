---
title: GitHub Releases Streaming ISO Upload & Non-Destructive Version Tagging
category: distribution
keywords:
  - github_releases_upload
  - curl_streaming_upload_file
  - curl_data_binary_oom
  - iso_split_chunks
  - draft_release_atomic
  - preserve_existing_releases
  - git_tag_force_guard
  - flowork_sysd_ota_sync
  - agent_bridge_rs
  - sha256_reassembly_verify
date: 2026-11-11
---

# GitHub Releases Streaming Upload & Non-Destructive Versioning

## Root Causes Solved (2026-11-11)
1. **`curl --data-binary` OOM on 1.88 GB ISO chunks:** `curl --data-binary @file` attempts to allocate a contiguous in-memory buffer and fails on 1.8 GiB `.part` assets (`curl: option --data-binary: out of memory`).
2. **Release Tag Overwrite Hazard:** Hardcoded `git tag -f -a v1.0.0 && git push --force ... v1.0.0` in `upload-flowork-os.sh` forcibly moved `v1.0.0` on every `main` sync and risked dirtying `core/system/version.json` post-push.
3. **OTA Gap for `flowork-sysd`:** `upload-flowork-os.sh` synced `mrflow-rs` but omitted `/opt/floworkos/sysd/` (`agent_bridge.rs`, `main.rs`, `routes.rs`) and `/usr/local/bin/flowork-sysd`.

## Canonical Fixes Implemented
- **Streaming Upload (`release-iso.sh`):** Split ISOs (`1800M` / `1,887,436,800 bytes`), validate `cat *.part | sha256sum`, create a `draft: true` GitHub Release, stream assets via `curl --http1.1 -X POST -T "${asset_file}" -H "Content-Length: ${bytes}" -H "Expect:"`, verify remote `state == "uploaded"` and exact byte counts, then `PATCH {"draft": false}`.
- **Version Protection (`upload-flowork-os.sh`):** Guard optional tagging via `FLOWORK_RELEASE_TAG` with `ls-remote` existence check (`ALLOW_FORCE_TAG=1` required for overrides) and update `/opt/floworkos/system/version.json` without leaving `/opt/flowork-os-repo` dirty post-push.
- **Full `sysd` OTA Parity:** Added `sysd/src/*`, `Cargo.{toml,lock}`, and `/usr/local/bin/flowork-sysd` syncing to `upload-flowork-os.sh`.
