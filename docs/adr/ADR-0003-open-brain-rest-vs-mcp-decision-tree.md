# ADR-0003: open-brain HTTP — REST vs MCP Client Decision Tree

## Status

Accepted (2026-04-26, CCP-sext)

## Context

open-brain exposes two distinct integration surfaces:

1. **REST API** — plain HTTP endpoints under `/api/*` (e.g. `/api/ingest`,
   `/api/worktree-session-summary`, `/api/session-end`, `/api/memories`).
   These are documented, stable, purpose-built ingestion/retrieval endpoints.

2. **MCP server** — a FastMCP server exposing tools (`save_memory`, `search`,
   `materialize_memories`, `weekly_briefing`, etc.) via the MCP Streamable-HTTP
   transport.

ADR-0001 established that MCP clients in this repo MUST use the official
`mcp` Python SDK (`mcp>=1.11`) — never homegrown httpx/urllib JSON-RPC clients.
That decision answered *how* to talk MCP. ADR-0003 answers *when* to reach for
REST vs MCP in the first place.

The four-layer bug cascade (CCP-yosw → CCP-scw5 → CCP-sd9e → CCP-zodj) proved
that the distinction matters: each bug arose from conflating the two surfaces or
hand-rolling transport logic that the SDK already handles correctly.

## Decision

Apply the following decision tree every time a script needs to communicate with
open-brain:

### Decision Tree

```
Need to push a data payload to open-brain?
│
├─ Is there a documented REST endpoint for this operation?
│   (/api/ingest, /api/worktree-session-summary, /api/session-end, /api/memories, ...)
│   │
│   └─ YES → REST via urllib (stdlib). No extra dependencies.
│
└─ Is the operation exposed only as an MCP tool?
    (save_memory, search, materialize_memories, weekly_briefing, ...)
    │
    └─ YES → MCP via official mcp Python SDK (mcp>=1.11). PEP 723 dependency.

In doubt → prefer REST if the endpoint exists; otherwise MCP via SDK.
```

### Rule summary

| Use case | Protocol | Client | Dependency |
|----------|----------|--------|------------|
| Ingest session/worktree data | REST `/api/worktree-session-summary` | `urllib.request` | stdlib only |
| One-shot data drop | REST `/api/ingest` | `urllib.request` | stdlib only |
| Session-end notification | REST `/api/session-end` | `urllib.request` | stdlib only |
| Read raw memories | REST `GET /api/memories` | `urllib.request` | stdlib only |
| Any future documented REST endpoint | REST | `urllib.request` | stdlib only |
| Save a memory (tool) | MCP `save_memory` | mcp SDK | `mcp>=1.11` |
| Search memories (tool) | MCP `search` | mcp SDK | `mcp>=1.11` |
| Materialize memories (tool) | MCP `materialize_memories` | mcp SDK | `mcp>=1.11` |
| Weekly briefing (tool) | MCP `weekly_briefing` | mcp SDK | `mcp>=1.11` |
| Any MCP-only tool | MCP | mcp SDK | `mcp>=1.11` |

### REST pattern (copy-paste)

```python
import urllib.request
import json
import os

base_url = os.environ.get("OPEN_BRAIN_URL", "https://open-brain.sussdorff.org").rstrip("/")
api_key = os.environ.get("OPEN_BRAIN_API_KEY", "")

payload = json.dumps({...}).encode("utf-8")
req = urllib.request.Request(
    f"{base_url}/api/worktree-session-summary",
    data=payload,
    headers={"Content-Type": "application/json", "X-API-Key": api_key},
    method="POST",
)
resp = urllib.request.urlopen(req, timeout=15)
```

No extra dependencies. Shebang: `#!/usr/bin/env python3`.

### MCP pattern (copy-paste)

```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "mcp>=1.11"
# ]
# ///
import asyncio
import os
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def call_tool(tool_name: str, args: dict):
    url = os.environ.get("OPEN_BRAIN_MCP_URL", "https://open-brain.sussdorff.org/mcp")
    api_key = os.environ.get("OPEN_BRAIN_API_KEY", "")
    headers = {"x-api-key": api_key}
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            if result.isError:
                raise RuntimeError(f"MCP tool error: {result.content}")
            return result
```

Authentication: `x-api-key` header (lowercase). Do NOT use `Authorization: Bearer` —
open-brain rejects it (api_key values are opaque strings, not JWTs).

## Anti-pattern

**DO NOT** roll a custom MCP HTTP client using httpx or urllib. This means:
- No hand-written initialize handshake
- No manual session-id header management
- No custom SSE response parsers
- No `httpx.AsyncClient` with JSON-RPC payloads targeting `/mcp`

The bug history (CCP-yosw → CCP-scw5 → CCP-sd9e → CCP-zodj: URL path, Accept
header, missing initialize, missing session-id) documents four distinct failure
modes in homegrown transport code. The mcp SDK eliminates this class of bugs
permanently because the SDK is co-developed with the FastMCP server open-brain uses.

## Consequences

- Scripts that only call REST endpoints remain stdlib-only — no `uv`/PEP 723
  overhead required.
- Scripts that call MCP tools add `mcp>=1.11` to their PEP 723 `# dependencies`
  block and use `#!/usr/bin/env -S uv run --quiet --script`.
- New open-brain REST endpoints are added to the table in this ADR as they are
  documented; MCP-only operations use the SDK by default.
- Code review must reject any new `httpx`-based or hand-written MCP transport
  targeting open-brain.

## Affected Files

- `core/agents/session-close-handlers/turn-log-upload.py` — canonical REST example
- `scripts/query-sources.py` — canonical MCP SDK example
- `scripts/orchestrate-brief.py` — MCP SDK via `_async_save_memory`

## References

- ADR-0001: Use Official mcp Python SDK — establishes SDK requirement for MCP clients
- ADR-0002: open-brain as System-of-Record — context for why both surfaces are used
- CCP-sext: ADR + skill for open-brain HTTP client decision tree
- CCP-zodj: Replace homegrown MCP HTTP client with official mcp Python SDK
- `standards/integrations/open-brain-http-client.md` — compact quick-reference
