---
disable-model-invocation: true
name: sync-standards
model: haiku
description: Synchronize global standards and commands into the current project for team sharing. Use when sharing standards with a team or copying conventions to a project. Triggers on sync standards, share standards, team standards, sync conventions.
---

# Sync Standards

Synchronisiere globale Standards und Commands ins aktuelle Projekt fuer Team-Sharing.

## When to Use

- Share coding standards and commands with team members via the project repo
- Set up a new project with the same conventions as other projects
- Check which global standards are missing in the current project (`--dry-run`)
- Update project standards after global standards have changed
- Copy specific commands or conventions into a team-shared repository

## Trigger

- "sync standards", "share standards with team"
- "copy global commands to project"
- "make standards available for team"
- "sync conventions"

## Workflow

### Schritt 1: Inventar erstellen

Scanne beide Quellen:

**Global (~/.claude/):**
```bash
# Standards
yq -r '.standards | keys | .[]' ~/.claude/standards/index.yml 2>/dev/null || echo "No global standards"

# Commands
ls ~/.claude/commands/*.md 2>/dev/null | xargs -n1 basename | sed 's/.md$//'
```

**Projekt (.claude/):**
```bash
# Standards
yq -r '.standards | keys | .[]' .claude/standards/index.yml 2>/dev/null || echo "No project standards"

# Commands
ls .claude/commands/*.md 2>/dev/null | xargs -n1 basename | sed 's/.md$//'
```

### Schritt 2: Projekt-Kontext analysieren

Ermittle relevante Technologien aus:
1. `CLAUDE.md` - Tech Stack Beschreibung
2. Dateiendungen im Projekt (`.py`, `.ps1`, `.ts`, etc.)
3. Config-Dateien (`pyproject.toml`, `package.json`, etc.)

```bash
# Quick tech detection
[ -f pyproject.toml ] && echo "python"
[ -f package.json ] && echo "javascript/typescript"
[ -d modules/ ] && ls modules/*.psm1 2>/dev/null && echo "powershell"
[ -f .gitignore ] && echo "git"
```

### Schritt 3: Relevanz-Matching

Fuer jeden globalen Standard/Command:
1. Pruefe ob bereits im Projekt vorhanden
2. Pruefe ob Triggers zum Projekt-Kontext passen
3. Kategorisiere: `relevant` | `maybe` | `not-relevant`

**Matching-Logik:**
- Standard hat Trigger der im Projekt-Kontext vorkommt → `relevant`
- Standard-Domain (python/, git/) passt zu Tech-Stack → `maybe`
- Keine Uebereinstimmung → `not-relevant`

### Schritt 4: Diff anzeigen

Zeige dem User eine Uebersicht:

```markdown
## Sync-Vorschlag

### Standards

| Standard | Status | Relevanz | Aktion |
|----------|--------|----------|--------|
| python/style | Fehlt | relevant | Kopieren? |
| python/python314-patterns | Fehlt | relevant | Kopieren? |
| git/conventional-commits | Fehlt | relevant | Kopieren? |
| powershell/style | Fehlt | maybe | Kopieren? |

### Commands

| Command | Status | Beschreibung | Aktion |
|---------|--------|--------------|--------|
| inject-standards | Fehlt | Standards in Kontext laden | Kopieren? |
| review-conventions | Fehlt | Convention Discovery (nur lokal) | Skip |
```

### Schritt 5: User-Entscheidung

Frage mit AskUserQuestion:

```
Welche Items sollen ins Projekt kopiert werden?

[ ] Alle relevanten (empfohlen)
[ ] Einzeln auswaehlen
[ ] Abbrechen
```

Bei "Einzeln auswaehlen" → Folgefrage pro Item oder Multiselect.

### Schritt 6: Kopieren

Fuer jeden ausgewaehlten Standard:

1. **Datei kopieren:**
   ```bash
   cp ~/.claude/standards/python/style.md .claude/standards/python/style.md
   ```

2. **index.yml updaten:**
   - Lade beide index.yml
   - Merge: Projekt-Eintrag hinzufuegen wenn nicht vorhanden
   - Schreibe aktualisierte index.yml

