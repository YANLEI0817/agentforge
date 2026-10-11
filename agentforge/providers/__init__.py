"""Provider implementations and the provider registry.

Importing this package registers every bundled provider. The heavy SDKs
(``openai``, ``anthropic``, ``requests``) are imported lazily inside each
provider's ``chat`` method, so the classes can be registered even when the SDK
is not installed - you only need the SDK at call time.
"""

from __future__ import annotations

from ..core.provider import register_provider
from .mock_provider import MockProvider

# The Mock provider is always available (zero dependencies).
register_provider("mock", MockProvider)

# Real providers are registered when their modules import successfully. Their
# SDKs are only required when actually calling ``chat``.
try:
    from .openai_provider import OpenAIProvider

    register_provider("openai", OpenAIProvider)
except Exception:  # pragma: no cover - depends on optional SDK
    pass

try:
    from .anthropic_provider import AnthropicProvider

    register_provider("anthropic", AnthropicProvider)
except Exception:  # pragma: no cover
    pass

try:
    from .ollama_provider import OllamaProvider

    register_provider("ollama", OllamaProvider)
except Exception:  # pragma: no cover
    pass

__all__ = ["MockProvider", "OpenAIProvider", "AnthropicProvider", "OllamaProvider"]
