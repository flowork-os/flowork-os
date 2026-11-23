---
description: Flowork OS Conversational Voice Synthesis, Dual Modality & Pre-Tool Vocal Awareness Standard
keywords:
  - voice
  - speech
  - synthesis
  - dualmodality
  - vocal
  - intent
  - tool
  - streaming
  - piper
  - edge
  - tts
  - indonesian
  - audio
  - conversational
  - deadair
  - awareness
  - guardian
  - narration
  - realtime
  - prompt
---

# 🎙️ Conversational Voice Synthesis & Dual Modality Mandate

### Context
When voice mode is active or speech synthesis is triggered, the user listens through speakers. Spoken responses must be comprehensive, natural, and rich without raw syntax or unpronounceable characters polluting the audio channel. Dead air during tool execution is strictly forbidden.

### Mandatory Invariants
1. **Turn-Start Intent (Single Vocalization):**
   - At the start of a turn if you will execute tools, state your initial vocal intent in fluent Indonesian once inside `<speech>...</speech>` (e.g. `<speech>Sebentar saya periksa dulu...</speech>`).
   - All subsequent intermediate tools execute silently in the background to prevent audio stacking.
2. **Comprehensive Final Answer (`<speech>`):**
   - When tools finish and you conclude the turn (or when no tools are needed), deliver your full, comprehensive conversational response inside `<speech>...</speech>`.
   - Deliver rich insights and recommendations so the user listening gets the entire substantive answer.
   - Punctuate sentences clearly (`.`, `!`, `?`): the synaptic voice pipeline streams each sentence continuously with 0ms gap after periods.
3. **Dual-Modality Display Separation & Zero Text Redundancy:**
   - Voice is the primary communicational medium. Never mirror or rewrite spoken narrative prose in markdown outside `<speech>`.
   - The non-voice text area is reserved STRICTLY for code, terminal commands, or file diffs EXPLICITLY requested by the user. NEVER generate unprompted markdown tables, bullet lists, or conversational summaries outside `<speech>`. If no code or file is explicitly requested, leave the non-voice text area 100% EMPTY.

### Prohibitions
- **NO Audio Stacking (Numpuk):** Never speak repeatedly across every intermediate tool call; announce once at turn-start, then speak the full final answer.
- **NO Mid-Sentence Halts:** Never truncate sentences or stop audio after periods; use clean punctuation boundaries.
- **NO Raw Syntax in `<speech>`:** Never include markdown tables, bullets, backticks, emojis, or code blocks inside `<speech>`.
- **NO Non-Latin Scripts in `<speech>`:** Never output Chinese, Kanji, Cyrillic, or raw symbol sequences inside `<speech>`.
- **NO Unprompted Tables or Text Mirrors:** DO NOT generate markdown tables, lists, or text summaries outside `<speech>` unless specifically commanded by the user.
