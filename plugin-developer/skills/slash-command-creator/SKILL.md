---
name: slash-command-creator
description: This skill should be used when creating or updating custom slash commands for Claude Code. It guides through the entire lifecycle - from determining if a slash command is appropriate (vs. CLAUDE.md instructions), designing the command structure with proper parameters and frontmatter, selecting the right model and tool permissions, and discussing reusability across projects. Use when the user wants to create a new slash command, convert repeated prompts into commands, or improve existing commands.
---

# Slash Command Creator

## Overview

This skill provides comprehensive guidance for creating effective custom slash commands in Claude Code. It covers when to use slash commands versus CLAUDE.md instructions, command structure design, parameter planning, model selection, tool permissions, and strategies for making commands reusable across projects and teams.

## Workflow Decision Tree

When the user wants to create or improve a prompt workflow, follow this decision tree:

### 1. Assess if a Slash Command is Appropriate

**Use a slash command when:**
- The workflow is repeated frequently (multiple times per week)
- The prompt pattern is reusable across multiple projects or team members
- The task follows a consistent structure that can be parameterized
- Team members would benefit from the same standardized workflow
- The workflow has 2-10 clear, sequential steps
- Examples: debugging loops, testing workflows, PR reviews, log analysis, issue triage

**Use CLAUDE.md instructions instead when:**
- The guidance is project-specific (architectural patterns, conventions, common pitfalls)
- It's general context that should always be available
- The workflow is ad-hoc and doesn't repeat
- The task requires heavy context-specific customization
- Examples: coding standards, project relationships, team preferences, default behaviors

**Key principle:** If you find yourself typing the same instructions in multiple sessions, that's a strong signal for a slash command. If it's always relevant to a specific project, that's CLAUDE.md material.

### 2. Gather Command Requirements

Before creating the command, collect information through conversation:

**Core Questions:**
1. **Purpose**: What specific task or workflow should this command accomplish?
2. **Concrete examples**: Can you provide 2-3 examples of exactly how you'd use this command?
3. **Frequency**: How often do you perform this task? (daily, weekly, per-project)
4. **Scope**: Should this be project-specific (.claude/commands/) or personal (~/.claude/commands/)?
5. **Parameters**: What varies between uses? (issue numbers, file paths, priorities, etc.)

**Follow-up Questions:**
1. **Success criteria**: How do you know when this task is complete?
2. **Tools needed**: Will this require git operations, file modifications, API calls, etc.?
3. **Complexity**: Is this a simple prompt or a multi-step workflow?
4. **Reusability**: Could others on your team use this? Could it work across different projects?

Avoid overwhelming the user - ask 2-3 questions at a time and iterate based on responses.

### 3. Design the Command Structure

Based on gathered requirements, design the command with these components:

#### Command Name and Location

**Naming conventions:**
- Use lowercase with hyphens: `review-pr`, `fix-issue`, `test-all`
- Be specific and action-oriented: `analyze-logs` not `logs`
- Keep it short: ideally 2-3 words maximum

**Location:**
- `.claude/commands/` for project-specific, team-shared commands
- `~/.claude/commands/` for personal commands across all projects
- Subdirectories for organization: `.claude/commands/testing/`, `.claude/commands/git/`

#### Parameter Design

Determine what should be parameterized:

**Use $ARGUMENTS for:**
- Single flexible parameter that users provide freely
- Example: `/fix-issue $ARGUMENTS` → `/fix-issue 123` or `/fix-issue authentication bug`

**Use positional arguments ($1, $2, $3) for:**
- Multiple distinct parameters
- When accessing individual parameters in different sections
- When providing defaults or validation
- Example: `/review-pr $1 $2` where $1 is PR number and $2 is priority level

**Use @file references for:**
- Commands that operate on specific files
- Example: `/optimize-component @src/components/Header.tsx`

**Parameter best practices:**
- Provide clear `argument-hint` in frontmatter (e.g., `[issue-number]`, `[PR-number] [priority]`)
- Include examples in command description
- Consider defaults for optional parameters
- Validate parameter format when critical

