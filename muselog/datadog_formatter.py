import datetime
import json_log_formatter
import socket
import traceback


def object_to_json(obj):
    """Convert object that cannot be natively serialized by python to JSON representation."""
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    return str(obj)


class DatadogJSONFormatter(json_log_formatter.JSONFormatter):

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
