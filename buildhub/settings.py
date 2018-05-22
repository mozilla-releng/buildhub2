# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

from decouple import config, Csv
from unipath import Path
import dj_database_url

BASE_DIR = Path(__file__).parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default='localhost')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'corsheaders',

    'buildhub.main',
    'buildhub.api',
    'buildhub.ingest',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


DATABASES = {
    'default': config(
        'DATABASE_URL',
        default='postgresql://localhost/buildhub2',
        cast=dj_database_url.parse
    )
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

ROOT_URLCONF = 'buildhub.urls'


# Note-to-self; By default 'corsheaders.middleware.CorsMiddleware' only kicks
# in when matched to this regex.
CORS_URLS_REGEX = r'^/api/.*$'

CORS_ORIGIN_ALLOW_ALL = True


# Dockerflow from Tecken
LOGGING_USE_JSON = config('LOGGING_USE_JSON', True, cast=bool)

LOGGING_DEFAULT_LEVEL = config('LOGGING_DEFAULT_LEVEL', 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'dockerflow.logging.JsonLogFormatter',
            'logger_name': 'buildhub',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': LOGGING_DEFAULT_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': (
                'json' if LOGGING_USE_JSON else 'verbose'
            ),
        },
        'sentry': {
            'level': 'ERROR',
            'class': (
                'raven.contrib.django.raven_compat.handlers'
                '.SentryHandler'
            ),
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['sentry', 'console'],
    },
    'loggers': {
        'django': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.request': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'buildhub': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'markus': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'request.summary': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}

# If you all you know is the queue *name* and its AWS region,
# make the URL be:
#   aws://https://sqs.$NAME_OF_REGION.amazonaws.com/$NAME_OF_QUEUE
SQS_QUEUE_URL = config('SQS_QUEUE_URL')

# For more details, see:
# http://boto3.readthedocs.io/en/latest/reference/services/sqs.html#SQS.Queue.receive_messages

# The duration (in seconds) for which the call waits for a message
# to arrive in the queue before returning.
SQS_QUEUE_WAIT_TIME_SECONDS = config(
    'SQS_QUEUE_WAIT_TIME_SECONDS', cast=int, default=10
)
# The duration (in seconds) that the received messages are hidden
# from subsequent retrieve requests after being retrieved by
# a ReceiveMessage request.
# Note! This only really matters when multiple concurrent consumers run
# daemons that consume the queue.
SQS_QUEUE_VISIBILITY_TIMEOUT = config(
    'SQS_QUEUE_VISIBILITY_TIMEOUT', cast=int, default=5,
)
# The maximum number of messages to return.
# Valid values are 1 to 10. Default is 1.
SQS_QUEUE_MAX_NUMBER_OF_MESSAGES = config(
    'SQS_QUEUE_MAX_NUMBER_OF_MESSAGES', cast=int, default=1,
)

# Name of the Elasticsearch index to put builds into
ES_BUILD_INDEX = config('ES_BUILD_INDEX', 'buildhub2')
ES_BUILD_INDEX_SETTINGS = {
    'refresh_interval': config('ES_REFRESH_INTERVAL', '1s')
}

ES_URLS = config('ES_URLS', default='localhost:9200', cast=Csv())
ES_CONNECTIONS = {
    'default': {
        'hosts': ES_URLS,
    },
}
