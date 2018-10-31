# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

"""
This script is deliberately not unit tested. The intention is to run
this some day; once.

In the olden days, we used to scrape and scrutinize every individual file
published to the S3 bucket. All that scrutinzing resulted in that we save
a blob of JSON. That's
"""

import logging
import time

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.db import connection, connections
from django.db.models.sql.compiler import cursor_iter

from buildhub.main.models import Build

logger = logging.getLogger("buildhub")


class Command(BaseCommand):
    help = (
        "This uses the 'kinto' database connection to manually extract all the "
        "old records from a Kinto database. "
        "It is outside the remit of this script to make that database exist and "
        "be up to date."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-validation",
            default=False,
            action="store_true",
            help=(
                "If you really trust the records you get out of Kinto you "
                "can skip the validation of each and every record."
            ),
        )
        parser.add_argument(
            "--parent-id", default="/buckets/build-hub/collections/releases", help=""
        )
        parser.add_argument("--collection-id", default="record", help="")
        parser.add_argument("--chunk-size", default=10000, help="")

    def handle(self, *args, **options):
        if not settings.DATABASES.get("kinto"):
            raise ImproperlyConfigured(
                "See configuration documentation about setting up "
                "second the 'kinto' connection."
            )

        pages = 0
        done = 0
        skip_validation = options["skip_validation"]
        for builds, total_records in self.iterator(options):
            count = len(builds)
            logger.info(f"Page {pages + 1} ({count} records)")
            t0 = time.time()
            inserted = Build.bulk_insert(
                builds,
                skip_validation=skip_validation,
                metadata={"kinto-migration": True},
            )
            t1 = time.time()
            done += count
            logger.info(
                "Inserted {} new out of {} in "
                "{:.2f} seconds. {} of {} ({:.1f}%)".format(
                    format(inserted, ","),
                    format(count, ","),
                    t1 - t0,
                    format(done, ","),
                    format(total_records, ","),
                    100 * done / total_records,
                )
            )

            pages += 1

    def iterator(self, options):
        with connections["kinto"].cursor() as cursor:

            try:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM records
                    WHERE
                        parent_id = %s AND collection_id = %s
                """,
                    [options["parent_id"], options["collection_id"]],
                )
            except Exception:
                cursor.close()
                raise
            total_records, = cursor.fetchone()

            try:
                cursor.execute(
                    """
                    SELECT data
                    FROM records
                    WHERE
                        parent_id = %s AND collection_id = %s
                """,
                    [options["parent_id"], options["collection_id"]],
                )
            except Exception:
                cursor.close()
                raise

            chunk_size = options["chunk_size"]

            for rows in cursor_iter(
                cursor, connection.features.empty_fetchmany_value, None, chunk_size
            ):
                yield rows, total_records
