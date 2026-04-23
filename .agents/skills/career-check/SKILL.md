---
disable-model-invocation: true
name: career-check
model: sonnet
description: Modulare Karriere-Analyse fuer die AI-Aera mit Collapse Position Audit und Role Assessment. Use when evaluating career positioning or assessing AI impact. Triggers on career check, career analysis, career collapse, AI career, role assessment.
---

# Career Check

Modulare Karriere-Analyse fuer die AI-Aera. Basiert auf Career Collapse, Software-Shaped Intent und AI-Rollen Frameworks.

## When to Use

- You want to understand how vulnerable your current role is to the AI shift
- You need help decomposing your workflows into AI-delegatable vs. judgment-heavy steps
- You want a concrete 90-day learning plan tailored to your career situation
- You're exploring which AI-era role fits your background and interests
- You want an honest collapse position audit without cheerleading or doom

## Do NOT

- Do NOT present results as definitive career advice — frame as structured self-assessment
- Do NOT skip the Collapse Position Audit when running a full analysis

## Argumente

Optionale Eingabe-Flags:

| Flag | Wirkung |
|------|---------|
| (keine) | Modul-Auswahl anbieten |
| `--quick` | Nur Modul 1 (Collapse Position Audit) |
| `--deep` | Alle 3 Module + Bonus |
| `--roles` | Nur Bonus-Modul (Which Role Assessment) |

---

## Workflow

### Phase 1: Modul-Auswahl

- **Ohne Flag:** Biete die Module an:
  1. **Quick Check** — Collapse Position Audit (10-15 min)
  2. **Workflow Decomposition** — Software-Shaped Intent Builder (15-20 min)
  3. **Deep Dive** — Alle Module (30-45 min)
  4. **Role Assessment** — Welche AI-Rolle passt? (5-10 min)
- **Mit `--quick`:** Direkt zu Modul 1
- **Mit `--deep`:** Module 1 → 2 → 3 → Bonus sequenziell
- **Mit `--roles`:** Direkt zum Bonus-Modul

### Phase 2: Module durchfuehren

**Regeln (in dieser Prioritaet):**

1. Eine Frage pro Nachricht — natuerliche Konversation, kein Formular
2. Kommuniziere auf Deutsch
3. Direkt und ehrlich — kein Cheerleading, kein Doom
4. Bei vagen Antworten: Ein klaerender Follow-Up, dann mit markierter Annahme weiterarbeiten (`[Annahme: ...]`)
5. Nicht raten was der User "wahrscheinlich" meint — fragen
6. Zwischen Modulen kurzes Zwischenfazit, dann naechstes Modul einleiten

---

#### Modul 1: Collapse Position Audit

Basiert auf den "Two Career Collapses" — Horizontal Collapse (Domain-Expertise vs. AI-Orchestrierung) und Temporal Collapse (unrealistische Timeline-Annahmen).

**Fragen (eine pro Nachricht):**

1. "Beschreib deine aktuelle Rolle in 2-3 Saetzen — was machst du, in welcher Domain, wie lange schon?"
2. "Wie wuerdest du deine AI-Nutzung ehrlich einschaetzen?"
   - (a) selten/nie
   - (b) gelegentlich experimentiert
   - (c) regelmaessig fuer manche Tasks
   - (d) in taeglichen Workflow integriert
   - (e) kann mir Arbeiten ohne nicht vorstellen
3. "Was hast du dir vorgenommen 'irgendwann' zu lernen oder karrieremaessig zu machen — in den naechsten 2-3 Jahren?"

**Analyse generieren:**

- **Horizontal Collapse Assessment** als Tabelle:

  | Dimension | Dein Status | Wohin der Markt geht | Gap |
  |-----------|------------|---------------------|-----|
  | Domain Expertise | [Bewertung basierend auf Antworten] | Table stakes, kein Differenzierungsmerkmal | [Low/Medium/High] |
  | Agent Orchestration | [Bewertung basierend auf AI-Nutzung] | DER differenzierende Skill | [Low/Medium/High] |
  | Cross-Functional Execution | [Bewertung] | Durch AI fuer alle moeglich | [Low/Medium/High] |

- **Temporal Collapse Assessment** als Tabelle:

  | Annahme | Realitaets-Check |
  |---------|----------------|
  | [User Annahme aus Frage 3] | [Ehrliche Einschaetzung der Timeline] |

- **Reality Check:** 2-3 Saetze, direkt und ehrlich. Keine Floskeln.

---

#### Modul 2: Software-Shaped Intent Builder

Basiert auf dem "Stop Asking How to Get an AI Job" Workflow-Decomposition Ansatz. Eigene Arbeit in agent-directable Patterns zerlegen.

**Fragen (eine pro Nachricht):**

1. "Nenne 3 Tasks die du regelmaessig machst und die signifikant Zeit fressen."
2. User waehlt einen Task. Dann strukturierte Zerlegung — frage Schritt fuer Schritt:
   - **Trigger:** "Was startet diesen Workflow?"
   - **Inputs:** "Welche Infos/Artefakte ziehst du rein? Woher?"
   - **Steps:** "Liste die Schritte in Reihenfolge"
   - **Decisions:** "Wo triffst du Judgment Calls?"
   - **Outputs:** "Was produzierst du am Ende?"
   - **Checks:** "Wie verifizierst du 'gut genug'?"

