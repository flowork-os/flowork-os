# ⏱️ Native Asynchronous Scheduling & Background Timer Doctrine
- **Tool Authority:** Use `schedule` for all deferred notifications, interval executions, and recurring cron jobs.
- **One-Shot Timers:** Specify `DurationSeconds` (integer) and `Prompt` (notification text). Optional `TimerCondition`: `'never'` (default), `'any'` (cancel on any message), or specific sender ID.
- **Recurring Crons:** Specify `CronExpression` (5-field cron, e.g. `'*/5 * * * *'`) and `Prompt`. Use `MaxIterations` for finite loops, or `IsDaemon: true` for persistent standing jobs.
- **Strict Prohibition of Blocking Sleep:** NEVER execute blocking `sleep` commands in foreground or background shell to wait for time to pass. Doing so wastes system resources and halts agent progress.
- **Task Cancellation & Lifecycle:** Timers and crons are tracked in `ProcessRegistry`. Cancel any running schedule using `manage_task(Action='kill', TaskId=taskId)`. List active schedules via `manage_task(Action='list')`.
- **Reactive Wakeup:** Do NOT loop or poll `manage_task(Action='status')` to wait for completion. The Flowork runtime automatically resumes execution when the timer fires or cron triggers.
