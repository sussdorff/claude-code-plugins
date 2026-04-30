---
name: standards
description: >-
  Manage coding standards lifecycle - list, inject, create, sync, review.
  Use when loading standards, checking compliance, creating new standards,
  or syncing standards to projects. Triggers on standards, inject standards,
  load standards, check compliance, create standard, sync standards,
  review conventions, check patterns, apply patterns.
model: haiku
requires_standards: [english-only]
---

# Standards

Unified skill for managing coding standards. Merged global and project-specific standards with Partial-Merge Semantik.

## Mode Detection

Parse the first argument to determine mode:

| Argument | Mode |
|----------|------|
| `list` | list |
| `create <key>` | create |
| `sync [args]` | sync |
| `review [args]` | review |
| _(anything else)_ | inject |

Examples:
```
standards                          → inject (auto-suggest)
standards python/style             → inject (explicit)
standards --mode=paths python/*    → inject (explicit with options)
standards list                     → list
standards create python/errors     → create
standards sync --all               → sync
standards review python/style      → review
```

---

## Mode: inject (default)

Lade relevante Standards in den aktuellen Kontext.

### Usage

```
standards                                    # Auto-Suggest
standards python/dataprovider-test-patterns  # Explicit
standards python/* compliance/*              # Glob
standards --context="migration test"         # Explicit context
standards --files="src/**/*.py"              # File context
standards --mode=paths python/style          # Output mode
```

### Schritt 1: Index laden und mergen

Lade beide index.yml Dateien:
- Global: `<global-standards-dir>/index.yml`
- Projekt: `<project-standards-dir>/index.yml` (falls vorhanden)

**Partial-Merge Regeln:**

| Szenario | Verhalten |
|----------|-----------|
| Standard nur global | Global laden |
| Standard nur projekt | Projekt laden |
| Standard in beiden | Partial-Merge: triggers vereinigt, description/path ueberschrieben |
| `path: inherit` | Globaler Pfad bleibt erhalten |

Fehlerbehandlung:
- Kein global index → nur projekt laden
- Kein projekt index → nur global laden
- Beide fehlen → Fehler mit Anleitung
- YAML invalid → Abbruch mit Zeilennummer

### Schritt 2: Modus bestimmen

**Auto-Suggest (keine Argumente):**
- Analysiere Konversation
- Match triggers gegen Kontext
- Zeige Vorschlaege

**Explicit (mit Argumenten):**
- Parse Standard-Keys oder Glob-Pattern
- Validiere Pfade
- Direkt laden

### Schritt 3: Trigger-Matching (Auto-Suggest)

Kontext-Quellen (priorisiert):
1. `--context` Parameter (explizit)
2. `--files` Parameter (Dateipfade)
3. User-Prompt (aktuelle Nachricht)
4. Dateipfade in Konversation
5. Aktuell geoeffnete Datei

**Scoring:**
```
Exact word match (word boundary): +3
Word in context.split():          +2
Substring match:                  +1
file_types match in cwd:          +2  (if file_types defined in index)
Minimum Score:                    2
```

### Schritt 4: Path-Validierung

Fuer jeden Standard validiere:
- Nur relative Pfade (kein `/` oder `~` am Anfang)
- Kein `..` erlaubt (path traversal)
- Nur `.md` Dateien
- Datei muss existieren

Base-Path wird aus `_source` bestimmt:
- `global` → `<global-standards-dir>/`
- `project` / `project-override` → `<project-standards-dir>/`

### Schritt 5: Szenario erkennen (fuer Output-Modus)

Falls kein `--mode` angegeben:
1. Plan Mode aktiv → `refs`
2. Skill-Erstellung (`<project-skills-dir>/` im Kontext) → `refs`
3. Delegierter Helfer-Prompt → `paths`
4. Sonst → `full`

Falls unklar, frage den User:
```
Wie soll ich die Standards formatieren?

1. **Volltext** — Standards direkt in Chat laden (fuer Implementation)
2. **Referenzen** — @-Pfade fuer Skill/Plan
3. **Pfadliste** — Fuer Subagent-Prompts
```

### Schritt 6: Standards laden und formatieren

**Token-Budget:**
- Max 3 Standards bei Auto-Suggest
- Max 10 Standards bei Explicit
- Max 2000 chars pro Standard (sonst gekuerzt)
- Max 8000 chars total

**Sortierung (deterministisch):**
1. Score (absteigend)
2. Source-Prioritaet: project > project-override > global
3. Key (alphabetisch)

### Schritt 7: Output

#### Modus: full (Conversation)
```markdown
## Geladene Standards

### python/dataprovider-test-patterns
[Vollstaendiger Inhalt, max 2000 chars]

---

### compliance/check-structure
[Vollstaendiger Inhalt]

---

**Zusammenfassung:**
- MockSystemDataProvider statt MockCommandRunner
- Typisierte Daten statt Raw-Strings
```

