#!/usr/bin/env bash
# Core browser automation workflow: open a surface, verify, snapshot, interact.
cmux --json browser open https://example.com
# use returned surface ref, for example: surface:7

cmux browser surface:7 get url
cmux browser surface:7 wait --load-state complete --timeout-ms 15000
cmux browser surface:7 snapshot --interactive
cmux browser surface:7 fill e1 "hello"
cmux --json browser surface:7 click e2 --snapshot-after
cmux browser surface:7 snapshot --interactive
