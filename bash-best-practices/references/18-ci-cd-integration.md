# CI/CD Integration

Integrate Bash linting and validation into continuous integration pipelines.

## GitHub Actions

### Basic ShellCheck Workflow

Create `.github/workflows/shellcheck.yml`:

```yaml
name: ShellCheck

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  shellcheck:
    name: ShellCheck Validation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run ShellCheck
        uses: ludeeus/action-shellcheck@master
        with:
          severity: warning
          scandir: './scripts'
          ignore_paths: 'node_modules dist'
```

### Advanced Workflow with Caching

```yaml
name: Bash Validation

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    name: Validate Bash Scripts
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Cache ShellCheck
        uses: actions/cache@v3
        with:
          path: ~/.local/bin/shellcheck
          key: ${{ runner.os }}-shellcheck-0.9.0

      - name: Install ShellCheck
        run: |
          if [ ! -f ~/.local/bin/shellcheck ]; then
            wget -qO- "https://github.com/koalaman/shellcheck/releases/download/v0.9.0/shellcheck-v0.9.0.linux.x86_64.tar.xz" | tar -xJv
            mkdir -p ~/.local/bin
            mv "shellcheck-v0.9.0/shellcheck" ~/.local/bin/
          fi
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Run ShellCheck
        run: |
          find . -type f -name "*.sh" -o -name "*.bash" | xargs shellcheck --severity=warning

      - name: Check Bash version requirements
        run: |
          for script in $(find . -name "*.sh"); do
            if grep -q "BASH_VERSINFO" "$script"; then
              echo "✓ $script has version check"
            else
              echo "⚠ $script missing version check" >&2
            fi
          done

      - name: Generate function index
        run: |
          bash bash-best-practices/scripts/analyze-shell-functions.sh \
            --path ./scripts \
            --output extract.json

      - name: Upload extract.json artifact
        uses: actions/upload-artifact@v3
        with:
          name: function-index
          path: extract.json
```

## GitLab CI/CD

### Basic Pipeline

Create `.gitlab-ci.yml`:

```yaml
stages:
  - validate
  - test

shellcheck:
  stage: validate
  image: koalaman/shellcheck-alpine:stable
  script:
    - shellcheck --severity=warning scripts/*.sh
  only:
    - merge_requests
    - main

bash-lint:
  stage: validate
  image: bash:5.2
  before_script:
    - apk add --no-cache shellcheck jq
  script:
    - bash bash-best-practices/scripts/lint-and-index.sh --path ./scripts
  artifacts:
    paths:
      - extract.json
    expire_in: 1 week
  only:
    - merge_requests
    - main
```

### Advanced Pipeline with Parallel Jobs

```yaml
stages:
  - lint
  - analyze
  - test

.bash-base:
  image: bash:5.2
  before_script:
    - apk add --no-cache shellcheck jq findutils

shellcheck-strict:
  extends: .bash-base
  stage: lint
  script:
    - shellcheck --severity=error scripts/*.sh
  only:
    - merge_requests
    - main

shellcheck-warnings:
  extends: .bash-base
  stage: lint
  script:
    - shellcheck --severity=warning scripts/*.sh
  allow_failure: true
  only:
    - merge_requests
    - main

function-index:
  extends: .bash-base
  stage: analyze
  script:
    - bash bash-best-practices/scripts/analyze-shell-functions.sh --path ./scripts --output extract.json
    - jq '.index | length' extract.json
  artifacts:
    paths:
      - extract.json
    reports:
      dotenv: build.env
  only:
    - merge_requests
    - main

bash-tests:
  extends: .bash-base
  stage: test
  script:
    - bash tests/run-tests.sh
  coverage: '/Coverage: \d+\.\d+%/'
  only:
    - merge_requests
    - main
```

## Jenkins

### Jenkinsfile

```groovy
pipeline {
    agent any

    stages {
        stage('ShellCheck') {
            steps {
                sh '''
                    docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable \
                        shellcheck --severity=warning /mnt/scripts/*.sh
                '''
            }
        }

        stage('Generate Function Index') {
            steps {
                sh '''
                    bash bash-best-practices/scripts/analyze-shell-functions.sh \
                        --path ./scripts \
                        --output extract.json
                '''
                archiveArtifacts artifacts: 'extract.json', fingerprint: true
            }
        }

        stage('Run Tests') {
            steps {
                sh 'bash tests/run-tests.sh'
            }
        }
    }

    post {
        always {
            publishHTML([
                reportDir: 'reports',
                reportFiles: 'shellcheck.html',
                reportName: 'ShellCheck Report'
            ])
        }
    }
}
```

