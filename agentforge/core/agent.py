"""ReAct agent with an extensible tool-using reasoning loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Union

from .events import (
    AGENT_DONE,
    AGENT_START,
    AGENT_THOUGHT,
    TOOL_CALL,
    TOOL_RESULT,
    EventBus,
    attach_agentlens,
)
from .memory import MemoryStore
from .provider import ChatResult, Message, Provider
from .tool import Tool, get_tool


@dataclass
class AgentResult:
    """The outcome of :meth:`Agent.run`."""

    answer: str
    trace: List[dict] = field(default_factory=list)


class Agent:
    """An agent that runs a ReAct-style reasoning loop using a provider.

    Loop (bounded by ``max_iterations``):

    1. Put the task into memory as a ``user`` message (first run only).
    2. Build a system prompt describing the role and the available tools.
    3. Call ``provider.chat(messages, tools=schemas)``.
    4. If the model asks for tool calls, execute each one via the global tool
       registry, append the result as a ``tool`` message, and loop again.
    5. Otherwise treat the content as the final answer (stripping the
       ``FINAL:`` prefix if present) and return.
    """

    def __init__(
        self,
        name: str,
        role: str,
        provider: Provider,
        tools: Optional[Union[List[str], List[Tool]]] = None,
        memory: Optional[MemoryStore] = None,
        max_iterations: int = 5,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.name = name
        self.role = role
        self.provider = provider
        self.memory = memory or MemoryStore()
        self.max_iterations = max_iterations
        self.event_bus = event_bus or attach_agentlens(EventBus())
        self.tools: List[Tool] = []
        if tools:
            for t in tools:
                if isinstance(t, Tool):
                    self.tools.append(t)
                elif isinstance(t, str):
                    resolved = get_tool(t)
                    if resolved is None:
                        raise ValueError(f"Unknown tool: {t!r}")
                    self.tools.append(resolved)
                else:
                    raise TypeError(f"tools must be Tool instances or names, got {type(t)}")

    # -- internals -------------------------------------------------------
    def _emit(self, event: str, **data: object) -> None:
        self.event_bus.emit(event, **data)

    def _system_prompt(self) -> str:
        lines = [f"You are {self.name}.", self.role.strip(), ""]
        if self.tools:
            lines.append("You have access to the following tools:")
            for t in self.tools:
                lines.append(f"- {t.name}: {t.description}")
            lines.append("")
            lines.append(
                "To solve the task, call a tool when it helps. When you have the "
                "final answer, prefix it with 'FINAL:' (for example: "
                "'FINAL: the answer is 42')."
            )
        else:
            lines.append(
                "Answer the user's request directly, prefixing the final answer "
                "with 'FINAL:'."
            )
        return "\n".join(lines)

    # -- public API ------------------------------------------------------
    def run(self, task: str) -> AgentResult:
        """Run the reasoning loop on *task* and return an :class:`AgentResult`."""
        self._emit(AGENT_START, name=self.name, task=task)
        if not self.memory.history():
            self.memory.add("user", task)

        schemas = [t.schema() for t in self.tools] or None
        trace: List[dict] = []

        for i in range(self.max_iterations):
            messages = [Message("system", self._system_prompt())] + self.memory.history()
            result: ChatResult = self.provider.chat(messages, tools=schemas)
            self._emit(AGENT_THOUGHT, name=self.name, thought=result.content)

            if result.tool_calls:
                calls: List[str] = []
                observations: List[str] = []
                for tc in result.tool_calls:
                    tool = get_tool(tc.name)
                    self._emit(TOOL_CALL, name=self.name, tool=tc.name, arguments=tc.arguments)
                    if tool is None:
                        obs = f"Error: tool '{tc.name}' is not registered."
                    else:
                        try:
                            obs = tool.run(**tc.arguments)
                        except Exception as exc:  # keep the loop alive
                            obs = f"Error executing {tc.name}: {exc}"
                    self._emit(TOOL_RESULT, name=self.name, tool=tc.name, result=obs)
                    self.memory.add("tool", obs, tool_call_id=tc.id)
                    calls.append(tc.name)
                    observations.append(obs)
                trace.append(
                    {
                        "iteration": i,
                        "thought": result.content or "",
                        "tool_calls": calls,
                        "observation": " | ".join(observations)[:500],
                    }
                )
                continue

            answer = result.content or ""
            for prefix in ("FINAL:", "FINAL："):
                if answer.startswith(prefix):
                    answer = answer[len(prefix):].strip()
                    break
            trace.append({"iteration": i, "thought": answer, "tool_calls": [], "observation": None})
            self._emit(AGENT_DONE, name=self.name, answer=answer)
            return AgentResult(answer=answer, trace=trace)

        answer = "（已达到最大迭代次数，未能给出最终答案）"
        trace.append(
            {"iteration": self.max_iterations, "thought": answer, "tool_calls": [], "observation": None}
        )
        self._emit(AGENT_DONE, name=self.name, answer=answer)
        return AgentResult(answer=answer, trace=trace)
