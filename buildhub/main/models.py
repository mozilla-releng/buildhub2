# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import os
import hashlib
import json

import yaml
from jsonschema import ValidationError
from jsonschema.validators import validator_for

from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField

# from django.db.models.signals import pre_save
from django.db.models.signals import post_save
from django.utils.encoding import force_bytes

from buildhub.main.search import BuildDoc, es_retry


with open(os.path.join(settings.BASE_DIR, "schema.yaml")) as f:
    SCHEMA = yaml.load(f)["schema"]
_validator_class = validator_for(SCHEMA)
_validator_class.check_schema(SCHEMA)
validator = _validator_class(SCHEMA)


class Build(models.Model):
    build_hash = models.CharField(max_length=45, unique=True)
    build = JSONField()
    metadata = JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    # Every time we insert a build from an S3 key, we write these
    # down. The advantage is that when we run the backfill script
    # we can very quickly figure out if we have this build or not without
    # having to first download the S3 object, get its build_hash and look
    # it up that way.
    s3_object_key = models.CharField(max_length=400, null=True)
    s3_object_etag = models.CharField(max_length=400, null=True)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.build_hash!r}>"

    def to_search(self, **kwargs):
        return BuildDoc.create(self.id, **self.build)

    hash_prefix = "v1"

    @classmethod
    def get_build_hash(cls, build):
        """Set mutate=True if you don't mind it mutating."""
        prefix = "v1"
        md5string = hashlib.md5(
            force_bytes(json.dumps(build, sort_keys=True))
        ).hexdigest()
        return f"{prefix}:{md5string}"

    @classmethod
    def validate_build(cls, build):
        validator.validate(build)

    @classmethod
    def insert(cls, build, metadata=None, skip_validation=False, **kwargs):
        """Optimized version that tries to insert but doesn't complain if
        the build_hash is already there."""
        metadata = metadata or {}
        if skip_validation:
            metadata["skip_validation"] = True
        metadata.update(settings.VERSION)

        # Two options for how to insert without raising conflict errors.
        #
        #   * Seek permission - Do a .exists() query first, then .create()
        #   * Seek forgiveness - try:... except IntegrityError: pass
        #
        # Some numbers (doing it locally on a local Postgres)...
        #
        # Using 'Seek permission':
        #
        #  * 1,000 all new objects:
        #    - MEAN   3.51ms
        #    - MEDIAN 3.37ms
        #  * 1,000 all existing objects
        #    - MEAN   0.57ms
        #    - MEDIAN 0.54ms
        #  * 500 new, 500 existing
        #    - MEAN   2.02ms
        #    - MEDIAN 2.63ms
        #
        # Using 'Seek forgiveness':
        #
        #  * 1,000 all new objects:
        #    - MEAN   9.25ms
        #    - MEDIAN 9.08ms
        #  * 1,000 all existing objects
        #    - MEAN   2.33ms
        #    - MEDIAN 2.26ms
        #  * 500 new, 500 existing
        #    - MEAN   7.04ms
        #    - MEDIAN 4.40ms
        #
        if not skip_validation:
            cls.validate_build(build)
        build_hash = cls.get_build_hash(build)
        if not cls.objects.filter(build_hash=build_hash).exists():
            return cls.objects.create(
                build_hash=build_hash, build=build, metadata=metadata, **kwargs
            )

    @classmethod
    def bulk_insert(
        cls, builds, metadata=None, skip_validation=False, skip_invalid=False
    ):
        """Bulk insert that avoids potential conflict inserts by first
        checking for existances.

        Note! This method is NOT thread-safe. The reason is that we query
        the database which build hashes it does *not* have, then we come
        back to this code and prepare to send them to the database with
        Build.objects.bulk_create(). So if new builds are made during that
        window of time, you might get conflict errors during the bulk insert.

        Note! This method does NOT update Elasticsearch.
        """
        metadata = metadata or {}
        if skip_invalid:
            assert not skip_validation
            # Forcing this because we're doing the validation first,
            # and it mustn't be run again.
            skip_validation = True
        elif skip_validation:
            metadata["skip_validation"] = True
        metadata.update(settings.VERSION)
        # Note! Unfortunately, there is no easy way to do a bulk insert.
        # Not until https://code.djangoproject.com/ticket/28668 lands.
        hashes = {}
        skipped = 0
        for build in builds:
            if skip_invalid:
                try:
                    cls.validate_build(build)
                except ValidationError:
                    skipped += 1
                    continue
            hashes[cls.get_build_hash(build)] = build
        for build_hash in cls.objects.filter(build_hash__in=hashes.keys()).values_list(
            "build_hash", flat=True
        ):
            hashes.pop(build_hash)
        if not skip_validation:
            # Only run the validation on the records that we're about to
            # insert.
            # The reason we're doing this late is because calculating the
            # build's hash string is much much faster than calling
            # `cls.validate_build(build)` on the build.
            # Did some benchmarks on this and found that it takes about
            # 1.5ms to run the validation and 0.03ms to generate the hash.
            for build in hashes.values():
                cls.validate_build(build)
        cls.objects.bulk_create(
            [cls(build_hash=k, build=v, metadata=metadata) for k, v in hashes.items()]
        )
        return len(hashes), skipped


# @receiver(pre_save, sender=Build)
# def prepare(sender, instance, **kwargs):
#     assert instance.build
#     assert instance.build_hash
#     # if not instance.build_hash:
#     #     assert instance.build
#     #     instance.build_hash = sender.get_build_hash(instance.build)


@receiver(post_save, sender=Build)
def send_to_elasticsearch(sender, instance, **kwargs):
    doc = instance.to_search()
    es_retry(doc.save)
