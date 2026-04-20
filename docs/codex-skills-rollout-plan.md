# Codex Skills Rollout Plan

Stand: 2026-04-20 (ursprünglich 2026-04-15)

## Ziel

Die Skills aus diesem Repo sollen in Codex nutzbar werden, ohne zwei dauerhaft
auseinanderlaufende Skill-Bestände zu pflegen.

## Ausgangslage

- Die bestehenden Architektur-Notizen gehen bereits von einer portablen
  Skill-Schicht aus: `AGENTS.md`, `agentskills.io` und `just` sollen Claude
  Code, Codex und pi gemeinsam bedienen.
- Die Skills in diesem Repo liegen heute plugin-orientiert unter
  `*/skills/<name>/SKILL.md`.
- Codex kann Skills offiziell aus repo-lokalen `.agents/skills`-Ordnern sowie
  aus `$HOME/.agents/skills` laden. Plugins sind in Codex die Distributionseinheit,
  Skills das Authoring-Format.
- **Maschinen-Realität 2026-04-20**: Auf dieser Maschine liegt der aktiv geladene
  Codex-Skill unter `~/.codex/skills/frontend-skill/`. Weder `./.agents/skills`
  noch `~/.agents/skills` existieren. Der tatsächlich von der hier laufenden
  Codex-Version benutzte Discovery-Pfad muss daher vor dem Pilot verifiziert
  werden (siehe CCP-c2p Phase 0). Bis zur Verifikation gilt `~/.codex/skills`
  als belastbarer user-scoped Zielpfad; `.agents/skills` bleibt die
  repo-interne Authoring-/Export-Schicht, kein garantierter Ladeort.
- Viele vorhandene Skills sind noch Claude-spezifisch formuliert oder hängen an
  Claude-spezifischen Tools, Slash-Commands oder Workflow-Annahmen.

## Nicht-Ziele

- Kein Big-Bang-Port aller Skills in einem Schritt.
- Kein doppeltes manuelles Pflegen derselben Skill-Anweisung in zwei Verzeichnissen.
- Kein Umbau des bestehenden Plugin-Layouts, bevor ein kleiner Codex-Pilot
  tatsächlich funktioniert.

## Zielbild

Es gibt eine kleine, klar abgegrenzte Menge portabler Skills, die:

- im Repo unter einer Authoring-/Export-Schicht (`.agents/skills/`) gepflegt
  werden, die die Source-of-Truth-Sicht auf portable Skills darstellt — ob
  diese Schicht von der laufenden Codex-Version direkt geladen wird, ist
  pending Phase-0-Verifikation in CCP-c2p; bis dahin ist der belastbare
  Codex-Ladepfad `~/.codex/skills/` (user-scoped),
- weiterhin aus den fachlichen Plugin-Quellen dieses Repos abgeleitet werden,
- Claude-spezifische und Codex-spezifische Adapter explizit trennen,
- später bei Bedarf auch als Codex-Plugin gebündelt werden können.

## Rollout

### Phase 1: Pilot-Skills auswählen

Zuerst nur instruction-heavy Skills portieren, die wenig Harness-spezifische
Tooling-Annahmen haben.

Empfohlene Startmenge:

1. `project-context`
2. `spec-developer`
3. `bug-triage`

Bewusst später:

- `beads-workflow/*` wegen `cmux`, Worktrees, Review-Loops und Claude-Agenten
- `dev-tools/codex` weil das ein Codex-Wrapper für Claude ist, nicht ein
  portabler Fach-Skill
- Skills mit hartem Bezug auf Claude-spezifische Toolnamen oder Slash-Commands

### Phase 2: Portability-Split einführen

Für jeden Pilot-Skill gilt:

1. Portable Kernanweisung identifizieren.
2. Harness-spezifische Teile auslagern.
3. Skripte nur behalten, wenn sie wirklich deterministisches Verhalten liefern.

Praktische Regel:

- `SKILL.md` beschreibt die fachliche Aufgabe und den Workflow.
- Claude-spezifische Invocation-Hinweise, Slash-Commands und Toolnamen bleiben
  außerhalb des portablen Kerns.
- Optionales Codex-Metadaten-Tuning kommt in `agents/openai.yaml`, nicht in den
  eigentlichen Fachtext.

### Phase 3: Repo-Layout für Codex einführen

Im Repo eine neue, bewusst kleine Schicht einführen:

```text
.agents/
  skills/
    project-context/
    spec-developer/
    bug-triage/
```

Diese Ordner sind zunächst ein Pilot-Interface für Codex, nicht sofort die neue
Source of Truth für alle Skills.

Kurzfristig zulässige Modelle:

- Symlink von `.agents/skills/<name>` auf bestehende Skill-Ordner
- Kopier-/Sync-Skript, das portable Skills aus den Plugin-Ordnern erzeugt

Bevorzugt:

- ein kleines Sync-Skript, damit die Repo-Struktur explizit bleibt und keine
  stillen Symlink-Effekte entstehen

### Phase 4: Installationspfad definieren

Zwei Nutzungsmodi trennen:

1. **Repo-scoped**
   Codex startet im Repo und entdeckt den in CCP-c2p Phase 0 verifizierten
   repo-internen Pfad direkt (Kandidat: `.agents/skills`, sofern die laufende
   Codex-Version das unterstützt; ansonsten wird in Phase 0 ein alternativer
   Pfad festgelegt oder der Repo-Export läuft über Sync in `~/.codex/skills`).

