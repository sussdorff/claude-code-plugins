#!/usr/bin/env bash
bd dolt pull        # Pull latest from remote
bd list --all       # Verify all issues are present
bd dolt push        # Should succeed without force
# Test consecutive pushes:
bd create --title="push test" --type=task --priority=4
bd dolt push        # Should also succeed
bd close <test-id> --reason="test"
bd dolt push        # Third consecutive push — should still work
