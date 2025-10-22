# CI/CD Integration with ShellSpec

Complete guide to integrating ShellSpec tests into continuous integration pipelines.

## GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/test.yml

name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Install ShellSpec
        run: |
          curl -fsSL https://git.io/shellspec | sh -s -- -y
          sudo ln -s ${HOME}/.local/lib/shellspec/shellspec /usr/local/bin/shellspec

      - name: Run tests
        run: shellspec

      - name: Run tests with coverage
        run: |
          sudo apt-get update
          sudo apt-get install -y kcov
          shellspec --kcov

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/cobertura.xml
          fail_ci_if_error: true
```

### Matrix Testing (Multiple Bash Versions)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-20.04, ubuntu-22.04, macos-latest]
        bash-version: [4.4, 5.0, 5.1]

    steps:
      - uses: actions/checkout@v3

      - name: Install Bash ${{ matrix.bash-version }}
        run: |
          # Install specific Bash version
          # (implementation depends on OS)

      - name: Install ShellSpec
        run: curl -fsSL https://git.io/shellspec | sh -s -- -y

      - name: Run tests
        run: ${HOME}/.local/lib/shellspec/shellspec --shell bash
```

### Advanced: Parallel Test Execution

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]

    steps:
      - uses: actions/checkout@v3

      - name: Install ShellSpec
        run: curl -fsSL https://git.io/shellspec | sh -s -- -y

      - name: Run tests (shard ${{ matrix.shard }}/4)
        run: |
          export PATH="${HOME}/.local/lib/shellspec:${PATH}"
          shellspec --jobs 1 --random --example-index ${{ matrix.shard }}/4
```

### Caching for Faster Builds

```yaml
steps:
  - uses: actions/checkout@v3

  - name: Cache ShellSpec
    uses: actions/cache@v3
    with:
      path: ~/.local/lib/shellspec
      key: shellspec-${{ runner.os }}-v1

  - name: Install ShellSpec
    run: |
      if [ ! -d ~/.local/lib/shellspec ]; then
        curl -fsSL https://git.io/shellspec | sh -s -- -y
      fi

  - name: Run tests
    run: ${HOME}/.local/lib/shellspec/shellspec
```

## GitLab CI

### Basic Configuration

```yaml
# .gitlab-ci.yml

image: ubuntu:latest

stages:
  - test
  - coverage

before_script:
  - apt-get update -qq
  - apt-get install -y curl

test:
  stage: test
  script:
    - curl -fsSL https://git.io/shellspec | sh -s -- -y
    - export PATH="${HOME}/.local/lib/shellspec:${PATH}"
    - shellspec
  artifacts:
    reports:
      junit: report.xml
    when: always

coverage:
  stage: coverage
  script:
    - apt-get install -y kcov
    - curl -fsSL https://git.io/shellspec | sh -s -- -y
    - export PATH="${HOME}/.local/lib/shellspec:${PATH}"
    - shellspec --kcov
  coverage: '/Overall coverage rate.*?(\d+\.\d+)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura.xml
```

### Parallel Jobs

```yaml
test:
  stage: test
  parallel: 4
  script:
    - curl -fsSL https://git.io/shellspec | sh -s -- -y
    - export PATH="${HOME}/.local/lib/shellspec:${PATH}"
    - shellspec --jobs 4
```

### Multiple Environments

```yaml
.test_template: &test_template
  script:
    - curl -fsSL https://git.io/shellspec | sh -s -- -y
    - export PATH="${HOME}/.local/lib/shellspec:${PATH}"
    - shellspec

test:ubuntu-20.04:
  <<: *test_template
  image: ubuntu:20.04

test:ubuntu-22.04:
  <<: *test_template
  image: ubuntu:22.04

test:debian:
  <<: *test_template
  image: debian:latest
