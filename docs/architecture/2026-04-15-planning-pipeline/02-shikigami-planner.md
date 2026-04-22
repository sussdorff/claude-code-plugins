# Shikigami-Planner — Design & Involvement Map

Der Shikigami-Planner ist **Maltes persönlicher Planning-Agent** für die
Phasen 1–7 der Planning-Pipeline (siehe [01-full-pipeline.md](01-full-pipeline.md)).
Er gehört zur **Shikigami-Familie** — ausschließlich Maltes Agent-Infrastruktur,
nicht Teil von Produkt-Deployments (Mira, Praxis-Runtime etc.).

## Abgrenzung

| Kontext | Wer agiert |
|---------|------------|
| Malte plant/entwickelt (egal welches Repo) | Shikigami-Familie |
| Praxis nutzt Mira-Produkt | Mira-eigene Agents, eigene Regeln |

**vs. AFK Dispatcher:** Zwei getrennte Agents. Shikigami-Planner = Phasen 1–7
(Planning). AFK Dispatcher = Phasen 9–10 (Engineering Execution). Sie teilen
sich keine Queue, keine Kalibrierung. Klare Domänen-Trennung.

**vs. Mira-Agents:** Shikigami liest Agent-Deskriptoren (`.md`-Dateien mit
Rolle/Tools) als **Kontext** — um zu wissen, was in einem geplanten Feature
schon existiert. Er ruft Mira-Agents **nicht auf** (keine Side-Effects,
keine PII-Risiken).

**Testing von Mira-Agents** läuft weiterhin über die bestehende Test-
Infrastruktur (holdout-validator, playwright-tester, uat-validator,
Pester/pytest). Nicht Shikigamis Zuständigkeit.

## Human-Involvement-Stufen

| Stufe | Bedeutung |
|-------|-----------|
| **🔴 HARD** | Nur Malte. **Unverletzlich** — kein Session-Override. |
| **🟠 SOFT** | Shikigami entwirft, Malte bestätigt. |
| **🟡 SIM** | Shikigami entscheidet autonom, Malte bekommt Summary. |
| **🟢 AUTO** | Kein Human, kein Shikigami — rein mechanisch. |

### Phase-für-Phase

| Phase | Checkpoint | Stufe |
|-------|------------|-------|
| 1 Refine | Rückfragen beantworten | 🔴 HARD |
| 1 Refine | Brief approven | 🟠 SOFT |
| 2 Council | Profil auswählen | 🟡 SIM |
| 2 Council | *weiter / überarbeiten / verwerfen* | 🔴 HARD |
| 3 Pitch | Pitch redigieren | 🟠 SOFT |
| 3 Pitch | "Überzeugt der Pitch?" | 🔴 HARD |
| 4 Scenarios | Vollständigkeit prüfen | 🟡 SIM |
| 5 Epic/Bead | Zuschnitt | 🟡 SIM |
| 6 Arch-Review | ADR approven | 🟠 SOFT |
| 7 Readiness | PASS/CONCERNS/FAIL | 🟢 AUTO |
| 7 Readiness | CONCERNS-Routing | 🟠 SOFT |

**Drei unverletzliche HARD-Punkte:**
1. Verwerfen-Entscheidung nach Council (billig-scheitern-Mechanismus)
2. Pitch-Überzeugung (Bauchgefühl nicht delegierbar)
3. Architektur-Strategie bei Konflikten (Trade-off-Wertentscheidung)

## Autonomie-Modell

**Konfidenz-basiert.** Shikigami liefert bei jeder SIM/SOFT-Entscheidung eine
Confidence (0-100%). Liegt sie unter dem Threshold für diesen Entscheidungstyp,
eskaliert er automatisch eine Stufe hoch.

**Start-Defaults** (hart im Agent-Prompt):

| Entscheidungstyp | Default-Threshold |
|------------------|-------------------|
| Council-Profil-Wahl | 70% |
| Scenarios-Vollständigkeit | 80% |
| Bead-Zuschnitt (S/M Routing) | 90% |
| ADR-Konsistenz-Check | 85% |
| Readiness-CONCERNS-Routing | 80% |

**Self-Update:** Shikigami darf sein eigenes Profil (`shikigami-profile.md`)
auf Rückfrage aktualisieren. Wenn er feststellt "ich war in den letzten 10
Scenarios-Approvals immer richtig — Threshold auf 70% runter?", fragt er dich
einmal, dann ändert er die Zahl im Profil. **Cross-Cutting-Prinzip:** das
soll für alle profilbasierten Agents gelten, nicht nur Shikigami.

## Kalibrierung

### Cold-Start (Hybrid)

1. **Retroaktiv aus open-brain:** liest letzte ~90 Tage Sessions, Bead-
   Entscheidungen, Session-Summaries. Extrahiert Muster
   (Verwerfungs-Begründungen, Pitch-Tonalität, Size-Intuition).
2. **Kurzes Interview (10 Fragen):** einmalig beim ersten Start, füllt
   Lücken, die aus Memory nicht klar sind.
