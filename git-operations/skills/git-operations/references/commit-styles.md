# Commit Message Styles

This document describes all available commit message styles supported by the git-operations skill.

## Configuration

Set your preferred style in CLAUDE.md or CLAUDE.local.md:

```markdown
Commit style: [style-name]
Commit attribution: [none|claude|custom]
```

**Priority**:
1. CLAUDE.local.md (project-specific)
2. CLAUDE.md (user-wide)
3. Default: conventional

## Available Styles

### conventional (Default)

Standard conventional commits format widely used in the industry.

**Format**: `type(scope?): message`

**Valid Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `refactor` - Code refactoring
- `test` - Test changes
- `chore` - Build/tooling changes
- `perf` - Performance improvements
- `style` - Code style changes (formatting, etc.)

**Scope**: Optional, lowercase, hyphenated (e.g., `api`, `auth`, `user-service`)

**Examples**:
```
feat: add user authentication
fix(api): handle null response
docs: update README with examples
refactor(core): simplify error handling
test(auth): add integration tests
chore: update dependencies
perf(db): optimize query performance
style: fix indentation
```

**With scopes**:
```
feat(auth): implement JWT tokens
fix(api): resolve timeout issues
docs(readme): add installation guide
```

**Multi-line example**:
```
feat(api): add user profile endpoint

This endpoint allows users to view and update their profiles.
Includes validation and error handling.

Closes #123
```

**Validation**: Strict - must follow `type(scope?): message` format

---

### pirate

Commit messages in pirate speak. Perfect for Friday deployments and keeping the mood light.

**Transformations**:
- `feat` → "Arr! Hoisted the new feature:"
- `fix` → "Arr! Plundered the bug in:"
- `docs` → "Arr! Scribed the scrolls for:"
- `refactor` → "Arr! Rejiggered the code for:"
- `test` → "Arr! Tested the waters of:"
- `chore` → "Arr! Swabbed the decks:"
- `perf` → "Arr! Made faster the:"
- `style` → "Arr! Polished the brass on:"

**Input** (conventional format):
```
feat: add user authentication
fix(api): handle null pointer
docs: update README
```

**Output** (pirate style):
```
Arr! Hoisted the new feature: user authentication
Arr! Plundered the bug in api: null pointer handling
Arr! Scribed the scrolls for: README updates
```

**Validation**: Accepts conventional format as input

---

### snarky

Sarcastic commit messages. Use when bugs are especially frustrating or features are questionable.

**Transformations**:
- `feat` → "Because apparently we needed:"
- `fix` → "Obviously this needed attention:"
- `docs` → "Yet another documentation update for:"
- `refactor` → "Because the previous implementation was clearly brilliant:"
- `test` → "Testing, because who doesn't love tests for:"
- `chore` → "The thrilling chore of:"

**Input** (conventional format):
```
feat: add user preferences
fix: handle edge case
docs: clarify API usage
refactor: simplify auth logic
```

**Output** (snarky style):
```
Because apparently we needed: user preferences
Obviously this needed attention: edge case handling
Yet another documentation update for: API usage
Because the previous implementation was clearly brilliant: auth logic
```

**Validation**: Accepts conventional format as input

---

### emoji

Conventional commits with emoji prefixes for visual clarity.

**Emoji Mapping**:
- `feat`: ✨ (sparkles)
- `fix`: 🐛 (bug)
- `docs`: 📝 (memo)
- `refactor`: ♻️ (recycle)
- `test`: ✅ (check mark)
- `chore`: 🔧 (wrench)
- `perf`: ⚡ (zap)
- `style`: 💄 (lipstick)

**Input** (conventional format):
```
feat: add user authentication
fix(api): handle null pointer
docs: update README
perf: optimize database queries
```

**Output** (emoji style):
```
✨ feat: add user authentication
🐛 fix(api): handle null pointer
📝 docs: update README
⚡ perf: optimize database queries
```

**Validation**: Accepts conventional format as input

---

### minimal

Just the message, no type prefixes. For small projects or personal repos where formality isn't needed.

**Transformation**: Strips type and scope prefixes from conventional format.

**Input** (conventional format):
```
feat: add user authentication
fix(api): handle null pointer
docs: update README
```

**Output** (minimal style):
```
add user authentication
handle null pointer
update README
```

**Input** (plain message):
```
improve error messages
add tests
```

**Output** (unchanged):
```
improve error messages
add tests
```

**Validation**: Minimal - accepts any non-empty message

