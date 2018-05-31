# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import time
import logging

import backoff
from elasticsearch.exceptions import ConnectionError

from django.core import checks
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from buildhub.main.search import build_index

logger = logging.getLogger('buildhub')


def _backoff_hdlr(details):
    logger.info(
        "Backing off {wait:0.1f} seconds afters {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )

connection_exceptions = (ConnectionError,)

@backoff.on_exception(
    backoff.expo,
    connection_exceptions,
    max_tries=3,
    on_backoff=_backoff_hdlr,
)
def fetch_stats(idx):
    return build_index.stats()


def check_elasticsearch(app_configs, **kwargs):
    errors = []
    try:
        stats = fetch_stats(build_index)
        failed = stats['_shards']['failed']
        if failed:
            errors.append(checks.Error(
                f"{failed} shard(s) are failing on Elasticsearch "
                f"on {settings.ES_URLS[0]}",
                id="buildhub.health.E002"
            ))
    except connection_exceptions as exception:
        errors.append(checks.Error(
            f"Unable to connect to Elasticsearch on {settings.ES_URLS[0]}",
            id="buildhub.health.E001"
        ))
    return errors


