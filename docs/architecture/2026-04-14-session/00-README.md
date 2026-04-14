# Architecture Session — 2026-04-14

Long design conversation covering six distinct but related threads. Each thread has its own document. Read in any order; cross-references note dependencies.

## Session context

Starting point: "How would disler's bowser help us?"

End point: architectural direction for UI testing, harness-agnostic skill distribution, multi-harness orchestration (Claude Code + Codex + pi), the Shikigami / AFK Dispatcher split, and a prioritized bead plan.

## Documents

| # | Document | Core question answered |
|---|---|---|
| 01 | [Bowser Comparison and UI Testing](01-bowser-comparison-ui-testing.md) | Should we use bowser? What's our agent-driven UI testing architecture? |
| 02 | [Scenario Generator Refactor](02-scenario-generator-refactor.md) | Where do scenarios belong — in beads or in `scenarios/`? How do we fix the drift? |
| 03 | [Higher-Order Prompts and `just` Architecture](03-higher-order-prompts-and-just-architecture.md) | The 4-layer model (skill → agent → command → `just`), HOP vocabulary, bash lockdown strategy |
| 04 | [Claude + Codex + pi Orchestration](04-claude-codex-pi-orchestration.md) | How does pi fit alongside Claude Code and Codex? Lessons from disler's 5 pi videos |
| 05 | [Shikigami vs AFK Dispatcher](05-shikigami-vs-afk-dispatcher.md) | Conversational agent vs engineering dispatcher — one system or two? Healthcare PII implications. |
| 06 | [Bead Generation Plan](06-bead-generation-plan.md) | What beads to create, in which repo, in what order |

## Reading order recommendation

If reading cold: 03 → 04 → 01 → 02 → 05 → 06. That follows the logical build order (architecture first, then specific applications, then operational plan).

If triaging: 06 first (what to actually do), then 05 (biggest architectural decision), then others as needed.

## Key design decisions emerging from this session

1. **Do not install bowser as a plugin.** Cherry-pick one pattern (scenario files as QA contracts), build it on existing primitives. Details in 01.
2. **Scenarios for bead-level implementation verification live IN the bead.** The `scenarios/` folder is reserved for epic-wide/business-process scenarios only. Details in 02.
3. **Adopt `just` as Layer 4** — the shell-level, harness-agnostic contract. Don't restrict bash generically; curate verbs via justfile + permission allowlist. Details in 03.
4. **pi is a meta-orchestrator, not a replacement for Claude Code.** Claude Code stays as execution muscle (80%); pi orchestrates complex multi-agent workflows (20%). Details in 04.
5. **Shikigami (conversational, PII-safe) and AFK Dispatcher (engineering work) are different agents.** Same PETER framework (Prompt/Trigger/Environment/Review), different roles. AFK Dispatcher lives on hokora. Details in 05.
6. **Fork the-library as a new repo (not a merge into claude-code-plugins).** The library catalogs pointers to skills in their source repos; it does not own them. Details in 03 and 06.
7. **Expertise files live in the repo they describe.** Mira expertise in mira; IG expertise in fhir-praxis-de etc. Not centralized. Details in 04 and 06.

## What changed vs pre-session assumptions

- Bowser was initially considered as a drop-in. Rejected after comparison — too narrow; we already have superior primitives in places.
- The four-layer model was a useful frame but needed a fourth stable layer (`just`), which we had never articulated explicitly.
- Harness-agnostic portability turned out to be larger than expected: skills, AGENTS.md, agentskills.io, and `just` are portable across Claude Code, Codex, and pi.
- Claude Code's plugin marketplace is not a viable distribution path. Disler's Library (YAML catalog + GitHub refs + npm/Pi Packages) is.
- Shikigami and AFK Dispatcher were treated as possibly-one-agent. Disler's work + healthcare PII requirements reframed them as definitely-separate.

## What was flagged as deferred

- pi deep hands-on — watch course #9 (Elite Context Engineering) first, then play with pi for a day, then plan.
- CEO + Board deliberation pattern — use council skill today; evolve later.
- Intel MacBook Pro as macOS worker — shelved unless a concrete use case appears.
- Paperclip integration — no clear use case; revisit later.
- Codex-as-MCP-server deeper integration — current subprocess dispatch works; upgrade later.