```

## Jenkins

### Jenkinsfile

```groovy
pipeline {
    agent any

    stages {
        stage('Install Dependencies') {
            steps {
                sh '''
                    curl -fsSL https://git.io/shellspec | sh -s -- -y
                    export PATH="${HOME}/.local/lib/shellspec:${PATH}"
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    export PATH="${HOME}/.local/lib/shellspec:${PATH}"
                    shellspec --format tap > test-results.tap
                '''
            }
        }

        stage('Coverage') {
            steps {
                sh '''
                    apt-get update && apt-get install -y kcov
                    export PATH="${HOME}/.local/lib/shellspec:${PATH}"
                    shellspec --kcov
                '''
            }
        }
    }

    post {
        always {
            junit 'test-results.tap'
            publishHTML([
                reportDir: 'coverage',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
            ])
        }
    }
}
```

## CircleCI

### Configuration

```yaml
# .circleci/config.yml

version: 2.1

jobs:
  test:
    docker:
      - image: ubuntu:latest

    steps:
      - checkout

      - run:
          name: Install dependencies
          command: |
            apt-get update
            apt-get install -y curl kcov

      - run:
          name: Install ShellSpec
          command: |
            curl -fsSL https://git.io/shellspec | sh -s -- -y

      - run:
          name: Run tests
          command: |
            export PATH="${HOME}/.local/lib/shellspec:${PATH}"
            shellspec --format junit > test-results.xml

      - run:
          name: Run coverage
          command: |
            export PATH="${HOME}/.local/lib/shellspec:${PATH}"
            shellspec --kcov

      - store_test_results:
          path: test-results.xml

      - store_artifacts:
          path: coverage
          destination: coverage

workflows:
  version: 2
  test:
    jobs:
      - test
```

## Travis CI

### Configuration

```yaml
# .travis.yml

language: bash

os:
  - linux
  - osx

before_install:
  - curl -fsSL https://git.io/shellspec | sh -s -- -y
  - export PATH="${HOME}/.local/lib/shellspec:${PATH}"

script:
  - shellspec

