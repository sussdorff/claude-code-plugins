# Skill Testing Workflow

Complete guide for testing skills during development in the solutio-claude-skills project.

## Project Structure

```
solutio-claude-skills/
├── jira-context-fetcher/      # Skill under development
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   └── assets/
├── screenshot-analyzer/        # Another skill
├── jira-commentator/          # Another skill
├── skill-tester/              # This meta skill!
└── .claude/                   # Testing location
    └── skills/                # Where skills are installed for testing
        └── jira-context-fetcher/  # Installed copy
```

## How Skills Are Loaded

**Critical Understanding:**
- Skills are loaded when Claude Code **starts a session**
- Skills are **NOT** dynamically reloaded during a session
- Changes to skill files require a **new session** to take effect
- New skills require a **restart** to be discovered

## Testing Workflow

### Option 1: Quick Test (Recommended)

Use the skill-tester skill's install script:

```bash
# Install/update skill for testing
./skill-tester/scripts/install-skill-for-testing.zsh jira-context-fetcher

# Follow the output instructions:
# - If NEW skill: Exit and restart Claude Code
# - If UPDATED: Changes available (restart if issues)

# Test the skill
# For new skills, start new session first:
claude

# Then test naturally:
"Test jira-context-fetcher by fetching PROJ-123"
"Use jira-context-fetcher to download CH2-14031"
```

### Option 2: Manual Copy

```bash
# Create target if needed
mkdir -p .claude/skills/

# Copy skill
rsync -av --delete jira-context-fetcher/ .claude/skills/jira-context-fetcher/

# If this is a NEW skill (first time):
#   - Exit Claude Code session
#   - Start new session: claude
# If this is an UPDATE:
#   - Changes should be available
#   - Restart session if not appearing
```

### Option 3: Development Loop

```bash
# 1. Edit skill files
vi jira-context-fetcher/SKILL.md
vi jira-context-fetcher/scripts/fetch-ticket-standalone.zsh

# 2. Install for testing
./skill-tester/scripts/install-skill-for-testing.zsh jira-context-fetcher

# 3. Test in Claude Code (start new session if needed)
# 4. Observe results
# 5. Repeat from step 1
```

## Validation Before Testing

Always validate before testing to catch issues early:

```bash
# Quick validation
./skill-tester/scripts/validate-skill.py jira-context-fetcher

# Full validation with packaging
cd /Users/malte/.claude/plugins/marketplaces/anthropic-agent-skills/skill-creator/
./scripts/package_skill.py /Users/malte/code/solutio/solutio-claude-skills/jira-context-fetcher
```

## Testing Checklist

### Before Testing
- [ ] Skill validates successfully
- [ ] SKILL.md description is clear and specific
- [ ] All script dependencies are documented
- [ ] References are organized and named correctly (kebab-case)

### During Testing
- [ ] Skill activates when expected (check Claude's response)
- [ ] Scripts execute correctly
- [ ] Error messages are helpful
- [ ] Edge cases are handled

### After Testing
- [ ] All test scenarios pass
- [ ] Documentation is accurate
- [ ] Examples work as described
- [ ] Ready for packaging

## Common Issues

### Issue: Skill doesn't activate

**Symptoms:** Claude doesn't use the skill when prompted

**Causes:**
1. Skill not installed to `.claude/skills/`
2. New skill but didn't restart session
3. Description doesn't match use case

**Solutions:**
1. Run install script: `./skill-tester/scripts/install-skill-for-testing.zsh <name>`
2. Exit and restart Claude Code session
3. Improve skill description in YAML frontmatter

### Issue: Old version of skill is being used

**Symptoms:** Changes don't appear in Claude's behavior

**Causes:**
1. Didn't copy updated files to `.claude/skills/`
2. Session started before files were copied

**Solutions:**
1. Run install script again
2. Start a fresh Claude Code session

### Issue: Scripts not found

**Symptoms:** Script execution fails with "not found"

**Causes:**
1. Script paths in SKILL.md are wrong
2. Scripts weren't copied to `.claude/skills/`

**Solutions:**
1. Verify paths are relative to skill root
2. Re-run install script
3. Check file permissions: `chmod +x scripts/*.zsh`

## Testing with Real Data

For jira-context-fetcher and similar skills:

1. **Set up environment**:
   ```bash
   # Ensure JIRA credentials are configured
   cat ~/.jira-analyzer.json
   echo $JIRA_EMAIL $JIRA_TOKEN
   ```

2. **Test with real tickets**:
   ```bash
   # Use actual ticket numbers from your JIRA
   "Fetch CH2-14031"
   "Download PROJ-123 including linked tickets"
   ```

3. **Verify outputs**:
   ```bash
   # Check generated files
   ls -la /tmp/jira-ticket-CH2-14031/
   jq . /tmp/jira-ticket-CH2-14031/manifest.json
   ```

## Programmatic Testing

For automated testing (useful for CI/CD later):

```bash
# test-skills.sh
#!/bin/zsh

# Install all skills
for skill in jira-context-fetcher screenshot-analyzer jira-commentator; do
  if [[ -d "$skill" ]]; then
    echo "Installing $skill..."
    ./skill-tester/scripts/install-skill-for-testing.zsh "$skill"
  fi
done

# Run tests with claude -p
echo "Testing jira-context-fetcher..."
claude -p "Use jira-context-fetcher to validate configuration" > test-results.txt

# Check results
if grep -q "success" test-results.txt; then
  echo "✓ Tests passed"
else
  echo "✗ Tests failed"
  cat test-results.txt
fi
```

## Distribution Workflow

Once testing is complete:

```bash
# 1. Final validation
./skill-tester/scripts/validate-skill.py jira-context-fetcher

# 2. Package for distribution
cd /Users/malte/.claude/plugins/marketplaces/anthropic-agent-skills/skill-creator/
./scripts/package_skill.py /Users/malte/code/solutio/solutio-claude-skills/jira-context-fetcher

# 3. Share the .zip file
ls -lh /Users/malte/code/solutio/solutio-claude-skills/jira-context-fetcher.zip

# 4. Users can install with:
#    unzip jira-context-fetcher.zip -d ~/.claude/skills/
```

## Best Practices

1. **Test incrementally**: Install and test after each significant change
2. **Use real scenarios**: Test with actual data, not just synthetic examples
3. **Document issues**: Keep notes on what works and what doesn't
4. **Validate often**: Run validation before committing changes
5. **Clean installs**: Delete `.claude/skills/<name>` and reinstall for clean tests

## See Also

- [install-skill-for-testing.zsh](../scripts/install-skill-for-testing.zsh) - Installation script
- [validate-skill.py](../scripts/validate-skill.py) - Validation script
- [SKILL.md](../SKILL.md) - Skill-tester documentation
