# Full Pipeline — Idee bis Produktion

## Übersicht

```
Idee ──► 1.Refine ──► 2.Council ──► 3.Pitch ──► 4.Scenarios ──► 5.Epic/Bead
                                                                      │
                                                              6.Arch-Review
                                                                      │
                                                              7.Readiness Gate
                                                                      │
                                                   8.Plan ──► 9.Impl (Orchestrator)
                                                                      │
                                                     10.Review ──► 11.Session-Close
```

Jede Phase: **ein klarer Input**, **genau ein Artefakt**, **ein expliziter
Human-Checkpoint**. Kleine Beads (bugs/chores) überspringen Phasen 1–7 via
Fast-Path.

---

## Phase 1 — Refine (Sokratisches Sounding-Board)

**Trigger:** `/refine "ich denke drüber nach, X zu bauen..."` oder nach `/vision`.

**Was passiert:** Ein einzelner Agent (nicht Council) stellt offene Rückfragen —
*"Wer ist die Zielgruppe? Was passiert, wenn es nicht existiert? Was ist das
Kleinste, das funktionieren würde?"*. Keine Lösungen, nur Klarstellung.
Dauer: 5–15 Minuten Dialog.

**Artefakt:** `idea-brief.md` (1 Seite):
- Problem in einem Satz
- Zielgruppe
- Hypothese ("Wenn wir X bauen, dann…")
- Scope-Grenzen (was explizit NICHT dazugehört)
- 3–5 offene Fragen für den Council

**Gate:** Malte liest den Brief, bestätigt oder schickt zurück.

**Skip:** Bugs/Chores überspringen komplett.

---

## Phase 2 — Council (Multi-Perspektiven-Review)

**Trigger:** automatisch nach Phase 1 oder manuell mit `--profile`.

**Profile:**
- `ceo` — CEO-Board für Geschäftsentscheidungen
- `feature` — 4-Haiku (End-User / Developer / Security / Product Owner)
- `infra` — Architect + Security + Performance
- `medical` — Compliance-Reviewer + Clinical-UX-Reviewer

**Artefakt:** `council-review.md` — angehängt an `idea-brief.md`. Konsolidierte
Findings sortiert nach Severity.

**Gate:** Malte entscheidet: *weiter* / *überarbeiten* (zurück zu 1) / *verwerfen*.
Verworfene Ideen als Bead mit Status=archived.

---

## Phase 3 — Pitch (Landing-Page / PRFAQ-light)

**Trigger:** `/pitch` auf den approvten Brief.

**Was passiert:** Ein Agent schreibt, **als wäre das Feature live**:
- Press Release (3 Absätze): Headline, Problem→Lösung, Kundenstimme
- FAQ: 5 harte Kundenfragen
- Landing-Page-Sektion: Hero-Text, 3 Feature-Bullets, CTA

**Artefakt:** `pitch.md`.

**Gate:** Malte liest und redigiert. Wenn Pitch nicht überzeugt → zurück zu 1.

**Skip:** Nur für `type=feature` mit `priority ≤ 2`. Chores/Bugs/Refactors skip.

---

## Phase 4 — Scenarios

**Trigger:** automatisch nach Phase 3.

**Was passiert:** Scenario-Generator liest **`pitch.md` als Input**. Produziert
Gherkin-artige Szenarien: Happy-Path, Edge-Cases, Error-Cases.

**Artefakt:** `scenarios.md` — wird als Verification-Contract im Bead gespeichert.

**Gate:** Malte prüft Vollständigkeit.

---

## Phase 5 — Epic/Bead-Erstellung

**Trigger:** `/epic-init` mit dem Bundle (Brief + Council + Pitch + Scenarios).

**Was passiert:** Breakdown in Epic + Child-Beads. Jeder Bead bekommt
Acceptance-Criteria aus Scenarios, Reference auf Pitch, Parent-Epic mit Brief +
Council attached.

**Artefakt:** Epic-Bead + N Child-Beads in Beads-DB.

