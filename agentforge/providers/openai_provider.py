"""OpenAI provider (real implementation; requires the ``openai`` SDK)."""

from __future__ import annotations

import json
import os
from typing import Any, List, Optional

from ..core.provider import ChatResult, Message, Provider, ToolCall


class OpenAIProvider(Provider):
    """Provider backed by ``openai`` (``client.chat.completions``)."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, api_key=api_key, **kwargs)

    @staticmethod
    def _to_openai_messages(messages: List[Message]) -> List[dict]:
        out: List[dict] = []
        for m in messages:
            d: dict = {"role": m.role, "content": m.content or ""}
            if m.role == "tool" and m.tool_call_id:
                d["tool_call_id"] = m.tool_call_id
            if m.tool_calls:
                d["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                    }
                    for tc in m.tool_calls
                ]
            out.append(d)
        return out

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Call the OpenAI chat completions API with optional tools."""
        import openai  # lazy import: only needed at call time

        client = openai.OpenAI(api_key=self.api_key or os.environ.get("OPENAI_API_KEY"))
        call_kwargs: dict = {
            "model": self.model,
            "messages": self._to_openai_messages(messages),
        }
        if tools:
            call_kwargs["tools"] = tools
            call_kwargs["tool_choice"] = "auto"
        # Allow callers to override temperature, max_tokens, etc.
        call_kwargs.update({k: v for k, v in self.extra.items() if k not in call_kwargs})
        call_kwargs.update(kwargs)

        resp = client.chat.completions.create(**call_kwargs)
        choice = resp.choices[0].message
        content = choice.content or ""
        tool_calls: List[ToolCall] = []
        if choice.tool_calls:
            for tc in choice.tool_calls:
                args: dict = {}
                if tc.function.arguments:
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
        return ChatResult(content=content, tool_calls=tool_calls, raw=resp)
