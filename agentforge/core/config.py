"""Configuration loading from dicts, YAML strings, or YAML files."""

from __future__ import annotations

import os
from typing import Any, Dict, Union

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is an optional convenience
    yaml = None  # type: ignore[assignment]


def load_config(source: Union[dict, str]) -> Dict[str, Any]:
    """Load configuration from a dict, a YAML string, or a file path.

    Args:
        source: A ``dict`` (returned as-is), a path to a ``.yaml``/``.yml`` file,
            or an inline YAML string.

    Raises:
        TypeError: If *source* is neither a dict nor a string.
        RuntimeError: If PyYAML is required but not installed.
    """
    if isinstance(source, dict):
        return dict(source)
    if not isinstance(source, str):
        raise TypeError("source must be a dict, a YAML string, or a file path")

    if os.path.exists(source):
        if yaml is None:
            raise RuntimeError("PyYAML is required to load config files (pip install pyyaml).")
        with open(source, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    if yaml is None:
        raise RuntimeError("PyYAML is required to parse YAML strings (pip install pyyaml).")
    return yaml.safe_load(source) or {}


def default_config() -> Dict[str, Any]:
    """Return a sensible default configuration."""
    return {
        "provider": "mock",
        "model": "mock-1",
        "max_iterations": 5,
        "max_rounds": 3,
    }
