# Development Environment Setup

Optional IDE integration for enhanced Bash development experience. These tools complement the Claude Code workflow but are not required.

## Overview

While Claude Code runs ShellCheck directly for validation, IDE integration provides real-time feedback during development. This setup is optional but recommended for enhanced productivity.

## Bash Language Server

The Bash Language Server provides IDE features like diagnostics, code completion, and documentation lookup.

### Installation

```bash
# Install via npm
npm install -g bash-language-server

# Verify installation
bash-language-server --version
```

### IDE Integration

**VS Code:**
- Install the "Bash IDE" extension
- Extension automatically uses bash-language-server if installed
- Provides real-time ShellCheck diagnostics

**Other IDEs:**
- Vim/Neovim: Use coc.nvim or native LSP
- Emacs: Use lsp-mode
- Sublime Text: Use LSP package

## VS Code Configuration

### Recommended Settings

Create or update `.vscode/settings.json`:

```json
{
  // Bash IDE extension
  "bashIde.shellcheckPath": "shellcheck",
  "bashIde.explainshellEndpoint": "https://explainshell.com/explain",

  // ShellCheck integration
  "shellcheck.enable": true,
  "shellcheck.executablePath": "shellcheck",
  "shellcheck.run": "onType",
  "shellcheck.useWorkspaceRootAsCwd": true,

  // File associations
  "files.associations": {
    "*.sh": "shellscript",
    "*.bash": "shellscript",
    ".shellcheckrc": "properties"
  },

  // Editor settings for shell scripts
  "[shellscript]": {
    "editor.tabSize": 2,
    "editor.insertSpaces": true,
    "editor.formatOnSave": false
  }
}
```

### Workspace Settings

For project-specific configuration:

```json
{
  "shellcheck.customArgs": [
    "--shell=bash",
    "--severity=warning"
  ],
  "shellcheck.exclude": [
    "SC1090",  // Can't follow non-constant source
    "SC1091"   // Not following sourced file
  ]
}
```

## ShellCheck Configuration File

Place `.shellcheckrc` in project root (copy from skill assets):

```bash
# Copy skill's shellcheckrc to project
cp bash-best-practices/assets/.shellcheckrc .shellcheckrc
```

This ensures IDE and command-line ShellCheck use the same rules.

## Git Integration

### Pre-Commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Find all .sh files being committed
mapfile -t files < <(git diff --cached --name-only --diff-filter=ACM | grep '\.sh$' || true)

