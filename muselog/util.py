"""Helper functions useful to multiple middlewares."""

import logging
import sys
from typing import Any, Callable, Optional, Union
import uuid

from . import context, logger
from .attributes import NetworkAttributes, HttpAttributes

LOGGER: logging.Logger = logger.get_logger_with_context(logging.getLogger(__name__))


def init_context(extract_header: Callable[[str], Any]) -> None:
    """Set logging context that will survive the entire request."""
    rid = extract_header("Request-Id") or extract_header("X-Request-Id") or extract_header("X-Amzn-Trace-Id")
    if rid is None:
        rid = str(uuid.uuid4())
    context.bind(request_id=rid)


def log_request(path: str,
                duration_secs: int,
                network_attrs: NetworkAttributes,
                http_attrs: HttpAttributes,
                user_id: Optional[Union[str, int]] = None):
    """Log the provided request information in a standardized format.

    :param path:            Request path.
    :param duration_secs:   Seconds spent processing the request.
    :param network_attrs:   See :class:`NetworkAttributes`
    :param http_attrs:      See :class:`HttpAttributes`
    :param user_id:         GDPR-compliant (not a name, username, or email) user identifier, if available.
    """
    status_code = http_attrs.status_code
    if status_code < 400:
        log_method = LOGGER.info
    elif status_code < 500:
        log_method = LOGGER.warning
    elif not sys.exc_info()[0]:
        log_method = LOGGER.error
    else:
        log_method = LOGGER.exception

    duration_ms = duration_secs * 1000
    extra = {
        "duration": duration_ms * 1000000,
        **network_attrs.standardize(),
        **http_attrs.standardize()
    }
    if user_id:
        extra["usr.id"] = user_id

    log_method(
        "%d %s %s (%s) %.2fms",
        status_code,
        http_attrs.method,
        path,
        network_attrs.client_ip or "?",
        duration_ms,
        extra=extra
    )