#### Modus: refs (Skill/Plan)
```markdown
Fuege diese Referenzen ein:

@<project-standards-dir>/python/dataprovider-test-patterns.md
@<global-standards-dir>/python/dependency-injection.md

Diese Standards decken ab:
- MockSystemDataProvider mit typisierten Daten fuer Tests
- CommandRunner DI Pattern fuer testbare System-Calls
```

#### Modus: paths (Subagent)
```markdown
## Standards (lies diese zuerst)
- <project-standards-dir>/python/dataprovider-test-patterns.md
- <project-standards-dir>/compliance/check-structure.md
```

### Glob-Pattern Syntax

| Pattern | Bedeutung | Beispiel-Match |
|---------|-----------|----------------|
| `python/*` | Alle in Domain | python/style, python/abc |
| `*/test*` | Name beginnt mit "test" | python/test-patterns |
| `*/*pattern*` | Name enthaelt "pattern" | compliance/check-patterns |

---

## Mode: list

Zeige alle verfuegbaren Standards mit smartem kontextuellem Ranking.

### Prozess

1. Lade und merge index.yml (gleich wie inject Schritt 1)
2. Fuehre Trigger-Matching gegen aktuellen Kontext aus (Konversation, cwd-Dateien)
3. Sortiere: matched Standards zuerst, dann Rest alphabetisch

### Output-Format

```markdown
## Verfuegbare Standards

### Empfohlen fuer dieses Projekt (Triggers matched)

| Standard | Beschreibung | Score | Triggers |
|----------|-------------|-------|----------|
| python/style | Python 3.14+, type hints, pathlib | 6 | .py, uv |
| python/dependency-injection | CommandRunner DI Pattern | 4 | subprocess |
| git/conventional-commits | Conventional Commits Format | 3 | git |

### Alle Standards (N gesamt)

| Standard | Beschreibung | Source |
|----------|-------------|--------|
| dev-tools/ast-grep-reference | ast-grep syntax | global |
| dev-tools/command-substitutions | CLI command substitutions | global |
| dev-tools/dotclaude-access | Symlink-safe .claude access | global |
| ... | | |
```

Hinweis: Bei `--verbose` zusaetzlich triggers und path pro Standard anzeigen.

---

## Mode: create

Scaffold einen neuen Standard.

### Usage

```
standards create python/error-handling
standards create --project frontend/api-patterns
```

Default: global (`<global-standards-dir>/`). Mit `--project`: projekt-lokal (`<project-standards-dir>/`).

### Prozess

1. **Parse Key:** `domain/name` extrahieren
2. **Zielverzeichnis bestimmen:**
   - Global: `<global-standards-dir>/<domain>/<name>.md`
   - Projekt: `<project-standards-dir>/<domain>/<name>.md`
3. **Pruefen:** Existiert der Key bereits in index.yml? Falls ja → Warnung und Abbruch
4. **Datei erstellen:**

```markdown
# <Name> (Title Case)

## Rules

- TODO: Add rules here

## Examples

### Good
```
TODO
```

### Bad
```
TODO
```
```

5. **index.yml updaten:**

```yaml
<domain>/<name>:
  description: "TODO: Add description"
  triggers:
    - "<domain>"
    - "<name>"
  path: "<domain>/<name>.md"
```

6. **Meldung:**
```
Standard erstellt:
  Datei: <global-standards-dir>/<domain>/<name>.md
  Index: <global-standards-dir>/index.yml (Eintrag hinzugefuegt)

Naechste Schritte:
1. Inhalt der .md Datei bearbeiten
2. Triggers in index.yml anpassen
3. Testen: standards python/error-handling
```

---

## Mode: sync

Kopiere globale Standards ins Projekt fuer Team-Sharing.

### Usage

```
standards sync                           # Interaktiv
standards sync python/style git/*        # Bestimmte Standards
standards sync --all                     # Alle relevanten
standards sync --dry-run                 # Nur zeigen
```

### Prozess

1. **Inventar erstellen:** Scanne global und projekt index.yml
2. **Projekt-Kontext analysieren:** Tech-Stack aus Dateien, pyproject.toml, package.json etc.
3. **Relevanz-Matching:**
   - Trigger matched Projekt-Kontext → `relevant`
   - Domain passt zu Tech-Stack → `maybe`
   - Keine Uebereinstimmung → `not-relevant`
4. **Diff anzeigen:**

