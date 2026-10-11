"""Anthropic provider (real implementation; requires the ``anthropic`` SDK)."""

from __future__ import annotations

import os
from typing import Any, List, Optional

from ..core.provider import ChatResult, Message, Provider, ToolCall


class AnthropicProvider(Provider):
    """Provider backed by ``anthropic`` (``messages.create``)."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-latest",
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, api_key=api_key, **kwargs)

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Call the Anthropic Messages API with optional tools."""
        import anthropic  # lazy import

        client = anthropic.Anthropic(api_key=self.api_key or os.environ.get("ANTHROPIC_API_KEY"))
        system_text = "\n".join(m.content for m in messages if m.role == "system")
        convo = [
            {"role": m.role if m.role != "system" else "user", "content": m.content or ""}
            for m in messages
            if m.role != "system"
        ]
        call_kwargs: dict = {
            "model": self.model,
            "messages": convo,
            "max_tokens": kwargs.get("max_tokens", self.extra.get("max_tokens", 1024)),
        }
        if system_text:
            call_kwargs["system"] = system_text
        if tools:
            call_kwargs["tools"] = [t["function"] for t in tools]
        call_kwargs.update({k: v for k, v in self.extra.items() if k not in call_kwargs})
        call_kwargs.update(kwargs)

        resp = client.messages.create(**call_kwargs)
        content_text = ""
        tool_calls: List[ToolCall] = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                content_text += block.text
            elif getattr(block, "type", None) == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=dict(block.input))
                )
        return ChatResult(content=content_text, tool_calls=tool_calls, raw=resp)
