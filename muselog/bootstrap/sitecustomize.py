"""Support application-wide exception hook with muselog integration."""

import os

import muselog

module_log_levels = dict()
if os.environ.get("MUSELOG_MODULE_LOG_LEVELS"):
    for module_log_level in os.environ["MUSELOG_MODULE_LOG_LEVELS"].split(","):
        module, log_level = module_log_level.split("=")
        module_log_levels[module] = log_level

muselog.setup_logging(
    root_log_level=os.environ.get("MUSELOG_LOG_LEVEL"),
    module_log_levels=module_log_levels,
    console_handler_format=os.environ.get("MUSELOG_LOG_FORMAT"),
)
