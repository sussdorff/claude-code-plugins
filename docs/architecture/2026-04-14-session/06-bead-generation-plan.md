# Bead Generation Plan

**Session date**: 2026-04-14
**Scope**: Prioritized, per-repo bead plan covering everything from this session. Order of attack.

## Summary

This document lists every bead that should eventually exist to implement the architecture decisions from this session. It is organized by repo and priority. Actions marked "do-it-now" do not need beads (too small, no design risk).

**Do not create all of these immediately.** Create as you reach each. Architecture changes fastest when beads are created near the time of doing the work, not weeks in advance.

## Priority scheme

| Priority | Meaning |
|---|---|
| P0 | This week. No design risk. Clear value. |
| P1 | Next 2 weeks. Unblocks downstream. |
| P2 | Soon. Builds on P1 foundation. |
| P3 | Strategic. Deferrable. |
| P4 | Design-only. Not yet code-ready. |

## Do-it-now (no bead needed)

Small tasks, clear action, <30min each:

1. `brew install rtk && rtk init -g` — token savings, Claude hooks
2. Enable sandbox in `~/.claude/settings.json` (add `"sandbox": {"enabled": true}`)
3. Schedule memory-heartbeat via `/schedule` skill (daily work hours + weekly Friday)
4. Delete stale scenario-generator cached plugin versions (see doc 02)

If any fails unexpectedly, convert to a bead.

## Weekend starter (the 4 actions from in-session discussion)

**Saturday morning (~1h)**:
1. Install rtk + enable sandbox + install DCG

**Saturday afternoon (~2h)**:
2. Fork `the-library` → create `cognovis-library` repo
   - Clone disler's template
   - Create new repo under your org
   - Seed `library.yaml` with 5-10 skills (beads, scenario-generator, playwright-cli, summarize, council, qa-agent once it exists)
   - Run `library sync` on workstation to verify

**Sunday (~2h)**:
3. Write `docs/architecture/2026-04-14-session/PRD-shikigami-afk-dispatch-protocol.md`
   - 2-page markdown
   - Defines roles, boundaries, shared substrate, dispatch protocol, healthcare use case framing
   - This doc unblocks 15+ downstream beads

**Monday if feeling good (~1h)**:
4. Ship bead: `[REFACTOR] scenario-generator: flip default to bead-scenario, write via bd update`
   - Small, bounded, real value
   - Fixes drift in mira's scenarios folder
   - Proves the workflow still works end-to-end

## Beads by repo

### Repo: `cognovis-library` (new, after fork)

| Bead | Priority | Type |
|---|---|---|
| `[FEATURE] library.yaml catalog of top 20 skills` | P0 | feature |
| `[TASK] Document library sync workflow in README` | P1 | task |
| `[TASK] CI: validate library.yaml on push` | P2 | chore |
| `[TASK] Sync library to shikigami-bot deployment pipeline` | P2 | task |
| `[TASK] Sync library to hokora when AFK dispatcher arrives` | P3 | task |

### Repo: `claude-code-plugins`

#### Foundational refactors (P1)

| Bead | Priority | Type | Why here |
|---|---|---|---|
| `[REFACTOR] scenario-generator: flip default to bead-scenario, write via bd update` | P1 | refactor | Fixes drift across all projects |
| `[FEATURE] Structured JSON output contract for subagents — schema + 3 pilot migrations` | P1 | feature | Linchpin for observability + orchestration |
| `[REFACTOR] CLAUDE.md → AGENTS.md split (portable vs Claude-specific)` | P1 | refactor | Enables Codex + pi harness use |
| `[DESIGN] Shikigami vs AFK Dispatcher — role split, shared substrate, dispatch protocol` | P1 | task | Design bead; unblocks many downstream |

#### Next tier (P2)

