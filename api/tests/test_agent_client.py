"""Tests for the agent_client module.

Covers per testing-standards.md §4:
  - Happy path: successful agent invocation, response parsing
  - Sad path: timeout, SDK exception, malformed responses
"""

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.agent_client import (
    AgentInvocationError,
    _parse_agent_response,
    _parse_json_string,
    query_reasoning_engine,
)


# ── Response Parsing ─────────────────────────────────────────────────────────


def test_parse_dict_response():
    """Direct dict response is returned as-is."""
    data = {"briefing": "test", "p2bScore": 42}
    assert _parse_agent_response(data) == data


def test_parse_wrapped_dict_response():
    """Dict wrapped in {"output": {...}} is unwrapped."""
    inner = {"briefing": "test"}
    assert _parse_agent_response({"output": inner}) == inner


def test_parse_string_json_response():
    """JSON string is parsed to dict."""
    data = {"briefing": "hello"}
    result = _parse_agent_response(json.dumps(data))
    assert result == data


def test_parse_markdown_fenced_json():
    """JSON wrapped in markdown code fences is extracted."""
    raw = '```json\n{"briefing": "hello"}\n```'
    result = _parse_json_string(raw)
    assert result == {"briefing": "hello"}


def test_parse_json_embedded_in_text():
    """JSON embedded in surrounding text is extracted via brace-matching."""
    raw = 'Here is the result: {"briefing": "found"} end'
    result = _parse_json_string(raw)
    assert result == {"briefing": "found"}


def test_parse_unparseable_string_returns_fallback():
    """Unparseable string returns fallback with raw text as briefing."""
    result = _parse_json_string("This is just plain text with no JSON")
    assert result["briefing"] == "This is just plain text with no JSON"


def test_parse_non_dict_non_string():
    """Non-dict, non-string response is converted to string."""
    result = _parse_agent_response(12345)
    assert result == {"briefing": "12345"}


# ── SDK Invocation ───────────────────────────────────────────────────────────


async def test_query_reasoning_engine_success():
    """Successful invocation returns output + latency_ms."""
    mock_response = {"briefing": "AI result", "p2bScore": 80}

    with patch(
        "app.services.agent_client._invoke_sync",
        return_value=mock_response,
    ):
        result = await query_reasoning_engine(
            project_id="test-project",
            location="us-central1",
            agent_id="123456",
            input_text="test input",
        )

    assert result["output"] == mock_response
    assert isinstance(result["latency_ms"], int)
    assert result["latency_ms"] >= 0


async def test_query_reasoning_engine_timeout():
    """Timeout raises AgentInvocationError."""
    import time

    def slow_sync(*args):
        time.sleep(10)
        return {}

    with patch(
        "app.services.agent_client._invoke_sync",
        side_effect=slow_sync,
    ):
        with pytest.raises(AgentInvocationError, match="timed out"):
            await query_reasoning_engine(
                project_id="test-project",
                location="us-central1",
                agent_id="123456",
                input_text="test",
                timeout=1,
            )


async def test_query_reasoning_engine_sdk_error():
    """SDK exception raises AgentInvocationError."""
    with patch(
        "app.services.agent_client._invoke_sync",
        side_effect=RuntimeError("Connection refused"),
    ):
        with pytest.raises(AgentInvocationError, match="Connection refused"):
            await query_reasoning_engine(
                project_id="test-project",
                location="us-central1",
                agent_id="123456",
                input_text="test",
            )
