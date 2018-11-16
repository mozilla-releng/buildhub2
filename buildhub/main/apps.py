import markus
from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from elasticsearch_dsl.connections import connections


class MainConfig(AppConfig):
    name = "buildhub.main"

    def ready(self):
        self._connect_elasticsearch()
        self._configure_markus()
        self._check_s3_bucket_urls()

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
