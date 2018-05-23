# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

from django.core.management.base import BaseCommand
from django.conf import settings

from buildhub.main.search import build_index
from buildhub.main.models import Build


class Command(BaseCommand):
    help = (
        "Delete all content from Postgres and Elasticsearch"
    )

    def handle(self, *args, **options):

        assert settings.DEBUG, "Only ever works in DEBUG mode"

        if input("Are you sure? [y/N] ").lower().strip() != 'y':
            print("Aborted!")
            return
        Build.objects.all().delete()
        build_index.delete(ignore=404)
