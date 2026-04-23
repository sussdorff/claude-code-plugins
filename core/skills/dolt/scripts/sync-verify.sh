#!/usr/bin/env bash
bd dolt pull        # Pull latest from remote
bd list --all       # Verify all issues are present
bd dolt push        # Should succeed without force
# Test consecutive pushes:
TEST_ID=$(bd create --title="push test" --type=task --priority=4 | grep -oE '[A-Z]+-[a-z0-9]+' | head -1)
bd dolt push        # Should also succeed
bd close "$TEST_ID" --reason="test"
bd dolt push        # Third consecutive push — should still work
