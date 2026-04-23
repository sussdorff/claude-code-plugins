#!/usr/bin/env bash
# Core browser automation workflow: open a surface, verify, snapshot, interact.
SURFACE=$(cmux --json browser open https://example.com | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('surface') or d.get('ref') or d.get('id','surface:7'))" 2>/dev/null || echo "surface:7")

cmux browser "$SURFACE" get url
cmux browser "$SURFACE" wait --load-state complete --timeout-ms 15000
cmux browser "$SURFACE" snapshot --interactive
cmux browser "$SURFACE" fill e1 "hello"
cmux --json browser "$SURFACE" click e2 --snapshot-after
cmux browser "$SURFACE" snapshot --interactive
