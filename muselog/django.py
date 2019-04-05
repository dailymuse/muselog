"""Middleware to log django request information."""

import logging
import sys
import time

logger = logging.getLogger(__name__)


class MuseDjangoRequestLoggingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logger

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        self.process_response(request, response)
        return response

    def process_request(self, request):
        request.started_at = time.time()

    def process_response(self, request, response):
        response_status = response.status_code
        request_time = 1000 * (time.time() - request.started_at)
        request_ip = self.get_client_ip(request)
        request_summary = f"{request.method} {request.get_full_path()} ({request_ip})"

        if response_status < 400:
            log_method = self.logger.info
        elif response_status < 500:
            log_method = self.logger.warning
        elif not sys.exc_info()[0]:
            log_method = self.logger.error
        else:
            log_method = self.logger.exception

        extra = {
            "duration": int(request_time * 1000000),
            **self._derive_network_attrs(request, response),
            **self._derive_http_attrs(request, response),
            **self._derive_usr_attrs(request)
        }

        log_method(
            "%d %s %.2fms",
            response_status,
            request_summary,
            request_time,
            extra=extra
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def set_logger(self, logger):
        self.logger = logger

    def _derive_network_attrs(self, request, response):
        result = {
            "network.client.ip": self.get_client_ip(request)
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
        result["network.bytes_read"] = int(request.META.get("CONTENT_LENGTH") or 0)
        result["network.bytes_written"] = response.tell()

        return result

    def _derive_http_attrs(self, request, response):
        headers = request.META
        result = {
            "http.url": request.get_raw_uri(),
            "http.method": request.method,
            "http.status_code": response.status_code,
        }
        request_id = headers.get("HTTP_X_REQUEST_ID") or headers.get("HTTP_X_AMZN_TRACE_ID")
        if request_id:
            result["http.request_id"] = request_id
        if "HTTP_REFERER" in headers:
            result["http.referer"] = headers["HTTP_REFERER"]
        if "HTTP_USER_AGENT" in headers:
            result["http.useragent"] = headers["HTTP_USER_AGENT"]

        return result

    def _derive_usr_attrs(self, request):
        result = dict()
        if not hasattr(request, "user"):
            return result
        user = request.user
        if user.is_authenticated:
            result["usr.id"] = user.id

        return result
