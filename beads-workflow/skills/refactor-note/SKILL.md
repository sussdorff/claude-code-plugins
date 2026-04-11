---
name: refactor-note
description: Refactor Note
---
# Refactor Note

Erstellt ein Backlog-Bead fuer Code der refactored werden sollte, aber nicht zum aktuellen Task gehoert.

Verwendung: `/refactor-note <Beschreibung des Problems>`

Beispiele:
- `/refactor-note Funktion transformQueueEntry ist in 3 Dateien dupliziert`
- `/refactor-note TypeScript any-Usage in api-client.ts entfernen`
- `/refactor-note Shared types zwischen Backend und Frontend extrahieren`

---

Erstelle ein neues Bead mit dem `[REFACTOR]` Prefix:

```bash
bd create --title="[REFACTOR] $ARGUMENTS" --type=task --priority=3
```

Nach dem Erstellen:
1. Zeige die Bead-ID kurz an
2. Arbeite am aktuellen Task weiter - lass dich nicht ablenken
