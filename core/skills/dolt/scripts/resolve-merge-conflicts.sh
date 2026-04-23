#!/usr/bin/env bash
# 1. Check conflicts
ssh dolt-server "cd /var/lib/dolt && /usr/local/bin/dolt sql -q \"
USE <db_name>; SELECT * FROM dolt_conflicts;\""

# 2. Resolve on remote (--ours keeps remote version)
ssh dolt-server "cd /var/lib/dolt && /usr/local/bin/dolt sql -q \"
USE <db_name>;
SET autocommit = 0;
SET @@dolt_allow_commit_conflicts = 1;
CALL DOLT_MERGE('<branch>');
CALL DOLT_CONFLICTS_RESOLVE('--ours', '<table>');
CALL DOLT_COMMIT('-am', 'merge: resolve conflicts');\""

# 3. If too diverged → Re-Clone Local Database (below)
