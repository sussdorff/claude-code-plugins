# Higher-Order Prompts and `just` Architecture

**Session date**: 2026-04-14
**Scope**: The four-layer mental model (skill → agent → command → `just`), Higher-Order Prompts (HOP) as vocabulary, and the bash lockdown strategy.

## Summary

We named a four-layer model for agent work. The fourth layer (`just` recipes) was missing from our stack and turns out to be the most portable one. Adopting `just` gives us: (1) shareable versioned commands, (2) humans and agents calling the same thing, (3) a permission allowlist model that replaces scattered Bash-pattern permissions, (4) self-documenting discoverability.

## The four-layer model

```
Layer 4 — just            (stable, versioned, shell-level contract)
          └── invokes
Layer 3 — command/HOP     (prompt that orchestrates work, parameterizable)
          └── given to
Layer 2 — agent           (entity with capabilities + context isolation)
          └── uses
Layer 1 — skill           (capability primitive)
```

Unix philosophy for agents: primitives → composers → tasks → stable interface.

## Higher-Order Prompts (HOP) — the vocabulary

A **Higher-Order Prompt** is a prompt that takes another prompt as a parameter. Like a function of functions.

Examples from our stack that we never called HOPs before:

| HOP | Takes as argument |
|---|---|
| `beads-workflow:wave-orchestrator` | Multiple bead IDs → prompts per bead |
| `beads-workflow:bead-orchestrator` | One bead → lifecycle prompts (plan/impl/review) |
| `business:council` | Document → 4 perspective prompts |
| `dev-tools:scenario-generator` | Bead description → scenario template prompt |
| `core:prompt-refiner` | Raw text → cleaned/structured prompt |

HOP is not a new capability. It's a label for a pattern we already use heavily. Naming it clarifies design conversations.

Bowser's `/ui-review` is a HOP: "for each story file, invoke QA-agent(story)." Generic pattern: HOP fans out sub-prompts to specialized subagents.

## Why `just` is the missing layer

