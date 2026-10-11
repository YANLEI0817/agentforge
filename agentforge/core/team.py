"""Team: a supervisor routes work to member agents and synthesizes results."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .agent import Agent
from .events import AGENT_DONE, EventBus, TEAM_ROUTE, attach_agentlens
from .provider import ChatResult, Message, Provider


class Team:
    """A supervisor-routed multi-agent team.

    The supervisor (``supervisor_provider``) receives a routing prompt that lists
    the available members and is asked to return JSON indicating which member
    should act next (``{"member": "<name>", ...}``) or that the task is complete
    (``{"member": "synthesis", ...}``). Each chosen member runs as an
    :class:`~agentforge.core.agent.Agent`, and the loop continues until a
    synthesis is produced or ``max_rounds`` is reached.
    """

    def __init__(
        self,
        supervisor_provider: Provider,
        members: Dict[str, Agent],
        event_bus: Optional[EventBus] = None,
        max_rounds: int = 3,
    ) -> None:
        self.supervisor_provider = supervisor_provider
        self.members = members
        self.event_bus = event_bus or attach_agentlens(EventBus())
        self.max_rounds = max_rounds

    # -- internals -------------------------------------------------------
    def _emit(self, event: str, **data: object) -> None:
        self.event_bus.emit(event, **data)

    def _routing_prompt(self, task: str) -> str:
        lines = [
            "You are a supervisor that routes a task to the best team member.",
            "ROUTING MODE",
            f"Task: {task}",
            "Available members:",
        ]
        for name, agent in self.members.items():
            lines.append(f"- {name}: {agent.role}")
        lines.append(
            'Respond ONLY with JSON: {"member": "<name>", "reason": "..."} '
            'or {"member": "synthesis", "answer": "..."} when the task is complete.'
        )
        return "\n".join(lines)

    @staticmethod
    def _safe_json(text: str) -> Optional[dict]:
        text = (text or "").strip()
        try:
            return json.loads(text)
        except Exception:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start : end + 1])
                except Exception:
                    return None
            return None

    def _synthesize(self, task: str, results: Dict[str, str]) -> str:
        if not results:
            return "（无可综合的成员结果）"
        parts = [f"- {name}: {ans}" for name, ans in results.items()]
        return "综合各成员结论：\n" + "\n".join(parts)

    # -- public API ------------------------------------------------------
    def run(self, task: str) -> str:
        """Route *task* through the team and return the synthesized answer."""
        self._emit(TEAM_ROUTE, task=task)
        results: Dict[str, str] = {}

        for _ in range(self.max_rounds):
            msgs = [Message("system", self._routing_prompt(task))]
            if results:
                body = "MEMBER RESULTS:\n" + "\n".join(f"{k}: {v}" for k, v in results.items())
                msgs.append(Message("user", body))

            res: ChatResult = self.supervisor_provider.chat(msgs, tools=None)
            text = (res.content or "").strip()

            # Supervisor signaled completion (Mock returns a FINAL: string).
            if text.startswith("FINAL") or '"synthesis"' in text:
                answer = text.split("FINAL:", 1)[-1].strip() if "FINAL:" in text else text
                self._emit(AGENT_DONE, answer=answer)
                return answer

            parsed = self._safe_json(text)
            member = parsed.get("member") if isinstance(parsed, dict) else None

            if member and member != "synthesis" and member in self.members:
                answer = self.members[member].run(task)
                results[member] = answer
                continue

            # Unknown member or explicit synthesis -> finalize.
            return self._synthesize(task, results)

        return self._synthesize(task, results)
