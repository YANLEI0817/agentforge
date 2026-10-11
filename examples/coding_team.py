"""Example: a coding team with an architect and an engineer, supervised by a router.

Runs offline with the Mock provider by default. Set ``AGENTFORGE_PROVIDER`` to
use a real provider (e.g. ``openai``).
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

    architect = Agent(
        name="architect",
        role="You design clear, modular software architecture.",
        provider=provider,
        tools=["read_file"],
        memory=MemoryStore(),
    )
    engineer = Agent(
        name="engineer",
        role="You implement the design in correct, tested code.",
        provider=provider,
        tools=[],
        memory=MemoryStore(),
    )

    team = Team(provider, {"architect": architect, "engineer": engineer}, max_rounds=3)
    answer = team.run("Build a command-line calculator in Python.")
    print("TEAM RESULT:\n", answer)


if __name__ == "__main__":
    main()
