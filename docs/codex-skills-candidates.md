# Codex Skills Candidates

## Selection Criteria

Skills are selected for Codex/agentskills-compatible conversion based on the following criteria:

**Include** (all criteria must be met):
1. **Instruction-heavy** — the skill's value is primarily procedural knowledge and workflow guidance, not raw tool plumbing
2. **Low tool-dependency** — uses standard shell commands (`bash`, `grep`, `curl`, etc.) or project-local scripts, not harness-specific MCP tools
3. **No cmux / worktree / Claude-agent dependency** — does not require Claude Code's multi-window cmux topology or worktree orchestration
4. **No hard dependency on Claude slash-commands** — does not use `/epic-init`, `/inject-standards`, or similar as primary workflow steps (these can move to an adapter)
5. **No hard dependency on MCP tool names** — `mcp__open-brain__*`, `mcp__playwright__*` etc. can be isolated in a SKILL.claude-adapter.md

**Defer** (any one criterion is sufficient):
- Heavy use of Claude-specific paths that represent core functionality (not just a storage detail)
- Requires `/claude-config-handler`, `bd init`, or other Claude Code infrastructure commands as non-optional steps
- Entire workflow is meaningless outside Claude Code (e.g., harness self-management skills)
- Hardcoded personal paths (`/Users/malte/...`) that form the core of the skill's value

## Candidate List

| # | Skill | Source | Status | Notes |
|---|-------|--------|--------|-------|
| 1 | project-health | dev-tools/skills/ | ✅ converted | Adapter split: harness check paths + CLAUDE.md ref → adapter |
| 2 | binary-explorer | dev-tools/skills/ | ✅ converted | Clean; minimal adapter stub only |
| 3 | entropy-scan | meta/skills/ | ✅ converted | Adapter split: malte/skills/ script path → adapter |
| 4 | nbj-audit | meta/skills/ | ✅ converted | Adapter split: malte/skills/ + malte/agents/ detection paths → adapter |
| 5 | system-prompt-audit | meta/skills/ | ✅ converted | Adapter split: malte/system-prompts/ paths + registry → adapter |
| 6 | vision | core/skills/ | ✅ converted | Adapter split: /epic-init slash-command → adapter |
| 7 | infra-principles | infra/skills/ | ✅ converted | Clean; minimal adapter stub only |
| 8 | skill-auditor | meta/skills/ | ✅ converted | Adapter split: ~/.claude/standards/ paths + eval-viewer path → adapter |
| 9 | token-cost | meta/skills/ | ✅ converted | Adapter split: mcp__open-brain ref + ~/.claude/ paths → adapter |
| 10 | agent-forge | meta/skills/ | ✅ converted | Clean; minimal adapter stub (disableModelInvocation note) |

## Deferrals

| Skill | Rationale |
|-------|-----------|
| `dev-tools/skills/project-setup` | Heavy dependency on Claude Code infrastructure: `bd init --server`, `/inject-standards`, `/claude-config-handler`, `bd dolt` commands, hardcoded personal paths (`/Users/malte/...`). The entire workflow is Claude Code + beads + this specific user's setup. Not meaningfully portable. |
| `dev-tools/skills/playwright-cli` | The skill is a command reference for the `playwright-cli` CLI tool. The `allowed-tools: Bash(playwright-cli:*)` frontmatter is a Claude Code permission key and not portable. The skill's primary audience is Claude Code users who need the tool reference. It could be ported but offers little value to Codex which uses MCP playwright tools with a different API. |
| `beads-workflow/*` | All beads-workflow skills (`plan`, `impl`, `wave-orchestrator`, `epic-init`, etc.) have deep dependencies on the beads CLI (`bd`), Dolt-backed issue tracking, and Claude Code worktree orchestration. These are Claude Code + beads-specific infrastructure skills — the workflow is meaningless outside that stack. |
| `dev-tools/skills/codex` | This skill wraps the Codex CLI itself. Converting it to an agentskills-compatible format creates a circularity: it would be a Codex skill that tells Codex how to run Codex. |
| `core/skills/dolt` / `core/skills/event-log` | These skills troubleshoot or query Claude Code harness internals (`~/.claude/events.db`, Dolt server). Entirely Claude Code infrastructure. |
| `meta/skills/hook-creator` | Creates Claude Code hooks (`.claude/settings.json` `hooks:` config). Deeply Claude Code specific. |
| `meta/skills/agent-forge` | Actually included above — passes portability checks. The `.claude/agents/` references are structural doc, not harness API calls. |
