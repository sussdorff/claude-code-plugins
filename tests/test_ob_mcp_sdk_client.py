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
- _build_ob_client() returns an object with the correct interface (URL, token, search method)
- _OBClient.search(): method signature and return contract (tested via mock)
- _async_save_memory(): passes correct tool arguments to MCP save_memory
- _async_save_memory(): uses x-api-key (not Authorization: Bearer) in SDK headers
- Integration: gated on OB_API_KEY env var (skip if absent)

Mocking strategy:
  The SDK transport uses a uv-managed venv which makes patching the transport layer
  fragile across different Python environments. Instead, we mock at the client interface
  boundary (client.search, _async_save_memory) or use end-to-end integration tests.

  For _async_save_memory specifically: we patch at the mcp module level within the
  same process that loaded orchestrate-brief.py.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
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
        """_build_ob_client() must construct URL ending in /mcp, not /mcp/mcp.

        Regression: CCP-sd9e — _resolve_ob_credentials() appended '/mcp/mcp'
        instead of '/mcp' to server_url.
        """
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
        assert hasattr(client, "_url"), "Client must expose _url for regression testing"
        assert client._url == "https://open-brain.sussdorff.org/mcp", (
            f"URL must end with /mcp, not /mcp/mcp; got '{client._url}'"
        )
        assert not client._url.endswith("/mcp/mcp"), (
            f"URL must NOT end with /mcp/mcp; got '{client._url}'"
        )

    def test_token_stored_from_config_json(self, tmp_path: Path) -> None:
        """_build_ob_client() must store the token from config.json for SDK use."""
        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://ob.example.test", "api_key": "ob_mytoken"}'
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is not None
        assert hasattr(client, "_token"), "Client must expose _token for testing"
        assert client._token == "ob_mytoken"

    def test_env_token_takes_precedence_over_config_json(self, tmp_path: Path) -> None:
        """OB_TOKEN env var takes precedence over config.json api_key."""
        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://ob.example.test", "api_key": "ob_config_key"}'
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {"OB_TOKEN": "ob_env_key"}, clear=False):
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is not None
        assert client._token == "ob_env_key", (
            "OB_TOKEN env var must override config.json api_key"
        )

    def test_url_from_config_json_used_even_when_env_token_set(self, tmp_path: Path) -> None:
        """config.json server_url is used even when OB_TOKEN env var provides the token.

        Regression: previously config.json was only read when no token was found.
        """
        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://custom.example.org", "api_key": "ob_config_key"}'
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {"OB_TOKEN": "ob_env_key"}, clear=False):
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is not None
        assert client._url == "https://custom.example.org/mcp", (
            f"URL must come from config.json even when OB_TOKEN is set; got '{client._url}'"
        )
        assert client._token == "ob_env_key"


# ---------------------------------------------------------------------------
# Unit tests: SDK-based _OBClient.search() interface contract
# ---------------------------------------------------------------------------


class TestSDKOBClientSearchInterface:
    """Tests for _OBClient.search() interface contract.

    Mocking approach: we mock client.search directly (via AsyncMock) to test
    the upstream consumers (query_sources), and separately verify the method
    signature/contract. Testing the SDK transport layer itself is done via
    integration tests.
    """

    def test_search_result_is_consumed_by_query_sources(
        self, tmp_path: Path
    ) -> None:
        """query_sources uses the result of client.search() for sessions/learnings/decisions."""
        config_path = _REPO_ROOT / "tests" / "fixtures" / "daily_brief_config.yml"

        session_entry = {
            "id": "ob-session-sdk",
            "type": "session_summary",
            "text": "SDK session content",
            "session_ref": "sess-sdk-1",
            "project": "claude-code-plugins",
        }
        learning_entry = {
            "id": "ob-learning-sdk",
            "type": "learning",
            "text": "SDK learning content",
        }

        mock_client = MagicMock()
        mock_client.search = AsyncMock(return_value=[session_entry, learning_entry])

        # Import query_sources' query_sources() function
        result = qs.query_sources(
            project="claude-code-plugins",
            date="2026-04-24",
            config_path=config_path,
            runner=qs.MockCommandRunner({
                "bd list": "[]",
                "bd ready": "[]",
                "bd blocked": "[]",
                "bd human": "[]",
            }),
            ob_client=mock_client,
        )

        mock_client.search.assert_awaited_once()
        assert len(result["data"]["sessions"]) == 1
        assert result["data"]["sessions"][0]["id"] == "ob-session-sdk"
        assert len(result["data"]["learnings"]) == 1

    def test_search_401_from_client_becomes_warning_in_query_sources(self, tmp_path: Path) -> None:
        """When client.search raises PermissionError (401), query_sources emits actionable warning."""
        config_path = _REPO_ROOT / "tests" / "fixtures" / "daily_brief_config.yml"

        mock_client = MagicMock()
        mock_client.search = AsyncMock(
            side_effect=PermissionError(
                "open-brain auth failed (401 Unauthorized). "
                "Check ~/.open-brain/config.json: verify 'api_key' is correct "
                "and not expired."
            )
        )

        result = qs.query_sources(
            project="claude-code-plugins",
            date="2026-04-24",
            config_path=config_path,
            runner=qs.MockCommandRunner({
                "bd list": "[]",
                "bd ready": "[]",
                "bd blocked": "[]",
                "bd human": "[]",
            }),
            ob_client=mock_client,
        )

        ob_warnings = [w for w in result["data"]["warnings"] if w.get("source") == "open-brain"]
        assert ob_warnings, "Expected open-brain warning for 401"
        actionable = [
            w for w in ob_warnings
            if "config.json" in w.get("reason", "") or "api_key" in w.get("reason", "")
        ]
        assert actionable, f"Warning must be actionable (mention config.json/api_key); got: {ob_warnings}"


