import time
import unittest
from unittest.mock import Mock

from freezegun import freeze_time

from muselog.django import MuseDjangoRequestLoggingMiddleware

from .support import ClearContext


class MuseDjangoRequestLoggingMiddlewareTestCase(ClearContext, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.response = Mock()
        self.response.tell.return_value = 4
        self.request = self.get_mock_request()

        def get_response():
            self.response

        self.middleware = MuseDjangoRequestLoggingMiddleware(get_response)

    def get_mock_request(self):
        request = Mock()
        request.started_at = 0
        request.META = {
            "HTTP_X_FORWARDED_FOR": "ip1, ip2",
            "REMOTE_ADDR": "ip3"
        }
        request.method = "GET"
        request.get_raw_uri.return_value = "http://localhost/?someparam=5"
        return request

    def test_process_request(self):
        with freeze_time("2019-04-05 20:00:02"):
            self.middleware.process_request(self.request)
            self.assertEqual(self.request.started_at, time.time())

    def test_process_response(self):
        with freeze_time("2019-04-05 20:00:02"):
            self.request.started_at = time.time()

        self.response.status_code = 200

        with self.assertLogs("muselog.util") as cm:
            with freeze_time("2019-04-05 20:00:03"):
                self.middleware.process_response(self.request, self.response)

                # Should output a single log record
                self.assertEqual(len(cm.records), 1)

                # That record should have our extra attributes where available
                record = cm.records[0].__dict__
                self.assertEqual(record["duration"], 1000000000)
                self.assertEqual(record["network.bytes_read"], 0)
                self.assertEqual(record["network.bytes_written"], 4)
                self.assertEqual(record["http.url"], "http://localhost/?someparam=5")
                self.assertEqual(record["http.method"], "GET")
                self.assertEqual(record["http.status_code"], 200)