### 4. Select Model and Configuration

Choose the appropriate model based on command complexity and discuss with the user:

#### Model Selection

Present options and ask for user preference:

**claude-3-5-haiku-20241022** (faster, cheaper):
- Simple, well-defined tasks with clear steps
- Routine workflows (linting, testing, formatting)
- Commands with explicit instructions
- Tasks requiring speed over deep reasoning
- Example commands: `/lint-fix`, `/run-tests`, `/format-code`

**claude-3-7-sonnet-20250219** (default, balanced):
- Standard workflows requiring moderate complexity
- Multi-step tasks with some decision-making
- Most custom commands fit here
- Good balance of speed and capability
- Example commands: `/review-pr`, `/fix-issue`, `/refactor-component`

**claude-opus-4-20250514** (most capable, slower):
- Complex problem-solving requiring deep analysis
- Tasks needing architectural decisions
- Novel or ambiguous situations
- Research and exploration tasks
- Example commands: `/design-system`, `/investigate-bug`, `/security-audit`

**Recommendation:** Default to Sonnet unless there's a clear reason for Haiku (speed/cost for simple tasks) or Opus (complexity requires highest capability). Discuss with the user based on their use case.

#### Tool Permissions

Determine which tools the command needs access to:

**Common patterns:**

```yaml
# Git operations only
allowed-tools: Bash(git:*)

# Specific git commands
allowed-tools: Bash(git status:*), Bash(git add:*), Bash(git commit:*)

# Testing commands
allowed-tools: Bash(npm test:*), Bash(pytest:*), Read, Glob, Grep

# File operations
allowed-tools: Read, Edit, Write, Glob, Grep

# No restrictions (allow all tools)
# Don't specify allowed-tools field
```

**Best practice:** Be as specific as possible while allowing the workflow to function. This prevents unintended actions and makes the command's scope clear.

### 5. Create Command File

Generate the complete command file with proper frontmatter and content:

#### Frontmatter Template

```yaml
---
description: Brief, clear explanation of what this command does
allowed-tools: [tool specifications if needed]
argument-hint: [expected arguments for auto-completion]
model: [model-id if overriding default]
disable-model-invocation: false
---
```

**Frontmatter fields:**

- `description`: Shows in `/help`, be concise but informative (1-2 sentences)
- `allowed-tools`: Specifies which tools Claude can use (optional, see patterns above)
- `argument-hint`: User-facing hint for what arguments to provide (e.g., `[issue-number]`, `[file-path]`)
- `model`: Override default model if needed (haiku for simple, opus for complex)
- `disable-model-invocation`: Set to `true` to prevent Claude from auto-invoking via SlashCommand tool

#### Command Content Structure

**For simple commands (2-4 steps):**

```markdown
---
description: Run all pre-commit checks (types, lint, tests)
allowed-tools: Bash(npm:*), Bash(pnpm:*)
model: claude-3-5-haiku-20241022
---

Run the following checks in order:

1. Run pnpm type:check and report any TypeScript errors
2. Run pnpm lint and fix any auto-fixable issues
3. Run pnpm test and report test results
4. Summarize overall status: ✅ if all pass, ❌ if any fail with details
```

**For workflow commands (5-10 steps):**

```markdown
---
description: Fix GitHub issue following project standards
argument-hint: [issue-number]
allowed-tools: Bash(gh:*), Bash(git:*), Read, Edit, TodoWrite
---

Fix GitHub issue #$ARGUMENTS following these steps:

1. Fetch issue details using gh issue view $ARGUMENTS
2. Create a feature branch: git checkout -b fix/$ARGUMENTS/description
3. Create a todo list with: understanding issue, implementing fix, testing, creating PR
4. Read relevant files mentioned in the issue
5. Implement the fix following project coding standards
6. Run tests to verify the fix works
7. Commit changes with message: "fix: resolve issue #$ARGUMENTS"
8. Push branch and create PR linking to issue #$ARGUMENTS

Success criteria:
- Issue description is fully addressed
- All tests pass
- PR is created and linked to issue
```

