# IG Installation (`install-ig`)

Install a FHIR Implementation Guide into a local Aidbox instance.

**Wichtig:** Es gibt zwei klar getrennte Kontexte — BUILD und USE. Nicht verwechseln.

---

## Context A — BUILD (im IG-Repository)

Gilt nur wenn du **im IG-Source-Repo** arbeitest (`fhir-praxis-de`, `fhir-dental-de`) und einen neuen Build erzeugen willst für lokales Testen oder Release.

- **Wo:** `/Users/malte/code/fhir-praxis-de/` oder `/Users/malte/code/fhir-dental-de/`
- **Wer baut:** Normalerweise die CI (`.github/workflows/ig-release.yml`), die anschließend nach `npm.cognovis.de` publisht. Lokale Builds sind nur für Dev.
- **Lokaler Build:**
  ```bash
  bash scripts/build-package.sh
  # Erzeugt dist/<package-id>-<version>.tgz
  ```
- **⚠️ `dist/` ist NICHT Source of Truth.** Lokale Builds sind oft veraltet. Nach CI-Release immer die Registry nutzen (siehe Context B).
- Verwendung nur wenn du die IG gerade editierst und VOR dem CI-Release lokal testen willst.

**Known IG Projects:**

| Project | Canonical | Package ID | Registry |
|---------|-----------|------------|----------|
| fhir-praxis-de | `https://fhir.cognovis.de/praxis` | `de.cognovis.fhir.praxis` | `npm.cognovis.de` |
| fhir-dental-de | `https://fhir.cognovis.de/dental` | `de.cognovis.fhir.dental` | `npm.cognovis.de` |

`fhir-dental-de` depends on `fhir-praxis-de` — install praxis first.

---

## Context B — USE (im mira-adapters oder mira repo)

Gilt wenn du eine **fertig gebaute** IG in Aidbox laden willst — z.B. für Test-Imports, lokale Dev-Aidbox, Validierung.

- **Source of Truth:** `https://npm.cognovis.de` (Verdaccio). CI in den IG-Repos publisht nach jedem Release dorthin.
- **Niemals** die `dist/`-Ordner der IG-Repos verwenden — die sind nicht autoritativ.

### Aktuelle Latest-Versionen abfragen

```bash
curl -s https://npm.cognovis.de/de.cognovis.fhir.praxis | jq -r '.["dist-tags"].latest'
curl -s https://npm.cognovis.de/de.cognovis.fhir.dental | jq -r '.["dist-tags"].latest'
```

### Paket von Registry ziehen

```bash
# praxis
PRAXIS_VERSION=$(curl -s https://npm.cognovis.de/de.cognovis.fhir.praxis | jq -r '.["dist-tags"].latest')
PRAXIS_TARBALL=$(curl -s https://npm.cognovis.de/de.cognovis.fhir.praxis | jq -r ".versions[\"$PRAXIS_VERSION\"].dist.tarball")
curl -sL "$PRAXIS_TARBALL" -o /tmp/praxis.tgz

# dental
DENTAL_VERSION=$(curl -s https://npm.cognovis.de/de.cognovis.fhir.dental | jq -r '.["dist-tags"].latest')
DENTAL_TARBALL=$(curl -s https://npm.cognovis.de/de.cognovis.fhir.dental | jq -r ".versions[\"$DENTAL_VERSION\"].dist.tarball")
curl -sL "$DENTAL_TARBALL" -o /tmp/dental.tgz
```

Registry ist read-only anonym erreichbar — keine Auth nötig.

### In lokale Aidbox laden

Setup:
- Host: `localhost:8080`
- Container: `mira-aidbox-1`
- Auth: Admin-Client aus `/Users/malte/code/mira/.env` (`AIDBOX_ADMIN_ID` / `AIDBOX_ADMIN_PASSWORD`) — der `basic:secret`-Client hat in mira keine AccessPolicy und bekommt 403.

**Aidbox ≥ 2511**: `$fhir-package-install` nimmt `<name>@<version>` als `valueString` und akzeptiert eine **custom registry** als Parameter im selben Request. Kein `docker cp` nötig, Aidbox zieht direkt von der Registry.

Das alte `file://`-Format funktioniert in 2602 **nicht** (`Unsupported version syntax` — Aidbox parst die Version aus der URL und scheitert bei Empty-String). Das gleiche gilt für separate `name`+`version`-Parameter (`unmatched-element-in-closed-slicing`). Nur `@version` als ein `valueString` ist korrekt.

```bash
# Latest Versionen holen
PRAXIS_VERSION=$(curl -s https://npm.cognovis.de/de.cognovis.fhir.praxis | jq -r '.["dist-tags"].latest')
DENTAL_VERSION=$(curl -s https://npm.cognovis.de/de.cognovis.fhir.dental | jq -r '.["dist-tags"].latest')

# Auth aus mira .env
source /Users/malte/code/mira/.env
AUTH="-u $AIDBOX_ADMIN_ID:$AIDBOX_ADMIN_PASSWORD"

# Praxis ZUERST (Dependency für dental)
curl -s $AUTH -X POST "http://localhost:8080/fhir/\$fhir-package-install" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Parameters\",\"parameter\":[
    {\"name\":\"package\",\"valueString\":\"de.cognovis.fhir.praxis@${PRAXIS_VERSION}\"},
    {\"name\":\"registry\",\"valueString\":\"https://npm.cognovis.de\"}
  ]}"

# Dann dental
curl -s $AUTH -X POST "http://localhost:8080/fhir/\$fhir-package-install" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Parameters\",\"parameter\":[
    {\"name\":\"package\",\"valueString\":\"de.cognovis.fhir.dental@${DENTAL_VERSION}\"},
    {\"name\":\"registry\",\"valueString\":\"https://npm.cognovis.de\"}
  ]}"
```

**Override bei kaputten transitiven Dependencies:** Wenn eine Abhängigkeit fehlt oder gepinnt werden muss, zusätzlich einen `override`-Parameter mitgeben (siehe [Aidbox-Doku](https://www.health-samurai.io/docs/aidbox/reference/package-registry-api.md#dependency-overrides)).

### Installation verifizieren

```bash
curl -s -u basic:secret "http://localhost:8080/fhir/StructureDefinition?url:contains=fhir.cognovis.de/praxis&_summary=count"
curl -s -u basic:secret "http://localhost:8080/fhir/CodeSystem?url:contains=fhir.cognovis.de/praxis&_summary=count"
curl -s -u basic:secret "http://localhost:8080/fhir/ValueSet?url:contains=fhir.cognovis.de/praxis&_summary=count"

# Dental analog
curl -s -u basic:secret "http://localhost:8080/fhir/StructureDefinition?url:contains=fhir.cognovis.de/dental&_summary=count"
```

Erwartet: praxis StructureDefinitions > 100. Falls 0 nach Install → Installation fehlgeschlagen, Container-Logs prüfen.

### Regeln im USE-Kontext

- **Do NOT** `build-package.sh` im mira-adapters/mira Repo aufrufen — das ist BUILD-Kontext und gehört nicht hierher.
- **Do NOT** die `dist/`-Ordner der IG-Repos durchwühlen — Registry ist Source of Truth.
- **Do NOT** strict validation global einschalten — nutze `$validate` mit expliziter Profil-Parameter.
- **Do NOT** PUT/POST Test-Ressourcen für Validierung — nutze `$validate` um keine Daten zu pollen.
