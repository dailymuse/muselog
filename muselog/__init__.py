"""Custom logging facilities to simplify the process of passing additional data to loggers."""

import logging
import os
from typing import Mapping, Optional, Union

from pygelf import GelfUdpHandler, GelfTlsHandler


#: Format to use
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"

def setup_logging(root_log_level: Optional[str] = None,
                  module_log_levels: Optional[Mapping[str, Union[str, int]]] = None,
                  add_console_handler: bool = True,
                  console_handler_format: Optional[str] = None):
    """Setup log handlers for the rover namespace"""

    if root_log_level is None:
        root_log_level = "WARNING"

    root_logger = logging.getLogger()
    root_logger.setLevel(root_log_level)

    if module_log_levels:
        for module_name, log_level in module_log_levels.items():
            logging.getLogger(module_name).setLevel(log_level)

    if add_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(fmt=console_handler_format or DEFAULT_LOG_FORMAT))
        root_logger.addHandler(console_handler)
        

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
