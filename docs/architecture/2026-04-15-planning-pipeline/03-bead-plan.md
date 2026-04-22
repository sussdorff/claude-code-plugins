# Bead Plan — Rollout Planning-Pipeline & Shikigami-Familie

Beads-Plan für die Umsetzung. Gruppiert in drei Epics, mit Priorisierung nach
**Quick-Wins zuerst, Framework-Arbeit mittendrin, Shikigami am Ende**.

Grund für diese Reihenfolge: die Pipeline-Phasen und Architecture-Context-Fixes
haben Wert auch **ohne** Shikigami. Shikigami wird erst richtig hilfreich, wenn
die Phasen stabil laufen — und dann ist open-brain auch voller nutzbarer
Kalibrierungs-Daten.

## Repo

Alles in `claude-code-plugins` (dieses Repo). Ausnahme: wenn ein Skill
projektspezifisch ist (z.B. medical-Profile im Council), kann er in
`fleet-packs` oder im jeweiligen Projekt liegen.

---

## Epic 1 — Architecture-Context-Fix (Quick-Wins, Priorität 1)

**Warum zuerst:** hat sofort Wirkung auf alle Implementer-Runs, unabhängig von
Planning-Pipeline. Klein und isoliert.

| # | Bead | Typ | Prio | Größe |
|---|------|-----|------|-------|
| 1.1 | `bead-orchestrator Phase 2 — Architecture Context Block injizieren` | task | P1 | S |
| 1.2 | `project-context.md Generator — aus Codebase initial erzeugen` | feature | P1 | M |
| 1.3 | `session-close — project-context.md Auto-Update bei Arch-Entscheidungen` | task | P2 | S |
| 1.4 | `bead-orchestrator Phase 2.6 — Module-Impact-Analyse als Pflichtschritt` | task | P2 | S |

**Output nach Epic 1:** Implementer-Agents haben konsistent Architecture-Context.
Das adressiert direkt Maltes beobachtetes Problem aus dieser Session.

---

## Epic 2 — Planning-Pipeline-Phasen (Priorität 2)

**Warum als zweites:** die Skills funktionieren eigenständig (du nutzt sie
manuell), bevor Shikigami sie orchestriert. Jede Phase einzeln testbar.

### 2a — Neue Phase-Skills

| # | Bead | Typ | Prio | Größe |
|---|------|-----|------|-------|
| 2.1 | `/refine Skill — Sokratisches Sounding-Board mit idea-brief.md Output` | feature | P2 | M |
| 2.2 | `/pitch Skill — PRFAQ-light mit Landing-Page-Text und FAQ` | feature | P2 | M |
| 2.3 | `/arch-review Skill — PRE-Implementation Architecture-Check mit ADR-Output` | feature | P2 | M |
| 2.4 | `/readiness Skill — PASS/CONCERNS/FAIL Gate vor Plan/Impl` | feature | P2 | S |

### 2b — Bestehende Skills erweitern

| # | Bead | Typ | Prio | Größe |
|---|------|-----|------|-------|
| 2.5 | `council Skill — Profile einführen (ceo/feature/infra)` | feature | P2 | S |
| 2.6 | `scenario-generator — Input auf pitch.md umstellen` | task | P3 | XS |
| 2.7 | `epic-init — Bundle-Input (Brief+Council+Pitch+Scenarios) unterstützen` | task | P2 | S |

### 2c — Verkettung

| # | Bead | Typ | Prio | Größe |
|---|------|-----|------|-------|
| 2.8 | `Pipeline-Orchestrator — Phase 1-7 End-to-End ohne Shikigami ausführbar` | feature | P2 | M |
| 2.9 | `Fast-Path-Matrix — explizite Skip-Logik mit Begründungen` | task | P3 | S |

**Output nach Epic 2:** Du kannst Idee → Bead manuell mit strukturierten Skills
durchlaufen. Artefakte sind versioniert, Fast-Paths definiert. Alle
Entscheidungen noch von dir.

---

## Epic 3 — Shikigami-Familie (Priorität 3)

