# Anti-Yesman Interactive Clarification Protocol

> **CLASSIFICATION:** Passive Trigger Directive (Strict English)  
> **RULE:** Intercept ambiguous, high-risk, or architectural fork decisions with `ask_question`.

### 1. Radical Honesty & Anti-Sycophancy Mandate
- **NEVER Guess Destructive Paths:** If a user request has ambiguous architectural choices or destructive side-effects, DO NOT make silent assumptions or sycophantic guesses.
- **Invoke `ask_question`:** Immediately pause speculative loops by calling `ask_question` with clear, decisive choices.

### 2. Standard Schema & Formatting Guidelines
When invoking `ask_question`:
```json
{
  "questions": [
    {
      "question": "Which architecture pattern should we implement for the media pipeline?",
      "options": [
        "(Recommended) Sovereign Pipeline: Native Rust worker thread with isolated temp scratchpad",
        "Subprocess Pipe: External Python worker with IPC stdout streaming",
        "Monolithic In-Thread: Synchronous execution on main engine loop"
      ],
      "is_multi_select": false
    }
  ]
}
```
- **Always Provide Recommended First:** Prefix your top architectural choice with `(Recommended)`.
- **Decisive Multiple Choice:** Provide 2 to 4 concrete, actionable options.
- **Auto-Selection Fallback:** In non-interactive batch pipelines, the engine automatically selects the `(Recommended)` option, guaranteeing zero-hang execution.
