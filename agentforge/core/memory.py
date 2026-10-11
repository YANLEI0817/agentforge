"""In-memory conversation history plus a long-term key/value store.

This default :class:`MemoryStore` is process-local and ephemeral. It is the
extension point for persistence and semantic retrieval: subclass it (or swap the
instance passed to :class:`~agentforge.core.agent.Agent`) to back it with a
vector database, a SQL store, or Redis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .provider import Message


class MemoryStore:
    """Stores short-term conversation history and long-term key/value memory."""

    def __init__(self) -> None:
        self._history: List[Message] = []
        self._kv: Dict[str, Any] = {}

    def add(
        self,
        role: str,
        content: str,
        tool_call_id: Optional[str] = None,
        tool_calls: Optional[List] = None,
    ) -> None:
        """Append a message to the conversation history.

        Args:
            role: ``user`` / ``assistant`` / ``system`` / ``tool``.
            content: Text content of the message.
            tool_call_id: Links a ``tool`` message to its originating call.
            tool_calls: Tool invocations attached to an ``assistant`` message.
        """
        self._history.append(
            Message(
                role=role,
                content=content,
                tool_call_id=tool_call_id,
                tool_calls=tool_calls,
            )
        )

    def history(self) -> List[Message]:
        """Return a copy of the full conversation history."""
        return list(self._history)

    def remember(self, key: str, value: Any) -> None:
        """Persist a fact in long-term memory."""
        self._kv[key] = value

    def recall(self, key: str) -> Any:
        """Retrieve a fact from long-term memory (``None`` if absent)."""
        return self._kv.get(key)

    def clear(self) -> None:
        """Clear both conversation history and long-term memory."""
        self._history.clear()
        self._kv.clear()
