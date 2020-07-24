"""Test the context-enabled log adapter."""

import logging
import unittest

from muselog import context
from muselog.logger import get_logger_with_context

from .support import ClearContext

LOGGER: logging.Logger = logging.getLogger(__name__)


class LoggerTestCase(ClearContext, unittest.TestCase):
    """Tests for the contextual logging functionality."""

    def test_empty_ctx(self) -> None:
        """Test that logging without any context does not populate the 'ctx' object."""
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER)
            logger.info("Test")
            self.assertEqual(len(log.records), 1)
            self.assertFalse(hasattr(log.records[0], "ctx"))

    def test_default_context(self) -> None:
        """Test that logging with a default context provides that context in the 'ctx' object."""
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER, testing="Sandwich")
            logger.info("Test")
            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].ctx, dict(testing="Sandwich"))

    def test_provided_context(self) -> None:
        """Test that logging with a provided context results in that provided context in the 'ctx' object."""
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER)
            logger.info("Test", testing="Hello")
            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].ctx, dict(testing="Hello"))

    def test_merged_context(self) -> None:
        """Test that logging with both a default and provided context merges the contexts."""
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER, testing="Sandwich")
            # Test no conflict
            logger.info("Test", testing1="Hello")

            # Test conflict (testing appears in custom and default context)
            logger.info("Test2", testing="Not Sandwich", testing2="Test")

            self.assertEqual(len(log.records), 2)
            self.assertEqual(log.records[0].ctx, dict(testing="Sandwich", testing1="Hello"))
            self.assertEqual(log.records[1].ctx, dict(testing="Not Sandwich", testing2="Test"))

    def test_ignore_reserved_kwargs(self) -> None:
        """Test that the logger does not include reserved kwargs in the context, and should not remove these keywords from the record."""
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER)
            logger.info("Test", stack_info=True, testing="Testing")
            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].ctx, dict(testing="Testing"))

    def test_merge_extra(self) -> None:
        """Test that the logger extracts context from 'extra' arg and merges it into the primary context."""
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER, testing1="Testing1")
            logger.info("Test", testing="Testing", extra=dict(ctx=dict(testing2="Testing2"), other=5))
            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].other, 5)
            self.assertEqual(log.records[0].ctx, dict(testing="Testing", testing1="Testing1", testing2="Testing2"))

    def test_bind(self) -> None:
        """Test that bind adds new context."""
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER, testing1="Testing1")
            logger = logger.bind(testing2="Testing2")
            logger.info("Test2")
            logger = logger.bind(testing3="Testing3")
            logger.info("Test3")
            self.assertEqual(len(log.records), 2)
            self.assertEqual(log.records[0].ctx, dict(testing1="Testing1", testing2="Testing2"))
            self.assertEqual(log.records[1].ctx, dict(testing1="Testing1", testing2="Testing2", testing3="Testing3"))

    def test_unbind(self) -> None:
        """Test that unbind removes specified context."""
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER, testing1="Testing1")
            logger = logger.bind(testing2="Testing2")
            logger.info("Test2")
            logger = logger.unbind("testing2", "testing3")
            logger.info("Test3")
            self.assertEqual(len(log.records), 2)
            self.assertEqual(log.records[0].ctx, dict(testing1="Testing1", testing2="Testing2"))
            self.assertEqual(log.records[1].ctx, dict(testing1="Testing1"))

    def test_new(self) -> None:
        """Test that new replaces original context with specified context."""
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER, testing1="Testing1")
            logger = logger.new(testing2="Testing2")
            logger.info("Test2")
            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].ctx, dict(testing2="Testing2"))

    def test_bind_global(self) -> None:
        """Test that global context is always added."""
        context.bind(testing="Testing", testing1="Override")
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER, testing2="Testing2")
            logger.info("First Test")
            logger = logger.bind(testing1="Testing1")
            logger.info("Second Test")
            self.assertEqual(len(log.records), 2)
            self.assertEqual(log.records[0].ctx, dict(testing="Testing", testing1="Override", testing2="Testing2"))
            self.assertEqual(log.records[1].ctx, dict(testing="Testing", testing1="Testing1", testing2="Testing2"))

    def test_unbind_global(self) -> None:
        """Test that global context is removed."""
        context.bind(testing="Testing", testing1="Remove")
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER)
            logger.info("First Test")
            context.unbind("testing1")
            logger.info("Second Test")
            self.assertEqual(len(log.records), 2)
            self.assertEqual(log.records[0].ctx, dict(testing="Testing", testing1="Remove"))
            self.assertEqual(log.records[1].ctx, dict(testing="Testing"))

    def test_clear_global(self) -> None:
        """Test that global context is cleared."""
        context.bind(testing1="Remove1", testing2="Remove2")
        with self.assertLogs(__name__) as log:
            logger = get_logger_with_context(LOGGER, testing3="Stay")
            logger.info("First Test")
            context.clear()
            logger.info("Second Test")
            self.assertEqual(len(log.records), 2)
            self.assertEqual(log.records[0].ctx, dict(testing1="Remove1", testing2="Remove2", testing3="Stay"))
            self.assertEqual(log.records[1].ctx, dict(testing3="Stay"))
