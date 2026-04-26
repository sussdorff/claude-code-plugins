# open-brain HTTP Client — REST vs MCP Quick Reference

**Full decision record:** `docs/adr/ADR-0003-open-brain-rest-vs-mcp-decision-tree.md`

## Decision Tree

```
Calling open-brain?
│
├─ Documented REST endpoint exists? (/api/ingest, /api/worktree-session-summary,
│  /api/session-end, /api/memories, ...)
│   └─ YES → urllib (stdlib). No extra deps.
│
├─ Operation exposed only as MCP tool? (save_memory, search, materialize_memories,
│  weekly_briefing, ...)
│   └─ YES → mcp Python SDK (mcp>=1.11). PEP 723 dep.
│
└─ In doubt → REST if endpoint exists, else MCP SDK.
```

## Known REST Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/worktree-session-summary` | POST | Upload worktree turn log |
| `/api/ingest` | POST | One-shot data ingestion |
| `/api/session-end` | POST | Session end notification |
| `/api/memories` | GET | Read raw memories |

## Known MCP Tools

`save_memory`, `search`, `search_by_concept`, `materialize_memories`,
`weekly_briefing`, `compact_memories`, `refine_memories`, `triage_memories`,
`get_context`, `get_observations`, `get_wake_up_pack`, `timeline`, `stats`,
`run_lifecycle_pipeline`, `update_memory`

## REST Snippet

```python
import urllib.request, json, os

base = os.environ.get("OPEN_BRAIN_URL", "https://open-brain.sussdorff.org").rstrip("/")
key = os.environ.get("OPEN_BRAIN_API_KEY", "")
req = urllib.request.Request(
    f"{base}/api/worktree-session-summary",
    data=json.dumps({...}).encode(),
    headers={"Content-Type": "application/json", "X-API-Key": key},
    method="POST",
)
resp = urllib.request.urlopen(req, timeout=15)
```

Shebang: `#!/usr/bin/env python3` (stdlib only, no uv needed).

## MCP Snippet

```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["mcp>=1.11"]
# ///
import asyncio, os
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def call_tool(tool_name, args):
    url = os.environ.get("OPEN_BRAIN_MCP_URL", "https://open-brain.sussdorff.org/mcp")
    key = os.environ.get("OPEN_BRAIN_API_KEY", "")
    async with streamablehttp_client(url, headers={"x-api-key": key}) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            result = await s.call_tool(tool_name, args)
            if result.isError:
                raise RuntimeError(f"MCP tool error: {result.content}")
            return result
```

Auth: `x-api-key` header (lowercase). NOT `Authorization: Bearer`.

## Anti-Pattern (BLOCKED)

Do NOT hand-roll an MCP transport using httpx or urllib:
- No manual initialize handshake
- No manual session-id management
- No custom SSE parsers
- No `httpx.AsyncClient` with JSON-RPC payloads to `/mcp`

Evidence: CCP-yosw → CCP-scw5 → CCP-sd9e → CCP-zodj — four successive bugs
in handwritten transport code. The mcp SDK eliminates this class permanently.
