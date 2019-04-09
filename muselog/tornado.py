"""Helpers to log tornado request information."""

import logging
import sys
from typing import Optional, Type, Union
from types import TracebackType

from ddtrace import tracer

from tornado.web import HTTPError, RequestHandler

from . import attributes, util

logger = logging.getLogger(__name__)


def _get_user_id(handler: RequestHandler) -> Optional[Union[str, int]]:
    user_id = None
    user = handler.current_user
    if user:
        if hasattr(user, "id"):
            user_id = user.id
        elif isinstance(user, dict) and "id" in user:
            user_id = user["id"]
        elif isinstance(user, str) or isinstance(user, int):
            user_id = user
    return user_id


def _make_network_attributes(handler: RequestHandler) -> attributes.NetworkAttributes:
    request = handler.request
    return attributes.NetworkAttributes(
        extract_header=request.headers.get,
        remote_addr=request.remote_ip,
        bytes_read=request.headers.get("Content-Length")
    )


def _make_http_attributes(handler: RequestHandler) -> attributes.NetworkAttributes:
    request = handler.request
    return attributes.HttpAttributes(
        extract_header=request.headers.get,
        url=request.full_url(),
        method=request.method,
        status_code=handler.get_status()
    )


def log_request(handler: RequestHandler) -> None:
    """Log the request information with extra context."""
    request = handler.request
    network_attrs = _make_network_attributes(handler)
    http_attrs = _make_http_attributes(handler)
    util.log_request(
        request.uri,
        request.request_time(),
        network_attrs,
        http_attrs,
        user_id=_get_user_id(handler)
    )


class ExceptionLogger:
    """Middleware (as best as tornado supports that...) to log request-scoped exception information.

    Expected to be used in the context of a :class:`RequestHandler`.
    """

    def dd_log_exception(self, typ: type, value: BaseException, tb: TracebackType) -> None:
        """Re-implements Datadog's log_exception wrapper.

        This is necessary because ExceptionLogger does /not/ call super().log_exception,
        and thus will not invoke Datadog's log_exception wrapper.
        """
        # retrieve the current span
        current_span = tracer.current_span()

        if isinstance(value, HTTPError):
            # Tornado uses HTTPError exceptions to stop and return a status code that
            # is not a 2xx. In this case we want to check the status code to be sure that
            # only 5xx are traced as errors, while any other HTTPError exception is handled as
            # usual.
            if 500 <= value.status_code <= 599:
                current_span.set_exc_info(typ, value, tb)
        else:
            # any other uncaught exception should be reported as error
            current_span.set_exc_info(typ, value, tb)

    def log_exception(
        self,
        typ: Optional[Type[BaseException]],
        value: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        """Log request exception information in a standardized format.

        Extend this method with your own logic to ensure you do not log
        the stack for custom exceptions you consider 4xx level. In this case,
        please call `super().log_exception(...)` after executing your logic,
        unless you purposefully want to silence the exception.

        """
        network_attrs = _make_network_attributes(self)
        http_attrs = _make_http_attributes(self)
        user_id = _get_user_id(self)

        extra = {
            **network_attrs.standardize(),
            **http_attrs.standardize()
        }
        if user_id:
            extra["usr.id"] = user_id

        try:
            self.dd_log_exception(typ, value, tb)
        except Exception:
            log_method = logger.error
            exc_info = sys.exc_info()
        else:
            exc_info = sys.exc_info()
            if isinstance(value, HTTPError) and value.status_code < 500:
                # Log at warning level for 4xx errors that are uncaught.
                log_method = logger.warning
            else:
                log_method = logger.error

        log_method(
            "%s %s (%s) encountered uncaught exception %s: " + str(value),
            http_attrs.method,
            self.request.uri,
            network_attrs.client_ip or "?",
            typ.__name__,
            extra=extra,
            exc_info=exc_info
        )
