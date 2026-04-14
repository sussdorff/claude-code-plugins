# Claude Code + Codex + pi Orchestration

**Session date**: 2026-04-14
**Scope**: How the three harnesses compose. Lessons from disler's pi videos. pi as meta-orchestrator, not replacement.

## Summary

Claude Code + Codex + pi is not a "pick one" choice. Each has a distinct strength:

- **Claude Code** — primary execution muscle (agentic impl, cmux, beads, playwright, MCP depth)
- **Codex** — specialized review and adversarial verification (GPT-5.4, `/review`, exposable as MCP server)
- **pi** — meta-orchestrator for complex multi-agent workflows + broadest model routing + working package distribution (Pi Packages)

Disler's consistent message across 5 videos: Claude Code handles 80% of stable work; pi handles 20% of experimental/specialized systems. Never migrate; layer.

## The three harnesses compared

### Claude Code

**Strongest**:
- Skill/agent/hook ecosystem maturity
- CLAUDE.md depth + plugin cache (even with broken marketplace)
- cmux integration for multi-pane orchestration
- MCP client+server — deepest integration
- Beads + open-brain tooling already wired
- Sandbox, hooks, PreToolUse/PostToolUse lifecycle

**Model lock**: Anthropic only

**Unique**: rtk/DCG hook ecosystem, sophisticated cmux workflow, sandbox mode

### Codex CLI

**Strongest**:
- `/review` built in — pre-commit diff review with GPT-5.4
- Exposes itself as MCP server — orchestrable by Claude or pi
- Cloud-isolated task execution (separate environments)
- GitHub/Slack/Linear integrations shipped
- Remote TUI (`codex app-server` + `codex --remote`)
- Same hook event model as Claude (PreToolUse, PostToolUse, UserPromptSubmit, Stop, SessionStart)

**Model lock**: GPT-5.4 / 5.3 / Azure OpenAI

**Unique**: **codex-as-MCP-server** — Claude can call Codex as a tool, which is how `codex:codex-rescue` already works in your stack. Adversarial cross-model perspective.

