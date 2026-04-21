---
harness: claude
skill: vision
---

# Vision — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific commands.
A Codex user does NOT need to read this file.

## Exit Protocol Commands (Claude)

After the user selects ideas to pursue, offer:

```
Soll ich dafür ein Bead anlegen (`bd create`) oder einen Epic ausarbeiten (`/epic-init`)?
```

- `bd create` — creates a beads issue for the selected idea
- `/epic-init` — guided planning dialog for the idea as an epic