**For complex commands with multiple parameters:**

```markdown
---
description: Review PR with specified priority and optional reviewer assignment
argument-hint: [PR-number] [priority] [reviewer]
allowed-tools: Bash(gh:*), Read, Grep, Glob
---

Review PR #$1 with priority level: $2 (reviewer: ${3:-unassigned})

Priority levels:
- high: Full review including security, performance, architecture
- medium: Standard review of logic, tests, and style
- low: Quick review of major issues only

Steps:

1. Fetch PR details: gh pr view $1
2. Review changed files based on priority level
3. Check for: code quality, test coverage, documentation
4. If priority is "high", also check: security issues, performance implications
5. Provide structured feedback with specific file:line references
6. If $3 is provided and not "unassigned", suggest assigning reviewer
```

**For commands with bash execution:**

```markdown
---
description: Analyze application logs for errors and patterns
allowed-tools: Bash(tail:*), Bash(grep:*), Bash(awk:*)
argument-hint: [log-file-path]
---

Analyze logs in $ARGUMENTS:

# Execute bash commands (prefix with !)
!tail -100 $ARGUMENTS > /tmp/recent_logs.txt
!grep -i "error\|warning\|exception" $ARGUMENTS | wc -l

Steps:

1. Show last 100 log entries
2. Count total errors, warnings, and exceptions
3. Identify patterns (recurring errors, time-based issues)
4. Group by severity and frequency
5. Provide recommendations for investigation

Note: Bash commands with ! prefix are executed automatically.
```

### 6. Discuss Reusability and Generalization

After designing the command, have a conversation with the user about making it more reusable:

**Questions to explore:**

1. **Cross-project applicability**: "This command is designed for [current project]. Could it be useful in other projects if we made [specific aspect] more flexible?"

2. **Parameter flexibility**: "Currently this assumes [specific assumption]. Would it be more useful if users could specify [parameter] as an argument?"

3. **Scope expansion**: "This handles [current case]. Are there related scenarios where a similar command with variations would be useful?"

4. **Team vs. personal**: "Is this something your team would benefit from, or is it specific to your workflow? If team-wide, should we add it to .claude/commands/ and commit it?"

5. **Conventions and standards**: "This references [specific standard/tool/pattern]. Is that consistent across your projects, or should we make it configurable?"

**Reusability strategies:**

- **Parameterize specifics**: Project names, repo paths, tool commands as arguments
- **Support multiple tools**: Check for npm/pnpm/yarn availability
- **Conditional behavior**: "If production, run security scan; if development, skip"
- **Clear documentation**: Include examples of different use cases in command description
- **Defaults with overrides**: Sensible defaults that can be overridden with parameters

**Example transformation:**

Original (project-specific):
```markdown
Run pnpm type:check && pnpm lint && pnpm test
```

Generalized (cross-project):
```markdown
# Detect package manager
!command -v pnpm >/dev/null 2>&1 && echo "pnpm" || (command -v npm >/dev/null 2>&1 && echo "npm" || echo "yarn")

Run checks using detected package manager:
1. Type checking
2. Linting
3. Testing
```

### 7. Create and Test the Command

After finalizing design:

1. **Write the command file** at the appropriate location
2. **Test immediately**: The command is available as soon as the file is created
3. **Iterate based on results**: Refine steps, adjust tool permissions, improve clarity
4. **Document edge cases**: Update command if you discover missing scenarios

**Testing checklist:**
- ✅ Command appears in `/help` output
- ✅ Arguments are parsed correctly
- ✅ All steps execute in order
- ✅ Tool permissions allow necessary operations
- ✅ Success and failure cases both handled
- ✅ Output is clear and actionable

## Command Templates Library

Use these templates as starting points:

### Template: Simple Git Workflow

