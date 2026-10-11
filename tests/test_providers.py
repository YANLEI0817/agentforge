"""Offline unit tests for the real providers (OpenAI / Anthropic / Ollama).

These tests never touch the network and never require an API key. Instead they
inject *fake* SDK modules (``openai`` / ``anthropic`` / ``requests``) into
``sys.modules`` so the provider's request-building and response-parsing logic is
exercised end to end. This proves the conversion code is correct rather than
merely "importable".
"""

from __future__ import annotations

import json
import sys
import types
from typing import Any, Dict

import pytest

import agentforge  # noqa: F401  (registers providers + tools)

from agentforge.core.provider import Message
from agentforge.providers.anthropic_provider import AnthropicProvider
from agentforge.providers.ollama_provider import OllamaProvider
from agentforge.providers.openai_provider import OpenAIProvider


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------
def _fake_openai_module(response: Any) -> types.ModuleType:
    """Build a fake ``openai`` module returning *response* from create()."""

    module = types.ModuleType("openai")

    class _Completions:
        def create(self, **kwargs: Any) -> Any:
            return response

    class _Chat:
        def __init__(self) -> None:
            self.completions = _Completions()

    class _Client:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.chat = _Chat()

    module.OpenAI = _Client  # type: ignore[attr-defined]
    return module


def _fake_anthropic_module(response: Any) -> types.ModuleType:
    """Build a fake ``anthropic`` module returning *response* from create()."""

    module = types.ModuleType("anthropic")

    class _Messages:
        def create(self, **kwargs: Any) -> Any:
            return response

    class _Client:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.messages = _Messages()

    module.Anthropic = _Client  # type: ignore[attr-defined]
    return module


def _fake_requests_module(
    response: Any, captured: Dict[str, Any]
) -> types.ModuleType:
    """Build a fake ``requests`` module recording calls and returning *response*."""

    module = types.ModuleType("requests")

    def post(url: str, json: Any = None, timeout: Any = None, **kwargs: Any) -> Any:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return response

    module.post = post  # type: ignore[attr-defined]
    return module


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------
def test_openai_parses_content_and_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    message = types.SimpleNamespace(
        content="Let me compute that.",
        tool_calls=[
            types.SimpleNamespace(
                id="call_abc",
                type="function",
                function=types.SimpleNamespace(
                    name="calculator", arguments=json.dumps({"expression": "2+3*4"})
                ),
            )
        ],
    )
    response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])
    monkeypatch.setitem(sys.modules, "openai", _fake_openai_module(response))

    provider = OpenAIProvider(model="gpt-4o-mini", api_key="test-key")
    result = provider.chat([Message(role="user", content="calc 2+3*4")])

    assert result.content == "Let me compute that."
    assert len(result.tool_calls) == 1
    call = result.tool_calls[0]
    assert call.id == "call_abc"
    assert call.name == "calculator"
    assert call.arguments == {"expression": "2+3*4"}


def test_openai_handles_content_only(monkeypatch: pytest.MonkeyPatch) -> None:
    message = types.SimpleNamespace(content="Hello!", tool_calls=None)
    response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])
    monkeypatch.setitem(sys.modules, "openai", _fake_openai_module(response))

    provider = OpenAIProvider()
    result = provider.chat([Message(role="user", content="hi")])

    assert result.content == "Hello!"
    assert result.tool_calls == []


def test_openai_tolerates_invalid_arguments_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = types.SimpleNamespace(
        content="",
        tool_calls=[
            types.SimpleNamespace(
                id="call_bad",
                function=types.SimpleNamespace(name="calculator", arguments="{not json"),
            )
        ],
    )
    response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])
    monkeypatch.setitem(sys.modules, "openai", _fake_openai_module(response))

    result = OpenAIProvider().chat([Message(role="user", content="x")])

    assert len(result.tool_calls) == 1
    # Malformed JSON must degrade to an empty dict instead of raising.
    assert result.tool_calls[0].arguments == {}


