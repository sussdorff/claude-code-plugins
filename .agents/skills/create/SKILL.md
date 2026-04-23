---
name: create
description: >-
  Smart bead creation with type guidance, size routing, and auto-scenario generation for features.
  Use when creating beads, adding work items, or when user describes something to build/fix/improve.
  Triggers on bead erstellen, create bead, neues bead, new bead, bd create.
---

# Smart Bead Create

Intelligente Bead-Erstellung mit Typ-Coaching, Groessen-Routing und automatischer
Szenario-Generierung fuer Features.

## Input

```
<Beschreibung des Vorhabens> [optionale Flags]
```

---

## Phase 0: Input parsen

Falls kein Vorhabenstext uebergeben wurde: Frage "Was soll gemacht werden? Beschreib kurz das Vorhaben."

Falls Vorhabenstext vorhanden: Verwende ihn als Beschreibung des Vorhabens.

---

## Phase 1: Typ-Klassifikation

Analysiere die Beschreibung und klassifiziere den Typ anhand dieser Definitionen:

### Typ-Definitionen

| Typ | Definition | Erkennungsmuster | Beispiele |
|-----|-----------|------------------|-----------|
| **feature** | Neue, **user-sichtbare** Funktionalitaet. Der Endnutzer kann danach etwas tun, sehen oder erleben, das vorher nicht moeglich war. | "User kann...", "Neue Seite/View/Dialog", "Anzeige von...", neuer Workflow, neue API die ein UI bedient | "Patient kann Termin online buchen", "Dashboard zeigt Umsatz-Chart", "eRezept-Versand an Apotheke" |
| **task** | Interne, technische Arbeit die fuer den User **nicht direkt sichtbar** ist. Infrastruktur, Tooling, Konfiguration, Refactoring, Migration, Setup. | "Einrichten", "Migrieren", "Konfigurieren", "Aufraumen", "Refactoring", CI/CD, Datenbank-Schema, Dependency-Update | "PostgreSQL auf v16 upgraden", "CI Pipeline fuer E2E Tests", "API-Client auf neues SDK migrieren" |
| **bug** | Etwas funktioniert **nicht wie erwartet** oder ist **kaputt**. Regression, Fehler, Crash, falsches Verhalten. | "Fehler", "geht nicht", "kaputt", "Crash", "falsch", "sollte X aber macht Y", Stacktrace, Error | "Login-Button reagiert nicht auf Mobile", "Rechnung zeigt falschen MwSt-Satz", "App crasht bei leerer Liste" |
| **chore** | Wartung, Housekeeping, Abhaengigkeiten. Kein neues Verhalten, keine Bug-Behebung. Routine. | "Update", "Aufraumen", "Lint-Fehler", "Dependency bump", "Docs aktualisieren", Versions-Bump | "ESLint-Warnings beseitigen", "README aktualisieren", "Node.js Security Patch einspielen" |

### Entscheidungsbaum

```
Ist etwas KAPUTT oder FEHLERHAFT?
  → JA: bug

Kann der ENDNUTZER danach etwas NEUES tun/sehen?
  → JA: feature
  → NEIN: Ist es Routine/Wartung ohne Verhaltensaenderung?
    → JA: chore
    → NEIN: task
```

### Groessen-Check

Bewerte gleichzeitig die Groesse:

| Signal | Aktion |
|--------|--------|
| Mehrere unabhaengige Teile, verschiedene Bereiche betroffen, "und ausserdem" | **Zu gross fuer einen Bead.** Empfehle `/epic-init` |
| Ein klar abgegrenztes Thema, 1-3 Sessions Arbeit | **Passt als einzelner Bead** |
| Kleiner Fix, Config-Aenderung, 30min Aufwand | **Passt als einzelner Bead** (micro/small) |

---

## Phase 2: Vorschlag praesentieren

Zeige dem User den Vorschlag:

```
## Bead-Vorschlag

**Titel:** [praegnanter Titel]
**Typ:** [feature/task/bug/chore] — [1-Satz Begruendung warum dieser Typ]
**Prioritaet:** P2 (Standard, aenderbar)

**Beschreibung:**
[2-4 Saetze: Was, Warum, Fuer Wen]

[Falls Typ falsch erscheinen koennte, erklaere proaktiv:]
> Hinweis: Das klingt vielleicht nach Feature, ist aber ein **task** weil
> [Begruendung — z.B. "der User merkt davon nichts, es ist interne Infrastruktur"].
```

**Falls Groessen-Check "zu gross" ergab:**

```
Das Vorhaben hat mehrere unabhaengige Teile — ich empfehle `/epic-init` statt
eines einzelnen Beads. Damit bekommst du ein Epic mit Sub-Tasks und Abhaengigkeiten.

Soll ich `/epic-init "[Ziel]"` starten?
```

→ Bei "ja": Skill `epic-init` aufrufen und hier beenden.

**Frage:** "Passt Typ und Beschreibung? (ja / Aenderungen / anderer Typ)"

→ Bei Aenderungen: iterieren bis akzeptiert.

---

## Phase 3: Contract-Label Check (bei allen Typen)

Frage den User vor der Feature-Gate und Erstellung:

