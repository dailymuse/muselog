"""Middleware that flask applications use to enable datadog-compatible request logging."""

import time
from typing import Optional

from flask import g, request, Flask
from flask.ctx import has_request_context
from flask.wrappers import Response

from . import attributes, util


def _start_request_timer() -> None:
    g.start = time.time()


def _log_request(response: Optional[Response] = None) -> None:
    network_attrs = attributes.NetworkAttributes(
        extract_header=request.headers.get,
        remote_addr=request.remote_addr,
        bytes_read=request.content_length,
        bytes_written=response.calculate_content_length() if response else None
    )
    http_attrs = attributes.HttpAttributes(
        extract_header=request.headers.get,
        url=request.url,
        method=request.method,
        status_code=response.status_code if response else 500
    )
    util.log_request(request.full_path, time.time() - g.start, network_attrs, http_attrs)

    return response


def _handle_exception(_exception: Exception) -> None:
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


def register_muselog_request_hooks(app: Flask) -> None:
    """Hookup muselog to flask's request lifecycle.

    Call immediately after instantiating the Flask application object. For example,
    ```
    app = flask.Flask("rex")
    muselog.flask.register_muselog_request_hooks(app)
    ...
    ```
    """
    app.before_request(_start_request_timer)
    app.after_request(_log_request)
    app.teardown_request(_handle_exception)
