"""Built-in tools.

Importing this package registers the built-in tools (``calculator``,
``get_datetime``, ``read_file``, ``web_search``) via the ``@tool`` decorator.
"""

from . import builtin  # noqa: F401  (triggers @tool registration)

__all__ = ["builtin"]
