"""Ollama provider (real implementation; calls a local Ollama server)."""

from __future__ import annotations

from typing import Any, List, Optional

from ..core.provider import ChatResult, Message, Provider, ToolCall


class OllamaProvider(Provider):
    """Provider that talks to a local Ollama server over HTTP."""

    def __init__(
        self,
        model: str = "llama3",
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:11434/api/chat",
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, api_key=api_key, **kwargs)
        self.base_url = base_url

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """POST to the local Ollama ``/api/chat`` endpoint."""
        import requests  # lazy import

        payload: dict = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content or ""} for m in messages],
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        timeout = kwargs.get("timeout", self.extra.get("timeout", 120))

        resp = requests.post(self.base_url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message", {})
        content = msg.get("content", "")
        tool_calls: List[ToolCall] = []
        for i, tc in enumerate(msg.get("tool_calls", [])):
            fn = tc.get("function", {})
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", f"call_{i}"),
                    name=fn.get("name", ""),
                    arguments=fn.get("arguments", {}),
                )
            )
        return ChatResult(content=content, tool_calls=tool_calls, raw=data)
