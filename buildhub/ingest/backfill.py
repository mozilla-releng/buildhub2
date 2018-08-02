# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import re
import io
from urllib.parse import urlparse

import boto3
import markus
from django.db import transaction
from buildhub.main.models import Build


logger = logging.getLogger("buildhub")
metrics = markus.get_metrics("buildhub2")


@metrics.timer_decorator("backfill")
def backfill(s3_url, region_name=None):
    def download_and_insert(obj, maybe=False):
        key = obj["Key"]
        with io.BytesIO() as f:
            # 'bucket_name' and 's3_client' is hoisted from the closure
            s3_client.download_fileobj(bucket_name, key, f)
            # After it has been populated by download_fileobj() we need to
            # rewind it so we can send it to json.load().
            f.seek(0)
            # Before exiting this context (and freeing up the binary data),
            # we turn it into a Python dict.
            build = json.load(f)
        inserted = Build.insert(
            build=build, s3_object_key=obj["Key"], s3_object_etag=obj["ETag"]
        )
        if inserted:
            logger.info(f"New Build inserted from backfill ({key})")
            metrics.incr("backfill_inserted")
        else:
            logger.info(f"Key downloaded but not inserted again ({key})")
            metrics.incr("backfill_not_inserted")
        if maybe and not inserted:
            # If this happens, it means that the build exists exactly with
            # this build_hash already but the ETag isn't matching.
            # Update the s3_object_* attributes
            found = Build.objects.filter(
                s3_object_key=key, build_hash=Build.get_build_hash(build)
            )
            found.update(s3_object_etag=obj["ETag"])

    def is_equal_etags(etag1, etag2):
        if etag1.startswith('"'):
            etag1 = etag1[1:-1]
        if etag2.startswith('"'):
            etag2 = etag2[1:-1]
        return etag1 == etag2

    # Prepare a massive dict every existing known Build by their 's3_object_key'.
    existing = get_builds_existing_map()
    existing_set = set(existing.keys())
    logger.info(f"We currently have {len(existing_set)} s3_object_keys in our database")
    bucket_name = urlparse(s3_url).path.split("/")[-1]
    if not region_name:
        region_name = re.findall(r"s3[\.-](.*?)\.amazonaws\.com", s3_url)[0]
    s3_client = boto3.client("s3", region_name)
    count = 0
    for objs in get_matching_s3_objs(
        s3_client, bucket_name, suffix="buildhub.json", max_keys=100
    ):
        keys = {x["Key"]: x for x in objs}
        keys_set = set(keys.keys())
        count += len(keys_set)
        # Of the keys that we've never seen in our database before,
        # this is a slam dunk.
        with transaction.atomic():
            for key in keys_set - existing_set:
                download_and_insert(keys[key])
                keys.pop(key)

            for key in keys:
                etag_before = existing[key]
                if is_equal_etags(etag_before, keys[key]["ETag"]):
                    continue
                # The Etag has changed!
                download_and_insert(keys[key], maybe=True)
    logger.info(f"Analyzed {count} keys (called buildhub.json) from S3")


def get_builds_existing_map():
    existing = {}
    qs = Build.objects.filter(s3_object_key__isnull=False).only(
        "s3_object_key", "s3_object_etag"
    )
    while True:
        for build in qs.order_by("id")[:1000]:
            existing[build.s3_object_key] = build.s3_object_etag
            qs = qs.filter(id__gt=build.id)
        else:
            break

    return existing


def get_matching_s3_objs(s3_client, bucket, prefix="", suffix="", max_keys=1000):
    """
    Return an iterator of S3 objects in batches.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    kwargs = {"Bucket": bucket, "MaxKeys": max_keys, "Prefix": prefix}
    loops = 0
    while True:
        resp = s3_client.list_objects_v2(**kwargs)
        metrics.incr("backfill_listed", len(resp["Contents"]))
        matched = [
            obj for obj in resp["Contents"] if not suffix or obj["Key"].endswith(suffix)
        ]
        logger.info(f"Found {len(matched)} S3 keys on page {loops + 1}")
        if matched:
            metrics.incr("backfill_matched", len(matched))
            yield matched
        try:
            kwargs["ContinuationToken"] = resp["NextContinuationToken"]
        except KeyError:
            break
        loops += 1
