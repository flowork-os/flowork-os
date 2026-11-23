---
description: PersonaPlex Voice Daemon Spool Architecture & Zero-Leak Acoustic Housekeeper Garbage Collector
keywords:
  - voice
  - daemon
  - housekeeper
  - spool
  - audio
  - garbage
  - collector
  - purge
  - cleanup
  - memory
  - tts
  - synthesis
  - playback
  - paplay
  - unlinking
  - leak
  - orphan
  - mp3
  - wav
  - personaplex
---

# 🛡️ PersonaPlex Acoustic Housekeeper & Zero-Leak Spool Doctrine

### Context
When synthesizing high-frequency speech streams and single-shot responses, the voice daemon generates short-lived audio chunks. Without deterministic garbage collection and isolated spooling, unexpected restarts, crashes, or unhandled exceptions can leave orphan audio files in RAM.

### Mandatory Architecture & Runtime Invariants
1. **Isolated Spool Directory (`AUDIO_SPOOL_DIR`):**
   - Synthesize all temporary audio chunks exclusively into `flowork-voice-spool` inside `/run/user/<uid>` or `/dev/shm` with mode 0700.
   - Never clutter user runtime root or persistent storage with audio cache files.
2. **Guaranteed Post-Playback Unlinking (`try ... finally`):**
   - In `playback_worker_loop` and `_playback_monitor`, wrap playback in `try ... finally` blocks to ensure that chunk files and single-shot files are unlinked (`os.remove()`) in all execution branches.
3. **Startup Sanitary Sweep:**
   - On daemon startup (`run_server()`), immediately execute `purge_audio_spool(max_age_seconds=0.0)` to clean all leftover audio files from prior crashed sessions.
4. **Autonomous Periodic Housekeeper:**
   - Maintain a background watchdog thread (`audio_housekeeper_loop`) running every 30 seconds that purges any audio spool file older than 30 seconds.
5. **Clean Signal Termination:**
   - On `SIGTERM` / `SIGINT`, invoke `purge_audio_spool(0.0)` to ensure zero orphan audio artifacts remain upon shutdown.
