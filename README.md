# Muselog #

Muselog standardizes logging across all Python applications in use at The Muse. It provides support
for Graylog and provides request hooks for Tornado.

## Usage

Import `muselog` as early as possible. At The Muse, this is usually in the application's top-level `__init__.py`.
After import, call the `setup_logging` function to initialize the library. For example,

```
import muselog

muselog.setup_logging(root_log_level=os.environ.get("LOG_LEVEL", "INFO"),
                      module_log_levels={"themuse": os.environ.get("THEMUSE_LOG_LEVEL", "INFO")},
                      add_console_handler=True,
                      console_handler_format=os.environ.get("LOG_FORMAT"))
```

See the method's documentation if any of the configuration options in this example are not clear.

### Graylog integration
You must set following environment variables to enable Graylog integration.

- GRAYLOG_HOST              :: The Graylog server hostname to which muselog will send GELF messages.
- GRAYLOG_ENV               :: The environment to tag the logging application with. One of `tst`, `stg`, or `prd`.
- GRAYLOG_APP_NAME          :: The name of the logging application.
- GRAYLOG_DEBUG             :: Enable debug log output from the underlying pygelf library. (Default: `true`).
- GRAYLOG_HANDLER_TYPE      :: The Layer 4 protocol to use when sending GELF messages. One of `tls` or `udp`. (Default: `tls`).
- GRAYLOG_UDP_PORT          :: Graylog server port that `udp` handler type sends GELF messages to. (Default: 12201).
- GRAYLOG_UDP_COMPRESS      :: Compress GELF messages. (Default: True).
- GRAYLOG_UDP_CHUNK_SIZE    :: Maxmium size (in bytes) of GELF message before it must be sent in multiple chunks. (Default: 1300).
- GRAYLOG_TLS_PORT          :: Graylog server port that `tls` handler type sends GELF messages to. (Default: 12201).
- GRAYLOG_TLS_TIMEOUT_SECS  :: Number of seconds to wait for TCP ack before abandoning message send.

### Datadog integation
You must set following environment variables to enable datadog integration.

- DATADOG_HOST            :: Datadog host to send JSON logs to
- DATADOG_UDP_PORT        :: datadog server port that `udp` handler type sends messages to. (Default: 10518).

### Tornado integration
Muselog provides a request hook for Tornado, which logs request data at the conclusion of each request.
You can use this hook in your application by pointing Tornado's `log_function` setting to `muselog.tornado.log_request`.

## Testing

Run `docker-compose up test` to run unit tests.

If you want to test integration with Graylog, run `docker-compose up graylog` followed by
`docker-compose run --rm -e GRAYLOG_HOST=graylog -e GRAYLOG_APP_NAME=test -e GRAYLOG_ENV=tst test bash -c "pip install -r test-requirements.txt && python"`. When inside the Python interpreter, run `import muselog` and test
to your heart's content.
