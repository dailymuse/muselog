import json
import socket
import traceback

from datetime import datetime, timedelta
from logging import LogRecord
from logging.handlers import DatagramHandler

import json_log_formatter

record_dict = dict()


class DataDogUdpHandler(DatagramHandler):
    """
    A handler class which writes logging records, in pickle format, to
    a datagram socket.  The pickle which is sent is that of the LogRecord's
    attribute dictionary (__dict__), so that the receiver does not need to
    have the logging module installed in order to process the logging event.

    To unpickle the record at the receiving end into a LogRecord, use the
    makeLogRecord function.
    """

    def __init__(self, host: str, port: int):
        """
        Initializes the handler with a specific host address and port.

        :param host: Datadog UDP input host
        :param port: Datadog UDP input port
        """

        super().__init__(host, port)

    def send(self, s: str):
        """
        Send a pickled string to a socket.

        This function no longer allows for partial sends which can happen
        when the network is busy - UDP does not guarantee delivery and
        can deliver packets out of sequence.
        """

        if self.sock is None:
            self.createSocket()

        self.sock.sendto(bytes(s+"\n", "utf-8"), (self.host, self.port))

    def makePickle(self, record: LogRecord) -> str:
        """
        Pickles the record in binary format with a length prefix, and
        returns it ready for transmission across the socket.
        """

        ei = record.exc_info
        if ei:
            dummy = self.format(record) # just to get traceback text into record.exc_text
            record.exc_info = None  # to avoid Unpickleable error
        d = dict(record.__dict__)
        s = json.dumps(d)
        if ei:
            record.exc_info = ei  # for next handler
        return s


class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return self.default(obj.to_json())
        elif hasattr(obj, "__dict__"):
            return obj.__class__.__name__
        elif hasattr(obj, "tb_frame"):
            return "traceback"
        elif isinstance(obj, timedelta):
            return obj.__str__()

        return super().default(obj)


class DatadogJSONFormatter(json_log_formatter.JSONFormatter):

    def format(self, record):
        message = record.getMessage()
        extra = self.extra_from_record(record)
        json_record = self.json_record(message, extra, record)
        mutated_record = self.mutate_json_record(json_record)
        # Backwards compatibility: Functions that overwrite this but don't
        # return a new value will return None because they modified the
        # argument passed in.
        if mutated_record is None:
            mutated_record = json_record
        return self.json_lib.dumps(mutated_record, cls=ObjectEncoder)
    
    def key_val(self, item):
        global record_dict

        context_obj = {}
        key, val = item.split("=")
        # del key from record before replacing with modified version
        del record_dict[key]
        key = f"ctx.{key}"
        context_obj[key]=int(val) if val.isdigit() else val
        return context_obj

    def json_record(self, message, extra, record):
        global record_dict

        extra['message'] = message
        record_dict = dict(record.__dict__)

        if "context" in record_dict:
            context_value = record_dict.get("context")
            array = context_value.replace(" ", "").split(",")
            for item in array:
                context_obj=self.key_val(item)
                extra.update(context_obj)

            del record_dict['context']

        if 'time' not in extra:
            extra['time'] = datetime.utcnow()
        if record.exc_info:
            extra['exception'] = self.formatException(record.exc_info)

        return {**extra, **record_dict}
