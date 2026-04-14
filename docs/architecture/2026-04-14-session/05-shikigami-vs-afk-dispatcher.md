# Shikigami vs AFK Dispatcher

**Session date**: 2026-04-14
**Scope**: The conversational agent vs engineering dispatcher architectural decision. Healthcare PII framing. Hokora placement. Mac Mini Agent comparison.

## Summary

Shikigami and AFK Dispatcher are two different agents with opposite operational profiles. Do not merge them. They share substrate (Postgres, audit log, Library-distributed skills, beads) but are distinct processes with distinct roles. Shikigami lives on elysium (existing VM). AFK Dispatcher lives on hokora (existing VM, previously Gastown-installed but unused).

## The two-agent split

| Dimension | Shikigami (conversational) | AFK Dispatcher (engineering) |
|---|---|---|
| **Trigger** | Human message (Telegram) | Event (webhook, cron, bead-status, mail parse) |
| **Latency expectation** | Seconds — user waiting | Minutes to hours — no one waiting |
| **Output shape** | Chat reply | PR, bead updates, commits, screenshots |
| **Resource profile** | Low CPU, I/O on chat | High CPU/disk, many subprocesses |
| **State scope** | Session-scoped, short | Bead-scoped, long, stateful across runs |
| **Failure impact** | User sees error, retries | Silent — must be detected via audit log |
| **Trust model** | User input → restricted tools | Automated triggers → broader tool access |
| **Good day metric** | ~1000 small turns | ~5 large runs |
| **Security posture** | Stricter (PII in user messages) | Broader (git, deploy, infra access) |

## mac-mini-agent alignment

