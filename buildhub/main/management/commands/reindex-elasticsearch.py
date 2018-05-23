# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import requests
from elasticsearch_dsl.connections import connections
from elasticsearch.helpers import streaming_bulk
from django.core.management.base import BaseCommand
from django.conf import settings

from buildhub.main.search import build_index
from buildhub.main.models import Build


class Command(BaseCommand):
    help = (
        "Reindex everything in Postgres to Elasticsearch. "
        "In bulk. And by first deleting the index."
    )

    def handle(self, *args, **options):

        bulk_refresh_interval = (
            settings.ES_BUILD_INDEX_SETTINGS['refresh_interval'] == '-1'
        )
        if not bulk_refresh_interval:
            print(" WARNING ".center(80, "-"))
            print(
                "When doing re-index, it's adviced that you set "
                "environment variable:\n\n"
                "\tES_REFRESH_INTERVAL=-1\n\n"
                "for much faster reindexing."
            )
            print("\n")

        build_index.delete(ignore=404)
        build_index.create()

        es = connections.get_connection()
        report_every = 500
        count = 0

        iterator = Build.objects.all().order_by("created_at")
        total_count = iterator.count()

        index_name = settings.ES_BUILD_INDEX
        for success, doc in streaming_bulk(
            es,
            (
                m.to_search().to_dict(True)
                for m in iterator
            ),
            index=index_name,
            doc_type="doc",
        ):
            if not success:
                raise Exception(doc)
            count += 1
            if not count % report_every:
                print(
                    format(count, ",").ljust(6),
                    "\t",
                    "{:.1f}%".format(100 * count / total_count)
                )

        if bulk_refresh_interval:
            # We have done a bunch of bulk inserts into Elasticsearch with
            # the refresh interval "disabled". Now we need to "force merge"
            # the index. See
            # https://www.elastic.co/guide/en/elasticsearch/reference/6.x/indices-update-settings.html#bulk
            es_url = settings.ES_URLS[0]
            force_merge_url = (
                f"{es_url}/{index_name}/_forcemerge?max_num_segments=5"
            )
            response = requests.post(force_merge_url)
            response.raise_for_status()
            print("Force merged Elasticsearch index after bulk insert")
