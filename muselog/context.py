"""Manipulate logging context."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

#: Global context that is always applied.
_CONTEXT = ContextVar("muselog", default=dict())


def copy() -> dict:
    """Return a copy of the context-local context var for muselog."""
    return _CONTEXT.get().copy()


def get(key: str, default=None) -> Any:
    """Get a specific key from the context-local context."""
    return _CONTEXT.get().get(key, default)


def clear():
    """Clear the context-local context.

    The typical use-case for this function is to invoke it early in request-
    handling code.
    """
    ctx = _CONTEXT.get()
    ctx.clear()


def bind(**ctx):
    """Put keys and values into the context-local context.

    NOTE: Keys in the ctx parameter overwrite keys of the same name in the
    global context.
    """
    _CONTEXT.get().update(ctx)


def unbind(*keys):
    """Remove *keys* from the context-local context, if they are present."""
    ctx = _CONTEXT.get()
    for key in keys:
        ctx.pop(key, None)


class Context:
    """Scoped context management.

    This class provides a context manager that will automatically
    remove only that context which it was provided.

    It also provides a `bind` method that allows adding to the
    context, and removing those newly added items on context
    manager exit.

    Note that Context will not work as expected when used with generators.
    See https://www.python.org/dev/peps/pep-0568/ for more information.
    """

    def __init__(self, **ctx):
        """Initialize the context with the given keyword arguments."""
        self.ctx = ctx

    def __enter__(self) -> Context:  # noqa: D105
        self.bind()
        return self

    def __exit__(self, type, value, traceback):  # noqa: D105
        unbind(*list(self.ctx.keys()))

    def bind(self, **ctx) -> None:
        """Put keys and values into the context-local context."""
        if ctx:
            self.ctx.update(ctx)
        bind(**self.ctx)
