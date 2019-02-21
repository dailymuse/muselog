import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MuseDjangoRequestLoggingMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logger

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        self.process_response(request, response)
        return response

    def process_request(self, request):
        request.started_at = datetime.utcnow().timestamp()

    def process_response(self, request, response):
        response_status = response.status_code
        request_time = 1000.0 * datetime.utcnow().timestamp() - request.started_at
        request_ip = self.get_client_ip(request)
        request_summary = f"{request.method} {request.get_full_path()} ({request_ip})"

        self.logger.debug(
            "%d %s %.2fms",
            response_status,
            request_summary,
            request_time,
            extra={
                "request_method": request.method,
                "request_path": request.path,
                "request_query": request.GET.urlencode(),
                "response_status": response_status,
                "request_duration": request_time,
                "request_remote_ip": request_ip,
                "request_summary": request_summary
            }
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
