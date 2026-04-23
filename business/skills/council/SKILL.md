---
name: council
model: haiku
description: >-
  Multi-perspective sequential document review. Orchestrates 4 specialized Haiku subagents
  that critique a document from different angles (End-User, Developer, Security, Product Owner
  for requirements; configurable per type). Produces a consolidated findings table sorted by
  severity. Use when reviewing specs, requirements, deliverables, or training materials.
---

# /council — Multi-Agent Document Review

Du orchestrierst ein Council aus 4 spezialisierten Agenten die ein Dokument aus verschiedenen Perspektiven reviewen. Brutal ehrlich, kein Sugarcoating — das Council findet Schwaechen bevor es der Kunde tut.

## Usage

```
/council <path>                         # File mode: auto-detect document type
/council requirements <path>            # File mode: explicit type
/council training <path>                # File mode: training/workshop documents
/council deliverable <path>             # File mode: concepts, proposals, OKRs
/council requirements <path> --roles=<yaml_path>   # Custom roles YAML
/council <bead-id>                      # Bead mode (single bead) or Epic mode (if children)
/council label:<name>                   # Label mode: all beads with this label
```

$ARGUMENTS

## Phase 0: Input parsen

### Step 0a: Input-Modus erkennen

Nutze `parse_council_input(arg)` aus `council.py` um den Modus zu bestimmen:

| Input | Erkennung | Modus |
|-------|-----------|-------|
| `docs/spec.md`, `src/main.py` | Endet mit `.md` oder enthaelt `/` | **file** |
| `label:security` | Beginnt mit `label:` | **label** |
| `5shz` (bd show erfolgreich, keine Kinder) | Kein `.md`, kein `/`, `bd show` OK, children=[] | **bead** |
| `5shz` (bd show erfolgreich, hat Kinder) | Kein `.md`, kein `/`, `bd show` OK, children=[...] | **epic** |
| `xyzzy` (bd show schlaegt fehl) | Kein `.md`, kein `/`, `bd show` Fehler | **Fehler**: "Not a file, not a known bead ID. Use label:\<name\> for labels." |

### Step 0b: File-Mode (bestehende Logik)

Erwartetes Format: `[typ] <pfad>` oder nur `<pfad>`, optional `--roles=<yaml_path>`

**Typen:** `training`, `requirements`, `deliverable`

**Argument parsing:**
1. Prüfe ob `--roles=<path>` vorhanden — wenn ja, speichere als `custom_roles_path`
2. Prüfe ob erstes Wort ein bekannter Typ ist — wenn ja, extrahiere als `doc_type`
3. Restliches Argument ist der Dokumentpfad

**Typ-Erkennung bei fehlendem Typ:**
- Enthält "Workshop", "Training", "Lernziel", "Agenda", "Uebung" → `training`
- Enthält "User Story", "Requirement", "Akzeptanzkriterien", "API", "Endpoint" → `requirements`
- Sonst → `deliverable`
- Bei Unsicherheit: Nutzer fragen

**Validierung:**
1. Pfad existiert? Wenn nicht: Fehler + Abbruch.
2. Datei lesbar? Read tool nutzen.
3. Datei leer? Abbruch: "Dokument ist leer. Nichts zu reviewen."
4. Typ erkannt? Weiter.

### Step 0c: Bead/Epic/Label-Mode

**Bead mode:** Lade Bead-Beschreibung via `bd show <id>`. Nutze als Dokument fuer das Council. Typ ist immer `requirements`.

**Epic mode:** Lade Epic-Bead + alle Kind-Beads via `bd show <id> --json`. Jedes Kind-Bead wird einzeln reviewed. Ergebnisse werden cross-bead konsolidiert (siehe Phase 4).

**Label mode:** Lade alle Beads mit `bd list --label <name> --json`. Jedes Bead wird einzeln reviewed. Ergebnisse werden cross-bead konsolidiert (siehe Phase 4).

---

## Phase 1: Rollen laden

**Default roles path:** `business/skills/council/council-roles.yml` (relativ zum claude-config root)
**Override:** `--roles=<yaml_path>` Argument

Die YAML-Datei enthält Rollen-Profile pro Dokumenttyp. Lade das passende Profil für den erkannten `doc_type`.

**Rollen-Struktur (je Profil):**

```yaml
requirements:
  - name: End-User
    description: "UX-Friction, Verstaendlichkeit, fehlende Szenarien, Accessibility"
    focus: "Usability, missing error states, confusing flows"
  - name: Developer
    ...
```

**Rollen nach Typ (Standard):**

