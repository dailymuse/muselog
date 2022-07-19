# Muselog
Muselog standardizes logging across all Python applications in use at The Muse.
It integrates with [DataDog](https://www.datadoghq.com/), and it provides request hooks for the following web frameworks or interfaces.

- [ASGI](https://asgi.readthedocs.io/en/latest/)
- [Django](https://www.djangoproject.com/)
- [Flask](https://palletsprojects.com/p/flask/)
- [Tornado](https://www.tornadoweb.org/en/stable/)

## Installation

### pip
`muselog` is avaible on themuse's public gemfury index `https://pypi.fury.io/themuse/` . You'll need to add our index to your `requirements.txt` in order to resolve the module.

```sh
# requirements.txt
--extra-index-url https://pypi.fury.io/themuse/

muselog==1.8.4
```

### git
You can still install `muselog` through git via the tags we publish on github and an egg _(string directory that gets checked out as part of the install)_.

```sh
# requirements.txt

# example
-e git+git://github.com/dailymuse/muselog.git@1.8.4#egg=muselog[tornado]
```

## Usage

### From the command line
The most effective manner to use muselog is to run your python program using `muselog-run`.
This will ensure that muselog is setup before anything else.

Say you wanted to run the file "main.py" with arguments "--file data.txt". You only care about
ERROR logs for all modules, except 'muselog', for which you want to see INFO logs,
and 'muselog.logger', for which you want to see DEBUG logs.
Your command would look as follows.

```
muselog-run --root-log-level ERROR --module-log-level muselog=INFO --module-log-level muselog.logger=DEBUG python main.py --file data.txt
```

### In code
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


## Integrations
### Datadog

- DATADOG_ERROR_STACK_LIMIT  :: truncate the stack trace sent in `error.stack` to X number of characters, default 10000

#### Send logs to stdout
- ENABLE_DATADOG_JSON_FORMATTER  :: set to `True` to enable datadog docker logging

This option will only work if muselog.setup_logging's `add_console_handler` parameter is `True` (the default).

#### Send logs to a UDP listener
Set the following environment variables to enable datadog UDP integration.

- DATADOG_HOST            :: Datadog host to send JSON logs to
- DATADOG_UDP_PORT        :: datadog server port that `udp` handler type sends messages to. (Default: 10518).

### Web framework
Muselog provides middleware / request hooks (depending on the framework) to logs request data at the conclusion of each request.
Below are instructions to setup muselog for each supported web framework.

#### ASGI
Muselog supports any ASGI-compatible web framework, such as FastAPI and Starlette.
To use, first install muselog with the `[asgi]` extra.
Then add the `muselog.asgi.RequestLoggingMiddleware` middleware to your ASGI application.
In FastAPI, this could look as follows.

```
from fastapi import Depends, FastAPI
from muselog.asgi import RequestLoggingMiddleware

app = FastAPI()
# RequestLoggingMiddleware is a muselog middleware that logs the end of a request.
# It will add a `request_id` to the context for you, which you can access as follows.
# from muselog import context
# req_id = context.get("request_id")
app.add_middleware(RequestLoggingMiddleware)
```

#### Django
Install with the `[django]` extra.
Add `muselog.django.MuseDjangoRequestLoggingMiddleware` to your middleware list.

#### Flask
Install with the `[flask]` extra.
Call `muselog.flask.register_muselog_request_hooks` immediately after instantiating the Flask application object.
For example,

```
import flask
import muselog.flask

app = flask.Flask("example")
muselog.flask.register_muselog_request_hooks(app)
```

#### Tornado
Install with the `[tornado]` extra.
Set Tornado's `log_function` to `muselog.tornado.log_request`.
To log exceptions with more detail, add `muselog.tornado.ExceptionLogger`
as a base class for your request handlers.

## Development
### Testing
Run `docker-compose up test` to run unit tests.
