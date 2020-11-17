"""Manipulate logging context."""

from contextvars import ContextVar
from contextlib import contextmanager
from typing import Any, Iterator

#: Context that we can access anywhere in the thread
_CONTEXT: ContextVar = ContextVar("muselog", default=dict())


def copy() -> dict:
    """Return a copy of the context var for muselog."""
    return _CONTEXT.get().copy()


def get(key: str, default=None) -> Any:
    """Get a specific key from the context."""
    return _CONTEXT.get().get(key, default)


def clear() -> None:
    """Clear the context-local context.

    The typical use-case for this function is to invoke it early in request-
    handling code.
    """
    ctx = _CONTEXT.get()
    ctx.clear()


def bind(**ctx) -> None:
    """Put keys and values into the context-local context."""
    _CONTEXT.get().update(ctx)


def unbind(*keys) -> None:
    """Remove *keys* from the context-local context if they are present."""
    ctx = _CONTEXT.get()
    for key in keys:
        ctx.pop(key, None)


@contextmanager
def Context(**ctx) -> Iterator:
    """Bind additional context to muselog global context."""
    bind(**ctx)
    try:
        yield
    finally:
        unbind(*list(ctx.keys()))
