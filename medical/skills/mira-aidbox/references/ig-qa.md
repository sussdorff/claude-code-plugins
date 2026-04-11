# IG QA Review (`review-qa`)

Fetch and analyze the IG Publisher QA report from GitHub Pages.

## Steps

1. Determine the repo name from `sushi-config.yaml` or the git remote
2. Fetch the QA report:
   ```bash
   # Use summarize or web_url_read for clean extraction
   # URL pattern: https://cognovis.github.io/<repo>/qa.html
   ```
3. Parse errors and warnings into categories:
   - **Blocking errors** (must fix before publishing)
   - **Strong warnings** (should fix)
   - **Informational** (can suppress)
4. For each error, identify:
   - The affected FSH source file
   - The specific issue
   - A suggested fix
5. Output a prioritized fix plan

## Common QA issues and fixes

| Issue | Fix |
|-------|-----|
| Missing `experimental` on CodeSystem | Add `* ^experimental = false` |
| ConceptMap target is CodeSystem not ValueSet | Change `targetCanonical` to a ValueSet URL |
| Resource ID/URL mismatch | Align Instance name with `* url = ...` |
| ShareableCodeSystem/ValueSet violations | Add missing required elements (`experimental`, `name`) |
| Deprecated extension references | Remove or replace with current equivalent |
| Unresolvable CodeSystem URL | Verify URL exists on tx.fhir.org or fix typo |

## Local IG Publisher (QA Validation)

Run the IG Publisher locally to validate the IG before pushing to CI.
This produces the same QA report as CI but without the ~8min round-trip.

### Prerequisites

```bash
# Java (Homebrew, keg-only — needs explicit PATH or system symlink)
brew install openjdk
sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk

# Jekyll (Ruby gem, also needs PATH)
gem install jekyll

# IG Publisher JAR (download to input-cache/)
curl -L -o input-cache/publisher.jar https://github.com/HL7/fhir-ig-publisher/releases/latest/download/publisher.jar
```

### PATH Setup

Homebrew Java and Jekyll gems are keg-only — they're installed but not on the system PATH.
Set these before running:

```bash
export JAVA_HOME=$(/opt/homebrew/bin/brew --prefix openjdk)/libexec/openjdk.jdk/Contents/Home
export PATH="/opt/homebrew/lib/ruby/gems/4.0.0/bin:$JAVA_HOME/bin:$PATH"
```

### Run

```bash
# Compile FSH first
sushi .

# Run IG Publisher (skip SUSHI since we just ran it)
java -jar input-cache/publisher.jar -ig . -no-sushi
```

### Check Results

```bash
# Quick summary
head -5 output/qa.txt

# Error count
grep "errors =" output/qa.html

# All errors
grep "^ERROR:" output/qa.txt | sort | uniq -c | sort -rn

# All warnings
grep "^WARNING:" output/qa.txt | sort | uniq -c | sort -rn
```

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Unable to locate a Java Runtime` | Java not on PATH | Set JAVA_HOME + PATH as above |
| `Cannot run program "jekyll"` | Jekyll not on PATH | Add gem bin dir to PATH |
| `Exec failed, error: 2` | Missing binary | Check both Java and Jekyll PATH |
| Stale `input-cache/publisher.jar` | Old IG Publisher version | Re-download from GitHub releases |
