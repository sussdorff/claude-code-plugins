---
name: command-creator
description: Guide for creating effective slash commands. Use when creating custom commands, converting repeated prompts into commands, or improving existing commands. Guides through command vs CLAUDE.md decisions, structure design, parameter planning, model selection, and tool permissions.
---

# Command Creator

Guide for creating effective custom slash commands in Claude Code.

## Overview

Commands are user-invoked shortcuts that expand to prompts. Unlike skills (Claude decides when to use) or CLAUDE.md (always available), commands are explicit user actions.

**Key characteristics:**
- User-triggered with /command-name
- Can accept arguments ($ARGUMENTS, $1, $2, etc.)
- Configurable model and tool permissions
- Reusable across projects
- Available immediately after creation

## When to Use Commands

Consult `references/decision-criteria.md` for complete decision guidance.

**Use commands when:**
- Workflow repeated frequently (multiple times per week)
- Pattern reusable across projects/team
- Consistent structure that can be parameterized
- Team would benefit from standardization
- 2-10 clear, sequential steps

**Use CLAUDE.md instead when:**
- Guidance is project-specific (conventions, patterns)
- General context always relevant
- Workflow is ad-hoc and doesn't repeat
- Heavy context-specific customization needed

**Key principle:** If typing same instructions repeatedly → command. If always relevant to project → CLAUDE.md.

## Command Creation Workflow

Follow this workflow for creating effective commands. Each step references detailed guidance in bundled resources.

### Step 1: Assess if Command is Appropriate

Before creating a command, verify it's the right approach.

**Decision criteria:**
- Repeated frequently? → Command
- Project-specific context? → CLAUDE.md
- Ad-hoc workflow? → Neither, just use naturally

**Reference:** `references/decision-criteria.md` for complete decision tree with examples.

**Output:** Clear decision that command is appropriate.

---

### Step 2: Gather Command Requirements

Collect information through focused questions (ask 2-3 at a time, iterate).

**Core questions:**
- Purpose: What task should this accomplish?
- Examples: How would you use it? (2-3 concrete examples)
- Frequency: How often? (daily, weekly, per-project)
- Scope: Project-specific (.claude/commands/) or personal (~/.claude/commands/)?
- Parameters: What varies between uses?

**Follow-up questions:**
- Success criteria: When is it complete?
- Tools needed: Git, files, APIs, etc.?
- Complexity: Simple or multi-step?
- Reusability: Team-wide? Cross-project?

**Output:** Clear requirements and use cases.

---

### Step 3: Initialize Command Structure

Use the init-command.py script to create command with proper template.

**Usage:**
```bash
python3 scripts/init-command.py <command-name>
```

**Optional path specification:**
```bash
python3 scripts/init-command.py <command-name> --path .claude/commands/
```

**Example:**
```bash
python3 plugin-developer/skills/command-creator/scripts/init-command.py review-pr
```

The script will:
- Validate command name (lowercase-with-hyphens)
- Create command file with proper frontmatter template
- Add TODO markers for customization
- Provide next steps

**Alternative:** Manually create command file with frontmatter.

**Output:** Command file initialized at specified path.

---

### Step 4: Design Command Parameters

Determine what should be parameterized.

**Parameter types:**

**$ARGUMENTS** - Single flexible parameter:
```bash
/fix-issue $ARGUMENTS  # Can be: 123, or "authentication bug"
```

**$1, $2, $3** - Multiple distinct parameters:
```bash
/review-pr $1 $2  # $1=PR number, $2=priority
```

**@file** - File references:
```bash
/optimize @src/components/Header.tsx
```

**Best practices:**
- Set clear `argument-hint` in frontmatter (e.g., `[issue-number]`, `[PR-number] [priority]`)
- Include examples in description
- Consider defaults for optional parameters
- Validate format when critical

**Example command with parameters:**

