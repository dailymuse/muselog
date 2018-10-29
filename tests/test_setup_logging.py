import logging
import unittest

from unittest.mock import MagicMock

import muselog
from muselog.datadog import DataDogUdpHandler


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
        self.handler = h = DataDogUdpHandler(host="127.0.0.1", port=10518)
        self.logger = l = logging.getLogger('datadog')

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.handler.close()

    def test_datadog_handler_called(self):
         with self.assertLogs('datadog') as cm:
            self.handler.send = MagicMock(name='send')

            self.logger.warning("Datadog msg")
            self.logger.addHandler(self.handler)

            self.assertEqual(True, self.logger.hasHandlers())

            self.assertEqual(True, self.handler.send.called)
            self.assertEqual(cm.output, ['WARNING:datadog:Datadog msg'])
