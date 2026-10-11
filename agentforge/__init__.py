"""AgentForge - a lightweight, provider-agnostic AI agent framework.

AgentForge runs out-of-the-box with a zero-API-key Mock provider so that every
example and test works offline. Real providers (OpenAI, Anthropic, Ollama) are
opt-in extras.

Importing this package registers the built-in providers and tools.
"""

from . import core  # noqa: F401
from . import providers  # noqa: F401  (registers providers)
from . import tools  # noqa: F401  (registers built-in tools)

__version__ = "0.1.0"
__all__ = ["core", "providers", "tools", "__version__"]
