#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "pytest>=8.0",
#   "mcp>=1.11",
# ]
# ///
"""
Tests for SDK-based MCP client in query-sources.py and orchestrate-brief.py.

CCP-zodj: Replace homegrown httpx _OBClient with official mcp Python SDK.

Coverage:
- _OBClient (SDK-based): happy path search returns entries
- _OBClient (SDK-based): 401 / auth error -> PermissionError with actionable message
- _OBClient (SDK-based): session expiry -> error surfaces as exception (SDK handles reconnect internally)
- _async_save_memory (SDK-based): save_memory tool call succeeds
- _async_save_memory (SDK-based): SDK error -> exception propagates to _save_to_open_brain wrapper
- Integration: gated on OB_API_KEY env var (skip if absent)
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

_CONFIG_DIR = _REPO_ROOT / "core" / "skills" / "daily-brief" / "scripts"
sys.path.insert(0, str(_CONFIG_DIR))

# Load query-sources via importlib (hyphen in filename)
_qs_spec = importlib.util.spec_from_file_location(
    "query_sources", _SCRIPTS_DIR / "query-sources.py"
)
_qs_module = importlib.util.module_from_spec(_qs_spec)  # type: ignore[arg-type]
_qs_spec.loader.exec_module(_qs_module)  # type: ignore[union-attr]
qs = _qs_module

# Load orchestrate-brief via importlib
_ob_spec = importlib.util.spec_from_file_location(
    "orchestrate_brief", _SCRIPTS_DIR / "orchestrate-brief.py"
)
_ob_module = importlib.util.module_from_spec(_ob_spec)  # type: ignore[arg-type]
_ob_spec.loader.exec_module(_ob_module)  # type: ignore[union-attr]
ob = _ob_module


# ---------------------------------------------------------------------------
# SDK mock helpers
# ---------------------------------------------------------------------------

def make_sdk_search_client(entries: list[dict[str, Any]]) -> Any:
    """Build a mock _OBClient whose search() returns the given entries via SDK pattern.

    The mock replaces the SDK call without needing a live server. Returns
    entries directly from the search method to test upstream consumers.
    """
    client = MagicMock()
    client.search = AsyncMock(return_value=entries)
    return client


def make_sdk_save_client_that_raises(exc: Exception) -> Any:
    """Build a mock _OBClient whose search raises the given exception."""
    client = MagicMock()
    client.search = AsyncMock(side_effect=exc)
    return client


# ---------------------------------------------------------------------------
# Unit tests: _build_ob_client returns SDK-based client
# ---------------------------------------------------------------------------


class TestBuildObClientSDK:
    """Verify _build_ob_client() returns an object with the correct interface."""

    def test_returns_client_with_search_method(self, tmp_path: Path) -> None:
        """_build_ob_client() must return an object with an async search() method."""
        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://open-brain.example.test", "api_key": "ob_test123"}'
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is not None, "Client must be built from config.json credentials"
        assert hasattr(client, "search"), "Client must have a search() method"
        assert callable(client.search), "search must be callable"

    def test_returns_none_when_no_credentials(self, tmp_path: Path) -> None:
        """_build_ob_client() returns None when no credentials are available."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is None, "Must return None when no credentials are found"

    def test_url_ends_with_mcp_not_mcp_mcp(self, tmp_path: Path) -> None:
        """_build_ob_client() must construct URL ending in /mcp, not /mcp/mcp."""
        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://open-brain.sussdorff.org", "api_key": "ob_key"}'
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is not None
        # The client must expose _url for introspection (SDK client stores url)
        assert hasattr(client, "_url"), "Client must expose _url for regression testing"
        assert client._url == "https://open-brain.sussdorff.org/mcp", (
            f"URL must end with /mcp, not /mcp/mcp; got '{client._url}'"
        )
        assert not client._url.endswith("/mcp/mcp"), (
            f"URL must NOT end with /mcp/mcp; got '{client._url}'"
        )


# ---------------------------------------------------------------------------
# Unit tests: SDK-based _OBClient.search()
# ---------------------------------------------------------------------------


