import datetime
import logging
import json
import zlib
import os
import struct
import traceback
import socket

from logging.handlers import DatagramHandler

LEVELS = {
    logging.DEBUG: 7,
    logging.INFO: 6,
    logging.WARNING: 4,
    logging.ERROR: 3,
    logging.CRITICAL: 2
}


def object_to_json(obj):
    """Convert object that cannot be natively serialized by python to JSON representation."""
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    return str(obj)

def pack(get_object, compress, default):
    packed = json.dumps(get_object, separators=(',', ':'), default=default).encode('utf-8')
    return zlib.compress(packed) if compress else packed

def split(gelf, chunk_size):
    header = b'\x1e\x0f'
    message_id = os.urandom(8)
    chunks = [gelf[pos:pos+chunk_size] for pos in range(0, len(gelf), chunk_size)]
    number_of_chunks = len(chunks)

    for chunk_index, chunk in enumerate(chunks):
        yield b''.join((
            header,
            message_id,
            struct.pack('b', chunk_index),
            struct.pack('b', number_of_chunks),
            chunk
        ))    


def get_datadog_object(record, domain):

    dd_object = {
        'shortMessage': record.getMessage(),
        'timestamp': record.created,
        'level': LEVELS[record.levelno],
        'host': domain,
        'file': record.filename,
        'line': record.lineno,
        'module': record.module,
        'func': record.funcName,
        'loggerName': record.name,
        'threadName': record.threadName,
        'errorType': record.levelname
    }

    if record.exc_info is not None:
        dd_object['fullMessage'] = '\n'.join(traceback.format_exception(*record.exc_info))

    return dd_object


class BaseHandler(object):
    def __init__(self, json_default=object_to_json, compress=False, **kwargs):
        
        self.json_default = json_default
        self.compress = compress
        self.domain = socket.getfqdn()

    def pickle_log(self, record):
        return pack(
            get_datadog_object(record, self.domain), self.compress, self.json_default
        )


class DataDogUdpHandler(BaseHandler, DatagramHandler):
    """
    A handler class which writes logging records, in pickle format, to
    a datagram socket.  The pickle which is sent is that of the LogRecord's
    attribute dictionary (__dict__), so that the receiver does not need to
    have the logging module installed in order to process the logging event.

    To unpickle the record at the receiving end into a LogRecord, use the
    makeLogRecord function.
    """

    def __init__(self, host, port, compress=False, chunk_size=1300, **kwargs):
        """
        Initializes the handler with a specific host address and port.

        :param host: Datadog UDP input host
        :param port: Datadog UDP input port
        :param compress: compress message before sending it to the server or not
        :param chunk_size: length of a chunk, should be less than the MTU (maximum transmission unit)
        """

        DatagramHandler.__init__(self, host, port)
        BaseHandler.__init__(self, compress=compress, **kwargs)

        self.chunk_size = chunk_size

    def makePickle(self, record):
        """
        Pickles the record in binary format with a length prefix, and
        returns it ready for transmission across the socket.
        """

        return self.pickle_log(record)
