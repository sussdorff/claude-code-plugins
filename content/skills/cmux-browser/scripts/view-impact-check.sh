#!/usr/bin/env bash
# View-impact check: navigate each affected view and snapshot to verify a UI element renders correctly.
SURFACE=$(cmux --json browser open http://mira-92.localhost:1355/patients | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('surface') or d.get('ref') or d.get('id','surface:7'))" 2>/dev/null || echo "surface:7")

cmux browser "$SURFACE" wait --load-state complete --timeout-ms 10000
cmux browser "$SURFACE" snapshot --interactive
# → verify badge/indicator appears correctly

cmux browser "$SURFACE" navigate http://mira-92.localhost:1355/dashboard
cmux browser "$SURFACE" wait --load-state complete --timeout-ms 10000
cmux browser "$SURFACE" snapshot --interactive
# → verify same component renders here too