## CircleCI

### config.yml

```yaml
version: 2.1

executors:
  bash-executor:
    docker:
      - image: bash:5.2
    working_directory: ~/repo

jobs:
  shellcheck:
    executor: bash-executor
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: apk add --no-cache shellcheck jq
      - run:
          name: Run ShellCheck
          command: shellcheck --severity=warning scripts/*.sh
      - run:
          name: Lint and Index
          command: bash bash-best-practices/scripts/lint-and-index.sh --path ./scripts
      - store_artifacts:
          path: extract.json

  test:
    executor: bash-executor
    steps:
      - checkout
      - run:
          name: Run tests
          command: bash tests/run-tests.sh

workflows:
  version: 2
  build-and-test:
    jobs:
      - shellcheck
      - test:
          requires:
            - shellcheck
```

## Travis CI

### .travis.yml

```yaml
language: bash

addons:
  apt:
    packages:
      - shellcheck
      - jq

script:
  - shellcheck --severity=warning scripts/*.sh
  - bash bash-best-practices/scripts/lint-and-index.sh --path ./scripts
  - bash tests/run-tests.sh

after_success:
  - cat extract.json | jq '.index | length'
```

## Azure Pipelines

### azure-pipelines.yml

```yaml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UseNode@1
    inputs:
      version: '18.x'

  - script: |
      sudo apt-get update
      sudo apt-get install -y shellcheck jq
    displayName: 'Install dependencies'

  - script: |
      shellcheck --severity=warning scripts/*.sh
    displayName: 'Run ShellCheck'

  - script: |
      bash bash-best-practices/scripts/analyze-shell-functions.sh \
        --path ./scripts \
        --output extract.json
    displayName: 'Generate function index'

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: 'extract.json'
      artifactName: 'function-index'
```

## Custom ShellCheck Reporter

Create a script to format ShellCheck output for CI:

```bash
#!/usr/bin/env bash
set -euo pipefail

# ci-shellcheck.sh - Format ShellCheck for CI/CD
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

main() {
    local exit_code=0
    local total_issues=0

    echo "🔍 Running ShellCheck..."
    echo ""

    # Find all shell scripts
    mapfile -t scripts < <(find . -type f \( -name "*.sh" -o -name "*.bash" \) 2>/dev/null)

    for script in "${scripts[@]}"; do
        if ! shellcheck --format=gcc "$script"; then
            exit_code=1
            total_issues=$((total_issues + 1))
        fi
    done

    echo ""
    if [[ $exit_code -eq 0 ]]; then
        echo "✅ All scripts passed ShellCheck"
    else
        echo "❌ $total_issues script(s) failed ShellCheck"
    fi

    return $exit_code
}

main "$@"
```

## Best Practices for CI/CD

### 1. Fail Fast
Run linting before tests to catch syntax errors early:
```yaml
stages:
  - lint      # Fast, fails early
  - test      # Slower, runs only if lint passes
  - deploy
```

### 2. Cache Dependencies
Cache ShellCheck installation to speed up builds:
```yaml
- name: Cache ShellCheck
  uses: actions/cache@v3
  with:
    path: ~/.local/bin/shellcheck
    key: shellcheck-v0.9.0
```

### 3. Parallel Jobs
Run multiple checks in parallel:
```yaml
jobs:
  shellcheck:
    # ...
  function-analysis:
    # ...
  # Run simultaneously
```

### 4. Artifacts
Save analysis results for later use:
```yaml
- store_artifacts:
    path: extract.json
    destination: function-index
```

### 5. Required Checks
Make ShellCheck a required status check in pull requests.

## Related References

- [09-shellcheck-integration.md](09-shellcheck-integration.md) - ShellCheck usage
- [11-development-environment.md](11-development-environment.md) - Local setup
- [19-pre-commit-hooks.md](19-pre-commit-hooks.md) - Pre-commit integration
