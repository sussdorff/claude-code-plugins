---
name: epic-init
model: sonnet
description: Guided planning dialog for larger initiatives producing Beads epics with sub-tasks. Use when planning features or multi-task initiatives needing structured breakdown. Triggers on epic init, plan epic, create epic, plan feature, break down feature.
---

# Epic Init

Gefuehrter Planungsdialog fuer groessere Vorhaben. Produziert ein Beads-Epic mit Sub-Tasks.

Workflow: Ziel -> Zerlegung -> Constraints+WHY -> Handshake -> Beads anlegen

## When to Use

- Planning a new feature or initiative that needs structured task breakdown
- Breaking a large project into trackable sub-tasks with dependencies
- Starting a multi-session effort and want an epic with acceptance criteria
- Organizing work before kicking off implementation across multiple areas

## Do NOT

- Do NOT use for single-task work that doesn't need breakdown
- Do NOT create epics without acceptance criteria on sub-tasks

## Argumente

$ARGUMENTS

| Flag | Wirkung |
|------|---------|
| (keine) | Interaktiver Dialog ab Phase 1 |
| `"<Ziel>"` | Ziel vorbelegen, Phase 1 ueberspringen |

Beispiele:
```
/epic-init
/epic-init "FHIR Patient Intake implementieren"
/epic-init "CLI Tool fuer Log-Rotation"
```

---

## Workflow

### Phase 0: Kontext laden & Duplikat-Prüfung

**Pre-Check: bd Verfügbarkeit**

1. Prüfe ob `bd` installiert ist und `.beads/` existiert:
   ```bash
   which bd && test -d .beads && echo "beads ready"
   ```

   Falls `bd` nicht verfügbar oder `.beads/` fehlt:
   - Hinweis: "Beads ist noch nicht initialisiert in diesem Projekt."
   - Angebot: "Soll ich `bd init` ausführen um Beads einzurichten?"
   - Falls User zustimmt: `bd init` ausführen
   - Falls User ablehnt: Abbrechen mit "Verstanden — wir planen dann ohne Beads-Integration."

**Kontext laden:**

2. Lies `~/.claude/CLAUDE.md` (globales Profil — wer ist der User, wie arbeitet er)
3. Lies `./CLAUDE.md` (Projekt-Kontext — Tech-Stack, Architektur, Konventionen)
4. Lade offene und aktive Beads (falls verfügbar):
   ```bash
   bd list --status=open
   bd list --status=in_progress
   ```

4. **Duplikat-Prüfung mit expliziten Kriterien:**

   Prüfe geladene Beads gegen neues Vorhaben anhand dieser Kriterien:

   **(a) Ähnliche Titel** — Keyword-Matching:
   - Gleiche oder sehr ähnliche Schlüsselwörter (z.B. "API" in beiden Titeln)
   - Prüfe mit `bd search "<keyword>"` für gründlichere Suche
   - Beispiel: Neues Vorhaben "REST API für Patienten", existierende Bead "Patient-API Implementation" → Potential Duplikat

   **(b) Überlappende Scope-Beschreibung:**
   - Betreffen beide die gleiche(n) Komponente(n) oder Module?
   - Bearbeiten beide den gleichen Codebereich?
   - Beispiel: Neues Vorhaben "Database Schema Migration", existierende Bead "Migrate User Table" → Scope-Überlappung

   **(c) Gleiche Ziel-Dateien/Module:**
   - Listen beide die gleichen Dateien, Services oder APIs auf?
   - Adressieren beide das gleiche Problem/Feature in der gleichen Location?
   - Beispiel: Neues Vorhaben "Fix logging in auth.py", existierende Bead "Add authentication logging" → Ziel-Datei gleich

   **Falls Duplikat gefunden:** "Es gibt bereits [bead-id] '[titel]' — soll das hier integriert werden, oder sind das unterschiedliche Ansaetze?"

   **bd search Beispiele für gründlichere Prüfung:**
   ```bash
   bd search "API"           # Alle Beads mit "API" in Titel oder Beschreibung
   bd search "database"      # Alle Beads mit "database" als Keyword
   bd search "auth users"    # Mehrere Keywords (UND-Verknuepfung)
   ```

5. Fasse zusammen: "Projekt: **[Name]**, Stack: **[Stack]**, Offene Beads: **[Anzahl]**. Lass uns dein Vorhaben planen."

**Hinweis:** Falls kein `./CLAUDE.md` existiert, ist das OK — arbeite mit dem was verfuegbar ist.

### Phase 1: Ziel

**Falls `$ARGUMENTS` ein Ziel enthaelt:** Ueberspringe diese Phase, verwende das Argument als Ziel.

**Sonst:**
- Frage: "Was willst du erreichen? Beschreib das Ziel in 1-2 Saetzen."
- Warte auf Antwort
- Bestaetige: "Verstanden: **[umformuliertes Ziel]**. Stimmt das?"
- Bei Korrektur: nochmal nachfragen bis klar

### Phase 2: Zerlegung & Task-Level Duplikat-Prüfung

