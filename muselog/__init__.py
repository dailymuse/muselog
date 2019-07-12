"""Custom logging facilities to simplify the process of passing additional data to loggers."""

import logging
import os
from typing import Mapping, Optional, Union

from .datadog import DataDogUdpHandler, DatadogJSONFormatter

#: Format to use
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"


def setup_logging(root_log_level: Optional[str] = None,
                  module_log_levels: Optional[Mapping[str, Union[str, int]]] = None,
                  add_console_handler: bool = True,
                  console_handler_format: Optional[str] = None):
    """
    Setup log handlers for each application's namespace

    :param root_log_level: The log level all loggers use by default. (Default: `"WARNING"`)
    :param module_log_levels: A mapping of module names to their desired log levels.
    :param add_console_handler: If `True`, enable logging to stdout. (Default: `True`).
                                Python's root_logger by default adds a StreamHandler
                                if none is specified at app initialization, if this
                                is present we want it tracked and taken out later,
                                not to be sent to datadog (remove double entry as
                                it doesn't have the JSON formatter for easy interpretation on
                                Datadog)
    :param console_handler_format: Specifies the format of stdout logs. (Default: `DEFAULT_LOG_FORMAT`).
    """

    if root_log_level is None:
        root_log_level = "WARNING"

    root_logger = logging.getLogger()
    root_logger.setLevel(root_log_level)
    default_stdout_handler = None

    if root_logger.handlers:
        default_stdout_handler = root_logger.handlers[0]

    if module_log_levels:
        for module_name, log_level in module_log_levels.items():
            logging.getLogger(module_name).setLevel(log_level)

    if add_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(fmt=console_handler_format or DEFAULT_LOG_FORMAT))
        root_logger.addHandler(console_handler)
        if default_stdout_handler is not None:
            root_logger.removeHandler(default_stdout_handler)

        # log to docker for datadog if enabled.
        if "ENABLE_DATADOG_JSON_FORMATTER" in os.environ and os.environ["ENABLE_DATADOG_JSON_FORMATTER"].lower() == "true":
            formatter = DatadogJSONFormatter(trace_enabled=os.environ.get("DATADOG_TRACE_ENABLED", "false").lower() == "true")
            console_handler.setFormatter(formatter)

    # Add datadog handler if log to datadog is enabled
    if "DATADOG_HOST" in os.environ:
        opts = dict(
            host=os.environ["DATADOG_HOST"],
            port=int(os.environ.get("DATADOG_UDP_PORT", 10518))
        )

        datadog_handler = DataDogUdpHandler(**opts)
        root_logger.addHandler(datadog_handler)
