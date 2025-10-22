# Tool Integration Guide for Claude Code

How Claude Code discovers and analyzes Bash functions efficiently.

## Overview

Claude Code uses a **metadata-first** approach for Bash function discovery:
1. Generate `extract.json` with function metadata (one-time cost)
2. Query with `jq` for instant function discovery
3. Extract specific functions with Read tool using exact line numbers

This pattern is borrowed from `charly-server/developer-tools/Analyze-ShellFunctions.zsh`.

## Primary Tools

| Tool | Purpose | When Used |
|------|---------|-----------|
| **analyze-shell-functions.sh** | Generate function metadata | First encounter with codebase |
| **jq** | Query function metadata | Function discovery |
| **Read tool** | Extract specific functions | After discovery |
| **ShellCheck** | Lint and validate code | Always (after changes) |

## Complete Workflow

### Step 1: Generate Metadata (One-Time)

```bash
# When user asks to work with a Bash codebase
# Claude Code runs:
bash bash-best-practices/scripts/analyze-shell-functions.sh \
    --path ./project \
    --output extract.json

# Output: extract.json created
# ✅ Analysis complete: 47 function(s) found
# 📄 Output: extract.json
```

**What's in extract.json**:
```json
{
  "index": {
    "backup_database": {
      "file": "/path/to/backup.sh",
      "start": 42,
      "end": 67,
      "size": 26,
      "signature": "backup_database() {",
      "purpose": "Backs up database to specified location",
      "return_type": "int",
      "category": "export",
      "params": ["target_dir", "database_name"]
    },
    "restore_database": { ... }
  },
  "categories": {
    "export": ["backup_database", "backup_config"],
    "core": ["get_config", "set_config"]
  },
  "quick_ref": {
    "backup_database": "backup.sh:42-67"
  }
}
```

### Step 2: Discover Functions

**Scenario**: User asks "How do I backup the database?"

```bash
# Claude Code runs jq query for semantic search
jq '.index | to_entries[] | select(.value.purpose | test("backup"; "i")) | .key' extract.json

# Output:
# "backup_database"
# "backup_config"
# "restore_backup"
```

**Other discovery patterns**:

```bash
# Find by category
jq '.categories.export[]' extract.json

# Find by parameter name
jq '.index | to_entries[] | select(.value.params[] | test("database")) | .key' extract.json

# Find small functions (easier to understand)
jq '.index | to_entries[] | select(.value.size <= 20) | .key' extract.json

# Get quick reference
jq -r '.quick_ref."backup_database"' extract.json
# Output: backup.sh:42-67
```

### Step 3: Extract Function

**Get extraction parameters**:

```bash
# Claude Code runs:
jq '.index."backup_database" | {file_path: .file, offset: .start, limit: .size}' extract.json

# Output:
# {
#   "file_path": "/path/to/backup.sh",
#   "offset": 42,
#   "limit": 26
# }
```

**Use Read tool with exact parameters**:

```
Read(
    file_path="/path/to/backup.sh",
    offset=42,
    limit=26
)
```

**Result**: Exact function code, no extra context, token-efficient.

### Step 4: Validate with ShellCheck

```bash
# After making changes
shellcheck --format=json backup.sh | jq '.[] | select(.line >= 42 and .line <= 67)'

# Only show issues in the modified function
```

## Comparison: Old vs New Approach

### Old Approach: Grep + Read Full Files

```bash
# User: "Find the backup function"

# Step 1: Search for function
grep -rn "backup_database" .
# Output: ./scripts/backup.sh:42:backup_database() {
#         ./scripts/main.sh:15:    backup_database "$target"
#         ./tests/test-backup.sh:10:    test_backup_database

# Step 2: Read entire file to understand context
Read(file_path="./scripts/backup.sh")
# Problem: 500 lines loaded, only need 26

# Step 3: Search for related functions
grep -rn "backup" . | grep "^.*\.sh:[0-9]*:.*().*{$"
# Problem: Regex complexity, false positives

# Issues:
# - Multiple searches needed
# - Read entire files (token waste)
# - No semantic information (what does it do?)
# - Manual filtering required
```

### New Approach: Metadata + jq + Targeted Read

