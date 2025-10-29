---
name: git-operations
description: Performs git operations with safety checks - commit, push, force-push. Enforces Git Safety Protocol and supports styleable commit messages via CLAUDE.md configuration. Use when you need to create commits or push changes.
allowed_tools:
  - Bash(./.claude/skills/git-operations/git-ops.zsh commit *)
  - Bash(./.claude/skills/git-operations/git-ops.zsh push *)
  - Bash(git status)
  - Bash(git diff *)
  - Bash(git log *)
  - Read(*/CLAUDE.md)
  - Read(*/CLAUDE.local.md)
---

# Git Operations Skill

Safe git operations with styleable commit messages and branch protection.

## Overview

This skill provides secure git operations for commit and push workflows. It enforces the Git Safety Protocol, supports configurable commit message styles, and prevents dangerous operations like force-pushing to protected branches.

**Key features**:
- Styleable commit messages (conventional, pirate, snarky, emoji, minimal, corporate)
- Attribution filtering based on CLAUDE.md configuration
- Pre-commit hook handling with auto-amend logic
- Branch protection (prevents force-push to main/master)
- Single entry point for encapsulation

## When to Use This Skill

Use this skill when you need to:
- Create commits with proper formatting
- Push changes with safety checks
- Force-push to feature branches (blocked on main/master)
- Handle pre-commit hooks that modify files
- Apply consistent commit message styling

**For agents/orchestrators**: Invoke this skill via Claude Code, not by calling scripts directly.

## Commit Message Processing

When creating commits, this skill:

1. **Reads commit style from CLAUDE.md/CLAUDE.local.md**:
   - Look for "Commit style: [style-name]"
   - Look for "Commit attribution: [none|claude|custom]"
   - Project-level CLAUDE.local.md overrides global CLAUDE.md

2. **Filters attribution based on configuration**:
   - If "Commit attribution: none" (or not specified): Remove footers like:
     - "Generated with [Claude Code]..."
     - "Co-Authored-By: Claude <noreply@anthropic.com>"
   - If "Commit attribution: claude": Keep attribution
   - If "Commit attribution: custom": Use custom attribution from CLAUDE.md

3. **Applies commit style**:
   - Use style library from references/commit-styles.md
   - Default to "conventional" if no style specified
   - Validate structure based on chosen style

**Style Selection Priority**:
1. CLAUDE.local.md "Commit style:" (project-specific)
2. CLAUDE.md "Commit style:" (user-wide)
3. Default: "conventional"

**Attribution Selection Priority**:
1. CLAUDE.local.md "Commit attribution:"
2. CLAUDE.md "Commit attribution:"
3. Default: "none"

## Usage

### Commands

**Commit**:
```bash
# Basic commit
git-ops.zsh commit --message "feat: add user authentication"

# Commit with scope
git-ops.zsh commit --message "fix(api): handle null pointer"

# Allow empty commit
git-ops.zsh commit --message "chore: trigger CI" --allow-empty

# Dry run (show what would be committed)
git-ops.zsh commit --message "feat: new feature" --dry-run
```

**Push**:
```bash
# Push current branch
git-ops.zsh push

# Force push to feature branch (blocked on main/master)
git-ops.zsh push --force

# Create upstream if missing
git-ops.zsh push --set-upstream

# Dry run (show what would be pushed)
git-ops.zsh push --dry-run
```

### For Claude Code (Skill Invocation)

When you need to create commits or push changes, invoke this skill. The skill will:
1. Read commit style preferences from CLAUDE.md
2. Validate and format the commit message
3. Handle pre-commit hooks safely
4. Create the commit or push with appropriate safety checks

### For Agents/Orchestrators

This skill is invoked by Claude Code, not called directly from other scripts.

**Example workflow**:
1. ticket-manager creates worktree
2. User makes changes
3. Claude Code invokes git-operations skill
4. git-operations reads CLAUDE.md for style/attribution
5. Creates commit with appropriate style

**Do NOT** call `.claude/skills/git-operations/git-ops.zsh` directly from other skills.

## Commit Styles

See `references/commit-styles.md` for complete style library.

**Built-in styles**:
- `conventional` - Standard (feat:, fix:, docs:, etc.) - DEFAULT
- `pirate` - "Arr! Plundered the bug in authentication"
- `snarky` - "Obviously the login needed fixing"
- `emoji` - "✨ feat: shiny new feature"
- `minimal` - Just the message, no prefixes
- `corporate` - "[PROJ-123] Feature: Implemented per specification"

### Configuration

**In CLAUDE.md (user-wide)**:
```markdown
Commit style: pirate
Commit attribution: none
```

**In CLAUDE.local.md (project-specific, overrides CLAUDE.md)**:
```markdown
Commit style: conventional
Commit attribution: none
```

### Examples

**Default (conventional, no attribution)**:
```
feat: add user authentication
fix(api): handle null response
docs: update README with examples
```

**Pirate style**:
```
Arr! Hoisted the new feature: user authentication
Arr! Plundered the bug in: API null handling
Arr! Scribed the scrolls for: README updates
```