Basierend auf Ziel + Projekt-Kontext, schlage eine Aufteilung vor:

"Ich sehe folgende Teile:
1. **[Komponente A]** — [Kurzbeschreibung]
2. **[Komponente B]** — [Kurzbeschreibung]
3. **[Komponente C]** — [Kurzbeschreibung]

Abhaengigkeiten: B haengt von A ab, C kann parallel zu B.

Passt das? Fehlt etwas? Soll ich etwas anders aufteilen?"

**Regeln:**
- Nutze Projekt-Kontext fuer informierte Vorschlaege (z.B. bei FastAPI-Projekt: Routes + Models + Tests)
- Jede Komponente sollte grob 1-2 fokussierte Sessions umfassen
- Zeige Abhaengigkeiten zwischen Komponenten wo offensichtlich
- Warte auf User-Feedback und iteriere bei Bedarf
- **Groessen-Check:** Falls eine Komponente zu gross wirkt fuer eine einzelne fokussierte Session, weise darauf hin: "[Komponente X] sieht recht gross aus. Soll ich den weiter aufteilen?"

**Nach Akzeptanz der Zerlegung: Task-Level Duplikat-Prüfung**

Prüfe jede geplante Task gegen existierende Beads mit den Kriterien aus Phase 0:
- Gleiche oder ähnliche Titel (keyword matching)?
- Überlappende Scope-Beschreibung?
- Gleiche Ziel-Dateien/Module?

Für jeden gefundenen Duplikat-Kandidaten:
```bash
bd search "<task-keywords>"
```

Falls Task-Level Duplikate gefunden: "Task **[Name]** überschneidet sich mit [bead-id] — soll diese Task trotzdem angelegt oder mit der bestehenden Bead kombiniert werden?"

### Phase 3: Constraints + WHY

Fuer jede Komponente, frage nach Einschraenkungen:

"Gibt es fuer **[Komponente A]** Einschraenkungen oder bewusste Entscheidungen? Warum genau dieser Ansatz?"

**Gute Constraint-Beispiele:**
- "FHIR Patient Resource weil Aidbox das erwartet"
- "Kein ORM — Raw SQL wegen komplexer FHIR-Queries"
- "Muss offline funktionieren weil Praxen unreliable Internet haben"

**Regeln:**
- "Keine besonderen" ist eine valide Antwort — nicht erzwingen
- Mehrere Komponenten koennen in einer Runde abgefragt werden wenn es natuerlich fliesst
- Constraints die sich aus dem Projekt-Kontext ergeben, proaktiv vorschlagen: "Laut CLAUDE.md verwendet ihr [X] — gilt das auch hier?"

### Phase 4: Handshake

Praesentiere den KOMPLETTEN Plan:

```
## Vorhaben: [Ziel]

### Epic: [Titel]
[Ziel-Beschreibung mit Kontext]

### Tasks:
1. **[Task 1]** (P2, feature)
   - [Beschreibung mit Acceptance Criteria]
   - Constraints: [falls vorhanden]
   - Blocked by: —

2. **[Task 2]** (P2, task)
   - [Beschreibung mit Acceptance Criteria]
   - Constraints: [falls vorhanden]
   - Blocked by: Task 1

3. **[Task 3]** (P2, task)
   - [Beschreibung mit Acceptance Criteria]
   - Constraints: [falls vorhanden]
   - Blocked by: Task 1, Task 2
```

**Break Analysis (Pre-Mortem):**

Vor der Bestaetigungsfrage, fuehre eine Break Analysis durch:

"Bevor wir das finalisieren — wo koennte das schiefgehen?

**Abhaengigkeitsrisiken:**
- [z.B. Task 2 nimmt an, dass Task 1 ein bestimmtes Interface exponiert — ist das klar definiert?]
- [z.B. Shared State: Task 1 und 3 bearbeiten beide das gleiche Modul]

**Fehlende Annahmen:**
- [z.B. Setzt externes API X voraus — ist der Zugang eingerichtet?]
- [z.B. Braucht DB-Migration — wann wird die deployed?]

**Riskanteste Task:**
- [z.B. Task 3 hat die meisten Unbekannten weil...]"

Falls die Break Analysis echte Risiken aufdeckt: Aenderungen am Plan vorschlagen bevor weiter.

Dann frage: "Stimmt das so? Soll ich Aenderungen vornehmen oder die Beads anlegen?"

**KRITISCH:**
- Warte auf explizite Bestaetigung ("ja", "passt", "anlegen", o.ae.)
- Bei Aenderungswuenschen: zurueck zur Bearbeitung, dann erneut praesentieren
- Niemals automatisch weiter zur Erstellung

### Phase 5: Beads erstellen

**Erst nach expliziter Bestaetigung:**

1. Epic erstellen:
   ```bash
   bd create --title="[Epic-Titel]" --type=feature --priority=2 --description="[Vollstaendige Beschreibung mit Ziel, Kontext und Gesamtueberblick]"
   ```

2. Sub-Tasks erstellen (fuer jede Komponente, mit Parent-Link zum Epic):
   ```bash
   bd create --title="[Task-Titel]" --type=task --priority=2 --parent=<epic-id> --description="[Beschreibung mit Acceptance Criteria]"
   ```

