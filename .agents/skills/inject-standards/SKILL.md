---
name: inject-standards
description: Load and merge global and project-specific coding standards into current context. Use when applying standards, patterns, or compliance requirements. Triggers on inject standards, load standards, standards, check patterns, apply patterns.
model: haiku
---

# Inject Standards

Lade relevante Standards in den aktuellen Kontext. Merged globale und projekt-spezifische Standards mit Partial-Merge Semantik.

## When to Use

- Starting implementation work and need the relevant coding standards loaded
- Preparing a subagent prompt that should follow project patterns
- Checking which standards apply to the current task or file type
- Loading specific standard documents by name or glob pattern

## Usage

```
# Auto-Suggest (matched gegen Konversation)
inject-standards

# Explicit (direkt laden, kein Matching)
inject-standards python/dataprovider-test-patterns

# Multiple
inject-standards compliance/check-structure python/abc-structure

# Glob-Pattern
inject-standards python/*        # Alle in python/
inject-standards */test*         # Alle mit "test" im Namen

# Mit explizitem Kontext
inject-standards --context="migration test compliance"

# Mit Dateipfaden als Kontext
inject-standards --files="src/zahnrad/compliance/*.py"

# Output-Modus erzwingen
inject-standards --mode=paths    # Nur Pfade (fuer delegierte Helfer)
inject-standards --mode=refs     # @-Referenzen (fuer Skills/Plans)
inject-standards --mode=full     # Volltext (Default)
```

## Prozess

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

## Glob-Pattern Syntax

| Pattern | Bedeutung | Beispiel-Match |
|---------|-----------|----------------|
| `python/*` | Alle in Domain | python/style, python/abc |
| `*/test*` | Name beginnt mit "test" | python/test-patterns |
| `*/*pattern*` | Name enthält "pattern" | compliance/check-patterns |

## Fehlerbehandlung

| Fehler | Meldung |
|--------|---------|
| Keine index.yml | "Keine Standards konfiguriert. Erstelle <global-standards-dir>/index.yml" |
| YAML invalid | "Parse-Fehler in {file}, Zeile {n}: {detail}" |
| Path traversal | "Ungültiger Pfad (../ nicht erlaubt): {path}" |
| Absolute path | "Absolute Pfade nicht erlaubt: {path}" |
| Non-.md path | "Nur .md Dateien erlaubt: {path}" |
| File not found | "Datei nicht gefunden: {path}" |
| Kein Match | "Keine passenden Standards. Verfuegbar: {list}" |
| Glob no match | "Pattern '{pattern}' matched keine Standards. Verfuegbar: {list}" |

## Beispiele

### Auto-Suggest bei Test-Arbeit
```
User: "Schreibe Tests fuer den DHCP Lease Scanner"

inject-standards

→ Analysiert Kontext: "test", "scanner"
→ Matched: python/dataprovider-test-patterns (Score 6)
→ Matched: python/dependency-injection (Score 4)
→ Zeigt Volltext beider Standards
```

### Explicit mit Glob
```
inject-standards python/*

→ Laedt: python/style, python/dataprovider-test-patterns,
         python/mock-command-runner, python/abc-structure,
         python/language-convention, python/dependency-injection,
         python/python314-patterns
→ Merged aus global + projekt
→ Zeigt alle im aktuellen Output-Modus
```

### Fuer Subagent-Prompt
```
inject-standards --mode=paths compliance/check-structure python/abc-structure

→ Output:
## Standards (lies diese zuerst)
- <project-standards-dir>/compliance/check-structure.md
- <project-standards-dir>/python/abc-structure.md
```

## Integration

Dieser Command wird intern verwendet von:
- Manuell: `inject-standards` fuer bewusste Standard-Injection
- Skills: Standards als Referenzen einbinden
- Plan Mode: Standards beim Planen laden
- Subagents: Standard-Pfade in Task-Prompts

Fuer automatische Injection bei Task-Tool: Siehe Phase 2 Roadmap.
