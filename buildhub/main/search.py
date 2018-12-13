# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import logging

import backoff
from elasticsearch.exceptions import TransportError
from elasticsearch_dsl import Document, InnerDoc, Object, Long, Date, Keyword
from django.conf import settings


logger = logging.getLogger("buildhub")


@backoff.on_exception(
    backoff.constant,
    # The NotFoundError is a bit more tricky. Perhaps we want to delete
    # an item from Elasticsearch (at the time of writing; no plan to delete
    # things) then we might get NotFoundError exceptions caught up in this.
    TransportError,
    max_time=10,
)
def es_retry(callable, *args, **kwargs):
    return callable(*args, **kwargs)


class _Build(InnerDoc):
    id = Keyword()
    date = Date()


class _Source(InnerDoc):
    product = Keyword()
    repository = Keyword()
    tree = Keyword()
    revision = Keyword()


class _Target(InnerDoc):
    platform = Keyword()
    os = Keyword()
    locale = Keyword()
    version = Keyword()
    channel = Keyword()


class _Download(InnerDoc):
    url = Keyword()
    mimetype = Keyword()
    size = Long()
    date = Date()


class BuildDoc(Document):
    id = Keyword(required=True)
    # Note! The reason for using Object() instead of Nested() is because
    # SearchKit doesn't work if it's nested. This works though.
    build = Object(_Build)
    source = Object(_Source)
    target = Object(_Target)
    download = Object(_Download)

    class Index:
        name = settings.ES_BUILD_INDEX
        settings = settings.ES_BUILD_INDEX_SETTINGS

    @classmethod
    def create(cls, id, **doc):
        assert id and isinstance(id, int) and id > 0
        return BuildDoc(
            meta={"id": id},
            id=id,
            build=_Build(**doc["build"]),
            source=_Source(**doc["source"]),
            target=_Target(**doc["target"]),
            download=_Download(**doc["download"]),
        )
