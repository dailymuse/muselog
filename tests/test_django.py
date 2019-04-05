import unittest
from unittest.mock import Mock

from muselog.django import MuseDjangoRequestLoggingMiddleware


class MuseDjangoRequestLoggingMiddlewareTestCase(unittest.TestCase):

    def setUp(self):
        self.logger = Mock()
        self.response = Mock()
        self.response.tell.return_value = 0
        self.request = self.get_mock_request()

        def get_response():
            self.response

        self.middleware = MuseDjangoRequestLoggingMiddleware(get_response)
        self.middleware.set_logger(self.logger)

    def get_mock_request(self):
        request = Mock()
        request.started_at = 0
        request.META = {
            "HTTP_X_FORWARDED_FOR": "ip1, ip2",
            "REMOTE_ADDR": "ip3"
        }
        request.headers = request.META
        return request

    def test_process_request(self):
        self.middleware.process_request(self.request)
        self.assertIsInstance(self.request.started_at, float)

    def test_process_response(self):
        self.logger.info = Mock()
        self.response.status_code = 200
        self.request.started_at = 0
        self.middleware.process_response(self.request, self.response)
        self.logger.info.assert_called_once()
