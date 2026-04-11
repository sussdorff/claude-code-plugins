# PDF-Generierung aus Markdown-Angeboten

## Workflow

```
Markdown (Arbeitsdokument)
    ↓
MkDocs (HTML-Vorschau)
    ↓
Browser Print-to-PDF (finales PDF)
```

## MkDocs Setup

### Verzeichnisstruktur im Kundenprojekt

```
kundenordner/
├── ANGEBOT-GERUEST.md      # Arbeitsdokument
├── mkdocs.yml              # MkDocs-Konfiguration
├── docs/
│   ├── ANGEBOT-GERUEST.md  # Kopie für MkDocs
│   └── stylesheets/
│       └── extra.css       # Custom Styles
└── angebote.json           # Angebots-Registry
```

### mkdocs.yml Template

```yaml
site_name: "Angebot [Kundenname]"
docs_dir: docs

theme:
  name: material
  language: de
  palette:
    primary: custom
  font:
    text: Roboto
    code: Roboto Mono

extra_css:
  - stylesheets/extra.css

markdown_extensions:
  - tables
  - toc:
      permalink: true
  - admonition
  - pymdownx.details
  - pymdownx.superfences
```

### extra.css für Angebote

```css
/* cognovis Branding */
:root {
  --md-primary-fg-color: #8BC34A;
  --md-primary-fg-color--light: #9CCC65;
  --md-primary-fg-color--dark: #689F38;
}

/* Print-optimierte Styles */
@media print {
  /* Header auf jeder Seite */
  @page {
    margin: 2cm 1.5cm;
    @top-center {
      content: "cognovis GmbH • Angebot";
    }
    @bottom-center {
      content: "Seite " counter(page) " von " counter(pages);
    }
  }

  /* Navigation ausblenden */
  .md-sidebar, .md-header, .md-footer {
    display: none !important;
  }

  /* Seitenumbrüche vor H2 */
  h2 {
    page-break-before: auto;
    margin-top: 2em;
  }

  /* Tabellen nicht umbrechen */
  table {
    page-break-inside: avoid;
  }
}

/* Tabellen-Styling */
table {
  width: 100%;
  border-collapse: collapse;
}

th {
  background-color: #f5f5f5;
  text-align: left;
}

td, th {
  padding: 0.5em 1em;
  border: 1px solid #ddd;
}

/* Preistabelle rechtsbündig */
td:last-child {
  text-align: right;
}
```

## PDF-Generierung

### Methode 1: Browser Print-to-PDF (empfohlen)

1. MkDocs Server starten:
   ```bash
   cd kundenordner && mkdocs serve
   ```

2. Browser öffnen: `http://localhost:8000`

3. Print-Dialog (Cmd+P / Ctrl+P):
   - Ziel: "Als PDF speichern"
   - Layout: Hochformat
   - Ränder: Standard oder Minimal
   - Hintergrundgrafiken: aktivieren

4. Speichern als: `QYYYY_MM_NNNN.pdf`

### Methode 2: weasyprint (automatisiert)

```bash
# Installation
pip install weasyprint

# Generierung
weasyprint http://localhost:8000/ANGEBOT-GERUEST/ angebot.pdf
```

**Hinweis**: Benötigt libgobject. Bei Problemen auf Browser-Methode ausweichen.

### Methode 3: MkDocs PDF Plugin

```yaml
# mkdocs.yml
plugins:
  - with-pdf:
      cover: true
      cover_title: "Angebot"
      cover_subtitle: "cognovis GmbH"
```

**Hinweis**: Erfordert zusätzliche System-Dependencies. Nicht immer zuverlässig.

## Header/Footer für PDF

### Variante A: CSS @page (nur Chrome/Chromium)

Die CSS @page-Regel (siehe extra.css oben) funktioniert nur eingeschränkt in Browsern.

### Variante B: Deckblatt als Markdown

Füge am Anfang des Angebots ein Deckblatt hinzu:

```markdown
<div class="cover-page">

# Angebot

**Angebots-Nr.**: QYYYY_MM_NNNN
**Datum**: TT.MM.JJJJ
**Gültig bis**: TT.MM.JJJJ

---

**An:**
Kundenname
Straße
PLZ Ort

---

**Von:**
cognovis GmbH
Schrödersweg 27
22453 Hamburg

</div>

<div style="page-break-after: always;"></div>

[Rest des Angebots...]
```

### Variante C: Fußzeile im Markdown

Am Ende jeder Seite oder am Dokumentende:

```markdown
---

<small>
cognovis GmbH • Schrödersweg 27 • 22453 Hamburg
Tel: +49 (40) 386 60 521 • info@cognovis.de • www.cognovis.de
HRB 28909 • USt-ID: DE118620281
</small>
```

## Qualitätskontrolle vor PDF-Export

- [ ] Seitenumbrüche sinnvoll (keine einzelnen Zeilen am Seitenende)
- [ ] Tabellen nicht über Seitengrenzen gebrochen
- [ ] Angebotsnummer korrekt
- [ ] Datum und Gültigkeit aktuell
- [ ] Empfängeradresse vollständig
- [ ] Preise korrekt formatiert (EUR, Tausendertrennzeichen)
