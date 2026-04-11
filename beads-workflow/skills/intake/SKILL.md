---
name: intake
description: /intake — Transkript zu Beads Pipeline
---
# /intake — Transkript zu Beads Pipeline

Du nimmst ein Gespraechstranskript oder Freitext entgegen und zerlegst es in hochwertige,
umsetzbare Beads mit Akzeptanzkriterien und Means of Compliance.

## Input

```
$ARGUMENTS
```

---

## Phase 0: Input laden

### Schritt 1: Input erkennen

- **Dateipfad** (`.md`, `.txt`, `.docx`) → Datei lesen
- **Freitext** (mehrzeilig) → direkt verwenden
- **Kein Input** → Adrian fragen: "Transkript als Datei oder hier einfuegen?"

### Schritt 2: Transkript sichern

```bash
mkdir -p .intake
```

Transkript nach `.intake/transcript.md` schreiben (als Referenz fuer alle Phasen).

---

## Phase 1: Extraktion (Themen-Mining)

Starte **Task-Subagent** (subagent_type="general-purpose"):
```
Du bist ein Requirements-Analyst. Du extrahierst umsetzbare Themen aus Gespraechen.

## Input
Lies das Transkript: .intake/transcript.md

## Regeln
- Unterscheide: ANFORDERUNG (etwas bauen/aendern) vs. INFORMATION (Kontext, kein Action Item)
- Nur ANFORDERUNGEN werden Beads. INFORMATIONEN als Kontext-Notizen sammeln.
- Jedes Thema das eigenstaendig umsetzbar ist = 1 Bead-Kandidat
- Zusammengehoerende Punkte buendeln (nicht jeder Halbsatz ein Bead)
- Implizite Anforderungen explizit machen ("das muss natuerlich sicher sein" → Security-AK)

## Output
Schreibe nach: .intake/extraction.md

Format pro Kandidat:
### [N]: [Arbeitstitel]
- **Typ:** feature / bug / refactor / chore
- **Quelle:** Zitat oder Paraphrase aus Transkript
- **Kern:** Was genau soll passieren (1-2 Saetze)
- **Kontext:** Warum, fuer wen, Abhaengigkeiten

### Kontext-Notizen
[Informationen die kein Bead werden aber als Kontext relevant sind]

Antwort (1 Zeile): EXTRACT: [N] Kandidaten | [M] Kontext-Notizen
```

---

## Phase 1.5: Adrian-Gate

**PFLICHT.** Zeige die extrahierten Kandidaten als Tabelle:

```
| # | Typ | Arbeitstitel | Kern |
|---|-----|-------------|------|
| 1 | feature | ... | ... |
| 2 | bug | ... | ... |
```

Frage:
- "Welche Kandidaten sollen zu Beads werden? (alle / Nummern / keiner)"
- "Fehlt etwas? Soll ich Kandidaten zusammenlegen oder splitten?"

**Erst nach Freigabe weiter.** Geloeschte Kandidaten aus extraction.md entfernen.

---

## Phase 2: Strukturierung (AKs + Means of Compliance)

Fuer JEDEN freigegebenen Kandidaten einen **Task-Subagent** starten (parallel wenn > 1):

```
Du bist ein Requirements Engineer. Du schreibst praezise, testbare Akzeptanzkriterien
und definierst wie jede AK verifiziert wird (Means of Compliance).

## Input
Lies den Kandidaten [N] aus: .intake/extraction.md
Lies Kontext-Notizen aus: .intake/extraction.md (Abschnitt "Kontext-Notizen")

## Aufgabe
Erstelle eine vollstaendige Bead-Spec fuer diesen Kandidaten.

## Regeln fuer Akzeptanzkriterien (AKs)
- Jede AK ist EINE pruefbare Aussage (kein "und")
- Jede AK beginnt mit: "GEGEBEN ... WENN ... DANN ..." oder "ES GILT: ..."
- Jede AK hat eine Nummer: AK-1, AK-2, ...
- Minimum 2 AKs, Maximum 8 AKs pro Bead
- Keine vagen AKs ("funktioniert gut", "ist schnell") — immer messbar/pruefbar

## Means of Compliance (MoC)
Fuer JEDE AK definieren WIE sie geprueft wird:

| MoC-Typ | Wann | Beispiel |
|---------|------|---------|
| `code-review` | Logik, Pattern, Standards | "Reviewer prueft dass keine SQL-Injection moeglich ist" |
| `unit-test` | Einzelne Funktion/Methode | "pytest: test_calculate_discount_edge_cases" |
| `integration-test` | Zusammenspiel Komponenten | "pytest: test_api_returns_filtered_results" |
| `e2e-test` | User-Flow end-to-end | "Playwright: Login → Dashboard → Export → Download prueft" |
| `manual-test` | UI, UX, visuell | "Adrian prueft: Darstellung auf Mobile korrekt" |
| `static-analysis` | Types, Linting | "mypy --strict auf neuen Dateien" |
| `demo` | Stakeholder-Abnahme | "Demo an Adrian: Feature X in Aktion" |

## Output
Schreibe nach: .intake/bead-[N].md

Format:
# [Titel]

**Typ:** [feature/bug/refactor/chore]
**Prioritaet:** [P0-P4]
**Quelle:** [Zitat/Referenz aus Transkript]

## Beschreibung
[2-4 Saetze: Was, Warum, Fuer Wen]

## Akzeptanzkriterien

| # | Kriterium | MoC | Pruefdetail |
|---|-----------|-----|-------------|
| AK-1 | GEGEBEN ... WENN ... DANN ... | e2e-test | Playwright: [Szenario] |
| AK-2 | ES GILT: ... | code-review | Reviewer prueft: [was genau] |
| AK-3 | ... | unit-test | pytest: [test_name] |

## Scope
- **In Scope:** ...
- **Out of Scope:** ...

## Abhaengigkeiten
- [andere Beads, APIs, Services]

Antwort (1 Zeile): BEAD-[N]: [Titel] | AKs: [Anzahl] | MoCs: [code-review:X, unit-test:Y, e2e:Z]
```