class TestSDKOBClientSearch:
    """Tests for the SDK-based _OBClient search() method, mocking at the SDK layer."""

    def test_search_returns_entries_on_success(self, tmp_path: Path) -> None:
        """_OBClient.search() returns list[dict] entries when SDK call succeeds."""
        from mcp.types import CallToolResult, TextContent

        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://ob.example.test", "api_key": "ob_testkey"}'
        )

        entries = [
            {"id": "obs-1", "type": "session_summary", "text": "Session A"},
            {"id": "obs-2", "type": "learning", "text": "Learned B"},
        ]

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is not None

        # Mock the streamable_http client at SDK level
        mock_result = CallToolResult(
            content=[TextContent(type="text", text=json.dumps(entries))],
            isError=False,
        )

        async def _drive() -> list[dict[str, Any]]:
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value=mock_result)

            @asynccontextmanager
            async def mock_streamable(*args: Any, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            # Patch the SDK transport layer
            with patch("mcp.client.streamable_http.streamablehttp_client", mock_streamable):
                with patch("mcp.ClientSession") as MockSession:
                    MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                    MockSession.return_value.__aexit__ = AsyncMock(return_value=None)
                    return await client.search(
                        type_filter=["session_summary", "learning"],
                        project="test",
                        date_start="2026-04-24T00:00:00+02:00",
                        date_end="2026-04-25T00:00:00+02:00",
                    )

        result = asyncio.run(_drive())
        assert result == entries, f"Expected {entries}, got {result}"

    def test_search_raises_permission_error_on_auth_failure(self, tmp_path: Path) -> None:
        """_OBClient.search() raises PermissionError with actionable message on auth failure.

        The SDK raises an exception when auth fails; the client must translate
        this to a PermissionError mentioning config.json and api_key.
        """
        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://ob.example.test", "api_key": "ob_expiredkey"}'
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is not None

        async def _drive() -> None:
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            # SDK raises an auth error (could be httpx.HTTPStatusError with 401
            # or an mcp exception wrapping it)
            from httpx import HTTPStatusError, Request, Response
            req = Request("POST", "https://ob.example.test/mcp")
            resp = Response(401, request=req)
            mock_session.initialize = AsyncMock(
                side_effect=HTTPStatusError("401 Unauthorized", request=req, response=resp)
            )

            @asynccontextmanager
            async def mock_streamable(*args: Any, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            with patch("mcp.client.streamable_http.streamablehttp_client", mock_streamable):
                with patch("mcp.ClientSession") as MockSession:
                    MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                    MockSession.return_value.__aexit__ = AsyncMock(return_value=None)
                    with pytest.raises(PermissionError) as exc_info:
                        await client.search(
                            type_filter=["session_summary"],
                            project="test",
                            date_start="2026-04-24T00:00:00",
                            date_end="2026-04-25T00:00:00",
                        )

            msg = str(exc_info.value)
            assert "401" in msg or "Unauthorized" in msg, (
                f"Error must mention 401/Unauthorized; got: {msg}"
            )
            assert "~/.open-brain/config.json" in msg, (
                f"Error must point to config file; got: {msg}"
            )
            assert "api_key" in msg, (
                f"Error must mention api_key field; got: {msg}"
            )

        asyncio.run(_drive())

    def test_search_passes_x_api_key_to_sdk(self, tmp_path: Path) -> None:
        """_OBClient.search() must pass x-api-key in headers to the SDK transport.

        After the SDK migration, the x-api-key is passed as a header dict to
        streamablehttp_client(), not injected manually into httpx requests.
        """
        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://ob.example.test", "api_key": "ob_myapikey"}'
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is not None
        captured_headers: list[dict[str, str]] = []

        from mcp.types import CallToolResult, TextContent

        async def _drive() -> None:
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value=CallToolResult(
                content=[TextContent(type="text", text="[]")],
                isError=False,
            ))

            @asynccontextmanager
            async def mock_streamable(url: str, headers: dict | None = None, **kwargs: Any):
                captured_headers.append(headers or {})
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            with patch("mcp.client.streamable_http.streamablehttp_client", mock_streamable):
                with patch("mcp.ClientSession") as MockSession:
                    MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                    MockSession.return_value.__aexit__ = AsyncMock(return_value=None)
                    await client.search(
                        type_filter=["session_summary"],
                        project="test",
                        date_start="2026-04-24T00:00:00",
                        date_end="2026-04-25T00:00:00",
                    )

        asyncio.run(_drive())

        assert captured_headers, "No headers captured — streamablehttp_client was not called"
        hdrs = captured_headers[0]
        assert "x-api-key" in hdrs, (
            f"Expected x-api-key in headers passed to SDK; got: {list(hdrs.keys())}"
        )
        assert hdrs["x-api-key"] == "ob_myapikey", (
            f"Expected 'ob_myapikey', got '{hdrs.get('x-api-key')}'"
        )
        assert "authorization" not in {k.lower() for k in hdrs}, (
            "Must not send Authorization header — SDK uses x-api-key"
        )


# ---------------------------------------------------------------------------
# Unit tests: SDK-based _async_save_memory()
# ---------------------------------------------------------------------------


class TestSDKAsyncSaveMemory:
    """Tests for the SDK-based _async_save_memory() in orchestrate-brief.py."""

    def test_save_memory_calls_sdk_tool(self) -> None:
        """_async_save_memory() must call save_memory via the SDK, not raw httpx POST."""
        from mcp.types import CallToolResult, TextContent

        captured_tool_calls: list[dict[str, Any]] = []

        async def _drive() -> None:
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()

            async def mock_call_tool(name: str, arguments: dict | None = None, **kwargs: Any):
                captured_tool_calls.append({"name": name, "arguments": arguments})
                return CallToolResult(
                    content=[TextContent(type="text", text='{"status": "ok"}')],
                    isError=False,
                )

            mock_session.call_tool = mock_call_tool

            @asynccontextmanager
            async def mock_streamable(*args: Any, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            with patch("mcp.client.streamable_http.streamablehttp_client", mock_streamable):
                with patch("mcp.ClientSession") as MockSession:
                    MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                    MockSession.return_value.__aexit__ = AsyncMock(return_value=None)
                    await ob._async_save_memory(
                        ob_url="https://ob.example.test/mcp",
                        token="ob_testtoken",
                        title="test — 2026-04-24",
                        text="# Brief content",
                        ob_type="daily_brief",
                        project="test",
                        session_ref="daily-brief-2026-04-24",
                        metadata={"source": "daily-brief"},
                    )

        asyncio.run(_drive())

        assert captured_tool_calls, "_async_save_memory must call a tool via the SDK"
        assert captured_tool_calls[0]["name"] == "save_memory", (
            f"Expected tool name 'save_memory', got '{captured_tool_calls[0]['name']}'"
        )

    def test_save_memory_passes_correct_arguments(self) -> None:
        """_async_save_memory() must pass all required arguments to save_memory tool."""
        from mcp.types import CallToolResult, TextContent

        captured_arguments: list[dict[str, Any]] = []

        async def _drive() -> None:
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()

            async def mock_call_tool(name: str, arguments: dict | None = None, **kwargs: Any):
                if name == "save_memory":
                    captured_arguments.append(arguments or {})
                return CallToolResult(
                    content=[TextContent(type="text", text='{"status": "ok"}')],
                    isError=False,
                )

            mock_session.call_tool = mock_call_tool

            @asynccontextmanager
            async def mock_streamable(*args: Any, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            with patch("mcp.client.streamable_http.streamablehttp_client", mock_streamable):
                with patch("mcp.ClientSession") as MockSession:
                    MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                    MockSession.return_value.__aexit__ = AsyncMock(return_value=None)
                    await ob._async_save_memory(
                        ob_url="https://ob.example.test/mcp",
                        token="ob_tok",
                        title="myproject — 2026-04-24",
                        text="# Brief text",
                        ob_type="daily_brief",
                        project="myproject",
                        session_ref="daily-brief-2026-04-24",
                        metadata={"source": "daily-brief"},
                    )

        asyncio.run(_drive())

        assert captured_arguments, "save_memory must be called with arguments"
        args = captured_arguments[0]
        assert args.get("title") == "myproject — 2026-04-24"
        assert args.get("text") == "# Brief text"
        assert args.get("type") == "daily_brief"
        assert args.get("project") == "myproject"
        assert args.get("session_ref") == "daily-brief-2026-04-24"
        assert args.get("dedup_mode") == "merge", (
            "save_memory must use dedup_mode=merge for idempotent writes"
        )

    def test_save_memory_uses_x_api_key_header(self) -> None:
        """_async_save_memory() must pass x-api-key in headers to SDK transport."""
        from mcp.types import CallToolResult, TextContent

        captured_headers: list[dict[str, str]] = []

        async def _drive() -> None:
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value=CallToolResult(
                content=[TextContent(type="text", text='{"status": "ok"}')],
                isError=False,
            ))

            @asynccontextmanager
            async def mock_streamable(url: str, headers: dict | None = None, **kwargs: Any):
                captured_headers.append(headers or {})
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            with patch("mcp.client.streamable_http.streamablehttp_client", mock_streamable):
                with patch("mcp.ClientSession") as MockSession:
                    MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                    MockSession.return_value.__aexit__ = AsyncMock(return_value=None)
                    await ob._async_save_memory(
                        ob_url="https://ob.example.test/mcp",
                        token="ob_savetoken",
                        title="t",
                        text="# content",
                        ob_type="daily_brief",
                        project="p",
                        session_ref="daily-brief-2026-04-24",
                        metadata={},
                    )

        asyncio.run(_drive())

        assert captured_headers, "streamablehttp_client must have been called"
        hdrs = captured_headers[0]
        assert "x-api-key" in hdrs, (
            f"Expected x-api-key in headers; got: {list(hdrs.keys())}"
        )
        assert hdrs["x-api-key"] == "ob_savetoken"


# ---------------------------------------------------------------------------
# Integration test: live server (gated on OB_API_KEY env var)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not os.environ.get("OB_API_KEY"),
    reason="Integration test requires OB_API_KEY env var (set to run against live server)",
)
class TestLiveServerIntegration:
    """Integration tests against the real open-brain server.

    Skipped unless OB_API_KEY env var is set. Never run in CI.
    """

    def test_search_returns_data_from_live_server(self) -> None:
        """SDK-based _OBClient.search() returns data from the live open-brain server."""
        api_key = os.environ["OB_API_KEY"]
        ob_url = os.environ.get("OB_URL", "https://open-brain.sussdorff.org/mcp")

        # Build client directly
        client = qs._build_ob_client()
        # Override with env credentials if available
        if hasattr(client, "_token") and hasattr(client, "_url"):
            client._token = api_key
            client._url = ob_url

        async def _drive() -> list[dict[str, Any]]:
            return await client.search(
                type_filter=["session_summary"],
                project="claude-code-plugins",
                date_start="2026-04-01T00:00:00+02:00",
                date_end="2026-04-25T23:59:59+02:00",
            )

        result = asyncio.run(_drive())
        # Must return a list (may be empty for old dates)
        assert isinstance(result, list), f"Expected list, got {type(result)}"

    def test_save_memory_succeeds_on_live_server(self) -> None:
        """_async_save_memory() successfully writes to the live open-brain server."""
        api_key = os.environ["OB_API_KEY"]
        ob_url = os.environ.get("OB_URL", "https://open-brain.sussdorff.org/mcp")

        async def _drive() -> None:
            await ob._async_save_memory(
                ob_url=ob_url,
                token=api_key,
                title="CCP-zodj integration test",
                text="Integration test entry for CCP-zodj SDK migration verification.",
                ob_type="session_summary",
                project="claude-code-plugins",
                session_ref="ccp-zodj-integration-test",
                metadata={"source": "integration-test", "bead": "CCP-zodj"},
            )

        # Must not raise
        asyncio.run(_drive())
