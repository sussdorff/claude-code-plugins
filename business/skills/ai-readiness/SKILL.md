---
disable-model-invocation: true
name: ai-readiness
model: haiku
description: Structured AI-Readiness Self-Assessment across 6 dimensions. Use for career planning or evaluating AI capability readiness. Triggers on AI readiness, self assessment, AI capability check, career readiness, AI skills assessment.
---

# AI-Readiness Self-Assessment

Fuehrt ein strukturiertes Self-Assessment durch um die eigene AI-Readiness in 6 Dimensionen zu bewerten. Basiert auf Assessment-Frameworks fuer exponentielles Denken, Compound-Skills und Leverage-Positionierung.

## When to Use

- You want an honest assessment of how well you're positioned for the AI shift
- You need to identify which of your skills compound vs. lose value over time
- You want a structured scorecard to track your AI readiness progress quarterly
- You're unsure whether you're thinking linearly or exponentially about AI capabilities
- You want concrete 90-day priorities to close your biggest AI readiness gaps

## Argumente

$ARGUMENTS

| Flag | Wirkung |
|------|---------|
| (keine) | Assessment starten (6 Dimensionen, ~15-25 Min) |
| `--quick` | Kurzversion: nur Dimensionen 1, 2, 4 (~8-12 Min) |

---

## Das darfst du NICHT

1. Mehrere Fragen in einer Nachricht stellen — zerstoert den Gespraechsfluss. WHY: User beantworten nur die erste oder letzte Frage, mittlere gehen verloren.
2. Punkte vergeben ohne konkrete Evidenz aus User-Antworten — keine Wohlfuehl-Bewertung. WHY: Aufgeblaehte Bewertungen machen das Assessment wertlos.
3. Hoeflichkeits-Passes bei vagen Antworten geben ("Gut, weiter!") — immer nachbohren. WHY: Vage Antworten = keine Datenbasis fuer die Bewertung.
4. Die Scorecard-Struktur veraendern oder Sektionen weglassen (ausser bei `--quick`). WHY: Vergleichbarkeit ueber Zeit geht verloren.
5. Englische Fachbegriffe in den Dimensionsnamen oder Bewertungs-Levels eindeutschen — die bleiben als feststehende Begriffe auf Englisch. WHY: "Exponential Curve Reading" ist ein Framework-Begriff, keine Uebersetzung.

---

## Workflow

### Phase 1: Intro

1. Begruesse den User kurz (2-3 Saetze)
2. Erklaere was das Assessment misst: "Wir messen deine Positionierung auf der exponentiellen AI-Capability-Kurve in 6 Dimensionen."
3. **Falls `--quick`:** "Kurzversion: Wir machen 3 statt 6 Dimensionen (Exponential Curve Reading, Compound Skill ID, Leverage Positioning)."
4. "Wir gehen [6/3] Dimensionen durch. Ich stelle jeweils 2-3 Fragen. Sei ehrlich — das Assessment ist nur fuer dich."

### Phase 2: Assessment (6 Dimensionen)

**Regeln (in dieser Prioritaet):**

1. Eine Frage pro Nachricht — natuerliche Konversation, kein starres Formular. WHY: Mehrere Fragen fuehren zu oberflaechlichen Antworten; eine Frage erzwingt Tiefe.
2. Kommuniziere auf Deutsch. WHY: Selbstreflexion funktioniert besser in der Muttersprache.
3. Bei vagen Antworten: Nachbohren mit Probe-Fragen ("Zeig mir die Rechnung", "Konkretes Beispiel?", "Was genau meinst du mit...?") — keine Hoeflichkeits-Passes
4. Nach jeder Dimension: Kurzes Zwischen-Feedback (z.B. "Solid. Weiter zu Dimension 3." oder "Interessant — da ist eine Luecke. Weiter."). WHY: Haelt den User engagiert und gibt Orientierung wo er steht.
5. Bewertungs-Evidenz aus konkreten User-Antworten ableiten, nicht raten. WHY: Ohne Evidenz sind Bewertungen beliebig und das Assessment hat keinen Wert.
6. **Falls `--quick`:** Nur Dimensionen 1, 2, 4 durchfuehren. Dimensionen 3, 5, 6 komplett weglassen — nicht fragen, nicht scoren.

