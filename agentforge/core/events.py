"""Event bus used for observability (the AgentLens foundation).

Every meaningful step in an agent or team run emits an event. By default, when no
``event_bus`` is supplied, :class:`~agentforge.core.agent.Agent` and
:class:`~agentforge.core.team.Team` attach the ``AgentLens`` listener, which
prints a structured, human-readable trace. Advanced users can supply their own
bus to stream events to a UI, a log file, or an OpenTelemetry exporter.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List

# Event name constants.
AGENT_START = "agent.start"
AGENT_THOUGHT = "agent.thought"
TOOL_CALL = "tool.call"
TOOL_RESULT = "tool.result"
AGENT_DONE = "agent.done"
TEAM_ROUTE = "team.route"

_ICONS = {
    AGENT_START: "🚀",
    AGENT_THOUGHT: "🧠",
    TOOL_CALL: "🔧",
    TOOL_RESULT: "📨",
    AGENT_DONE: "✅",
    TEAM_ROUTE: "🧭",
}


def _agentlens_listener(event: str, data: dict) -> None:
    """Default, human-friendly trace printer (the AgentLens subscriber)."""
    msg = (
        data.get("answer")
        or data.get("thought")
        or data.get("result")
        or data.get("tool")
        or data.get("member")
        or data.get("task")
        or ""
    )
    icon = _ICONS.get(event, "•")
    print(f"  {icon} [{event}] {msg}")


class EventBus:
    """Minimal publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event: str, cb: Callable) -> None:
        """Register *cb(event, data)* to be called for *event*."""
        self._subscribers[event].append(cb)

    def emit(self, event: str, **data: object) -> None:
        """Emit *event* with arbitrary keyword *data* to all subscribers."""
        for cb in list(self._subscribers.get(event, [])):
            try:
                cb(event, data)
            except Exception:
                # A misbehaving listener must never break the agent loop.
                pass


def attach_agentlens(bus: EventBus) -> EventBus:
    """Attach the default AgentLens trace listener to *bus* and return it."""
    for ev in (AGENT_START, AGENT_THOUGHT, TOOL_CALL, TOOL_RESULT, AGENT_DONE, TEAM_ROUTE):
        bus.subscribe(ev, _agentlens_listener)
    return bus
