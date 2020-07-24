"""Request logging middleware for any ASGI application."""

import logging
import time
from typing import Awaitable, Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from . import attributes, util
from .logger import get_logger_with_context

LOGGER: logging.Logger = get_logger_with_context(logging.getLogger(__name__))

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


def _make_network_attributes(request: Request, response: Optional[Response] = None) -> attributes.NetworkAttributes:
    return attributes.NetworkAttributes(
        extract_header=request.headers.get,
        remote_addr=f"{request.client.host}:{request.client.port}",
        bytes_read=request.headers.get("Content-Length"),
        bytes_written=response.headers.get("Content-Length") if response else None
    )


def _make_http_attributes(request: Request, response: Optional[Response] = None) -> attributes.HttpAttributes:
    return attributes.HttpAttributes(
        extract_header=request.headers.get,
        url=str(request.url),
        method=request.method,
        status_code=response.status_code if response else 500
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log entry and exit point of request, and add request details to the global context."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        util.init_context(request.headers.get)
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception:
            network_attrs = _make_network_attributes(request)
            http_attrs = _make_http_attributes(request)
            util.log_request(request.url.path, time.time() - start_time, network_attrs, http_attrs)
            raise

        network_attrs = _make_network_attributes(request, response)
        http_attrs = _make_http_attributes(request, response)

        util.log_request(request.url.path, time.time() - start_time, network_attrs, http_attrs)

        return response