after_success:
  - |
    if [ "${TRAVIS_OS_NAME}" = "linux" ]; then
      sudo apt-get install -y kcov
      shellspec --kcov
      bash <(curl -s https://codecov.io/bash)
    fi
```

## Docker-Based Testing

### Dockerfile for Testing

```dockerfile
# Dockerfile.test

FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    kcov \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install ShellSpec
RUN curl -fsSL https://git.io/shellspec | sh -s -- -y
ENV PATH="/root/.local/lib/shellspec:${PATH}"

# Copy project
WORKDIR /app
COPY . .

# Run tests
CMD ["shellspec"]
```

### Docker Compose

```yaml
# docker-compose.test.yml

version: '3.8'

services:
  test:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - .:/app
    command: shellspec

  coverage:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - .:/app
    command: shellspec --kcov
```

### Run Tests in Docker

```bash
# Build and run tests
docker-compose -f docker-compose.test.yml up test

# Run with coverage
docker-compose -f docker-compose.test.yml up coverage
```

## Output Formats for CI

### JUnit XML (for test reports)

```bash
shellspec --format junit > test-results.xml
```

### TAP (Test Anything Protocol)

```bash
shellspec --format tap > test-results.tap
```

### JSON (for custom processing)

```bash
shellspec --format json > test-results.json
```

### Documentation Format (human-readable)

```bash
shellspec --format documentation
```

## Coverage Reporting Services

### Codecov

```yaml
# .github/workflows/test.yml

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/cobertura.xml
    flags: unittests
    name: codecov-umbrella
    fail_ci_if_error: true
```

### Coveralls

```yaml
- name: Upload coverage to Coveralls
  uses: coverallsapp/github-action@v2
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    path-to-lcov: ./coverage/lcov.info
```

### CodeClimate

```yaml
- name: Upload coverage to CodeClimate
  uses: paambaati/codeclimate-action@v3
  env:
    CC_TEST_REPORTER_ID: ${{ secrets.CC_TEST_REPORTER_ID }}
  with:
    coverageLocations: ./coverage/cobertura.xml:cobertura
```

## Badge Integration

### GitHub Actions Badge

```markdown
![Tests](https://github.com/username/repo/workflows/Tests/badge.svg)
```

### Codecov Badge

```markdown
[![codecov](https://codecov.io/gh/username/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/username/repo)
```

### GitLab CI Badge

```markdown
[![pipeline status](https://gitlab.com/username/repo/badges/main/pipeline.svg)](https://gitlab.com/username/repo/-/commits/main)

[![coverage report](https://gitlab.com/username/repo/badges/main/coverage.svg)](https://gitlab.com/username/repo/-/commits/main)
```

## Pre-commit Hooks

### Run Tests Before Commit

```bash
# .git/hooks/pre-commit

#!/bin/bash

echo "Running ShellSpec tests..."

if ! shellspec --format progress; then
  echo "Tests failed. Commit aborted."
  exit 1
fi

echo "All tests passed!"
```

Make executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Using Husky (for Node projects)

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "shellspec",
      "pre-push": "shellspec --kcov"
    }
  }
}
```

## Performance Optimization for CI

### Parallel Execution

```bash
# Run tests in parallel (4 workers)
shellspec --jobs 4
```

### Fail Fast

```bash
# Stop on first failure
shellspec --fail-fast
```

### Run Only Changed Tests

```bash
# Get changed files
changed_files=$(git diff --name-only HEAD~1 HEAD | grep '\.sh$')

# Find related spec files
for file in $changed_files; do
  spec_file="spec/$(basename ${file%.sh})_spec.sh"
  if [ -f "$spec_file" ]; then
    shellspec "$spec_file"
  fi
done
```

### Cache Dependencies

```yaml
# GitHub Actions
- uses: actions/cache@v3
  with:
    path: |
      ~/.local/lib/shellspec
      /usr/local/bin/kcov
    key: ${{ runner.os }}-deps-${{ hashFiles('**/lockfile') }}
```

## Notification Integration

### Slack Notification

```yaml
# .github/workflows/test.yml

- name: Notify Slack on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'ShellSpec tests failed!'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Email Notification

```yaml
# .gitlab-ci.yml

test:
  script:
    - shellspec
  after_script:
    - |
      if [ $CI_JOB_STATUS == 'failed' ]; then
        echo "Tests failed" | mail -s "CI Failure" team@example.com
      fi
```

## Best Practices for CI

1. **Run tests on every push** - Catch issues early
2. **Test multiple environments** - Ensure compatibility
3. **Enable coverage reporting** - Track test quality
4. **Cache dependencies** - Faster builds
5. **Fail fast** - Quick feedback on failures
6. **Parallelize when possible** - Reduce CI time
7. **Use appropriate output format** - JUnit for test reports
8. **Set up notifications** - Team awareness of failures
9. **Run tests before merge** - Prevent broken main branch
10. **Monitor test performance** - Keep CI fast

## Troubleshooting CI Issues

### Tests Pass Locally but Fail in CI

**Common causes**:
- Different Bash version
- Missing dependencies
- Environment variables not set
- Different file permissions
- Race conditions in parallel tests

**Solutions**:
- Match CI environment locally with Docker
- Explicitly set environment in CI config
- Check file permissions in tests
- Make tests independent

### Slow CI Builds

**Optimizations**:
```yaml
# Cache ShellSpec installation
# Run tests in parallel
# Use fail-fast mode
# Run only changed tests
```

### Coverage Not Updating

**Check**:
- Kcov installed in CI
- Coverage upload step configured
- Token/credentials set correctly
- Coverage file path is correct

## Next Steps

- Read `07-coverage.md` for coverage setup
- Read `10-troubleshooting.md` for debugging CI issues
- Check CI provider documentation for specific features
