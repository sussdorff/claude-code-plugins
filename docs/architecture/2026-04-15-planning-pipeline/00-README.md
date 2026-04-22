# Planning Pipeline — 2026-04-15

Follow-up zur Session 2026-04-14. Ergebnis einer Analyse der I-Phase-Lücken
(Idee → fertig spezifiziertes Bead) und der Architecture-Context-Gaps beim
Implementer-Agent.

## Auslöser

- Die Entwicklungs-Pipeline ab "Bead ist spezifiziert" läuft stabil
  (wave-orchestrator, bead-orchestrator, review/verification-Agents).
- Der Weg **von loser Idee zu bead-fertiger Spec** ist unstrukturiert:
  keine Sokratische Clarification, kein Pitch-Artefakt, Council erst nach
  Grob-Spec, kein PRE-Implementation Architecture-Review, kein Readiness-Gate.
- Der Implementer-Agent bekommt Architektur-Kontext nur inkonsistent
  (CLAUDE.md wird gelesen aber nicht in Subagent-Prompts injiziert;
  arch-design-Docs existieren nur nach Wave-Orchestrator).

## Frameworks analysiert

- **BMAD Method** (Analysis → Planning → Solutioning → Implementation) —
  Pattern-Quelle für PRFAQ, Product Brief, Implementation-Readiness-Gate,
  Adversarial Review.
- **Superpowers Plugin** (obra) — Pattern-Quelle für Sokratisches Brainstorming
  und "junior-engineer-proof" Plans. Wenig Ideation, stark bei Implementation.
- **GitHub Spec Kit** / **Kiro** / **Tessl** — Pattern-Quelle für Constitution
  (`project-context.md`) und Phase-Artefakte mit Human-Checkpoints.

**Grundregel:** Patterns extrahieren, keine Frameworks importieren. Das Beads-
System bleibt Source of Truth, neue Skills erzeugen nur zusätzliche Artefakte.

## Dokumente

| # | Dokument | Thema |
|---|---|---|
| 01 | [Full Pipeline](01-full-pipeline.md) | End-to-End Ablauf Idee → Produktion, 11 Phasen, Fast-Paths |
| 02 | [Human Involvement Map](02-human-involvement-map.md) | Wo Malte-Involvement nötig ist, wo ein "Malte-Simulator"-Agent einspringt |
| 03 | [Bead Plan](03-bead-plan.md) | Welche Beads in welcher Reihenfolge anlegen |

## Key Design Decisions

1. **Neue Phasen-Skills, keine neuen Frameworks.** `/refine`, `/pitch`,
   `/arch-review`, Readiness-Gate als eigenständige Skills, die sich in den
   bestehenden Flow einhaken.
2. **Council wird früher eingesetzt** und bekommt Profile
   (`ceo` / `feature` / `infra` / `medical`).
3. **Pitch und Scenarios werden gekoppelt** — Scenario-Generator konsumiert
   `pitch.md` statt roher Bead-Beschreibung.
4. **`project-context.md` als Projekt-Constitution** — einmal generiert,
   automatisch in jeden Implementer-Subagent-Prompt injiziert, von
   `session-close` aktualisiert.
5. **Fast-Paths sind explizit**, nicht implizit. Skips werden vom System
   angezeigt und begründet.

## Offene Fragen (aus dieser Session)

- Wie stark soll der "Malte-Simulator"-Agent sein? Welche Entscheidungen darf
  er treffen, welche muss er immer eskalieren? Siehe Dokument 02.
- Wie bleibt `project-context.md` konsistent über parallele Waves? Lock-File?
  Merge-Strategie?
- Welche Council-Profile brauchen wir wirklich, und welche Rollen besetzen sie?
