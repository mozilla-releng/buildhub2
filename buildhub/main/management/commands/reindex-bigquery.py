# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from buildhub.main.models import Build
from buildhub.main.bigquery import get_schema_file_object

logger = logging.getLogger("buildhub")


class Command(BaseCommand):
    help = "Create new table from Postgres into BigQuery via batched inserts."

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

        if input("Are you sure? [y/N] ").lower().strip() != "y":
            print("Aborted!")
            return

        client.delete_table(table_id, not_found_ok=True)
        schema = client.schema_from_json(get_schema_file_object())
        table = bigquery.table.Table(table_id, schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY, field="created_at"
        )
        client.create_table(table)

        max_error_count = 1000
        error_count = 0
        chunk_size = 10000
        count = 0

        build_docs = Build.objects.all().order_by("created_at")
        total_count = build_docs.count()
        for chunk in build_docs.iterator(chunk_size=chunk_size):
            rows = [doc.to_dict(True) for doc in chunk]
            errors = client.insert_rows(table, rows)
            for error in errors:
                error_count += 1
                logging.warning(error)
                if error_count >= max_error_count:
                    raise Exception(
                        "encountered max number of errors: {error_count}/count"
                    )
            count += chunk_size
            # print at every chunk
            print(
                format(count, ",").ljust(8),
                "\t",
                "{:.1f}%".format(100 * count / total_count),
            )
