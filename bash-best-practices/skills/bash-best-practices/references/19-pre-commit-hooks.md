# Pre-Commit Hooks

Automate Bash script validation before commits using pre-commit hooks.

## Using pre-commit Framework

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Or via homebrew
brew install pre-commit
```

### Configuration

Create `.pre-commit-config.yaml` in repository root:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.9.0
    hooks:
      - id: shellcheck
        args: ['--severity=warning']

  - repo: https://github.com/jumanjihouse/pre-commit-hooks
    rev: 3.0.0
    hooks:
      - id: shellcheck
        args: ['--format=gcc']
      - id: script-must-have-extension
      - id: script-must-not-have-extension

  - repo: local
    hooks:
      - id: bash-lint-and-index
        name: Bash Lint and Index
        entry: bash bash-best-practices/scripts/lint-and-index.sh --path
        language: system
        files: \.sh$
        pass_filenames: false

      - id: bash-version-check
        name: Check Bash Version Requirements
        entry: bash scripts/check-bash-version.sh
        language: system
        files: \.sh$
```

### Install Hooks

```bash
# Install hooks in repository
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## Git Native Hooks

### Basic ShellCheck Hook

Create `.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Running ShellCheck on modified scripts..."

# Get staged .sh files
mapfile -t staged_files < <(git diff --cached --name-only --diff-filter=ACM | grep '\.sh$' || true)

