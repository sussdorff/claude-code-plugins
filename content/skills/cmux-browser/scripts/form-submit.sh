#!/usr/bin/env bash
# Form submit workflow: open a signup page, fill fields, submit, and verify navigation.
SURFACE=$(cmux --json browser open https://example.com/signup | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('surface') or d.get('ref') or d.get('id','surface:7'))" 2>/dev/null || echo "surface:7")

cmux browser "$SURFACE" get url
cmux browser "$SURFACE" wait --load-state complete --timeout-ms 15000
cmux browser "$SURFACE" snapshot --interactive
cmux browser "$SURFACE" fill e1 "Jane Doe"
cmux browser "$SURFACE" fill e2 "jane@example.com"
cmux --json browser "$SURFACE" click e3 --snapshot-after
cmux browser "$SURFACE" wait --url-contains "/welcome" --timeout-ms 15000
cmux browser "$SURFACE" snapshot --interactive
