# Tool Selection - When to Use Bash (and When Not To)

Guide for choosing the right tool for the job.

## Philosophy

**Core principle**: Use the simplest tool that reliably solves the problem.

Bash is excellent for **orchestration and automation**, but struggles with **data processing and computation**. Choose tools based on the primary task, not familiarity.

## Decision Matrix

### Use Bash When

| Task Category | Examples | Why Bash Works |
|---------------|----------|----------------|
| **File operations** | Copy, move, archive, permissions | Native file handling, `cp`, `mv`, `chmod` |
| **Process management** | Start/stop services, monitor processes | Direct access to `systemctl`, `ps`, `kill` |
| **Command orchestration** | Chaining tools, pipelines | Built for composition: `cmd1 | cmd2` |
| **Environment setup** | PATH manipulation, exports | Native shell environment control |
| **Quick automation** | One-time tasks, prototypes | Rapid iteration, no compilation |
| **CI/CD pipelines** | Build, test, deploy scripts | Standard in CI environments |

### Use Alternative Tools When

| Task Category | Better Tool | Why | Example Use Case |
|---------------|-------------|-----|------------------|
| **Complex text processing** | `awk`, `sed`, `perl` | Pattern matching, field extraction | Parse logs, transform CSV |
| **JSON manipulation** | `jq` | Query language, type safety | API responses, config files |
| **YAML processing** | `yq` | Schema-aware parsing | Kubernetes manifests, CI configs |
| **XML/HTML parsing** | `xmlstarlet`, `pup`, Python | DOM traversal, XPath | Web scraping, config parsing |
| **Heavy computation** | Python, Go | Math libraries, performance | Data analysis, algorithms |
| **Business logic** | Python, Ruby | OOP, testing frameworks | Multi-step workflows, validation |
| **Type safety** | Go, Rust, TypeScript | Compile-time checks | Production systems, APIs |
| **Performance-critical** | Go, Rust, C | Native compilation | High-throughput, low-latency |
| **GUI applications** | Python (Tkinter), Electron | UI frameworks | Desktop apps, dashboards |
| **Database operations** | SQL, Python (SQLAlchemy) | Transactions, ORM | Complex queries, migrations |

## Detailed Scenarios

### Scenario 1: Text Processing

#### When Bash is Sufficient

```bash
# Simple pattern matching and extraction
grep "ERROR" /var/log/app.log | tail -n 10

# Basic text transformation
cat file.txt | tr '[:lower:]' '[:upper:]'

# Line counting and filtering
wc -l < file.txt
```

#### When to Use awk/sed/perl

```bash
# ❌ DON'T: Complex Bash logic
while IFS=',' read -r name age city; do
    if [[ $age -gt 30 ]]; then
        echo "$name lives in $city"
    fi
done < data.csv

# ✅ DO: Use awk for field processing
awk -F',' '$2 > 30 { print $1 " lives in " $3 }' data.csv

# ✅ DO: Use sed for complex substitutions
sed -E 's/([0-9]{3})-([0-9]{3})-([0-9]{4})/(\1) \2-\3/g' phone.txt
```

### Scenario 2: Structured Data (JSON/YAML)

#### When Bash Struggles

```bash
# ❌ WRONG: Parsing JSON with grep/sed (brittle, breaks on formatting)
api_response='{"user":{"name":"Alice","age":30}}'
name=$(echo "$api_response" | grep -oP '"name":"\K[^"]+')  # Fragile!

# ❌ WRONG: Manual JSON construction (escaping nightmare)
json="{\"name\":\"$user\",\"status\":\"$status\"}"  # Fails with quotes in variables
```

#### When to Use jq

```bash
# ✅ CORRECT: Use jq for JSON parsing
name=$(jq -r '.user.name' response.json)

# ✅ CORRECT: Safe JSON construction
jq -n --arg name "$user" --arg status "$status" '{name: $name, status: $status}'

# ✅ CORRECT: Complex transformations
jq '.users[] | select(.age > 30) | .name' users.json
```