```markdown
## Sync-Vorschlag

| Standard | Status | Relevanz | Aktion |
|----------|--------|----------|--------|
| python/style | Fehlt | relevant | Kopieren? |
| git/conventional-commits | Vorhanden (aktuell) | relevant | Skip |
| powershell/style | Fehlt | maybe | Kopieren? |
```

5. **User-Entscheidung:** Bei expliziten Args oder `--all` direkt kopieren, sonst fragen
6. **Kopieren:** Fuer jeden ausgewaehlten Standard:
   - Erstelle Verzeichnis: `mkdir -p <project-standards-dir>/<domain>/`
   - Kopiere Datei: `cp <global-standards-dir>/<path> <project-standards-dir>/<path>`
   - Update projekt index.yml: Eintrag hinzufuegen (oder `path: inherit` wenn gewuenscht)
7. **Zusammenfassung:**

```markdown
## Sync abgeschlossen

Kopiert: 3 Standards (python/style, python/python314-patterns, git/conventional-commits)

Naechste Schritte:
1. git add <project-standards-dir>/
2. git commit -m "feat: add shared standards for team"
```

### Do NOT (Sync)

- Do NOT sync ohne lokale Modifikationen zu pruefen — Projekt-Anpassungen wuerden ueberschrieben
- Do NOT index.yml Update vergessen — Standards ohne Index-Eintrag sind unsichtbar fuer inject
- Do NOT irrelevante Standards blind kopieren — Noise fuer Agents die sie lesen

---

## Mode: review

Pruefe Codebase-Compliance gegen geladene Standards.

### Usage

```
standards review                         # Alle matched Standards
standards review python/style            # Bestimmter Standard
standards review --fix                   # Mit Fix-Vorschlaegen
```

### Prozess

1. **Standards bestimmen:**
   - Ohne Args: Trigger-Matching gegen Projekt (wie inject Auto-Suggest, aber ohne Limit)
   - Mit Args: Nur angegebene Standards
2. **Standards laden:** Volltext aller zu pruefenden Standards einlesen
3. **Codebase scannen:**
   - Finde relevante Dateien (basierend auf Standard-Triggers und file_types)
   - Begrenze auf max 20 Dateien pro Standard (aelteste/groesste zuletzt)
   - Lies Dateien und pruefe gegen Standard-Regeln
4. **Compliance bewerten:**

Fuer jede Regel im Standard:
- PASS: Regel wird eingehalten
- WARN: Potenzielle Abweichung (nicht eindeutig)
- FAIL: Klarer Verstoss

5. **Report erstellen:**

```markdown
## Compliance Report

### python/style (Score: 8/10)

| Regel | Status | Details |
|-------|--------|---------|
| Type hints on all public functions | PASS | 12/12 functions typed |
| Use pathlib over os.path | FAIL | 3 files use os.path |
| Dataclasses over dicts | WARN | 2 untyped dicts in config.py |

Dateien mit Verstoessen:
- `src/utils.py:45` — os.path.join statt Path()
- `src/utils.py:78` — os.path.exists statt Path.exists()
- `src/config.py:12` — Untyped dict, dataclass empfohlen

### git/conventional-commits (Score: 10/10)

Alle 5 letzten Commits folgen dem Format.

---

**Gesamt: 2 Standards geprueft, 1 FAIL, 1 WARN**
```

6. **Fix-Vorschlaege** (bei `--fix`):
   - Zeige konkreten Code-Fix pro Verstoss
   - Frage ob Fixes angewendet werden sollen

---

## Fehlerbehandlung (alle Modi)

| Fehler | Meldung |
|--------|---------|
| Keine index.yml | "Keine Standards konfiguriert. Erstelle <global-standards-dir>/index.yml" |
| YAML invalid | "Parse-Fehler in {file}, Zeile {n}: {detail}" |
| Path traversal | "Ungueltiger Pfad (../ nicht erlaubt): {path}" |
| Absolute path | "Absolute Pfade nicht erlaubt: {path}" |
| Non-.md path | "Nur .md Dateien erlaubt: {path}" |
| File not found | "Datei nicht gefunden: {path}" |
| Kein Match | "Keine passenden Standards. Verfuegbar: {list}" |
| Glob no match | "Pattern '{pattern}' matched keine Standards. Verfuegbar: {list}" |
| Key exists (create) | "Standard {key} existiert bereits in index.yml" |

## Index Format

Standards are defined in `index.yml` under the `standards:` key:

```yaml
standards:
  <domain>/<name>:
    description: "Short description for agent context"
    triggers: ["keyword1", "keyword2"]  # Case-insensitive matching
    # file_types: [".py", ".pyi"]       # Future: auto-boost when matching files in cwd
    path: "<domain>/<name>.md"          # Relative to standards/
```

The `file_types` field is reserved for future use. When present, matching files in the current working directory boost the trigger score by +2.