---

### corporate

Formal enterprise style with categorization. Suitable for large organizations with strict documentation requirements.

**Format**: `[SCOPE] Category: Description`

**Category Mapping**:
- `feat` → "Feature"
- `fix` → "Defect Fix"
- `docs` → "Documentation"
- `refactor` → "Code Improvement"
- `test` → "Test Enhancement"
- `chore` → "Maintenance"
- `perf` → "Performance Enhancement"
- `style` → "Code Style"

**Input** (conventional format):
```
feat(auth): add JWT support
fix(api): resolve timeout
docs: update deployment guide
perf: optimize queries
```

**Output** (corporate style):
```
[AUTH] Feature: Add JWT support
[API] Defect Fix: Resolve timeout
Documentation: Update deployment guide
Performance Enhancement: Optimize queries
```

**Note**: Description is automatically capitalized. Scopes are uppercased and put in brackets.

**Validation**: Accepts conventional format as input

---

## Attribution Settings

Control commit attribution footers via CLAUDE.md:

```markdown
Commit attribution: none
```

**Options**:
- `none` (default) - Remove all attribution footers
- `claude` - Keep Claude Code attribution
- `custom` - Use custom attribution (define in CLAUDE.md)

**Example Footers Removed When `attribution: none`**:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Style Selection Examples

### Example 1: User-Wide Pirate

```markdown
# ~/CLAUDE.md
Commit style: pirate
Commit attribution: none
```

All repositories use pirate style unless overridden.

### Example 2: Project-Specific Override

```markdown
# ~/CLAUDE.md (user-wide)
Commit style: pirate
Commit attribution: none

# ~/work-project/CLAUDE.local.md (project-specific)
Commit style: conventional
Commit attribution: none
```

Result: Work project uses conventional, personal projects use pirate.

### Example 3: Corporate with Attribution

```markdown
# ~/work-project/CLAUDE.local.md
Commit style: corporate
Commit attribution: claude
```

Result: Formal commits with Claude attribution preserved.

### Example 4: Emoji for Visual Clarity

```markdown
# ~/fun-project/CLAUDE.local.md
Commit style: emoji
Commit attribution: none
```

Result: Visual emoji prefixes, no attribution.

---

## Validation Rules by Style

| Style        | Validation                                      |
|--------------|-------------------------------------------------|
| conventional | Strict - must match `type(scope?): message`     |
| pirate       | Accepts conventional input                      |
| snarky       | Accepts conventional input                      |
| emoji        | Accepts conventional input                      |
| minimal      | Minimal - any non-empty message                 |
| corporate    | Accepts conventional input                      |

**Note**: All styles except `conventional` and `minimal` expect conventional format as input and transform it.

---

## Best Practices

1. **Use conventional format as input** - Even with other styles, write messages in conventional format. The skill will transform them.

2. **Be consistent per project** - Use CLAUDE.local.md to enforce project-specific styles.

3. **Choose style based on context**:
   - **conventional**: Open source, professional projects
   - **pirate**: Fun projects, team morale
   - **snarky**: Internal tools, debugging sessions
   - **emoji**: Visual learners, quick scanning
   - **minimal**: Personal projects, rapid prototyping
   - **corporate**: Enterprise, compliance-heavy environments

4. **Attribution**:
   - **none**: Most cases (default)
   - **claude**: When showcasing AI-assisted development
   - **custom**: When specific attribution required

---

## Creating Custom Styles

To add a custom style, modify `lib/style-engine.zsh`:

1. Add case in `apply_commit_style()` function
2. Create transformation function (e.g., `transform_to_mystyle()`)
3. Update SKILL.md and this document

**Example custom style** (zombie):
```zsh
transform_to_zombie() {
    local message=$1
    # Transformation logic
    echo "Braaaains... ${message}... *gurgle*"
}
```

---

## Troubleshooting

### "Invalid commit message for style: conventional"

You're using conventional style but message doesn't follow the format.

**Fix**: Use `type(scope?): message` format.

### Style not being applied

1. Check CLAUDE.md/CLAUDE.local.md for typos
2. Verify format: `Commit style: stylename` (case-sensitive stylename)
3. Ensure file is in correct location (~ or project root)

### Attribution still appearing

1. Check `Commit attribution:` setting
2. Verify it's set to `none`
3. Check CLAUDE.local.md doesn't override

---

## Related Documentation

- `SKILL.md` - Main skill documentation
- `references/safety-protocol.md` - Git safety rules
