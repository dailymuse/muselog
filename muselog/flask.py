"""Middleware that flask applications use to enable datadog-compatible request logging."""

import logging
import sys
import time

from flask import g, request
from flask.ctx import has_request_context

from werkzeug.wrappers import Request, Response

logger = logging.getLogger(__name__)


def _derive_network_attrs(response=None):
    result = dict()
    if request.remote_addr:
        result["network.client.ip"] = request.remote_addr

    # This is iffy, as it's unclear what network layer 'bytes_read' and 'bytes_written' refers to
    # Still, the info is too useful to ignore, and the error is small.
    result["network.bytes_read"] = int(request.content_length or 0)
    if response:
        result["network.bytes_written"] = response.calculate_content_length() or 0

    return result


def _derive_http_attrs(response=None):
    headers = request.headers
    result = {
        "http.url": request.url,
        "http.method": request.method,
        "http.status_code": response.status_code if response else 500,
    }
    request_id = headers.get("X-Request-Id") or headers.get("X-Amzn-Trace-Id")
    if request_id:
        result["http.request_id"] = request_id
    if request.referrer:
        result["http.referer"] = request.referrer
    if request.user_agent:
        result["http.useragent"] = request.user_agent

    return result


def _log_request(response=None):
    response_status = response.status_code if response else 500

    if response_status < 400:
        log_method = logger.info
    elif response_status < 500:
        log_method = logger.warning
    elif not sys.exc_info()[0]:
        log_method = logger.error
    else:
        log_method = logger.exception

    request_time = 1000.0 * (time.time() - g.start)
    extra = {
        "duration": int(request_time * 1000000),
        **_derive_network_attrs(response),
        **_derive_http_attrs(response)
    }

    log_method("%d %s %s (%s) %.2fms",
        response_status,
        request.method,
        request.full_path,
        request.remote_addr or "?",
        request_time,
        extra=extra
    )

def _handle_exception(_exception):
    # Flask's documentation is confusing, and this presents a good example of why stackoverflow
    # should *not* be trusted. Users on stackoverflow claim that request context is not available
    # during teardown_request, but this is not true. teardown_request is called immediately before
    # the request context stack is popped, not after. Thus, we have access to the request and
    # can log information about it. To be absolutely safe, I call has_request_context. Really
    # is not necessary unless Flask makes a breaking change to their framework.

    # Sanity check. Should not happen, but I have seen multiple apps include this check, which
    # suggests that maybe it could happen in some crazy circumstance.
    if not _exception:
        return

    # Another sanity check. Should never happen.
    if not has_request_context():
        return

    # Note that we do not have access to the response object (it may not even exist),
    # so we cannot record everything. That is okay, as for unhandled exceptions all we want to know
    # is what was called.

    _log_request()


def register_muselog_request_hooks(app):
    """Hookup muselog to flask's request lifecycle.

    Call immediately after instantiating the Flask application object. For example,
    ```
    app = flask.Flask("rex")
    muselog.flask.register_muselog_request_hooks(app)
    ...
    ```
    """
    app.after_request(_log_request)
    app.teardown_request(_handle_exception)
