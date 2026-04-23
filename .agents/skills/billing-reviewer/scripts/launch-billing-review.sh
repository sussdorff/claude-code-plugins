#!/usr/bin/env bash
# launch-billing-review.sh
# Prints instructions for launching the billing-reviewer as a subagent in Claude Code.
# The Task() invocation below is not runnable shell — it documents the Claude Code API call.

set -euo pipefail

cat <<'EOF'
To launch the billing-reviewer as a subagent, use the following Task() call in Claude Code:

  Task(
    subagent_type="general-purpose",
    description="Billing UI review",
    prompt="""
    You are an Abrechnungsspezialistin reviewing MIRA's billing UI.

    Read ~/.claude/skills/billing-reviewer/SKILL.md for the full review process.

    Navigate the frontend at http://localhost:3000/billing and evaluate
    each feature from the billing specialist's perspective.

    Create beads for every improvement you identify.
    """
  )

Prerequisites:
  - Frontend running: cd frontend && bun run dev  (port 3000)
  - Backend running: bun run dev  (port 3001)
  - Aidbox accessible: https://mira.cognovis.de/aidbox
  - MCN seed data loaded (see aidbox-fhir skill)
EOF
