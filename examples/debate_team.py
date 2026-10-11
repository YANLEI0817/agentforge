"""Example: a debate team with two opposing agents and a supervising synthesizer.

Runs offline with the Mock provider by default. Set ``AGENTFORGE_PROVIDER`` to
use a real provider (e.g. ``anthropic``).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agentforge  # noqa: F401
from agentforge.core.agent import Agent
from agentforge.core.memory import MemoryStore
from agentforge.core.provider import get_provider
from agentforge.core.team import Team


def main() -> None:
    provider_name = os.environ.get("AGENTFORGE_PROVIDER", "mock")
    provider = get_provider(provider_name)()

    pro = Agent(
        name="pro",
        role="You argue strongly in favor of the topic, with clear reasoning.",
        provider=provider,
        tools=[],
        memory=MemoryStore(),
    )
    con = Agent(
        name="con",
        role="You argue strongly against the topic, with clear reasoning.",
        provider=provider,
        tools=[],
        memory=MemoryStore(),
    )

    team = Team(provider, {"pro": pro, "con": con}, max_rounds=3)
    answer = team.run("Is artificial intelligence beneficial to society?")
    print("DEBATE SYNTHESIS:\n", answer)


if __name__ == "__main__":
    main()
