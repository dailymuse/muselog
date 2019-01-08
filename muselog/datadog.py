import json
import socket
import traceback

from datetime import datetime
from logging import LogRecord
from logging.handlers import DatagramHandler

import json_log_formatter


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

class DatadogJSONFormatter(json_log_formatter.JSONFormatter):

     def json_record(self, message, extra, record):
         
        extra['message'] = message
        extra['host'] = socket.getfqdn()

        record_dict = dict(record.__dict__)

        if 'time' not in extra:
            extra['time'] = datetime.utcnow()
        if record.exc_info:
            extra['fullMessage'] = '\n'.join(traceback.format_exception(*record.exc_info))

        return {**extra, **record_dict}
