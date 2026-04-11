# Playwright-CLI Examples

## Form Submission

```bash
playwright-cli open https://example.com/form
playwright-cli snapshot

playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "password123"
playwright-cli click e3
playwright-cli snapshot
playwright-cli close
```

## Multi-tab Workflow

```bash
playwright-cli open https://example.com
playwright-cli tab-new https://example.com/other
playwright-cli tab-list
playwright-cli tab-select 0
playwright-cli snapshot
playwright-cli close
```

## Debugging with DevTools

```bash
playwright-cli open https://example.com
playwright-cli click e4
playwright-cli fill e7 "test"
playwright-cli console
playwright-cli network
playwright-cli close
```

```bash
playwright-cli open https://example.com
playwright-cli tracing-start
playwright-cli click e4
playwright-cli fill e7 "test"
playwright-cli tracing-stop
playwright-cli close
```

## Python Wrapper Pattern

```python
import json, subprocess, time
from pathlib import Path

SESSION = "extract"
PROFILE = str(Path.home() / ".local" / "share" / "playwright-cli" / "profiles" / "substack")

def pcli(*args: str, session: str = SESSION, profile: str | None = None, timeout: int = 30) -> str:
    """Run a playwright-cli command and return stdout."""
    cmd = ["playwright-cli"]
    if session:
        cmd.append(f"-s={session}")
    cmd.extend(list(args))
    if profile or PROFILE:
        # --profile only applies to 'open' command
        if args and args[0] == "open":
            cmd.extend(["--profile", profile or PROFILE])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip()

def pcli_open(url: str, session: str = SESSION) -> None:
    pcli("open", url, session=session)
    time.sleep(2)

def pcli_eval(js: str, timeout: int = 30) -> str:
    """Execute JavaScript via playwright-cli eval command."""
    cmd = ["playwright-cli"]
    if SESSION:
        cmd.append(f"-s={SESSION}")
    cmd.extend(["eval", js])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip()

def pcli_scroll_down() -> None:
    """Scroll to bottom - reliable infinite scroll triggering."""
    pcli_eval("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
```

## Download Workflow

```bash
# PDF export of current page
playwright-cli pdf --filename=invoice.pdf

# Screenshot as fallback
playwright-cli screenshot --filename=page.png

# Download via clicking a link (get ref from snapshot first)
playwright-cli snapshot
playwright-cli click e15  # click download link
# File downloads to .playwright-cli/ directory
```
