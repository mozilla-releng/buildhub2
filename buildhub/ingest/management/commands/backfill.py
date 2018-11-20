# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import time

from django.core.management.base import BaseCommand
from django.conf import settings
from buildhub.ingest.backfill import backfill


class Command(BaseCommand):
    help = (
        "This will go over every single file in the S3 bucket and see if "
        "don't already have it in our database."
    )

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--resume",
            action="store_true",
            default=False,
            help="Will try to continue where it last fell through.",
        )

    def handle(self, *args, **options):
        t0 = time.time()
        try:
            backfill(settings.S3_BUCKET_URL, resume=options["resume"])
        finally:
            t1 = time.time()
            self.stdout.write(
                self.style.SUCCESS(
                    "Been backfilling for {}".format(
                        datetime.timedelta(seconds=int(t1 - t0))
                    )
                )
            )
