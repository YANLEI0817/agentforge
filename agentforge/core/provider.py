"""Provider abstraction: message types, result types, and a name registry.

A *Provider* is the only component that talks to an LLM. Everything else in
AgentForge is provider-agnostic, which is what makes the framework portable
across OpenAI, Anthropic, Ollama, or any custom backend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Message:
    """A single message in a conversation.

    Attributes:
        role: One of ``user``, ``assistant``, ``system`` or ``tool``.
        content: The textual content of the message.
        tool_calls: Tool invocations produced by an assistant message.
        tool_call_id: Links a ``tool`` message back to the call that spawned it.
    """

    role: str
    content: str
    tool_calls: Optional[List["ToolCall"]] = None
    tool_call_id: Optional[str] = None


@dataclass
class ToolCall:
    """A request from the model to invoke a tool."""

    id: str
    name: str
    arguments: dict = field(default_factory=dict)


@dataclass
class ChatResult:
    """The result returned by :meth:`Provider.chat`."""

    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw: Any = None


class Provider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.model = model
        self.api_key = api_key
        # Any extra provider-specific options (base_url, temperature, ...) land here.
        self.extra: dict = dict(kwargs)

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Run a chat completion, optionally with tool schemas.

        Args:
            messages: The conversation so far.
            tools: OpenAI-style tool schemas, or ``None`` when no tools are used.
        """
        raise NotImplementedError

    def format_tools(self, tools: List[dict]) -> Any:
        """Optional helper to adapt tool schemas for a specific backend.

        The default implementation returns the schemas unchanged.
        """
        return tools


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------
PROVIDERS: dict = {}


def register_provider(name: str, cls: type) -> None:
    """Register a provider class under *name* (e.g. ``"openai"``)."""
    PROVIDERS[name] = cls


def get_provider(name: str) -> type:
    """Return the registered provider class for *name*.

    Raises:
        KeyError: If *name* is not registered.
    """
    if name not in PROVIDERS:
        raise KeyError(f"Unknown provider: {name!r}. Registered: {list(PROVIDERS)}")
    return PROVIDERS[name]