#### When to Use yq

```bash
# ✅ CORRECT: Parse Kubernetes manifests
kubectl_version=$(yq '.spec.containers[0].image' deployment.yaml)

# ✅ CORRECT: Modify YAML in place
yq -i '.metadata.labels.env = "production"' config.yaml
```

### Scenario 3: Performance and Scale

#### Bash Performance Limits

```bash
# ❌ SLOW: Bash loops for large files (millions of lines)
while IFS= read -r line; do
    # Process line
done < huge_file.txt  # Takes minutes

# ❌ SLOW: String manipulation in loops
for file in *.log; do
    content=$(cat "$file")
    modified="${content//foo/bar}"  # Inefficient for large files
    echo "$modified" > "$file"
done
```

#### When to Use Compiled Languages

```bash
# ✅ FAST: Use awk for line-by-line processing
awk '{ gsub(/foo/, "bar"); print }' huge_file.txt > output.txt

# ✅ FAST: Use Python for complex operations
python3 -c "
import sys
for line in sys.stdin:
    # Complex logic
    print(line.strip())
" < huge_file.txt

# ✅ FASTEST: Use Go for performance-critical tasks
# go run process.go < huge_file.txt
```

### Scenario 4: Complex Logic and Testing

#### When Bash Gets Unwieldy

```bash
# ❌ COMPLEX: Business logic in Bash (hard to test, maintain)
validate_user() {
    local email="$1"
    local age="$2"

    # Email validation (regex gets messy)
    if ! [[ $email =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 1
    fi

    # Age validation
    if ! [[ $age =~ ^[0-9]+$ ]] || [[ $age -lt 18 ]] || [[ $age -gt 120 ]]; then
        return 1
    fi

    # More complex validation...
    # (Testing this is difficult)
}
```

#### When to Use Python/Ruby

```python
# ✅ BETTER: Python for complex validation (easy to test)
import re
from typing import Tuple

def validate_user(email: str, age: int) -> Tuple[bool, str]:
    """Validate user input with clear error messages."""

    # Email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    # Age validation
    if not 18 <= age <= 120:
        return False, f"Age must be between 18 and 120, got {age}"

    return True, "Valid"

# Easy to unit test with pytest
def test_validate_user():
    assert validate_user("alice@example.com", 25)[0] == True
    assert validate_user("invalid", 25)[0] == False
    assert validate_user("alice@example.com", 15)[0] == False
```

## Hybrid Approaches

Often, the best solution combines Bash with specialized tools:

### Pattern 1: Bash for Orchestration, Specialized Tools for Processing

```bash
#!/usr/bin/env bash
set -euo pipefail

# Bash handles orchestration
readonly LOG_DIR="/var/log/app"
readonly OUTPUT_DIR="/tmp/reports"

echo "Generating reports..."

# jq for JSON processing
jq -r '.[] | select(.level == "ERROR") | .message' "$LOG_DIR/app.json" > "$OUTPUT_DIR/errors.txt"

# awk for CSV processing
awk -F',' '$3 > 100 { print $1, $2 }' "$LOG_DIR/metrics.csv" > "$OUTPUT_DIR/high_metrics.txt"

# Python for complex analysis
python3 analyze.py "$OUTPUT_DIR/errors.txt" > "$OUTPUT_DIR/analysis.json"

echo "Reports generated in $OUTPUT_DIR"
```

### Pattern 2: Python for Logic, Bash for System Integration

```bash
#!/usr/bin/env bash
set -euo pipefail

# Bash handles system tasks
systemctl stop myapp
backup_db

# Python handles complex business logic
python3 migrate_database.py --config /etc/myapp/config.json

# Bash handles deployment
systemctl start myapp
verify_health_check
```

## Orchestration Scripts: When Long is OK

**Key insight**: A 500-line orchestration script is often better than splitting into 5 separate scripts with unclear dependencies.

### Good: Long Orchestration Script

