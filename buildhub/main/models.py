import hashlib
import json

import yaml
from jsonschema import validate
from unipath import Path

from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import pre_save
from django.utils.encoding import force_bytes


with open(Path(settings.BASE_DIR, 'schema.yaml')) as f:
    SCHEMA = yaml.load(f)['schema']


class Build(models.Model):
    build_hash = models.CharField(max_length=45, unique=True)
    build = JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.build_hash!r}>"

    hash_prefix = 'v1'

    @classmethod
    def get_build_hash(cls, build):
        """Set mutate=True if you don't mind it mutating."""
        prefix = 'v1'
        md5string = hashlib.md5(
            force_bytes(json.dumps(build, sort_keys=True))
        ).hexdigest()
        return f'{prefix}:{md5string}'

    @classmethod
    def validate_build(cls, build, schema=SCHEMA):
        validate(build, schema)

    @classmethod
    def insert(cls, build, validate=False):
        """Optimized version that tries to insert but doesn't complain if
        the build_hash is already there."""

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
        if validate:
            cls.validate_build(build)
        build_hash = cls.get_build_hash(build)
        if not cls.objects.filter(build_hash=build_hash).exists():
            return cls.objects.create(build_hash=build_hash, build=build)

    @classmethod
    def bulk_insert(cls, builds, validate=False):
        """Bulk insert that avoids potential conflict inserts by first
        checking for existances.

        Note! This method is NOT thread-safe.
        """
        # Note! Unfortunately, there is no easy way to do a bulk insert.
        # Not until https://code.djangoproject.com/ticket/28668 lands.
        hashes = {}
        for build in builds:
            if validate:
                cls.validate(build)
            hashes[cls.get_build_hash(build)] = build
        for build_hash in cls.objects.filter(
            build_hash__in=hashes.keys()
        ).values_list('build_hash', flat=True):
            hashes.pop(build_hash)
        cls.objects.bulk_create([
            cls(build_hash=k, build=v) for k, v in hashes.items()
        ])
        return len(hashes)


@receiver(pre_save, sender=Build)
def prepare(sender, instance, **kwargs):
    if not instance.build_hash:
        assert instance.build
        instance.build_hash = sender.get_build_hash(instance.build)

    if not kwargs.get('skip_validation'):
        Build.validate_build(instance.build)
