"""Built-in tools, registered automatically via the ``@tool`` decorator."""

from __future__ import annotations

import ast
import math
import operator
import re
from datetime import datetime

from ..core.tool import tool

# AST-based safe arithmetic evaluator for ``calculator``.
# Only numeric literals and a small set of operators are allowed, which
# prevents arbitrary code execution *and* resource-exhaustion attacks such as
# ``9**9**9`` (huge integers) that a character whitelist cannot stop.
_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

# Reject exponents that would blow up memory/time before they are computed.
_POW_MAX_EXP = 1000
# Reject results whose magnitude would be impractical to materialise.
_RESULT_MAX_MAGNITUDE = 1e18


def _safe_eval(node: ast.AST):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            if isinstance(node.value, float) and not math.isfinite(node.value):
                raise ValueError("non-finite numbers are not allowed")
            return node.value
        raise ValueError("only numeric constants are allowed")
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if type(node.op) is ast.Pow:
            if not isinstance(right, (int, float)) or abs(right) > _POW_MAX_EXP:
                raise ValueError("exponent too large")
        result = _BINOPS[type(node.op)](left, right)
        if isinstance(result, (int, float)) and abs(result) > _RESULT_MAX_MAGNITUDE:
            raise ValueError("result magnitude too large")
        return result
    raise ValueError("unsupported expression")


@tool
def calculator(expression: str) -> str:
    """Evaluate a safe arithmetic expression.

    Uses an AST whitelist: only numeric literals and the operators
    ``+ - * / % **`` (with unary ``+``/``-``) are permitted. Arbitrary code and
    resource-exhausting expressions (e.g. ``9**9**9``) are rejected.

    Args:
        expression: An arithmetic string, e.g. "(2+3)*4".
    """
    try:
        tree = ast.parse(expression, mode="eval")
        value = _safe_eval(tree)
        return str(value)
    except Exception as exc:  # pragma: no cover - defensive
        return f"Error: {exc}"


@tool
def get_datetime() -> str:
    """Return the current local date and time as a string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def read_file(path: str) -> str:
    """Read a UTF-8 text file and return its first 2000 characters.

    Args:
        path: Filesystem path to the text file.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read(2000)
    except Exception as exc:
        return f"Error reading {path}: {exc}"


@tool
def web_search(query: str) -> str:
    """Offline mock web search.

    Returns simulated results so examples run without a network or API key.
    A real deployment should call a search API (e.g. Bing, Tavily, SerpAPI)
    and return the top hits here.

    Args:
        query: The search query.
    """
    safe = re.sub(r"\s+", " ", (query or "")).strip() or "unknown"
    return (
        f"Mock web results for: {safe}\n"
        f"1. https://example.com/result?q={safe.replace(' ', '+')}\n"
        f"2. https://en.wikipedia.org/wiki/{safe.replace(' ', '_')}"
    )
