import copy
import hashlib
import json

import yaml
from jsonschema import validate
from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import pre_save
from django.utils.encoding import force_bytes


with open(settings.BASE_DIR.join('buildhub/schema.yaml')) as f:
    SCHEMA = yaml.load(f)


class Build(models.Model):
    build = JSONField()
    build_hash = models.CharField(max_length=32, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    hash_prefix = 'v1'
    hash_skip_keys = ('')

    @classmethod
    def get_build_hash(cls, build, mutate=False):
        """Set mutate=True if you don't mind it mutating."""
        prefix = 'v1'
        if not mutate:
            build = copy.copy(build)
        for key in cls.hash_skip_keys:
            build.pop(key, None)
        md5string = hashlib.md5(
            force_bytes(json.dumps(build, sort_keys=True))
        ).hexdigest()
        return f'{prefix}:{md5string}'

    @classmethod
    def validate_build(cls, build, schema=SCHEMA):
        validate(build, schema)


@receiver(pre_save, sender=Build)
def prepare(sender, instance, **kwargs):
    if not instance.build_hash:
        assert instance.build
        instance.build_hash = sender.get_build_hash(instance.build)

    if not kwargs.get('skip_validation'):
        assert Build.validate_build(instance.build)