---

## Phase 3: Council Review (Optional, Orchestrator entscheidet)

### Auto-JA:
- 3+ Beads aus einem Transkript (Konsistenz-Check wichtig)
- Mindestens 1 Bead mit Typ `feature` und 4+ AKs
- Transkript war ein Kunden-/Stakeholder-Gespraech

### Auto-NEIN:
- 1-2 kleine Beads (chore/refactor)
- Rein internes Tooling

### Wenn Council JA:

Starte **Task-Subagent**:
```
Du bist ein Council aus 4 Perspektiven das Bead-Specs reviewed.

## Input
Lies alle Bead-Specs: .intake/bead-*.md
Lies das Original-Transkript: .intake/transcript.md

## Perspektiven
1. **Transkript-Treue** — Decken die Beads ALLES ab was im Gespraech besprochen wurde? Fehlen Themen?
2. **AK-Qualitaet** — Sind alle AKs wirklich testbar? Gibt es Luecken, Ueberlappungen, Widersprueche?
3. **MoC-Realismus** — Sind die Pruefmethoden realistisch? E2E wo Unit reicht? Manual wo automatisiert moeglich?
4. **Scope & Schnitt** — Sind die Beads richtig geschnitten? Zu gross? Zu klein? Abhaengigkeiten klar?

## Output
Schreibe nach: .intake/council.md

Pro Perspektive: max 3 Findings (CRITICAL/WARNING/NOTE).
Dann: Konsolidierte Empfehlungen.

Antwort (1 Zeile): COUNCIL: [N] Findings | Top: [wichtigstes Finding]
```

**Bei CRITICAL Findings:** Betroffene Bead-Specs ueberarbeiten (neuer Subagent oder inline).

---

## Phase 4: Beads erstellen

### Schritt 1: Finale Uebersicht zeigen

```
| # | Typ | Titel | AKs | MoCs | Prio |
|---|-----|-------|-----|------|------|
| 1 | feature | ... | 4 | e2e:2, unit:1, review:1 | P2 |
| 2 | bug | ... | 2 | unit:1, review:1 | P1 |
```

Frage: "Beads so erstellen? (ja / Aenderungen)"

### Schritt 2: Beads anlegen

Fuer jeden Bead:
```bash
bd create "[Titel]" \
  --description "$(cat .intake/bead-[N].md)" \
  --priority [P0-P4] \
  --labels "[typ]" \
  --json
```

Merke die Bead-IDs.

### Schritt 3: Abhaengigkeiten setzen

```bash
bd dep add [child-id] blocks [parent-id]
```

### Schritt 4: Kontext-Notizen speichern

Wenn Kontext-Notizen aus Phase 1 vorhanden:
```bash
# Als Kommentar an den ersten/relevantesten Bead
bd comments add [id] "Kontext aus Gespraech: [Notizen]"
```

---

## Phase 5: Cleanup + Summary

```bash
rm -rf .intake/
```

**Ausgabe:**
```
## Intake Complete

Transkript: [Dateiname oder "Freitext"]
Erstellt: [N] Beads

| Bead-ID | Typ | Titel | AKs | Prio |
|---------|-----|-------|-----|------|
| bd-xxx | feature | ... | 4 | P2 |
| bd-yyy | bug | ... | 2 | P1 |

Abhaengigkeiten: [bd-xxx blocks bd-yyy] (oder "keine")
Naechster Schritt: `/dispatch bd-xxx` fuer Umsetzung
```

---

## Regeln

1. **Adrian-Gate nach Extraktion ist PFLICHT** — keine Beads ohne Freigabe
2. **Jede AK hat einen MoC** — kein Kriterium ohne Pruefmethode
3. **MoC-Typen muessen realistisch sein** — kein e2e-test fuer eine Config-Aenderung
4. **Transkript-Treue** — nichts erfinden, nichts weglassen was besprochen wurde
5. **Kontext-Uebergabe ueber `.intake/` Dateien** — nicht inline
6. **Orchestrator sieht nur 1-Zeilen-Summaries** — Details in Dateien
7. **Council bei 3+ Beads oder Stakeholder-Input** — Qualitaetssicherung
8. **Beads muessen eigenstaendig umsetzbar sein** — kein Bead das ohne ein anderes keinen Sinn ergibt (ausser explizite Dep)

---

## Input

$ARGUMENTS
