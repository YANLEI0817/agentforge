"""Tool abstraction, the ``@tool`` decorator, JSON-schema inference, registry.

Tools are plain Python functions wrapped by :class:`Tool`. The ``@tool``
decorator can auto-generate an OpenAI-style JSON schema from the function
signature, type hints and docstring, and registers the tool globally on
definition.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# Global registry of all tools, keyed by name.
TOOLS: dict = {}

# Python type -> JSON schema type.
_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


@dataclass
class Tool:
    """A callable tool with a name, description and JSON-schema parameters."""

    name: str
    description: str
    parameters: dict  # JSON-schema "properties" dict
    func: Callable
    required: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.required is None:
            self.required = list(self.parameters.keys())

    def schema(self) -> dict:
        """Return an OpenAI-style tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required or [],
                },
            },
        }

    def run(self, **kwargs: Any) -> str:
        """Invoke the underlying function and return its result as a string."""
        return str(self.func(**kwargs))

    # Allow ``tool_instance(...)`` as a shortcut for ``tool_instance.run(...)``.
    __call__ = run


def _infer_schema(func: Callable) -> Tuple[dict, List[str]]:
    """Infer ``(properties, required)`` from a function signature + annotations."""
    sig = inspect.signature(func)
    props: Dict[str, dict] = {}
    required: List[str] = []
    for pname, param in sig.parameters.items():
        if pname in ("self", "cls"):
            continue
        ann = param.annotation
        jtype = _TYPE_MAP.get(ann, "string")
        props[pname] = {"type": jtype, "description": f"Parameter '{pname}'."}
        if param.default is inspect.Parameter.empty:
            required.append(pname)
    return props, required


def tool(
    _func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[dict] = None,
):
    """Decorator that turns a function into a registered :class:`Tool`.

    Supports both ``@tool`` (bare) and ``@tool(name=..., description=...)`` forms.
    When *parameters* is omitted, the JSON schema is inferred from the function
    signature (property name = argument name, type mapped from the annotation,
    required = arguments without a default value).
    """

    def decorator(func: Callable) -> Tool:
        tool_name = name or func.__name__
        doc = (func.__doc__ or "").strip()
        desc = description or (doc.splitlines()[0] if doc else tool_name)
        if parameters is not None:
            props, req = parameters, None
        else:
            props, req = _infer_schema(func)
        t = Tool(name=tool_name, description=desc, parameters=props, func=func, required=req)
        register_tool(t)
        return t

    # Bare @tool usage: the decorated function is passed as the first argument.
    if _func is not None:
        return decorator(_func)
    return decorator


def register_tool(t: Tool) -> None:
    """Register a tool instance in the global registry."""
    TOOLS[t.name] = t


def get_tool(name: str) -> Optional[Tool]:
    """Return the tool registered under *name*, or ``None``."""
    return TOOLS.get(name)


def list_tools() -> List[Tool]:
    """Return all registered tools."""
    return list(TOOLS.values())


def get_schemas(names: Optional[List[str]] = None) -> List[dict]:
    """Return tool schemas, optionally restricted to *names*."""
    if names is None:
        tools = list_tools()
    else:
        tools = [t for n in names if (t := get_tool(n)) is not None]
    return [t.schema() for t in tools]
