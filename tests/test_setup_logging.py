import logging
import unittest

import muselog

from .support import ClearContext


class SetupLoggingTestCase(ClearContext, unittest.TestCase):

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
