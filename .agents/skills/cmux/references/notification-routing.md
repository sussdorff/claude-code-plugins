# cmux Notification Routing — Haiku Stop-Hook Filter

Filters cmux's noisy `Stop` hook notifications using a Claude Haiku classifier
so only "user actually needs to act" events fire a system notification.

## Why this exists

cmux's `claude` wrapper (`/Applications/cmux.app/Contents/Resources/bin/claude`)
injects a `Stop` hook on every Claude Code session that fires
`cmux claude-hook stop` after **every model turn** — not just at session end.
With multi-turn work and parallel Wave Orchestrator panes this produces a flood
of "Claude is finished" system notifications. The user only cares about real
"needs input" events.

The hooks are injected via `--settings` at runtime, so they do **not** appear in
`malte/settings.json`. They only exist inside cmux's wrapper script (line 207).

## How it works

A bash shim is wired in via the `CMUX_BUNDLED_CLI_PATH` environment variable.
cmux's wrapper resolves this variable to find which `cmux` binary to call from
hook handlers (see `resolve_hook_cmux_bin()` in the wrapper).

```
~/.zshrc:
  export CMUX_BUNDLED_CLI_PATH=/Users/malte/code/claude/malte/scripts/cmux-shim.sh
```

The shim:

1. **Pass-through** for everything that is not `claude-hook stop`. The real
   cmux binary is `exec`ed unchanged. No latency, no behavior change.
2. For `claude-hook stop`:
   - Reads the JSON payload (`session_id`, `transcript_path`) from stdin.
   - **Forks the decision into the background and exits 0 immediately** so
     cmux's 10s hook timeout never fires.
   - In the background: parses the transcript JSONL, extracts the last
     assistant text message, calls
     `claude --model haiku --system-prompt "<binary classifier>" -p "<msg>"`
     with a 15s `timeout`.
   - If Haiku says `NOTIFY` → forwards the original payload to real cmux:
     `printf '%s' "$PAYLOAD" | /Applications/cmux.app/Contents/Resources/bin/cmux claude-hook stop`
   - If Haiku says `QUIET` → does nothing.
   - On any failure (timeout, parse error, claude not found, unparseable
     decision) → fail-safe = forward (better one extra ping than missing a
     real one).
3. Logs every decision to `/tmp/cmux-shim.log` for debugging.

## Classifier logic

The system prompt instructs Haiku to reply with exactly one word — `NOTIFY`
or `QUIET`:

- **NOTIFY** when the last assistant message indicates the user must act:
  question awaiting answer, confirmation/approval needed, error/blocker,
  completed task asking for review, auth/credentials needed.
- **QUIET** when no human action is required: autonomous loop iteration
  finishing, routine progress, intermediate findings, self-contained completion,
  subagent output for the orchestrator.
- **When unsure → NOTIFY** (fail-safe).

## Files

| Path | Purpose |
|------|---------|
| `malte/scripts/cmux-shim.sh` | The shim itself |
| `~/.zshrc` (`CMUX_BUNDLED_CLI_PATH=...`) | Activation |
| `/tmp/cmux-shim.log` | Decision log (last N entries) |

## Operations

**Disable temporarily** (current shell only):
```bash
unset CMUX_BUNDLED_CLI_PATH
# launch new claude session — falls back to default cmux behavior
```

**Disable permanently**: Comment out the export in `~/.zshrc` and restart
your cmux pane.

**Check decisions**:
```bash
tail -20 /tmp/cmux-shim.log
```

**Force-test the shim** (outside a real Stop hook):
```bash
# QUIET case
cat > /tmp/q.jsonl <<'EOF'
{"type":"assistant","message":{"content":[{"type":"text","text":"Iteration 3 of 10 done, continuing."}]}}
EOF
echo '{"session_id":"t","transcript_path":"/tmp/q.jsonl"}' | \
    /Users/malte/code/claude/malte/scripts/cmux-shim.sh claude-hook stop
sleep 12 && tail /tmp/cmux-shim.log
```

## Known trade-offs

- **Sidebar state lag**: cmux's `claude-hook stop` updates the sidebar pane
  state to "Idle" AND fires the system notification — there is no separate
  command for state-only. When the shim suppresses a Stop, the sidebar may
  briefly show "Running" instead of "Idle". The next `prompt-submit` resets it
  anyway, so this is mostly invisible during active work.
- **Latency**: Background Haiku call takes ~5-9s. The user sees real `NOTIFY`
  events that long after the actual model turn ends. Acceptable because the
  shim returns 0 instantly (cmux hook timeout never triggers) and "needs
  input" notifications are not time-critical.
- **Cost**: Each NOTIFY/QUIET decision is one short Haiku call (~600 input
  tokens, ~5 output tokens). Covered by Claude Code Max subscription, so
  effectively free against the user's quota bucket.
- **Wrapper coverage**: This only intercepts `Stop`. cmux's other injected
  hooks (`SessionStart`, `SessionEnd`, `Notification`, `UserPromptSubmit`,
  `PreToolUse`) pass through unchanged. The good "Claude is waiting for your
  input" notification still works because it comes from the `Notification`
  hook (idle_prompt / permission_prompt), not from `Stop`.

## When to revisit

- If cmux ships an in-app per-event notification toggle, drop the shim and
  use the native setting.
- If the sidebar-state lag becomes annoying, look for a separate cmux command
  to update state without firing notifications (none exists as of cmux
  inspection on 2026-04-11).
- If Haiku is too slow or wrong too often, consider a fast pre-filter
  (regex/keyword) before the Haiku call, or replace Haiku with a smaller local
  model.
