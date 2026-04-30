---
name: cmux-browser
description: End-user browser automation with cmux. Use when you need to open sites, interact with pages, wait for state changes, and extract data from cmux browser surfaces.
requires_standards: [english-only]
---

# Browser Automation with cmux

Use this skill for browser tasks inside cmux webviews.

## Core Workflow

1. Open or target a browser surface.
2. Verify navigation with `get url` before waiting or snapshotting.
3. Snapshot (`--interactive`) to get fresh element refs.
4. Act with refs (`click`, `fill`, `type`, `select`, `press`).
5. Wait for state changes.
6. Re-snapshot after DOM/navigation changes.

```bash
cmux --json browser open https://example.com  # returns surface ref, e.g. surface:7
cmux browser surface:7 wait --load-state complete --timeout-ms 15000
cmux browser surface:7 snapshot --interactive
cmux --json browser surface:7 click e2 --snapshot-after
```

See [`scripts/core-workflow.sh`](scripts/core-workflow.sh) for the complete example.

## Surface Targeting

```bash
# identify current context
cmux identify --json

# open routed to a specific topology target
cmux browser open https://example.com --workspace workspace:2 --window window:1 --json
```

Notes:
- CLI output defaults to short refs (`surface:N`, `pane:N`, `workspace:N`, `window:N`).
- UUIDs are still accepted on input; only request UUID output when needed (`--id-format uuids|both`).
- Keep using one `surface:N` per task unless you intentionally switch.

## Wait Support

cmux supports wait patterns similar to agent-browser:

```bash
cmux browser <surface> wait --selector "#ready" --timeout-ms 10000
cmux browser <surface> wait --text "Success" --timeout-ms 10000
cmux browser <surface> wait --url-contains "/dashboard" --timeout-ms 10000
cmux browser <surface> wait --load-state complete --timeout-ms 15000
cmux browser <surface> wait --function "document.readyState === 'complete'" --timeout-ms 10000
```

## Common Flows

### Form Submit

```bash
cmux --json browser open https://example.com/signup
cmux browser surface:7 fill e1 "Jane Doe"
cmux browser surface:7 fill e2 "jane@example.com"
cmux --json browser surface:7 click e3 --snapshot-after
```

See [`scripts/form-submit.sh`](scripts/form-submit.sh) for the complete example.

### Clear an Input

```bash
cmux browser surface:7 fill e11 "" --snapshot-after --json
cmux browser surface:7 get value e11 --json
```

### Stable Agent Loop (Recommended)

```bash
# navigate -> verify -> wait -> snapshot -> action -> snapshot
cmux browser surface:7 get url
cmux browser surface:7 wait --load-state complete --timeout-ms 15000
cmux browser surface:7 snapshot --interactive
cmux --json browser surface:7 click e5 --snapshot-after
cmux browser surface:7 snapshot --interactive
```

If `get url` is empty or `about:blank`, navigate first instead of waiting on load state.

## Deep-Dive References

| Reference | When to Use |
|-----------|-------------|
| [references/commands.md](references/commands.md) | Full browser command mapping and quick syntax |
| [references/snapshot-refs.md](references/snapshot-refs.md) | Ref lifecycle and stale-ref troubleshooting |
| [references/authentication.md](references/authentication.md) | Login/OAuth/2FA patterns and state save/load |
| [references/authentication.md#saving-authentication-state](references/authentication.md#saving-authentication-state) | Save authenticated state right after login |
| [references/session-management.md](references/session-management.md) | Multi-surface isolation and state persistence patterns |
| [references/video-recording.md](references/video-recording.md) | Current recording status and practical alternatives |
| [references/proxy-support.md](references/proxy-support.md) | Proxy behavior in WKWebView and workarounds |

## Ready-to-Use Templates

| Template | Description |
|----------|-------------|
| [templates/form-automation.sh](templates/form-automation.sh) | Snapshot/ref form fill loop |
| [templates/authenticated-session.sh](templates/authenticated-session.sh) | Login once, save/load state |
| [templates/capture-workflow.sh](templates/capture-workflow.sh) | Navigate + capture snapshots/screenshots |

## Dev Feedback Loop (for Implementation Agents)

When you're implementing frontend features inside cmux, use the browser surface as a
**live feedback loop** — no need for external Playwright processes.

### Why use cmux-browser during implementation?

- **Zero overhead** — no Chromium startup, no separate process; the browser is just another cmux surface
- **Same environment** — your editor pane and browser pane share the cmux workspace
- **Instant feedback** — code change → dev server hot-reloads → snapshot → see result → iterate
- **Snapshot-driven** — accessibility snapshots give you structured DOM state, not just screenshots

### Workflow: Implement → Verify → Iterate

```bash
# 1. Open browser surface alongside your editor
cmux --json browser open http://mira-92.localhost:1355/patients

# 2. Wait for page load
cmux browser surface:7 wait --load-state complete --timeout-ms 15000

# 3. After code change: snapshot to see current state
cmux browser surface:7 snapshot --interactive

# 4. Interact if needed (fill form, click button)
cmux browser surface:7 click e3 --snapshot-after

# 5. Verify visual result matches acceptance criteria
cmux browser surface:7 snapshot --interactive
```

### When to use cmux-browser vs playwright-cli

| Situation | Tool |
|-----------|------|
| Agent runs inside cmux (implementation orchestrator, wave orchestrator) | **cmux-browser** — native, zero-overhead |
| CI/CD pipeline or headless testing | **playwright-cli** — cross-platform, Chromium engine |
| Need viewport emulation, network mocking, offline mode | **playwright-cli** — WKWebView doesn't support these |
| Visual verification during implementation (pre-commit gate) | **cmux-browser** preferred, playwright-cli fallback |
| UAT validation (uat-validator agent) | **playwright-cli** — deterministic, CI-compatible |

### Integration with view-impact-check

When implementing a new UI element that appears across multiple views (see `standards/frontend/view-impact-check.md`), use cmux-browser to quickly verify all affected views:

```bash
cmux browser surface:7 navigate http://mira-92.localhost:1355/patients
cmux browser surface:7 wait --load-state complete --timeout-ms 10000
cmux browser surface:7 snapshot --interactive
```

See [`scripts/view-impact-check.sh`](scripts/view-impact-check.sh) for the multi-view example.

## Limits (WKWebView)

These commands currently return `not_supported` because they rely on Chrome/CDP-only APIs not exposed by WKWebView:
- viewport emulation
- offline emulation
- trace/screencast recording
- network route interception/mocking
- low-level raw input injection

Use supported high-level commands (`click`, `fill`, `press`, `scroll`, `wait`, `snapshot`) instead.

## Troubleshooting

### `js_error` on `snapshot --interactive` or `eval`

Some complex pages can reject or break the JavaScript used for rich snapshots and ad-hoc evaluation.

Recovery steps:

```bash
cmux browser surface:7 get url
cmux browser surface:7 get text body
cmux browser surface:7 get html body
```

- Use `get url` first so you know whether the page actually navigated.
- Fall back to `get text body` or `get html body` when `snapshot --interactive` or `eval` returns `js_error`.
- If the page is still failing, navigate to a simpler intermediate page, then retry the task from there.
