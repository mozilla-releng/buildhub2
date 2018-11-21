# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import re
from urllib.parse import urlparse

import backoff
import boto3
import requests
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings
from django.core import checks

logger = logging.getLogger("buildhub")


def _backoff_hdlr(details):
    logger.info(
        "Backing off {wait:0.1f} seconds afters {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )


connection_exceptions = (requests.exceptions.ConnectionError,)


@backoff.on_exception(
    backoff.constant, connection_exceptions, max_tries=3, on_backoff=_backoff_hdlr
)
def fetch(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def check_elasticsearch(app_configs, **kwargs):
    errors = []
    # The reason we're not checking the health of the index is because of the
    # chicken-and-egg problem that the index hasn't been created the very
    # first time we start the service.
    url = f"{settings.ES_URLS[0]}/_cluster/health"
    try:
        health = fetch(url)["status"]
        if not (health in ("yellow", "green")):
            errors.append(
                checks.Error(
                    f"Elasticsearch ({settings.ES_URLS[0]}) not healthy ({health!r}).",
                    id="buildhub.health.E002",
                )
            )
    except connection_exceptions:
        errors.append(
            checks.Error(
                f"Unable to connect to Elasticsearch on {settings.ES_URLS[0]}",
                id="buildhub.health.E001",
            )
        )
    return errors


def check_s3_bucket_url(app_configs, **kwargs):
    """Iff settings.S3_BUCKET_URL is set, check that we can access it."""
    s3_url = settings.S3_BUCKET_URL
    if not s3_url:
        return []
    return _check_s3_bucket_url(s3_url, region_name=kwargs.get("region_name"))


def check_sqs_s3_bucket_url(app_configs, **kwargs):
    """Iff settings.SQS_S3_BUCKET_URL is set, check that we can access it."""
    s3_url = settings.SQS_S3_BUCKET_URL
    if not s3_url:
        return []
    return _check_s3_bucket_url(s3_url, region_name=kwargs.get("region_name"))


def _check_s3_bucket_url(s3_url, region_name=None):
    errors = []
    bucket_name = urlparse(s3_url).path.split("/")[-1]
    if not region_name:
        try:
            region_name = re.findall(r"s3[\.-](.*?)\.amazonaws\.com", s3_url)[0]
        except IndexError:
            region_name = None
    connection_config = None
    if settings.UNSIGNED_S3_CLIENT:
        connection_config = Config(signature_version=UNSIGNED)
    s3_client = boto3.client("s3", region_name, config=connection_config)
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as exception:
        if exception.response["Error"]["Code"] == "404":
            errors.append(
                checks.Error(
                    f"The bucket {bucket_name} can not be found. From {s3_url}",
                    id="buildhub.health.E002",
                )
            )
        elif exception.response["Error"]["Code"] == "403":
            errors.append(
                checks.Error(
                    f"You do not have access to read {bucket_name}. From {s3_url}",
                    id="buildhub.health.E003",
                )
            )
        else:
            raise
    return errors
