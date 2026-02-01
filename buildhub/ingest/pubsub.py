# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

from copy import deepcopy
import io
import itertools
import json
import logging
import os
import re
from urllib.parse import urlparse

import markus
from google.cloud import pubsub_v1
from jsonschema import ValidationError

from buildhub.main.models import Build

logger = logging.getLogger("buildhub")
metrics = markus.get_metrics("buildhub2")


def start(
    subscription_name,
    wait_time=10,
    visibility_timeout=5,
    max_number_of_messages=1,
):
    # subscribe to pubsub something or other
    with pubsub_v1.SubscriberClient() as subscriber:
        future = subscriber.subscribe(subscription_name, process_event)

        # TODO: probably need to do this in an interruptable way to
        # make sure we can shut down properly?
        future.result()


def process_event(config, body):
    # TODO: adapt to pubsub
    try:
        message = body["Message"]
        assert isinstance(message, str), type(message)
        records = json.loads(message).get("Records", [])
    except KeyError:
        if "Records" in body:
            records = body["Records"]
        else:
            raise
    for record in records:
        s3 = record.get("s3")
        if not s3:
            # If it's not an S3 event, we don't care.
            logger.debug("Ignoring record because it's not S3")
            continue
        # Only bother if the filename is exactly "buildhub.json"
        if not os.path.basename(s3["object"]["key"]).endswith("buildhub.json"):
            logger.debug(f"Ignoring S3 key {s3['object']['key']}")
            metrics.incr("sqs_not_key_matched")
            continue

        metrics.incr("sqs_key_matched")
        process_buildhub_json_key(config, s3)


@metrics.timer_decorator("sqs_process_buildhub_json_key")
def process_buildhub_json_key(config, s3):
    # TODO: adapt to pubsub
    logger.debug(f"S3 buildhub.json key {s3!r}")
    key_name = s3["object"]["key"]
    assert os.path.basename(key_name).endswith("buildhub.json"), key_name
    bucket_name = s3["bucket"]["name"]
    # We need a S3 connection client to be able to download this one.
    if bucket_name not in config:
        logger.debug("Creating a new BOTO3 S3 CLIENT")
        connection_config = None
        if settings.UNSIGNED_S3_CLIENT:
            connection_config = Config(signature_version=UNSIGNED)
        config[bucket_name] = boto3.client(
            "s3", config["region_name"], config=connection_config
        )

    with io.BytesIO() as f:
        try:
            config[bucket_name].download_fileobj(bucket_name, key_name, f)
        except ClientError as exception:
            if exception.response["Error"]["Code"] == "404":
                logger.warning(
                    f"Tried to download {key_name} (in {bucket_name}) " "but not found."
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
    inserted = []
    try:
        ret = Build.insert(
            build=build,
            s3_object_key=s3["object"]["key"],
            s3_object_etag=s3["object"]["eTag"],
        )
        inserted.append(ret)
        # This is a hack to fix https://bugzilla.mozilla.org/show_bug.cgi?id=1470948
        # In some future world we might be able to architecture buildhub in such a way
        # where this sort of transformation isn't buried down deep in the code
        if (
            build["source"]["product"] == "firefox"
            and build["target"]["channel"] == "release"
        ):
            beta_build = deepcopy(build)
            beta_build["target"]["channel"] = "beta"
            ret = Build.insert(
                build=beta_build,
                s3_object_key=s3["object"]["key"],
                s3_object_etag=s3["object"]["eTag"],
            )
            inserted.append(ret)

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
    # Build.insert() above can return None (for Builds that already exist).
    # If anything was _actually_ inserted, log it.
    if any(inserted):
        for i in inserted:
            metrics.incr("sqs_inserted")
            logger.info(f"Inserted {key_name} as a valid Build ({i.build_hash})")
    else:
        metrics.incr("sqs_not_inserted")
        logger.info(f"Did not insert {key_name} because we already had it")
