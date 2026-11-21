# Flowork OS Short Video Foundry (`short_foundry`)

Autonomous generation of 9:16 vertical short videos for YouTube Shorts, Instagram Reels, and TikTok.

## Invariants
- Vertical Aspect Ratio: 1080x1920 (9:16)
- Duration Cap: <= 59.0s
- Audio: 6-channel procedural mix + edge-tts Indonesian voiceover
- Visuals: Procedural stickman rendering streamed to FFmpeg rawvideo pipe
- Delivery: Saved to `/opt/floworkos/documents/videos/` and mirrored to `~/Documents/videos/`
