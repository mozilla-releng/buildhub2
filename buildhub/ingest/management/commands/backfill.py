# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

from django.core.management.base import BaseCommand
from django.conf import settings
from buildhub.ingest.backfill import backfill


class Command(BaseCommand):
    help = (
        "This will go over every single file in the S3 bucket and see if "
        "don't already have it in our database."
    )

    def handle(self, *args, **options):
        backfill(settings.S3_BUCKET_URL)