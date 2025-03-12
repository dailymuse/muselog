"""Custom logging facilities to simplify the process of passing additional data to loggers."""

import logging
import os
import sys
from types import TracebackType
from typing import Callable, Mapping, Optional, Type, Union

DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"

LOGGER = logging.getLogger(__name__)


def default_exc_handler(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType
) -> None:
    """Log exceptions with context provided by muselog."""
    if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return None

    import muselog.logger
    logger = muselog.logger.get_logger_with_context(LOGGER)
    logger.critical(
        "Uncaught exception.",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    return None


def setup_logging(
    root_log_level: Optional[str] = None,
    module_log_levels: Optional[Mapping[str, Union[str, int]]] = None,
    add_console_handler: bool = True,
    console_handler_format: Optional[str] = None,
    exception_handler: Optional[Callable[[Type[BaseException], BaseException, TracebackType], None]] = default_exc_handler
):
    """Configure and install the log handlers for each application's namespace.

    :param root_log_level: The log level all loggers use by default. (Default: `"WARNING"`)
    :param module_log_levels: A mapping of module names to their desired log levels.
    :param add_console_handler: If `True`, enable logging to stdout. (Default: `True`).
    :param console_handler_format: Specifies the format of stdout logs. (Default: DEFAULT_LOG_FORMAT).
    :param exception_handler: Specifies the exception handler to use after setting up muselog.
        If `None`, do not install an exception handler.
        (Default: default_exc_handler)
    """
    if root_log_level is None:
        root_log_level = "WARNING"

    root_logger = logging.getLogger()
    root_logger.setLevel(root_log_level)

    if module_log_levels:
        for module_name, log_level in module_log_levels.items():
            logging.getLogger(module_name).setLevel(log_level)

    if add_console_handler:
        trace_enabled = (
            os.environ.get("ENABLE_DATADOG_JSON_FORMATTER", "false").lower() == "true"
            and os.environ.get("OTEL_SDK_DISABLED", "false").lower() != "true"
        )
        if trace_enabled:
            from muselog.datadog import DatadogJSONFormatter
            formatter = DatadogJSONFormatter(trace_enabled=trace_enabled)
        else:
            formatter = logging.Formatter(fmt=console_handler_format or DEFAULT_LOG_FORMAT)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        if root_logger.handlers:
            # Python's root_logger by default adds a StreamHandler if none is specified.
            # If this is present, we want it tracked and taken out later.
            # We do not to be sent to datadog (remove double entry as
            # it doesn't have the JSON formatter for easy interpretation on Datadog)
            root_logger.removeHandler(root_logger.handlers[0])
        root_logger.addHandler(console_handler)

    if exception_handler is not None:
        sys.excepthook = exception_handler
