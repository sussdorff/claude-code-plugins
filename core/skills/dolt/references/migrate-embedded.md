# Migrate Embedded → Shared-Server (legacy)

For projects still on `bd init` (embedded mode). Symptom: every second push fails with
`target has uncommitted changes`. This is the embedded remotesapi dirty-working-set bug —
unfixable in embedded mode, only resolved by switching protocols.

## Why embedded mode is broken

Embedded mode pushes via remotesapi (HTTPS). Every remotesapi push dirties the remote SQL
server's working set (phantom row deletes in `events`/`issues`), causing the next push to
fail. This persists even on Dolt v1.85.0 (which fixed related issues #10727, #10731).

Root cause: the remotesapi write updates HEAD on the remote, but the SQL server's cached
working set becomes stale — it sees a diff between cached working set root hash and new HEAD,
reporting phantom changes. SQL-protocol pushes (shared-server mode) are unaffected.

Workarounds that **don't** stick:
- `CALL dolt_checkout('.')` on remote — fixes one push, breaks again on next
- Dropping `schema_migrations` table — unrelated cause
- Clearing `dolt_ignore` — unrelated cause
- Moving SQL listener port — engine still loads all DBs on startup

The only fix is to migrate.

## Migration steps

```bash
# 1. Force-push current local data to remote so we don't lose it
bd dolt push --force

# 2. Switch project config:
#    .beads/metadata.json:  set    "dolt_mode": "server"
#    .beads/config.yaml:    add    dolt.shared-server: true

# 3. Clone into ~/.dolt-data/ (DOLT_CLONE ignores env vars; pass --user explicitly)
dolt --host 127.0.0.1 --port 3306 --no-tls sql -q \
  "CALL DOLT_CLONE('--user', 'malte', 'https://dolt.cognovis.de/<db_name>')"
brew services restart dolt

# 4. Add SQL remote (then set __DOLT__grpc_username manually — see SKILL.md > Auth Layers)
bd dolt remote add origin https://dolt.cognovis.de/<db_name>

# 5. Verify and push
bd dolt show && bd dolt pull && bd dolt push --force

# 6. Clean up embedded artifacts
rm -rf .beads/embeddeddolt
```

See [`../scripts/sync-verify.sh`](../scripts/sync-verify.sh) for the consecutive-push
verification routine.

## Stale `schema_migrations` table

bd v1.0.0 created a `schema_migrations` table in embedded mode. The Dolt SQL server on
the remote auto-deletes it from WORKING on every startup/push, causing permanent
"target has uncommitted changes" errors.

Fix: drop the table locally (`DROP TABLE schema_migrations` + `DOLT_COMMIT`), verify both
sides have the same issue count, then `bd dolt push --force` once. bd works fine without
it after initial migrations.
