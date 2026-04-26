# ADR-0002: open-brain as System-of-Record for Daily Briefs

## Status

Accepted (2026-04-25, CCP-glnq)

## Context

Prior to v1.5, `orchestrate-brief.py` wrote daily briefs to two places:

1. **Disk** — `<project>/.claude/daily-briefs/YYYY-MM-DD.md` (primary)
2. **open-brain** — via `save_memory` MCP tool (secondary, non-blocking)

The disk was the de-facto system-of-record: `brief_exists` checked disk first; OB
writes were fire-and-forget (exceptions silently swallowed). If OB was unavailable,
the brief was still produced and persisted to disk. The `session_ref` used
`daily-brief-{date}` — no project slug — causing cross-project collisions when
multiple projects were stored in the same OB instance.

Problems with the disk-first model:

1. **OB read path was missing** — `/daily-brief` could not retrieve a brief from
   OB; it always re-queried data sources and re-rendered. Generating a brief was
   the only way to persist it.
2. **Silent OB write failures** — If OB was unreachable, the brief existed on
   disk but not in OB. OB was never the authoritative store.
3. **Disk portability** — The `dev-only repository` principle (`CLAUDE.md`) states
   `rm -rf $(pwd)` must leave Codex/Claude fully operational. Daily briefs stored
   only on disk violate this when the project directory is removed.
4. **session_ref collision** — `daily-brief-2026-04-23` is ambiguous across projects.

## Decision

Promote **open-brain to the primary system-of-record** for daily briefs starting
from v1.5. Disk write becomes opt-in via `--persist-disk` flag.

### SoR shift (v1.5)

| Concern | Before (v1.4) | After (v1.5) |
|---------|---------------|--------------|
| Read path | disk first | OB first → disk fallback |
| Write path | disk (via render) + OB (non-blocking) | OB (hard error) + disk optional |
| OB failure | silent skip | RuntimeError raised |
| session_ref | `daily-brief-{date}` | `daily-brief-{project}-{date}` |
| disk write | default | opt-in via `--persist-disk` |

### do-not-compact contract

Every brief written to OB includes `do_not_compact: true` in its metadata dict.
This instructs the open-brain lifecycle pipeline to exclude these entries from
the standard compaction run (which truncates or merges old memories to save
space). Daily briefs are primary source data and must not be compacted.

Additional metadata fields injected per write:
- `do_not_compact: true` — lifecycle-pipeline exclusion flag
- `schema_version: "1.5"` — version of the write format
- `version: "v1.5"` — human-readable version tag

### Failure mode

`_save_to_open_brain` is now a hard error:
- Missing credentials → `RuntimeError("open-brain: no credentials configured ...")`
- Connection/tool error → exception re-raised from `_async_save_memory`

Callers (e.g. `run_for_project`) no longer swallow OB write errors. If OB is
unavailable, the orchestrator surfaces the error rather than silently producing
a brief that exists only locally.

The offline fallback is preserved at the **read** side only: when
`_read_from_open_brain` returns `None` (OB unreachable), the disk check fires
before triggering a new render. This allows reads to degrade gracefully; writes
do not.

### Migration playbook

Existing disk briefs must be imported into OB before v1.5 is the active default.
Run the migration script once per environment:

```bash
# 1. Preview what would be migrated (dry-run, default)
python3 scripts/migrate-disk-briefs-to-open-brain.py

# 2. Execute the migration
python3 scripts/migrate-disk-briefs-to-open-brain.py --apply

# 3. Verify (spot-check one date)
python3 scripts/orchestrate-brief.py --date 2026-04-23
# Expected: brief read from OB (not re-rendered); skipped=True in logs
```

**Note on legacy observations**: Pre-v1.5 daily-brief runs wrote to OB with
`session_ref=daily-brief-{date}` (no project slug). These observations are
**orphaned** — they will not be found by the v1.5 read path (which searches for
`daily-brief-{project}-{date}`). They can be identified by their session_ref
format and cleaned up manually if desired, but the migration script only migrates
disk briefs to the new format; it does not attempt to rename existing OB entries.

The migration script (`scripts/migrate-disk-briefs-to-open-brain.py`):
- Reads all `<project>/.claude/daily-briefs/*.md` files
- Parses date from filename (`YYYY-MM-DD.md`)
- Posts to OB with `session_ref=daily-brief-{slug}-{date}`, `dedup_mode=merge`
- Reports: migrated, failed
- Is idempotent: re-running does not duplicate entries (OB dedup by session_ref)

## Consequences

### Positive

- Daily briefs persist across machine resets and project-directory removal.
- OB read path enables deduplication at the retrieval level: second run for
  the same (project, date) is a no-op because OB already has the content.
- Cross-project session_ref collision eliminated.
- Lifecycle pipeline can honour `do_not_compact` to protect brief history.

### Negative / Trade-offs

- OB credentials are now required. A session without valid OB credentials
  cannot generate or retrieve briefs.
- Latency: every brief write makes an async MCP call (adds ~200ms per brief
  in practice; acceptable for a daily operation).
- Breaking change: callers relying on `brief_exists` (disk) as the sole
  idempotency guard must be updated to mock `_read_from_open_brain`.

### Follow-up required

- **CCP-mhjf**: Verify open-brain lifecycle-pipeline.py honours
  `do_not_compact: true`. If the flag is not respected, patch the pipeline.
  See acceptance criterion AK6 of CCP-glnq.

## Affected Files

- `scripts/orchestrate-brief.py` — `_save_to_open_brain` (hard error),
  `_read_from_open_brain` (new), `_async_search_memory` (new),
  `_run_render_brief` (persist_disk param), `run_for_project` (OB read path),
  `make_session_ref` (project slug), `parse_args` (--persist-disk)
- `scripts/migrate-disk-briefs-to-open-brain.py` — NEW migration script; checks both
  new path (`~/.claude/projects/<slug>/daily-briefs/`) and legacy path
  (`<project.path>/.claude/daily-briefs/`) for backward compatibility (CCP-gtue)
- `core/skills/daily-brief/scripts/config.py` — `briefs_dir()` now returns
  `~/.claude/projects/<slug>/daily-briefs/` (user-local state, not repo-internal);
  `legacy_briefs_dir()` added for migration backward-compat (CCP-gtue)
- `core/skills/daily-brief/SKILL.md` — Updated to reflect v1.5 SoR and CCP-gtue path

## References

- ADR-0001: Use Official mcp Python SDK — foundation for MCP client
- CCP-glnq: [FEAT] daily-brief v1.5: open-brain as system-of-record
- `core/contracts/execution-result.schema.json` — envelope used by migration script
