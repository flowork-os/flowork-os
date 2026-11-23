# Context & Activation Scope
Active when generating, editing, concatenating, or scripting video files, screen recordings, motion sequences, and FFmpeg rendering pipelines.

# Mandatory Behavioral Invariants
1. **Atomic Scene Encoding:** Encode each scene as a standalone video segment with uniform resolution, framerate (default 30 fps), and pixel format (`yuv420p`), then concatenate via FFmpeg concat demuxer with `-c copy`.
2. **Staged Safe Rendering:** Write output to temporary files (`.tmp.mp4`) and rename to the target filename only after FFmpeg exits with code 0 to prevent corrupt partial video files.
3. **Stream Copy Optimization:** Use `-c:v copy` when muxing audio or trimming cuts without re-encoding to preserve generation loss and execute at hardware speed.
4. **Still Frame & Web Capture Efficiency:** For still scenes, use FFmpeg loop filtering (`loop=-1:1,trim=...`) instead of generating thousands of redundant PNG frames. For page capture, use high-quality JPEG (quality 92).

# Strict Prohibitions
- PROHIBITED: Generating uncompressed individual PNG image files per frame on disk for long scenes.
- PROHIBITED: Re-encoding the entire video stream when only modifying audio tracks or lossless concat.
- PROHIBITED: Announcing video completion before verifying the rendering process returned Exit Code 0.
