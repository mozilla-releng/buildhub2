# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import requests
from elasticsearch_dsl.connections import connections
from elasticsearch.helpers import streaming_bulk
from django.core.management.base import BaseCommand
from django.conf import settings

from buildhub.main.search import BuildDoc
from buildhub.main.models import Build


class Command(BaseCommand):
    help = (
        "Reindex everything in Postgres to Elasticsearch. "
        "In bulk. And by first deleting the index."
    )

    def handle(self, *args, **options):
        build_index = BuildDoc._index
        build_index.delete(ignore=404)
        build_index.create()
        es_url = settings.ES_URLS[0]
        index_name = settings.ES_BUILD_INDEX
        update_settings_url = f"{es_url}/{index_name}/_settings"
        response = requests.put(
            update_settings_url, json={"index": {"refresh_interval": "-1"}}
        )
        response.raise_for_status()

        es = connections.get_connection()
        report_every = 1000
        count = 0

        qs = Build.objects.all().order_by("created_at")
        total_count = qs.count()
        iterator = qs.iterator(chunk_size=10000)
        for success, doc in streaming_bulk(
            es,
            (m.to_search().to_dict(True) for m in iterator),
            index=index_name,
            doc_type="doc",
        ):
            if not success:
                raise Exception(doc)
            count += 1
            if not count % report_every:
                print(
                    format(count, ",").ljust(8),
                    "\t",
                    "{:.1f}%".format(100 * count / total_count),
                )

        # We have done a bunch of bulk inserts into Elasticsearch with
        # the refresh interval "disabled". Now we need to "force merge"
        # the index. See
        # https://www.elastic.co/guide/en/elasticsearch/reference/6.x/indices-update-settings.html#bulk

        force_merge_url = f"{es_url}/{index_name}/_forcemerge?max_num_segments=5"
        response = requests.post(force_merge_url)
        response.raise_for_status()
        print("Force merged Elasticsearch index after bulk insert")

        # Restore refresh_interval
        response = requests.put(
            update_settings_url,
            json={
                "index": {
                    "refresh_interval": settings.ES_BUILD_INDEX_SETTINGS[
                        "refresh_interval"
                    ]
                }
            },
        )
        response.raise_for_status()
