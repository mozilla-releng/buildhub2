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

import requests
import backoff

from django.core.management.base import BaseCommand

from buildhub.main.models import Build


logger = logging.getLogger("buildhub")


@backoff.on_exception(
    backoff.constant,
    requests.exceptions.RequestException,
    max_tries=3,
)
def fetch(session, url):
    logger.debug(f"Fetching {url}")
    return session.get(url)


class Command(BaseCommand):
    help = (
        "Given a Kinto URL this will download all their existing records, "
        "repackage them as valid buildhub.json blobs and ingest them."
    )

    def add_arguments(self, parser):
        parser.add_argument('kinto-url')
        parser.add_argument(
            '--skip-validation', default=False, action='store_true',
            help=(
                "If you really trust the records you get out of Kinto you "
                "can skip the validation of each and every record."
            )
        )

    def handle(self, *args, **options):
        # Ping it first
        kinto_url = options['kinto-url']
        r = requests.get(kinto_url)
        r.raise_for_status()
        assert r.json()['project_name'] == 'kinto', r.json()

        if kinto_url.endswith('/'):
            kinto_url = kinto_url[:-1]
        url = (
            f"{kinto_url}/buckets/build-hub/collections/releases/records"
            "?_limit=10000"
        )
        pages = 0
        session = requests.Session()
        done = 0
        skip_validation = options['skip_validation']
        for batch, total_records in self.iterator(session, url):
            logger.info(f"Page {pages + 1} ({len(batch)} records)")
            # Now let's bulk insert these
            builds = []
            for record in batch:
                record.pop('id')
                record.pop('last_modified')
                builds.append(record)
            # Skip validation most of the time
            t0 = time.time()
            inserted = Build.bulk_insert(
                builds,
                skip_validation=skip_validation,
                metadata={'kinto-migration': True},
            )
            t1 = time.time()
            done += len(batch)
            logger.info(
                "Inserted {} new out of {} in "
                "{:.2f} seconds. {} of {} ({:.1f}%)".format(
                    format(inserted, ','),
                    format(len(builds), ','),
                    t1 - t0,
                    format(done, ','),
                    format(total_records, ','),
                    100 * done / total_records,
                )
            )

            pages += 1

    def iterator(self, session, url):
        total_records = None
        while True:
            response = fetch(session, url)
            response.raise_for_status()
            if total_records is None:
                total_records = int(response.headers['Total-Records'])
            yield response.json()['data'], total_records
            try:
                next_page = response.headers['Next-Page']
                if not next_page:
                    raise KeyError('exists but empty value')
                url = next_page
            except KeyError:
                break