| Bead | Priority | Type |
|---|---|---|
| `[FEATURE] qa-agent skill (agentskills.io format) consuming scenarios from bead or file` | P2 | feature |
| `[FEATURE] /ui-review slash command (global dispatcher)` | P2 | feature |
| `[FEATURE] Agent Experts pattern — /expert-plan /expert-build /expert-improve slash commands` | P2 | feature |
| `[TASK] R&D framework audit of top 20 subagents, classify interactions, flag violations` | P2 | task |
| `[FEATURE] CLI wrappers for MCP tools (ob, searxng, markitdown) — pi compatibility` | P2 | feature |
| `[FEATURE] justfile-common snippets in claude-code-plugins for reuse` | P2 | feature |
| `[TASK] project-setup skill: scaffold justfile for new repos` | P2 | task |

#### Strategic (P3)

| Bead | Priority | Type |
|---|---|---|
| `[TASK] Convert top 20 skills to agentskills.io format compliance` | P3 | task |
| `[FEATURE] expert-improve hook: runs on bead close, reads git diff, updates expertise files` | P3 | feature |
| `[FEATURE] core:deliberation skill — CEO+Board evolution of business:council` | P3 | feature |
| `[FEATURE] Codex-as-MCP-server deeper integration for adversarial review` | P3 | feature |

### Repo: `mira`

#### One-time cleanup (P1)

| Bead | Priority | Type |
|---|---|---|
| `[TASK] Migrate scenarios/mira-*-scenarios.md (single-bead) into beads via bd update, delete files` | P1 | task |
| `[TASK] Rename remaining epic-wide scenario files to business-process names` | P2 | task |

#### Build (P2)

| Bead | Priority | Type |
|---|---|---|
| `[FEATURE] mira justfile: review-bead, review-process, scenario-for-bead recipes` | P2 | feature |
| `[FEATURE] /ui-review slash command (mira overlay, dispatches via just)` | P2 | feature |
| `[FEATURE] mira expertise/ files: react-ui-expert, aidbox-integration-expert, billing-flow-expert` | P2 | feature |
| `[TASK] Tighten mira permissions.yml to Bash(just *) + utility allowlist after justfile matures` | P3 | chore |
| `[TASK] Integrate /ui-review as gate in bead-orchestrator review phase for mira` | P3 | task |

#### Deferred cleanup (P3)

| Bead | Priority | Type |
|---|---|---|
| `[REFACTOR] Deprecate frontend/e2e/*.spec.ts after qa-agent proves on 5 beads` | P3 | refactor |

### Repo: `fhir-praxis-de`

| Bead | Priority | Type |
|---|---|---|
| `[FEATURE] expertise/fhir-praxis-ig-expert.md — IG development patterns, SUSHI, validation` | P2 | feature |

### Repo: `fhir-dental-de`

| Bead | Priority | Type |
|---|---|---|
| `[FEATURE] expertise/fhir-dental-ig-expert.md — dental IG, BEMA/GOZ, KZBV patterns` | P2 | feature |

### Repo: `fhir-terminology-de`

| Bead | Priority | Type |
|---|---|---|
| `[FEATURE] expertise/fhir-terminology-expert.md — CodeSystem, ValueSet, expansion patterns` | P2 | feature |

### Repo: `shikigami-bot`

| Bead | Priority | Type |
|---|---|---|
| `[FEATURE] Mail adapter — IMAP trigger source` | P2 | feature |
| `[FEATURE] Calendar adapter — Google Calendar trigger source` | P2 | feature |
| `[FEATURE] Bead events adapter — poll bd for status changes` | P2 | feature |
| `[FEATURE] Structured JSON envelope for agent responses + audit log sink` | P2 | feature |
| `[FEATURE] agent.yml: harness field (claude\|codex\|pi) + dispatch logic` | P3 | feature |
| `[FEATURE] Webhook endpoint — HMAC-auth /trigger for external integrations` | P3 | feature |
| `[FEATURE] Cron triggers — systemd timers dispatching prompts` | P3 | feature |
| `[FEATURE] Delegate long-running jobs to AFK Dispatcher (HTTP dispatch)` | P3 | feature |
| `[TASK] library sync integration at deploy time` | P3 | task |

