#!/usr/bin/env bash
# View-impact check: navigate each affected view and snapshot to verify a UI element renders correctly.
cmux browser surface:7 navigate http://mira-92.localhost:1355/patients
cmux browser surface:7 wait --load-state complete --timeout-ms 10000
cmux browser surface:7 snapshot --interactive
# → verify badge/indicator appears correctly

cmux browser surface:7 navigate http://mira-92.localhost:1355/dashboard
cmux browser surface:7 wait --load-state complete --timeout-ms 10000
cmux browser surface:7 snapshot --interactive
# → verify same component renders here too
