# Brand Profile Specification

Complete format reference for brand/voice profile files used by Claude Code skills.

## File Location

| Scope | Path | Priority |
|-------|------|----------|
| Global (personal) | `~/.claude/brands/<name>.md` | Lower |
| Project-specific | `.claude/brands/<name>.md` | Higher (overrides global) |

Project brands override global brands with the same name.

## File Format

Brand profiles use **Markdown with YAML frontmatter** — the same format as SKILL.md, standards, and CLAUDE.md files.

```yaml
---
name: brand-name           # Required. kebab-case, [a-z0-9-], no leading/trailing hyphens
type: voice                # Required. voice | visual | combined
description: "Short text"  # Required. 1-2 sentences describing this brand's purpose
inherits: parent-name      # Optional. Parent brand to inherit from
version: 1                 # Required. Integer, increment on breaking changes
tags: [tag1, tag2]         # Optional. For discovery and filtering
---

# brand-name

Markdown body with profile sections...
```

## Frontmatter Fields

| Field | Required | Type | Constraints |
|-------|----------|------|-------------|
| `name` | Yes | string | 1-64 chars, kebab-case `[a-z0-9-]`, no leading/trailing/consecutive hyphens |
| `type` | Yes | enum | `voice`, `visual`, `combined` |
| `description` | Yes | string | Max 300 chars. What this brand is for |
| `inherits` | No | string | Name of parent brand (must exist in same or higher scope) |
| `version` | Yes | integer | Start at 1, increment on breaking changes |
| `tags` | No | list | Lowercase kebab-case strings for filtering |

## Profile Types

### `voice` — Tone, vocabulary, writing rules

Sections: Tone & Register, Vocabulary, Writing Rules, Examples.

### `visual` — Colors, typography, logo usage

Sections: Colors, Typography, Logo Rules, Spacing.

### `combined` — Both voice and visual

Contains all sections from both types. Use when a brand needs unified voice + visual guidance.

## Body Sections

### Voice Profile (type: voice | combined)

```markdown
## Voice Profile

### Tone & Register
- Formality level (du/Sie, casual/formal)
- Emotional register (warm, neutral, authoritative)
- Perspective (solution-oriented, analytical, empathetic)

### Vocabulary
#### Prefer
- Terms to use (with rationale)
#### Avoid
- Terms to avoid (with what to use instead)

### Writing Rules
- Sentence structure preferences
- Paragraph length guidelines
- Formatting conventions

### Examples

<example-good>
Concrete example of text following this brand's voice.
</example-good>

<example-bad>
Same content written poorly — violating the brand's rules.
</example-bad>
```

### Visual Profile (type: visual | combined)

```markdown
## Visual Profile

### Colors
- Primary, secondary, accent colors (hex/name)
- When to use each

### Typography
- Font families, sizes, weights

### Logo Rules
- Placement, minimum size, clear space

### Spacing
- Margins, padding conventions
```

## Inheritance

Brand profiles support **single-parent inheritance** with **max 2 levels**.

### Semantics

- Child inherits all sections from parent
- Child sections **override** parent sections at the heading level
- If child defines `### Tone & Register`, it replaces the parent's entirely
- If child omits a section, parent's version is used
- Child frontmatter fields override parent fields (except `name`)

### Resolution Order

1. Load child brand
2. If `inherits` is set, load parent brand
3. Merge: child headings override parent headings, parent fills gaps
4. If parent also has `inherits`, stop — max 2 levels enforced

### Constraints

- Max depth: 2 (child -> parent, no grandparents)
- Parent must exist in same or higher scope (project can inherit from global)
- Circular references are invalid
- WHY max 2 levels: deeper hierarchies create debugging nightmares and token bloat when resolved

## Token Budget

| Component | Limit | Estimation |
|-----------|-------|------------|
| Single brand file | < 2000 tokens | `words * 1.3` |
| Brand + resolved parent | < 3000 tokens combined | After inheritance merge |

WHY these limits: brands are injected into skill context at runtime. Larger brands eat into the skill's own token budget.

## Skill Integration

Skills reference brands via the `brand:` field in their SKILL.md body or a comment near the top:

```markdown
<!-- brand: malte-professional -->
```

Or in workflow instructions:

```markdown
## Voice
Load brand profile: `malte-professional`
```

When a skill declares a brand:
1. Resolve the brand (check project scope, then global)
2. If `inherits`, resolve parent and merge
3. Inject the resolved voice/visual profile into the skill's context

Skills without a `brand:` reference operate without brand guidance — this is opt-in.

## Naming Conventions

- **File name** matches `name` field: `malte-professional.md` for `name: malte-professional`
- Names describe identity, not function: `cognovis-proposals` not `proposal-voice`
- Parent brands use broader names: `malte-professional` not `malte-professional-base`

## Validation Rules

A valid brand profile must:
1. Have all required frontmatter fields
2. Pass kebab-case name validation
3. Have at least one `## Voice Profile` or `## Visual Profile` section matching its type
4. Stay within token budget (< 2000 tokens)
5. If `inherits`: parent must exist and combined resolution must be < 3000 tokens
6. Have at least one `<example-good>` block (for voice/combined types)
