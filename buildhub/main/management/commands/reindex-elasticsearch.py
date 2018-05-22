# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

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

        if settings.ES_BUILD_INDEX_SETTINGS['refresh_interval'] != '-1':
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
        report_every = 100
        count = 0

        iterator = Build.objects.all().order_by("created_at")
        total_count = iterator.count()

        for success, doc in streaming_bulk(
            es,
            (
                m.to_search().to_dict(True)
                for m in iterator
            ),
            index=settings.ES_BUILD_INDEX,
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