3. Abhaengigkeiten setzen:
   ```bash
   bd dep add <task-id> <blocking-task-id>
   ```

#### Architecture Scout per Sub-Task

After creating all sub-tasks and setting dependencies, run architecture-scout for each
sub-task to detect architectural debt before implementation begins.

**For each sub-task created:**

1. Determine `touched_paths` from the sub-task description:
   - Extract package names (e.g., `packages/pvs-charly`) from file/module mentions
   - Extract directory paths from acceptance criteria
   - If no paths mentioned: use empty array (scout scans all packages)

2. Spawn architecture-scout:
   ```
   Agent(
     subagent_type="architecture-trinity:architecture-scout",
     prompt=json.dumps({
       "bead_id": "<sub-task-id>",
       "bead_description": "<sub-task title and description>",
       "touched_paths": ["<extracted-path-1>", "<extracted-path-2>"],
       "mode": "advisor"
     })
   )
   ```

3. Handle the scout result:
   - If `status: CONFORM` with empty findings: skip (keep task description clean)
   - If findings exist: append to the sub-task via:
     ```bash
     bd update <task-id> --append-notes="Coverage Matrix (architecture-scout):\n<scout-markdown-output>"
     ```

4. **Important**: Run scouts **sequentially** (not in parallel) to avoid rate limits.
   Each scout run takes approximately 5 seconds.

5. If a scout returns `status: VIOLATION` with BLOCKING findings:
   - Still append the matrix to the sub-task notes (as above)
   - Add a warning to the Phase 4 handshake summary:
     "⚠️ Sub-task [id] has BLOCKING architecture findings — review before implementation"
   - Do NOT block epic creation (epic-init is advisory-only; gate mode is /plan's responsibility)

4. Constraints als Notes speichern (falls vorhanden):
   ```bash
   bd update <id> --notes="Constraints: [...]"
   ```

5. Zusammenfassung zeigen:
   "Epic **[id]** mit **[n]** Sub-Tasks angelegt. `bd ready` zeigt dir was du anfangen kannst."

**Abbruch-Handling während Phase 5:**

Falls der User während dieser Phase abbricht (z.B. "stopp", "abbrechen", Ctrl+C):

1. Auflisten welche Beads bereits erstellt wurden (Epic + Sub-Tasks)
2. Angebot zum Aufräumen: "Ich habe [n] Beads angelegt. Soll ich diese löschen um aufzuräumen?"
3. Falls User zustimmt: Cleanup durchführen
   ```bash
   bd delete <epic-id> <task-id-1> <task-id-2> ...
   # oder kompakt mit parent:
   bd delete <epic-id>  # löscht Epic + alle Sub-Tasks
   ```
4. Bestätigung: "Aufgeräumt. Beads wurden gelöscht."

## Wichtige Verhaltensregeln

- **Sprache:** Durchgehend Deutsch
- **Handshake ist Pflicht:** Niemals Phase 5 ohne explizite Bestaetigung starten
- **Abhaengigkeiten:** Basierend auf tatsaechlichen technischen Abhaengigkeiten, nicht nur Reihenfolge
- **Acceptance Criteria:** Muessen testbar/verifizierbar sein
- **Beads-Commands:** Ausschliesslich `bd` verwenden (kein TodoWrite, TaskCreate, o.ae.)
- **Keine Dauer-Schaetzungen:** Keine konkreten Zeitangaben machen (z.B. "dauert 3 Stunden") — nur relative Groessen ("sieht gross aus", "kompakt")
- **Iterativ:** Bei Unklarheiten lieber nachfragen als annehmen
- **Duplikat-Pruefung:** Zweistufig durchfuehren:
  1. **Phase 0 (Epic-Level):** In Phase 0 geladene offene Beads gegen neues Gesamt-Vorhaben pruefen. Falls Ueberschneidungen: "Es gibt bereits [bead-id] '[titel]' — soll das hier integriert oder getrennt bleiben?"
  2. **Phase 2 (Task-Level):** Nach Zerlegung jede geplante Task gegen existierende Beads pruefen. Nutze `bd search "<keywords>"` für gründlichere Suche. Falls Task-Level Duplikate: "Task **[Name]** überschneidet sich mit [bead-id] — soll diese Task trotzdem angelegt oder kombiniert werden?"
  3. **Kriterien:** (a) Ähnliche Titel, (b) Überlappende Scope, (c) Gleiche Ziel-Dateien/Module

- **Rollback-Guidance bei Abbruch in Phase 5:**
  Falls der User während Phase 5 abbricht (teilweise Erstellung von Beads):
  1. Tracke welche Beads bereits angelegt wurden (Epic-ID + Sub-Task IDs)
  2. Biete aktiv an: "Soll ich die bereits erstellten Beads wieder löschen?"
  3. Falls ja: `bd delete <epic-id>` (löscht Epic + alle Sub-Tasks)
  4. Benutzer wird informiert welche Beads gelöscht wurden