**Emoji style**:
```
✨ feat: add user authentication
🐛 fix: handle null response
📝 docs: update README
```

**Minimal style**:
```
add user authentication
fix API null handling
update README
```

## Git Safety Protocol

This skill enforces strict safety rules:

### NEVER
- Update git config (unless explicitly requested by user)
- Force-push to main/master branches
- Skip hooks (--no-verify) unless explicitly requested
- Amend commits that:
  - Were created by another author
  - Have been pushed to remote

### ALWAYS
- Check authorship before amending
- Verify commit hasn't been pushed before amending
- Warn before force-pushing (even to feature branches)

### Pre-Commit Hook Handling

When pre-commit hooks modify files:

1. Check authorship: `git log -1 --format='%an %ae'`
2. Check not pushed: `git status` shows "ahead"
3. If both true: `git commit --amend --no-edit` (safe)
4. If false: Create new commit for hook changes (not safe to amend)

**Decision tree**:
```
Hook modified files?
├─ No → Done
└─ Yes → Is commit by current user?
    ├─ No → Create new commit
    └─ Yes → Has commit been pushed?
        ├─ Yes → Create new commit
        └─ No → Amend commit (safe)
```

### Branch Protection

**Protected branches**: `main`, `master`

**Rules**:
- ❌ Never allow force-push to protected branches
- ✅ Allow force-push to feature branches with --force flag
- ⚠️  Warn before force-pushing

## Configuration Examples

### Example 1: Default (Conventional + No Attribution)

No configuration needed - this is the default.

**Result**:
```
feat: add feature
```

### Example 2: Pirate Mode

```markdown
# CLAUDE.md
Commit style: pirate
Commit attribution: none
```

**Result**:
```
Arr! Hoisted the new feature: user auth
```

### Example 3: Corporate with Attribution

```markdown
# CLAUDE.md
Commit style: corporate
Commit attribution: claude
```

**Result**:
```
[PROJ-123] Feature: Implement user authentication

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Example 4: Project Override

```markdown
# ~/CLAUDE.md (user-wide)
Commit style: pirate
Commit attribution: none

# ~/project/CLAUDE.local.md (project-specific - wins)
Commit style: conventional
Commit attribution: none
```

**Result**: Project uses conventional style (overrides pirate)

## Error Handling

The skill returns clear error messages and exit codes:

- Exit 0: Success
- Exit 1: Validation error (invalid message format, protected branch, etc.)
- Exit 2: Git error (nothing to commit, no upstream, etc.)

**Example errors**:
```
❌ ERROR: Invalid commit message for style: conventional
Expected format: type(scope?): message

❌ ERROR: Force push to protected branch 'main' is not allowed

⚠️  Branch has no upstream. Use --set-upstream to create it.
```

## References

- `references/commit-styles.md` - Complete style library and transformations
- `references/safety-protocol.md` - Detailed Git Safety Protocol documentation

## Integration with Other Skills

### ticket-manager

**ticket-manager DOES NOT call git-ops.zsh directly**

Instead, ticket-manager's SKILL.md says:
```markdown
After creating worktree and fetching ticket data, inform Claude Code:
"Workspace ready. When user makes changes, use the git-operations skill to commit."
```

### Communication Flow

```
User → Claude Code
  ↓
  Invokes: ticket-manager skill
    Creates worktree
    Informs: "Workspace ready, use git-operations for commits"
  ↓
  User makes changes
  ↓
  Claude Code invokes: git-operations skill
    Reads CLAUDE.md for style/attribution
    Creates styled commit
    Handles hooks safely
```

## Testing

Test the skill with different configurations:

1. **Style detection**: Set different styles in CLAUDE.md, verify applied
2. **Attribution filtering**: Set "none", verify no attribution footer
3. **Hook handling**: Create pre-commit hook that modifies file, verify amend logic
4. **Branch protection**: Try force-push to main (should fail)
5. **Conventional validation**: Try invalid format, verify rejection

**Test commands**:
```bash
# Test commit with conventional style
git-ops.zsh commit --message "feat: test feature"

# Test invalid conventional format (should fail)
git-ops.zsh commit --message "added feature"

# Test force-push protection on main
git checkout main
git-ops.zsh push --force  # Should fail

# Test force-push on feature branch
git checkout feature/test
git-ops.zsh push --force  # Should succeed with warning
```

## Troubleshooting

### "Invalid commit message for style: conventional"

Your message doesn't match the conventional commit format.

**Fix**: Use format `type(scope?): message`

Valid types: feat, fix, docs, refactor, test, chore, perf, style

### "Force push to protected branch 'X' is not allowed"

You tried to force-push to main or master.

**Fix**: Never force-push to protected branches. For feature branches, this is allowed.

### "Branch has no upstream"

Your branch doesn't have a remote tracking branch.

**Fix**: Use `--set-upstream` flag: `git-ops.zsh push --set-upstream`

### Hook modified files but commit wasn't amended

The commit either:
- Was created by another author, or
- Has already been pushed

**Fix**: This is safe behavior - a new commit was created for hook changes instead of amending.
