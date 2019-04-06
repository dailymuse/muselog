import io
import logging
import time
import unittest

from freezegun import freeze_time

import flask
from flask import g
from flask.wrappers import Response

from muselog.flask import register_muselog_request_hooks


class TestCase(unittest.TestCase):

    def setUp(self):
        self.output = io.StringIO()
        self.logger = logging.getLogger("muselog.util")
        self.logger.setLevel(logging.INFO)

        self.app = flask.Flask(__name__)

        register_muselog_request_hooks(self.app)

    def tearDown(self):
        self.logger.handlers = []
        self.output.close()

    def test_happy(self):
        with self.app.test_request_context("/?someparam=5"):
            with freeze_time("2019-04-03 20:00:00"):
                g.start = time.time()

            resp = Response("Okay", status=200, headers=[("Content-Length", "4")])

            with freeze_time("2019-04-03 20:00:02"):
                with self.assertLogs("muselog.util") as cm:
                    self.app.process_response(resp)

                    # Should output a single log record
                    self.assertEqual(len(cm.records), 1)

                    # That record should have our extra attributes where available
                    record = cm.records[0].__dict__
                    self.assertEqual(record["duration"], 2000000000)
                    self.assertEqual(record["network.bytes_read"], 0)
                    self.assertEqual(record["network.bytes_written"], 4)
                    self.assertEqual(record["http.url"], "http://localhost/?someparam=5")
                    self.assertEqual(record["http.method"], "GET")
                    self.assertEqual(record["http.status_code"], 200)

    def test_exception(self):
        with self.app.test_request_context("/?someparam=5"):
            with freeze_time("2019-04-03 20:00:00"):
                g.start = time.time()

            with freeze_time("2019-04-03 20:00:02"):
                with self.assertLogs("muselog.util") as cm:
                    try:
                        raise Exception("WHO CARES")
                    except Exception as e:
                        self.app.do_teardown_request(e)

                    # Should output a single log record
                    self.assertEqual(len(cm.records), 1)

                    # That record should have our extra attributes where available
                    record = cm.records[0].__dict__
                    self.assertEqual(record["duration"], 2000000000)
                    self.assertEqual(record["network.bytes_read"], 0)
                    # We have no idea about the bytes written because we do not have access to response
                    # when an unhandled exception occurs. We should not set '0' as that is misleading
                    self.assertNotIn("network_bytes_written", record)
                    self.assertEqual(record["http.url"], "http://localhost/?someparam=5")
                    self.assertEqual(record["http.method"], "GET")
                    self.assertEqual(record["http.status_code"], 500)
