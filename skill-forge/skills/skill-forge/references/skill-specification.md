# Skill Specification Reference

Complete SKILL.md format reference based on the [Agent Skills](https://agentskills.io) open standard and Claude Code extensions.

## Directory Structure

```
skill-name/
├── SKILL.md           # Main instructions (required)
├── references/        # Detailed docs, checklists (loaded on demand)
├── scripts/           # Executable helpers (loaded on demand)
└── assets/            # Templates, examples (loaded on demand)
```

Only `SKILL.md` is required. Other directories are optional and load on demand via progressive disclosure.

## SKILL.md Format

```yaml
---
# YAML frontmatter (between --- markers)
name: skill-name
description: >
  What the skill does. Use when [trigger scenarios].
  Triggers on "phrase1", "phrase2". Do NOT use for [exclusions].
---

# Markdown body follows
Instructions here...
```

## Frontmatter Fields

### Required/Recommended

| Field | Required | Constraints | Purpose |
|-------|----------|-------------|---------|
| `name` | No (defaults to dir name) | 1-64 chars, `[a-z0-9-]`, no leading/trailing/consecutive hyphens | Becomes `/slash-command` name |
| `description` | Recommended | Max 1024 chars, target 150-300 | Routing: Claude matches user intent to this text |

### Optional (Claude Code Extensions)

| Field | Values | Purpose |
|-------|--------|---------|
| `context` | `fork` | Run in isolated subagent -- no conversation history access |
| `agent` | Agent name (e.g., `Explore`, `Plan`, `general-purpose`) | Which subagent type when `context: fork` is set |
| `user-invocable` | `true` (default) / `false` | `false` hides from `/` menu -- background knowledge only |
| `disable-model-invocation` | `false` (default) / `true` | `true` prevents auto-invocation -- manual `/name` only |
| `allowed-tools` | Space-delimited tool names | Tools Claude can use without asking permission |
| `model` | Model identifier | Override model when skill is active |
| `argument-hint` | e.g., `[issue-number]` | Shown in autocomplete hint |
| `hooks` | Hook config object | Hooks scoped to skill lifecycle |

### Base Spec Fields

| Field | Purpose |
|-------|---------|
| `license` | License identifier |
| `compatibility` | Max 500 chars, compatibility notes |
| `metadata` | Arbitrary key-value map |

## Invocation Control Matrix

| Frontmatter | User can invoke | Claude can invoke | When loaded |
|-------------|----------------|-------------------|-------------|
| (defaults) | Yes | Yes | Description always, body on invocation |
| `disable-model-invocation: true` | Yes | No | Not in context until user invokes |
| `user-invocable: false` | No | Yes | Description always, body on invocation |

## Token Budgets

| Component | Limit | Estimation |
|-----------|-------|------------|
| SKILL.md body | < 500 lines, < 3000 tokens | `words * 1.3` |
| Each reference file | < 2000 tokens | Keep focused on one topic |
| Total skill (all files) | < 10000 tokens | Sum of SKILL.md + all references |

## Loading Priority

When skills share the same name, higher-priority locations win:

1. **Enterprise** (managed settings)
2. **Personal** (`~/.claude/skills/`)
3. **Project** (`.claude/skills/`)
4. **Plugin** (namespaced as `plugin-name:skill-name`, no conflicts)

## Naming Conventions

- **Directory name**: kebab-case, matches `name` field
- **Name reflects function**: `code-reviewer` not `helper` or `my-tool`
- **No org/team prefixes**: `deploy-checker` not `team-alpha-deploy`

## Description Format

Standard pattern:
```
[Function verb phrase]. Use when [2-3 trigger scenarios].
Triggers on "keyword1", "keyword2", "keyword3".
Do NOT use for [exclusions] (use [alternative] instead).
```

Target 150-300 characters. Include 3+ trigger phrases for auto-delegation matching.
