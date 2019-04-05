import io
import json
import logging
import time
import unittest
from unittest.mock import MagicMock

from freezegun import freeze_time

from muselog.datadog import DataDogUdpHandler, DatadogJSONFormatter


class DataDogTestLoggingTestCase(unittest.TestCase):

    def setUp(self):
        self.handler = DataDogUdpHandler(host="127.0.0.1", port=10518)
        self.logger = logging.getLogger('datadog')

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.handler.close()

    def test_datadog_handler_called(self):
         with self.assertLogs('datadog') as cm:
            self.handler.send = MagicMock(name='send')

            self.logger.addHandler(self.handler)
            self.logger.warning("Datadog msg")

            self.assertEqual(True, self.logger.hasHandlers())

            self.assertEqual(True, self.handler.send.called)
            self.assertEqual(cm.output, ['WARNING:datadog:Datadog msg'])


class InjectTraceValuesTestCase(unittest.TestCase):
    """Tests code related to injecting logs with a trace and span id."""

    def setUp(self):
        self.output = io.StringIO()
        self.logger = logging.getLogger("test")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        self.handler = logging.StreamHandler(self.output)
        self.logger.addHandler(self.handler)

        self.formatter = DatadogJSONFormatter()
        self.handler.setFormatter(self.formatter)

    def tearDown(self):
        self.logger.handlers = []
        self.output.close()

    @freeze_time("2019-04-03 20:00:00")
    def test_dd_attributes_present(self):

        self.logger.info("this is a test message")
        output = json.loads(self.output.getvalue())

        self.assertEqual(output["message"], "this is a test message")
        self.assertEqual(output["timestamp"], int(time.time() * 1000))
        self.assertEqual(output["severity"], "INFO")
        self.assertEqual(output["logger.name"], "test")
        self.assertEqual(output["logger.method_name"], "test_dd_attributes_present")
        self.assertEqual(output["logger.thread_name"], "MainThread")

    def test_dd_exception_attributes(self):
        try:
            raise Exception("All is well.")
        except Exception:
            self.logger.exception("OH SHIT THERE'S A HUGE EXCEPTION IN HERE")
        output = json.loads(self.output.getvalue())

        # Exception log level should translate to 'ERROR' severity
        self.assertEqual(output["severity"], "ERROR")

        # Should populate 'error' fields
        self.assertEqual(output["error.kind"], "Exception")
        self.assertEqual(output["error.message"], "All is well.")
        # Just make sure the stack is populated. Not going to do an exact
        # comparison.
        self.assertIn("error.stack", output)

    def test_context_attributes(self):
        self.logger.info("Here's some context for u", extra={"context": "test=f"})
        output = json.loads(self.output.getvalue())

        self.assertEqual(output["ctx.test"], "f")

    def test_bad_context_attributes(self):
        # TODO: Fix the bad context values bug so we can get this test outta here.

        self.logger.info("Here's some context for u", extra={"context": "test=f, ok"})
        output = json.loads(self.output.getvalue())

        # Let's do a sanity test to see that an error raised during context extraction
        # gets recorded into the 'error' fields

        # log level should NOT be altered
        self.assertEqual(output["severity"], "INFO")

        # Should populate 'error' fields
        self.assertEqual(output["error.kind"], "ValueError")
        self.assertEqual(output["error.message"], "not enough values to unpack (expected 2, got 1)")

    def test_bad_context_attributes_prior_exc(self):
        # TODO: Fix the bad context values bug so we can get this test outta here.

        try:
            raise Exception("All is well.")
        except Exception:
            self.logger.exception("Here's some context for u", extra={"context": "test=f, ok"})
        output = json.loads(self.output.getvalue())

        # Let's do a sanity test to see that an error raised during context extraction
        # gets recorded into the 'error' fields

        # log level should NOT be altered
        self.assertEqual(output["severity"], "ERROR")

        # Should populate 'error' fields with the /new/ error info
        self.assertEqual(output["error.kind"], "ValueError")
        self.assertEqual(output["error.message"], "not enough values to unpack (expected 2, got 1)")

        # The traceback should have the entire exception chain.
        # We'll just do a simple containment check to see.
        self.assertIn("Exception: All is well.", output["error.stack"])

    def test_trace_enabled_true(self):
        self.formatter.trace_enabled = True

        self.logger.info("this is a test message")
        output = json.loads(self.output.getvalue())

        self.assertEqual(output["dd.trace_id"], 0)
        self.assertEqual(output["dd.span_id"], 0)

    def test_trace_enabled_false(self):
        self.formatter.trace_enabled = False

        self.logger.info("this is a test message")
        output = json.loads(self.output.getvalue())

        self.assertNotIn("dd.trace_id", output)
        self.assertNotIn("dd.span_id", output)