```markdown
---
description: Create feature branch and initial commit for new feature
argument-hint: [feature-name]
allowed-tools: Bash(git:*)
---

Set up new feature: $ARGUMENTS

1. Create branch: git checkout -b feature/$ARGUMENTS
2. Create initial commit: git commit --allow-empty -m "feat: initialize $ARGUMENTS"
3. Show status: git status
```

### Template: Multi-Step Testing

```markdown
---
description: Run comprehensive test suite with coverage
allowed-tools: Bash(npm:*), Bash(pytest:*), Read
model: claude-3-5-haiku-20241022
---

Run comprehensive tests:

1. Unit tests: npm test
2. Integration tests: npm run test:integration
3. Coverage report: npm run test:coverage
4. Analyze coverage and report gaps
5. Suggest areas needing more tests
```

### Template: Code Review

```markdown
---
description: Review code changes in current branch vs main
allowed-tools: Bash(git:*), Read, Grep
---

Review current branch changes:

1. Show changed files: git diff main...HEAD --name-only
2. Review each changed file for:
   - Code quality and clarity
   - Potential bugs or edge cases
   - Test coverage
   - Documentation needs
3. Check for common issues:
   - Hardcoded values
   - Missing error handling
   - Performance concerns
4. Provide actionable feedback with file:line references
```

### Template: Issue Triage

```markdown
---
description: Analyze and categorize GitHub issue with reproduction steps
argument-hint: [issue-number]
allowed-tools: Bash(gh:*), Read, Grep, Glob
---

Triage issue #$ARGUMENTS:

1. Fetch issue: gh issue view $ARGUMENTS
2. Analyze description for:
   - Clear reproduction steps (✅/❌)
   - Expected vs actual behavior
   - Environment details
   - Error messages
3. Search codebase for related code
4. Categorize: bug/feature/documentation/question
5. Suggest priority: critical/high/medium/low
6. Recommend label additions
7. Draft initial response or questions if info is missing
```

## Best Practices

### Writing Effective Commands

1. **Be specific in steps**: "Run npm test and report failures" not "test the code"
2. **Include success criteria**: Define what "done" looks like
3. **Number your steps**: Makes execution order clear
4. **Use active voice**: "Review files" not "Files should be reviewed"
5. **Keep it concise**: Under 10 steps for main workflow (sub-steps are fine)
6. **Provide context**: Explain *why* certain steps matter when non-obvious

### Parameter Design

1. **Clear naming**: `$1` should have obvious meaning from context or argument-hint
2. **Document expectations**: "issue-number", "file-path", "priority-level"
3. **Handle missing parameters**: Provide defaults or clear error messages
4. **Examples in description**: Show concrete usage in the description field

### Tool Permissions

1. **Principle of least privilege**: Only grant necessary tools
2. **Be specific**: `Bash(git status:*)` not `Bash(git:*)` if only status is needed
3. **Test permissions**: Verify the command can execute all steps
4. **Document reasoning**: Comment why specific tools are needed if non-obvious

### Model Selection

1. **Default to Sonnet**: Unless there's a clear reason otherwise
2. **Use Haiku for**: Well-defined, routine tasks (testing, linting, formatting)
3. **Use Opus for**: Novel problems, architecture, complex debugging
4. **Discuss with user**: Ask about complexity expectations

### Maintenance

1. **Version control**: Commit .claude/commands/ for team sharing
2. **Document changes**: Update description when modifying commands
3. **Gather feedback**: Ask team members how commands work in practice
4. **Iterate regularly**: Refine based on actual usage patterns
5. **Archive unused**: Remove or disable commands that don't get used

## Common Patterns

### Pattern: Morning Routine

```markdown
---
description: Daily project setup and status check
---

Morning routine:

1. git pull origin main
2. Check for dependency updates
3. Run test suite to verify clean state
4. Review open PRs assigned to you
5. Check recent issues for urgent items
6. Summarize what needs attention today
```

### Pattern: Pre-Commit Validation

