"""Example: a research agent that can calculate, search the web and tell time.

Runs offline with the Mock provider by default. Switch providers with the
environment variable ``AGENTFORGE_PROVIDER`` (e.g. ``export AGENTFORGE_PROVIDER=openai``)
or by editing ``PROVIDER`` below.
"""

import os
import sys

# Make the project root importable when run as a standalone script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agentforge  # noqa: F401  (registers providers + tools)
from agentforge.core.agent import Agent
from agentforge.core.memory import MemoryStore
from agentforge.core.provider import get_provider


def main() -> None:
    provider_name = os.environ.get("AGENTFORGE_PROVIDER", "mock")
    provider = get_provider(provider_name)()

    agent = Agent(
        name="researcher",
        role="You are a diligent research assistant who verifies facts with tools.",
        provider=provider,
        tools=["calculator", "web_search", "get_datetime"],
        memory=MemoryStore(),
    )

    result = agent.run("What is (2+3)*4? Also tell me today's date.")
    print("ANSWER:\n", result.answer)
    print("\nTRACE:")
    for step in result.trace:
        print(" ", step)


if __name__ == "__main__":
    main()