2. **User-scoped**
   Ausgewählte Skills werden nach `~/.codex/skills/` (belegter realer
   Ladepfad, Stand 2026-04-20) gespiegelt, wenn sie repo-übergreifend verfügbar
   sein sollen. Frühere Annahme `$HOME/.agents/skills` ist gegen die laufende
   Codex-Version zu prüfen, bevor CCP-u01 den Zielpfad hart setzt.

Wichtig:

- Für lokalen Alltag zuerst repo-scoped starten.
- User-scoped erst einführen, wenn klar ist, welche Skills wirklich global
  nützlich sind.
- Plugin-Paketierung erst nach funktionierendem lokalen Pilot.

### Phase 5: Validierung

Für jeden Pilot-Skill prüfen:

1. explizite Invocation funktioniert
2. implizite Invocation triggert nicht zu breit
3. optionale Skripte laufen relativ zum Skill-Verzeichnis
4. Skill bleibt auch ohne Claude-spezifische Zusatzinstruktionen brauchbar

Abnahme für den Pilot:

- mindestens 3 Skills in Codex direkt nutzbar
- keine manuell divergierenden Doppelversionen
- klar dokumentierte Stellen für Codex-spezifische Metadaten

## Design-Regeln

- Portabel zuerst: Skill-Inhalt vor Harness-Integration.
- Progressive Disclosure erhalten: kurze, harte `description`; Details erst in
  `SKILL.md`.
- Eine Aufgabe pro Skill.
- `AGENTS.md` bleibt globale Arbeitsanweisung; Skills sind fokussierte
  Workflow-Bausteine.
- `just`-Rezepte und normale CLIs bleiben der gemeinsame Ausführungspfad, wenn
  ein Skill deterministische Shell-Schritte braucht.

## Offene Entscheidungen

1. **Source of Truth**
   Bleiben die Plugin-Skill-Ordner führend, oder werden portable Skills später
   nach `.agents/skills` gehoben?

2. **Sync-Mechanik**
   Reicht ein einfaches Repo-Skript, oder soll `project-setup` / ein Plugin-Tool
   den Export in `.agents/skills` übernehmen?

3. **Metadaten-Tiefe**
   Wo lohnt sich `agents/openai.yaml` wirklich, und wo reicht ein schlankes
   `SKILL.md`?

## Nächste Beads

Die folgenden Work-Items sind bereits angelegt und nach Wave-Review
2026-04-20 überarbeitet:

1. `CCP-tkd` — [TASK] Extract portable skill core from Claude-specific wrappers
2. `CCP-u01` — [TASK] Add sync-codex-skills script for repo/user installation
   (inkl. `--check` Mode als Enforcer-Reactive)
3. `CCP-c2p` — [FEATURE] Codex pilot: 3 portable skills (mit Phase 0
   Discovery-Pfad-Verifikation als blockierendem ersten Schritt)
4. `CCP-50y` — [TASK] Convert next 10 candidate skills to agentskills-compatible
   format

## Nach dem Skill-Pilot (Folge-Arbeit für Codex)

Skills sind nicht der einzige Claude-Surface, der Codex-Reichweite bekommen soll.
Nach erfolgreichem Abschluss der 4 Beads oben steht die Agent-Schicht an. In
dieser Reihenfolge:

1. **Codex-Port `session-close`**
   Session-close ist die erste Agent-Portierung. Grund: session-close ist der
   kritische Abschlusspfad (Double-Merge, Changelog, CalVer, Dolt push, bead
   close) und hat vergleichsweise klar abgegrenzte Verantwortlichkeiten.
   Codex nutzt ein eigenes Agent-Format (Custom TOML Agents in
   `~/.codex/agents/`, plus Built-ins default/worker/explorer). Der Port muss
   die Claude-Subagent-Semantik (Tool-Whitelist, isolation, model override)
   auf Codex-Äquivalente abbilden — wo diese fehlen, wird das explizit
   dokumentiert.

2. **Codex-Port Wave-/Bead-Orchestrator**
   Parallel zum Skill-Rollout läuft `CCP-2vo` (Single-pane wave mode —
   bead-orchestrator redesign). Sobald dieser Epic stabil ist, wird der
   Orchestrator für Codex portiert. Abhängigkeit: muss nach `CCP-2vo` und
   nach dem session-close-Port kommen, weil Orchestrator-Ende session-close
   triggert.

Dependency-Kette der Folge-Beads:

- `CCP-9yd` (session-close Codex-Port) depends on `CCP-50y` — Skills-Pilot
  muss zuerst funktionieren, bevor Agent-Ports sinnvoll sind.
- `CCP-67x` (Wave-/Bead-Orchestrator Codex-Port) depends on `CCP-9yd`
  **und** `CCP-2vo` — braucht den session-close-Port als Handoff-Ziel und
  die Single-Pane-Shape aus dem Claude-seitigen Redesign.

## Referenzen

- `docs/architecture/2026-04-14-session/03-higher-order-prompts-and-just-architecture.md`
- `docs/architecture/2026-04-14-session/04-claude-codex-pi-orchestration.md`
- `docs/architecture/2026-04-14-session/06-bead-generation-plan.md`
- https://developers.openai.com/codex/skills
- https://agentskills.io/
