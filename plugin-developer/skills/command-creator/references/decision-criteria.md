# Slash Commands vs. CLAUDE.md: Decision Criteria

## Quick Decision Matrix

| Factor | Slash Command | CLAUDE.md |
|--------|---------------|-----------|
| **Frequency** | Used multiple times per week | Always relevant |
| **Scope** | Specific workflow with clear steps | General guidelines & context |
| **Trigger** | User manually invokes | Auto-loaded for all sessions |
| **Parameterization** | Variable inputs (issue #, files) | Fixed conventions |
| **Team usage** | Specific repeatable tasks | Project-wide standards |
| **Length** | 2-10 steps | Any length |

## When Slash Commands Shine

### ✅ Perfect Use Cases

**Debugging Workflows**
```markdown
/debug-production [service-name]
1. Check service logs
2. Verify database connections
3. Review recent deployments
4. Analyze error patterns
```

**Testing Routines**
```markdown
/test-all
1. Run unit tests
2. Run integration tests
3. Check coverage
4. Report results
```

**PR & Issue Management**
```markdown
/review-pr [number]
/fix-issue [number]
/triage-issue [number]
```

**Code Generation**
```markdown
/create-component [name]
/add-api-endpoint [path]
/generate-migration [description]
```

### ❌ Wrong Use Cases (Use CLAUDE.md Instead)

**Project Conventions**
```markdown
❌ /coding-standards
✅ Add to CLAUDE.md:
   - Use camelCase for variables
   - Prefer functional components
   - Follow ESLint config
```

**Architecture Patterns**
```markdown
❌ /explain-architecture
✅ Add to CLAUDE.md:
   - API layer structure
   - State management approach
   - Database relationships
```

**Always-On Context**
```markdown
❌ /project-context
✅ Add to CLAUDE.md:
   - Tech stack overview
   - Common pitfalls
   - Team preferences
```

## Hybrid Approach: Using Both

Many teams benefit from combining both approaches:

**CLAUDE.md** (Project Context)
```markdown
## Coding Standards
- Use TypeScript strict mode
- Follow Airbnb style guide
- Write tests for all new features

## Architecture
- Frontend: React + Redux
- Backend: Node.js + Express
- Database: PostgreSQL

## Common Workflows
- Testing: Use /test-all command
- PRs: Use /review-pr command before submitting
- Issues: Use /fix-issue command for bug fixes
```

**Slash Commands** (Specific Workflows)
```
.claude/commands/test-all.md
.claude/commands/review-pr.md
.claude/commands/fix-issue.md
```

This approach gives Claude always-on context while providing repeatable workflows.

## Red Flags: Wrong Tool Choice

### Signs You Should Use a Slash Command

1. **Copy-paste pattern**: You keep pasting the same instructions
2. **Manual invocation**: You want to trigger it only when needed
3. **Parameterized**: Different values each time (IDs, names, paths)
4. **Multiple steps**: Clear sequential workflow
5. **Optional workflow**: Not every session needs this

### Signs You Should Use CLAUDE.md

1. **Always relevant**: Every conversation should know this
2. **Project-specific**: Unique to this codebase
3. **Conventions**: How we do things here
4. **No clear trigger**: Not a "run this now" workflow
5. **Context layer**: Background knowledge vs. action steps

## Evolution Strategy

Start with CLAUDE.md, migrate to slash commands as patterns emerge:

**Phase 1: Discovery (Week 1-2)**
```markdown
# CLAUDE.md
When fixing bugs:
1. Check logs
2. Write failing test
3. Fix code
4. Verify test passes
```

**Phase 2: Pattern Recognition (Week 3-4)**
- Notice you're using this workflow 3+ times per week
- Realize it could be parameterized (bug ID, component name)
- Identify that teammates would benefit

**Phase 3: Extraction (Week 5+)**
```markdown
# .claude/commands/fix-bug.md
---
description: Debug and fix bug with test-driven approach
argument-hint: [bug-id]
---

Fix bug #$ARGUMENTS:
1. Fetch bug details: gh issue view $ARGUMENTS
2. Check relevant logs
3. Write failing test reproducing bug
4. Implement fix
5. Verify test passes
6. Create PR linking to bug
```

Update CLAUDE.md to reference:
```markdown
## Bug Fixing
Use the /fix-bug [id] command for systematic bug resolution.
```

## Model Selection Guidance

Different commands need different models based on complexity:

### Haiku (Fast & Cheap)
- Well-defined, routine tasks
- Clear success criteria
- Minimal decision-making
```
/lint-fix
/format-code
/run-tests
```

### Sonnet (Default Balance)
- Standard workflows
- Moderate complexity
- Some judgment needed
```
/review-pr
/fix-issue
/refactor-component
```

### Opus (Complex & Novel)
- Architecture decisions
- Novel problems
- Deep analysis
```
/design-system
/investigate-outage
/security-audit
```

## Team Sharing Strategies

### Project Commands (.claude/commands/)
```
.claude/commands/
├── git/
│   ├── review-pr.md
│   └── prepare-release.md
├── testing/
│   ├── test-all.md
│   └── coverage-report.md
└── debugging/
    ├── analyze-logs.md
    └── check-production.md
```

Commit to git for team sharing.

### Personal Commands (~/.claude/commands/)
```
~/.claude/commands/
├── daily-standup.md
├── time-tracking.md
└── personal-notes.md
```

Available across all projects, not committed to git.

## Tool Permissions Best Practices

Principle of least privilege - grant only what's needed:

```yaml
# Too broad ❌
allowed-tools: Bash(*), Read, Edit, Write, Glob, Grep

# Too restrictive ❌
allowed-tools: Bash(git status:*)
# Breaks if command needs git diff or git log

# Just right ✅
allowed-tools: Bash(git:*), Read, Grep
# Allows all git operations, file reading, searching
```

## Common Patterns Library

### Pattern: Morning Routine
```markdown
# Personal command (~/.claude/commands/)
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

### Pattern: Pre-Commit Checks
```markdown
# Project command (.claude/commands/)
---
description: Validate changes before committing
allowed-tools: Bash(git:*), Bash(npm:*)
model: claude-3-5-haiku-20241022
---

Pre-commit validation:
1. Show staged changes: git diff --cached
2. Run type check
3. Run linter
4. Run relevant tests
5. Check for TODOs or FIXMEs
6. Verify no console.logs or debugger statements
7. Report status: ✅ or ❌ with details
```

### Pattern: Issue Triage
```markdown
# Project command (.claude/commands/)
---
description: Analyze and categorize GitHub issue
argument-hint: [issue-number]
allowed-tools: Bash(gh:*), Read, Grep, Glob
---

Triage issue #$ARGUMENTS:
1. Fetch issue: gh issue view $ARGUMENTS
2. Analyze for clarity and completeness
3. Search codebase for related code
4. Categorize: bug/feature/docs/question
5. Suggest priority: critical/high/medium/low
6. Recommend labels
7. Draft response if more info needed
```

## Troubleshooting Decision Paralysis

**"Should this be a slash command or CLAUDE.md?"**

Ask yourself:
1. Will I manually trigger this? → Slash command
2. Should Claude always know this? → CLAUDE.md
3. Does it have clear steps? → Slash command
4. Is it project context? → CLAUDE.md
5. Can it be parameterized? → Slash command

**When in doubt:**
- Start with CLAUDE.md (easier to refactor later)
- Extract to slash command when you use it 3+ times
- You can always move content between them

## Real-World Examples

### Example 1: TypeScript Project

**CLAUDE.md:**
```markdown
## Project Context
- TypeScript with strict mode
- React + Redux for state
- Jest for testing
- Follow Airbnb style guide

## Common Pitfalls
- Always type Redux actions
- Avoid default exports except for pages
- Use React.FC for components

## Workflows
- Use /test-component for component testing
- Use /review-pr before submitting PRs
```

**Slash Commands:**
```
.claude/commands/test-component.md
.claude/commands/review-pr.md
.claude/commands/add-redux-slice.md
```

### Example 2: Monorepo

**CLAUDE.md:**
```markdown
## Monorepo Structure
- packages/frontend - React app
- packages/backend - Express API
- packages/shared - Shared types & utils

## Conventions
- Changes to shared require version bump
- Run tests in affected packages only
- Update root changelog for releases

## Workflows
- Use /test-affected to test changed packages
- Use /release-package for publishing
```

**Slash Commands:**
```
.claude/commands/test-affected.md
.claude/commands/release-package.md
.claude/commands/add-shared-util.md
```

## Further Resources

- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code/slash-commands
- **Best Practices**: https://www.anthropic.com/engineering/claude-code-best-practices
- **Community Examples**: https://github.com/hesreallyhim/awesome-claude-code
