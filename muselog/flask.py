"""
Custom logger for user auth service in python flask 
"""

import sys
import logging

from time import strftime
from muselog import add_gelf_handler

logger = logging.getLogger(__name__)

# http://flask.pocoo.org/docs/0.12/api/#flask.Flask.after_request
def log_request(app, request, response):
    """Logging after every flask request with extra context for use w/ Graylog-enabled apps.
    
    Usage:
    @app.after_request
    def after_request(response):
        return muselog.flask.log_request(app, request, response)

    """

    root_logger = app.logger
    root_logger.setLevel(logging.INFO)
    add_gelf_handler(root_logger)
    root_logger.addHandler(logging.StreamHandler(stream=sys.stdout))

    # http://flask.pocoo.org/docs/0.12/quickstart/#logging
    if response.status_code < 400:
        log_method = app.logger.info
    elif response.status_code < 500:
        log_method = app.logger.warning
    else:
        log_method = app.logger.error

    ts = strftime('[%Y-%b-%d %H:%M]')
    resquest_query = request.query_string.decode("utf-8")
    request_summary = "{0} {1} {2}".format(request.method, resquest_query, request.remote_addr)


    data={"request_method": request.method,
          "request_path": request.full_path,
          "request_query": resquest_query,
          "response_status": response.status,
          "request_remote_ip": request.remote_addr,
          "request_summary": request_summary}
  
    log_method("%d %s %s", response.status_code, request_summary, ts, extra=data)
    return response
