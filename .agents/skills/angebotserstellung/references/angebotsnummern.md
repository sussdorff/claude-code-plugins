# Angebotsnummern-System

## Nummernformat

```
QYYYY_MM_NNNN
```

- **Q**: Quote (Angebot)
- **YYYY**: Jahr
- **MM**: Monat
- **NNNN**: Laufende Nummer im Monat (4-stellig, mit führenden Nullen)

**Beispiele**:

- `Q2026_02_0001` - Erstes Angebot im Februar 2026
- `Q2026_02_0002` - Zweites Angebot im Februar 2026
- `Q2026_03_0001` - Erstes Angebot im März 2026

## Registry-Datei

Jeder Kundenordner enthält eine `angebote.json` mit den versendeten Angeboten:

```json
{
  "angebote": [
    {
      "nummer": "Q2026_02_0001",
      "titel": "KI-gestützter technischer Support",
      "kunde": "solutio GmbH & Co.KG",
      "datum": "2026-02-05",
      "gueltig_bis": "2026-03-05",
      "version": "1.0",
      "status": "versendet",
      "betrag_netto": 18500,
      "datei": "Q2026_02_0001.pdf"
    }
  ]
}
```

### Felder

| Feld | Beschreibung |
|------|--------------|
| `nummer` | Eindeutige Angebotsnummer |
| `titel` | Kurztitel des Angebots |
| `kunde` | Kundenname |
| `datum` | Erstellungsdatum (ISO 8601) |
| `gueltig_bis` | Gültigkeitsdatum |
| `version` | Aktuelle Version (siehe Versionierung) |
| `status` | `entwurf`, `versendet`, `angenommen`, `abgelehnt` |
| `betrag_netto` | Angebotssumme netto in EUR |
| `datei` | Dateiname des PDFs |

## Versionierung

### Wann Version hochziehen?

- **Version 1.0**: Erstes versendetes Angebot
- **Version 1.1, 1.2, ...**: Kleinere Änderungen nach Kundenfeedback
- **Version 2.0**: Grundlegende Neugestaltung des Angebots

### Regeln

1. **Nur hochziehen wenn versendet**: Interne Entwürfe brauchen keine neue Version
2. **Subversionen für Feedback**: Kundenfeedback → 1.1, 1.2, 1.3, ...
3. **Major für Neugestaltung**: Komplett anderer Ansatz → 2.0

### Beispiel

```
v1.0  → An Kunden gesendet
v1.1  → Feedback: Preis zu hoch, reduziert auf 15.000 EUR
v1.2  → Feedback: Zusatzmodul gewünscht
v2.0  → Kunde will anderen Scope, komplett neues Angebot
```

## Workflow

### Neues Angebot erstellen

1. Nächste freie Nummer ermitteln:
   ```bash
   jq '.angebote | map(.nummer) | sort | last' angebote.json
   ```

2. Angebot in Markdown erarbeiten

3. Bei Versendung:
   - PDF generieren mit Angebotsnummer
   - Eintrag in `angebote.json` hinzufügen
   - Status auf `versendet` setzen

### Angebot aktualisieren

1. Markdown-Datei bearbeiten
2. Version hochziehen (nur wenn versendet wird)
3. Neues PDF generieren
4. `angebote.json` aktualisieren:
   ```bash
   jq '.angebote[-1].version = "1.2"' angebote.json > tmp.json && mv tmp.json angebote.json
   ```

### Status ändern

```bash
# Angebot angenommen
jq '.angebote[-1].status = "angenommen"' angebote.json > tmp.json && mv tmp.json angebote.json

# Angebot abgelehnt
jq '.angebote[-1].status = "abgelehnt"' angebote.json > tmp.json && mv tmp.json angebote.json
```

## Zentrale Übersicht

Optional: Globale Registry in `/Users/malte/Documents/cognovis/Kunden/Angebote/registry.json`

Diese aggregiert alle Angebote über alle Kunden hinweg für eine Gesamtübersicht.

```bash
# Alle Kundenordner durchsuchen und aggregieren
find /Users/malte/Documents/cognovis/Kunden -name "angebote.json" -exec cat {} \; | jq -s 'map(.angebote) | add'
```
