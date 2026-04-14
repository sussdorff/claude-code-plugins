# Scenario Generator Refactor

**Session date**: 2026-04-14
**Scope**: Fix the scope drift in `scenario-generator` and the `scenarios/` folder convention.

## The problem

`dev-tools:scenario-generator` agent has two modes defined:

| Mode | Purpose | Output |
|---|---|---|
| `bead-scenario` | Generate `## Szenario` section for a bead | Markdown text |
| `persistent-scenario` | Generate permanent scenario document | `<scenarios_path>/<bead-id>-scenarios.md` file |

**Current default is `persistent-scenario`**. This is wrong.

Consequence: in mira, `scenarios/` contains 30+ files named `mira-XX-scenarios.md` with `Scope: single-bead`. These should not exist on disk. They should live inside their respective beads.

Evidence from mira:

```
scenarios/mira-01p-scenarios.md    Scope: single-bead
scenarios/mira-10ke-scenarios.md   Scope: single-bead
scenarios/mira-123-scenarios.md    Scope: epic-wide      ← correct
scenarios/mira-5ih-scenarios.md    Scope: epic-wide      ← correct
scenarios/mira-tx9c-scenarios.md   Scope: epic-wide      ← correct
... 30+ single-bead files          ← all wrong location
```

Only 3 files have `Scope: epic-wide`; the rest are drift.

## The correct model

Two distinct scenario layers, each with its own home:

| Layer | Lives in | Scope tag | Generator mode | Consumed by |
|---|---|---|---|---|
| Bead scenario | **Bead itself** (design field) | n/a — implicit per bead | `bead-scenario` (default) | `/ui-review <bead-id>` during implementation |
| Business process | `scenarios/<name>.md` | `epic-wide` or `business-process` | `persistent-scenario` (explicit opt-in) | `/ui-review <scenario-file>` at release/acceptance |

**Rule**: single-bead files should not exist on disk. The bead IS the scenario home.

## The fix

### 1. Flip scenario-generator default

In `claude-code-plugins/dev-tools/agents/scenario-generator.md`:

- Change default mode from `persistent-scenario` to `bead-scenario`
- In `bead-scenario` mode: stop returning markdown to caller; write directly via `bd update <id> --append-notes="..."` (or `--design="..."` — pick one field; see below)
- In `persistent-scenario` mode: require explicit `--scope=epic-wide|business-process` argument; reject `single-bead` scope
- Update the pre-flight checklist and mode-selection table in the agent spec

**Field choice (bead `notes` vs `design`)**: recommendation is `design`. Semantically "how to verify this works" is design-adjacent, and it's the field most frequently used for bead-local structured content. `notes` is free-form append log; less structured.

### 2. Migrate mira single-bead files

One-time script in mira repo:

```bash
for file in scenarios/mira-*-scenarios.md; do
  scope=$(grep "^> Scope:" "$file" | awk '{print $3}')
  bead_id=$(grep "^> Source:" "$file" | awk '{print $3}')
  if [ "$scope" = "single-bead" ] && [ -n "$bead_id" ]; then
    content=$(tail -n +10 "$file")  # strip preamble lines
    bd update "$bead_id" --append-notes "$content"
    git rm "$file"
    echo "Migrated: $bead_id"
  fi
done
```

Commit the migration in a single reversible commit:

```
refactor(scenarios): migrate single-bead scenarios from scenarios/ into bead design fields

- Move all Scope: single-bead files into their respective beads via bd update
- Delete migrated files from scenarios/
- Keep Scope: epic-wide files (future: rename to business-process names)
```

Before running the migration: **commit the current scenarios/ directory state first as a backup checkpoint**, so `git revert` works if the migration has issues.

### 3. Rename remaining epic-wide files

Business-process scenarios deserve semantic names, not opaque bead IDs:

```
scenarios/mira-5ih-scenarios.md   → scenarios/neuer-patient-bis-abrechnung.md
scenarios/mira-123-scenarios.md   → scenarios/hkp-genehmigung-und-kv-submission.md
scenarios/mira-tx9c-scenarios.md  → scenarios/<meaningful-name>.md
```

Keep a reference to the source epic bead in the file header (`> Source: mira-5ih`).

### 4. Update scenario-generator to handle epic scope

Audit whether `scenario-generator` today produces sensible output when given an epic bead with many child beads. If not:

- Extend the agent to collect child bead scenarios, compose cross-feature flow logic, and output a business-process-oriented scenario
- Keep this as `persistent-scenario` mode with explicit `--scope=epic-wide` flag
- Document the pattern in the scenario-generator spec

### 5. Delete stale cached plugin versions

`scenario-generator` is cached in multiple plugin versions:

```
~/.claude/plugins/cache/sussdorff-plugins/dev-tools/2026.04.9/agents/scenario-generator.md
~/.claude/plugins/cache/sussdorff-plugins/dev-tools/2026.04.10/agents/scenario-generator.md
~/.claude/plugins/cache/sussdorff-plugins/dev-tools/2026.04.11/agents/scenario-generator.md
~/.claude/plugins/cache/sussdorff-plugins/dev-tools/2026.04.12/agents/scenario-generator.md
~/.claude/plugins/cache/sussdorff-plugins/dev-tools/2026.04.16/agents/scenario-generator.md
```

