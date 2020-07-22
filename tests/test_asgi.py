import unittest

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient


from muselog import asgi

from .support import ClearContext


class ASGIRequestLoggingMiddlewareTestCase(ClearContext, unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.app = Starlette()
        self.app.add_middleware(asgi.RequestLoggingMiddleware)
        self.client = TestClient(self.app)

    def test_happy(self) -> None:
        """Test that the middleware emits populated log record."""

        @self.app.route("/")
        def homepage(request):
            return PlainTextResponse("x" * 4000, status_code=202)

        with self.assertLogs("muselog.util") as cm:
            self.client.get("/?someparam=10")

            # Should output a single log record
            self.assertEqual(len(cm.records), 1)

            # That record should have our extra attributes where available
            record = cm.records[0].__dict__
            self.assertTrue("duration" in record)
            self.assertTrue("http.request_id" in record)
            self.assertEqual(record["network.bytes_read"], 0)
            self.assertEqual(record["network.bytes_written"], 4000)
            self.assertEqual(record["http.url"], "http://testserver/?someparam=10")
            self.assertEqual(record["http.method"], "GET")
            self.assertEqual(record["http.status_code"], 202)

    def test_exception(self) -> None:
        """Test that the middleware logs exceptions."""

        @self.app.route("/")
        def rekt(request):
            raise Exception("Oh no.")

        with self.assertLogs("muselog.util", "ERROR") as cm:
            with self.assertRaises(Exception):
                self.client.get("/")

            # Should output a single log record
            self.assertEqual(len(cm.records), 1)

            # That record should have our extra attributes where available
            record = cm.records[0].__dict__
            self.assertTrue("duration" in record)
            self.assertTrue("http.request_id" in record)
            self.assertEqual(record["network.bytes_read"], 0)
            self.assertEqual(record["network.bytes_written"], 0)
            self.assertEqual(record["http.url"], "http://testserver/")
            self.assertEqual(record["http.method"], "GET")
            self.assertEqual(record["http.status_code"], 500)
