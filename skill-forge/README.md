# skill-forge

Quality-focused skill development toolkit for Claude Code. Create, review, refactor, audit, and optimize skills against a bundled quality standard.

## What it does

skill-forge helps you build better Claude Code skills by providing structured workflows for every stage of skill development:

| Mode | What it does |
|------|-------------|
| **Create** | Scaffold and build new skills from requirements |
| **Review** | Score skills against quality standard (A-F grading) |
| **Refactor** | Review + generate concrete before/after rewrite suggestions |
| **Audit** | Scan all skills, produce fleet-wide quality report |
| **Optimize** | Focused trigger and description quality improvements |

## Installation

Install via the Claude Code plugin system from the `sussdorff/claude-code-plugins` marketplace.

## Usage

skill-forge activates automatically when you mention skill creation or quality:

```
"create a skill for X"
"review skill Y"
"audit all skills"
"refactor skill Z"
```

Or invoke manually: `/skill-forge:skill-forge`

## Scaffolding

The bundled `init-skill.sh` script creates a new skill directory with a template:

```bash
# Global skill (default: ~/.claude/skills/)
scripts/init-skill.sh my-tool

# Project-specific skill
scripts/init-skill.sh --local my-tool
```

Override the global skills directory with the `SKILL_FORGE_GLOBAL_DIR` environment variable.

## Quality Standard

The plugin bundles a comprehensive quality standard at `references/quality-standard.md` covering:

- Frontmatter and description format
- SKILL.md structure and section order
- Writing style (imperative, WHY statements)
- Progressive disclosure patterns
- Prompt engineering techniques (Six-Layer Stack, Goldilocks Zone)
- Quality checklist and anti-patterns

## Complementary plugins

- **plugin-developer** — How to build Claude Code plugins, skills, commands, and agents (structure and mechanics)
- **skill-forge** — How to make skills *good* (quality, scoring, refactoring)

## License

MIT
