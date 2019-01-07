"""Custom logging facilities to simplify the process of passing additional data to loggers."""

import logging
import os
from typing import Mapping, Optional, Union

from pygelf import GelfUdpHandler, GelfTlsHandler

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
    :param console_handler_format: Specifies the format of stdout logs. (Default: `DEFAULT_LOG_FORMAT`).
    """

    if root_log_level is None:
        root_log_level = "WARNING"

    root_logger = logging.getLogger()
    root_logger.setLevel(root_log_level)
    default_stdout_handler = None

    if len(root_logger.handlers) > 0:
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
        if "ENABLE_DATADOG_JSON_FORMATTER" in os.environ and os.environ["ENABLE_DATADOG_JSON_FORMATTER"] == "True":
            formatter = DatadogJSONFormatter()
            console_handler.setFormatter(formatter)

    # Add GELF handler if GELF is enabled
    if "GRAYLOG_HOST" in os.environ:
        common_opts = dict(
            host=os.environ["GRAYLOG_HOST"],
            debug=bool(os.environ.get("GRAYLOG_DEBUG", True)),
            include_extra_fields=True,
            _app_name=os.environ["GRAYLOG_APP_NAME"],
            _env=os.environ["GRAYLOG_ENV"]
        )
        handler_type = os.environ.get("GRAYLOG_HANDLER_TYPE", "tls").lower()
        if handler_type == "udp":
            gelf_handler = GelfUdpHandler(**common_opts,
                                          port=int(os.environ.get("GRAYLOG_UDP_PORT", 12201)),
                                          chunk_size=int(os.environ.get("GRAYLOG_UDP_CHUNK_SIZE", 1300)),
                                          compress=bool(os.environ.get("GRAYLOG_UDP_COMPRESS", True)))
        elif handler_type == "tls":
            gelf_handler = GelfTlsHandler(**common_opts,
                                          port=int(os.environ.get("GRAYLOG_TLS_PORT", 12201)),
                                          timeout=float(os.environ.get("GRAYLOG_TLS_TIMEOUT_SECS", 0.3)))
        else:
            raise ValueError("Graylog handler type '{}' not recognized. Valid types are 'udp' and 'tls'.".format(handler_type))

        root_logger.addHandler(gelf_handler)

    # Add datadog handler if log to datadog is enabled
    if "DATADOG_HOST" in os.environ:
        opts = dict(
            host=os.environ["DATADOG_HOST"],
            port=int(os.environ.get("DATADOG_UDP_PORT", 10518))
        )

        datadog_handler = DataDogUdpHandler(**opts)
        root_logger.addHandler(datadog_handler)
