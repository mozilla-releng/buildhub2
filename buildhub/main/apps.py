import markus
from elasticsearch_dsl.connections import connections

from django.conf import settings
from django.apps import AppConfig


class MainConfig(AppConfig):
    name = "buildhub.main"

    def ready(self):
        self._connect_elasticsearch()
        self._configure_markus()

    @staticmethod
    def _connect_elasticsearch():
        connections.configure(**settings.ES_CONNECTIONS)

    @staticmethod
    def _configure_markus():
        """Must be done once and only once."""
        markus.configure(settings.MARKUS_BACKENDS)
