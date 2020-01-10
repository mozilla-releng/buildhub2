# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import requests
from django.core.management.base import BaseCommand
from django.conf import settings

from buildhub.main.models import Build


class Command(BaseCommand):
    help = "Reindex tables from Postgres into BigQuery via batched inserts."

    def handle(self, *args, **options):
        """See https://googleapis.dev/python/bigquery/latest/index.html."""

        # TODO: Best place to put this variable? Implicit in GOOGLE_APPLICATION_CREDENTIALS
        project_id = "buildhub2-bigquery-dev"
        dataset_id = settings.BQ_DATASET_ID
        table_id = settings.BQ_TABLE_ID

        client = bigquery.Client()
        qualified_table_id = f"{project_id}.{dataset_id}.{table_id}"
        table = client.get_table(qualified_table_id)

        chunk_size = 10000
        count = 0

        build_docs = Build.objects.all().order_by("created_at")
        total_count = build_docs.count()
        for chunk in build_docs.iterator(chunk_size=chunk_size):
            rows = [doc.to_dict(True) for doc in chunk]
            errors = client.insert_rows(table, rows)
            if errors:
                # dump the the first error seen
                raise Exception(errors[0])
            count += chunk_size
            # print at every chunk
            print(
                format(count, ",").ljust(8),
                "\t",
                "{:.1f}%".format(100 * count / total_count),
            )