# ---------------------------------------------------------------------------
# Unit tests: _async_save_memory() with patched SDK
# ---------------------------------------------------------------------------


class TestSDKAsyncSaveMemory:
    """Tests for _async_save_memory() in orchestrate-brief.py.

    Mocking strategy: patch at the function that's called INSIDE _async_save_memory.
    We patch the mcp module imports that are local to _async_save_memory's execution.
    Since _async_save_memory does local imports, we patch the mcp module attributes
    directly in sys.modules so the local import picks them up.
    """

    def _make_mock_session_and_client(self) -> tuple[Any, Any]:
        """Build mock SDK ClientSession and streamablehttp_client context manager."""
        from contextlib import asynccontextmanager

        captured: dict[str, Any] = {"tool_calls": [], "headers": [], "urls": []}
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=MagicMock(isError=False))

        @asynccontextmanager
        async def mock_sh(url: str, headers: dict | None = None, **kwargs: Any):
            captured["headers"].append(headers or {})
            captured["urls"].append(url)
            yield (MagicMock(), MagicMock(), lambda: "session-id")

        return mock_session, mock_sh, captured

    def test_save_memory_is_called_with_correct_tool_name(self) -> None:
        """_async_save_memory() must call the 'save_memory' MCP tool."""
        tool_calls: list[dict[str, Any]] = []

        async def mock_call_tool(name: str, arguments: dict | None = None, **kwargs: Any):
            tool_calls.append({"name": name, "arguments": arguments})
            return MagicMock(isError=False)

        async def _drive() -> None:
            # We need to mock at the module level that _async_save_memory imports from.
            # Since _async_save_memory does local imports, we can intercept by replacing
            # the module attributes in sys.modules before the imports run.
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod

            from contextlib import asynccontextmanager

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(side_effect=mock_call_tool)

            @asynccontextmanager
            async def mock_sh(url: str, headers: dict | None = None, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession

            # Create a context manager class that wraps our mock session
            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
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
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        asyncio.run(_drive())

        assert tool_calls, "_async_save_memory must call at least one MCP tool"
        assert tool_calls[0]["name"] == "save_memory", (
            f"Expected tool name 'save_memory', got '{tool_calls[0]['name']}'"
        )

    def test_save_memory_passes_required_arguments(self) -> None:
        """_async_save_memory() must pass all required arguments to save_memory tool."""
        tool_calls: list[dict[str, Any]] = []

        async def _drive() -> None:
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod
            from contextlib import asynccontextmanager

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()

            async def capture_call(name: str, arguments: dict | None = None, **kwargs: Any):
                tool_calls.append({"name": name, "arguments": arguments})
                return MagicMock(isError=False)

            mock_session.call_tool = AsyncMock(side_effect=capture_call)

            @asynccontextmanager
            async def mock_sh(url: str, headers: dict | None = None, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession
            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
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
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        asyncio.run(_drive())

        assert tool_calls, "save_memory must be called"
        args = tool_calls[0]["arguments"]
        assert args is not None, "arguments must not be None"
        assert args.get("title") == "myproject — 2026-04-24"
        assert args.get("text") == "# Brief text"
        assert args.get("type") == "daily_brief"
        assert args.get("project") == "myproject"
        assert args.get("session_ref") == "daily-brief-2026-04-24"
        assert args.get("dedup_mode") == "merge", (
            "save_memory must use dedup_mode=merge for idempotent writes"
        )

    def test_save_memory_passes_x_api_key_in_headers(self) -> None:
        """_async_save_memory() must pass x-api-key (not Authorization: Bearer) to SDK transport."""
        captured_headers: list[dict[str, str]] = []

        async def _drive() -> None:
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod
            from contextlib import asynccontextmanager

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value=MagicMock(isError=False))

            @asynccontextmanager
            async def mock_sh(url: str, headers: dict | None = None, **kwargs: Any):
                captured_headers.append(dict(headers or {}))
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession
            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
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
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        asyncio.run(_drive())

        assert captured_headers, "streamablehttp_client must have been called"
        hdrs = captured_headers[0]
        assert "x-api-key" in hdrs, (
            f"Expected x-api-key in headers; got: {list(hdrs.keys())}"
        )
        assert hdrs["x-api-key"] == "ob_savetoken"
        assert "authorization" not in {k.lower() for k in hdrs}, (
            "Must NOT send Authorization header — use x-api-key only"
        )


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
    Run with: OB_API_KEY=<key> uv run --with pytest ... python3 -m pytest tests/test_ob_mcp_sdk_client.py -m '' -k 'TestLiveServer'
    """

    def test_search_returns_data_from_live_server(self) -> None:
        """SDK-based _OBClient.search() successfully connects to live open-brain server."""
        import tempfile

        api_key = os.environ["OB_API_KEY"]
        ob_url = os.environ.get("OB_URL", "https://open-brain.sussdorff.org/mcp")

        tmp_path = Path(tempfile.mkdtemp())
        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            json.dumps({"server_url": "https://open-brain.sussdorff.org", "api_key": api_key})
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                client = qs._build_ob_client()

        assert client is not None

        async def _drive() -> list[dict[str, Any]]:
            return await client.search(
                type_filter=["session_summary"],
                project="claude-code-plugins",
                date_start="2026-04-01T00:00:00+02:00",
                date_end="2026-04-25T23:59:59+02:00",
            )

        result = asyncio.run(_drive())
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

        asyncio.run(_drive())
