# Git Safety Protocol

This document describes the safety rules and protocols enforced by the git-operations skill.

## Core Safety Rules

### NEVER

The skill will NEVER do the following operations:

1. **Update git config** (unless explicitly requested by user)
   - Never modify `user.name`, `user.email`, or other config values
   - Config changes must be done manually by the user

2. **Run destructive/irreversible git commands**
   - No `git reset --hard` (unless explicitly requested)
   - No `git clean -fd` (unless explicitly requested)
   - No `git push --force` to main/master branches (always blocked)

3. **Skip hooks**
   - Never use `--no-verify` flag (unless explicitly requested)
   - Never use `--no-gpg-sign` flag (unless explicitly requested)
   - Hooks are there for a reason - respect them

4. **Force-push to protected branches**
   - main and master are protected
   - Force-push to these branches is ALWAYS blocked
   - No exceptions, no warnings, just blocked

5. **Amend commits that shouldn't be amended**
   - Never amend commits created by another author
   - Never amend commits that have been pushed to remote
   - See "Amend Safety Checks" below for details

### ALWAYS

The skill will ALWAYS do the following:

1. **Check authorship before amending**
   - Verify last commit was created by current user
   - Command: `git log -1 --format='%an %ae'`
   - Compare with `git config user.name` and `git config user.email`

2. **Verify commit hasn't been pushed**
   - Check branch tracking status
   - Command: `git status` shows "ahead"
   - Only amend if commit is local-only

3. **Warn before force-pushing**
   - Even on feature branches, show warning
   - Use `--force-with-lease` instead of `--force`
   - Prevents accidental overwrites

4. **Validate commit messages**
   - Check format matches selected style
   - Reject invalid messages with clear error
   - Provide examples of correct format

5. **Respect CLAUDE.md configuration**
   - Always read style and attribution settings
   - Never override user preferences
   - Project CLAUDE.local.md takes precedence

---

## Pre-Commit Hook Handling

### The Problem

Pre-commit hooks (like formatters or linters) often modify files during commit. This creates a situation where:
1. You create a commit
2. Hook runs and modifies files
3. Working directory is now "dirty" again
4. The modifications aren't in the commit

### The Solution: Smart Amend

The skill automatically handles hook modifications:

```
Create commit → Hook modifies files → Safe to amend? → Amend or new commit
```

### Decision Tree

```
Hook modified files?
├─ No → Done ✅
└─ Yes → Is commit by current user?
    ├─ No → Create new commit ⚠️
    └─ Yes → Has commit been pushed?
        ├─ Yes → Create new commit ⚠️
        └─ No → Amend commit ✅
```

### Safety Checks for Amend

**Check 1: Authorship**
```zsh
# Get last commit author
author=$(git log -1 --format='%an %ae')

# Get current user
current_user=$(git config user.name)
current_email=$(git config user.email)

# Compare
if [[ "$author" == "$current_user $current_email" ]]; then
    # Safe: Own commit
else
    # NOT SAFE: Someone else's commit
fi
```

**Check 2: Push Status**
```zsh
# Check if commit has been pushed
status=$(git status -sb | head -1)

if [[ "$status" =~ "ahead" ]]; then
    # Safe: Local only, not pushed
else
    # NOT SAFE: Already pushed
fi
```

### Amend Scenarios

**Scenario 1: Safe to Amend** ✅
```
User: malte <malte@example.com>
Last commit author: malte <malte@example.com>  ✅ Match
Pushed: No (branch is "ahead" of remote)       ✅ Local only

Action: git commit --amend --no-edit
```

**Scenario 2: Different Author** ⚠️
```
User: malte <malte@example.com>
Last commit author: alice <alice@example.com>  ❌ Different author
Pushed: No

Action: Create new commit
Reason: Never amend someone else's work
```

