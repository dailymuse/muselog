"""Run an application with muselog pre-configured."""

import os
from distutils import spawn
from enum import Enum
from typing import List, Optional

import muselog
import typer


class LogLevel(str, Enum):
    """Python logger levels."""

    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"


def _validate_module_log_level(ctx, param, value):
    try:
        for module_log_level in value:
            module, log_level = module_log_level.split("=", 2)
            if not module or not log_level:
                raise ValueError
            _ = LogLevel[log_level.lower()]
    except TypeError:
        if value is None:
            raise typer.BadParameter("log levels cannot be None")
        else:
            raise typer.BadParameter("format must be module=DEBUG|INFO|WARNING|ERROR|CRITICAL")
    except ValueError:
        raise typer.BadParameter("format must be module=DEBUG|INFO|WARNING|ERROR|CRITICAL")
    except KeyError:
        raise typer.BadParameter("log level must be one of DEBUG|INFO|WARNING|ERROR|CRITICAL")
    return value


app = typer.Typer()


@app.command(
    context_settings=dict(
        allow_extra_args=True,
        ignore_unknown_options=True,
        allow_interspersed_args=False,
    )
)
def main(
    ctx: typer.Context,
    program: str = typer.Argument(..., help="Python program to execute."),
    args: Optional[List[str]] = typer.Argument(
        None,
        help="Arguments to pass to *program*.",
    ),
    root_log_level: LogLevel = typer.Option(
        LogLevel.warning,
        case_sensitive=False,
        help="Root logger log level.",
    ),
    module_log_level: Optional[List[str]] = typer.Option(
        None,
        callback=_validate_module_log_level,
        help="""\b
Set the minimum log level for a module.
Can specify multiple times.
Format: module=DEBUG|INFO|WARNING|ERROR|CRITICAL. (e.g., muselog.logger=CRITICAL)
""",
    ),
    log_format: str = typer.Option(
        muselog.DEFAULT_LOG_FORMAT,
        help="The format to use for the log messages. Has no effect for datadog logs.",
    ),
):
    """Execute the given Python program with muselog configured."""
    from muselog import __file__ as muselog_root
    root_dir = os.path.dirname(muselog_root)
    bootstrap_dir = os.path.join(root_dir, "bootstrap")
    path = os.environ.get("PYTHONPATH")
    if path:
        os.environ["PYTHONPATH"] = f"{bootstrap_dir}{os.path.pathsep}{path}"
    else:
        os.environ["PYTHONPATH"] = bootstrap_dir
    os.environ["MUSELOG_LOG_LEVEL"] = root_log_level
    if module_log_level:
        os.environ["MUSELOG_MODULE_LOG_LEVELS"] = ",".join(module_log_level)
    if log_format:
        os.environ["MUSELOG_LOG_FORMAT"] = log_format
    if not args:
        args = []
    executable = spawn.find_executable(program)
    os.execl(executable, executable, *args)  # nosec
