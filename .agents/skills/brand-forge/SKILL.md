---
disable-model-invocation: true
name: brand-forge
model: sonnet
description: Create, review, and manage voice/brand profiles for Claude Code skills. Use when creating brands, reviewing quality, or applying voice profiles. Triggers on create brand, voice profile, review brand, change tone. Not for skill creation.
---

# Brand Forge

Create, evaluate, update, and manage voice/brand profile files that Claude Code skills reference for consistent tone, vocabulary, and writing style.

## When to Use

- "I need a brand for my proposals" / "create a voice profile"
- "Review brand X" / "how good is my brand profile?"
- "Update the tone in brand X" / "change vocabulary rules"
- "What brands do I have?" / "list brands"
- "Rewrite this in the cognovis voice" / "apply brand X to this text"

## Modes

Route based on user intent:

| Mode | Trigger Examples | Action |
|------|-----------------|--------|
| **Create** | "create brand X", "new voice profile" | Interview -> scaffold -> write -> review |
| **Review** | "review brand X", "brand quality" | 5-dimension scoring, produce report |
| **Update** | "update brand X", "change tone" | Load existing, ask what changed, merge |
| **List** | "list brands", "what brands exist?" | Run `scan-brands.sh`, show table |
| **Apply** | "apply brand X to this text" | Resolve brand (+ inheritance), rewrite |

## Create Mode

### 1. Gather Requirements

Use the guided interview from `references/brand-interview-guide.md`. Classify intent first:
- **voice** — tone, vocabulary, writing rules
- **visual** — colors, typography, logo
- **combined** — both

Ask one question group at a time. Skip groups the user already answered in their initial request.

### 2. Scaffold

```bash
scripts/init-brand.sh [--local] [--type=voice|visual|combined] <brand-name>
```

Default: store global brands in the user-level brand directory. Use `--local` for project-specific brands in the project brand directory.

### 3. Write Profile

Fill the template with interview answers. Follow `references/brand-specification.md` for format.

Key constraints:
- Single brand < 2000 tokens
- At least one `<example-good>` block for voice/combined types
- Vocabulary section with Prefer/Avoid lists

### 4. Validate

Run Review mode on the new brand. Target grade B+ or better.

### 5. Inheritance (optional)

If brand extends a parent:
- Set `inherits: parent-name` in frontmatter
- Only write sections that differ from parent
- Combined resolution must be < 3000 tokens

## Review Mode

### 1. Load Context

Read `references/brand-review-checklist.md` for scoring criteria.

### 2. Evaluate

Score against five dimensions:

| Dimension | Weight | Key Criteria |
|-----------|--------|-------------|
| Completeness | 25 pts | Required fields, sections match type, examples present |
| Specificity | 25 pts | Concrete rules, specific vocabulary, measurable constraints |
| Actionability | 20 pts | Skills can immediately apply, clear do/don't |
| Consistency | 15 pts | No contradictions, tone matches examples |
| Token Efficiency | 15 pts | Under 2000 tokens, no redundancy |

### 3. Output

Use the Review output template from `references/brand-review-checklist.md`.

## Update Mode

1. Load the existing brand profile
2. Ask what the user wants to change
3. Show the current section, propose the edit
4. Apply delta — only modify changed sections
5. Verify token budget still met

## List Mode

Run `scripts/scan-brands.sh [--verbose]` and present the output.

Shows all brands from the global and project brand directories with name, type, scope, and description.

## Apply Mode

1. Resolve the target brand (project scope overrides global)
2. If `inherits` is set, load parent and merge (child headings override parent)
3. Read the text to rewrite
4. Apply voice rules: tone, vocabulary preferences/avoidances, writing rules
5. Present before/after with annotations explaining changes

## Do NOT

- Create brands without interviewing about purpose and audience first
- Modify brands without showing current state and confirming changes
- Skip Review after Create — always validate new brands
- Create brands exceeding 2000 tokens — extract to parent via inheritance instead
- Apply brands to code — brands are for human-readable text only
- Assume brand content — always load and read the actual file
- Use inheritance depth > 2 — if you need a grandparent, flatten instead

## Resources

- `references/brand-specification.md` — Complete format reference, frontmatter fields, inheritance rules
- `references/brand-interview-guide.md` — Guided questions per brand type
- `references/brand-review-checklist.md` — Scoring criteria, output templates
- `references/brand-examples.md` — Annotated example brands
- `scripts/init-brand.sh` — Scaffold a new brand profile
- `scripts/scan-brands.sh` — Discover all brands with metadata
