# Bowser Comparison and Agent-Driven UI Testing

**Session date**: 2026-04-14
**Scope**: Evaluation of disler's bowser plugin; design of our agent-driven UI testing architecture.

## Summary

We evaluated disler's `bowser` plugin (https://github.com/disler/bowser) against our existing Claude Code stack. Decision: **do not install bowser**. Cherry-pick one pattern (user story files as QA specs) and build it on primitives we already have. The resulting architecture has two scope levels (bead-level and epic-wide) and cleanly reuses `scenario-generator`, `playwright-tester`, and `wave-orchestrator`.

## What bowser is

Bowser is a Claude Code plugin implementing a four-layer stack for agentic browser automation and UI QA:

1. **Skill layer** — drives the browser via Playwright CLI (headless) or Chrome MCP (authenticated). Prefers Playwright CLI for token efficiency and lower prompt-injection risk.
2. **Subagent layer** — a QA subagent that reads user story files, runs steps, takes screenshots, and returns structured pass/fail.
3. **Command layer** — `/ui-review` fans out one QA subagent per story file in parallel.
4. **Justfile layer** — `just ui-review` as the stable entry point callable by humans or other agents.

Key claims: ~40k tokens per parallel QA run; Playwright CLI is token-efficient and safer than MCP.

## What we already have

| Bowser layer | Our equivalent | Verdict |
|---|---|---|
| Browser driver skill | `dev-tools:playwright-cli` | Equivalent |
| Authenticated browser | `crwl` profiles + `content:cmux-browser` | Superior — persistent profiles |
| QA subagent | `dev-tools:playwright-tester`, `dev-tools:gui-review` | Partial — exists, not spec-file-driven |
| UAT harness | `dev-tools:uat-validator`, `dev-tools:holdout-validator` | Superior — info-barrier discipline |
| Fan-out | `beads-workflow:wave-orchestrator` + cmux | Superior — dependency-aware waves |
| Stable entry | `just` (to be adopted) | Missing today; see doc 03 |
| Task tracking | beads | Bowser has no equivalent |
| Memory | open-brain | Bowser has no equivalent |

Bowser is a narrow vertical slice of what we have horizontally. The only novel structural idea is **user-story-file as machine-readable QA spec**.

## The reframe: beads ARE the spec files

Original bowser model: separate `stories/` tree with markdown user stories. Our better model: the scenario lives IN the bead.

```
Feature bead (mira-01p)
  ├── Description: what & why
  ├── Acceptance criteria: machine-checkable outcomes
  └── Scenario: "how a human would test this" ← generated/edited
        │
        ▼
/ui-review mira-01p
        │
        ▼
qa-agent (new subagent)
        │ spawns N× playwright-tester in parallel
        ▼
playwright-tester per scenario step
        ├── loads: scenario + playwright-cli skill + auth profile
        ├── executes: navigate, click, screenshot
        └── returns: {status, evidence[], errors[]}
        │
        ▼
qa-agent aggregates
  → bd update <id> --append-notes
  → screenshots to open-brain or bead attachment
  → if fail: bd create --type=bug --blocks=<id>
```

## Two scope levels

There are two distinct scenario layers, both consumable by the same `/ui-review` command:

| Layer | Scope | Source | Purpose | Consumed by |
|---|---|---|---|---|
| **Bead scenario** | `single-bead` | `scenario-generator` appends to bead | Does *this implementation* work? | `/ui-review <bead-id>` during bead implementation |
| **Business process** | `epic-wide` or `business-process` | Human-authored or epic-level generation | Does the *business process* work across features? | `/ui-review <scenario-file>` at release/acceptance |

Example business processes in mira: "New patient → HKP → billing submitted to KV" spanning mira-01p + mira-10ke + mira-123.

The same `/ui-review` command handles both scopes; it reads the `Scope:` header and adjusts preconditions and execution context.

## Why `.spec.ts` Playwright files are the antipattern (mira specifically)

The mira frontend has `frontend/e2e/*.spec.ts` files written by coding agents. These should be deprecated.

Reasons:

1. **Rigidity** — specs pass today, minor UI drift breaks them without testing user intent.
2. **Wrong level of abstraction** — `page.locator('[data-testid=submit-btn]').click()` tests the implementation, not the feature.
3. **Maintenance tax** — every refactor rewrites selectors.
4. **Agent-unfriendly** — an agent can't reason about *whether the feature works*, only whether the script still runs.

Agent-driven verification tests **intent**: "Can I submit the billing form for an EBM patient and see the confirmation?" The agent figures out which buttons, adapts to DOM changes, and reports like a human QA tester.

**Action**: audit existing `frontend/e2e/*.spec.ts`. After qa-agent proves itself on 5+ beads, delete or demote to "smoke check that app boots."

## Distinction from what scenario-generator currently does

See doc 02 for the full scenario-generator refactor. In short:

- Today: scenario-generator writes `scenarios/<bead-id>-scenarios.md` files with `Scope: single-bead`. This is drift — single-bead scenarios should live in the bead, not on disk.
- Fix: flip scenario-generator default to `bead-scenario` mode which writes via `bd update <id> --append-notes` (or `--design`). Keep `persistent-scenario` mode only for epic-wide/business-process.
- Migration: move existing single-bead files into their beads, delete the files, keep only epic-wide files.

## Architecture components (new or newly specified)

### qa-agent (new subagent)

Lives in `claude-code-plugins/dev-tools/agents/qa-agent.md` (or as an agentskills.io-format skill for portability).

Responsibilities:
- Accept bead ID or scenario file path
- Read scenario (from bead `design` field or from `scenarios/<name>.md`)
- Parse Szenario blocks
- Spawn `playwright-tester` subagent per Szenario in parallel
- Aggregate results into a structured JSON report
- Write back to the bead (notes + evidence) or to the scenario file's runbook history
- If failures: create child bug beads via `bd create --type=bug --blocks=<id>`

Output contract:
```json
{
  "bead_id": "mira-01p",
  "scope": "single-bead",
  "overall": "pass" | "fail" | "partial",
  "scenarios": [
    {
      "name": "Happy Path — Lukrativer HKP",
      "status": "pass",
      "steps_completed": 3,
      "steps_total": 3,
      "evidence": ["screenshot-01.png", "screenshot-02.png"],
      "errors": []
    }
  ],
  "timestamp": "2026-04-14T17:30:00Z",
  "duration_seconds": 42
}
```

See doc 03 for why structured JSON output contracts matter across all subagents.

### /ui-review slash command

Lives in `claude-code-plugins/dev-tools/commands/ui-review.md` (Claude Code) and `mira/.claude/commands/ui-review.md` (mira-local overlay).

Behavior:
- `/ui-review <bead-id>` — reads bead, dispatches qa-agent with `single-bead` scope
- `/ui-review <scenario-file>` — reads file, dispatches qa-agent with the scope declared in the file header
- Thin wrapper that shells to `just review-bead <id>` or `just review-process <file>` (see doc 03 on `just` as Layer 4)

### Integration points

- **Bead orchestrator review phase**: auto-trigger `/ui-review <bead-id>` as a gate before marking a UI-touching bead ready-for-close.
- **Session close gate**: `core:session-close` agent checks for UI beads; runs `/ui-review` before allowing close.
- **Epic close**: when an epic closes, trigger epic-wide `/ui-review` on matching `scenarios/<epic>.md` files.
- **Release candidate**: business-process scenarios run as acceptance tests before release.

## Component ownership

| Component | Repo | Why |
|---|---|---|
| qa-agent definition | `claude-code-plugins` | Reusable across projects |
| /ui-review slash command (global) | `claude-code-plugins` | Reusable command |
| /ui-review slash command (mira overlay) | `mira` | Project-specific routes, auth, seeds |
| playwright-tester subagent | `claude-code-plugins` (already exists) | Already there |
| `just` recipes for review | per-project justfile | Project-specific dispatch |
| Bead-level scenarios | in the bead | Source of truth |
| Epic-wide scenarios | `<project>/scenarios/*.md` | Source of truth |

## Non-goals

- Do not install the-bowser plugin.
- Do not maintain parallel `.spec.ts` and agent-driven QA long-term. Agent-driven replaces them (after validation period).
- Do not invent a new scenario format. The existing `Szenario` markdown convention with Steps / Expected Results works.
- Do not tie qa-agent to Claude Code only. Design the agent as portable (agentskills.io format) so it can run in Codex or pi later.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Agent-driven QA is flaky (non-deterministic) | Keep specs for true regression gates (smoke tests, critical path). Agent QA covers breadth, not gate. |
| Screenshots bloat open-brain | Store in bead attachments or a blob store; only metadata/paths in memory. |
| Scenarios drift from reality | qa-agent failures feed back into bead comments; scenario-generator can re-suggest updates on refactor. |
| Parallel runs overwhelm a dev environment | Rate-limit via wave-orchestrator's existing concurrency controls. |
| Playwright profile auth expires | Same risk exists today with `crwl` profiles; same manual refresh solution. |

## Open questions

- **Where do business-process QA results go?** Options: new bead per run, attached to epic bead, open-brain memory as observation. Recommendation: open-brain memory with `type=qa_run` and cross-references to beads exercised.
- **Automatic vs manual trigger for bead-level QA?** Recommendation: explicit during dev (`/ui-review <id>`), automatic as gate in `core:session-close`.
- **How does qa-agent handle app-not-running?** Recommendation: qa-agent's preflight checks dev server on expected port; if absent, fails fast with clear error rather than retry loop.
- **Can qa-agent write tests itself (upgrade existing `.spec.ts`)?** Deferred — separate question after agent-driven QA proves reliable.

## Status

Design stage. No code written. See doc 06 for the concrete bead plan that operationalizes this.
