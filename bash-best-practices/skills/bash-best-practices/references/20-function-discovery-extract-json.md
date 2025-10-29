# Function Discovery with extract.json

Comprehensive guide for using extract.json for efficient function discovery in large shell codebases (100+ functions).

## Table of Contents

- [Overview](#overview)
- [When to Use extract.json](#when-to-use-extractjson)
- [Setup and Location](#setup-and-location)
- [Generating extract.json](#generating-extractjson)
- [Navigating with jq](#navigating-with-jq)
- [Code Commenting Best Practices](#code-commenting-best-practices)
- [Integration Workflow](#integration-workflow)

## Overview

extract.json is a metadata file that enables semantic search and precise function extraction for shell codebases. It replaces grep-based discovery with structured queries.

### The Problem with grep

For codebases with 100+ functions across multiple files:

```bash
# Traditional grep approach
grep -r "backup" scripts/  # Returns hundreds of matches
grep -n "function.*backup" scripts/*.sh  # Still many false positives
# Then: manually parse output, guess line ranges, read wrong sections
# Result: 10+ tool calls, wasted context, imprecise results
```

### The extract.json Solution

```bash
# Generate once
uv run analyze-shell-functions.py --path scripts --output extract.json

# Semantic search - finds by purpose, not just name
jq '.index | to_entries[] | select(.value.purpose | test("backup"; "i")) | .key' extract.json

# Get exact Read parameters
jq '.index."create_backup" | {file_path: .file, offset: .start, limit: .size}' extract.json
# Result: 2-3 tool calls, precise extraction, zero wasted reads
```

## When to Use extract.json

### Use extract.json When:

1. **Large codebase**: 100+ functions across 5+ files
2. **Semantic search needed**: Find functions by purpose, not just name
3. **Category browsing**: Need to see all test/core/display functions
4. **Starting new session**: Fresh context, need to understand codebase structure
5. **Function not found**: grep fails, need better discovery

**Real-world examples:**
- PowerShell codebase: 708 functions
- macOS scripts: 326 functions across 19 files
- VM scripts: 125 functions across 20 files

### Don't Use extract.json When:

1. **Small codebase**: < 20 functions in 1-2 files (grep is fine)
2. **Known function name**: You already know exact name and file
3. **Simple scripts**: Single-purpose scripts without libraries

## Setup and Location

### Recommended Locations

Choose based on scope:

```bash
# Project-wide metadata (recommended for most projects)
/project-root/
├── scripts/
│   ├── backup.sh
│   ├── restore.sh
│   └── lib/
│       ├── config-functions.sh
│       └── network-functions.sh
└── extract.json          # ← Here (covers all scripts/)

# Multi-directory project
/project-root/
├── macos/
│   ├── scripts/
│   └── macos-extract.json    # ← macOS-specific
├── vm/
│   ├── scripts/
│   └── vm-extract.json       # ← VM-specific
└── windows/
    ├── scripts/
    └── windows-extract.json  # ← Windows-specific

# Monorepo with separate tools
/monorepo/
├── tools/
│   ├── deployment/
│   │   ├── scripts/
│   │   └── extract.json      # ← Per-tool metadata
│   └── monitoring/
│       ├── scripts/
│       └── extract.json
```

### .gitignore Considerations

**Option 1: Commit extract.json (recommended for stable codebases)**
```bash
# Pros: Shared across team, fast initial discovery
# Cons: Must regenerate on code changes
# Add to git
git add extract.json
```

**Option 2: Ignore extract.json (recommended for active development)**
```bash
# Pros: Always fresh, no merge conflicts
# Cons: Must generate on first use
# Add to .gitignore
echo "extract.json" >> .gitignore
```

**Hybrid approach:**
```bash
# Commit extract.json, regenerate in CI/CD or pre-commit
# Best of both worlds
```

## Generating extract.json

### First-Time Generation

```bash
# Navigate to project root
cd /path/to/project

# Generate for entire codebase
uv run path/to/analyze-shell-functions.py \
    --path ./scripts \
    --output extract.json

# Generate for multiple directories
uv run analyze-shell-functions.py --path ./macos --output macos-extract.json
uv run analyze-shell-functions.py --path ./vm --output vm-extract.json
```

### When to Regenerate

Regenerate after:

1. **Adding new functions** - New functions won't be discovered
2. **Modifying function signatures** - Parameters may have changed
3. **Refactoring** - Function names, locations, or purposes updated
4. **Changing comments** - Purpose extraction relies on function comments
5. **Function not found** - If search fails, code may be out of sync

**Quick regeneration check:**
```bash
# Count functions in codebase
grep -rh "^[[:space:]]*\(function\)\?[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*(" scripts/ | wc -l

# Count functions in extract.json
jq '.index | length' extract.json

# If numbers differ significantly, regenerate
```

### Performance

- **Small projects** (< 50 functions): < 1 second
- **Medium projects** (100-300 functions): 1-3 seconds
- **Large projects** (500+ functions): 3-5 seconds

Regeneration is fast enough for frequent updates.

## Navigating with jq

### Essential Query Patterns

#### 1. Semantic Search (Find by Purpose)

```bash
# Find all backup-related functions (even if "backup" not in name)
jq '.index | to_entries[] | select(.value.purpose | test("backup"; "i")) | .key' extract.json

# Find network/connection functions
jq '.index | to_entries[] | select(.value.purpose | test("network|connection"; "i")) | .key' extract.json

# Find database functions
jq '.index | to_entries[] | select(.value.purpose | test("database|postgres|sql"; "i")) | .key' extract.json
```

#### 2. Category Browsing

```bash
# List all categories
jq '.categories | keys' extract.json

# Get all test functions
jq '.categories.test[]' extract.json

# Get all core/data functions
jq '.categories.core[]' extract.json

# Get all display/UI functions
jq '.categories.display[]' extract.json

# Count functions per category
jq '.categories | to_entries[] | {category: .key, count: (.value | length)}' extract.json
```

#### 3. Extract Function for Reading

```bash
# Get Read tool parameters (THIS IS THE KEY PATTERN)
jq '.index."function_name" | {file_path: .file, offset: .start, limit: .size}' extract.json

# Output: {"file_path": "/full/path/script.sh", "offset": 42, "limit": 25}
# Use these values directly in Read tool

# Quick reference (file:line format)
jq -r '.quick_ref."function_name"' extract.json
# Output: "script.sh:42-67"
```

#### 4. Parameter Inspection

```bash
# Check function parameters before reading
jq '.index."function_name".params' extract.json
# Output: ["param1", "param2", "param3"]

# Find functions with specific parameter
jq '.index | to_entries[] | select(.value.params[] == "config_file") | .key' extract.json

# Find functions with many parameters (complex functions)
jq '.index | to_entries[] | select(.value.params | length > 3) | {key: .key, param_count: (.value.params | length)}' extract.json
```

#### 5. Combined Queries

```bash
# Find test functions that take parameters
jq '.index | to_entries[] | select(.value.category == "test" and (.value.params | length) > 0) | {key: .key, params: .value.params}' extract.json

# Find functions in specific file
jq '.index | to_entries[] | select(.value.file | contains("backup")) | .key' extract.json

# Find long functions (potential refactoring candidates)
jq '.index | to_entries[] | select(.value.size > 50) | {key: .key, size: .value.size, file: (.value.file | split("/") | last)}' extract.json
```

### Agent Workflow Integration

**Optimal pattern for agents:**

```bash
# Step 1: Semantic search
FUNCTIONS=$(jq '.index | to_entries[] | select(.value.purpose | test("backup"; "i")) | .key' extract.json)

# Step 2: Get extraction params for target function
PARAMS=$(jq '.index."create_backup" | {file_path: .file, offset: .start, limit: .size}' extract.json)

# Step 3: Use Read tool with exact parameters
# Read tool called with:
#   file_path: from PARAMS
#   offset: from PARAMS
#   limit: from PARAMS

# Result: Precise extraction in 2-3 tool calls
```

## Code Commenting Best Practices

The value of extract.json depends on good code comments. Follow these practices to maximize discoverability.

### Function-Level Comments

**Best Practice: Single-line descriptive comment immediately before function**

```bash
# Creates compressed backup of specified directory
backup_directory() {
    typeset directory="$1"
    # ... implementation
}

# Validates database connection and returns status
check_database_connection() {
    typeset host="$1"
    typeset port="$2"
    # ... implementation
}
```

**What Gets Extracted:**
```json
{
  "backup_directory": {
    "purpose": "Creates compressed backup of specified directory",
    ...
  },
  "check_database_connection": {
    "purpose": "Validates database connection and returns status",
    ...
  }
}
```

### Purpose Comment Guidelines

**✅ Good Purpose Comments:**

```bash
# Exports database to specified format (SQL, CSV, JSON)
export_database() { ... }

# Fetches JIRA ticket metadata and attachments
fetch_ticket_data() { ... }

# Synchronizes local branch with remote main branch
sync_branch() { ... }

# Tests network connectivity to VM and returns latency
test_vm_network() { ... }
```

**❌ Bad Purpose Comments:**

```bash
# TODO: Refactor this
export_database() { ... }

# Main function
main() { ... }

# ============================
# Backup Section
# ============================
backup_files() { ... }

# This exports the database
export_database() { ... }  # Too vague
```

### Commenting Style for Maximum Value

#### 1. Describe "What" and "Why", Not "How"

```bash
# ✅ GOOD - Describes intent and outcome
# Migrates backup folders to tar.gz format for better compression
migrate_backups() { ... }

# ❌ BAD - Describes implementation details
# Loops through backup folders and runs tar command
migrate_backups() { ... }
```

#### 2. Include Key Details

```bash
# ✅ GOOD - Specific about what it validates
# Validates JIRA ticket format (PROJECT-NUMBER) and checks if ticket exists
validate_ticket() { ... }

# ❌ BAD - Too generic
# Validates ticket
validate_ticket() { ... }
```

#### 3. Mention Return Values or Side Effects

```bash
# ✅ GOOD - Clear about behavior
# Checks if branch exists in git repository (returns 0 if found, 1 otherwise)
branch_exists() { ... }

# ✅ GOOD - Mentions side effects
# Creates git worktree and syncs configuration files from main repository
create_worktree() { ... }
```

#### 4. Multiple-Line Comments (When Needed)

```bash
# Analyzer uses the FIRST valid comment found, so structure carefully:

# Primary purpose: Performs incremental database backup with rotation
# NOTE: Requires PostgreSQL 12+ for WAL archiving
# TODO: Add support for MySQL
backup_database() { ... }
# Extracted: "Performs incremental database backup with rotation"

# ✅ Multi-line with continuation
# Performs incremental database backup with rotation.
# Automatically cleans up backups older than 30 days.
backup_database() { ... }
# Extracted: "Performs incremental database backup with rotation."
```

### Parameter Documentation

**In-function comments for parameter clarity:**

```bash
# Synchronizes branch with main and handles conflicts
sync_branch() {
    typeset branch_name="$1"      # Branch to synchronize
    typeset base_branch="$2"      # Base branch (usually 'main')
    typeset auto_resolve="$3"     # Auto-resolve conflicts (true/false)

    # ... implementation
}
```

**Extracted parameters:**
```json
{
  "sync_branch": {
    "params": ["branch_name", "base_branch", "auto_resolve"],
    "purpose": "Synchronizes branch with main and handles conflicts"
  }
}
```

### Category Optimization

Functions are automatically categorized by name patterns. Use consistent naming for better organization:

| Category | Naming Pattern | Examples |
|----------|---------------|----------|
| **display** | `show_*`, `display_*`, `write_*` | `show_help`, `display_status` |
| **core** | `get_*`, `set_*`, `update_*` | `get_config`, `set_option` |
| **test** | `test_*`, `check_*`, `validate_*` | `test_connection`, `validate_input` |
| **export** | `export_*`, `import_*`, `backup_*`, `restore_*` | `backup_database`, `export_logs` |
| **install** | `install_*`, `add_*`, `remove_*` | `install_package`, `remove_service` |
| **service** | `start_*`, `stop_*`, `restart_*`, `enable_*` | `start_server`, `restart_database` |
| **helper** | Everything else | `calculate_size`, `format_timestamp` |

**Name functions intentionally** to land in the right category for easier discovery.

## Integration Workflow

### Recommended Agent Workflow

```bash
# 1. Session start or when function discovery fails
uv run analyze-shell-functions.py --path scripts --output extract.json

# 2. Discover functions semantically
jq '.index | to_entries[] | select(.value.purpose | test("KEYWORD"; "i")) | .key' extract.json

# 3. Browse by category (optional)
jq '.categories.CATEGORY[]' extract.json

# 4. Get extraction parameters
jq '.index."function_name" | {file_path: .file, offset: .start, limit: .size}' extract.json

# 5. Use Read tool with exact parameters
# Read: file_path, offset, limit

# 6. Regenerate if function not found or after code changes
```

### Pre-commit Hook (Optional)

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Regenerate extract.json before each commit
if [[ -f "extract.json" ]]; then
    echo "Regenerating extract.json..."
    uv run scripts/analyze-shell-functions.py --path scripts --output extract.json
    git add extract.json
fi
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Generate extract.json
  run: |
    uv run scripts/analyze-shell-functions.py \
      --path scripts \
      --output extract.json

    # Optionally: Commit and push if changed
    git add extract.json
    git commit -m "chore: update function metadata" || true
```

## Summary

**Key Takeaways:**

1. **Use for large codebases** (100+ functions) - provides semantic search and precise extraction
2. **Location**: Project root or per-directory for multi-directory projects
3. **Regenerate frequently** - after code changes, especially new/modified functions
4. **Comment well** - purpose comments drive semantic search value
5. **Name intentionally** - function names determine category classification
6. **Navigate with jq** - structured queries >> grep for discovery
7. **Agent workflow** - Discover (jq) → Extract params (jq) → Read (precise)

**The ROI:** For 300+ function codebases, extract.json reduces function discovery from 10+ grep/read iterations to 2-3 precise queries, saving tokens and time.
