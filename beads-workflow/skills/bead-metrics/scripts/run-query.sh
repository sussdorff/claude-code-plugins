#!/usr/bin/env bash
# Run a bead-metrics query via the orchestrator.metrics module.
# Usage: run-query.sh [--top=N] [--bead=ID] [--wave=ID] [--adhoc]
# Requires CLAUDE_PLUGIN_ROOT to be set (done automatically when the plugin is active).
set -euo pipefail

ARGS="${*}"

uv run python -c "
import os, sys
sys.path.insert(0, os.path.join(os.environ['CLAUDE_PLUGIN_ROOT'], 'lib'))
from orchestrator.metrics import query_report, query_wave_report, query_adhoc_report

args = '${ARGS}'.strip()

if '--adhoc' in args:
    print(query_adhoc_report())
elif '--wave=' in args:
    wave_id = [a.split('=',1)[1] for a in args.split() if a.startswith('--wave=')][0]
    print(query_wave_report(wave_id=wave_id))
elif '--bead=' in args:
    bead_id = [a.split('=',1)[1] for a in args.split() if a.startswith('--bead=')][0]
    print(query_report(bead_id=bead_id))
elif '--top=' in args:
    top = int([a.split('=',1)[1] for a in args.split() if a.startswith('--top=')][0])
    print(query_report(top=top))
else:
    print(query_report())
"