---

#### Dimension 1: Exponential Curve Reading (Gewicht: 25%)

**Was gemessen wird:** Versteht die Person exponentielle AI-Capability-Kurven?

**Fragen (2-3, eine pro Nachricht):**

- "Die METR-Daten zeigen Verdopplung der autonomen Task-Dauer alle 7 Monate. Was passiert in 14 Monaten? Zeig mir die Rechnung."
- "Nimm eine Aufgabe die du regelmaessig machst (2-4h). Wenn AI 8h autonome Tasks schafft — was aendert sich konkret an deinem Workflow?"

**Bewertung 1-10:**

| Punkte | Level | Kriterien |
|-------|-------|-----------|
| 1-3 | Linear Thinker | Denkt in linearen Fortschritten, keine Vorstellung von Verdopplungsraten |
| 4-6 | Emerging | Weiss dass es exponentiell ist, kann aber keine konkreten Implikationen ableiten |
| 7-8 | Solid | Kann rechnen UND konkrete Workflow-Implikationen benennen |
| 9-10 | Advanced | Denkt in Capability-Stufen, plant proaktiv fuer naechste Verdopplungen |

---

#### Dimension 2: Compound Skill Identification (Gewicht: 20%)

**Was gemessen wird:** Welche Skills kompoundieren vs. verlieren Wert?

**Fragen (2-3, eine pro Nachricht):**

- "Liste 3-5 AI-Skills die du in den letzten 6 Monaten aufgebaut hast. Fuer jeden: steigt, bleibt gleich, oder sinkt der Wert wenn AI-Capabilities sich verdoppeln?"
- "Sei ehrlich: In welche Skills investierst du gerade die obsolet werden koennten?"
- "Wie viel deiner Lernzeit geht in Compound-Skills vs. lineare vs. abnehmende?"

**Bewertung 1-10:**

| Punkte | Level | Kriterien |
|-------|-------|-----------|
| 1-3 | No Awareness | Keine Unterscheidung zwischen Skill-Typen, investiert blind |
| 4-6 | Emerging | Erkennt das Konzept, aber Investitions-Mix stimmt noch nicht |
| 7-8 | Solid | Klare Compound-Skill-Strategie, ehrliche Einschaetzung der Risiken |
| 9-10 | Strategic | Systematische Skill-Portfolio-Optimierung, bewusste Wetten |

---

#### Dimension 3: Cognitive Failure Recognition (Gewicht: 20%)

**Was gemessen wird:** Erkennt die Person eigene Blindspots?

**Fragen (2-3, eine pro Nachricht):**

- "Was haettest du vor 3 Monaten als unmoeglich fuer AI bezeichnet? Was hat sich geaendert — die Technologie oder dein Verstaendnis?"
- "Wenn du AI scheitern siehst: Ist dein erster Impuls 'geht nicht' oder 'geht NOCH nicht — hier ist die Verbesserungsrate'?"
- "Vervollstaendige ehrlich: 'Ich unterschaetze AI-Fortschritt am ehesten wenn _____'"

**Bewertung 1-10:**

| Punkte | Level | Kriterien |
|-------|-------|-----------|
| 1-3 | Blind | Keine Reflexion ueber eigene Fehleinschaetzungen |
| 4-6 | Aware But Vulnerable | Erkennt Bias nachtraeglich, aber faellt noch regelmaessig rein |
| 7-8 | Actively Resistant | Aktive Strategien gegen eigene Blindspots, gute Selbstreflexion |
| 9-10 | Systematically Resistant | Systematische Gegenstrategien, trackt eigene Fehleinschaetzungen |

