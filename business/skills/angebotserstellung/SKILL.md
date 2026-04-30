---
name: angebotserstellung
model: sonnet
description: Professionelle Angebote fuer IT-Projekte und Beratungsleistungen erstellen. Use when writing proposals, revising offers, or calculating project pricing. Triggers on Angebot, proposal, Preiskalkulation, Angebotserstellung, offer, Beratungsangebot.
disableModelInvocation: true
requires_standards: [english-only]
---

# Angebotserstellung

## Übersicht

Dieser Skill unterstützt bei der Erstellung professioneller Angebote für IT-Projekte, insbesondere für KI- und Automatisierungslösungen. Er enthält bewährte Muster für Struktur, Preiskalkulation und Kundenansprache.

## When to Use

- Neues Angebot fuer ein IT-Projekt oder Beratungsleistung erstellen
- Bestehendes Angebot ueberarbeiten oder aktualisieren
- Preiskalkulation fuer Projekte (Rueckwaertsrechnung, Stundensaetze)
- Angebotsstruktur planen (Stufenmodell, optionale Module)
- PDF aus fertigem Angebots-Markdown generieren

## Workflow

```
1. Markdown-Entwurf erstellen (ANGEBOT-GERUEST.md)
2. Iterativ mit Kunde abstimmen
3. Bei Versendung: MkDocs → HTML → Browser Print-to-PDF
4. Angebotsnummer vergeben und in angebote.json eintragen
```

**Referenzen:**

- [PDF-Generierung](references/pdf-generierung.md) - MkDocs-Setup, CSS für Print, Export-Methoden
- [MkDocs Workflow](references/mkdocs-workflow.md) - Build, Package, Pfad-Korrektur für standalone HTML
- [Angebotsnummern](references/angebotsnummern.md) - Nummernformat, Versionierung, Registry
- [cognovis Stammdaten](references/cognovis-stammdaten.md) - Firmendaten für Header/Footer

## Kernprinzipien

### 1. Iterativer Ansatz statt Big Bang

Niemals große Automatisierungsversprechen ohne Validierung:

- **Stufe 1**: Validierung (z.B. Chatbot, Workshop)
- **Stufe 2**: Erst nach erfolgreicher Stufe 1

Begründung: "Wir verkaufen keine Luftschlösser" - der Kunde sieht nach Stufe 1, ob die Lösung funktioniert.

### 2. Perspektive des Kunden

Angebote aus Kundensicht schreiben:

- Was ist das Problem des Kunden?
- Welchen Mehrwert liefert jede Stufe?
- Welche Risiken werden minimiert?

### 3. Keine konkreten Zahlen, die sich ändern können

Vermeiden:

- "NPS von -50" → "Stark negativer NPS"
- "3 von 8 Stellen unbesetzt" → "Offene Stellen, die schwer zu besetzen sind"

Begründung: Angebote werden archiviert. Konkrete Zahlen veralten und können peinlich werden.

### 4. Wiederverwendbarkeit einkalkulieren

Bei der Preiskalkulation berücksichtigen:

- Kann die Lösung für andere Kunden wiederverwendet werden?
- Rechtfertigt das einen engeren Preis?
- Strategischer Wert vs. reiner Projektgewinn

## Standard-Angebotsstruktur

```markdown
# Projekttitel

**Angebotsnummer:** QYYYY_MM_NNNN
**Version:** 1.0
**Datum:** YYYY-MM-DD
**Gültig bis:** YYYY-MM-DD

---

**Anbieter:** [cognovis Stammdaten]
**Empfänger:** [Kunde mit Adresse]

---

## Kurzübersicht für Entscheider

| | |
|---|---|
| **Investition Stufe 1** | XX.XXX EUR (Festpreis) |
| **Laufende Kosten** | ca. XXX EUR/Monat |
| **Zeitrahmen** | X-Y Wochen bis produktiv |
| **Erwarteter Nutzen** | [1 Satz] |
| **Risiko** | [1 Satz - warum gering] |

**Warum jetzt?**

- [Bullet 1]
- [Bullet 2]

**Warum wir?**

- [Bullet 1]
- [Bullet 2]

→ Details siehe Management Summary und Investition Gesamt

---

## Management Summary
[Ausgangslage, Problem, Ziel, Ansatz - ohne konkrete interne Zahlen]

## Stufe 1: [Validierung/Pilot]
[Beschreibung, Lieferumfang, Abnahmekriterien, Preis]

## Stufe 2: [Vollausbau] (Option)
[Nur nach erfolgreicher Stufe 1]
[Beschreibung, Lieferumfang, Preisspanne]
[Hinweis: Separates Angebot nach Stufe 1]

## Optionale Module
[Zusatzleistungen - Coaching vs. Umsetzung unterscheiden]

## Investition Gesamt
[Tabellarische Zusammenfassung inkl. laufende Kosten]

## Mitwirkungspflichten [Kunde]
| Was | Wofür | Wann |
|-----|-------|------|
[Alles was der Kunde bereitstellen muss]

## Nutzungsrechte
[IP-Regelung: Framework bei cognovis, Daten beim Kunden, Nutzungsrecht]

## Nächste Schritte
[Konkrete Handlungsaufforderung]
```