3. **Konservative Defaults** wo immer noch unklar: alles SOFT, niedrige
   Confidence-Annahmen.

### Drift-Erkennung

**Rolling Metric** (automatisch):
- Zustimmungsrate der letzten 30 Entscheidungen pro Typ wird permanent
  getrackt.
- Fällt sie unter Threshold → Auto-Downgrade in SOFT-Mode + Notification.

**Monatlicher Retro** (manuell):
- Shikigami zeigt 20 repräsentative Entscheidungen + Zustimmungsrate.
- Du bestätigst / korrigierst im Batch.
- Qualitativer Lernimpuls, der über reine Quote hinausgeht.

### Feedback-Loop

Bei jeder Korrektur einer Shikigami-Entscheidung: **Kurzer Reason-Prompt**
("3 Sekunden: warum hast du das geändert?"). Ein Satz reicht. Pro
Entscheidungstyp deaktivierbar. Das ist der wertvollste Lerndatenpunkt.

## Scope & State

**Scope:** Global mit Project-Overrides.
- `~/.claude/shikigami/profile.md` — Basis-Profil (Maltes Präferenzen)
- `<projekt>/.claude/shikigami-overrides.md` — projektspezifische Overrides

**State-Aufteilung** (Hybrid):
- **Profil als Datei** (`shikigami-profile.md`): lesbar, editierbar,
  git-versioniert. Du kannst manuell rein.
- **History + Feedback in open-brain** (Tag-Namespace `shikigami:planner:*`):
  jede Entscheidung, Feedback-Reason, Confidence. Queryable,
  analytics-fähig.

## Modell

**Zwei-Tier:**
- **Haiku** für Routing/Sub-Tasks: Council-Profil-Wahl, Size-Check,
  Scenario-Coverage-Scan, Readiness-Check. Schnell und billig.
- **Opus (4.6, 1M context)** für Dialog-Phasen und tiefe Entscheidungen:
  `/refine`, `/pitch`-Redaktion, ADR-Entwurf. Maximaler Kontext, beste
  Kalibrierung mit allen Memories gleichzeitig lesbar.

Sonnet kommt bewusst nicht vor — entweder schnell (Haiku) oder tief (Opus).

## Interaktion

**Ein Agent, zwei Modi** — umschaltbar beim Start oder per Session-Marker.

### Sync-Mode (Begleiter)

Du bist im Terminal, Shikigami ist Dialog-Partner. SIM-Entscheidungen
zeigt er kurz, du kannst jederzeit eingreifen.

### Async-Mode (AFK-Dispatcher)

Trigger: **Auto bei AFK-Marker**. Du setzt einmal `afk=true` (z.B. via
`/afk on`), Shikigami übernimmt alle SOFT/SIM-Gates autonom, HARD-Punkte
werden in die Queue gestellt. Beim Deaktivieren (`/afk off`) normaler
Begleit-Modus.

### Rückkanal (Async → Sync)

**Kombination:**
- **Beads-Queue:** HARD-Entscheidungen landen als Beads mit
  `assignee=malte`, sichtbar in `bd ready`.
- **Morning-Briefing:** beim nächsten `cld`-Start zeigt Shikigami eine
  kompakte Zusammenfassung:
  ```
  Shikigami-Briefing (letzte 8h):
  ✓ 3 autonom entschieden: [Liste]
  ⚠ 2 warten auf dich: [Liste mit Links]
  ✗ 1 Sackgasse: [Kurz begründet]
  📈 Self-Update vorgeschlagen: [optional]
  ```

## Audit-Trail

**Tag pro Artefakt.** Jedes Artefakt (Bead, ADR, Pitch, idea-brief,
council-review) bekommt Metadata:
```yaml
decided_by: shikigami | malte
confidence: 0.87          # falls shikigami
reasoning_log: ob://shikigami:planner:decision:<uuid>
```

**Undo-Pfad:** Shikigami-getätigte Entscheidungen lassen sich per Filter
finden und zurückdrehen (`bd list --decided-by=shikigami --since=2d`).

**Log in open-brain:** Pro Entscheidung ein strukturierter Memory-Eintrag
mit Input-Summary, Output, Confidence, angewendeter Regel — auditierbar,
wenn mal gefragt wird *"warum hat er damals so entschieden?"*.

## Offene Punkte (vertagt)

- **PII-Filter** in Shikigamis Memory-Pipeline: Pattern-Matching?
  Modell-basiert? Whitelist? Entscheidung nötig, bevor er Mira-Repo-
  Kontext aufnehmen darf.
- **Morning-Briefing als eigener Skill:** `/briefing`-Skill oder
  automatischer Trigger im SessionStart-Hook?
- **Self-Learning Standard-Dokument:** Wie genau triggert ein Agent die
  Profil-Aktualisierung? Reasoning-Protokoll? Das ist ein
  cross-cutting Prinzip, gehört ins Standards-Repo.
