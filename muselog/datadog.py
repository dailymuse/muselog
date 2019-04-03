"""Module that houses all logic necessary to send well-formed logs to Datadog."""

import json
from typing import Any, Mapping

from datetime import datetime, timedelta
from logging import LogRecord
from logging.handlers import DatagramHandler

import json_log_formatter

from ddtrace import helpers


class DataDogUdpHandler(DatagramHandler):
    """A handler class which writes logging records, in pickle format, to a datagram socket.

    The pickle which is sent is that of the LogRecord's attribute dictionary (__dict__),
    so that the receiver does not need to have the logging module installed in order to process the logging event.

    To unpickle the record at the receiving end into a LogRecord, use the
    makeLogRecord function.
    """

    def __init__(self, host: str, port: int):
        """Initialize the handler with a specific host address and port.

        :param host: Datadog UDP input host
        :param port: Datadog UDP input port
        """
        super().__init__(host, port)

    def send(self, s: str):
        """Send a pickled string to a socket.

        This function no longer allows for partial sends which can happen
        when the network is busy - UDP does not guarantee delivery and
        can deliver packets out of sequence.
        """
        if self.sock is None:
            self.createSocket()

        self.sock.sendto(bytes(s + "\n", "utf-8"), (self.host, self.port))

    def makePickle(self, record: LogRecord) -> str:
        """Pickle the log record.

        Pickles the record in binary format with a length prefix, and
        returns it ready for transmission across the socket.
        """
        ei = record.exc_info
        if ei:
            _ = self.format(record)  # just to get traceback text into record.exc_text
            record.exc_info = None  # to avoid Unpickleable error
        d = dict(record.__dict__)
        s = json.dumps(d)
        if ei:
            record.exc_info = ei  # for next handler
        return s


class ObjectEncoder(json.JSONEncoder):
    """Class to convert an object into JSON."""

    def default(self, obj: Any):
        """Convert `obj` to JSON."""
        if hasattr(obj, "to_json"):
            return self.default(obj.to_json())
        elif hasattr(obj, "__dict__"):
            return obj.__class__.__name__
        elif hasattr(obj, "tb_frame"):
            return "traceback"
        elif isinstance(obj, timedelta):
            return obj.__str__()
        else:
            # generic, captures all python classes irrespective.
            cls = type(obj)
            result = {
                "__custom__": True,
                "__module__": cls.__module__,
                "__name__": cls.__name__,
            }
            return result


class DatadogJSONFormatter(json_log_formatter.JSONFormatter):
    """JSON log formatter that includes Datadog standard attributes."""

    def __init__(self, trace_enabled: bool = False):
        """Create the formatter.

        :param trace_enabled: Set to true to include trace information in the log.
        """
        self.trace_enabled = trace_enabled

    def inject_trace_values(self, record: LogRecord):
        """Inject logs with a 'trace_id' and 'span_id'.

        If a trace is active this helps DD to correlate logs sent to that specific
        trace in APM.
        """
        if not self.trace_enabled:
            return record

        # Create a new record so we don't modify the original
        new_record = record.copy()

        # get correlation ids from current tracer context
        trace_id, span_id = helpers.get_correlation_ids()

        new_record["dd.trace_id"] = trace_id or 0
        new_record["dd.span_id"] = span_id or 0

        return new_record

    def format(self, record: LogRecord):
        """Return the record in the format usable by Datadog."""
        message = record.getMessage()
        json_record = self.json_record(message, record)
        trace_injected_record = self.inject_trace_values(json_record)
        mutated_record = self.mutate_json_record(trace_injected_record)
        # Backwards compatibility: Functions that overwrite this but don't
        # return a new value will return None because they modified the
        # argument passed in.
        if mutated_record is None:
            mutated_record = json_record
        return self.to_json(mutated_record)

    def to_json(self, record: Mapping[str, Any]):
        """Convert record dict to a JSON string.

        Override this method to change the way dict is converted to JSON.
        """
        return self.json_lib.dumps(record, cls=ObjectEncoder)

    def json_record(self, message: str, record: LogRecord):
        """Convert the record to JSON and inject Datadog attributes."""
        record_dict = dict(record.__dict__)

        record_dict["message"] = message

        if "time" not in record_dict:
            record_dict["time"] = datetime.utcnow()
        if record.exc_info:
            record_dict["exception"] = self.formatException(record.exc_info)

        # Handle non-standard attributes
        try:
            if "context" in record_dict:
                context_obj = dict()
                context_value = record_dict.get("context")
                array = context_value.replace(" ", "").split(",")
                for item in array:
                    key, val = item.split("=")

                    # del key from record before replacing with modified version
                    del record_dict[key]

                    key = f"ctx.{key}"
                    context_obj[key] = int(val) if val.isdigit() else val
                    record_dict.update(context_obj)

                del record_dict["context"]
        except Exception as e:
            # This will allow the context come in as a regular string if it
            # it is not empty although I suspect an empty context here.
            record_dict["context_error"] = str(e)

        return record_dict
