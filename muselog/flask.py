"""
Custom logger for user auth service in python flask 
"""

import sys
import logging

from time import strftime

logger = logging.getLogger(__name__)

# http://flask.pocoo.org/docs/0.12/api/#flask.Flask.after_request
def log_request(request_duratio, request, response):
    """Logging after every flask request with extra context for use w/ Graylog-enabled apps.
    
    Usage:
    @app.after_request
    def after_request(response):
        return muselog.flask.log_request(request_duration, request, response)

    """

    # http://flask.pocoo.org/docs/0.12/quickstart/#logging
    if response.status_code < 400:
        log_method = logger.info
    elif response.status_code < 500:
        log_method = logger.warning
    else:
        log_method = logger.error

    ts = strftime('[%Y-%b-%d %H:%M]')
    # decode byte to string for query_string here
    request_query = request.query_string.decode("utf-8")
    request_summary = f"{request.method} {request_query} {request.remote_addr}"

    data={"request_method": request.method,
          "request_path": request.full_path,
          "request_query": request_query,
          "response_status": response.status,
          "request_duration": request_duration,
          "request_remote_ip": request.remote_addr,
          "request_summary": request_summary}
  
    log_method("%d %s %s", response.status_code, request_summary, ts, extra=data)
    return response