**Gate:** Malte prüft den Zuschnitt (Beads sauber S/M, nicht XL).

---

## Phase 6 — Architecture-Review (PRE-Implementation)

**Trigger:** automatisch für `type=feature` **oder** `priority ≤ 1` **oder**
Label `needs-arch`. Sonst Skip.

**Was passiert:** `/arch-review` Agent liest:
- Bead + Pitch + Scenarios
- `project-context.md`
- Andere offene Architecture-Beads
- Voraussichtlich betroffene Module (Keyword-Grep)

Schreibt **ADR-Entwurf** und konkrete Architektur-Notizen ins Bead:
*"Dies gehört in Modul X, Pattern Y nutzen, Vorsicht wegen offener Änderung
in Bead Z"*.

**Artefakt:** `bd update <id> --design="..."` + ggf. ADR-Datei.

**Gate:** Optional — bei niedrigem Risiko direkt weiter, bei heiklen Fragen
Human-Review.

---

## Phase 7 — Readiness-Gate

**Trigger:** automatisch nach Phase 6 (oder direkt nach 5 für kleine Beads).

**Was passiert:** Leichtgewichtiger Check (1 Haiku-Agent, ~10 Sekunden):

| Check | Frage |
|-------|-------|
| AC testbar? | Lässt sich jedes Kriterium mit einem Test nachweisen? |
| Scope klar? | Sind die Grenzen explizit? |
| Dependencies? | Alle blockierenden Beads identifiziert? |
| Arch-Fragen offen? | Gibt's ungelöste Design-Entscheidungen? |
| Größe? | Micro / S / M / L / XL — XL muss gesplittet werden |

**Output:** `PASS` / `CONCERNS: [...]` / `FAIL: [...]`

**Gate:** `CONCERNS` → Malte entscheidet. `FAIL` → Stop, zurück zur
passenden Phase. `PASS` → Bead ist factory-ready.

---

## Phase 8 — Plan

`/plan <bead-id>` generiert Implementierungs-Plan mit Approach-Vergleich,
Test-Strategie, Risiken. Plan-Reviewer prüft. Human-Checkpoint.

---

## Phase 9 — Implementation

`bead-orchestrator` wie heute, aber **Phase 2 injiziert jetzt zuverlässig
Architecture-Context** in den Subagent-Prompt:

```
### Project Architecture Context
<aus project-context.md>

### Bead-spezifische Architektur-Notizen
<aus Phase 6 ADR/design>

### Module-Impact
<auto-identifiziert: "Du wirst X, Y, Z ändern">

### Bestehende Patterns in diesen Modulen
<kurze Pattern-Liste, damit der Implementer nicht davon abweicht>
```

Rest wie heute: Red-Green-Refactor, review-agent Loop, verification-agent.

---

## Phase 10 — Review

review-agent → optional cmux-reviewer (Codex) → holdout-validator →
constraint-checker. Schon gut abgedeckt.

---

## Phase 11 — Session-Close

Commit → Changelog → Merge → Push → Bead close. **Wichtig:
`project-context.md` wird hier aktualisiert**, falls der Bead
Architektur-Entscheidungen getroffen hat.

---

## Fast-Path-Matrix

| Typ | Phasen |
|-----|--------|
| Feature (neu, groß) | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 |
| Feature (inkremental) | 1 → 3 → 4 → 5 → 7 → 8 → 9 → 10 → 11 |
| Bug (P≤1) | 5 → 6 (opt.) → 7 → 9 → 10 → 11 |
| Bug (P≥2) / Chore | 5 → 7 → 9 → 10 → 11 (quick-fix) |
| Refactor | 1 → 6 → 7 → 8 → 9 → 10 → 11 |
| Infra-Change | 1 → 2 (Profil=infra) → 5 → 6 → 7 → 9 → 10 → 11 |

**Regel:** Jedes Skip ist **explizit** — das System begründet *"Überspringen
weil {Grund}?"*.
