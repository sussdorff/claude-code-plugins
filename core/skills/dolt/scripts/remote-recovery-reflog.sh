#!/usr/bin/env bash
# 1. Inspect reflog for last good commit
ssh dolt-server "cd /var/lib/dolt && /usr/local/bin/dolt sql -q \"
USE <db_name>;
SELECT ref, commit_hash, commit_message FROM dolt_reflog('main') LIMIT 20;\""

# 2. Reset main to good commit
ssh dolt-server "cd /var/lib/dolt && /usr/local/bin/dolt sql -q \"
USE <db_name>;
CALL DOLT_RESET('--hard', '<good_commit_hash>');\""

# 3. Re-import any local-only issues via dolt table import
# Export from local: dolt sql -r csv -q "SELECT * FROM issues WHERE ..."
# Import on remote or re-clone locally

# 4. Re-clone locally (see Re-Clone Local Database above)
