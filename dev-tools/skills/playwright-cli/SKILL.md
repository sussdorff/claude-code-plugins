---
name: playwright-cli
disableModelInvocation: true
description: Browser automation via playwright-cli. ALWAYS use instead of Chrome MCP tools. Use when opening websites, scraping pages, filling forms, or interacting with web UIs. Triggers on any URL, website name, open page, browse, navigate, scrape, fill form.
allowed-tools: Bash(playwright-cli:*)
---

# Browser Automation with playwright-cli

## When to Use

- You need to open a website, navigate pages, or interact with a web UI
- You want to scrape content, fill out forms, or click through a workflow
- You need to access an authenticated web app (e.g. Grafana, Paperless, Amazon) using a saved browser profile
- You want to take screenshots, export PDFs, or record browser sessions
- You need to debug frontend issues by inspecting console logs, network requests, or tracing

## Do NOT

- Do NOT use for tasks that don't require a browser (use curl/API calls instead)
- Do NOT trigger JavaScript alerts/confirms — they block the browser extension
- Do NOT use Chrome MCP tools — always use playwright-cli instead

## Quick start

```bash
playwright-cli open
playwright-cli goto https://playwright.dev
playwright-cli click e15
playwright-cli close
```

> Full command reference: [references/commands.md](references/commands.md)

## Commands

### Core

```bash
playwright-cli open https://example.com/
playwright-cli click e3
playwright-cli fill e5 "user@example.com"
playwright-cli snapshot
```

> Full core command listing: [references/commands.md#core-commands](references/commands.md#core-commands)

### Navigation

```bash
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload
```

### Keyboard

```bash
playwright-cli press Enter
playwright-cli press ArrowDown
playwright-cli keydown Shift
playwright-cli keyup Shift
```

### Mouse

```bash
playwright-cli mousemove 150 300
playwright-cli mousedown
playwright-cli mousewheel 0 100
```

> Full mouse command listing: [references/commands.md#mouse-commands](references/commands.md#mouse-commands)

### Save as

```bash
playwright-cli screenshot
playwright-cli screenshot e5
playwright-cli screenshot --filename=page.png
playwright-cli pdf --filename=page.pdf
```

### Tabs

```bash
playwright-cli tab-new https://example.com/page
playwright-cli tab-select 0
playwright-cli tab-close
```

> Full tabs command listing: [references/commands.md#tabs-commands](references/commands.md#tabs-commands)

### Storage

```bash
playwright-cli state-save auth.json
playwright-cli state-load auth.json
playwright-cli cookie-set session_id abc123
playwright-cli localstorage-set theme dark
```

> Full storage command listing (cookies, localStorage, sessionStorage): [references/commands.md#storage-commands](references/commands.md#storage-commands)

### Network

```bash
playwright-cli route "**/*.jpg" --status=404
playwright-cli route "https://api.example.com/**" --body='{"mock": true}'
playwright-cli route-list
playwright-cli unroute "**/*.jpg"
playwright-cli unroute
```

### DevTools

```bash
playwright-cli console
playwright-cli network
playwright-cli tracing-start
playwright-cli tracing-stop
```

> Full DevTools command listing: [references/commands.md#devtools-commands](references/commands.md#devtools-commands)

## Open parameters

```bash
playwright-cli open --browser=chrome
playwright-cli open --persistent
playwright-cli open --profile=/path/to/profile
```

> Full open parameters: [references/commands.md#open-parameters](references/commands.md#open-parameters)

## Snapshots

After each command, playwright-cli provides a snapshot of the current browser state.

```bash
> playwright-cli goto https://example.com
### Page
- Page URL: https://example.com/
- Page Title: Example Domain
### Snapshot
[Snapshot](.playwright-cli/page-2026-02-14T19-22-42-679Z.yml)
```

You can also take a snapshot on demand using `playwright-cli snapshot` command.

If `--filename` is not provided, a new snapshot file is created with a timestamp. Default to automatic file naming, use `--filename=` when artifact is a part of the workflow result.

## Browser Sessions

```bash
playwright-cli -s=mysession open example.com --persistent
playwright-cli -s=mysession click e6
playwright-cli -s=mysession close
```

> Full browser sessions management: [references/commands.md#browser-sessions-management](references/commands.md#browser-sessions-management)

## Local installation

In some cases user might want to install playwright-cli locally. If running globally available `playwright-cli` binary fails, use `npx playwright-cli` to run the commands. For example:

```bash
npx playwright-cli open https://example.com
npx playwright-cli click e1
```

> See [references/examples.md](references/examples.md) for form submission, multi-tab, debugging, Python wrapper, and download examples.

## Profiles

Persistent Chromium profiles at `~/.local/share/playwright-cli/profiles/<name>/`. Always close before switching profiles. Use `--headed` for initial login (never enter passwords).

> See [references/profiles.md](references/profiles.md) for profile list, usage examples, and creation instructions.

## Key Rules

1. **Prefer `snapshot` for exploration, `eval` for extraction pipelines**
2. **`--headed` only when user needs to see/interact** (login, visual verification)
3. **Always close before changing profile** — profile is set at browser launch
4. **Never enter passwords or sensitive credentials** — launch headed and let user do it
5. **Use `-s=` for parallel instances** — each session is independent
6. **For infinite scroll, use `eval "window.scrollTo(0, document.body.scrollHeight)"`** — `mousewheel` may not reach page bottom
7. **Snapshot files land in `.playwright-cli/`** — reference them for structured data

> See [references/gotchas.md](references/gotchas.md) for troubleshooting PDF capture, eval limitations, and profile issues.

## Specific tasks

* **Request mocking** [references/request-mocking.md](references/request-mocking.md)
* **Running Playwright code** [references/running-code.md](references/running-code.md)
* **Browser session management** [references/session-management.md](references/session-management.md)
* **Storage state (cookies, localStorage)** [references/storage-state.md](references/storage-state.md)
* **Test generation** [references/test-generation.md](references/test-generation.md)
* **Tracing** [references/tracing.md](references/tracing.md)
* **Video recording** [references/video-recording.md](references/video-recording.md)
