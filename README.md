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


### Datadog integration
You must set the following environment variables to enable datadog integration.

- DATADOG_HOST            :: Datadog host to send JSON logs to
- DATADOG_UDP_PORT        :: datadog server port that `udp` handler type sends messages to. (Default: 10518).


### STDOUT Logging 
- ENABLE_DATADOG_JSON_FORMATTER  :: set to `True` to enable datadog docker logging 


### Tornado integration
Muselog provides a request hook for Tornado, which logs request data at the conclusion of each request.
You can use this hook in your application by pointing Tornado's `log_function` setting to `muselog.tornado.log_request`.

## Testing

Run `docker-compose up test` to run unit tests.

If you want to test integration with Graylog, run `docker-compose up graylog` followed by
`docker-compose run --rm -e GRAYLOG_HOST=graylog -e GRAYLOG_APP_NAME=test -e GRAYLOG_ENV=tst test bash -c "pip install -r test-requirements.txt && python"`. When inside the Python interpreter, run `import muselog` and test
to your heart's content.