def test_openai_message_conversion_includes_tools_and_tool_links() -> None:
    from agentforge.core.provider import ToolCall

    messages = [
        Message(role="system", content="be terse"),
        Message(
            role="assistant",
            content="",
            tool_calls=[ToolCall(id="c1", name="calculator", arguments={"expression": "1+1"})],
        ),
        Message(role="tool", content="2", tool_call_id="c1"),
    ]
    converted = OpenAIProvider._to_openai_messages(messages)

    assert converted[0] == {"role": "system", "content": "be terse"}
    assistant = converted[1]
    assert assistant["tool_calls"][0]["id"] == "c1"
    assert assistant["tool_calls"][0]["function"]["name"] == "calculator"
    assert json.loads(assistant["tool_calls"][0]["function"]["arguments"]) == {
        "expression": "1+1"
    }
    assert converted[2]["tool_call_id"] == "c1"


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------
def test_anthropic_parses_text_and_tool_use(monkeypatch: pytest.MonkeyPatch) -> None:
    response = types.SimpleNamespace(
        content=[
            types.SimpleNamespace(type="text", text="Thinking... "),
            types.SimpleNamespace(
                type="tool_use",
                id="toolu_1",
                name="calculator",
                input={"expression": "2+3*4"},
            ),
        ]
    )
    monkeypatch.setitem(sys.modules, "anthropic", _fake_anthropic_module(response))

    provider = AnthropicProvider(api_key="test-key")
    result = provider.chat([Message(role="user", content="calc")])

    assert result.content == "Thinking... "
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "toolu_1"
    assert result.tool_calls[0].name == "calculator"
    assert result.tool_calls[0].arguments == {"expression": "2+3*4"}


def test_anthropic_passes_system_and_flattens_tool_schemas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: Dict[str, Any] = {}

    module = types.ModuleType("anthropic")

    class _Messages:
        def create(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text="ok")])

    class _Client:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.messages = _Messages()

    module.Anthropic = _Client  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "anthropic", module)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "compute",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]
    provider = AnthropicProvider()
    result = provider.chat(
        [Message(role="system", content="SYSTEM RULE"), Message(role="user", content="hi")],
        tools=tools,
    )

    assert result.content == "ok"
    assert captured["system"] == "SYSTEM RULE"
    # Anthropic expects the bare function schema (no "type": "function" wrapper).
    assert captured["tools"] == [tools[0]["function"]]
    # The system message must not leak into the conversation messages list.
    assert all(m["role"] != "system" for m in captured["messages"])


# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------
def test_ollama_parses_message_and_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "message": {
            "content": "Working on it.",
            "tool_calls": [
                {"id": "call_1", "function": {"name": "calculator", "arguments": {"expression": "2+3"}}}
            ],
        }
    }
    response = types.SimpleNamespace(
        json=lambda: payload,
        raise_for_status=lambda: None,
    )
    captured: Dict[str, Any] = {}
    monkeypatch.setitem(sys.modules, "requests", _fake_requests_module(response, captured))

    provider = OllamaProvider(model="llama3")
    result = provider.chat([Message(role="user", content="calc")])

    assert result.content == "Working on it."
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "calculator"
    assert result.tool_calls[0].arguments == {"expression": "2+3"}

    # Verify the outgoing payload shape.
    assert captured["url"] == provider.base_url
    assert captured["json"]["model"] == "llama3"
    assert captured["json"]["stream"] is False


def test_ollama_assigns_fallback_id_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"message": {"content": "", "tool_calls": [{"function": {"name": "get_datetime", "arguments": {}}}]}}
    response = types.SimpleNamespace(json=lambda: payload, raise_for_status=lambda: None)
    monkeypatch.setitem(sys.modules, "requests", _fake_requests_module(response, {}))

    result = OllamaProvider().chat([Message(role="user", content="x")])

    assert result.tool_calls[0].id == "call_0"
    assert result.tool_calls[0].name == "get_datetime"
