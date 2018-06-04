# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import time
import logging

import backoff
import requests

from django.core import checks
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('buildhub')


def _backoff_hdlr(details):
    logger.info(
        "Backing off {wait:0.1f} seconds afters {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )

connection_exceptions = (requests.exceptions.ConnectionError,)

@backoff.on_exception(
    backoff.constant,
    connection_exceptions,
    max_tries=3,
    on_backoff=_backoff_hdlr,
)
def fetch(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def check_elasticsearch(app_configs, **kwargs):
    errors = []
    url = f"{settings.ES_URLS[0]}/_cat/health"
    try:
        health = fetch(url)
        if not (' green ' in health or ' yellow ' in health):
            errors.append(checks.Error(
                f"Elasticsearch ({settings.ES_URLS[0]}) not healthy ({health!r}).",
                id="buildhub.health.E002"
            ))
    except connection_exceptions as exception:
        errors.append(checks.Error(
            f"Unable to connect to Elasticsearch on {settings.ES_URLS[0]}",
            id="buildhub.health.E001"
        ))
    return errors


