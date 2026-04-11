# Wave Orchestrator — Error Recovery

Read this when a bead fails, a reviewer disconnects, merge conflicts appear, or session
close collides. The orchestrator should reference this file when entering error states
during Phase 5 or Phase 6.

---

## Bead Fails During Implementation

Don't retry automatically. Report to user with the error from the screen output.
The user can:
- Fix manually in the pane
- Skip the bead and continue with the wave
- Abort the wave

## Reviewer Disconnect (No Impl Surface)

When a cmux-reviewer reports `impl_surface: none` or `No impl surface available`, the
reviewer cannot send fixes back to the implementer. This happens when the impl surface
was closed or became unreachable.

**The orchestrator may intervene in this specific case:**

1. Read the reviewer surface to understand what fixes are needed
2. If the reviewer already sent a cmux command that didn't arrive, re-send it:
   ```bash
   cmux send --surface surface:<reviewer> "re-review\n"
   ```
3. If the reviewer is waiting for fixes that the implementer already committed,
   trigger re-review directly

**Otherwise**: Stay out of the communication between reviewer and implementer. The
bead-orchestrator and cmux-reviewer coordinate autonomously — only intervene when you
can see that a cmux send was attempted but didn't arrive.

## Merge Conflicts During Session Close

Common when multiple beads in the same wave touch shared files (routing, test setup,
app entry points). The session-close agent attempts to resolve these automatically,
but may fail.

**If you see merge conflict errors on a surface:**

1. `cd` into the worktree:
   ```bash
   cd /path/to/repo/.claude/worktrees/bead-<id>/
   ```
2. Find conflicted files:
   ```bash
   git diff --name-only --diff-filter=U
   ```
3. Resolve conflicts:
   - For files not directly related to this bead's feature: `git checkout --theirs <file>`
   - For the bead's own files: manual merge (keep both sides)
4. Stage and commit:
   ```bash
   git add <resolved-files>
   git commit -m "merge: resolve conflicts — integrate <bead-id> with parallel changes"
   ```
5. The session-close agent will detect the clean state and continue automatically

## Session Close Collision

When multiple beads finish around the same time, their session-close agents can collide
on `git push` (one pushes, the other needs to pull first). This usually resolves itself
(session-close does `git pull --no-rebase` before push), but can cause merge conflicts.

Monitor for this: if two beads are both in "session close" phase simultaneously, watch
more closely for merge errors.

## Session Close Fails

Common cause: merge conflict from parallel worktrees touching the same file.
Read the error, report it, let the user resolve. After resolution:
```bash
cmux send --surface surface:<N> "session close\n"
```

## cmux Pane Becomes Unresponsive

```bash
# Check if the surface still exists
cmux list-pane-surfaces --pane pane:<N>
# If gone, the terminal crashed — report to user
# If surface exists but unresponsive, check by name in workspace:
cmux list-pane-surfaces --workspace workspace:<N>
```