**Scenario 3: Already Pushed** ⚠️
```
User: malte <malte@example.com>
Last commit author: malte <malte@example.com>  ✅ Match
Pushed: Yes (branch is up-to-date or behind)   ❌ Already on remote

Action: Create new commit
Reason: Never rewrite public history
```

### New Commit for Hook Changes

When it's not safe to amend, the skill creates a new commit:

```bash
# Stage hook modifications
git add -u

# Create new commit
git commit -m "chore: apply pre-commit hook changes"
```

This preserves history integrity and respects collaboration rules.

---

## Branch Protection

### Protected Branches

The following branches are always protected:
- `main`
- `master`

### Protection Rules

**1. Force-Push Protection**
```
Branch: main
Command: git-ops.zsh push --force

Result: ❌ BLOCKED
Error: "Force push to protected branch 'main' is not allowed"
```

**2. Regular Push (Allowed)**
```
Branch: main
Command: git-ops.zsh push

Result: ✅ ALLOWED
Action: Normal push with safety checks
```

**3. Force-Push to Feature Branch**
```
Branch: feature/add-auth
Command: git-ops.zsh push --force

Result: ✅ ALLOWED (with warning)
Warning: "Force pushing to 'feature/add-auth'"
Action: git push --force-with-lease
```

### Why --force-with-lease?

The skill uses `--force-with-lease` instead of `--force`:

```bash
# BAD: Overwrites any changes on remote
git push --force

# GOOD: Only overwrites if remote hasn't changed
git push --force-with-lease
```

`--force-with-lease` protects against the race condition where:
1. Someone pushes to your feature branch
2. You force-push
3. Their work is lost

With `--force-with-lease`, step 3 fails if step 1 happened.

---

## Push Safety Checks

### Pre-Push Validation

Before pushing, the skill performs these checks:

**1. Repository Check**
```zsh
if ! git rev-parse --git-dir &>/dev/null; then
    echo "Error: Not a git repository"
    exit 2
fi
```

**2. Remote Check**
```zsh
if ! git remote get-url origin &>/dev/null; then
    echo "Error: No remote 'origin' configured"
    exit 2
fi
```

**3. Branch Check**
```zsh
branch=$(git branch --show-current)
if [[ -z "$branch" ]]; then
    echo "Error: Not on any branch (detached HEAD)"
    exit 2
fi
```

**4. Protection Check**
```zsh
if [[ "$branch" == "main" ]] || [[ "$branch" == "master" ]]; then
    if [[ "$force" == "true" ]]; then
        echo "ERROR: Force push to protected branch not allowed"
        exit 1
    fi
fi
```

**5. Upstream Check**
```zsh
if ! git rev-parse --abbrev-ref "$branch@{upstream}" &>/dev/null; then
    echo "Error: Branch has no upstream"
    echo "Use --set-upstream to create it"
    exit 2
fi
```

**6. Ahead/Behind Check**
```zsh
status=$(git status -sb | head -1)

if [[ "$status" =~ "behind" ]]; then
    echo "Warning: Branch is behind remote"
    echo "Consider pulling before pushing"
fi

if [[ "$status" =~ "ahead" ]]; then
    # Has commits to push
else
    echo "Branch is up to date (nothing to push)"
    exit 0
fi
```

### Push Flow Diagram

```
Start push command
    ↓
Check: Is git repository? → No → ERROR ❌
    ↓ Yes
Check: Remote 'origin' exists? → No → ERROR ❌
    ↓ Yes
Check: On a branch? → No → ERROR ❌
    ↓ Yes
Check: Protected branch? → Yes → Force flag? → Yes → BLOCK ❌
    ↓ No                                      ↓ No
Check: Has upstream? → No → --set-upstream? → No → ERROR ❌
    ↓ Yes                 ↓ Yes                ↓ Yes
    |                     └─→ Push with -u
    ↓
Check: Ahead of remote? → No → INFO: Nothing to push
    ↓ Yes
Check: Force flag?
    ├─ Yes → Warn + push --force-with-lease
    └─ No → Regular push
        ↓
    ✅ SUCCESS
```

