from elasticsearch_dsl.connections import connections

from django.conf import settings
from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'buildhub.main'

    def ready(self):
        self._connect_elasticsearch()

    @staticmethod
    def _connect_elasticsearch():
        connections.configure(**settings.ES_CONNECTIONS)

