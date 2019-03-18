import logging
import unittest
from unittest.mock import MagicMock, Mock, patch

from muselog import DatadogJSONFormatter

class InjectTraceValuesTestCase(unittest.TestCase):
    """
    Tests code related to injecting logs with a trace and span id.
    """

    def test_inject_trace_values_present(self):
        msg = "this is a test message"
        original_record = {'msg': msg}
        dfcls = DatadogJSONFormatter()
        modified_record = dfcls.inject_trace_values(original_record)
        self.assertDictEqual(modified_record, {'msg': msg, 'dd.trace_id': 0, 'dd.span_id': 0})

    def test_inject_trace_values_not_present(self):
        """
        If 'inject_trace_values' is not able to find the 'ddtrace' package we
        don't want to attempt an import of 'ddtrace' and cause an error.
        """
        msg = "this is a test message"
        original_record = {'msg': msg}
        dfcls = DatadogJSONFormatter()

        # Patch the 'find_spec' call to simulate the ddtrace package not existing
        with patch('importlib.util.find_spec') as mock:
            mock.return_value = None
            modified_record = dfcls.inject_trace_values(original_record)

        self.assertDictEqual(modified_record, original_record)
