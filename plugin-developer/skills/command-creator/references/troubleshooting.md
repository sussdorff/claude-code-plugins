# Command Troubleshooting Guide

Comprehensive guide for diagnosing and fixing common slash command issues.

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Command Not Appearing](#command-not-appearing)
3. [Permission Errors](#permission-errors)
4. [Parameters Not Working](#parameters-not-working)
5. [Model Issues](#model-issues)
6. [Execution Order Issues](#execution-order-issues)
7. [Performance Issues](#performance-issues)
8. [Parameter Parsing](#parameter-parsing)
9. [Tool Access Issues](#tool-access-issues)
10. [Integration Issues](#integration-issues)

---

## Quick Diagnosis

Use this table for rapid issue identification:

| Symptom | Likely Cause | Section |
|---------|--------------|---------|
| Command doesn't appear in /help | File location or naming issue | [Command Not Appearing](#command-not-appearing) |
| "Permission denied" errors | Tool restrictions too strict | [Permission Errors](#permission-errors) |
| Parameters ignored or wrong | Parameter syntax incorrect | [Parameters Not Working](#parameters-not-working) |
| Command too slow | Wrong model or inefficient steps | [Performance Issues](#performance-issues) |
| Steps execute out of order | Async operation handling | [Execution Order Issues](#execution-order-issues) |
| "Tool not allowed" error | Missing tool in allowed-tools | [Tool Access Issues](#tool-access-issues) |
| Variables not substituted | Wrong variable syntax | [Parameter Parsing](#parameter-parsing) |
| Command inconsistent | Model too simple for task | [Model Issues](#model-issues) |

---

## Command Not Appearing

### Symptoms
- Command not listed in `/help`
- Command not found when typing `/command-name`
- Command was working but disappeared

### Causes and Solutions

#### 1. File Location

**Cause:** Command file in wrong directory.

**Check:**
```bash
# Project commands should be in:
ls .claude/commands/

# Personal commands should be in:
ls ~/.claude/commands/
```

**Solution:**
```bash
# Move to correct location
mv wrong/location/my-command.md .claude/commands/

# Or for personal commands
mv wrong/location/my-command.md ~/.claude/commands/
```

---

#### 2. File Naming

**Cause:** Incorrect file extension or naming.

**Wrong:**
```bash
# Missing .md extension
.claude/commands/review-pr

# Wrong extension
.claude/commands/review-pr.txt

# Invalid characters
.claude/commands/review_pr.md
.claude/commands/reviewPR.md
```

**Correct:**
```bash
# Proper naming: lowercase-with-hyphens.md
.claude/commands/review-pr.md
.claude/commands/fix-issue.md
.claude/commands/run-tests.md
```

**Solution:**
```bash
# Rename file correctly
mv .claude/commands/review_pr.md .claude/commands/review-pr.md
```

---

#### 3. Invalid Frontmatter

**Cause:** Malformed YAML frontmatter prevents loading.

**Wrong:**
```markdown
---
description: Review PR
allowed-tools: [Read, Edit  # Missing closing bracket
---
```

**Correct:**
```markdown
---
description: Review PR
allowed-tools: Read, Edit
---
```

**Validation:**
```bash
# Use validator script
python3 plugin-developer/skills/command-creator/scripts/validate-command.py .claude/commands/review-pr.md
```

---

#### 4. Missing Description

**Cause:** Required `description` field missing.

**Wrong:**
```markdown
---
argument-hint: [PR-number]
---
```

**Correct:**
```markdown
---
description: Review pull request for quality and standards
argument-hint: [PR-number]
---
```

---

#### 5. File Permissions

**Cause:** File not readable by Claude Code.

**Check:**
```bash
# Check permissions
ls -l .claude/commands/review-pr.md
# Should show: -rw-r--r-- or similar with read permissions
```

**Solution:**
```bash
# Fix permissions
chmod 644 .claude/commands/review-pr.md
```

---

#### 6. Cache Issues

**Cause:** Claude Code hasn't refreshed command list.

**Solution:**
```bash
# Commands are loaded immediately after save in most cases
# If issues persist, try:
# 1. Save file again
# 2. Check file with /help command
# 3. Restart Claude Code session if needed
```

---

## Permission Errors

### Symptoms
- "Tool not allowed" errors
- Bash commands fail with permission denied
- File operations blocked

### Causes and Solutions

#### 1. Missing Tool in allowed-tools

**Symptom:**
```
Error: Tool 'Edit' not allowed by command configuration
```

**Cause:**
```markdown
---
allowed-tools: Read, Grep
---

# But command tries to use Edit
2. Update file with fix
```

**Solution:**
```markdown
---
allowed-tools: Read, Grep, Edit
---
```

---

#### 2. Bash Command Pattern Too Restrictive

**Symptom:**
```
Error: Bash(git diff) not allowed
```

**Wrong:**
```markdown
---
allowed-tools: Bash(git status:*)
---

# Tries to run: git diff
```

**Correct:**
```markdown
---
allowed-tools: Bash(git:*)
---

# Allows all git commands
```

**Pattern Examples:**
```yaml
# Too restrictive
allowed-tools: Bash(npm test:*)
# Only allows: npm test
# Blocks: npm run test, npm run test:watch

# Better
allowed-tools: Bash(npm:*), Bash(npm run:*)
# Allows: npm test, npm run test, npm run test:watch

# Most permissive
allowed-tools: Bash(*)
# Allows all bash commands (use carefully)
```

---

#### 3. Wildcard Pattern Issues

**Common mistakes:**

```yaml
# Wrong: Missing asterisk
allowed-tools: Bash(git)
# Only matches exactly "git" with no arguments

# Wrong: Too specific
allowed-tools: Bash(npm run test:*)
# Only matches "npm run test:something"
# Blocks: "npm test", "npm run test"

# Right: Proper wildcards
allowed-tools: Bash(git:*), Bash(npm:*)
# Matches: git anything, npm anything
```

---

#### 4. Tool Permission Debugging

**Debug approach:**

1. **Identify failed command:**
   ```
   Error: Bash(npm run lint:fix) not allowed
   ```

2. **Check current permissions:**
   ```markdown
   ---
   allowed-tools: Bash(npm:*)
   ---
   ```

3. **Understand the pattern:**
   - `Bash(npm:*)` matches `npm [anything]`
   - `npm run lint:fix` is actually `npm` + `run` + `lint:fix`
   - Pattern should match

4. **If still failing, expand pattern:**
   ```markdown
   ---
   allowed-tools: Bash(npm:*), Bash(npm run:*)
   ---
   ```

---

#### 5. File Permission Issues

**Symptom:**
```
Error: Cannot write to file [path]
```

**Causes:**
- File is read-only
- Directory doesn't exist
- Insufficient system permissions

**Solutions:**
```bash
# Check file permissions
ls -l path/to/file

# Make file writable
chmod 644 path/to/file

# Create directory if missing
mkdir -p path/to/directory

# Check directory permissions
ls -ld path/to/directory
```

---

## Parameters Not Working

### Symptoms
- Parameters show as literal `$ARGUMENTS` in output
- Multiple parameters not separated correctly
- File references not recognized

### Causes and Solutions

#### 1. Wrong Variable Syntax

**Wrong:**
```markdown
Review PR #$PR_NUMBER
Review PR #{$1}
Review PR $(1)
```

**Correct:**
```markdown
Review PR #$1
Review PR #$ARGUMENTS
Review issue: $ARGUMENTS
```

**Valid parameter variables:**
- `$ARGUMENTS` - All arguments as single string
- `$1`, `$2`, `$3`, etc. - Positional arguments
- `@file` - File references (used in invocation, not in command)

---

#### 2. Parameter Not Passed in Invocation

**Symptom:** Parameter is blank or shows variable name.

**Wrong invocation:**
```bash
/review-pr
# Command expects: /review-pr [PR-number]
```

**Correct invocation:**
```bash
/review-pr 123
```

**Detection in command:**
```markdown
1. Check if parameter provided:
   - If $ARGUMENTS is empty:
     - Show usage: /review-pr [PR-number]
     - Exit with error
   - Otherwise proceed
```

---

#### 3. Multiple Parameters Not Separated

**Command definition:**
```markdown
---
argument-hint: [PR-number] [priority]
---

Review PR #$1 with priority: $2
```

**Wrong invocation:**
```bash
/review-pr 123high
# $1 = "123high", $2 = empty
```

**Correct invocation:**
```bash
/review-pr 123 high
# $1 = "123", $2 = "high"
```

---

#### 4. Spaces in Arguments

**Issue:** Arguments with spaces split incorrectly.

**Command expects:**
```markdown
Deploy to: $ARGUMENTS
```

**Invocation with spaces:**
```bash
/deploy my staging environment
# $ARGUMENTS = "my staging environment" (correct)

/deploy $1 $2
# $1 = "my", $2 = "staging" (may not want this)
```

**Solutions:**

Use `$ARGUMENTS` for multi-word input:
```markdown
---
argument-hint: [description]
---

Fix issue: $ARGUMENTS
# Invocation: /fix-issue authentication bug in login
# $ARGUMENTS = "authentication bug in login"
```

Or require single-word parameters:
```markdown
---
argument-hint: [env] [region]
---

Deploy to $1 in region $2
# Invocation: /deploy staging us-east-1
# $1 = "staging", $2 = "us-east-1"
```

---

#### 5. File References

**File reference syntax:**

```bash
# In invocation (use @file syntax)
/review-code @src/components/Button.tsx
/optimize @src/utils/helper.ts @src/lib/api.ts

# In command (access via $ARGUMENTS)
---
description: Review code in specified files
---

Review files: $ARGUMENTS

1. Read each file in: $ARGUMENTS
2. Analyze code quality
3. Provide feedback
```

**Multiple files:**
```bash
/review-code @src/file1.ts @src/file2.ts
# $ARGUMENTS contains both file paths
```

---

#### 6. Default Parameter Values

**Using defaults for optional parameters:**

```markdown
Review PR #$1 with priority: ${2:-medium}

# Invocation with both: /review-pr 123 high
# $1 = "123", $2 = "high"

# Invocation with one: /review-pr 123
# $1 = "123", $2 = "medium" (default)
```

**Syntax:** `${N:-default}` where N is parameter number.

---

## Model Issues

### Symptoms
- Inconsistent results
- Command too slow
- Command doesn't follow steps
- Results not detailed enough

### Causes and Solutions

#### 1. Model Too Simple for Task

**Symptom:** Haiku doesn't handle complex logic well.

**Wrong:**
```markdown
---
description: Complex architectural analysis
model: claude-3-5-haiku-20241022
---

Analyze architecture and suggest improvements...
```

**Solution:**
```markdown
---
description: Complex architectural analysis
model: claude-opus-4-20250514
---
```

**Model capabilities:**
- **Haiku:** Simple, well-defined tasks (< 5 steps)
- **Sonnet:** Standard workflows (5-15 steps)
- **Opus:** Complex reasoning, novel problems

---

#### 2. Model Too Powerful for Task

**Symptom:** Simple task is slow.

**Wrong:**
```markdown
---
description: Run linter
model: claude-opus-4-20250514
---

Run npm run lint
```

**Solution:**
```markdown
---
description: Run linter
model: claude-3-5-haiku-20241022
---
```

**Why:** Haiku is faster and cheaper for simple tasks.

---

#### 3. No Model Specified

**Behavior:** Uses default model (Sonnet).

**When default is fine:**
```markdown
---
description: Standard code review
---
# No model specified = Sonnet (good choice)
```

**When to specify:**
```markdown
# Specify Haiku for speed
---
model: claude-3-5-haiku-20241022
---

# Specify Opus for complexity
---
model: claude-opus-4-20250514
---
```

---

#### 4. Model ID Typos

**Wrong:**
```markdown
---
model: claude-3-haiku
model: claude-opus
model: sonnet-3.7
---
```

**Correct:**
```markdown
---
model: claude-3-5-haiku-20241022
model: claude-3-7-sonnet-20250219
model: claude-opus-4-20250514
---
```

**Validation:**
```bash
# Validate with script
python3 plugin-developer/skills/command-creator/scripts/validate-command.py .claude/commands/my-command.md
```

---

## Execution Order Issues

### Symptoms
- Steps execute out of order
- Some steps skipped
- Results from earlier steps not available later

### Causes and Solutions

#### 1. Implicit Dependencies Not Clear

**Wrong:**
```markdown
1. Create PR
2. Get PR number from previous step
```

**Better:**
```markdown
1. Create PR and capture PR number:
   - Run: gh pr create
   - Extract PR number from output
   - Store for next steps

2. Use PR number from step 1:
   - Add labels: gh pr edit [PR-number]
   - Request reviewers: gh pr edit [PR-number]
```

---

#### 2. Async Operations

**Issue:** Bash commands may need results immediately.

**Solution - Sequential operations:**
```markdown
1. Run operations in sequence:
   - First: npm run build
   - Wait for build to complete
   - Then: npm run test
   - Wait for tests to complete
   - Finally: report results
```

---

#### 3. Conditional Logic Unclear

**Wrong:**
```markdown
1. Check if tests pass
2. Deploy if passed
```

**Better:**
```markdown
1. Run tests:
   - Execute: npm test
   - Capture exit code

2. Decision point:
   - If tests passed (exit code 0):
     - Proceed to step 3 (deploy)
   - If tests failed:
     - Stop here
     - Report failures
     - Do not deploy

3. Deploy (only if tests passed):
   - Run: ./deploy.sh
```

---

## Performance Issues

### Symptoms
- Command takes too long
- Times out
- Uses too many resources

### Causes and Solutions

#### 1. Wrong Model for Task

**Issue:** Using Opus for simple tasks.

**Solution:**
```markdown
# Change from Opus to Haiku for simple tasks
---
model: claude-3-5-haiku-20241022
---
```

**Performance comparison:**
- Haiku: Fastest (< 5 seconds typical)
- Sonnet: Medium (5-15 seconds typical)
- Opus: Slowest (15-30+ seconds typical)

---

#### 2. Inefficient Commands

**Wrong:**
```markdown
1. For each file in src/:
   - Run: cat file | grep "pattern"
   - Process results
```

**Better:**
```markdown
1. Search efficiently:
   - Use: grep -r "pattern" src/
   - Or: Use Grep tool (optimized)
   - Process all results at once
```

---

#### 3. Unnecessary Operations

**Wrong:**
```markdown
1. Full test suite (10 minutes)
2. Full lint (5 minutes)
3. Full type check (5 minutes)
# Total: 20 minutes for simple fix
```

**Better:**
```markdown
1. Quick validation:
   - Lint only changed files
   - Type check only if TypeScript changed
   - Test only affected tests
# Total: 2-3 minutes
```

---

#### 4. Redundant Steps

**Wrong:**
```markdown
1. git status
2. git diff
3. git status again
4. git diff again
```

**Better:**
```markdown
1. Git status check (once):
   - Status: git status
   - Diff: git diff
   - Use results for all subsequent steps
```

---

#### 5. Large File Operations

**Wrong:**
```markdown
1. Read entire 10MB log file
2. Process all lines
```

**Better:**
```markdown
1. Read efficiently:
   - Last 1000 lines: tail -1000 logfile
   - Search for errors: grep ERROR logfile
   - Don't read entire file unless needed
```

---

## Parameter Parsing

### Symptoms
- Arguments split incorrectly
- Quotes not handled properly
- Special characters cause issues

### Causes and Solutions

#### 1. Quoted Arguments

**Issue:** Quotes in user input.

**User types:**
```bash
/fix-issue "authentication bug"
```

**In command:**
```markdown
# $ARGUMENTS = "authentication bug" (including quotes)
```

**Solution - Handle quotes:**
```markdown
1. Parse arguments:
   - Remove surrounding quotes if present
   - Extract actual content: authentication bug
2. Use cleaned argument in steps
```

---

#### 2. Special Characters

**Issue:** Characters like `$`, `*`, `&` in arguments.

**User types:**
```bash
/search-code $variable
```

**Problem:** `$variable` might be interpreted as shell variable.

**Solution:**
```markdown
1. Search for literal string: $ARGUMENTS
   - Escape special characters if needed
   - Use exact string search
```

---

#### 3. Numbers vs Strings

**Issue:** Distinguishing between issue numbers and text.

**Command:**
```markdown
Fix issue: $ARGUMENTS
```

**Invocations:**
```bash
/fix-issue 123           # Issue number
/fix-issue auth-bug      # Issue description
```

**Solution - Handle both:**
```markdown
1. Identify argument type:
   - If $ARGUMENTS is a number:
     - Fetch issue: gh issue view $ARGUMENTS
   - If $ARGUMENTS is text:
     - Search issues: gh issue list --search "$ARGUMENTS"
     - Ask user which issue to fix
```

---

## Tool Access Issues

### Symptoms
- Specific tools blocked
- Bash patterns don't match
- File operations fail

### Detailed Solutions

#### 1. Common Tool Patterns

**Git operations:**
```yaml
# All git commands
allowed-tools: Bash(git:*)

# Read-only git
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*)

# Specific git operations
allowed-tools: Bash(git status:*), Bash(git add:*), Bash(git commit:*)
```

**NPM operations:**
```yaml
# All npm
allowed-tools: Bash(npm:*)

# Only run scripts
allowed-tools: Bash(npm run:*)

# Testing only
allowed-tools: Bash(npm test:*), Bash(npm run test:*)

# No install/uninstall
allowed-tools: Bash(npm run:*), Bash(npm test:*)
# Blocks: npm install, npm uninstall
```

**File operations:**
```yaml
# Read only
allowed-tools: Read, Grep, Glob

# Read and search
allowed-tools: Read, Grep, Glob

# Read and modify
allowed-tools: Read, Edit, Grep, Glob

# Full file access
allowed-tools: Read, Edit, Write, Glob, Grep
```

---

#### 2. Debugging Tool Access

**When command fails:**

1. **Check error message:**
   ```
   Error: Bash(npm run lint:fix) not allowed
   ```

2. **Check current permissions:**
   ```markdown
   ---
   allowed-tools: Bash(npm:*)
   ---
   ```

3. **Test pattern matching:**
   - Command: `npm run lint:fix`
   - Pattern: `Bash(npm:*)`
   - Match: `npm` + anything after
   - Should work! ✅

4. **If pattern should work but doesn't:**
   - Try more specific pattern
   - Try broader pattern
   - Check for typos in tool name

---

#### 3. Overly Permissive

**Problem:** Allowing too much access.

**Too permissive:**
```yaml
# Allows everything (rarely needed)
allowed-tools: Bash(*), Read, Edit, Write, Glob, Grep
```

**Better - Principle of least privilege:**
```yaml
# Only what's needed
allowed-tools: Bash(git:*), Bash(npm test:*), Read, Edit, Grep
```

---

## Integration Issues

### Symptoms
- Commands don't work with hooks
- CLAUDE.md conflicts
- Skill interactions

### Causes and Solutions

#### 1. Command vs CLAUDE.md Conflict

**Issue:** Command and CLAUDE.md give conflicting instructions.

**CLAUDE.md:**
```markdown
Always run full test suite before committing
```

**Command:**
```markdown
# /quick-commit
Quick commit without tests
```

**Solution:** Align both or clarify priorities:

**Option 1 - Align:**
```markdown
# In command
1. Run full test suite (per CLAUDE.md)
2. Then commit
```

**Option 2 - Clarify:**
```markdown
# In CLAUDE.md
For standard commits: run /pre-commit (includes tests)
For emergency hotfix: use /quick-commit (skip tests, use with caution)
```

---

#### 2. Hook Conflicts

**Issue:** Hook and command both try to do same thing.

**Pre-commit hook:**
```bash
npm run lint
```

**Command also runs:**
```markdown
1. Run lint: npm run lint
```

**Solution:** Coordinate:
```markdown
# In command
1. Linting:
   - If pre-commit hook exists: will run automatically
   - If no hook: run npm run lint manually
```

---

#### 3. Skill Activation

**Issue:** Command triggers skill unintentionally.

**Solution:** Be specific in command to avoid triggering skills:
```markdown
# Avoid generic phrases that might trigger skills
❌ "Review this code"
✅ "Run code review following checklist"
```

---

## General Debugging Process

### Step-by-Step Debugging

1. **Verify command loads:**
   ```bash
   # Check if appears in help
   /help
   ```

2. **Check file location and naming:**
   ```bash
   ls -la .claude/commands/my-command.md
   ```

3. **Validate structure:**
   ```bash
   python3 plugin-developer/skills/command-creator/scripts/validate-command.py .claude/commands/my-command.md
   ```

4. **Test with minimal input:**
   ```bash
   /my-command simple-test
   ```

5. **Check error messages:**
   - Read full error
   - Identify which step failed
   - Check tool permissions for that step

6. **Simplify to isolate issue:**
   - Comment out steps
   - Test each step individually
   - Identify problematic step

7. **Check model appropriateness:**
   - Is model right for complexity?
   - Try different model

8. **Review permissions:**
   - Are all needed tools allowed?
   - Are patterns correct?

---

## Getting Help

### When You're Stuck

1. **Check this guide:** Most issues covered here

2. **Validate command:**
   ```bash
   python3 plugin-developer/skills/command-creator/scripts/validate-command.py [command-file]
   ```

3. **Simplify command:**
   - Remove complex steps
   - Test simple version
   - Add complexity back gradually

4. **Check examples:**
   - Look at working commands
   - Compare structure
   - Adapt working patterns

5. **Review references:**
   - best-practices.md
   - command-templates.md
   - common-patterns.md

---

## Prevention

### Avoid Issues Before They Happen

1. **Use validation script:**
   ```bash
   # Always validate before using
   python3 plugin-developer/skills/command-creator/scripts/validate-command.py .claude/commands/new-command.md
   ```

2. **Start with templates:**
   - Use init-command.py script
   - Modify proven templates
   - Don't start from scratch

3. **Test incrementally:**
   - Test after each change
   - Don't write entire command then test
   - Fix issues as you find them

4. **Follow naming conventions:**
   - Lowercase with hyphens
   - .md extension
   - Descriptive names

5. **Document as you go:**
   - Clear descriptions
   - Argument hints
   - Usage examples

6. **Minimal permissions:**
   - Start restrictive
   - Add as needed
   - Test permission errors

7. **Right model from start:**
   - Simple task? Haiku
   - Standard task? Sonnet (or don't specify)
   - Complex task? Opus

---

## Summary

**Most Common Issues:**
1. File naming or location
2. Tool permissions too restrictive
3. Parameter syntax errors
4. Wrong model for task
5. Frontmatter errors

**Quick Fixes:**
1. Run validation script
2. Check file location and naming
3. Expand tool permissions if needed
4. Verify parameter syntax
5. Test with simple input first

**Best Prevention:**
- Use init-command.py script
- Validate before first use
- Start with proven templates
- Test incrementally
- Follow best practices

Remember: Most issues are quick fixes once identified. Use validation script and this guide to diagnose and resolve issues efficiently.