When building a PR review command for "Review PR 123 with high priority":
```markdown
---
description: Review PR with specified priority
argument-hint: [PR-number] [priority]
---

Review PR #$1 with priority: $2

Priority levels:
- high: Full review (security, performance, architecture)
- medium: Standard review (logic, tests, style)
- low: Quick review (major issues only)

Steps:
1. Fetch PR: gh pr view $1
2. Review files based on $2 priority
3. Check quality, tests, docs
4. Provide structured feedback
```

**Reference:** `references/best-practices.md` section on "Parameter Design" for complete patterns.

**Output:** Clear parameter design.

---

### Step 5: Select Model and Tool Permissions

Choose appropriate model and configure tool access.

**Model selection:**

**claude-3-5-haiku-20241022** (faster, cheaper):
- Simple, well-defined tasks
- Routine workflows (linting, testing, formatting)
- Example: `/lint-fix`, `/run-tests`

**claude-3-7-sonnet-20250219** (default, balanced):
- Standard workflows with moderate complexity
- Most commands fit here
- Example: `/review-pr`, `/fix-issue`

**claude-opus-4-20250514** (most capable, slower):
- Complex problem-solving
- Architectural decisions
- Example: `/design-system`, `/security-audit`

**Recommendation:** Default to Sonnet unless clear reason for Haiku (speed/cost) or Opus (complexity).

**Tool permissions patterns:**
```yaml
# Git operations only
allowed-tools: Bash(git:*)

# Testing commands
allowed-tools: Bash(npm test:*), Read, Glob, Grep

# File operations
allowed-tools: Read, Edit, Write, Glob, Grep

# No restrictions (allow all tools)
# Don't specify allowed-tools field
```

**Best practice:** Be as specific as possible while allowing workflow to function.

**Reference:** `references/best-practices.md` sections on "Model Selection" and "Tool Permissions" for detailed guidance.

**Output:** Model choice and tool configuration.

---

### Step 6: Write Command Content

Create command with proper frontmatter and instructions.

**Frontmatter template:**
```yaml
---
description: Brief, clear explanation (1-2 sentences)
argument-hint: [expected arguments]
allowed-tools: [tool specifications]
model: [model-id if overriding default]
---
```

**Content structure for simple commands (2-4 steps):**
```markdown
---
description: Run all pre-commit checks
allowed-tools: Bash(npm:*)
model: claude-3-5-haiku-20241022
---

Run checks in order:

1. Run pnpm type:check and report TypeScript errors
2. Run pnpm lint and fix auto-fixable issues
3. Run pnpm test and report results
4. Summarize: ✅ if all pass, ❌ if any fail with details
```

**Content structure for workflow commands (5-10 steps):**
```markdown
---
description: Fix GitHub issue following project standards
argument-hint: [issue-number]
allowed-tools: Bash(gh:*), Bash(git:*), Read, Edit
---

Fix issue #$ARGUMENTS:

1. Fetch issue: gh issue view $ARGUMENTS
2. Create branch: git checkout -b fix/$ARGUMENTS/description
3. Read relevant files mentioned in issue
4. Implement fix following coding standards
5. Run tests to verify fix
6. Commit: "fix: resolve issue #$ARGUMENTS"
7. Push and create PR linking to issue

Success criteria:
- Issue fully addressed
- All tests pass
- PR created and linked
```

**Reference:** `references/command-templates.md` for complete template library with examples for all scenarios.

**Output:** Complete command file with frontmatter and instructions.

---

### Step 7: Validate Command

Use validate-command.py script to check structure and quality.

**Usage:**
```bash
python3 scripts/validate-command.py .claude/commands/<command-name>.md
```

**Example:**
```bash
python3 plugin-developer/skills/command-creator/scripts/validate-command.py .claude/commands/review-pr.md
```

The validator checks:
- ✅ YAML frontmatter structure
- ✅ Required fields (description)
- ✅ Tool specification validity
- ✅ Model ID correctness
- ✅ Content structure
- ✅ TODO markers

**Output:** Validation report with errors (must fix) and warnings (should consider).

---

### Step 8: Test and Iterate

Test command immediately (available as soon as saved).