After fix is released, older cached versions should not be used. Either bump version and let cache expire naturally, or document which version introduced the fix so other agents can reference it.

## Bead content convention

After fix, a bead with a generated scenario looks like:

```
Title: Dental Track: Stundenumsatz-Kalkulator
Type: feature
Priority: 2

Description:
ZMV sollte im HKP-Detailansicht einen Stundenumsatz-Badge sehen...

Acceptance Criteria:
- Stundenumsatz-Badge zeigt korrekten Wert
- Badge Farbe grün/gelb/rot basierend auf Benchmark
- Vergleichsbalken zeigt KZBV-Benchmark + Praxis-Ziel

Design (or Notes):
## Szenario 1: Happy Path — Lukrativer HKP
Ziel: ZMV öffnet HKP für Implantat-Versorgung und sieht grünen Stundenumsatz.

### Preconditions
- Solutio-Adapter Phase 1+3 implementiert
- GOZ/BEMA-Katalog als FHIR ChargeItemDefinition geladen
- Praxis-Zielstundensatz 350 EUR/h konfiguriert

### Steps
1. ZMV öffnet HKP-Detailansicht für Patient mit Implantat-Versorgung
2. System berechnet Stundenumsatz aus 5 GOZ-Positionen
3. Alle Positionen haben Zeitschätzungen

### Expected Results
- [ ] Stundenumsatz-Badge zeigt "412 EUR/h"
- [ ] Badge ist grün (über Praxis-Ziel 350 EUR/h)
- [ ] Aufschlüsselung zeigt Gesamthonorar 1.854 EUR, Zeit 4,5h

## Szenario 2: Unter Benchmark — Zeitintensiver HKP
...
```

qa-agent reads the `design` (or `notes`) field directly via `bd show --json` and parses `## Szenario` blocks.

## Business-process scenario format

Files in `<project>/scenarios/<name>.md`:

```markdown
# HKP-Genehmigung und KV-Submission

> Source: mira-5ih (epic)
> Scope: epic-wide
> Involves: mira-01p, mira-10ke, mira-123
> Generated: 2026-04-14
> Status: active

## Overview
Doktor erstellt neuen HKP, sendet zur Genehmigung ein, empfängt Antwort...

## Preconditions
- Alle Child-Beads der Epic mira-5ih sind gemerged
- Staging-Umgebung hat Seed-Daten für Patienten + KV
- Auth-Profile: zmv-tina

## Szenario 1: Happy Path
### Steps
1. ZMV öffnet Patient X
2. Erstellt HKP mit 5 Positionen
3. Klickt "Zur Genehmigung senden"
4. Wartet auf KV-Antwort (mocked, ~30s)
5. Öffnet empfangene Genehmigung
### Expected Results
- [ ] HKP-Status: eingereicht → genehmigt
- [ ] Notification erschienen
- [ ] Abrechnung im Billing-Cockpit sichtbar

## Szenario 2: KV-Ablehnung
...
```

## Component ownership

| Component | Repo | Why |
|---|---|---|
| scenario-generator agent | `claude-code-plugins` | Reusable across projects |
| Migration script | `mira` (one-time) | Project-specific |
| Scenario schema documentation | `claude-code-plugins/docs/` | Reusable |
| mira scenarios (epic-wide only) | `mira/scenarios/` | Project-owned |
| Bead design field usage | `.beads/` (per project) | Data-local |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Migration corrupts bead data | Commit backup checkpoint first; run migration as atomic commit; test on one bead before bulk. |
| Downstream tools expect `scenarios/` files to exist | Audit consumers before migration; update consumers first if needed. |
| Scope drift returns (future agents write to files again) | After fix, `bd lint` or similar should warn if scenario content appears in both bead and file. |
| Existing workflows reference file paths | Provide a compatibility shim during transition: a `scenarios/<bead-id>-scenarios.md` symlink or stub pointing at bead design field. Remove after all consumers updated. |

## Acceptance criteria for the refactor

- [ ] `scenario-generator` default mode is `bead-scenario`
- [ ] `bead-scenario` mode writes via `bd update`, does not return markdown to caller
- [ ] `persistent-scenario` mode requires explicit `--scope=epic-wide` or `--scope=business-process`
- [ ] mira has no files under `scenarios/` with `Scope: single-bead`
- [ ] All migrated bead content is reachable via `bd show <id>` and parses as Szenario blocks
- [ ] Remaining epic-wide files renamed to semantic names with source bead in header
- [ ] Scenario schema documented in `claude-code-plugins/docs/`

## Related documents

- Doc 01: Bowser Comparison and UI Testing (consumes the fixed scenario format)
- Doc 06: Bead Generation Plan (lists the specific beads for this refactor)
