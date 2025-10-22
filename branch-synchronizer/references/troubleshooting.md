# Branch Synchronizer - Troubleshooting Guide

Common issues and their solutions.

## Table of Contents

- [Configuration Issues](#configuration-issues)
- [Branch Issues](#branch-issues)
- [Rebase Issues](#rebase-issues)
- [Conflict Issues](#conflict-issues)
- [Performance Issues](#performance-issues)
- [Integration Issues](#integration-issues)

## Configuration Issues

### "No jira-analyzer.json found"

**Problem**: The script can't find ticket pattern configuration.

**Solution**:

1. **Check config location**:
```zsh
# Project-local (preferred for team projects)
ls -la .jira-analyzer.json

# Global (fallback)
ls -la ~/.jira-analyzer.json
```

2. **Create minimal config**:
```zsh
# In project root
cat > .jira-analyzer.json << 'EOF'
{
  "instances": [
    {
      "name": "my-jira",
      "prefixes": ["PROJ", "BUG"]
    }
  ]
}
EOF
```

3. **Verify JSON syntax**:
```zsh
jq empty .jira-analyzer.json
```

### "Invalid JSON in config file"

**Problem**: The jira-analyzer.json has syntax errors.

**Solution**:

1. **Validate JSON**:
```zsh
jq empty ~/.jira-analyzer.json
# Or
cat ~/.jira-analyzer.json | jq .
```

2. **Common syntax errors**:
- Missing commas between array elements
- Trailing commas in objects/arrays
- Unescaped quotes in strings
- Missing closing brackets

3. **Use a JSON validator**:
```zsh
# Online: https://jsonlint.com
# Or use jq for formatting
jq . ~/.jira-analyzer.json > temp.json && mv temp.json ~/.jira-analyzer.json
```

### "No prefixes found in config"

**Problem**: The config file exists but has no prefixes defined.

**Solution**:

1. **Check structure**:
```zsh
jq '.instances[].prefixes' ~/.jira-analyzer.json
```

Expected output: `["CH2", "FALL"]`

2. **Fix structure**:
```json
{
  "instances": [
    {
      "name": "my-jira",
      "prefixes": ["PROJ"]  // ← Must be here
    }
  ]
}
```

## Branch Issues

### "Branch does not exist"

**Problem**: The specified branch doesn't exist locally or remotely.

**Solution**:

1. **List available branches**:
```zsh
# Local branches
git branch

# Remote branches
git branch -r

# All branches with pattern
git branch -a | grep PROJ-123
```

2. **Fetch from remote**:
```zsh
git fetch --all
git branch -r | grep your-pattern
```

3. **Check branch name spelling**:
```zsh
# Case-sensitive search
git branch -a | grep -i ch2-123
```

### "Not on a branch (detached HEAD state)"

**Problem**: Repository is in detached HEAD state.

**Solution**:

1. **Check current state**:
```zsh
git status
# HEAD detached at a1b2c3d
```

2. **Create branch from current state**:
```zsh
git checkout -b my-branch
```

3. **Or checkout an existing branch**:
```zsh
git checkout main
```

### "Pattern already merged to main"

**Problem**: The ticket branch has already been merged and closed.

**Solution**:

1. **Verify merge status**:
```zsh
git log --merges --grep="PROJ-123" --oneline origin/main
```

2. **Options**:
   - Create new branch for additional work
   - Work on a different ticket
   - Create hotfix branch from main

### "Multiple branches found for pattern"

**Problem**: Multiple branches match the pattern.

**Information**: This is expected behavior. The script selects the most recently updated branch.

**To see which branch was selected**:
```zsh
# The script outputs:
Found 3 branch(es) for PROJ-123:
  - feature/PROJ-123/fix-bug
  - bugfix/PROJ-123/urgent
  - test/PROJ-123/verify
  → Using most recent: feature/PROJ-123/fix-bug (updated: 2024-01-15)
```

**To force a specific branch**:
```zsh
./sync-branch.zsh --branch feature/PROJ-123/fix-bug
```

## Rebase Issues

### "Failed to fetch from origin"

**Problem**: Can't connect to remote repository.

**Solution**:

1. **Check network connection**:
```zsh
ping github.com
```

2. **Verify remote URL**:
```zsh
git remote -v
# origin  git@github.com:user/repo.git (fetch)
```

3. **Test SSH/HTTPS access**:
```zsh
# For SSH
ssh -T git@github.com

# For HTTPS
git ls-remote origin
```

4. **Update remote URL if needed**:
```zsh
git remote set-url origin git@github.com:user/repo.git
```

### "No remote branch found"

**Problem**: Branch exists locally but not on remote.

**Solution**:

1. **Push branch to remote**:
```zsh
git push -u origin branch-name
```

2. **Or sync without remote**:
The script will skip remote sync and just rebase onto main.

### "Rebase encountered conflicts"

**Problem**: Files have conflicts during rebase.

**Solution depends on mode**:

**Interactive Mode**:
1. Edit conflicting files (marked with `<<<<<<<`, `=======`, `>>>>>>>`)
2. Choose which changes to keep
3. Remove conflict markers
4. Mark as resolved:
```zsh
git add <resolved-files>
git rebase --continue
```

**Agent Mode**:
The rebase is automatically aborted. Resolve manually:
```zsh
cd /path/to/worktree
git rebase origin/main

# Resolve conflicts
git add <files>
git rebase --continue
```

## Conflict Issues

### "Cannot apply stash pop after rebase"

**Problem**: Stashed changes conflict with rebased changes.

**Solution**:

1. **Check stash list**:
```zsh
git stash list
# stash@{0}: On branch: branch-synchronizer auto-stash
```

2. **Try applying stash**:
```zsh
git stash show
git stash apply  # Try apply without deleting stash
```

3. **If conflicts, resolve manually**:
```zsh
# Resolve conflicts in files
git add <resolved-files>

# Drop the applied stash
git stash drop
```

### "Uncommitted changes would be overwritten"

**Problem**: Have uncommitted changes that conflict with rebase.

**Solution**:

The script should auto-stash these, but if it fails:

1. **Stash manually**:
```zsh
git stash push -m "manual save before rebase"
```

2. **Run sync again**:
```zsh
./sync-branch.zsh
```

3. **Restore stash**:
```zsh
git stash pop
```

### "Force-push required after rebase"

**Problem**: Local branch has diverged from remote after rebase.

**Solution**:

1. **Use force-with-lease (safer)**:
```zsh
git push --force-with-lease origin branch-name
```

This fails if remote has commits you don't have locally (protects against data loss).

2. **If force-with-lease fails**:
```zsh
# Fetch latest and review remote commits
git fetch origin
git log HEAD..origin/branch-name

# If safe to overwrite, force push
git push --force origin branch-name
```

## Performance Issues

### "Sync is very slow"

**Problem**: Fetching and rebasing takes a long time.

**Solution**:

1. **Check network speed**:
```zsh
# Test fetch speed
time git fetch origin
```

2. **Use shallow fetch** (if appropriate):
```zsh
git fetch --depth=100 origin
```

3. **Reduce remote operations**:
```zsh
# Fetch once for multiple syncs
git fetch --all

# Then sync without repeated fetches (modify script or use cached fetch)
```

4. **Check repository size**:
```zsh
du -sh .git
```

Large repos benefit from:
- `git gc` (garbage collection)
- `git prune` (remove old objects)

### "Multiple syncs are slow"

**Problem**: Syncing many worktrees is taking too long.

**Solution**:

1. **Batch with shared fetch**:
```zsh
# Fetch once in main repo
cd /main/repo
git fetch --all

# Then sync worktrees (they share git objects)
for wt in /repo/.worktrees/*; do
  ./sync-branch.zsh --path "$wt"
done
```

2. **Parallel execution** (careful with conflicts):
```zsh
find /repo/.worktrees -maxdepth 1 -type d | \
  xargs -P 4 -I {} ./sync-branch.zsh --path {}
```

## Integration Issues

### "Script not found when called by Claude"

**Problem**: Claude Code can't find the script.

**Solution**:

1. **Check SKILL.md allowed_tools**:
```yaml
allowed_tools: Bash(./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh *)
```

2. **Verify skill is installed**:
```zsh
ls -la ./.claude/skills/branch-synchronizer/
```

3. **Test manually first**:
```zsh
./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --help
```

### "Permission denied"

**Problem**: Script is not executable.

**Solution**:

```zsh
chmod +x ./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh
chmod +x ./.claude/skills/branch-synchronizer/scripts/lib/*.zsh
```

### "Library functions not found"

**Problem**: Script can't source library files.

**Solution**:

1. **Check library files exist**:
```zsh
ls -la ./scripts/lib/*.zsh
```

2. **Verify SCRIPT_DIR detection**:
```zsh
# In sync-branch.zsh
echo "SCRIPT_DIR: $SCRIPT_DIR"
```

3. **Use absolute paths** if needed:
```zsh
# In sync-branch.zsh
SCRIPT_DIR="/absolute/path/to/scripts"
```

### "Agent mode not working correctly"

**Problem**: Script behaves interactively when it should be in agent mode.

**Solution**:

1. **Explicitly set agent mode**:
```zsh
export BRANCH_SYNC_AGENT_MODE=true
./sync-branch.zsh --path /worktree
```

2. **Verify mode detection**:
```zsh
# Add debug output to sync-functions.zsh
is_agent_mode() {
    echo "DEBUG: BRANCH_SYNC_AGENT_MODE=${BRANCH_SYNC_AGENT_MODE:-unset}" >&2
    echo "DEBUG: PATH_PROVIDED=${BRANCH_SYNC_PATH_PROVIDED:-unset}" >&2
    # ... rest of function
}
```

3. **Check environment variables**:
```zsh
env | grep BRANCH_SYNC
```

## Advanced Debugging

### Enable Trace Mode

```zsh
# Full command tracing
zsh -x ./sync-branch.zsh

# Or add to script
set -x
```

### Check Git Operations

```zsh
# Enable git trace
export GIT_TRACE=1
export GIT_CURL_VERBOSE=1
./sync-branch.zsh
```

### Test Individual Functions

```zsh
# Source libraries
source ./scripts/lib/config-functions.zsh
source ./scripts/lib/sync-functions.zsh
source ./scripts/lib/branch-functions.zsh

# Test specific function
load_ticket_patterns .
find_ticket_branch "PROJ-123" .
```

### Validate Shell Scripts

```zsh
# Check syntax
zsh -n ./sync-branch.zsh
zsh -n ./scripts/lib/*.zsh

# Use shellcheck (if available)
shellcheck ./sync-branch.zsh
shellcheck ./scripts/lib/*.zsh
```

## Getting Help

If issues persist:

1. **Check skill documentation**:
   - [SKILL.md](../SKILL.md) - Main documentation
   - [usage-guide.md](./usage-guide.md) - Usage examples

2. **Review git state**:
```zsh
git status
git log --oneline -10
git remote -v
```

3. **Collect diagnostic info**:
```zsh
# System info
uname -a
zsh --version
git --version

# Configuration
cat ~/.jira-analyzer.json | jq .
git config --list | grep remote
```

4. **Test in isolation**:
```zsh
# Create test repo
mkdir /tmp/test-sync
cd /tmp/test-sync
git init
# ... test sync operations
```

## Common Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Error: Not a git repository` | Not in git repo | `cd` to repo first |
| `Error: Path does not exist` | Invalid --path | Check path spelling |
| `Failed to fetch from origin` | Network issue | Check connection, credentials |
| `No existing branches found` | Pattern not found | Check pattern in `git branch -a` |
| `Rebase encountered conflicts` | Conflicting changes | Resolve conflicts manually |
| `Branch already merged` | Work complete | Create new branch |
| `Pattern not found in config` | Missing JIRA prefix | Add to jira-analyzer.json |

## See Also

- [SKILL.md](../SKILL.md) - Main skill documentation
- [usage-guide.md](./usage-guide.md) - Comprehensive usage examples