**Warum zuletzt:** braucht Kalibrierung aus open-brain (die sich durch Epic 2
füllt) und stabile Phase-Skills (aus Epic 2) als Input.

### 3a — Framework (einmalig, teilbar mit späteren Shikigami-Geschwistern)

| # | Bead | Typ | Prio | Größe |
|---|------|-----|------|-------|
| 3.1 | `Shikigami-Framework — Profil-Struktur, Audit-Tags, Decision-Log-Schema` | feature | P3 | M |
| 3.2 | `Self-Learning-Standard — cross-cutting Prinzip als Standard-Dokument` | task | P3 | S |
| 3.3 | `Confidence-Threshold-Pattern — wiederverwendbar für alle Shikigami` | task | P3 | S |
| 3.4 | `Rolling-Metric + Retro-Mechanik — Drift-Erkennung als Library` | feature | P3 | M |

### 3b — Shikigami-Planner

| # | Bead | Typ | Prio | Größe |
|---|------|-----|------|-------|
| 3.5 | `shikigami-planner — Agent-Definition mit Haiku/Opus Two-Tier` | feature | P3 | M |
| 3.6 | `shikigami-planner — Cold-Start Bootstrap (retroaktiv + Interview)` | feature | P3 | M |
| 3.7 | `shikigami-planner — Integration in Phase-Skills (SIM/SOFT-Gates)` | feature | P3 | L |
| 3.8 | `AFK-Marker + Sync/Async Mode-Switching` | feature | P3 | S |
| 3.9 | `Morning-Briefing Skill + Beads-Queue für HARD-Entscheidungen` | feature | P3 | M |

### 3c — Erst nach Burn-In

| # | Bead | Typ | Prio | Größe |
|---|------|-----|------|-------|
| 3.10 | `Reason-Prompt bei Korrekturen — Feedback-Loop aktivieren` | task | P4 | XS |
| 3.11 | `Monatlicher Shikigami-Retro — Skill + Cron` | feature | P4 | S |
| 3.12 | `PII-Filter in Memory-Pipeline (Design + Implementation)` | feature | P3 | M |

**Output nach Epic 3:** Shikigami-Planner läuft, kalibriert sich selbst, kann
im AFK-Mode autonom Phasen 1–7 begleiten.

---

## Dependency-Diagramm (vereinfacht)

```
Epic 1 (Architecture-Fix)
    │ (unabhängig, ready jetzt)
    ▼
Epic 2a (Phase-Skills)
    │
    ├─► 2b (Skill-Erweiterungen)
    │
    ▼
Epic 2c (Verkettung)
    │
    ▼
Epic 3a (Framework)
    │
    ▼
Epic 3b (Shikigami-Planner)
    │
    ▼
Epic 3c (Post-Burn-In)
```

---

## Erste 5 Beads zum Anlegen (sofort)

Diese sollten als erstes in die Beads-DB, damit Epic 1 startet und die
Struktur steht:

1. **Epic:** `Planning-Pipeline Rollout` (parent für alle unten)
2. **Epic:** `Architecture-Context-Fix` (Parent für 1.1-1.4)
3. **Bead 1.1:** bead-orchestrator Phase 2 — Architecture Context Block
4. **Bead 1.2:** project-context.md Generator
5. **Bead 1.4:** bead-orchestrator Phase 2.6 — Module-Impact-Analyse

Beads 2.x und 3.x werden angelegt, wenn Epic 1 PAUSE-ready ist — sonst wird
die Queue zu lang und unübersichtlich.

---

## Offene Entscheidungen vor Umsetzung

- **PII-Filter-Design** (3.12): Muss vor Shikigami im Mira-Repo entschieden
  werden. Als separates Design-Dokument vorab.
- **Council-Profile konkret** (2.5): Welche Rollen in `ceo`, `feature`,
  `infra`? Aus vorhandenem `business:council` ableiten, dann erweitern.
- **Morning-Briefing: Skill vs. Hook** (3.9): Entscheidung bei Implementierung.
- **`project-context.md` Format** (1.2): Template-Design als Vorarbeit —
  was gehört rein, was ist Overkill?
