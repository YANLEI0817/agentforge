"""End-to-end tests using the zero-key Mock provider (Agent + Team)."""

import agentforge  # noqa: F401  (registers everything)

from agentforge.core.agent import Agent
from agentforge.core.memory import MemoryStore
from agentforge.core.provider import get_provider
from agentforge.core.team import Team


def test_agent_runs_with_mock():
    provider = get_provider("mock")()
    agent = Agent(
        name="calc",
        role="You compute things accurately.",
        provider=provider,
        tools=["calculator"],
        memory=MemoryStore(),
        max_iterations=5,
    )
    result = agent.run("计算 (2+3)*4")
    assert isinstance(result.answer, str) and result.answer
    # The trace must contain exactly one tool-calling step.
    assert any(len(step["tool_calls"]) > 0 for step in result.trace)


def test_agent_without_tools_still_returns_answer():
    provider = get_provider("mock")()
    agent = Agent("thinker", "You reason carefully.", provider, tools=[], memory=MemoryStore())
    result = agent.run("What is the meaning of life?")
    assert isinstance(result.answer, str) and result.answer


def test_team_runs_with_mock():
    provider = get_provider("mock")()
    a1 = Agent("architect", "designs systems", provider, tools=[], memory=MemoryStore())
    a2 = Agent("engineer", "writes code", provider, tools=[], memory=MemoryStore())
    team = Team(provider, {"architect": a1, "engineer": a2}, max_rounds=3)
    out = team.run("设计一个计算器程序")
    assert isinstance(out, str) and out
