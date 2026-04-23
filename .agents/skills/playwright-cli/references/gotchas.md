# Playwright-CLI Gotchas & Troubleshooting

- **`pdf` captures the viewer, not the original PDF.** When the browser displays a PDF, `playwright-cli pdf` renders Chromium's built-in PDF viewer into a new PDF (with toolbar/sidebar). To get the original PDF, extract cookies via `cookie-list` and download with curl:
  ```bash
  COOKIES=$(playwright-cli -s=session cookie-list | jq -r '.[] | "\(.name)=\(.value)"' | paste -sd '; ' -)
  curl -s -L -H "Cookie: $COOKIES" -o output.pdf "<direct-pdf-url>"
  ```
- **`eval` is synchronous only.** `async/await` and `fetch().then()` do not work in `eval`. For async operations, use `run-code` with `async page => { ... }` syntax instead.
- **`eval` with complex expressions causes serialization errors.** Arrow functions containing `const`, `if`, or multi-statement bodies cause "not well-serializable" errors. Use `run-code` for complex JS, or wrap in a simple IIFE string for `eval`.
- **Old agent-browser profiles crash.** Profiles from `~/.agent-browser-profiles/` are NOT compatible (Chrome version/flag mismatch causes SIGTRAP). Always create fresh profiles.
