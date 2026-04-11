---
name: spec-developer
model: opus
disable-model-invocation: true
description: >
  Deep feature specification through adaptive Q&A. Use when planning complex
  features needing thorough requirements exploration before implementation.
  Triggers on "spec developer", "feature spec", "deep spec", "requirements spec".
---

# Spec Developer

Produces comprehensive 500-700 line feature specifications through an extensive, adaptive Q&A dialog. Asks 20+ insightful, non-obvious clarifying questions that challenge assumptions and surface edge cases before any implementation planning begins.

Complementary to `/epic-init` and `/plan`: this skill comes *before* both. Flow: `/spec-developer` -> spec document -> `/plan` or `/epic-init` uses spec as input.

## Modes

| Mode | Trigger | Description |
|------|---------|-------------|
| `create` | Default | Full Q&A dialog producing a new spec |
| `review` | `--review <path>` | Validate existing spec against question bank, flag gaps |
| `explore-first` | `--explore` | Spin up explore subagents before questioning |

## Arguments

$ARGUMENTS

| Flag | Effect |
|------|--------|
| (none) | Interactive dialog starting at Phase 1 |
| `"<feature>"` | Pre-fill feature description, skip initial question |
| `--explore` | Run codebase exploration (Phase 1) before Q&A |
| `--review <path>` | Review mode: evaluate existing spec for completeness |

Examples:
```
/spec-developer
/spec-developer "Patient intake FHIR workflow"
/spec-developer --explore "CLI log rotation tool"
/spec-developer --review malte/plans/spec-intake.md
```

---

## Workflow

### Phase 0: Context Loading

1. Read `~/.claude/CLAUDE.md` (user profile, conventions)
2. Read `./CLAUDE.md` (project context, tech stack, architecture)
3. Detect tech stack from project files (package.json, pyproject.toml, Cargo.toml, go.mod, etc.)
4. Summarize: "Project: **[Name]**, Stack: **[Stack]**. Ready to develop your spec."

### Phase 1: Codebase Exploration (only with `--explore`)

Spin up 3-5 explore subagents in parallel to scan relevant areas:

- **Agent 1**: File structure and module layout
- **Agent 2**: Existing data models, schemas, types
- **Agent 3**: API endpoints, CLI commands, entry points
- **Agent 4**: Test patterns and coverage areas
- **Agent 5**: Config files, environment, deployment patterns

Collect findings into a context summary. Use this to inform smarter, more targeted questions in Phase 2.

### Phase 2: Progressive Q&A (7 Themed Rounds)

Load `references/question-bank.md` for the full question catalog.

Ask 3-4 questions per round using `read` with `"Send a message to the user and wait for a response"` tool. Each round has a theme that builds on previous answers. Adapt questions based on what you learn -- skip irrelevant ones, add follow-ups where answers reveal complexity.

**Round order:**

1. **Goals & Motivation** -- Why this feature? What does success look like?
2. **Users & Actors** -- Who uses it? What's their current workflow?
3. **Data & State** -- What data exists, gets created, gets modified?
4. **Behavior & Edge Cases** -- Happy path, failure modes, concurrency?
5. **Error Handling & Recovery** -- How do errors surface? Can users recover?
6. **Integration & Dependencies** -- What systems are touched? APIs?
7. **Constraints & Non-Functionals** -- Performance, security, accessibility?

**Questioning rules:**

- Ask 3-4 questions per round, never more than 4
- Frame questions to challenge assumptions, not just confirm them
- When an answer reveals unexpected complexity, add a follow-up in the same round
- When an answer is "I don't know yet", note it as an Open Question for the spec
- Summarize key insights after each round before moving to the next
- Total: minimum 21 questions across all rounds

### Phase 3: Spec Generation

After all rounds complete, generate the spec document using `references/spec-template.md` as the structural guide.

**Output rules:**

- Target 500-700 lines of Markdown
- Save to `malte/plans/spec-<feature-name>.md` (kebab-case)
- Every functional requirement must be numbered and testable
- Include all "I don't know" answers as Open Questions
- Data model section includes entity relationships and state transitions
- Edge cases section references specific answers from the Q&A

Present the generated spec to the user for review.

### Phase 4: Refinement Loop

After presenting the spec:

1. Ask: "What's missing? What needs more detail? What did I get wrong?"
2. Iterate on feedback -- update the spec in place
3. Repeat until user confirms: "Looks good" / "Done" / "Ship it"
4. Final save and summary: "Spec saved to **[path]** ([N] lines, [M] requirements)."

---

## Review Mode (`--review`)

When invoked with `--review <path>`:

1. Load the existing spec document
2. Load `references/question-bank.md`
3. Evaluate each question category: does the spec adequately address it?
4. Produce a gap report:
   - **Covered**: Sections that are thorough
   - **Gaps**: Questions the spec doesn't answer
   - **Weak**: Sections present but lacking depth
5. Offer to fill gaps interactively via follow-up Q&A

---

## Do NOT

- Do NOT ask more than 4 questions per round (user fatigue)
- Do NOT make implementation decisions -- this is requirements, not design
- Do NOT produce task breakdowns or work estimates (use `/epic-init` for that)
- Do NOT skip the refinement loop (Phase 4) -- always ask what's missing
- Do NOT generate specs shorter than 400 lines -- if the feature is too small for a spec, tell the user to use `/plan` instead

## Resources

- `references/question-bank.md` -- Full question catalog with insight notes and follow-up triggers
- `references/spec-template.md` -- Output structure template with section guidance
