# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import markus
from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from elasticsearch_dsl.connections import connections
from buildhub.main.bigquery import ensure_table


class MainConfig(AppConfig):
    name = "buildhub.main"

    def ready(self):
        self._connect_elasticsearch()
        self._configure_markus()
        self._check_s3_bucket_urls()
        self._ensure_bigquery_table()

    @staticmethod
    def _connect_elasticsearch():
        connections.configure(**settings.ES_CONNECTIONS)

    @staticmethod
    def _configure_markus():
        """Must be done once and only once."""
        markus.configure(settings.MARKUS_BACKENDS)

    @staticmethod
    def _check_s3_bucket_urls():
        """Sanity check what you've set in the settings."""
        if settings.S3_BUCKET_URL == settings.SQS_S3_BUCKET_URL:
            raise ImproperlyConfigured(
                f"settings.SQS_S3_BUCKET_URL ({settings.SQS_S3_BUCKET_URL}) doesn't "
                "need to be set if it's the same value as settings.S3_BUCKET_URL"
            )

    @staticmethod
    def _ensure_bigquery_table():
        """Check for configured BigQuery credentials and access to the table.
        On failure, this will raise various exception from the `google`
        namespace."""
        if settings.BQ_ENABLED:
            ensure_table()