### Repo: `afk-dispatcher` (new, create after DESIGN bead closes)

| Bead | Priority | Type |
|---|---|---|
| `[FEATURE] FastAPI HTTP job server (port 7600, HMAC auth)` | P2 | feature |
| `[FEATURE] Job queue in Postgres (shared with Shikigami)` | P2 | feature |
| `[FEATURE] Per-job audit log — signed JSONL to shared sink` | P2 | feature |
| `[FEATURE] Subprocess manager with timeouts + resource limits` | P2 | feature |
| `[FEATURE] Git worktree manager — per active bead, auto-cleanup` | P2 | feature |
| `[FEATURE] pi as internal orchestrator — spawns Claude/Codex/pi subagents` | P3 | feature |
| `[FEATURE] Trigger adapters (HTTP, webhook, cron, mail-arrived, bead-status)` | P3 | feature |
| `[FEATURE] Callback to Shikigami on job completion` | P3 | feature |
| `[FEATURE] Langfuse integration for LLM call tracing` | P3 | feature |
| `[FEATURE] Heartbeat endpoint + Shikigami health monitoring` | P3 | feature |

### Repo: `infra-devops`

| Bead | Priority | Type |
|---|---|---|
| `[TASK] Update elysium-proxmox/ docs: hokora role = AFK Dispatcher host` | P2 | chore |
| `[TASK] Tailscale or WireGuard link between elysium and hokora` | P2 | task |
| `[TASK] Shared Postgres access pattern (hokora → elysium)` | P2 | task |
| `[TASK] 1Password secrets delivery to hokora at service startup` | P3 | task |

**Skip** — not needed:
- Hokora VM provision (already done)
- Gastown setup (decided against)
- Intel MacBook Pro worker (shelved)

## Order of attack

### Week 1 — foundation (do-it-now + P0)

- rtk install
- Sandbox enable
- DCG install
- Schedule memory-heartbeat
- Fork the-library → cognovis-library with initial 10 skills
- Write DESIGN doc for Shikigami vs AFK Dispatcher

### Week 2 — structural refactors (P1)

- scenario-generator flip
- Mira single-bead scenario migration (one-time cleanup)
- Structured JSON output contract spec + 3 pilot subagent migrations
- CLAUDE.md / AGENTS.md split

### Week 3–4 — build on foundation (P2 first wave)

- qa-agent + /ui-review (global + mira overlay)
- mira justfile with initial 5-10 recipes
- First agent expertise file (pick one mira domain, e.g. react-ui-expert)
- CLI wrappers for open-brain (for future pi compatibility)

### Month 2 — Shikigami extension

- Mail adapter, calendar adapter, bead-events adapter in shikigami-bot
- Audit log + structured JSON envelope
- agent.yml harness field (enables pi/codex dispatch from Shikigami)

### Month 2–3 — AFK Dispatcher MVP

- Create `afk-dispatcher` repo
- FastAPI job server on hokora
- Job queue, audit log, subprocess manager
- Initial dispatch from Shikigami for simple "run bead X" jobs
- Tailscale link elysium ↔ hokora

### Month 3+ — advanced

- pi orchestrator inside AFK Dispatcher
- Agent Experts pattern full rollout across mira + fhir-* repos
- Permission lockdown to `Bash(just *)` + utilities
- Deprecate mira `.spec.ts` files
- Expert-improve hook automation
- CEO/Board deliberation skill evolution

## Tracks you can run in parallel

These are independent enough to advance simultaneously without blocking each other:

### Track A: Infrastructure (Week 1–2)
- rtk, DCG, sandbox
- Library fork
- Design doc

### Track B: Scenario refactor (Week 2–4)
- scenario-generator flip
- mira migration
- qa-agent + /ui-review

