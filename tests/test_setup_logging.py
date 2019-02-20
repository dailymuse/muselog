import logging
import unittest

from unittest.mock import MagicMock, Mock

import muselog
from muselog.datadog import DataDogUdpHandler
from muselog.django import MuseDjangoRequestLoggingMiddleware


class SetupLoggingTestCase(unittest.TestCase):

    def test_defaults(self):
        logging.getLogger().setLevel(logging.INFO)
        self.assertEqual(logging.getLogger().getEffectiveLevel(), logging.INFO)

        muselog.setup_logging()

        self.assertEqual(logging.getLogger().getEffectiveLevel(), logging.WARNING)

    def test_custom_log_level(self):
        muselog.setup_logging(root_log_level=logging.CRITICAL)
        self.assertEqual(logging.getLogger().getEffectiveLevel(), logging.CRITICAL)

    def test_module_log_levels(self):
        muselog.setup_logging(module_log_levels={"muselog": logging.DEBUG,
                                                 "testing": logging.ERROR,
                                                 "testing.child": logging.CRITICAL,
                                                 "string": "INFO"})
        self.assertEqual(logging.getLogger().getEffectiveLevel(), logging.WARNING)
        self.assertEqual(logging.getLogger("muselog").getEffectiveLevel(), logging.DEBUG)
        self.assertEqual(logging.getLogger("testing").getEffectiveLevel(), logging.ERROR)
        self.assertEqual(logging.getLogger("testing.child").getEffectiveLevel(), logging.CRITICAL)
        self.assertEqual(logging.getLogger("string").getEffectiveLevel(), logging.INFO)


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


class MuseDjangoRequestLoggingMiddlewareTestCase(unittest.TestCase):

    def setUp(self):
        self.logger = Mock()
        self.response = Mock
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
        return request

    def test_process_request(self):
        self.middleware.process_request(self.request)
        self.assertIsInstance(self.request.started_at, float)

    def test_process_response_when_success(self):
        self.logger.info = Mock()
        self.response.status_code = 200
        self.request.started_at = 0
        self.middleware.process_response(self.request, self.response)
        self.logger.info.assert_called_once()

    def test_process_response_when_client_error(self):
        self.logger.warning = Mock()
        self.response.status_code = 404
        self.request.started_at = 0
        self.middleware.process_response(self.request, self.response)
        self.logger.warning.assert_called_once()

    def test_process_response_when_server_error(self):
        self.logger.error = Mock()
        self.response.status_code = 500
        self.request.started_at = 0
        self.middleware.process_response(self.request, self.response)
        self.logger.error.assert_called_once()
