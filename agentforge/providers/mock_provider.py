"""Zero-dependency, key-free Mock provider.

This provider makes AgentForge *runnable with no API key*, which is essential
for tutorials, CI and open-source discovery. It never performs a network
request; its behaviour is derived deterministically from the conversation state
so that both the ReAct agent loop and the Team supervisor routing can be
demonstrated offline.
"""

from __future__ import annotations

import re
from typing import List, Optional

from ..core.provider import ChatResult, Message, Provider, ToolCall


class MockProvider(Provider):
    """A deterministic provider that drives agents and teams offline."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: object,
    ) -> None:
        super().__init__(model=model or "mock-1", api_key=api_key, **kwargs)

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _system_text(messages: List[Message]) -> str:
        return "\n".join(m.content for m in messages if m.role == "system")

    @staticmethod
    def _last_user(messages: List[Message]) -> str:
        for m in reversed(messages):
            if m.role == "user":
                return m.content or ""
        return ""

    @staticmethod
    def _has_member_results(messages: List[Message]) -> bool:
        return any("MEMBER RESULTS" in (m.content or "").upper() for m in messages)

    @staticmethod
    def _tool_summary(messages: List[Message]) -> str:
        parts = [m.content for m in messages if m.role == "tool" and m.content]
        return "；".join(parts)[:300] if parts else "（无工具结果）"

    @staticmethod
    def _first_member(system_text: str) -> str:
        for line in system_text.splitlines():
            s = line.strip()
            if s[:1] in ("-", "*"):
                name = s[1:].split(":")[0].strip().strip("`").strip('"')
                if name:
                    return name
        return "agent"

    @staticmethod
    def _default_args(name: str, user_text: str) -> dict:
        if name == "calculator":
            return {"expression": "2+3*4"}
        if name == "get_datetime":
            return {}
        if name == "read_file":
            match = re.search(r"[\w./\\-]+\.\w+", user_text)
            return {"path": match.group(0) if match else "README.md"}
        if name == "web_search":
            return {"query": user_text[:50]}
        return {}

    # -- main entry ------------------------------------------------------
    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[dict]] = None,
        **kwargs: object,
    ) -> ChatResult:
        system_text = self._system_text(messages)
        user_text = self._last_user(messages)
        has_tool_result = any(m.role == "tool" for m in messages)
        has_tool_call_in_history = any(m.tool_calls for m in messages)

        is_routing = ("ROUTING" in system_text) or ("member" in system_text.lower())

        # --- Team supervisor routing -----------------------------------
        if is_routing and not tools:
            if self._has_member_results(messages):
                return ChatResult(
                    content="FINAL: 综合各成员结论：团队已完成任务并汇总各方观点。",
                    tool_calls=[],
                )
            member = self._first_member(system_text)
            return ChatResult(
                content=f'{{"member": "{member}", "reason": "demo routing"}}',
                tool_calls=[],
            )

        # --- ReAct agent step ------------------------------------------
        if tools and not (has_tool_result or has_tool_call_in_history):
            first = tools[0]
            name = first.get("function", {}).get("name", "tool")
            args = self._default_args(name, user_text)
            return ChatResult(
                content="",
                tool_calls=[ToolCall(id="call_1", name=name, arguments=args)],
            )

        # --- Final answer ----------------------------------------------
        summary = self._tool_summary(messages)
        return ChatResult(content=f"FINAL: 根据工具结果，答案是：{summary}。", tool_calls=[])