## Preiskalkulation

### Rückwärtsrechnung

1. Zielpreis festlegen (marktgerecht, strategisch)
2. Durch Stundensatz teilen → verfügbare Stunden
3. Prüfen: Ist das Projekt in diesen Stunden machbar?
4. Bei knapper Kalkulation: Wiederverwendbarkeit als Rechtfertigung

Beispiel:

```
Zielpreis: 18.500 EUR
Stundensatz: 250 EUR/h
Verfügbare Stunden: 74h
Frage: Ist Stufe 1 in 74h machbar?
```

### Stundensätze (Richtwerte)

| Leistung | Stundensatz |
|----------|-------------|
| Senior Consulting | 200-300 EUR |
| Workshop/Training | 250-350 EUR |
| Entwicklung | 150-250 EUR |

## Formatierung

### Deutsche Umlaute

**Immer verwenden**: ä, ö, ü, ß

**Niemals**: ae, oe, ue, ss (außer bei technischen Einschränkungen)

### Markdown-Bullets

Nach Label mit Doppelpunkt **immer** Leerzeile:

```markdown
Zuzüglich:

- Position 1
- Position 2
```

**Nicht**:

```markdown
Zuzüglich:
- Position 1
- Position 2
```

### Zeilenumbrüche in MkDocs

MkDocs ignoriert einfache Zeilenumbrüche. Für Adressblöcke `·` (Interpunkt) verwenden:

```markdown
# FALSCH - wird zu einer Zeile zusammengezogen
**Anbieter:**
cognovis GmbH
Schrödersweg 27

# RICHTIG
**Anbieter:** cognovis GmbH · Schrödersweg 27 · 22453 Hamburg
```

## Checkliste vor Abgabe

- [ ] Alle Umlaute korrekt (ä/ö/ü, nicht ae/oe/ue)?
- [ ] Keine konkreten internen Zahlen des Kunden?
- [ ] Stufen klar getrennt (Validierung vor Vollausbau)?
- [ ] Preise plausibel kalkuliert?
- [ ] Nächste Schritte konkret formuliert?
- [ ] Bullet-Formatierung korrekt (Leerzeilen nach Labels)?
- [ ] Aus Kundenperspektive geschrieben?
- [ ] **Kurzübersicht für Entscheider** vorhanden?
- [ ] **Mitwirkungspflichten** konsolidiert (nicht verstreut)?
- [ ] **Abnahmekriterien** für jede Stufe definiert?
- [ ] **Nutzungsrechte/IP** geklärt?
- [ ] AVV-Verantwortlichkeit geklärt (wer mit wem)?
- [ ] Angebotsnummer vergeben (nur bei Versendung)?
- [ ] Version korrekt (1.0 bei Erstversand, 1.x bei Änderungen)?
- [ ] In `angebote.json` eingetragen?

## Beispiel: Optionale Module

Optionale Module separat ausweisen, nicht in Hauptpreis verstecken:

```markdown
## Optionale Erweiterungen

### Lokale Datenverarbeitung
Für erhöhte Datenschutzanforderungen: Verarbeitung auf eigener Infrastruktur.

**Zusätzlich**: 5.000 EUR

### Coaching nach Workshop
Begleitung des Teams in den ersten 4 Wochen nach Go-Live.

**Zusätzlich**: 2.500 EUR
```

## Typische Fehler vermeiden

1. **Zu früh zu viel versprechen**
   - Lösung: Stufenmodell mit Validierung

2. **Technische Details statt Kundennutzen**
   - Lösung: "Was hat der Kunde davon?"

3. **Fixpreise für unklare Anforderungen**
   - Lösung: Preisspannen oder "nach Aufwand"

4. **Interne Metriken des Kunden nennen**
   - Lösung: Allgemeine Formulierungen

5. **Zu knappe Kalkulation ohne Begründung**
   - Lösung: Wiederverwendbarkeit oder strategischen Wert dokumentieren
