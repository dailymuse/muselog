"""Helpers to log tornado request information."""

import logging

logger = logging.getLogger(__name__)


def _derive_network_attrs(handler, request):
    result = {
        "network.client.ip": request.remote_ip,
        # "network.client.port": ....
        # There is no (public) interface to get the client's port. Even if one
        # existed, that port could be a load balancer port, whereas the remote ip
        # is extracted from X-Forwarded-For. This would be misleading, so we do
        # not include the client port.

        # "network.destination.ip": ....
        # The destination ip and port is not useful in this context, so
        # we do not include it
    }

    # This is iffy, as it's unclear what network layer 'bytes_read' and 'bytes_written' refers to
    # Still, the info is too useful to ignore, and the error is small.
    result["network.bytes_read"] = int(request.headers.get("Content-Length") or 0)

    # Tornado does not save the response object, and muselog is not in the business
    # of providing middleware at the moment. Will need to re-architect the tornado
    # setup to work as middleware.
    # result["network.bytes_written"] = ?

    return result


def _derive_http_attrs(handler, request):
    headers = request.headers
    result = {
        "http.url": request.full_url(),
        "http.method": request.method,
        "http.status_code": handler.get_status(),
    }
    request_id = headers.get("X-Request-Id") or headers.get("X-Amzn-Trace-Id")
    if request_id:
        result["http.request_id"] = request_id
    if "Referer" in headers:
        result["http.referer"] = headers["Referer"]
    if "User-Agent" in headers:
        result["http.useragent"] = headers["User-Agent"]

    return result


def _derive_usr_attrs(handler):
    result = dict()
    user = handler.current_user
    if user:
        if hasattr(user, "id"):
            result["usr.id"] = str(user.id)
        elif isinstance(user, dict) and "id" in user:
            result["usr.id"] = str(user["id"])
        elif isinstance(user, str) or isinstance(user, int):
            result["usr.id"] = str(user)
    return result


def log_request(handler):
    """Log the request information with extra context."""
    request = handler.request
    response_status = handler.get_status()

    if response_status < 400:
        log_method = logger.info
    elif response_status < 500:
        log_method = logger.warning
    else:
        log_method = logger.error

    request_time = 1000.0 * request.request_time()
    extra = {
        "duration": int(request_time * 1000000),
        **_derive_network_attrs(handler, request),
        **_derive_http_attrs(handler, request),
        **_derive_usr_attrs(handler)
    }

    log_method(
        "%d %s %.2fms",
        response_status,
        handler._request_summary(),
        request_time,
        extra=extra
    )