mac-mini-agent (disler's repo) is the **AFK Dispatcher primitive**, not a Shikigami shape. Evidence:

| Property | mac-mini-agent | Shikigami | AFK Dispatcher |
|---|---|---|---|
| Interface | HTTP `POST /job` | Telegram conversational | Event-driven (HTTP, webhook, queue) |
| Latency | Minutes–hours | Seconds | Minutes–hours |
| State | YAML job files | Postgres sessions + trust zones | Job queue + audit log |
| Routing | None — caller specifies work | Haiku semantic classification | Rule-based or tagged |
| Output | Fire-and-forget, poll via `just job <id>` | Immediate chat reply | Async (PR, bead update, screenshot) |
| User model | Single operator | Allowlisted users, per-user sessions | Automated triggers + admin |

mac-mini-agent is job-in, work-out — fire-and-forget HTTP dispatcher. Shikigami (as already built) is conversational routing with trust zones. They solve different problems.

**You built the more sophisticated half first.** Shikigami's semantic routing, trust zones, two-user security model, and Postgres session store exceed mac-mini-agent in maturity. What's missing is the engineering-work sibling.

## Healthcare PII use case framing

This use case crystallizes the split:

> In a clinical setting, Shikigami = conversational agent that talks to the doctor and runs on local models to be certain about PII and GDPR. Dispatches work to agents which run locally or in the cloud.

So Shikigami functions as a **PII firewall**:
- Local/on-prem LLM handles direct doctor conversation (no PII leaves the device)
- Complex engineering work (research, code generation, data analysis) gets dispatched to cloud agents with payloads scrubbed of PII
- Audit log captures what was dispatched, when, to where

This mirrors the two-agent split exactly. Shikigami handles chat + PII firewall; AFK Dispatcher handles heavy work with scrubbed inputs.

Same architectural pattern as your personal setup. Just with local models in front for compliance reasons.

## PETER framework mapping

From disler's course: PETER = Prompt input + Trigger + Environment + Review.

### Shikigami's PETER

| Slot | Current implementation |
|---|---|
| **P**rompt input | Telegram via aiogram |
| **T**rigger | Polling Telegram (aiogram loop) |
| **E**nvironment | Proxmox VM on elysium + Claude CLI subprocess |
| **R**eview | Response parser + optional Langfuse tracing |

Status: **already more mature than mac-mini-agent** on several axes (trust zones, two-user security, frozen agent configs, Postgres session store, semantic routing). Missing: non-Telegram trigger sources (mail, calendar, bead events).

### AFK Dispatcher's PETER (to build)

| Slot | Plan |
|---|---|
| **P**rompt input | Shikigami dispatch, mail parse, bead status, scheduled task |
| **T**rigger | HTTP from Shikigami, webhook from GitHub, cron, mail-arrived |
| **E**nvironment | Hokora VM (existing) + pi-as-orchestrator + Claude/Codex subprocesses |
| **R**eview | Structured JSON return + audit log + optional Langfuse |

## Physical placement decision

Two options considered:

### Option A — both on elysium (different VMs)

- Shikigami VM (existing) + new AFK Dispatcher VM
- Shared Postgres, shared audit log on elysium
- Simpler networking

### Option B — Shikigami on elysium, AFK Dispatcher on hokora (chosen)

- Physical isolation between conversation and work layers
- Slightly more networking (Tailscale or internal VLAN between hosts)
- Matches stated intent for hokora
- Failure isolation: AFK crash doesn't kill Telegram bot
- Resource isolation: engineering runs are CPU/disk heavy; Shikigami stays responsive
- Security posture: AFK needs broader tool access (SSH keys, git creds, MCP access); Shikigami stays minimal-trust

**Decision**: Option B. Hokora exists and is already intended for this. Gastown installed but unused — skip it per preference for IndyDevDan-aligned pattern.

## Network architecture

```
┌─────────────────────────────────────────────────────────────┐
│ ELYSIUM (existing Proxmox)                                  │
│                                                             │
│  ┌─────────────────┐   ┌──────────────────────────────┐    │
│  │ shikigami-bot   │   │ Shared substrate             │    │
│  │ (conversational)│◄──┤  - Postgres                  │    │
│  │  - Telegram     │   │  - open-brain MCP            │    │
│  │  - Haiku router │   │  - Library-distributed skills│    │
│  │  - 2-user model │   │  - Audit log (signed JSONL)  │    │
│  │  - trust zones  │   │  - beads .dolt remote        │    │
│  └───────┬─────────┘   └──────────────┬───────────────┘    │
│          │ can dispatch to ───────────┘                     │
└──────────┼──────────────────────────────────────────────────┘
           │ HTTP over Tailscale (HMAC-authed)
           ▼
┌─────────────────────────────────────────────────────────────┐
│ HOKORA (existing VM, new role: AFK Dispatcher host)         │
│                                                             │
│  afk-dispatcher (new service, FastAPI inspired by Listen)   │
│    - PETER trigger adapters                                 │
│    - pi as meta-orchestrator inside                         │
│    - spawns Claude + Codex + pi subagents                   │
│    - long-running jobs, structured JSON returns             │
│    - writes to shared audit log on elysium                  │
│                                                             │
│  Access: SSH key-only, separate from daily workstation      │
│  Secrets: pulled from 1Password vault at startup            │
│  Network: inbound only from Shikigami + workstation         │
└─────────────────────────────────────────────────────────────┘
```

## What Shikigami needs next (extend existing)

The hardware decision doesn't block progress. Shikigami's PETER is 80% there; gaps are in software:

1. **Trigger diversity** — add adapters:
   - Mail (IMAP via fastmail API)
   - Calendar (Google Calendar MCP or CalDAV)
   - Bead events (`bd ready` polling or event log tailing)
   - Generic webhook endpoint (POST /trigger with HMAC)
   - Cron (systemd timers dispatching prompts)

2. **Agent dispatch → pi option** — instead of only spawning `claude` subprocess, allow `pi` as alternative when multi-harness orchestration is needed. `agent.yml` gets `harness: claude | pi | codex` field.

3. **Structured JSON output contract** — agents return JSON, not prose. Parser extracts. Orchestrator decides next step deterministically. (Matches the cross-cutting contract design in doc 04.)

4. **Audit log** — append-only signed JSONL of every action. Required before Shikigami touches anything FHIR-adjacent.

5. **Library integration** — `library sync` on shikigami-bot deployment so skills stay current without rebuild.

6. **Delegate long-running jobs to AFK Dispatcher** (once AFK exists): when Shikigami receives "run QA on bead X", it POSTs to AFK and immediately replies "started, job ID 42"; later AFK finishes and writes bead comment; Shikigami notifies via Telegram.

## What AFK Dispatcher needs (new build)

### Core

- FastAPI server listening on port 7600 (per disler convention), HMAC-authed `POST /job`
- Job queue in Postgres (shared with Shikigami for observability)
- Per-job audit log entries (signed JSONL to shared sink)
- Structured job lifecycle states: queued → running → completed | failed | timeout

### Dispatch

- pi as internal orchestrator — receives job, decides whether to spawn Claude, Codex, or pi subagents
- Subprocess management with timeouts and resource limits
- Git worktree per active bead (automatic cleanup on completion)

### Trigger adapters

- HTTP POST from Shikigami
- Webhook endpoint for GitHub (push, PR events)
- Cron triggers via systemd timers
- Mail-arrived triggers (IMAP IDLE)
- Bead-status-change triggers (poll or event stream)

### Output

- Structured JSON per job
- Write-back to beads via `bd update` / `bd close`
- Evidence (screenshots, logs) to open-brain or artifact store
- Notification to Shikigami for completion → relay to user via Telegram

### Observability

- Langfuse for LLM call tracing
- Structured logs per job in `logs/<job-id>/`
- Metrics: job count, avg duration, failure rate

### Security

- SSH key-only admin access
- No inbound internet (behind Tailscale)
- Secrets from 1Password via op CLI at service startup
- Dropped privileges: service runs as unprivileged user
- Audit every action via signed JSONL

## Repository structure

| Component | Repo |
|---|---|
| Shikigami bot codebase | `shikigami-bot` (existing) |
| AFK Dispatcher codebase | `afk-dispatcher` (new — create after DESIGN bead closes) |
| Shared protocol definitions | `claude-code-plugins/docs/protocols/shikigami-afk.md` |
| Infrastructure (VM config) | `infra-devops/elysium-proxmox/` (existing, update hokora role) |
| Library of skills | `cognovis-library` (new, forked from the-library) |

## Why separate repos for Shikigami vs AFK Dispatcher

- Distinct deploy targets (elysium vs hokora)
- Distinct security contexts
- Distinct CI/CD gates
- Distinct release cadences
- Easier to open-source AFK Dispatcher later if desired (Shikigami contains PII-handling logic harder to open)

Not a subfolder of shikigami-bot.

## Protocol between Shikigami and AFK Dispatcher

When Shikigami dispatches work:

```json
POST /job HTTP/1.1
Host: hokora.internal
Authorization: HMAC ...
Content-Type: application/json

{
  "job_id": "uuid",
  "requested_by": "shikigami:user-123",
  "trigger": "telegram",
  "type": "bead-work",
  "payload": {
    "bead_id": "mira-01p",
    "action": "implement"
  },
  "callback": {
    "url": "https://shikigami.internal/job/uuid/callback",
    "auth": "HMAC ..."
  },
  "constraints": {
    "max_duration_seconds": 7200,
    "max_cost_usd": 5.00,
    "pii_scrubbed": true
  }
}
```

Response (immediate):

```json
{
  "job_id": "uuid",
  "status": "queued",
  "estimated_start_at": "2026-04-14T18:02:00Z",
  "poll_url": "https://hokora.internal/job/uuid"
}
```

Callback on completion (AFK → Shikigami):

```json
POST /job/uuid/callback HTTP/1.1

{
  "job_id": "uuid",
  "status": "completed",
  "result": {
    "bead_status": "closed",
    "commit_sha": "abc123",
    "pr_url": "https://github.com/...",
    "evidence": ["screenshot-01.png"]
  },
  "duration_seconds": 1834,
  "cost_usd": 2.15,
  "audit_log_ref": "hokora:2026-04-14-uuid.jsonl"
}
```

## The MacBook Pro answer

Explicitly shelved. Rationale:

- You identified that MBP became your AFK agent by accident (clamshell + caffeinate + cmux combo).
- Hokora exists, is dedicated 24/7 hardware, more reliable than MBP for long-running jobs.
- macOS-exclusive use cases (MoneyMoney, Apple Mail AppleScript) are rare enough to not warrant standing infrastructure.
- Pick up MBP worker idea only if/when a specific use case demands macOS.
- **MoneyMoney specifically**: you open it yourself anyway. Not an agent use case.

MBP returns to being daily-driver. Shikigami moves (already moved) to elysium. AFK moves to hokora.

## Compliance gaps to address before FHIR traffic

mac-mini-agent (disler's code) is explicitly unsafe for healthcare. Critical gaps:

1. **Audit trail for FHIR transactions** — HIPAA/GDPR require detailed access logs. Need "agent accessed patient X at T and wrote Y bytes" — not just "job ran."
2. **Sensitive data handling** — screenshots and job files plaintext. Need encryption at rest, retention policy.
3. **Single point of failure** — one hokora VM. Need failover story eventually.
4. **Separation of duties** — admin vs read-only agent roles. Currently one agent identity.
5. **Event-driven triggers** — disler's design assumes `just send`; healthcare needs audit on every event.

Most of these are addressable without major architecture changes:

- Audit wrapper around every tool call (signed JSONL to append-only store)
- Encrypted YAML job files (Fernet key from 1Password)
- Multi-sandbox deployment later (one per clinic)
- Role labels on agent capabilities; Listen checks before forwarding

Deferred until a concrete healthcare dispatch use case appears, but document as a known gap.

## Open questions

- **Where does the audit log physically live?** Probably elysium (shared substrate), with hokora appending. Need write-only access from hokora to elysium-hosted JSONL sink.
- **Tailscale vs WireGuard for the internal link?** Both work; Tailscale is simpler; WireGuard is lower level. Defer to infra preference.
- **How does Shikigami know AFK is healthy?** Heartbeat endpoint on AFK, monitored by Shikigami; fail-closed if missing.
- **What happens if AFK job outlives Shikigami session?** Callback URL should survive session rollover; Postgres holds state.
- **Does Shikigami or AFK own the bead write-back?** AFK owns (it did the work). Shikigami just notifies user.
- **Cost budgeting per job?** Job request specifies max cost; AFK enforces via model selection + token limits; report actual cost in callback.

## Related documents

- Doc 03: Higher-Order Prompts and `just` (permission lockdown applies to both)
- Doc 04: Claude + Codex + pi (pi as AFK's internal orchestrator)
- Doc 06: Bead Generation Plan (specific beads for Shikigami and AFK)
