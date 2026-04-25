# ADR-0001: Use Official mcp Python SDK for MCP Streamable-HTTP Clients

## Status

Accepted (2026-04-25, CCP-zodj)

## Context

The daily-brief scripts (`query-sources.py`, `orchestrate-brief.py`) needed to call open-brain
MCP tools (`search`, `save_memory`) via the MCP Streamable-HTTP transport.

Two implementation paths were evaluated:

**Path A — Roll the Streamable-HTTP transport by hand**
- Implement: initialize handshake, session-id caching, SSE response parsing, session teardown.
- Pro: zero additional dependencies.
- Con: Each layer of the MCP spec adds a new failure mode. CCP-yosw → CCP-scw5 → CCP-sd9e →
  CCP-zodj represents four successive bugs in the handwritten transport — URL path, Accept header,
  missing initialize, missing session-id. A fifth bug was expected.

**Path B — Use the official `mcp` Python SDK**
- Replace `_OBClient` (httpx-based) with `streamablehttp_client` + `ClientSession` from the
  `mcp` package (PyPI: `mcp>=1.11`).
- The SDK handles: initialize handshake, session-id negotiation, SSE parsing, capability
  exchange, timeout.
- Pro: Correct by construction; compatible with FastMCP servers (open-brain itself uses FastMCP).
- Con: Adds a ~10 MB dependency (mcp package). Acceptable for PEP 723 scripts run via uv.

## Decision

Use **Path B** (official mcp Python SDK) for all MCP Streamable-HTTP clients in this repository.

Rationale:
1. The open-brain server is built on FastMCP (`mcp.server.fastmcp`) — SDK compatibility
   is guaranteed at the protocol level.
2. The homegrown client accumulated four successive bugs across five beads. SDK eliminates
   this class of bugs permanently.
3. PEP 723 dependency management (`uv run --script`) makes the `mcp>=1.11` dep self-contained
   and portable — no manual install step.

## Consequences

- Any future MCP client in this repo MUST use `mcp.client.streamable_http.streamablehttp_client`
  + `mcp.ClientSession` rather than raw httpx JSON-RPC calls.
- Add `mcp>=1.11` to the PEP 723 `# dependencies` block of any script that calls MCP tools.
- Authentication: use `headers={"x-api-key": token}` with `streamablehttp_client`.
  Do NOT use `Authorization: Bearer` — open-brain rejects it (api_key values are opaque
  strings, not JWTs).
- Error handling: check `CallToolResult.isError` before parsing content. Walk the full
  exception chain (including `ExceptionGroup`) when translating 401 errors to `PermissionError`.

## Affected Files

- `scripts/query-sources.py` — `_OBClient` class, `_build_ob_client()`
- `scripts/orchestrate-brief.py` — `_async_save_memory()`

## References

- MCP Streamable-HTTP spec: https://modelcontextprotocol.io/docs/concepts/transports
- mcp Python SDK: https://github.com/modelcontextprotocol/python-sdk
- CCP-zodj: Replace homegrown MCP HTTP client in daily-brief with official mcp Python SDK