**requirements:**
1. End-User — UX-Friction, Verstaendlichkeit, fehlende Szenarien, Accessibility
2. Developer — Implementierbarkeit, Edge Cases, technische Schulden
3. Security Reviewer — Auth, Datenschutz, Input-Validierung, OWASP
4. Product Owner — Scope Creep, MVP-Disziplin, Priorisierung

**training:**
1. Learning Designer — Didaktik, Lernziele, Sequenzierung, Methodenmix
2. Teilnehmer-Anwalt — Zielgruppen-Passung, Komplexitaet, Vorwissen
3. Facilitator — Timing, Durchfuehrbarkeit, Energie-Management
4. Auftraggeber — Business-ROI, strategische Passung, messbare Ergebnisse

**deliverable:**
1. Client-Skeptiker — Einwaende, Widerstaende, politische Risiken
2. Umsetzungs-Realist — Was bricht in der Praxis, Ressourcen, Timeline
3. Executive — Strategische Passung, Executive Summary, Sprache/Tonalitaet
4. Change Manager — People Impact, Adoption, Kommunikationsstrategie

---

## Phase 1.5: Scenario Pre-Flight (nur Bead/Epic/Label Mode)

**NUR fuer bead, epic, und label Modi.** File-Mode ueberspringt diese Phase.

Fuer jedes Feature-Bead im Review-Set:

1. Lade die Bead-Beschreibung (falls nicht schon geladen)
2. Pruefe mit `detect_missing_scenario(description)` ob eine `## Szenario` oder `## Scenario` Sektion existiert
3. Falls fehlend:
   - Spawne `scenario-generator` Agent (mode: `bead-scenario`) um einen Szenario-Entwurf zu generieren
   - Gib den Entwurf als `SCENARIO_MISSING` Block **VOR** der Findings-Tabelle aus:

```
⚠ SCENARIO_MISSING: <bead-id>
Der folgende Szenario-Entwurf wurde automatisch generiert und sollte vor dem naechsten Council-Review in das Bead uebernommen werden:

[Generierter Szenario-Text]
```

4. Fahre mit dem Council-Review fort (das fehlende Szenario wird als implizites Finding behandelt)

---

## Phase 2: Dokument laden

Lies das Dokument mit dem Read tool.

**Groesse-Handling:**
- Dokument <= 500 Zeilen: Inhalt direkt in Agent-Prompts einfuegen (`DOCUMENT`)
- Dokument > 500 Zeilen: NUR Pfad an Agenten uebergeben. Jeder Agent liest selbst mit Read tool.

---

## Phase 3: Council ausfuehren

Starte 4 Subagenten **sequenziell** via Agent tool. Jeder Agent sieht das Dokument + alle vorherigen Kritiken.

```
Agent tool aufrufen mit:
  subagent_type: "general-purpose"
  model: "haiku"
  description: "[Rollenname] reviewt Dokument"
  prompt: (siehe unten)
```

**Prompt fuer Agent N:**

```
Du bist [ROLLENNAME] in einem Council-Review. Deine Perspektive: [ROLLENBESCHREIBUNG].
Fokus: [FOKUS aus YAML]

WICHTIG: Deine Aufgabe ist es Schwaechen und Luecken zu finden, NICHT zu validieren.
Sei konstruktiv-kritisch. Finde was andere uebersehen.

Antwort MUSS unter 1500 Zeichen bleiben. NUR Findings, kein Prozess.

## Dokument

[Bei <= 500 Zeilen: DOCUMENT hier einfuegen. Bei > 500 Zeilen: "Lies das Dokument: [PFAD]"]

## Vorherige Kritiken

[Outputs der vorherigen Agenten hier einfuegen, oder "Keine (du bist der erste Reviewer)" fuer Agent 1]

## Output-Format (EXAKT einhalten)

COUNCIL-REVIEW: [Rollenname]

Findings:
- [CRITICAL/WARNING/NOTE] [Thema]: [Beschreibung] → [konkreter Verbesserungsvorschlag]

Staerken (max 2):
- [Was gut funktioniert aus deiner Perspektive]

Wenn keine Findings: "Keine Findings aus meiner Perspektive."
```

### Cross-Bead Modus (Epic/Label): Zusaetzliche Agenten-Instruktionen

Wenn im cross-bead Modus (epic oder label), erhaelt jeder Agent zusaetzlich folgende Anweisungen im Prompt:

