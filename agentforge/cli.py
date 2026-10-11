"""Command-line entry point for AgentForge.

Examples
--------
Run a research agent with the zero-key Mock provider::

    python -m agentforge.cli --task "计算 (2+3)*4 并向我解释"

Run a debate team::

    python -m agentforge.cli --agent debate --task "AI 对人类是利大于弊吗？"
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from .core.memory import MemoryStore
from .core.provider import get_provider


# Tool sets and roles for the built-in single-agent presets.
_AGENT_TOOLS: Dict[str, List[str]] = {
    "research": ["calculator", "web_search", "get_datetime"],
    "coding": ["read_file", "calculator"],
}
_AGENT_ROLES: Dict[str, str] = {
    "research": "You are a diligent research assistant who verifies facts with tools.",
    "coding": "You are a software engineer who writes correct, well-tested code.",
}


def _build_agent(provider: Any, kind: str, max_iterations: int) -> Any:
    from .core.agent import Agent

    return Agent(
        name=kind,
        role=_AGENT_ROLES.get(kind, "You are a helpful assistant."),
        provider=provider,
        tools=_AGENT_TOOLS.get(kind, ["calculator"]),
        memory=MemoryStore(),
        max_iterations=max_iterations,
    )


def _build_team(provider: Any, kind: str) -> Any:
    from .core.agent import Agent
    from .core.team import Team

    if kind == "debate":
        pro = Agent("pro", "You argue strongly in favor of the topic.", provider, tools=[], memory=MemoryStore())
        con = Agent("con", "You argue strongly against the topic.", provider, tools=[], memory=MemoryStore())
        return Team(provider, {"pro": pro, "con": con})
    # coding team
    architect = Agent(
        "architect", "You design clear software architecture.", provider, tools=["read_file"], memory=MemoryStore()
    )
    engineer = Agent("engineer", "You implement the design in code.", provider, tools=[], memory=MemoryStore())
    return Team(provider, {"architect": architect, "engineer": engineer})


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agentforge",
        description="Run an AgentForge agent or team (defaults to the Mock provider).",
    )
    parser.add_argument("--task", required=True, help="The task/question to run.")
    parser.add_argument(
        "--agent",
        choices=["research", "coding", "debate"],
        default=None,
        help="Preset to run. Omit for a default research agent.",
    )
    parser.add_argument("--provider", default="mock", help="Provider name (default: mock).")
    parser.add_argument("--model", default=None, help="Model name passed to the provider.")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max ReAct iterations (agents).")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)
    provider_cls = get_provider(args.provider)
    provider = provider_cls(model=args.model)

    if args.agent == "debate":
        team = _build_team(provider, "debate")
        answer = team.run(args.task)
        print("\nTEAM ANSWER:\n")
        print(answer)
        return

    kind = args.agent or "research"
    agent = _build_agent(provider, kind, args.max_iterations)
    result = agent.run(args.task)

    print("\nANSWER:\n")
    print(result.answer)
    print("\nTRACE:")
    for step in result.trace:
        calls = ", ".join(step.get("tool_calls") or []) or "-"
        print(f"  step {step['iteration']}: thought={step['thought'][:80]!r} tools=[{calls}]")


if __name__ == "__main__":
    main()