**Bei `--quick`:** Diese Dimension wird komplett uebersprungen (nicht fragen, nicht scoren).

---

#### Dimension 4: Leverage Positioning (Gewicht: 20%)

**Was gemessen wird:** Ist die Person als High-Leverage Individual positioniert?

**Fragen (2-3, eine pro Nachricht):**

- "Was schaffst du heute solo mit AI was vor 2 Jahren ein 3-5 Personen Team brauchte? Konkretes Projekt-Beispiel."
- "In 12 Monaten, wenn AI 8h autonome Tasks kann — was versuchst du solo was du heute nicht wagst?"
- "Rate dich 1-10 vs. Peers: Von 'AI = bessere Suchmaschine' bis 'delegiere ganze Workstreams an AI'"

**Bewertung 1-10:**

| Punkte | Level | Kriterien |
|-------|-------|-----------|
| 1-3 | Low Leverage | AI fuer einfache Tasks, kein Multiplikator-Effekt |
| 4-6 | Emerging | Sichtbare Produktivitaetssteigerung, aber noch kein Paradigmenwechsel |
| 7-8 | Solid | Konkreter Leverage-Nachweis, ambitionierte Plaene fuer naechste Phase |
| 9-10 | Strategic | Denkt in Leverage-Multiplikatoren, baut systematisch Solo-Capabilities auf |

---

#### Dimension 5: Signal Recognition (Gewicht: 15%)

**Was gemessen wird:** Trackt die Person die richtigen Metriken?

**Fragen (2-3, eine pro Nachricht):**

- "Welche konkreten, quantitativen Metriken trackst du fuer AI-Fortschritt? Nicht 'ich lese News'."
- "Jemand sagt 'AI hat ein Plateau erreicht'. Welche Daten checkst du um das zu bewerten?"
- "Wahr oder falsch: 'Ich kann 3-5 Capability-Milestones fuer die naechsten 12 Monate aufschreiben'. Falls ja, tu es."

**Bewertung 1-10:**

| Punkte | Level | Kriterien |
|-------|-------|-----------|
| 1-3 | Noise-Driven | Informiert sich ueber Schlagzeilen, keine eigenen Metriken |
| 4-6 | Signal-Aware | Kennt einige Benchmarks, trackt aber nicht systematisch |
| 7-8 | Signal-Driven | Eigene Metriken-Liste, kann Plateau-Claims faktenbasiert bewerten |
| 9-10 | Strategic Reader | Kann konkrete Milestones vorhersagen, versteht Lead-Indikatoren |

**Bei `--quick`:** Diese Dimension wird komplett uebersprungen (nicht fragen, nicht scoren).

---

#### Dimension 6: Judgment — Bonus, optional (keine feste Gewichtung)

**Was gemessen wird:** Entscheidungsqualitaet im AI-Zeitalter, basierend auf 10 Prinzipien (Bottleneck finden, Patterns wiederverwenden, Momentum sequenzieren, etc.)

**Fragen (Top 3, eine pro Nachricht):**

- "Rate dich 1-5 bei: Das echte Bottleneck in einem Projekt finden. Konkretes Beispiel der letzten 3 Monate."
- "Rate dich 1-5 bei: Patterns aus einem Kontext in einen voellig anderen uebertragen. Beispiel?"
- "Rate dich 1-5 bei: Aufgaben so sequenzieren dass jeder Schritt Momentum fuer den naechsten erzeugt. Beispiel?"

**Bewertung 1-10:** Analog zu den anderen Dimensionen. Wird separat ausgewiesen und fliesst NICHT in die gewichtete Gesamtpunktzahl ein, es sei denn explizit gewuenscht. WHY: Judgment ist subjektiver als die anderen Dimensionen — separate Ausweisung verhindert Verzerrung der Gesamtpunktzahl.

**Bei `--quick`:** Diese Dimension wird komplett uebersprungen (nicht fragen, nicht scoren).