```
CROSS-BEAD REVIEW KONTEXT:
Du reviewst mehrere zusammengehoerige Beads. Achte ZUSAETZLICH auf:
1. **Konflikte zwischen Beads** — widerspruechliche Anforderungen, inkompatible Designs
2. **Scope-Ueberschneidungen** — Funktionalitaet die in mehreren Beads definiert wird
3. **Fehlende Inter-Bead-Abhaengigkeiten** — Bead A braucht etwas von Bead B, aber die Abhaengigkeit fehlt
4. **Luecken in der Feature Area** — Was fehlt komplett im Gesamtbild?

Beads im Review-Set:
[Liste aller Bead-IDs + Titel]
```

---

## Phase 4: Konsolidierung

Sammle alle 4 Agent-Outputs und erstelle eine konsolidierte Tabelle.

**Sortierung:** CRITICAL zuerst, dann WARNING, dann NOTE. Innerhalb gleicher Severity: Konsens-Findings vor Einzel-Findings.

### Single-Bead / File Mode (Standard-Tabelle)

```markdown
## Council Review: [Dokumentname]
Typ: [training/requirements/deliverable] | Agenten: 4 | Datum: [aktuelles Datum]

### Findings

| # | Severity | Agent | Thema | Finding | Empfehlung |
|---|----------|-------|-------|---------|------------|
| 1 | CRITICAL | [Rolle] | [Thema] | [Beschreibung] | [Vorschlag] |
| 2 | WARNING  | [Rolle] | [Thema] | [Beschreibung] | [Vorschlag] |
| ... | | | | | |

### Staerken
- [Rolle]: [Staerke]

### Zusammenfassung
- Critical: [N] | Warning: [N] | Note: [N]
- Konsens-Themen (von 2+ Agenten erwaehnt): [Liste]
- Top-Prioritaet: [wichtigstes Finding]

COUNCIL_BLOCKED: [true/false]
```

### Cross-Bead Mode (Epic/Label) — Tabelle mit Bead-Spalte

Im cross-bead Modus nutze `consolidate_findings_cross_bead()` fuer die Tabelle:

```markdown
## Council Review: [Epic/Label Name]
Modus: [epic/label] | Beads: [N] | Agenten: 4 pro Bead | Datum: [aktuelles Datum]

### SCENARIO_MISSING Blocks (falls vorhanden)

[Hier werden alle SCENARIO_MISSING Blocks aus Phase 1.5 eingefuegt]

### Findings

| # | Bead | Severity | Agent | Thema | Finding | Empfehlung |
|---|------|----------|-------|-------|---------|------------|
| 1 | [bead-id] | CRITICAL | [Rolle] | [Thema] | [Beschreibung] | [Vorschlag] |
| 2 | [bead-id] | WARNING  | [Rolle] | [Thema] | [Beschreibung] | [Vorschlag] |
| ... | | | | | | |

### Cross-Bead Analyse
- Konflikte: [gefundene Konflikte zwischen Beads]
- Scope-Ueberschneidungen: [Duplikate]
- Fehlende Abhaengigkeiten: [was fehlt]
- Luecken: [was im Gesamtbild fehlt]

### Zusammenfassung
- Critical: [N] | Warning: [N] | Note: [N]
- Betroffene Beads: [Liste]

COUNCIL_BLOCKED: [true/false]
```

**`COUNCIL_BLOCKED` Regel:**
- `true` wenn mindestens 1 CRITICAL Finding vorhanden
- `false` wenn nur WARNING/NOTE oder keine Findings

---

## Bead-Orchestrator Integration

Wenn `/council` im Kontext des bead-orchestrators aufgerufen wird:

1. Das letzte Token der Ausgabe ist immer `COUNCIL_BLOCKED: true` oder `COUNCIL_BLOCKED: false`
2. Bei `COUNCIL_BLOCKED: true` → **Implementation blockiert**. Der Orchestrator soll NICHT mit dem nächsten Schritt fortfahren, bis die CRITICAL Findings adressiert sind.
3. Der Nutzer muss CRITICAL Findings explizit quittieren oder das Dokument aktualisieren.

---

## Regeln

1. **Immer 4 Agenten** — keine ueberspringen
2. **Sequenziell** — jeder sieht vorherige Kritik (verhindert Redundanz, ermoeglicht Aufbauen)
3. **Anti-Groupthink** — Jeder Agent hat explizite Anweisung Schwaechen zu suchen
4. **Haiku-Modell** — schnell und guenstig, reicht fuer fokussierte Reviews
5. **Keine Aenderungen am Dokument** — nur Analyse und Empfehlungen
6. **Kompakte Outputs** — max 1500 Zeichen pro Agent, konsolidierte Tabelle am Ende
7. **Grosse Dokumente** — > 500 Zeilen: Pfad uebergeben statt Inhalt (Context-Effizienz)
8. **COUNCIL_BLOCKED immer ausgeben** — auch wenn keine Findings (dann `false`)
