#!/usr/bin/env bash
# Write a plan to a markdown file and open it in the cmux markdown viewer.
cat > plan.md << 'EOF'
# Task Plan

## Steps
1. Analyze the codebase
2. Implement the feature
3. Write tests
4. Verify the build
EOF

cmux markdown open plan.md
