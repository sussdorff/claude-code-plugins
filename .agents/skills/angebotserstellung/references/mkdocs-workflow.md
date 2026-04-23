# MkDocs Workflow für Angebote

## Build & Package Workflow

```bash
# 1. Build
cd /pfad/zum/projekt
mkdocs build

# 2. Standalone HTML erstellen (Pfade korrigieren)
cp site/DOKUMENTNAME/index.html standalone.html
sed -i '' 's|"\.\./assets/|"assets/|g' standalone.html
sed -i '' 's|"\.\./stylesheets/|"stylesheets/|g' standalone.html
sed -i '' "s|'\.\./assets/|'assets/|g" standalone.html

# 3. ZIP-Paket erstellen
mkdir -p package
cp standalone.html package/index.html
cp docs/DOKUMENTNAME.md package/
cp -r site/assets package/
cp -r site/stylesheets package/

# 4. Unnötige Dateien entfernen (Suche, Source Maps)
rm -rf package/assets/javascripts/lunr
rm -rf package/assets/javascripts/workers
rm -f package/assets/javascripts/*.map
rm -f package/assets/stylesheets/*.map

# 5. ZIP erstellen
zip -r Angebot.zip package
rm -rf package standalone.html
```

## Kritische Markdown-Regeln für MkDocs

### Zeilenumbrüche werden ignoriert

MkDocs/CommonMark ignoriert einfache Zeilenumbrüche. Mehrere Zeilen werden zu einer Zeile zusammengezogen.

```markdown
# FALSCH - wird zu einer Zeile
**Anbieter:**
cognovis GmbH
Schrödersweg 27
22453 Hamburg

# Ergebnis: "Anbieter: cognovis GmbH Schrödersweg 27 22453 Hamburg"

# RICHTIG - Interpunkte als Trenner
**Anbieter:** cognovis GmbH · Schrödersweg 27 · 22453 Hamburg
```

**Regel:** Für Adressblöcke, Kontaktdaten und Metadaten `·` (Interpunkt) als Trenner verwenden.

### Bullets nach Label - IMMER Leerzeile

```markdown
# FALSCH - wird nicht als Liste gerendert
**Warum jetzt?**
- Item 1
- Item 2

# RICHTIG
**Warum jetzt?**

- Item 1
- Item 2
```

### Tabellen - Leerzeile davor und danach

```markdown
Text davor.

| Spalte 1 | Spalte 2 |
|----------|----------|
| Wert 1   | Wert 2   |

Text danach.
```

## Pfad-Problem bei MkDocs

MkDocs generiert HTML in Unterordnern mit relativen Pfaden (`../assets/`).

Für standalone HTML müssen diese zu `assets/` korrigiert werden.

## PDF-Generierung

MkDocs selbst kann kein sauberes PDF. Optionen:

1. **Browser Print-to-PDF** - Cmd+P, "Als PDF speichern"
   - Print-CSS in extra.css blendet Navigation aus
   - Problem: Browser fügt Header/Footer hinzu

2. **Chrome Headless** - `--print-to-pdf-no-header` funktioniert nicht zuverlässig

3. **Empfehlung:** HTML/Markdown als primäres Format versenden, PDF nur auf Anfrage

## Typische extra.css für Angebote

```css
/* Print-Styles */
@media print {
  .md-header,
  .md-sidebar,
  .md-footer {
    display: none !important;
  }

  .md-main__inner {
    margin: 0;
    padding: 0;
  }

  table {
    page-break-inside: avoid;
  }
}
```
