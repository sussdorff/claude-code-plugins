---
name: workplan
description: /workplan — Beads-Backlog analysieren, priorisieren und verbessern
---
# /workplan — Beads-Backlog analysieren, priorisieren und verbessern

Analysiere das Beads-Backlog, erstelle einen priorisierten Arbeitsplan und schlage Verbesserungen zur Backlog-Organisation vor (Duplikate, Business-Domain-Labels, Epic-Gruppierung).

Optional: $ARGUMENTS (z.B. `--label billing`, `--epic mira-xxx`, `--focus P0`)

## Phase 1: Daten sammeln

Führe diese Befehle parallel aus:

```bash
bd stats
bd list --status=in_progress -n 0
bd ready -n 50
bd blocked | head -40
bd list --priority 0 --status=open -n 0
bd list --priority 1 --status=open -n 0
```

Falls `$ARGUMENTS` Label oder Epic Filter enthält, passe die Queries entsprechend an.

## Phase 2: Analyse

Aus den gesammelten Daten:

1. **Dependency-Graph**: Welche Blocker, wenn gelöst, unblockieren am meisten?
2. **Epic-Fortschritt**: Wie weit sind Themenblöcke?
3. **Stale Work**: in_progress ohne Updates seit >2 Tagen?

## Phase 3: Autonomie-Scoring

Bewerte jedes Ready-Bead nach Autonomie-Eignung:

| Signal | Score | Grund |
|--------|-------|-------|
| Hat Akzeptanzkriterien | +2 | Agent weiß wann fertig |
| Hat Description | +1 | Agent hat Kontext |
| Hat MoC-Tabelle | +1 | Agent weiß wie zu verifizieren |
| Hat NLSpec (intent/contracts) | +1 | Vollständige Spec für Agent (feature/epic) |
| Typ bug/task | +1 | Gut abgegrenzt |
| Typ feature/epic | -1 | Braucht oft Entscheidungen |
| P0 | -1 | Zu wichtig für unbeaufsichtigt |
| Leaf-Node (keine Deps) | +1 | Kein Koordinationsrisiko |

Scoring:
- Score >= 4: `cld -b <id>` empfohlen (autonom) — entspricht "factory-ready"
- Score 2-3: Semi-autonom (Ergebnis prüfen)
- Score <= 1: Interaktiv (braucht Mensch)

Für Autonomie-Scoring: Lade Details der Top-10 Ready-Beads via `bd show <id>` (parallel), um Akzeptanzkriterien, Description, MoC-Tabelle und NLSpec zu prüfen.

> **Detaillierte Spec-Analyse**: Für einzelne Beads mit hohem Score `/factory-check <id>` ausführen — bewertet alle 6 factory-ready Kriterien und gibt eine klare FACTORY READY / NEEDS INTERACTIVE WORK Empfehlung.

## Phase 3b: Duplikat- und Overlap-Erkennung

Scanne alle offenen Beads (aus Phase 1) nach Überschneidungen:

1. **Titel-Ähnlichkeit**: Vergleiche alle Paare offener Beads. Beads mit sehr ähnlichen Titeln (gleiche Kernbegriffe, umformuliert) sind Merge-Kandidaten.
2. **Thematische Überlappung**: Beads die das gleiche System/Feature adressieren aber aus unterschiedlichen Perspektiven (z.B. "Add error handling to X" + "Improve X resilience") → Epic-Kandidaten.
3. **Bereits-gelöst**: Beads deren Beschreibung sich mit kürzlich geschlossenen Beads deckt → Schließ-Kandidaten.

Für verdächtige Paare: `bd show <id>` für beide laden und Descriptions vergleichen.

**Keine externe Library nötig** — der LLM-Kontext reicht für semantischen Vergleich der Titel/Descriptions.

## Phase 3c: Business-Domain-Analyse

Identifiziere übergreifende Business-Domains aus den offenen Beads. Domains sind **fachliche Bereiche**, keine technischen Layer:

| Beispiel-Domain | Signalwörter |
|-----------------|-------------|
| billing | payment, invoice, transaction, pricing, subscription |
| auth | login, session, token, permission, role, access |
| observability | logging, monitoring, metrics, alerting, tracing |
| onboarding | setup, init, getting-started, first-run, wizard |
| workflow | pipeline, orchestrator, agent, automation, factory |
| documentation | docs, changelog, readme, standards, guide |

**Nicht verwenden**: frontend, backend, database, API, infrastructure — das sind technische Layer, keine Domains.

Schritte:
1. Clustere offene Beads nach erkannter Domain (aus Titel + Description)
2. Prüfe ob ein passendes Label bereits existiert: `bd label list`
3. Prüfe ob ein passendes Epic bereits existiert: `bd list --type=epic --status=open`
4. Für Cluster mit 3+ Beads ohne gemeinsames Label/Epic → Vorschlag generieren

## Phase 4: Output

Formatiere das Ergebnis als:

```markdown
## Workplan — [Projektname]

### Status
Open: X | Closed: Y (Z%) | Blocked: B | Ready: R

### Aktuell in Arbeit
(in_progress Beads mit Zeitstempel)

### Empfohlene nächste Aktionen

#### P0 — Jetzt
| ID | Titel | Autonomie | Grund |

#### P1 — Bald
| ID | Titel | Autonomie | Grund |

### Parallel startbar (cld -b)
```bash
cld -b <id1> &  # "Titel"
cld -b <id2> &  # "Titel"
```

### Kritischer Pfad (Blocker)
| Blocker | Unblockiert | Impact |

### Epic-Fortschritt
| Epic | Done/Total | % |

### Lücken
- [Epic X] fehlt: kein Bead für Schritt Y

### Backlog-Verbesserungen

#### Duplikate / Merge-Kandidaten
| Bead A | Bead B | Ähnlichkeit | Vorschlag |
|--------|--------|-------------|-----------|
| <id1> "Titel" | <id2> "Titel" | Gleiche Funktion | Merge → `bd close <id2> --reason="Merged into <id1>"` |

#### Business-Domain-Labels
| Domain | Beads | Vorschlag |
|--------|-------|-----------|
| billing | <id1>, <id2>, <id3> | `bd update <id1> --add-label=billing` (etc.) |

#### Epic-Gruppierung
| Vorgeschlagenes Epic | Beads | Vorschlag |
|---------------------|-------|-----------|
| "Observability Pipeline" | <id1>, <id2> | `bd create --title="[EPIC] Observability" --type=epic` + `bd dep add` |
```

## Phase 5: Aktionen anbieten

Frage den User:
- Soll ich ein Bead starten? (`bd update <id> --status=in_progress`)
- Parallel-Batch launchen? (mehrere `cld -b` commands)
- Einen Blocker untersuchen?
- **Backlog aufräumen?** Duplikate mergen, Labels anwenden, Epics erstellen?
  - Bei Zustimmung: die vorgeschlagenen `bd`-Commands direkt ausführen
  - Bei Teilzustimmung: User wählt welche Vorschläge umgesetzt werden
