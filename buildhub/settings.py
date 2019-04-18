# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distribute this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import re

from configurations import Configuration, values
import dj_database_url
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
        "https://s3-us-east-1.amazonaws.com/net-mozaws-prod-delivery-firefox"
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

    # When we ingest the SQS queue we get a payload that contains an S3 key and
    # a S3 bucket name. We then assume that we can use our boto client to connect
    # to that bucket to read the key to download its file. That S3 bucket name
    # comes at runtime so it depends on the payloads which aren't know yet.
    # However, if you *do* know the bucket set this variable in advance so access
    # to it can be healthchecked.
    # Note that it's optional! Unset by default.
    # In real product it should probably be:
    #  https://s3.amazonaws.com/net-mozaws-prod-delivery-firefox
    SQS_S3_BUCKET_URL = values.URLValue()

    # If we know that the S3 buckets we download from are public we should use
    # unsigned requests. The only time you'd potentially not use this is when you
    # test against an S3 bucket that is not public.
    UNSIGNED_S3_CLIENT = values.BooleanValue(True)


class CORS:
    # Note-to-self; By default 'corsheaders.middleware.CorsMiddleware'
    # only kicks in when matched to this regex.
    CORS_URLS_REGEX = r"^/api/.*$"

    CORS_ORIGIN_ALLOW_ALL = True


class Whitenoise:

    # The default is that Whitenoise sets `Access-Control-Allow-Origin: *` for
    # static assets. We don't need that because we don't intend to serve the
    # static assets via a CDN.
    WHITENOISE_ALLOW_ALL_ORIGINS = False

    # We serve all the static files that are built from the "ui" create-react-app.
    # These files are things like ui/build/static/css/main.8741ee2b.css.
    # For these make sure we set full caching.
    def WHITENOISE_IMMUTABLE_FILE_TEST(self):
        def inner(path, url):
            # Match with built static assets from create-react-app.
            return re.search(r"\b[a-f0-9]{8}\b", url)

        return inner


class CSP:

    CSP_DEFAULT_SRC = "'self'"
    CSP_STYLE_SRC = "'self' 'unsafe-inline'"
    CSP_IMG_SRC = "'self' data:"
    CSP_OBJECT_SRC = "'none'"  # not using <object>, <embed>, and <applet> elements
    CSP_WORKER_SRC = "'none'"  # not using JS Worker, SharedWorker, or ServiceWorkers
    CSP_FRAME_SRC = "'none'"  # not using frames or iframes
    CSP_BLOCK_ALL_MIXED_CONTENT = True

    CSP_REPORT_URI = values.Value(None)

    CSP_EXCLUDE_URL_PREFIXES = ("/api",)


class Backfill:

    # The backfill script will write down, to disk, the last successful key
    # (and some metadata) when it iterates though the pages.
    RESUME_DISK_LOG_FILE = values.Value("/tmp/backfill-last-successful-key.json")


class Core(Configuration, AWS, CORS, Whitenoise, CSP, Backfill):
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
        "csp.middleware.CSPMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "buildhub.middleware.StatsMiddleware",
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
        "buildhub.dockerflow_extra.check_s3_bucket_url",
        "buildhub.dockerflow_extra.check_sqs_s3_bucket_url",
    ]


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

    # To prevent the ES search query from being too big.
    MAX_SEARCH_SIZE = values.IntegerValue(1000)


class OptionalDatabaseURLValue(values.DatabaseURLValue):
    def caster(self, url, **options):
        if not url:
            return None
        return dj_database_url.parse(url, **options)


class Base(Core, Elasticsearch):
    """Settings that may change per-environment, som defaults."""

    # Django
    SECRET_KEY = values.SecretValue()
    DEBUG = values.BooleanValue(default=False)
    ALLOWED_HOSTS = values.ListValue([])

    _DATABASES = values.DatabaseURLValue("postgresql://localhost/buildhub2")
    _KINTO_DATABASES = OptionalDatabaseURLValue(
        default="", alias="kinto", environ_name="KINTO_DATABASE_URL"
    )
    CONN_MAX_AGE = values.IntegerValue(60)

    @property
    def DATABASES(self):
        """Because it's not possible to set 'CONN_MAX_AGE a URL,
        # we patch the 'DATABASES' dict *after* django-configurations has done its
        thing."""
        DATABASES = self._DATABASES.value.copy()
        if self.CONN_MAX_AGE:
            DATABASES["default"]["CONN_MAX_AGE"] = self.CONN_MAX_AGE
        if self._KINTO_DATABASES.value[self._KINTO_DATABASES.alias]:
            DATABASES.update(self._KINTO_DATABASES.value)
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

    # Security related

    SILENCED_SYSTEM_CHECKS = values.ListValue(
        [
            # This rule is about having "X-FRAME-OPTIONS" set to "DENY" which is
            # not important for Buildhub2 because it's considered NOT dangerous to
            # put any of this data inside an iframe.
            "security.W019",
            # There are no POST endpoints that *change* data that is exposed.
            # I.e. you can't CSRF attack this site because there's no URL to do so
            # with.
            "security.W003",
            # Don't require SECURE_SSL_REDIRECT to be true.
            # Our load balancer talks to Django directly, via /__lbheartbeat__,
            # and it will 301 redirect if you don't convince it that the request
            # is HTTPS with `X-Forwarded-Proto: https` header. Basically, this
            # header can't be set in the load balancer.
            # If we disable the SECURE_SSL_REDIRECT (in other words omit setting it)
            # the /__heartbeat__ will complain and thus we can't use that endpoint
            # for our regular monitoring.
            # See https://github.com/mozilla-services/buildhub2/issues/411
            "security.W008",
        ]
    )

    SECURE_HSTS_SECONDS = values.IntegerValue(3600)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = values.BooleanValue(True)
    SECURE_HSTS_PRELOAD = values.BooleanValue(True)
    SECURE_CONTENT_TYPE_NOSNIFF = values.BooleanValue(True)
    SECURE_BROWSER_XSS_FILTER = values.BooleanValue(True)


class Localdev(Base):
    """Configuration to be used during local development and base class
    for testing"""

    DOTENV = os.path.join(BASE_DIR, ".env")

    DEBUG = values.BooleanValue(default=True)

    LOGGING_USE_JSON = values.BooleanValue(False)

    @property
    def VERSION(self):
        fn = os.path.join(self.BASE_DIR, "version.json")
        if os.path.exists(fn):
            with open(fn) as fp:
                return json.load(fp)
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

    # When doing local development you don't need to redirect to HTTPS.
    SECURE_HSTS_SECONDS = values.IntegerValue(0)
    SECURE_HSTS_PRELOAD = values.BooleanValue(False)


class Test(Base):
    """Configurat
    ion to be used during testing"""

    DEBUG = False
    ES_BUILD_INDEX = "test_buildhub2"
    SECRET_KEY = values.Value("not-so-secret-after-all")
    SQS_QUEUE_URL = "https://sqs.ca-north-2.amazonaws.com/123/buildhub-s3-events"
    S3_BUCKET_URL = "https://s3-eu-south-1.amazonaws.com/buildhubses"
    VERSION = {"version": "Testing"}

    def STATIC_ROOT(self):
        path = "/tmp/test_buildhub2"
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

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
        DATABASES = super().DATABASES.copy()
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

    SECURE_HSTS_SECONDS = values.IntegerValue(31536000)  # 1 year


class Prod(Stage):
    """Configuration to be used in prod environment"""
