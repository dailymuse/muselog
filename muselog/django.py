"""Helpers to log requests processed within the Django web framework."""

import time
from typing import Any, Callable, Mapping, Optional, Union

from django.http import HttpRequest, HttpResponse

from . import attributes, context, util


def _extract_header(meta: Mapping[str, Any]) -> Callable[[str], Any]:
    """For use by the attribute classes, which require a framework-agnostic header function."""
    def _get(header: str, default=None) -> Optional[Any]:
        header = header.replace('-', '_').upper()
        if header not in ("CONTENT_TYPE", "CONTENT_LENGTH"):
            header = f"HTTP_{header}"
        return meta.get(header, default)
    return _get


class MuseDjangoRequestLoggingMiddleware:
    """Middleware to log django request information.

    Add to your MIDDLEWARE list in your Django settings file, like so:
    ```
    MIDDLEWARE = [
        ...
        "muselog.django.MuseDjangoRequestLoggingMiddleware",
        ...
    ]
    ```
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Configure the middleware.

        :param get_response: Callable provided by Django to get response from next middleware or view.

        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Execute middleware logic and return the response.

        This middleware modifies the request in order to calculate its duration.
        It does not modify the response.

        """
        self.process_request(request)
        response = self.get_response(request)
        self.process_response(request, response)
        return response

    def process_request(self, request: HttpRequest) -> None:
        """Add timing information to the request to calculate its duration."""
        request.started_at = time.time()
        meta = request.META
        extract_header = _extract_header(meta)
        util.init_context(extract_header)

    def process_response(self, request: HttpRequest, response: HttpResponse) -> None:
        """Extract and log timing, network, http, and user attributes."""
        meta = request.META
        extract_header = _extract_header(meta)
        network_attrs = attributes.NetworkAttributes(
            extract_header=extract_header,
            remote_addr=meta.get("REMOTE_ADDR"),
            bytes_read=meta.get("CONTENT_LENGTH"),
            bytes_written=self._get_bytes_written(response)
        )
        http_attrs = attributes.HttpAttributes(
            extract_header=extract_header,
            url=request.get_raw_uri(),
            method=request.method,
            status_code=response.status_code
        )
        util.log_request(
            request.get_full_path(),
            time.time() - request.started_at,
            network_attrs,
            http_attrs,
            user_id=self._get_user_id(request)
        )
        context.unbind("request_id")

    @staticmethod
    def _get_user_id(request: HttpRequest) -> Optional[Union[str, int]]:
        if not hasattr(request, "user"):
            return None
        user = request.user
        if user.is_authenticated:
            return user.id
        else:
            return None

    @staticmethod
    def _get_bytes_written(response: HttpResponse) -> int:
        """
        Attempts to get the bytes written, accounting for `StreamingHttpResponse`
        which will not be able to tell it's position.
        """
        try:
            return response.tell()
        except OSError:
            return 0