```
Beruehrt dieses Bead einen Architektur-Vertrag?

Beispiele: Ein ADR wird umgesetzt, ein Helper wird geaendert, ein Enforcer
wird hinzugefuegt, oder es gibt eine Luecke die einen neuen ADR/Helper/Enforcer braucht.

[ja / nein]
```

**Falls "ja":**

1. Setze das Label `touches-contract` (wird bei `bd create` als `--label touches-contract` uebergeben).

2. Injiziere dieses Template in die Bead-Description (vor den Acceptance Criteria):

```markdown
## Architecture Contracts Touched
- ADR-NNN (Name): <was der Bead tut, wie er den Contract nutzt>
- Helper: <pfad/zu/helper.ts>              # optional
- Enforcer-Proactive: <codegen/builder>    # optional
- Enforcer-Reactive: <lint-rule oder test> # optional

## Coverage Expected
- Packages: <liste der beruehrten Packages>
- Status nach Bead: <was wird gruen in der Matrix>

## Gaps to Close
- [ ] None
```

Erklaere dem User kurz:
> "Das Bead bekommt das Label `touches-contract` und die Pflicht-Sektion. Fuelle die drei
> Sub-Sektionen aus — der Linter (`bd lint --check=architecture-contracts`) prueft sie."

**Falls "nein":** Weiter ohne Label und ohne Template.

**Referenz:** `beads-workflow/skills/create/references/contract-sections.md`

---

## Phase 3.5: Feature-Gate (nur bei Typ = feature)

**PFLICHT fuer Features.** Wenn der akzeptierte Typ `feature` ist:

1. Nutze den konfigurierten Scenario-Generator im `bead-scenario` Mode, falls der Harness
   so einen Helper anbietet. Falls nicht, entwirf die Szenarien inline nach demselben Format:

```
Mode: bead-scenario
Bead-ID: NOCH_NICHT_ERSTELLT
Title: [Titel]
Description: [Beschreibung]

Generiere Szenarien basierend auf dieser Feature-Beschreibung.
Es gibt noch keinen Bead — arbeite mit Titel und Beschreibung statt bd show.
Gib die Szenarien als ## Szenario Markdown zurueck.
```

2. Zeige die generierten Szenarien dem User:

```
### Szenarien (auto-generiert)

[Szenario-Output vom Generator]
```

3. Frage: "Szenarien uebernehmen? (ja / anpassen / weglassen)"

→ Bei "ja": Szenarien werden in die Bead-Description integriert.
→ Bei "anpassen": User-Feedback einarbeiten, nochmal zeigen.
→ Bei "weglassen": Ohne Szenarien weiter (mit Hinweis dass sie spaeter nachgeholt werden koennen).

---

## Phase 4: Bead erstellen

Nach Handshake (Typ akzeptiert, Contract-Label ggf. gesetzt, bei Feature: Szenarien geklaert):

```bash
# Ohne touches-contract:
bd create --title="[Titel]" --type=[typ] --priority=[prio] --description="[Beschreibung]"

# Mit touches-contract:
bd create --title="[Titel]" --type=[typ] --priority=[prio] \
  --description="[Beschreibung inkl. Architecture Contracts Template]" \
  --label touches-contract
```

---

## Phase 4.5: Contract-Lint Smoke-Check (nur bei touches-contract)

Falls das Bead mit `touches-contract` Label erstellt wurde, fuehre sofort einen Lint-Check durch:

```bash
python3 beads-workflow/scripts/bd_lint_contracts.py --bead [neue-Bead-ID]
```

**Falls der Check fehlschlaegt:** Zeige die Fehlermeldungen dem User und bitte ihn,
die Sektion zu korrigieren (`bd update [ID] --description="..."`), bevor er mit der
Implementierung beginnt.

**Falls der Check erfolgreich ist:** Weiter mit der Ausgabe unten.

---

Ausgabe:

```
Bead [ID] erstellt: **[Titel]** ([typ], P[prio])
[Falls Feature mit Szenarien: "inkl. auto-generierter Szenarien"]
[Falls touches-contract: "inkl. Architecture Contracts Pflicht-Sektion — Lint: OK"]

Naechste Schritte:
- `/beads [ID]` — Implementierung starten
- `bd update [ID] --notes="..."` — Notizen ergaenzen
- `bd show [ID]` — Details anzeigen
```

---

## Regeln

1. **Typ-Vorschlag ist Pflicht** — niemals blind `--type=feature` setzen
2. **Begruendung ist Pflicht** — immer erklaeren WARUM dieser Typ
3. **Feature-Gate ist Pflicht** — bei Typ feature IMMER Scenario-Generator starten
4. **Handshake vor Erstellung** — niemals ohne User-Bestaetigung anlegen
5. **Epic-Routing** — zu grosse Vorhaben an `/epic-init` weiterleiten
6. **Sprache:** Deutsch fuer Kommunikation, Englisch fuer Code/technische Terme
7. **Keine Dauer-Schaetzungen** — nur relative Groessen ("klein", "komplex", "mehrere Sessions")
8. **Contract-Label ist opt-in** — NIEMALS `touches-contract` ohne explizite Bestaetigung setzen
9. **Lint-Smoke-Check bei touches-contract** — IMMER den Lint-Check nach Erstellung ausfuehren