---

### Phase 3: Auswertung & Synthese

1. Punkte pro Dimension (1-10) basierend auf konkreter Evidenz aus den Antworten
2. Gewichtete Gesamtpunktzahl berechnen:
   - Exponential Curve Reading: 25%
   - Compound Skill ID: 20%
   - Cognitive Failure Recognition: 20%
   - Leverage Positioning: 20%
   - Signal Recognition: 15%
   - (**Quick-Modus:** Exponential 40%, Compound Skill 30%, Leverage 30%)
3. Klassifizierung:

| Gesamtpunktzahl | Klassifizierung | Bedeutung |
|-------------|----------------|-----------|
| 8.0-10.0 | Exponentially Positioned | Vorsprung, Compound-Advantage wird aufgebaut |
| 6.0-7.9 | Tracking the Exponential | Auf Kurs, Schwachstellen fokussieren |
| 4.0-5.9 | Linearly Positioned | Risiko zurueckzufallen |
| 1.0-3.9 | Exponentially Blind | Dringender Mindset-Shift noetig |

4. Gap-Analyse: Schwaechste Dimension, groesster Blindspot, versteckte Staerke
5. Timing-Einschaetzung: Ist die Person Early, On-Time oder Late relativ zur Kurve?
6. 90-Tage-Prioritaeten ableiten

### Phase 4: Output

Zeige die vollstaendige Scorecard im folgenden Format:

```markdown
## AI-Readiness Scorecard

**Datum:** [YYYY-MM-DD]
**Modus:** [Voll / Quick]
**Gesamtpunktzahl:** [X.X/10] — [Klassifizierung]

### Dimensionen
| Dimension | Gewicht | Punkte | Level |
|-----------|---------|--------|-------|
| Exponential Curve Reading | 25% | X/10 | [Level] |
| Compound Skill ID | 20% | X/10 | [Level] |
| Cognitive Failure Recognition | 20% | X/10 | [Level] |
| Leverage Positioning | 20% | X/10 | [Level] |
| Signal Recognition | 15% | X/10 | [Level] |

### Judgment (Bonus)
| Prinzip | Selbst-Rating | Evidenz-Qualitaet |
|---------|--------------|-------------------|
| Bottleneck finden | X/5 | [Kurz-Assessment] |
| Patterns uebertragen | X/5 | [Kurz-Assessment] |
| Momentum sequenzieren | X/5 | [Kurz-Assessment] |

### Luecken-Analyse
**Schwaechste Dimension:** [Name] — [Warum das zurueckhaelt, 1-2 Saetze]
**Groesster Blindspot:** [Was der User nicht sieht, 1-2 Saetze]
**Versteckte Staerke:** [Wo die Beispiele staerker waren als die Selbsteinschaetzung]

### Timing-Einschaetzung
[Early / On-time / Late] — [1 Satz Begruendung]

### 90-Tage-Prioritaeten
1. **[Hoechster Impact]:** [Konkrete Aktion, 1-2 Saetze]
2. **[Zweite Prioritaet]:** [Konkrete Aktion]
3. **[Dritte Prioritaet]:** [Konkrete Aktion]

### Wettbewerbs-Kontext
[2-3 Saetze: Wie sich der Abstand zu weniger AI-fluenten Personen in 12 Monaten entwickelt]
```

**Hinweise zum Output:**
- Bei `--quick`: Judgment-Sektion und uebersprungene Dimensionen weglassen
- Gewichtung bei `--quick` angepasst anzeigen (40/30/30)
- Datum automatisch einsetzen (aktuelles Datum)
- Scorecard eignet sich zum Speichern fuer Progress-Tracking ueber Zeit

## Beispiel

```
/ai-readiness           # Volles Assessment starten (6 Dimensionen, ~15-25 Min)
/ai-readiness --quick   # Kurzversion (3 Dimensionen, ~8-12 Min)
```