### Track C: Shikigami extension (Month 1–2)
- Mail adapter, calendar, bead events
- Structured JSON envelope
- Audit log

### Track D: Expertise files (Month 1+)
- Start with one mira domain
- Prove the pattern
- Expand to others

### Track E: AFK Dispatcher (Month 2+)
- Depends on: DESIGN doc, Shikigami harness field, shared audit log

You can work A+B+C+D concurrently. E waits for A (design).

## Decision points ahead

Before creating these beads, resolve:

### Immediate (before any bead)

- [ ] Bead `design` vs `notes` field for scenario content — **recommend `design`**
- [ ] Library repo name — `cognovis-library` or `malte-library`?

### Within 2 weeks

- [ ] AFK Dispatcher repo name — `afk-dispatcher`?
- [ ] Tailscale vs WireGuard for elysium ↔ hokora link?
- [ ] Audit log format — JSON Lines signed with Ed25519?
- [ ] Which 3 subagents first for structured JSON contract? Recommend: `bead-orchestrator`, `review-agent`, `playwright-tester`

### Within 1 month

- [ ] Pi as AFK internal orchestrator — prototype first, or commit now?
- [ ] Codex-as-MCP-server — specific integration point?
- [ ] Business-process scenario storage — open-brain or dedicated store?

### Longer-term (month 2+)

- [ ] Multi-clinic deployment model for healthcare AFK?
- [ ] Role-based agent identity?
- [ ] Encryption at rest for job files?

## What to NOT bead

Stay as notes/research:

- pi deep hands-on experimentation (play for a day first)
- CEO/Board deliberation specifics (need a concrete first use case)
- Intel MacBook Pro worker (shelved)
- Paperclip integration (no clear use case)
- MCP vs CLI for all tools philosophy (decide per tool as they come up)
- Gemma local model integration (not focus per user)

## Bead count estimate

Cataloged above:

- cognovis-library: 5
- claude-code-plugins: 15
- mira: 7
- fhir-praxis-de: 1
- fhir-dental-de: 1
- fhir-terminology-de: 1
- shikigami-bot: 9
- afk-dispatcher: 10 (after creation)
- infra-devops: 4

**Total: ~53 beads.** Do not create at once. Create as you reach each.

## Immediate first 5 beads to create

If the weekend starter tasks are done and you want to create beads NOW:

1. `claude-code-plugins` — `[DESIGN] Shikigami vs AFK Dispatcher — role split, shared substrate, dispatch protocol` (P1, task)
2. `claude-code-plugins` — `[REFACTOR] scenario-generator: flip default to bead-scenario, write via bd update` (P1, refactor)
3. `claude-code-plugins` — `[FEATURE] Structured JSON output contract for subagents — schema + 3 pilots` (P1, feature)
4. `cognovis-library` (after fork) — `[FEATURE] library.yaml catalog of top 20 skills` (P0, feature)
5. `claude-code-plugins` — `[REFACTOR] CLAUDE.md → AGENTS.md split` (P1, refactor)

These five unblock the most downstream work for 2 weeks.

## Done-not-doing list

Explicitly ruled out during this session:

- Installing bowser as a plugin
- Continuing to invest in Claude Code plugin marketplace
- Keeping `.spec.ts` as the primary UI regression strategy in mira
- Storing single-bead scenarios in `scenarios/` folder
- Running Shikigami on Intel MacBook Pro
- Merging Shikigami and AFK Dispatcher into one agent
- Centralizing expertise files outside their source repos
- Using Gastown on hokora

## Related documents

- Doc 00: README — session overview
- Doc 01: Bowser Comparison and UI Testing
- Doc 02: Scenario Generator Refactor
- Doc 03: Higher-Order Prompts and `just` Architecture
- Doc 04: Claude + Codex + pi Orchestration
- Doc 05: Shikigami vs AFK Dispatcher