if [[ ${#files[@]} -gt 0 ]]; then
    echo "Running ShellCheck on modified scripts..."

    if ! shellcheck "${files[@]}"; then
        echo "ShellCheck failed. Commit aborted."
        echo "Fix issues or use 'git commit --no-verify' to skip."
        exit 1
    fi

    echo "ShellCheck passed!"
fi

exit 0
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Pre-Push Hook

Create `.git/hooks/pre-push` for more comprehensive checks:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Running lint-and-index before push..."

if [[ -f bash-best-practices/scripts/lint-and-index.sh ]]; then
    bash bash-best-practices/scripts/lint-and-index.sh --path . --severity warning
else
    echo "Warning: lint-and-index.sh not found, running ShellCheck only"
    find . -name "*.sh" -exec shellcheck {} +
fi

echo "All checks passed!"
exit 0
```

## Makefile Integration

Create `Makefile` for common tasks:

```makefile
.PHONY: lint
lint:
	@echo "Running ShellCheck..."
	@shellcheck --severity=warning **/*.sh

.PHONY: lint-errors
lint-errors:
	@echo "Checking for errors only..."
	@shellcheck --severity=error **/*.sh

.PHONY: lint-and-index
lint-and-index:
	@echo "Running combined workflow..."
	@bash bash-best-practices/scripts/lint-and-index.sh --path .

.PHONY: analyze
analyze:
	@echo "Generating function metadata..."
	@bash bash-best-practices/scripts/analyze-shell-functions.sh --path . --output extract.json

.PHONY: check
check: lint-and-index
	@echo "All checks completed!"
```

Usage:

```bash
make lint              # Run ShellCheck
make lint-errors       # Check errors only
make lint-and-index    # Combined workflow
make analyze           # Generate extract.json
make check             # Full check
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/shellcheck.yml`:

```yaml
name: ShellCheck

on: [push, pull_request]

jobs:
  shellcheck:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Run ShellCheck
        uses: ludeeus/action-shellcheck@master
        with:
          severity: warning
          scandir: '.'
          format: gcc

      - name: Generate function index
        run: |
          bash bash-best-practices/scripts/analyze-shell-functions.sh \
            --path . \
            --output extract.json

      - name: Upload extract.json
        uses: actions/upload-artifact@v3
        with:
          name: function-index
          path: extract.json
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
shellcheck:
  image: koalaman/shellcheck-alpine:latest
  script:
    - shellcheck --severity=warning **/*.sh
  only:
    - merge_requests
    - main

analyze-functions:
  image: bash:latest
  script:
    - apk add --no-cache bash
    - bash bash-best-practices/scripts/analyze-shell-functions.sh --path . --output extract.json
  artifacts:
    paths:
      - extract.json
    expire_in: 1 week
```

## Editor-Specific Tips

### VS Code

**Keyboard shortcuts:**
- `F8` / `Shift+F8`: Navigate diagnostics
- `Ctrl+Space`: Trigger completion
- `Ctrl+Shift+I`: Format document

**Recommended extensions:**
- Bash IDE
- ShellCheck
- shell-format (for formatting)

### Vim/Neovim

**Using ALE (Asynchronous Lint Engine):**

```vim
" In .vimrc or init.vim
let g:ale_linters = {'sh': ['shellcheck', 'shell']}
let g:ale_sh_shellcheck_options = '--shell=bash'
let g:ale_fixers = {'sh': ['shfmt']}
```

**Using native LSP (Neovim 0.5+):**

```lua
-- In init.lua
require'lspconfig'.bashls.setup{
  filetypes = {"sh", "bash"}
}
```

### Emacs

**Using Flycheck:**

```elisp
;; In .emacs or init.el
(require 'flycheck)
(add-hook 'sh-mode-hook 'flycheck-mode)
(setq flycheck-shellcheck-follow-sources nil)
```

## Continuous Monitoring

### Watch Mode

Monitor files and run checks on changes:

```bash
# Using inotifywait (Linux)
while inotifywait -e modify,create *.sh; do
    clear
    bash bash-best-practices/scripts/lint-and-index.sh --path .
done

# Using fswatch (macOS)
fswatch -o *.sh | xargs -n1 -I{} bash -c \
    'clear && bash bash-best-practices/scripts/lint-and-index.sh --path .'
```

### Pre-Commit Framework

Use the pre-commit framework for more sophisticated hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.9.0
    hooks:
      - id: shellcheck
        args: ['--severity=warning']

  - repo: local
    hooks:
      - id: analyze-functions
        name: Analyze Shell Functions
        entry: bash bash-best-practices/scripts/analyze-shell-functions.sh --path . --output extract.json
        language: system
        pass_filenames: false
```

## Troubleshooting

### ShellCheck Not Found

```bash
# Verify installation
which shellcheck

# Install if missing (macOS)
brew install shellcheck

# Install if missing (Linux)
sudo apt-get install shellcheck  # Debian/Ubuntu
sudo dnf install shellcheck      # Fedora/RHEL
```

### Bash Language Server Issues

```bash
# Reinstall globally
npm uninstall -g bash-language-server
npm install -g bash-language-server

# Clear VS Code cache
rm -rf ~/.vscode/extensions/*bash*
```

### Performance Issues

If IDE feels slow with many shell scripts:

1. **Exclude directories** in VS Code settings:
   ```json
   {
     "files.exclude": {
       "**/node_modules": true,
       "**/vendor": true
     }
   }
   ```

2. **Disable real-time linting**:
   ```json
   {
     "shellcheck.run": "onSave"
   }
   ```

3. **Limit ShellCheck scope**:
   ```json
   {
     "shellcheck.useWorkspaceRootAsCwd": false
   }
   ```

## Summary

**Essential setup:**
- Install ShellCheck
- Configure editor for real-time feedback
- Add pre-commit hooks

**Optional but recommended:**
- Bash language server for IDE features
- Makefile for common tasks
- CI/CD integration for automated checks

**Remember:**
- IDE tools complement Claude Code workflow
- Claude Code always runs ShellCheck directly
- extract.json should be generated after changes
- Use lint-and-index.sh to keep everything synchronized
