"""Tests for the @tool decorator, schema inference, and the tool registry."""

import agentforge  # noqa: F401  (registers built-in tools)

from agentforge.core.tool import get_tool, list_tools


def test_calculator_computes():
    calc = get_tool("calculator")
    assert calc is not None
    assert calc.run(expression="2+3*4") == "14"
    # calling the Tool instance directly is equivalent to .run(...)
    assert calc(expression="(2+3)*4") == "20"


def test_calculator_rejects_unsafe_input():
    calc = get_tool("calculator")
    out = calc.run(expression="__import__('os').system('echo hi')")
    assert out.startswith("Error")


def test_get_datetime_returns_string():
    dt = get_tool("get_datetime")
    assert isinstance(dt.run(), str) and len(dt.run()) > 0


def test_schema_inferred_from_signature():
    calc = get_tool("calculator")
    sch = calc.schema()
    assert sch["type"] == "function"
    assert sch["function"]["name"] == "calculator"
    props = sch["function"]["parameters"]["properties"]
    assert "expression" in props
    assert props["expression"]["type"] == "string"
    assert "expression" in sch["function"]["parameters"]["required"]


def test_autoregister_builtins():
    names = [t.name for t in list_tools()]
    for n in ("calculator", "get_datetime", "read_file", "web_search"):
        assert n in names