if [[ ${#staged_files[@]} -eq 0 ]]; then
    echo "No shell scripts to check"
    exit 0
fi

# Run ShellCheck
failed=0
for file in "${staged_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "Checking: $file"
        if ! shellcheck --severity=warning "$file"; then
            failed=1
        fi
    fi
done

if [[ $failed -eq 1 ]]; then
    echo ""
    echo "❌ ShellCheck found issues. Fix them before committing."
    echo "To skip this check (not recommended): git commit --no-verify"
    exit 1
fi

echo "✅ All scripts passed ShellCheck"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

### Advanced Hook with Auto-Fix

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(git rev-parse --show-toplevel)"

run_shellcheck() {
    local files=("$@")
    local failed=0

    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            echo "📝 Checking: $file"

            # Try to auto-fix
            if ! shellcheck --format=diff "$file" > /tmp/shellcheck.diff; then
                if [[ -s /tmp/shellcheck.diff ]]; then
                    echo "🔧 Applying auto-fixes..."
                    patch -p1 < /tmp/shellcheck.diff
                    git add "$file"
                else
                    echo "⚠️  Cannot auto-fix: $file"
                    shellcheck "$file"
                    failed=1
                fi
            fi
        fi
    done

    return $failed
}

regenerate_function_index() {
    if [[ -f "$REPO_ROOT/bash-best-practices/scripts/analyze-shell-functions.sh" ]]; then
        echo "🔄 Regenerating function index..."
        bash "$REPO_ROOT/bash-best-practices/scripts/analyze-shell-functions.sh" \
            --path "$REPO_ROOT/scripts" \
            --output "$REPO_ROOT/extract.json"

        # Stage the updated index
        git add "$REPO_ROOT/extract.json"
    fi
}

main() {
    echo "🎣 Running pre-commit hooks..."

    # Get staged shell files
    mapfile -t staged_files < <(git diff --cached --name-only --diff-filter=ACM | grep '\.sh$' || true)

    if [[ ${#staged_files[@]} -eq 0 ]]; then
        echo "✓ No shell scripts to check"
        exit 0
    fi

    # Change to repo root
    cd "$REPO_ROOT"

    # Run ShellCheck
    if ! run_shellcheck "${staged_files[@]}"; then
        echo ""
        echo "❌ ShellCheck found unfixable issues"
        echo "Fix them manually or skip with: git commit --no-verify"
        exit 1
    fi

    # Regenerate function index
    regenerate_function_index

    echo "✅ All checks passed"
}

main "$@"
```

## Husky Integration

For Node.js projects, use Husky:

### Installation

```bash
npm install --save-dev husky
npx husky install
npm pkg set scripts.prepare="husky install"
```

### Add Hook

```bash
npx husky add .husky/pre-commit "bash scripts/pre-commit-checks.sh"
```

Create `scripts/pre-commit-checks.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Running pre-commit checks..."

# Run ShellCheck on staged files
mapfile -t staged_sh_files < <(git diff --cached --name-only --diff-filter=ACM | grep '\.sh$' || true)

if [[ ${#staged_sh_files[@]} -gt 0 ]]; then
    shellcheck --severity=warning "${staged_sh_files[@]}"
fi

# Run lint-and-index
if [[ -f bash-best-practices/scripts/lint-and-index.sh ]]; then
    bash bash-best-practices/scripts/lint-and-index.sh --path ./scripts
fi

echo "✅ Pre-commit checks passed"
```

## Custom Hook: Bash Version Enforcement

Create `scripts/check-bash-version.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

check_version_requirement() {
    local file="$1"
    local has_version_check=false
    local uses_bash4_features=false

    # Check for version check
    if grep -q 'BASH_VERSINFO' "$file"; then
        has_version_check=true
    fi

    # Check for Bash 4+ features
    if grep -Eq '(mapfile|readarray|declare -A|\*\*)' "$file"; then
        uses_bash4_features=true
    fi

    if [[ "$uses_bash4_features" == true ]] && [[ "$has_version_check" == false ]]; then
        echo "⚠️  $file uses Bash 4+ features but lacks version check"
        return 1
    fi

    return 0
}

main() {
    local failed=0

    # Check staged shell files
    mapfile -t staged_files < <(git diff --cached --name-only --diff-filter=ACM | grep '\.sh$' || true)

    for file in "${staged_files[@]}"; do
        if [[ -f "$file" ]]; then
            if ! check_version_requirement "$file"; then
                failed=1
            fi
        fi
    done

    if [[ $failed -eq 1 ]]; then
        echo ""
        echo "Add this to scripts using Bash 4+ features:"
        cat << 'EOF'

if [[ "${BASH_VERSINFO[0]}" -lt 4 ]]; then
    echo "Error: Bash 4.0+ required" >&2
    exit 1
fi
EOF
        return 1
    fi

    return 0
}

main "$@"
```

## Hook Template with Multiple Checks

Complete pre-commit hook template:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Configuration
readonly REPO_ROOT="$(git rev-parse --show-toplevel)"
readonly SEVERITY="warning"
readonly AUTO_FIX=true

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}✓${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $*"
}

log_error() {
    echo -e "${RED}✗${NC} $*"
}

run_shellcheck() {
    local files=("$@")

    if [[ ${#files[@]} -eq 0 ]]; then
        return 0
    fi

    log_info "Running ShellCheck..."

    if shellcheck --severity="$SEVERITY" "${files[@]}"; then
        log_info "ShellCheck passed"
        return 0
    else
        log_error "ShellCheck failed"
        return 1
    fi
}

check_shebang() {
    local files=("$@")
    local failed=0

    log_info "Checking shebangs..."

    for file in "${files[@]}"; do
        if [[ -x "$file" ]] && ! head -1 "$file" | grep -q '^#!/'; then
            log_error "$file is executable but missing shebang"
            failed=1
        fi

        if head -1 "$file" | grep -q '^#!/bin/bash$'; then
            log_warn "$file uses #!/bin/bash (prefer #!/usr/bin/env bash)"
        fi
    done

    return $failed
}

check_strict_mode() {
    local files=("$@")
    local failed=0

    log_info "Checking strict mode..."

    for file in "${files[@]}"; do
        if ! grep -q 'set -euo pipefail' "$file" && ! grep -q 'set -e' "$file"; then
            log_error "$file missing strict mode (set -euo pipefail)"
            failed=1
        fi
    done

    return $failed
}

regenerate_index() {
    local analyzer="$REPO_ROOT/bash-best-practices/scripts/analyze-shell-functions.sh"

    if [[ ! -f "$analyzer" ]]; then
        return 0
    fi

    log_info "Regenerating function index..."

    if bash "$analyzer" --path "$REPO_ROOT/scripts" --output "$REPO_ROOT/extract.json" 2>/dev/null; then
        git add "$REPO_ROOT/extract.json"
        log_info "Function index updated"
    fi
}

main() {
    echo "🎣 Pre-commit hooks"
    echo ""

    # Get staged shell files
    mapfile -t staged_files < <(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(sh|bash)$' || true)

    if [[ ${#staged_files[@]} -eq 0 ]]; then
        log_info "No shell scripts to check"
        exit 0
    fi

    cd "$REPO_ROOT"

    local exit_code=0

    # Run checks
    run_shellcheck "${staged_files[@]}" || exit_code=1
    check_shebang "${staged_files[@]}" || exit_code=1
    check_strict_mode "${staged_files[@]}" || exit_code=1

    # Regenerate index (non-blocking)
    regenerate_index

    echo ""
    if [[ $exit_code -eq 0 ]]; then
        log_info "All pre-commit checks passed"
    else
        log_error "Some checks failed"
        echo ""
        echo "To skip checks (not recommended):"
        echo "  git commit --no-verify"
    fi

    exit $exit_code
}

main "$@"
```

## Sharing Hooks with Team

### Method 1: Core.hooksPath

```bash
# Store hooks in repository
mkdir -p .githooks
mv .git/hooks/pre-commit .githooks/

# Configure Git
git config core.hooksPath .githooks

# Share in README
echo "Run: git config core.hooksPath .githooks" >> README.md
```

### Method 2: Setup Script

Create `scripts/setup-hooks.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly REPO_ROOT="$(git rev-parse --show-toplevel)"
readonly HOOKS_DIR="$REPO_ROOT/.githooks"
readonly GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

install_hooks() {
    if [[ ! -d "$HOOKS_DIR" ]]; then
        echo "Error: Hooks directory not found: $HOOKS_DIR" >&2
        return 1
    fi

    for hook in "$HOOKS_DIR"/*; do
        local hook_name
        hook_name="$(basename "$hook")"
        local target="$GIT_HOOKS_DIR/$hook_name"

        echo "Installing hook: $hook_name"
        cp "$hook" "$target"
        chmod +x "$target"
    done

    echo "✅ Hooks installed successfully"
}

install_hooks
```

Run during setup:
```bash
bash scripts/setup-hooks.sh
```

## Best Practices

1. **Keep hooks fast** - Run only essential checks (< 5 seconds)
2. **Auto-fix when possible** - Don't block developers unnecessarily
3. **Provide skip option** - Allow `git commit --no-verify` for emergencies
4. **Share hooks** - Use core.hooksPath or pre-commit framework
5. **Test hooks** - Ensure they work on all team members' systems

## Related References

- [09-shellcheck-integration.md](09-shellcheck-integration.md) - ShellCheck configuration
- [18-ci-cd-integration.md](18-ci-cd-integration.md) - CI/CD pipelines
- [11-development-environment.md](11-development-environment.md) - Development setup
