# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distribute this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import subprocess

from configurations import Configuration, values
from dockerflow.version import get_version

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class AWS:
    """AWS configuration"""

    # If you all you know is the queue *name* and its AWS region,
    # make the URL be:
    #   aws://https://sqs.$NAME_OF_REGION.amazonaws.com/$NAME_OF_QUEUE
    SQS_QUEUE_URL = values.URLValue(
        "https://sqs.us-west-2.amazonaws.com/927034868273/buildhub-s3-events"
    )
    S3_BUCKET_URL = values.URLValue(
        "https://s3-us-east-1.amazonaws.com/"
        "net-mozaws-prod-delivery-inventory-us-east-1"
    )

    # For more details, see:
    # http://boto3.readthedocs.io/en/latest/reference/services/sqs.html#SQS.Queue.receive_messages

    # The duration (in seconds) for which the call waits for a message
    # to arrive in the queue before returning.
    SQS_QUEUE_WAIT_TIME_SECONDS = values.IntegerValue(10)

    # The duration (in seconds) that the received messages are hidden
    # from subsequent retrieve requests after being retrieved by
    # a ReceiveMessage request.
    # Note! This only really matters when multiple concurrent consumers run
    # daemons that consume the queue.
    SQS_QUEUE_VISIBILITY_TIMEOUT = values.IntegerValue(5)

    # The maximum number of messages to return.
    # Valid values are 1 to 10. Default is 1.
    SQS_QUEUE_MAX_NUMBER_OF_MESSAGES = values.IntegerValue(1)


class CORS:
    # Note-to-self; By default 'corsheaders.middleware.CorsMiddleware'
    # only kicks in when matched to this regex.
    CORS_URLS_REGEX = r"^/api/.*$"

    CORS_ORIGIN_ALLOW_ALL = True


class Core(Configuration, AWS, CORS):
    """Settings that will never change per-environment."""

    # THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    # BASE_DIR = os.path.dirname(THIS_DIR)
    BASE_DIR = BASE_DIR

    STATIC_URL = "/"
    STATIC_ROOT = values.PathValue(
        os.path.join(BASE_DIR, "ui/build"), check_exists=False
    )

    VERSION = get_version(BASE_DIR)

    INSTALLED_APPS = [
        "django.contrib.contenttypes",
        "corsheaders",
        "dockerflow.django",
        "buildhub.main",
        "buildhub.api",
        "buildhub.ingest",
    ]

    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "dockerflow.django.middleware.DockerflowMiddleware",
        "buildhub.whitenoise_extra.BuildhubWhiteNoiseMiddleware",
    ]

    ROOT_URLCONF = "buildhub.urls"

    WSGI_APPLICATION = "buildhub.wsgi.application"

    # Internationalization
    LANGUAGE_CODE = "en-us"
    TIME_ZONE = "UTC"
    USE_I18N = False
    USE_L10N = False
    USE_TZ = True

    DOCKERFLOW_CHECKS = [
        # Defaults are documented here:
        # https://python-dockerflow.readthedocs.io/en/latest/django.html#dockerflow-checks
        "dockerflow.django.checks.check_database_connected",
        "dockerflow.django.checks.check_migrations_applied",
        "buildhub.dockerflow_extra.check_elasticsearch",
    ]

    # The default is that Whitenoise sets `Access-Control-Allow-Origin: *` for
    # static assets. We don't need that because we don't intend to serve the
    # static assets via a CDN.
    WHITENOISE_ALLOW_ALL_ORIGINS = False


class Elasticsearch:
    # Name of the Elasticsearch index to put builds into
    ES_BUILD_INDEX = values.Value("buildhub2")
    ES_REFRESH_INTERVAL = values.Value("1s")

    @property
    def ES_BUILD_INDEX_SETTINGS(self):
        return {"refresh_interval": self.ES_REFRESH_INTERVAL}

    ES_URLS = values.ListValue(["http://localhost:9200"])

    @property
    def ES_CONNECTIONS(self):
        return {"default": {"hosts": self.ES_URLS}}