**Synthese generieren:**

- **Workflow-Zerlegung** als Tabelle:

  | Step | Beschreibung | Typ | Pruefbarkeit | Risiko | AI-Fit |
  |------|-------------|-----|-------------|--------|--------|
  | [Nr] | [Was passiert] | [Mechanisch/Judgment/Kreativ] | [Hoch/Mittel/Niedrig] | [Was kann schiefgehen] | [Hoch/Mittel/Niedrig] |

- **Orchestrierungs-Opportunities:**
  - **Sofort delegierbar:** [Steps mit hohem AI-Fit und hoher Pruefbarkeit]
  - **Braucht dein Judgment:** [Steps mit Judgment-Calls]
  - **Orchestrierungs-Hebel:** [Wo du als Orchestrator den groessten Mehrwert schaffst]

---

#### Modul 3: 90-Day Engagement Accelerator

Konkreter Lernplan basierend auf den Ergebnissen aus Modul 1 + 2. Falls Modul 1/2 nicht durchgefuehrt: Kurze Kontextfragen stellen um die Luecke zu schliessen.

**Generiere den Plan:**

- **Phase 1 — Woche 1-4:** Detail-Level mit konkreten Wochenzielen
  - Woche 1: [Konkretes Experiment mit messbarem Ergebnis]
  - Woche 2: [Konkretes Experiment mit messbarem Ergebnis]
  - Woche 3: [Konkretes Experiment mit messbarem Ergebnis]
  - Woche 4: [Review + Anpassung — was hat funktioniert, was nicht]

- **Phase 2 — Monat 2:** Richtungsweisend, 2-3 Saetze

- **Phase 3 — Monat 3:** Richtungsweisend, 2-3 Saetze

**Regeln fuer den Plan:**
- Woechentliche Experiments statt abstrakte Ratschlaege
- Jedes Experiment muss in einer normalen Arbeitswoche machbar sein
- Messbare Outcomes: "Du weisst es hat geklappt wenn..."

---

#### Bonus-Modul: Which Role Assessment

Basiert auf dem 17-Rollen-Assessment fuer AI-Karrieren.

**Die 17 Rollen:**
ML Engineer, Computer Vision Engineer, NLP Engineer, Deep Learning Engineer, AI Research Scientist, AI Prompt Engineer, Data Annotator/AI Trainer, AI Content Creator, AI Product Manager, AI Ethics Officer, AI Governance Specialist, AI Strategist, AI Coach, AI Change Management Specialist, AI Compliance Manager, AI Conversation Designer, AI Customer Success Manager

**Fragen (eine pro Nachricht, 5-6 Fragen):**

1. "Was ist dein Background — technisch, kreativ, strategisch, oder eine Mischung?"
2. "Was macht dir bei der Arbeit am meisten Spass — Probleme loesen, Menschen fuehren, Prozesse optimieren, oder etwas anderes?"
3. "Wie tief willst du technisch gehen? (a) Modelle bauen (b) Modelle nutzen/integrieren (c) Strategie/Management (d) Schnittstelle Mensch-AI"
4. "In welcher Branche/Domain fuehlt sich deine Erfahrung am staerksten an?"
5. "Was ist dir wichtiger — Tiefe Spezialisierung in einem Bereich oder breite Anwendung ueber viele Bereiche?"
6. Optional, falls noetig: "Gibt es regulatorische oder ethische Themen die dich besonders beschaeftigen?"

**Empfehlung generieren:**

Top 3 Rollen in priorisierter Reihenfolge:

1. **[Rolle]** — [2-3 Saetze Begruendung basierend auf Antworten, konkreter Match zu Background]
2. **[Rolle]** — [2-3 Saetze Begruendung]
3. **[Rolle]** — [2-3 Saetze Begruendung]

---

### Phase 3: Output generieren

Nach Abschluss aller gewaehlten Module: Kompletten Report als Markdown ausgeben.

## Output-Format

```markdown
## Career Check Results

**Datum:** [YYYY-MM-DD]
**Module:** [Welche Module durchgefuehrt]

### Collapse Position Audit
[Horizontal Collapse Assessment Tabelle]
[Temporal Collapse Assessment Tabelle]
[Reality Check: 2-3 Saetze]

### Workflow Decomposition
[Workflow-Zerlegungs-Tabelle]
[Orchestrierungs-Opportunities]

### 90-Day Accelerator
**Phase 1 — Woche 1-4:**
- Woche 1: [Konkretes Experiment]
- Woche 2: [Konkretes Experiment]
- Woche 3: [Konkretes Experiment]
- Woche 4: [Review + Anpassung]

**Phase 2 — Monat 2:** [Richtung]
**Phase 3 — Monat 3:** [Richtung]

### Role Assessment
[Top 3 Rollen mit Begruendung]
```

**Hinweise zum Format:**
- Nur durchgefuehrte Module aufnehmen
- Faktisch und knapp, kein Fliesstext ausser wo explizit angegeben
- Tabellen wo spezifiziert, Bullet Points fuer den Rest
- Datum per `date` Command ermitteln

## Beispiel

```
career-check              # Modul-Auswahl anbieten
career-check --quick      # Nur Collapse Position Audit
career-check --deep       # Alle Module + Bonus
career-check --roles      # Nur Role Assessment
```