---

## Commit Safety Checks

### Pre-Commit Validation

**1. Repository Check**
```zsh
if ! is_git_repo; then
    echo "Error: Not a git repository"
    exit 2
fi
```

**2. Changes Check**
```zsh
if ! has_staged_changes && ! allow_empty; then
    echo "Error: No staged changes to commit"
    echo "Stage changes with 'git add'"
    exit 2
fi
```

**3. Message Validation**
```zsh
if ! validate_commit_message "$message" "$style"; then
    echo "Error: Invalid commit message"
    exit 1
fi
```

**4. Style Application**
```zsh
styled_message=$(apply_commit_style "$message" "$style")
```

**5. Attribution Filtering**
```zsh
if [[ "$attribution" == "none" ]]; then
    styled_message=$(remove_attribution "$styled_message")
fi
```

**6. Create Commit**
```zsh
git commit -m "$styled_message"
```

**7. Hook Check**
```zsh
if files_were_modified_by_hooks; then
    handle_hook_modifications
fi
```

---

## Error Handling

### Exit Codes

The skill uses standard exit codes:

- **0**: Success
- **1**: Validation error (user error)
- **2**: Git error (environment/state error)

### Error Messages

All errors include:
1. What went wrong
2. Why it went wrong
3. How to fix it

**Example 1: Invalid Message**
```
❌ ERROR: Invalid commit message for style: conventional
Expected format: type(scope?): message

Valid types: feat, fix, docs, refactor, test, chore, perf, style
Example: feat(auth): add user authentication
```

**Example 2: Protected Branch**
```
❌ ERROR: Force push to protected branch 'main' is not allowed

Protected branches: main, master
Force-push is only allowed on feature branches.
```

**Example 3: No Upstream**
```
❌ ERROR: Branch 'feature/test' has no upstream

Use --set-upstream to create it:
  git-ops.zsh push --set-upstream
```

---

## Best Practices

### 1. Never Skip Hooks

If hooks are failing, fix the issue, don't skip them:

```bash
# ❌ BAD: Skip hooks
git commit --no-verify

# ✅ GOOD: Fix the issue
# Fix linting errors, then commit normally
```

### 2. Pull Before Force-Pushing

Even on feature branches:

```bash
# ✅ GOOD: Update local, then force-push
git fetch origin
git rebase origin/feature/my-feature
git-ops.zsh push --force
```

### 3. Use Descriptive Commit Messages

Even with fun styles like pirate, the underlying message should be descriptive:

```bash
# ❌ BAD
git-ops.zsh commit -m "feat: stuff"

# ✅ GOOD
git-ops.zsh commit -m "feat(auth): implement JWT token validation"
```

### 4. Check Status Before Committing

```bash
# See what will be committed
git status
git diff --cached

# Then commit
git-ops.zsh commit -m "feat: add feature"
```

### 5. Test Locally Before Pushing

```bash
# Run tests
npm test

# Then push
git-ops.zsh push
```

---

## Troubleshooting

### "Not safe to amend" - Why?

Check two conditions:

**1. Authorship**
```bash
# Who created last commit?
git log -1 --format='%an %ae'

# Who am I?
git config user.name
git config user.email

# If different → Not safe
```

**2. Push status**
```bash
# Has commit been pushed?
git status

# If shows "Your branch is up to date" → Pushed → Not safe
# If shows "Your branch is ahead by 1" → Not pushed → Safe (if authorship matches)
```

### Force-push blocked on main

This is intentional. Never force-push to main/master.

**Options**:
1. Create feature branch
2. Make changes there
3. Push normally to feature branch
4. Create pull request

### Hook keeps modifying files

If hooks continuously modify files:

1. Run hooks manually: `.git/hooks/pre-commit`
2. Fix the issue they're complaining about
3. Commit normally

---

## Related Documentation

- `SKILL.md` - Main skill documentation
- `commit-styles.md` - Commit message style library
