import pickle
import datetime
import json_log_formatter
import socket
import traceback
import json


from logging.handlers import DatagramHandler
from logging import LogRecord


def object_to_json(obj):
    """Convert object that cannot be natively serialized by python to JSON representation."""
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    return str(obj)


class DataDogUdpHandler(DatagramHandler):
    """
    A handler class which writes logging records, in pickle format, to
    a datagram socket.  The pickle which is sent is that of the LogRecord's
    attribute dictionary (__dict__), so that the receiver does not need to
    have the logging module installed in order to process the logging event.

    To unpickle the record at the receiving end into a LogRecord, use the
    makeLogRecord function.
    """

    def __init__(self, host, port):
        """
        Initializes the handler with a specific host address and port.

        :param host: Datadog UDP input host
        :param port: Datadog UDP input port
        :param chunk_size: length of a chunk, should be less than the MTU (maximum transmission unit)
        """

        DatagramHandler.__init__(self, host, port)

    def send(self, s):
        """
        Send a pickled string to a socket.

        This function no longer allows for partial sends which can happen
        when the network is busy - UDP does not guarantee delivery and
        can deliver packets out of sequence.
        """

        if self.sock is None:
            self.createSocket()

        self.sock.sendto(bytearray(s, 'utf-8'), self.host, self.port)

    def makePickle(self, record):
        """
        Pickles the record in binary format with a length prefix, and
        returns it ready for transmission across the socket.
        """

        ei = record.exc_info
        if ei:
            dummy = self.format(record) # just to get traceback text into record.exc_text
            record.exc_info = None  # to avoid Unpickleable error
        # s = pickle.dumps(record.__dict__)
        d = dict(record.__dict__)
        s = json.dumps(d)
        if ei:
            record.exc_info = ei  # for next handler
        return s


class DataDogJSONFormatter(json_log_formatter.JSONFormatter):

    def json_record(self, message, extra, record):

        extra['message'] = message
        extra['host'] = socket.getfqdn()

        if 'time' not in extra:
            extra['time'] = datetime.utcnow()

        if record.exc_info:
            extra['fullMessage'] = '\n'.join(traceback.format_exception(*record.exc_info))

        return extra

    def to_json(self, record):
        """Converts record dict to a JSON string.
        Override this method to change the way dict is converted to JSON.
        """
        return self.json_lib.dumps(record, separators=(',', ':'), default=object_to_json).encode('utf-8')