class Base(Core, Elasticsearch):
    """Settings that may change per-environment, som defaults."""

    #
    # Django
    SECRET_KEY = values.SecretValue()
    DEBUG = values.BooleanValue(default=False)
    ALLOWED_HOSTS = values.ListValue([])

    _DATABASES = values.DatabaseURLValue("postgresql://localhost/buildhub2")
    CONN_MAX_AGE = values.IntegerValue(60)

    @property
    def DATABASES(self):
        """Because it's not possible to set 'CONN_MAX_AGE a URL,
        # we patch the 'DATABASES' dict *after* django-configurations has done its
        thing."""
        DATABASES = self._DATABASES.value.copy()
        if self.CONN_MAX_AGE:
            DATABASES["default"]["CONN_MAX_AGE"] = self.CONN_MAX_AGE
        return DATABASES

    # Logging
    LOGGING_USE_JSON = values.BooleanValue(True)
    LOGGING_DEFAULT_LEVEL = values.Value("INFO")

    @property
    def LOGGING(self):
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "dockerflow.logging.JsonLogFormatter",
                    "logger_name": "buildhub",
                },
                "verbose": {"format": "%(levelname)s %(asctime)s %(name)s %(message)s"},
            },
            "handlers": {
                "console": {
                    "level": self.LOGGING_DEFAULT_LEVEL,
                    "class": "logging.StreamHandler",
                    "formatter": ("json" if self.LOGGING_USE_JSON else "verbose"),
                },
                "sentry": {
                    "level": "ERROR",
                    "class": (
                        "raven.contrib.django.raven_compat.handlers" ".SentryHandler"
                    ),
                },
                "null": {"class": "logging.NullHandler"},
            },
            "root": {"level": "INFO", "handlers": ["sentry", "console"]},
            "loggers": {
                "django": {
                    "level": "WARNING",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "django.db.backends": {
                    "level": "ERROR",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "django.request": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "raven": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "sentry.errors": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "buildhub": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "backoff": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "markus": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "elasticsearch": {
                    "level": "ERROR",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "request.summary": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
                "django.security.DisallowedHost": {
                    "handlers": ["null"],
                    "propagate": False,
                },
            },
        }


class Localdev(Base):
    """Configuration to be used during local development and base class
    for testing"""

    DOTENV = os.path.join(BASE_DIR, ".env")

    DEBUG = values.BooleanValue(default=True)

    LOGGING_USE_JSON = values.BooleanValue(False)

    @property
    def VERSION(self):
        fn = os.path.join(self.BASE_DIR, "version.json")
        try:
            with open(fn) as f:
                return json.load(f)
        except FileNotFoundError:
            output = subprocess.check_output(
                # Use the absolute path of 'git' here to avoid 'git'
                # not being the git we expect in Docker.
                ["/usr/bin/git", "describe", "--tags", "--always", "--abbrev=0"]
            )  # nosec
            if output:
                return {"version": output.decode().strip()}
            else:
                return {}

    @property
    def LOGGING(self):
        LOGGING = super().LOGGING
        # Add django.server (useful for local dev) and
        # unset the request.summary.
        LOGGING["loggers"]["django.server"] = {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        }
        LOGGING["loggers"]["request.summary"]["level"] = "ERROR"
        return LOGGING

    MARKUS_BACKENDS = values.ListValue(
        [{"class": "markus.backends.logging.LoggingMetrics"}]
    )


class Test(Base):
    """Configurat
    ion to be used during testing"""

    DEBUG = False
    ES_BUILD_INDEX = "test_buildhub2"
    SECRET_KEY = values.Value("not-so-secret-after-all")
    SQS_QUEUE_URL = "https://sqs.ca-north-2.amazonaws.com/123/buildhub-s3-events"
    S3_BUCKET_URL = "https://s3-eu-south-1.amazonaws.com/buildhubses"
    VERSION = {"version": "Testing"}
    STATIC_ROOT = "/tmp/test_buildhub2"

    MARKUS_BACKENDS = []


class Stage(Base):
    """Configuration for the Stage server."""

    # Defaulting to 'localhost' here because that's where the Datadog
    # agent is expected to run in production.
    STATSD_HOST = values.Value("localhost")
    STATSD_PORT = values.Value(8125)
    STATSD_NAMESPACE = values.Value("")

    @property
    def MARKUS_BACKENDS(self):
        return [
            {
                "class": "markus.backends.datadog.DatadogMetrics",
                "options": {
                    "statsd_host": self.STATSD_HOST,
                    "statsd_port": self.STATSD_PORT,
                    "statsd_namespace": self.STATSD_NAMESPACE,
                },
            }
        ]

    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    @property
    def DATABASES(self):
        "require encrypted connections to Postgres"
        DATABASES = super().DATABASES.value.copy()
        DATABASES["default"].setdefault("OPTIONS", {})["sslmode"] = "require"
        return DATABASES

    # Sentry setup
    SENTRY_DSN = values.Value(environ_prefix=None)

    MIDDLEWARE = [
        "raven.contrib.django.raven_compat.middleware"
        ".SentryResponseErrorIdMiddleware"
    ] + Base.MIDDLEWARE

    INSTALLED_APPS = Base.INSTALLED_APPS + ["raven.contrib.django.raven_compat"]

    @property
    def RAVEN_CONFIG(self):
        config = {
            "dsn": self.SENTRY_DSN,
            # "transport": RequestsHTTPTransport
        }
        if self.VERSION:
            config["release"] = (
                self.VERSION.get("version") or self.VERSION.get("commit") or ""
            )
        return config


class Prod(Stage):
    """Configuration to be used in prod environment"""
