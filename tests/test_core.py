"""Tests for core primitives: MemoryStore, EventBus, and the provider registry."""

import agentforge  # noqa: F401  (registers providers + tools)

from agentforge.core.events import AGENT_DONE, EventBus
from agentforge.core.memory import MemoryStore
from agentforge.core.provider import PROVIDERS, get_provider


def test_memory_store_basic():
    m = MemoryStore()
    m.add("user", "hello")
    assert len(m.history()) == 1
    assert m.history()[0].content == "hello"

    m.remember("lang", "python")
    assert m.recall("lang") == "python"

    m.clear()
    assert m.history() == []
    assert m.recall("lang") is None


def test_memory_tool_message_links_call():
    m = MemoryStore()
    m.add("tool", "42", tool_call_id="call_1")
    msg = m.history()[0]
    assert msg.role == "tool"
    assert msg.tool_call_id == "call_1"


def test_event_bus_pubsub():
    bus = EventBus()
    received = []
    bus.subscribe(AGENT_DONE, lambda e, d: received.append(d))
    bus.emit(AGENT_DONE, answer="done")
    assert received and received[0]["answer"] == "done"


def test_event_bus_unknown_event_is_safe():
    bus = EventBus()
    bus.emit("nothing.happened", value=1)  # must not raise


def test_provider_registry():
    assert "mock" in PROVIDERS
    cls = get_provider("mock")
    assert cls is not None
    inst = cls()
    assert inst.model  # defaults to "mock-1"