Fuer jeden ausgewaehlten Command:

1. **Datei kopieren:**
   ```bash
   cp ~/.claude/commands/inject-standards.md .claude/commands/inject-standards.md
   ```

### Schritt 7: CLAUDE.md Hinweis (optional)

Falls Commands kopiert wurden, schlage Ergaenzung fuer CLAUDE.md vor:

```markdown
## Projekt-Commands

- `/inject-standards` - Lade relevante Coding-Standards in den Kontext
```

### Schritt 8: Zusammenfassung

```markdown
## Sync abgeschlossen

Kopiert:
- 4 Standards (python/style, python/python314-patterns, git/conventional-commits, powershell/style)
- 1 Command (inject-standards)

Naechste Schritte:
1. `git add .claude/`
2. `git commit -m "feat: add shared standards and commands for team"`
3. `git push`
```

## Optionen

```
/sync-standards                    # Interaktiver Modus
/sync-standards --dry-run          # Nur zeigen, nichts kopieren
/sync-standards --all              # Alle relevanten ohne Nachfrage
/sync-standards --standards-only   # Nur Standards, keine Commands
/sync-standards --commands-only    # Nur Commands, keine Standards
```

## Fehlerbehandlung

| Fehler | Meldung |
|--------|---------|
| Kein .claude/ im Projekt | "Projekt hat kein .claude/ Verzeichnis. Erstelle mit: mkdir -p .claude/{standards,commands}" |
| Kein global index.yml | "Keine globalen Standards konfiguriert unter ~/.claude/standards/" |
| Datei existiert bereits | "Standard python/style existiert bereits im Projekt. Ueberschreiben? [y/N]" |
| yq nicht installiert | "yq wird benoetigt: brew install yq" |

## Beispiel-Session

```
User: /sync-standards

Claude: Analysiere Projekt...

Erkannter Tech-Stack:
- Python (pyproject.toml, src/*.py)
- PowerShell (modules/*.psm1)
- Git

## Sync-Vorschlag

### Fehlende Standards (4)
| Standard | Relevanz |
|----------|----------|
| python/style | hoch - Python-Projekt |
| python/python314-patterns | hoch - Python 3.14 in pyproject.toml |
| git/conventional-commits | hoch - Git-Repo |
| powershell/style | mittel - PowerShell-Module vorhanden |

### Fehlende Commands (1)
| Command | Beschreibung |
|---------|--------------|
| inject-standards | Standards in Kontext laden |

Welche Items kopieren?
1. Alle relevanten (empfohlen)
2. Einzeln auswaehlen
3. Abbrechen

User: 1

Claude: Kopiere Standards und Commands...

✓ python/style.md
✓ python/python314-patterns.md
✓ git/conventional-commits.md
✓ powershell/style.md
✓ inject-standards.md (Command)
✓ index.yml aktualisiert

Fertig! Committe die Aenderungen:
git add .claude/ && git commit -m "feat: add shared standards for team"
```

## Do NOT

- Do NOT sync without checking for local modifications in project standards first. WHY: sync overwrites local files with global versions — project-specific customizations would be silently lost.
- Do NOT copy commands that are only useful locally (e.g. `review-conventions`) to team projects without asking. WHY: some commands reference personal paths or tools that teammates do not have.
- Do NOT skip the `index.yml` update when copying standards. WHY: standards not registered in `index.yml` are invisible to `/inject-standards` — they exist on disk but are never loaded.
- Do NOT sync all standards blindly with `--all` on multi-stack projects without reviewing relevance. WHY: irrelevant standards (e.g. PowerShell in a pure Python project) add noise and confuse agents that read them.

## Hinweise

- Kopierte Standards sind **Snapshots** - Aenderungen am Global werden nicht automatisch synchronisiert. WHY: there is no automatic sync mechanism — global changes require re-running `/sync-standards`.
- Fuer regelmaessigen Sync: `/sync-standards` erneut ausfuehren
- Projekt-spezifische Standards haben Vorrang vor kopierten globalen. WHY: project standards are loaded after global ones and override matching rules.