```bash
# User: "Find the backup function"

# Step 1: Semantic search (instant)
jq '.index | to_entries[] | select(.value.purpose | test("backup"; "i"))' extract.json
# Output: All backup-related functions with metadata

# Step 2: Get extraction params (instant)
jq '.index."backup_database" | {file_path: .file, offset: .start, limit: .size}' extract.json

# Step 3: Extract exact function
Read(file_path="./scripts/backup.sh", offset=42, limit=26)
# Result: Exactly 26 lines, the function itself

# Benefits:
# - Single jq query for discovery
# - Semantic search (by purpose, not just name)
# - Precise extraction (no wasted tokens)
# - Related functions visible immediately (same category)
```

## Real-World Examples

### Example 1: "Refactor all config functions"

```bash
# Find all config-related functions
jq '.categories.core | .[]' extract.json
# ["get_config", "set_config", "update_config", "validate_config"]

# Get details for all
jq '.index | to_entries[] | select(.value.category == "core")' extract.json

# Extract each one for review
for func in $(jq -r '.categories.core[]' extract.json); do
    params=$(jq ".index.\"$func\" | {file_path: .file, offset: .start, limit: .size}" extract.json)
    # Use Read tool with $params
done
```

### Example 2: "Find functions that might fail"

```bash
# Functions with many lines (complexity indicator)
jq '.index | to_entries[] | select(.value.size > 50) | {name: .key, size: .value.size}' extract.json

# Functions that return int (probably have error handling)
jq '.index | to_entries[] | select(.value.return_type == "int") | .key' extract.json
```

### Example 3: "Understand the test suite"

```bash
# All test functions
jq '.categories.test[]' extract.json

# Test function purposes
jq '.index | to_entries[] | select(.value.category == "test") | {name: .key, purpose: .value.purpose}' extract.json

# Small test functions (quick wins)
jq '.index | to_entries[] | select(.value.category == "test" and .value.size <= 15)' extract.json
```

## Integration with Other Tools

### ShellCheck Integration

```bash
# Run ShellCheck on specific function
func_file=$(jq -r '.index."my_function".file' extract.json)
func_start=$(jq -r '.index."my_function".start' extract.json)
func_end=$(jq -r '.index."my_function".end' extract.json)

shellcheck --format=json "$func_file" | \
    jq --argjson start "$func_start" --argjson end "$func_end" \
    '.[] | select(.line >= $start and .line <= $end)'
```

### Git Blame Integration

```bash
# Who wrote this function?
func_file=$(jq -r '.index."my_function".file' extract.json)
func_start=$(jq -r '.index."my_function".start' extract.json)
func_end=$(jq -r '.index."my_function".end' extract.json)

git blame -L "$func_start,$func_end" "$func_file"
```

## When to Regenerate Metadata

Regenerate `extract.json` when:

1. **Adding new functions**
   ```bash
   # Quick regeneration
   bash bash-best-practices/scripts/analyze-shell-functions.sh --path . --output extract.json
   ```

2. **Significant refactoring**
   - Function signatures changed
   - Functions renamed
   - Files reorganized

3. **Switching branches** (if function set differs)

4. **Periodically** (e.g., daily during active development)

**Automation idea**: Git hook to regenerate on checkout/commit.

## Performance Characteristics

| Operation | Old (Grep) | New (extract.json) | Speedup |
|-----------|------------|-------------------|---------|
| Find function by name | ~100ms | <10ms | 10x |
| Find by purpose | N/A (impossible) | <10ms | ∞ |
| Find by category | Manual grep + filter | <10ms | 100x+ |
| Extract function | Read full file | Read exact lines | 10-50x |
| List all functions | Slow grep regex | Instant jq | 100x+ |

**Token savings**: ~80% reduction (reading only needed functions vs entire files)

## Summary

### For Claude Code

**Primary workflow**:
1. Generate `extract.json` once (analyze-shell-functions.sh)
2. Query with `jq` for function discovery
3. Extract with Read tool using exact line numbers
4. Validate with ShellCheck

**DO use**:
- ✅ analyze-shell-functions.sh (metadata generation)
- ✅ jq (metadata querying)
- ✅ Read tool with offset/limit (precise extraction)
- ✅ ShellCheck (validation)

**DON'T use**:
- ❌ Grep for function discovery (slow, no semantics)
- ❌ Reading full files (token waste)
- ❌ tree-sitter CLI (overhead, no semantic metadata)
- ❌ bash-language-server (too complex for CLI)

### Pattern Origin

This pattern is adapted from:
- `charly-server/developer-tools/Analyze-ShellFunctions.zsh` (ZSH version)
- `charly-server/windows/developer-tools/Analyze-PowerShellFunctions.ps1` (PowerShell version)

Proven effective for agent-driven development workflows.
