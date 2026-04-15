# sussdorff-plugins

Personal Claude Code plugin bundles — 8 category plugins covering infrastructure, business
operations, content creation, healthcare/FHIR, development tooling, harness authoring, core
session essentials, and beads-workflow orchestration.

Repository: https://github.com/sussdorff/claude-code-plugins

## Installation

Add the marketplace and install plugins by name:

```bash
# Add the marketplace
/plugin marketplace add sussdorff/claude-code-plugins

# Browse
/plugin

# Install individual bundles
/plugin install core@sussdorff-plugins
/plugin install dev-tools@sussdorff-plugins
/plugin install beads-workflow@sussdorff-plugins
```

## Plugins

Each plugin is a category bundle of skills, agents, and (where applicable) lifecycle hooks.
Install only the bundles you need — bundles are independent.

### core

Essential skills for every session: beads, dolt, standards injection, cmux, prompt-refiner,
summarize, vision, event-log. Ships `session-close` and git-operations agents, plus
`read-before-edit` and `rules-loader` hooks.

Key skills: `beads`, `dolt`, `standards`, `cmux`, `prompt-refiner`, `summarize`, `vision`,
`event-log`, `inject-standards`.

### beads-workflow

Beads orchestration and lifecycle — wave-orchestrator, epic-init, retro, compound,
bead-metrics, workplan, intake. Ships bead-orchestrator, quick-fix, review-agent,
verification-agent, plan-reviewer and session-context hooks.

Key skills: `wave-orchestrator`, `epic-init`, `plan`, `impl`, `retro`, `compound`,
`bead-metrics`, `workplan`, `intake`, `factory-check`, `stringer`.

### dev-tools

Development tooling — browser automation via `playwright-cli`, OpenAI Codex CLI wrapper
(`codex`), `bug-triage`, `project-health`, `project-setup`, `project-context`, `spec-developer`.
Ships 16 test/review agents (implementer, test-author, test-engineer, scenario-generator,
holdout-validator, UAT validator, chrome-devtools-tester, etc.) and `anatomy-index` / `buglog`
hooks.

Key skills: `playwright-cli`, `codex`, `bug-triage`, `project-health`, `project-setup`,
`project-context`, `spec-developer`.

### infra

Infrastructure management — Hetzner Cloud and UniFi CLIs, home network topology, local VMs,
document archives (Paperless, Piler), `portless` reverse-tunnel management, deployment
principles.

Key skills: `hetzner-cloud`, `ui-cli`, `home-infra`, `infra-principles`, `local-vm`,
`paperless-cli`, `piler-cli`, `portless`.

### business

Business operations — proposal writing, invoicing (Collmex, Google One), Amazon order history,
MoneyMoney finance queries, 1Password credentials, email dispatch via Apple Mail, AI readiness
/ career check, multi-perspective document review (`council`).

Key skills: `angebotserstellung`, `collmex-cli`, `google-invoice`, `amazon`, `mm-cli`,
`op-credentials`, `mail-send`, `ai-readiness`, `career-check`, `council`.

### content

Content creation and social — LinkedIn automation, brand/voice profiles, Pencil UI design,
audio transcription via AssemblyAI, cmux browser/markdown surfaces.

Key skills: `linkedin`, `brand-forge`, `pencil`, `transcribe`, `cmux-browser`, `cmux-markdown`.

### medical

Healthcare and FHIR — Mira-specific Aidbox configuration, billing catalog review
(EBM/GOA/HZV), and independent reviewer agents for GDPR/EU AI Act compliance and clinical UX
human factors.

Key skills: `mira-aidbox`, `billing-reviewer`. Agents: `compliance-reviewer`,
`human-factors-reviewer`.

### meta

Harness authoring and audit — agent/hook/skill/plugin creation, entropy scan, NBJ agent
primitives audit, system prompt audit, token cost measurement, CLAUDE.md pruning, fleet-wide
skill auditing, standards sync.

Key skills: `agent-forge`, `hook-creator`, `plugin-management`, `entropy-scan`, `nbj-audit`,
`system-prompt-audit`, `token-cost`, `claude-md-pruner`, `skill-auditor`, `sync-standards`.

## Repo Conventions

- **Issue tracking**: [`beads`](https://github.com/steveyegge/beads) (`bd`) backed by a Dolt
  remote. Run `bd prime` for the workflow, `bd ready` to find work, `bd show <id>` for detail.
  Do not use TodoWrite/TaskCreate or markdown TODOs.
- **Versioning**: CalVer at repo level (`VERSION`, git tag), SemVer in each
  `plugin.json`.
- **Python scripts**: Scripts with external dependencies use
  [PEP 723](https://peps.python.org/pep-0723/) inline metadata with `uv` so they travel
  self-contained into `~/.claude/`. Stdlib-only scripts use plain `python3`. See
  [`CLAUDE.md`](./CLAUDE.md) for templates.
- **Project context**: See [`docs/project-context.md`](./docs/project-context.md) for
  architecture principles, module map, patterns, and invariants.
- **Architecture notes**: Design sessions are captured under
  [`docs/architecture/`](./docs/architecture/) in dated folders.

## Development

This repo uses a symlinked `.claude/` pattern — the project's own harness state lives in
`~/code/claude/claude-code-plugins/` and is git-ignored, so local session state never ships
with the marketplace.

When developing a new plugin or skill:

1. `bd create --title="..." --description="..."` — file the issue first.
2. Add skill/agent/hook files under the appropriate plugin directory.
3. Register the skill in the plugin's manifest if required.
4. Close the bead and run `session-close` (commits, tags, pushes).

See [`CLAUDE.md`](./CLAUDE.md) for full standards and the
[`meta` plugin](./meta/) for authoring helpers (`agent-forge`, `hook-creator`,
`plugin-management`, `skill-auditor`).

## Contributing

Issues and PRs welcome. For substantive changes, file a bead first so work is trackable.

## License

MIT — see [LICENSE](./LICENSE).

Copyright © 2025 Malte Sussdorff.

## Changelog

See [CHANGELOG.md](./CHANGELOG.md).