```bash
#!/usr/bin/env bash
set -euo pipefail

# 500+ lines is fine when:
# 1. Each function is small and focused
# 2. Main logic is just calling functions in sequence
# 3. Each function calls external tools (not implementing complex logic)

setup_environment() {
    export DATABASE_URL="postgres://..."
    export API_KEY="$(cat /secrets/api.key)"
}

validate_prerequisites() {
    command -v jq >/dev/null || { echo "jq required" >&2; exit 1; }
    command -v kubectl >/dev/null || { echo "kubectl required" >&2; exit 1; }
}

backup_database() {
    pg_dump "$DATABASE_URL" | gzip > "backup-$(date +%Y%m%d).sql.gz"
}

deploy_to_kubernetes() {
    kubectl apply -f manifests/
    kubectl rollout status deployment/myapp
}

run_smoke_tests() {
    curl -f http://localhost:8080/health || return 1
    python3 tests/smoke_test.py
}

notify_team() {
    local status="$1"
    jq -n --arg status "$status" '{deployment: $status}' | \
        curl -X POST -H "Content-Type: application/json" \
             -d @- https://hooks.slack.com/...
}

main() {
    echo "Starting deployment..."

    setup_environment
    validate_prerequisites
    backup_database
    deploy_to_kubernetes
    run_smoke_tests && notify_team "success" || notify_team "failed"

    echo "Deployment complete"
}

main "$@"
```

**Why this works**:
- Main function is simple orchestration
- Each function does ONE thing
- Complex operations delegate to appropriate tools (jq, kubectl, Python)
- Easy to read and maintain despite being long
- Clear separation of concerns within a single file

### Bad: Complex Logic in Long Script

```bash
#!/usr/bin/env bash

# ❌ BAD: Implementing complex parsing/validation in Bash
process_api_response() {
    local response="$1"

    # 100+ lines of string manipulation
    # Nested loops and conditionals
    # Manual JSON parsing with sed/grep
    # Complex business logic
    # Difficult to test
}

validate_user_input() {
    # 80+ lines of validation logic
    # Multiple nested if statements
    # Complex regex patterns
    # No clear error messages
}

# More complex functions...
# (This should be Python/Ruby)
```

**Why this fails**:
- Individual functions are complex
- Implementing business logic in Bash
- Hard to test
- Better served by a language with proper data structures

### Guidelines for Orchestration Scripts

**Length is OK when**:
- Script orchestrates multiple tools/services
- Each function is < 50 lines
- Functions mostly call external commands
- Clear, linear flow
- Well-commented sections

**Split into separate scripts when**:
- Script serves multiple distinct purposes
- Functions could be reused independently
- Different scripts run in different contexts (CI vs production)
- Clear module boundaries exist

**Use Python/Ruby instead when**:
- Individual functions need complex logic
- Need data structures beyond arrays
- Implementing algorithms or business rules
- Heavy testing requirements

## Decision Checklist

When deciding between Bash and alternatives, ask:

1. **Data processing complexity**
   - [ ] Simple filtering/grep → Bash is fine
   - [ ] Multi-field extraction/transformation → Consider `awk`
   - [ ] JSON/XML/YAML → Use `jq`/`yq`/`xmlstarlet`

2. **Logic complexity** (focus on complexity, not line count)
   - [ ] Orchestration (calling tools sequentially) → Bash is fine, even if long
   - [ ] Simple functions (< 50 lines each) → Bash is fine
   - [ ] Complex conditionals/nested loops → Consider Python
   - [ ] Needs data structures beyond arrays → Use Python/Ruby
   - [ ] Implementing business logic → Use Python/Ruby

3. **Performance requirements**
   - [ ] Small files (< 10MB), quick tasks → Bash is fine
   - [ ] Large files (> 100MB) → Use `awk` or compiled language
   - [ ] High throughput/low latency → Use Go/Rust