**Testing checklist:**
- ✅ Command appears in `/help` output
- ✅ Arguments parse correctly
- ✅ All steps execute in order
- ✅ Tool permissions allow necessary operations
- ✅ Success and failure cases handled
- ✅ Output is clear and actionable

**Iteration:**
1. Run command with test inputs
2. Observe behavior and results
3. Refine steps, adjust permissions, improve clarity
4. Update command file
5. Test again (changes immediate)

**Discuss reusability:**
- Could this work across projects if more flexible?
- Should parameters be more configurable?
- Is this team-wide value or personal workflow?
- If team-wide, commit to `.claude/commands/` in git

**Output:** Working, tested command ready for use.

---

## Quick Reference

### Command vs CLAUDE.md vs Skill

| Component | When to Use | Invocation | Context |
|-----------|-------------|------------|---------|
| **Command** | Repeated workflow, user-triggered | Explicit: `/command` | Ephemeral |
| **CLAUDE.md** | Project conventions, always relevant | Automatic: always loaded | Persistent |
| **Skill** | Procedural knowledge, Claude decides | Automatic: Claude invokes | On-demand |

### Frontmatter Quick Reference

```yaml
---
description: Brief explanation (shows in /help)   # Required
argument-hint: [expected arguments]               # Optional
allowed-tools: Read, Bash(git:*)                  # Optional (omit for all)
model: claude-3-7-sonnet-20250219                 # Optional (default: sonnet)
---
```

### Model Selection

```yaml
model: claude-3-5-haiku-20241022       # Fast, routine tasks
model: claude-3-7-sonnet-20250219      # Balanced (default)
model: claude-opus-4-20250514          # Complex reasoning
```

### Tool Access Patterns

```yaml
# Git only
allowed-tools: Bash(git:*)

# Testing
allowed-tools: Bash(npm test:*), Read, Grep

# File ops
allowed-tools: Read, Edit, Write, Glob, Grep

# All tools (default)
# Omit allowed-tools field
```

---

## Resources

This skill includes comprehensive references and utilities:

### scripts/

**init-command.py** - Initialize new command with template
- Validates command name (kebab-case)
- Creates command file with proper frontmatter
- Includes TODO markers for customization

**validate-command.py** - Validate command structure
- Checks frontmatter format and required fields
- Validates tool specifications and model ID
- Reports errors (must fix) and warnings (should consider)

### references/

**decision-criteria.md** - Complete decision guide
- Command vs CLAUDE.md decision tree
- Detailed comparison with examples
- Use cases for each approach

**command-templates.md** - Full template library
- Simple Git Workflow
- Multi-Step Testing
- Code Review
- Issue Triage
- And more...

**best-practices.md** - Comprehensive guide
- Writing Effective Commands
- Parameter Design
- Tool Permissions
- Model Selection
- Maintenance

**common-patterns.md** - Proven patterns
- Morning Routine
- Pre-Commit Validation
- PR Preparation
- Common workflow patterns

**troubleshooting.md** - Issues and solutions
- Command Not Appearing
- Permission Errors
- Parameters Not Working
- Model Issues
- Execution Order Issues

**advanced-features.md** - Advanced capabilities
- Bash Command Execution
- File References
- Conditional Logic
- Context from Claude

**integration.md** - Integration patterns
- With CLAUDE.md
- With Hooks
- With Skills
- With Memory

---

## Summary

Create effective Claude Code commands by:

1. **Assess**: Confirm command is appropriate (vs CLAUDE.md)
2. **Gather**: Collect requirements through focused questions
3. **Initialize**: Use init-command.py script
4. **Design**: Plan parameters and structure
5. **Configure**: Select model and tool permissions
6. **Write**: Create command with clear instructions
7. **Validate**: Run validate-command.py
8. **Test**: Iterate based on results

**Key principles:**
- Commands for repeated workflows (not project context)
- Specific tool permissions (principle of least privilege)
- Right model for task (Haiku for simple, Sonnet for most, Opus for complex)
- Clear, numbered steps with success criteria
- Test immediately (available as soon as saved)

Leverage bundled references for detailed guidance on templates, best practices, patterns, troubleshooting, and integration throughout command creation.