`just` (https://github.com/casey/just) is a command runner similar to `make` but designed for human-run recipes. Three properties make it the right fourth layer:

### 1. Shareable, repo-scoped, versioned commands

| Where workflow logic lives today | Visibility | Review |
|---|---|---|
| Global skill in `~/.claude/` | Only you | No |
| Plugin skill | Fleet; out-of-repo | Plugin PR only |
| Slash command | Same as plugin | Same |
| **`justfile` in repo** | **Everyone with the repo** | **PR'd with the code** |

Project-specific workflows (deploy mira, seed mira DB, run mira QA) are the wrong thing to bake into skills — they leak project knowledge into global config. `justfile` is the right home.

### 2. Dual-use: humans and agents invoke the same verb

- Dev typing `just review-bead mira-01p` in terminal
- Claude running `Bash(just review-bead mira-01p)`
- Both hit the same code path with the same result

Today many of our skills work for Claude but can't be run by a human without going through Claude. `just` fixes that asymmetry.

### 3. Permission allowlist clarity

Current permission model is messy — dozens of `Bash(X:*)` patterns scattered in `permissions.yml`.

With `just`:

```yaml
# BEFORE (scattered)
- "Bash(bd:*)"
- "Bash(git status)"
- "Bash(git diff:*)"
- "Bash(rg:*)"
- "Bash(sg:*)"
- "Bash(curl:*)"
- ... dozens more

# AFTER (curated)
- "Bash(just review:*)"       # entire review family
- "Bash(just bead:*)"          # entire bead family
- "Bash(just deploy-staging)"  # specific deploy
- "Bash(rg:*)"                  # utility: search
- "Bash(sg:*)"                  # utility: AST search
- "Bash(git status)"            # utility: status-only
# NO generic Bash
```

**The justfile IS the capability manifest.** Code-reviewed. Diffable. No "allow Bash, pray the prompt doesn't misbehave."

### 4. Self-documenting

`just --list` enumerates every verb the repo exposes. Agents and humans learn the repo's capabilities without reading skill definitions.

## What `just` does NOT buy you

### Coarse permission granularity

`Bash(just deploy-prod)` is fine; `Bash(just deploy-prod --env=staging-only)` is hard to enforce. Permission patterns match prefixes, not semantics.

Mitigation: split recipes (`just deploy-staging`, `just deploy-prod`) so the verb name carries the risk.

### Tool sprawl

Every new repo gets a justfile. They drift.

Mitigation: base `justfile-common` in `claude-code-plugins`, imported via `import '../common.just'`. Or a `project-setup` skill that scaffolds a consistent justfile skeleton.

### Escaping hell

`just recipe "arg with spaces and 'quotes'"` is routinely broken for complex strings.

Mitigation: long prompt arguments (scenario text) pass via stdin or file path, not CLI arg. Design recipes accordingly.

### Not a replacement for utility Bash

Trivial calls (`git status`, `rg foo`, `jq .data`) should stay direct. `just` is for **multi-step or higher-order** operations. Fighting this produces bloat: 50 one-line recipes that wrap one shell command.

### Doesn't solve context isolation

`just ui-review` doesn't know about Claude's subagent boundaries. The subagent still has to be spawned by a command or agent definition. `just` is the entry, not the isolator.

## Decision matrix: which layer for which task

| I need to... | Right layer |
|---|---|
| Encapsulate how to do X (reusable primitive) | Skill |
| Run X in isolated context with specific capabilities | Agent |
| Describe a multi-step task with parameters | Command (slash or HOP) |
| Make X a stable shell verb any human/agent can invoke | `just` recipe |
| Expose a curated safe surface to agents with restricted Bash | `just` + permission allowlist |
| Ship workflow logic that lives with the code | `just` in repo |
| Ship workflow logic that's project-agnostic | Skill in plugin |

Layers are not competing. They compose.

## Integration with slash commands

Slash commands remain valuable — they're Claude Code's native chrome. They compose with `just`:

```
User types: /ui-review mira-01p
Slash command expands to HOP:
  "Run `just review-bead mira-01p` and summarize results"
Shell runs: just review-bead mira-01p
Recipe spawns: qa-agent subagent
Agent invokes: playwright-cli skill
```

Slash command = Claude-native entry. `just` = shell-native entry. Same workflow reachable from both. No forking.

## The Library pattern (disler's shipping implementation)

`https://github.com/disler/the-library` — a real, shipping solution for cross-project skill distribution. Use it to replace the broken Claude Code plugin marketplace.

### How it works

1. Fork `the-library` template → create new repo (suggested: `cognovis-library`)
2. Customize `library.yaml` with skill/agent/prompt references (local paths or GitHub URLs)
3. Use `/library` commands to pull, push, sync across devices and teams
4. Supports `requires:` for dependency resolution

### Relationship to claude-code-plugins

`the-library` is the **catalog**, not the source. claude-code-plugins stays your working repo where skills are developed. The library catalogs pointers.

```
claude-code-plugins/     ← source (keep developing here)
  beads-workflow/skills/
  dev-tools/skills/
  core/skills/
  ...

cognovis-library/         ← NEW repo (fork of the-library)
  library.yaml            ← references skills in claude-code-plugins
  scripts/sync.sh
```

Sample `library.yaml`:

```yaml
skills:
  - name: beads
    source: github:malte/claude-code-plugins//core/skills/beads
  - name: qa-agent
    source: github:malte/claude-code-plugins//dev-tools/skills/qa-agent
  - name: scenario-generator
    source: github:malte/claude-code-plugins//dev-tools/agents/scenario-generator
  - name: playwright-cli
    source: github:malte/claude-code-plugins//dev-tools/skills/playwright-cli

agents:
  - name: bead-orchestrator
    source: github:malte/claude-code-plugins//beads-workflow/agents/bead-orchestrator
```

On deploy or new machine: clone `cognovis-library`, run `library sync`, skills land in `.claude/skills/`. Works for shikigami-bot deploy, hokora AFK dispatcher deploy, new workstation setup.

**Do not migrate anything INTO the library.** The library catalogs pointers. claude-code-plugins stays your working repo.

## Security layers — the stack

Disler emphasizes (contradicting an earlier impression I gave): the bash tool is the #1 security surface. Full stack for lockdown:

| Tool | Concern | When it fires | Install priority |
|---|---|---|---|
| **rtk** | Token compression on Bash output (60–90% savings) | PreToolUse, rewrites command | Week 1 — free win |
| **Anthropic sandbox** | OS-level isolation | Always if enabled | Week 1 — 1 line settings.json |
| **DCG** | Block destructive commands (`rm -rf`, `git push --force`, `curl \| sh`) | PreToolUse, before command | Week 2 — pair with just allowlist |
| **Permission allowlist + `just`** | Curate which verbs exist | PreToolUse permission check | Week 2–3 — gradual |

Hook order: `DCG → permission check → rtk rewrite → execute`. DCG blocks dangerous patterns; permissions check allowlist; rtk compresses output on the way back.

### Important clarification

- **rtk is context (token compression)** — NOT a security tool. It makes bash output cheaper; does not block anything.
- **DCG is security (destructive command guard)** — NOT a context tool.
- Earlier framing "security is mostly theater" was a paraphrase of disler's personal stance, not his teaching. In his teaching material he explicitly identifies bash as the #1 surface. For healthcare/FHIR context, full lockdown is required.

## Harness-agnostic implications

This four-layer model plus `just` plus Library plus AGENTS.md gives us portability across Claude Code + Codex + pi.

| Primitive | Claude Code | Codex | pi | Portable? |
|---|---|---|---|---|
| AGENTS.md | ✅ via CLAUDE.md + AGENTS.md | ✅ native | ✅ native | Yes |
| agentskills.io skills | ✅ | ✅ | ✅ native | Yes |
| `.mcp.json` | ✅ | ✅ | ❌ (Extensions) | Partial |
| Subagents | ✅ | ✅ via config.toml | ❌ (Extensions) | Conceptually yes |
| Hooks | ✅ | ✅ same events | ❌ (Extensions) | Claude ↔ Codex yes |
| **`just` recipes** | ✅ | ✅ | ✅ | **Yes** |
| **bd, crwl, other CLIs** | ✅ | ✅ | ✅ | **Yes** |
| **Library (cognovis-library)** | ✅ | ✅ | ✅ | **Yes** |

`just` is the only layer that survives every harness swap. See doc 04 for the full multi-harness implications.

## Concrete first justfile (starter)

For each project, a minimal starter:

```makefile
# <project>/justfile

# Default: show available commands
default:
    @just --list

# === beads ===
bead-ready:
    bd ready

bead-show id:
    bd show {{id}}

bead-claim id:
    bd update {{id}} --claim

bead-close id:
    bd close {{id}}

# === review ===
review-bead id:
    #!/usr/bin/env bash
    echo "Loading scenario from bead {{id}}"
    bd show {{id}} --json | jq -r .design
    # dispatch to qa-agent (once built)

review-process file:
    echo "Loading business-process scenario from {{file}}"
    # dispatch to qa-agent (once built)

# === dev ===
test:
    # project-specific test command

lint:
    # project-specific lint command

# === deploy ===
# Split by risk level
deploy-staging:
    # safe deploy

deploy-prod:
    # risky deploy
```

## Migration strategy

### Phase 1 — additive (no breakage)

- Install just on all workstations (`brew install just`)
- Create justfile in mira (first, as proving ground)
- Add 5-10 recipes for most common operations
- Document in mira/CLAUDE.md how to invoke
- Keep existing bash permissions intact

### Phase 2 — prefer-just (gradual)

- Add more recipes as new workflows arise
- Update mira CLAUDE.md to say "prefer `just <verb>` for workflow ops"
- Train agents (via bead descriptions) to use `just` for common ops

### Phase 3 — lock down

- Audit mira permissions.yml
- Restrict generic `Bash(*)` to utility commands only
- Allow `Bash(just *)` + minimal utilities
- Install DCG for belt-and-suspenders

### Phase 4 — propagate

- Roll same pattern to claude-code-plugins, fhir-praxis-de, shikigami-bot, etc.
- Shared `justfile-common` to avoid drift
- project-setup skill scaffolds justfile for new repos

## Component ownership

| Component | Repo | Why |
|---|---|---|
| project-setup scaffolding justfile | `claude-code-plugins/dev-tools/skills/project-setup` | Reusable |
| `justfile-common` snippets | `claude-code-plugins/justfile-common/` (new) | Shared recipes |
| Project-specific justfiles | Each project repo | Project-owned |
| `cognovis-library` (Library fork) | New repo | Distribution catalog |
| Permission patterns | per-project `permissions.yml` | Project-owned |
| DCG / rtk / sandbox config | `claude-code-plugins/` + user settings | Global |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Two entry points confuse newcomers (slash command vs `just`) | Document: slash command = Claude sugar; `just` = universal. Both compose. |
| Agents hit permission denied when needing a new verb | Log denial → PR to justfile → review → deploy. Short feedback loop. |
| Justfile becomes a dumping ground | Organize by section (beads, review, dev, deploy); enforce review discipline. |
| Projects fork justfile-common silently | Audit quarterly; `bd doctor --check=conventions` if we formalize. |
| rtk/DCG install order matters | Document hook order: DCG first, rtk second. |

## Open questions

- **Should justfile recipes be the primary dispatch for pi too, or does pi get its own Extension-based equivalent?** Probably justfile for recipes; pi Extensions for custom behaviors not expressible as recipes.
- **How do we handle recipe arguments that are long scenario text?** Via file path or stdin, not CLI arg.
- **Do we want a `just-repl` mode for exploratory work?** Not needed short-term; revisit if friction surfaces.
- **Shared secrets/config between justfile recipes and skills?** Use `op` (1Password CLI) for secrets; standard env files for non-sensitive config.

## Related documents

- Doc 01: Bowser Comparison (consumes `just review-bead` as the entry)
- Doc 04: Claude + Codex + pi Orchestration (why `just` is the portability layer)
- Doc 06: Bead Generation Plan (lists specific beads for `just` adoption)