4. **Testing requirements**
   - [ ] Simple smoke tests → Bash is fine
   - [ ] Unit tests, mocking → Use Python/Go with test frameworks

5. **Portability requirements**
   - [ ] POSIX systems only → Bash is fine
   - [ ] Windows support needed → PowerShell or Python
   - [ ] Minimal dependencies → Bash (available everywhere)

6. **Maintenance expectations**
   - [ ] One-time script → Bash is fine
   - [ ] Long-term maintenance → Consider type-safe languages
   - [ ] Team collaboration → Use well-known language (Python, Go)

## Common Anti-Patterns

### Anti-Pattern 1: Reinventing jq in Bash

```bash
# ❌ DON'T: Parse JSON with string manipulation
json_value=$(echo "$response" | sed 's/.*"key":"\([^"]*\)".*/\1/')

# ✅ DO: Use jq
json_value=$(echo "$response" | jq -r '.key')
```

### Anti-Pattern 2: Complex Math in Bash

```bash
# ❌ DON'T: Floating-point math in Bash (doesn't support it natively)
result=$(echo "scale=2; $a / $b" | bc)  # External dependency, slow

# ✅ DO: Use Python/awk for math
result=$(python3 -c "print($a / $b)")
result=$(awk "BEGIN { print $a / $b }")
```

### Anti-Pattern 3: Parsing HTML/XML with Regex

```bash
# ❌ DON'T: Parse HTML with grep/sed (breaks on edge cases)
title=$(curl -s "$url" | grep -oP '<title>\K[^<]+')

# ✅ DO: Use proper parser
title=$(curl -s "$url" | pup 'title text{}')
title=$(curl -s "$url" | xmlstarlet sel -t -v '//title')
```

### Anti-Pattern 4: Large Data Structures

```bash
# ❌ DON'T: Simulate dictionaries with arrays (ugly, error-prone)
declare -A users
users["alice"]="30"
users["bob"]="25"
# Gets messy quickly...

# ✅ DO: Use Python for complex data structures
python3 -c "
users = {'alice': 30, 'bob': 25}
for name, age in users.items():
    if age > 28:
        print(f'{name}: {age}')
"
```

## Tooling Recommendations

### Always Available in Bash Scripts

- `grep`, `sed`, `awk` - Text processing
- `find`, `xargs` - File operations
- `curl`, `wget` - HTTP requests
- `date`, `sleep` - Time operations
- `tee`, `cat`, `head`, `tail` - Stream manipulation

### Install for Structured Data

- **jq** - JSON processor (must-have)
- **yq** - YAML processor (essential for DevOps)
- **xmlstarlet** - XML processor
- **pup** - HTML parser

### Install for Performance

- **parallel** - GNU parallel for task parallelization
- **ripgrep** (`rg`) - Faster grep
- **fd** - Faster find

### Language Alternatives

- **Python** - General-purpose, great stdlib, wide adoption
- **Go** - Performance, static typing, single binary
- **Rust** - Performance, memory safety
- **Ruby** - Scripting, readable syntax
- **Node.js** - JavaScript ecosystem, async I/O

## Summary

**Use Bash for**:
- System automation and orchestration (even 500+ line scripts are OK!)
- Gluing command-line tools together
- Quick scripts and prototypes
- CI/CD pipelines and build scripts
- Sequential workflows with simple, focused functions

**Use alternatives when**:
- Processing structured data (JSON/XML/YAML) → Use jq/yq
- Complex business logic or validation → Use Python/Ruby
- Performance is critical (large files, computation) → Use Go/Rust/awk
- Individual functions exceed 50 lines of complex logic → Use Python/Ruby
- Need type safety or comprehensive testing → Use Go/Rust/TypeScript

**Key principle**: Focus on **complexity, not line count**. A 500-line orchestration script with simple functions is better than a 100-line script implementing complex parsing logic.

**Remember**: The best solution often combines Bash orchestration with specialized tools for processing. Don't force Bash to do everything—use it as the conductor, not the entire orchestra.
