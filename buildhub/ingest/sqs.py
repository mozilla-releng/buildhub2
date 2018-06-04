# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import re
import os
import io
import itertools
from urllib.parse import urlparse

import boto3
from jsonschema import ValidationError
from botocore.exceptions import ClientError

from buildhub.main.models import Build


logger = logging.getLogger('buildhub')


def start(
    queue_url,
    region_name=None,
    wait_time=10,
    visibility_timeout=5,
    max_number_of_messages=1,
):

    queue_name = urlparse(queue_url).path.split('/')[-1]
    if not region_name:
        region_name = re.findall(r'sqs\.(.*?)\.amazonaws\.com', queue_url)[0]

    logger.debug(
        f"Connecting to SQS queue {queue_name!r} (in {region_name!r})"
    )
    sqs = boto3.resource('sqs', region_name=region_name)
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    # This is a mutable that will be included in every callback.
    # It's intended as cheap state so that things like S3 client
    # configuration and connection can be reused without having to
    # be bootstrapped in vain.
    config = {
        'region_name': region_name
    }

    # By default, we receive 1 message per call to `queue.receive_messages()`
    # but you can change that with settings.SQS_QUEUE_MAX_NUMBER_OF_MESSAGES.
    # If it's 1, the number of "loops" will be the same as the number "count".
    count = 0
    # Use `itertools.count()` instead of `while True` to be able to mock it in
    # tests.
    for loops in itertools.count():
        for message in queue.receive_messages(
            WaitTimeSeconds=wait_time,
            VisibilityTimeout=visibility_timeout,
            MaxNumberOfMessages=max_number_of_messages,
        ):
            logger.debug(f"About to process message number {count}")
            process_event(config, json.loads(message.body))
            count += 1
            message.delete()
            logger.debug(f"Processed event number {count} (loops={loops + 1})")

        # if loops>=10:raise Exception#during testing
        # if loops > 40:
        #     raise Exception


def process_event(config, body):
    for record in body.get('Records', []):
        s3 = record.get('s3')
        if not s3:
            # If it's not an S3 event, we don't care.
            logger.debug(f"Ignoring record because it's not S3")
            continue
        # Only bother if the filename is exactly "buildhub.json"
        if not os.path.basename(s3['object']['key']) == 'buildhub.json':
            logger.debug(f"Ignoring S3 key {s3['object']['key']}")
            continue

        process_buildhub_json_key(config, s3)


def process_buildhub_json_key(config, s3):
    logger.debug(f"S3 buildhub.json key {s3!r}")
    key_name = s3['object']['key']
    assert os.path.basename(key_name) == 'buildhub.json', key_name
    bucket_name = s3['bucket']['name']
    # We need a S3 connection client to be able to download this one.
    if bucket_name not in config:
        logger.debug('Creating a new BOTO3 S3 CLIENT')
        config[bucket_name] = boto3.client('s3', config['region_name'])

    with io.BytesIO() as f:
        try:
            config[bucket_name].download_fileobj(bucket_name, key_name, f)
        except ClientError as exception:
            if exception.response['Error']['Code'] == '404':
                logger.warning(
                    f"Tried to download {key_name} (in {bucket_name}) "
                    "but not found."
                )
                return
            raise

        # After it has been populated by download_fileobj() we need to
        # rewind it so we can send it to json.load().
        f.seek(0)
        # Before exiting this context (and freeing up the binary data),
        # we turn it into a Python dict.
        build = json.load(f)

    # XXX Needs to deal with how to avoid corrupt buildhub.json S3 keys
    # never leaving the system.
    try:
        inserted = Build.insert(
            build=build,
            s3_object_key=s3['object']['key'],
            s3_object_etag=s3['object']['eTag'],
        )
    except ValidationError as exc:
        # We're only doing a try:except ValidationError: here so we get a
        # chance to log a useful message about the S3 object and the
        # validation error message.
        logger.warning(
            "Failed to insert build because the build was not valid. "
            f"S3 key {key_name!r} (bucket {bucket_name!r}). "
            f"Validation error message: {exc.message}"
        )
        raise
    if inserted:
        logger.info(
            f"Inserted {key_name} as a valid Build ({inserted.build_hash})"
        )
    else:
        logger.info(
            f"Did not insert {key_name} because we already had it"
        )
