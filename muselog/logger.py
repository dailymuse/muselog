"""Logging Utilities.

This class provides logging utilitis that are meant to be compatible with structlog,
a Python library for contextual logging. At the moment, we cannot switch over to
structlog immediately, as it is unclear how it will impact existing muselog integrations.
"""

import logging
from typing import Any, Dict, Mapping, Tuple

from . import context


#: Keyword argumnts to log emission methods that we should not include in context.
RESERVED_KWARGS: tuple = ('exc_info', 'stack_info', 'stacklevel', 'extra')


class LoggerAdapter(logging.LoggerAdapter):
    """Adapter that attaches context to log messages automatically."""

    def process(self, msg: str, kwargs: Mapping[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Process log message."""
        ctx = context.copy()

        extra = self._copy_dict_none_to_empty(self.extra)
        passed_extra = self._copy_dict_none_to_empty(kwargs.get("extra"))

        # Merge contexts, removing them from their respective extras so that we can merge extras.
        extra_ctx = self._copy_dict_none_to_empty(extra.pop("ctx", None))
        passed_extra_ctx = self._copy_dict_none_to_empty(passed_extra.pop("ctx", None))
        extra_ctx.update(passed_extra_ctx)
        ctx.update(extra_ctx)

        # Merge extras
        extra.update(passed_extra)

        # Place keyword args (other than the four reserved kwargs) into extra["ctx"]
        for k, v in kwargs.items():
            if k in RESERVED_KWARGS:
                continue
            ctx[k] = v

        # Remove kwargs that we already have in the context (make sure not to remove reserved kwargs)
        for k, _ in ctx.items():
            if k in kwargs and k not in RESERVED_KWARGS:
                del kwargs[k]

        # Add context
        if ctx:
            extra["ctx"] = ctx

        # If extra has contents, add it back to kwargs
        if extra:
            kwargs["extra"] = extra

        return msg, kwargs

    def bind(self, **new_ctx) -> "LoggerAdapter":
        """Create a copy of the logger with provided context merged into existing context."""
        extra = self._copy_dict_none_to_empty(self.extra)
        ctx = self._copy_dict_none_to_empty(extra.get("ctx"))
        ctx.update(new_ctx)
        extra["ctx"] = ctx
        return LoggerAdapter(self.logger, extra)

    def unbind(self, *keys) -> "LoggerAdapter":
        """Create a copy of the logger with provided context keys removed from existing context."""
        extra = self._copy_dict_none_to_empty(self.extra)
        ctx = self._copy_dict_none_to_empty(extra.get("ctx"))
        extra["ctx"] = {k: v for k, v in ctx.items() if k not in keys}
        return LoggerAdapter(self.logger, extra)

    def new(self, **ctx) -> "LoggerAdapter":
        """Return a new logger with only the specified context included."""
        extra = self._copy_dict_none_to_empty(self.extra)
        if "ctx" in extra:
            del extra["ctx"]
        return LoggerAdapter(self.logger, extra).bind(**ctx)

    @staticmethod
    def _copy_dict_none_to_empty(orig: Mapping[str, Any]) -> Dict[str, Any]:
        return dict(orig) if orig is not None else dict()


def get_logger_with_context(logger: logging.Logger, **ctx) -> LoggerAdapter:
    """Get a logger that always adds `ctx` to its log records."""
    return LoggerAdapter(logger, dict(ctx=ctx))
