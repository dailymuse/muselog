"""Helpers to log tornado request information."""

from typing import Optional, Union

from tornado.web import RequestHandler

from . import attributes, util


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


def log_request(handler: RequestHandler) -> None:
    """Log the request information with extra context."""
    request = handler.request
    network_attrs = attributes.NetworkAttributes(
        extract_header=request.headers.get,
        remote_addr=request.remote_ip,
        bytes_read=request.headers.get("Content-Length")
    )
    http_attrs = attributes.HttpAttributes(
        extract_header=request.headers.get,
        url=request.full_url(),
        method=request.method,
        status_code=handler.get_status()
    )
    util.log_request(
        request.uri,
        request.request_time(),
        network_attrs,
        http_attrs,
        user_id=_get_user_id(handler)
    )
