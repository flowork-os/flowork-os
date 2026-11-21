# SUNO AUDIO PIPELINE & COPYRIGHT BYPASS DIRECTIVE

## 1. Context & Activation Scope
Triggered when generating AI music covers, handling copyright bypass, isolating vocals via Demucs, or orchestrating Suno audio generation workflows.

## 2. Mandatory Behavioral Invariants
- Isolate clean vocal stems using Demucs (`--two-stems vocals -n htdemucs`) prior to any remixing or acoustic alteration.
- Modulate vocal stems to 5.0x speed with proportional pitch elevation using FFmpeg (`asetrate=44100*5,aresample=44100`) to shatter acoustic fingerprints (ACRCloud/Audible Magic) while retaining melodic contour and staying under the 60-second upload ceiling. Alternatively, execute `flowork-vocal-to-piano` to extract fundamental pitch ($F_0$) via YIN and synthesize clean Grand Piano audio (`.mp3`) and MIDI (`.mid`) stripping all vocal lyrics.
- Format lyrics into phonetic Pinyin or dual Hanzi/Pinyin and structure song tags (`[Verse]`, `[Chorus]`, `[Outro]`) explicitly before dispatching to generation.
- Enforce the Cover mode dropdown (`create.modeAdvanced`) and provide precise cinematic Guofeng/Mandopop style descriptors with target BPM.
- Validate finished generation status empirically: verify duration indicators (>1:00) and playable media containers (`.mp4`/`.mp3`) before claiming task completion.

## 3. Strict Prohibitions
- Never upload unmodulated or full instrumental audio stems directly to Suno; doing so triggers immediate fingerprint rejections.
- Never claim audio synthesis completion based solely on task launch; confirm delivery in the user's library with Exit Code 0 file extraction.
- Never hardcode personal user directories in pipeline automation scripts; resolve dynamically via `$HOME`.