```markdown
---
description: Validate changes before committing
allowed-tools: Bash(git:*), Bash(npm:*), Read
model: claude-3-5-haiku-20241022
---

Pre-commit validation:

1. Show staged changes: git diff --cached
2. Run type check
3. Run linter
4. Run relevant tests
5. Check for TODOs or FIXMEs being committed
6. Verify no console.logs or debugger statements
7. Confirm all checks pass before commit
```

### Pattern: PR Preparation

```markdown
---
description: Prepare branch for PR submission
allowed-tools: Bash(git:*), Bash(gh:*), Read, TodoWrite
---

Prepare PR:

1. Ensure branch is up to date with main
2. Run full test suite
3. Review all changed files one more time
4. Draft PR description summarizing changes
5. List testing done and remaining TODOs
6. Check for breaking changes that need documentation
7. Create PR with template: gh pr create --web
```

## Troubleshooting

### Command Not Appearing

- Check file is in correct directory (.claude/commands/ or ~/.claude/commands/)
- Verify file has .md extension
- Check YAML frontmatter is valid (use `---` delimiters)
- Restart Claude Code if necessary

### Permission Errors

- Verify `allowed-tools` includes necessary tools
- Check specific command patterns (e.g., `Bash(git:*)` for all git commands)
- Test with fewer restrictions first, then narrow down
- Check user's `/permissions` settings aren't blocking

### Parameters Not Working

- Verify using `$ARGUMENTS` or `$1, $2, $3` syntax
- Check `argument-hint` matches actual usage
- Test with concrete examples
- Ensure no typos in variable references

### Model Issues

- Verify model ID is correct and available
- Check if task complexity matches model capability
- Consider removing `model:` field to use default
- Test with different models to compare results

### Execution Order Issues

- Number steps clearly (1, 2, 3...)
- Use sequential dependencies: "After step X completes, run Y"
- For bash commands, ensure they're properly marked with `!` prefix
- Check if parallel execution is causing race conditions

## Advanced Features

### Bash Command Execution

Commands can include bash commands that execute automatically when the command runs:

```markdown
---
allowed-tools: Bash(date:*), Bash(git:*)
---

# These execute when command runs
!date
!git log -1 --oneline

Then analyze the output above...
```

### File References

Commands can reference files using @ prefix:

```markdown
Review the implementation in @src/utils/helpers.js and @tests/utils.test.js
```

### Conditional Logic

Include conditional behavior based on context:

```markdown
1. Check current branch: git branch --show-current
2. If on main/master, warn about committing directly
3. If on feature branch, proceed with commit
4. If on release branch, require additional validation
```

### Context from Claude

Commands can ask Claude to determine information:

```markdown
1. Analyze the current codebase to identify test framework
2. Run tests using detected framework
3. Parse results based on framework output format
```

## Integration with Other Features

### With CLAUDE.md

- Use CLAUDE.md for project-wide conventions
- Use slash commands for specific workflows
- Reference CLAUDE.md standards in commands: "Follow coding standards in CLAUDE.md"

### With Hooks

- Pre-prompt hooks can inject context before command runs
- Tool-call hooks can intercept command tool usage
- User-submit hooks can validate command inputs

### With Skills

- Commands are for manual invocation by user
- Skills are for automatic discovery by Claude
- Commands can reference skills: "Use the pdf skill to process..."
- Skills can suggest related commands in their documentation

### With Memory

- Commands can reference memory: "Following preferences from memory..."
- Memory can store command preferences: "Always use priority=high for PR reviews"

## Skill Usage by Claude

When Claude needs to help users create slash commands, Claude should:

1. **Start with the decision tree**: Determine if a slash command is appropriate
2. **Gather requirements**: Ask questions from "Gather Command Requirements" section
3. **Design structure**: Use templates and patterns from this skill
4. **Discuss model selection**: Present options and help user choose
5. **Configure permissions**: Identify necessary tools based on workflow
6. **Create the command**: Write complete command file with all components
7. **Explore reusability**: Discuss generalization opportunities
8. **Test together**: Run the command and iterate based on results

The goal is a collaborative process where the user's domain knowledge combines with Claude's understanding of command structure and best practices to create effective, reusable commands.