**Already in your stack**:
- `codex:codex-rescue` agent
- `codex:codex-setup` skill
- `dev-tools:codex` skill (custom wrapper)
- `openai-codex` plugin (Anthropic's)
- `codex-companion` runtime
- `beads-workflow:cmux-reviewer` agent uses codex adversarial-review

Codex dispatch is already mature. The frontier is deepening codex-as-MCP usage.

### pi

**Strongest**:
- 13+ model providers: Anthropic (including Claude Pro/Max without API key), OpenAI, Google, Azure, Bedrock, Mistral, Groq, Cerebras, xAI, OpenRouter, Hugging Face, Kimi, MiniMax, GitHub Copilot, Gemini CLI
- **Pi Packages on npm** (keyword `pi-package`) — actually-shipping package marketplace
- TypeScript Extensions API — 25+ lifecycle hook points
- 4 invocation modes: TUI, print/JSON, RPC (stdin/stdout JSONL), TypeScript SDK
- agentskills.io standard (same as Claude + Codex) for skills
- AGENTS.md support + `.pi/settings.json` + `.pi/SYSTEM.md`

**Model lock**: None — broadest by far

**Philosophically excluded**: MCP, subagents, hooks, plan mode. All handled via Extensions.

**Pi Package distribution**:
- npm keyword `pi-package`
- `pi install npm:@foo/pi-tools`
- Discoverable on npmjs.com

## Disler's 5 videos — pattern extraction

### Video 1 — "Pi as Open-Source Alternative to Claude Code" (f8cfH5XX-XU)

**Core thesis**: Pi is philosophically opposite to Claude Code — minimal system prompt (~200 tokens vs ~10,000), no default guardrails, full device access.

**Positioning**: 80% Claude Code for stable work, 20% pi for experimental/custom workflows.

**Demos**:
- Multi-tier extensions system with 25+ hook points (onInput, onToolCall, onAgentEnd)
- "Till done" extension — blocks all tool calls until tasks are marked complete
- Multi-agent sub-command with persistent widget showing parallel agent status
- Sequential agent chains (scout → planner → builder → reviewer)
- Meta-agent that generates extension code

**Claims**:
- Model-provider flexibility enables version pinning
- Open-source allows indefinite behavior freeze (no Anthropic-driven changes)
- Bash tool is the #1 security surface (contradicts earlier paraphrase)

### Video 2 — "The Library" (_vpNQ6IwP9w)

**Core thesis**: Multi-device engineering teams need a distribution layer for skills/agents/prompts. Library is a YAML-based meta-skill.

**Demos**:
- `library add`, `use`, `sync`, `push` commands
- CLI installs referenced code from GitHub repos into `.claude/skills/` on any device
- Workflow: build skill in natural repo → `library add` → `library use` pulls latest across team

**Claims**:
- Valuable agentic tooling stays private
- 2026 theme: trust means knowing exactly what runs
- Custom meta-skill/meta-prompt/meta-agent > generic built-ins

**Relevance**: This solves the broken-marketplace problem. Fork it.

### Video 3 — "CEO + Board of Directors" (TqjmTZRL31E)

**Core thesis**: Use agents at the *highest* leverage — strategic decisions, not coding tasks. 7 Claude models as CEO + board (Revenue, Compounder, Product Strategist, Contrarian, Moonshot, Technical Architect).

**Demos**:
- Structured brief-in, memo-out pipeline
- CEO broadcasts to board in parallel; synthesis loop constrained by time/budget
- Board voted 5-1 on fictional $12M acquisition; Moonshot dissented
- Cost: ~$2.50 per deliberation at $1-5 budget

**Claims**:
- 1M-context on Sonnet 4.6 and Opus 4.6 at flat pricing
- Pi enables custom front matter, runtime variable injection, micro-applications specialized to one task
- "Agent expertise" files (domain-specific persistent memory) compound over sessions

**Relevance**: Your existing `business:council` skill is a 4-agent CEO/board precursor. Evolve it; use for cognovis-level strategic decisions (not just coding).

### Video 4 — "Multi-Team Orchestration" (M30gp1315Y4)

**Core thesis**: Single agent hits a ceiling. Multi-team with persistent mental models solves production-scale codebases.

**Architecture demonstrated**:
```
Orchestrator
  ├── Planning Team
  │     ├── lead (Opus, plans + delegates)
  │     └── workers (Sonnet, execute)
  ├── Engineering Team
  │     ├── lead (Opus)
  │     └── workers: backend-dev, frontend-dev, security, QA
  └── Validation Team
        ├── lead (Opus)
        └── workers (Sonnet)
```

**Demos**:
- Domain-locked permissions (planning lead reads all, writes only expertise dir; must delegate writes to workers)
- Live run: classify prompts with 3 teams in parallel using different models (Minimax 2.7, Step Flash, Sonnet)
- Backend dev accumulated 5,000 tokens of stored context from prior sessions
- Teams A/B failed; Team C (Sonnet) succeeded; orchestrator consolidated

**Claims**:
- Mental model grows autonomously (75-line skill; agent decides content)
- Compounding specialization over sessions
- Three-tier prevents scaling input complexity
- Workers run Sonnet, leads/orchestrator run Opus (cost-tiered)

**Relevance**: This is pi's strongest use case for you — multi-harness dispatch with domain-locked permissions.

### Video 5 — "Agent Harness as the Real Product" (RairMJflUSA)

**Core thesis**: Claude Code's $2.5B ARR isn't the model — it's the harness (deterministic execution, token caching, orchestration, model control). Harness engineering is the underappreciated skill.

**Demos**:
- Three parallel UI generation teams (A, B, C) producing brand-consistent Aegis security dashboards
- 15 agents total, 9 in reduced config
- View generator agent self-tracked 7,000 tokens of design context
- "Till done" task list
- Teams A/B failed → lead agents broke rules, wrote components themselves
- Team C (Sonnet) succeeded

**Claims**:
- Harness control = owning "core four": context, model, prompt, tools
- Swapping models across teams is one-line change
- Open-source harnesses let engineers outperform general tools within their domain

## Core frameworks (from local lesson extracts)

Local extracts at `/Users/malte/code/learning-references/indydevdan/tac-lessons/concepts/` define:

### PETER — 4 elements of AFK (away-from-keyboard) agents

**P**rompt input + **T**rigger + **E**nvironment + **R**eview

- **Prompt input**: source of work (GitHub issues, beads, mail, calendar)
- **Trigger**: event that kicks off (webhook, cron, polling)
- **Environment**: where agents execute (dedicated machine/sandbox)
- **Review**: validation of completed work (PR, structured report)

See doc 05 for how this maps to Shikigami and AFK Dispatcher.

### R&D Framework — context engineering

Every context-engineering technique fits in one of two buckets:

- **Reduce** — minimize unnecessary context entering an agent (strip prose, compress output, narrow scope, rtk)
- **Delegate** — distribute work across specialized context windows (subagents, wave-orchestrator, info-barrier agents)

| Technique | R/D |
|---|---|
| Structured JSON subagent outputs | R |
| rtk bash output compression | R |
| Per-agent expertise files | R (narrow scope) |
| Subagent info-barriers | D |
| wave-orchestrator parallel waves | D |
| pi as meta-orchestrator | D |
| Library pattern (load on demand) | R |
| Codex-as-MCP (separate context pool) | D |

Every design decision should answer: am I reducing context, delegating, or both?

### Agent Experts — plan/build/improve workflow

**Three slash commands per expert**:

- `/expert-plan` — plan expert reads expertise section, writes spec
- `/expert-build` — build expert reads expertise section, implements
- `/expert-improve` — meta-expert analyzes git diff, UPDATES expertise sections

**Self-evolving**: `expert-improve` reads the diff from the implementation and appends learnings. Over time the agent knows the codebase better than any human does.

**Caveat**: this pattern is in video 4's demo but **not shipped in his public repos**. You'd be early adopter.

## The key architectural shift: observability for orchestrators, not humans

From in-session discussion:

- Humans consume summaries (weekly, retro, dashboard)
- Orchestrators consume structured JSON (per-tool-call, per-agent-run)
- AGENTS.md / CLAUDE.md = instructions TO agents
- Output channel = hooks → JSON logs → orchestrator reads → decides next step

Disler's shipped pattern (`claude-code-hooks-mastery`): hooks emit `user_prompt_submit.json`, `post_tool_use.json`, `post_tool_use_failure.json` to `logs/`. Orchestrator consumes. Deterministic control flow.

**Implication**: your bead-orchestrator / wave-orchestrator should consume structured JSON from subagents, not prose. Today many subagents return free-form markdown; the parent has to re-parse. Fix by adding a structured JSON output contract to subagent definitions.

## When to use each harness (decision matrix)

| Task | Harness | Why |
|---|---|---|
| Implementation on beads | Claude Code | cmux, wave-orchestrator, deep tooling |
| Pre-commit diff review | Codex | native `/review`, GPT-5.4 adversarial |
| QA scenario runs | Claude Code | playwright-cli skill already wired |
| Massive-context reads (2M+) | pi + Gemini | only easy Gemini routing |
| Cheap bulk processing | pi + Groq/Cerebras | only harness with these providers (deferred for you — not focus) |
| Local/privacy-sensitive | pi + local model | only harness supporting it cleanly |
| CI/CD automation | Codex Action OR pi RPC mode | non-interactive |
| Remote-controlled dev | Codex `app-server` | built for this |
| Model A/B testing | pi | `/model` cycling + `--models` pool |
| Meta-orchestration (agents that manage agents) | pi | Extensions API |
| Multi-model deliberation (CEO/Board) | pi or Claude | both work; pi has more provider flexibility |

**None replaces the others.**

## The revised multi-harness architecture

```
┌─────────────────────────────────────────────────────────────┐
│ META-ORCHESTRATION (pi)                                     │
│                                                             │
│   pi = orchestrator of complex multi-agent workflows        │
│     - CEO/Board deliberation for strategic decisions        │
│     - Multi-team QA runs with parallel verification         │
│     - Meta-agents that compose other agents                 │
│     - Domain-locked leads → workers hierarchy               │
└───────┬─────────────────────────────────────────────────────┘
        │ orchestrates / spawns
        ▼
┌─────────────────────────────────────────────────────────────┐
│ EXECUTION                                                   │
│                                                             │
│   Claude Code   ← primary: agentic impl, cmux, beads,       │
│                   playwright QA, session management         │
│                                                             │
│   Codex         ← specialized: /review, GPT-5.4 adversarial,│
│                   codex-as-MCP-server for Claude to invoke  │
└───────┬─────────────────────────────────────────────────────┘
        │ all agents emit structured JSON via hooks
        ▼
┌─────────────────────────────────────────────────────────────┐
│ OBSERVABILITY                                               │
│   logs/<session>/*.json      ← per-tool-call, per-agent-run │
│   Subagent outputs = structured contracts (not prose)       │
│   Orchestrator consumes JSON → branches decisions           │
│   Humans see aggregated summaries (not raw logs)            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ MEMORY (three tiers)                                        │
│   expertise/<agent>.md   ← agent auto-curates (narrow)      │
│   open-brain             ← human-curated + lifecycle pipeline│
│                            (auto-triage, refine, materialize)│
│   beads scenarios/design ← per-feature verification specs   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PORTABLE CONTRACT (works with any harness)                  │
│   justfile                ← verbs, humans + agents          │
│   AGENTS.md + CLAUDE.md   ← instructions to agents          │
│   cognovis-library        ← skill/agent distribution catalog│
│   .beads/ (bd)            ← task tracking                   │
│   CLI wrappers            ← ob, searxng, etc. (pi-reachable)│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SECURITY                                                    │
│   DCG          ← destructive command guard (PreToolUse)     │
│   rtk          ← token compression (PreToolUse, post-DCG)   │
│   Sandbox      ← OS isolation (settings.json)               │
│   just + allow ← Bash restricted to declared verbs          │
└─────────────────────────────────────────────────────────────┘
```

## The MCP + pi problem

pi deliberately doesn't speak MCP. Our stack invests heavily in MCP (open-brain, searxng, markitdown, playwright, pencil). Resolution:

### Option A — Dual-mode memory/tools (recommended)

- Ensure open-brain has a CLI interface in addition to MCP (`ob search`, `ob save`)
- Wrap MCP tools in thin CLI shims where pi needs them
- All three harnesses use CLI; Claude/Codex additionally use MCP for richer integration
- One extra layer, universal compatibility

### Option B — pi Extension that bridges to MCP

- Build a pi Extension speaking MCP client internally
- More work, keeps pi feeling native
- Only worth it if pi usage is heavy

### Option C — Accept pi as "ephemeral" harness

- Use pi only for tasks without memory (quick refactors, model experimentation)
- Use Claude/Codex for memory-backed work
- Simplest, but segments workflow

**Recommendation: A.** You already have `bd` as a CLI that works everywhere. Same treatment for open-brain: CLI-first, MCP as enhancement. Future-proofs beyond any specific harness.

## Model routing at harness level

Today: model choice happens inside Claude Code (skill frontmatter `model: sonnet`). That's Claude-specific routing.

Future: harness choice IS the routing. Verb stays stable:

```bash
AI_CLI=codex   just review-bead X    # Codex adversarial review
AI_CLI=gemini  just index-corpus     # Gemini 2M context
AI_CLI=claude  just implement X      # Claude agentic impl
AI_CLI=opencode just local-scan      # local model (privacy)
```

Selection = "which harness is best for this verb given model strength?" Not "which sub-model inside one harness?"

## Three stealable patterns from videos

1. **The Library pattern** — solves broken-marketplace problem. Fork `the-library`, seed `library.yaml`, adopt immediately.
2. **Mental model / expertise files per agent** — third memory tier. Per-agent `expertise/<agent>.md`, autonomously updated by expert-improve. Caveat: not yet in public repos.
3. **Structured JSON output contracts** — observability for orchestrators, not humans. Refactor subagents to return JSON envelopes.

## One anti-pattern to avoid

**"Security theater"**. Disler's personal stance tolerates it; his teaching does not. For mira FHIR + production infra, the bash tool lockdown is mandatory, not optional. rtk + DCG + sandbox + just-allowlist is the minimum.

## Open questions

- **When is pi actually worth pulling in?** First concrete use case: multi-team orchestration across Claude + Codex with domain-locked permissions. No urgency; experiment after course #9 (Elite Context Engineering).
- **Codex-as-MCP deeper use?** Current subprocess dispatch works (`codex:codex-rescue`). Upgrade to MCP when a concrete integration point arises.
- **Gemma local model?** Low priority; user explicitly not a focus. Defer unless a specific use case surfaces.
- **Multi-model deliberation first use case?** Probably cognovis strategic decisions, not coding. Use existing `business:council` as starting point; evolve later.

## Related documents

- Doc 03: Higher-Order Prompts and `just` (harness-agnostic contract layer)
- Doc 05: Shikigami vs AFK Dispatcher (where pi might live)
- Doc 06: Bead Generation Plan (multi-harness beads)
