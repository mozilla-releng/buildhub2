# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from buildhub.main.models import Build
from buildhub.main.bigquery import get_schema_file_object

logger = logging.getLogger("buildhub")


class Command(BaseCommand):
    help = "Create new table from Postgres into BigQuery via batched inserts."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--yes",
            action="store_true",
            default=False,
            help="Confirm overwriting tables without prompt",
        )

    def handle(self, *args, **options):
        """See https://googleapis.dev/python/bigquery/latest/index.html."""

        project_id = settings.BQ_PROJECT_ID
        dataset_id = settings.BQ_DATASET_ID
        table_id = f"{project_id}.{dataset_id}.{settings.BQ_TABLE_ID}"

        client = bigquery.Client(project=project_id)
        try:
            client.get_table(table_id)
            print(f"Will drop and create {table_id}.")
        except NotFound:
            print(f"Will create {table_id}.")

        if not options["yes"] and input("Are you sure? [y/N] ").lower().strip() != "y":
            print("Aborted!")
            return

        client.delete_table(table_id, not_found_ok=True)
        schema = client.schema_from_json(get_schema_file_object())
        table = bigquery.table.Table(table_id, schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY, field="created_at"
        )
        client.create_table(table)

        max_error_count = settings.BQ_REBUILD_MAX_ERROR_COUNT
        chunk_size = settings.BQ_REBUILD_CHUNK_SIZE
        count = 0
        error_count = 0
        start = time.time()

        builds = Build.objects.all().order_by("created_at")
        total_count = builds.count()

        # stateful inner loop
        def insert_batch(rows):
            nonlocal count
            nonlocal error_count
            if not rows:
                return
            errors = client.insert_rows(table, rows)
            for error in errors:
                error_count += 1
                logging.warning(error)
                if error_count >= max_error_count:
                    raise Exception(
                        "encountered max number of errors: {error_count}/count"
                    )
            count += len(rows)
            # print at every chunk
            print(
                format(count, ",").ljust(8),
                "\t",
                "{:.1f}%".format(100 * count / total_count),
            )

        rows = []
        for build in builds.iterator(chunk_size=chunk_size):
            rows.append(build.to_dict())
            if len(rows) < chunk_size:
                continue
            insert_batch(rows)
            rows = []
        insert_batch(rows)

        end = time.time()
        print(
            f"Completed insert of {count} documents with {error_count} errors "
            f"in {end-start} seconds"
        )
