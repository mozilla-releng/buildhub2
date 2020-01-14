# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import shutil
from functools import partial
import uuid

import pytest
from unittest import mock
import requests
import requests_mock

from django.conf import settings
from google.cloud import bigquery

# Needed to make sure django-configurations works correctly
# Without it, we get:
# django.core.exceptions.ImproperlyConfigured:
# django-configurations settings importer wasn't correctly installed.
# Please use one of the starter functions to install it as mentioned
# in the docs: https://django-configurations.readthedocs.io/
from buildhub import wsgi
from buildhub.main.search import BuildDoc
from buildhub.main.bigquery import get_schema_file_object

from utils import runif_bigquery_testing_enabled

assert wsgi


def pytest_configure():
    """Automatically called by pytest-django. Here's our chance to make sure
    the settings are tight and specific to running tests."""

    # This makes sure we never actually use the Elasticsearch index
    # we use for development.
    settings.ES_BUILD_INDEX = "test_buildhub2"
    settings.BQ_ENABLED = False

    # Make sure we can ping the Elasticsearch
    response = requests.get(settings.ES_URLS[0])
    response.raise_for_status()


def _load(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return json.load(f)


@pytest.fixture
def valid_build():
    """Return a function that returns a valid dict of a valid buildhub.json.
    Useful because it always generates a new one so you don't have to worry
    about mutating a fixture.
    Usage::

        def test_something(valid_build):
            build = valid_build()
            build2 = valid_build()
            assert build == build2
            assert build is not build2
            build['target']['version'] = 'different'
            assert build2['target']['version'] != 'different'
    """
    return partial(_load, "valid-buildhub.json")


@pytest.fixture
def valid_build_release_channel():
    return partial(_load, "valid-buildhub-release-channel.json")


@pytest.fixture
def valid_build_fennec_release_channel():
    return partial(_load, "valid-buildhub-fennec-release-channel.json")


@pytest.fixture
def elasticsearch(request):
    """Returns the index object for builds. But before, it re-creates the index.
    And after the index is deleted. All 404s ignored.

    Usage::

        def test_something(elasticsearch):
            # Test stuff and assume the Elasticsearch build index
            # exists and is empty.

            assert something

    """

    build_index = BuildDoc._index
    assert build_index._name.startswith("test_")
    build_index.delete(ignore=404)
    build_index.create()
    yield build_index
    build_index.delete(ignore=404)


@runif_bigquery_testing_enabled
@pytest.fixture
def bigquery_testing_table(settings):
    """Yields a BigQuery client and the reference to the testing table.

    Usage::

        @runif_bigquery_testing_enabled
        def test_bigquery_behavior(bigquery_testing_table):
            client, table = bigquery
            ...
            errors = client.insert_rows(table, rows)
            ...
    """
    # enable callback after insertion into the model store
    settings.BQ_ENABLED = True

    project_id = settings.BQ_PROJECT_ID
    client = bigquery.Client(project=project_id)

    # create a new testing dataset
    dataset_id = f"{settings.BQ_DATASET_ID}_pytest"
    client.delete_dataset(dataset_id, delete_contents=True, not_found_ok=True)
    client.create_dataset(dataset_id)

    # create a partitioned table
    schema = client.schema_from_json(get_schema_file_object())
    # Due to eventual consistency and caching behavior when streaming into
    # re-created tables, we include a random table suffix to always create a new
    # table. This avoids streaming delays.
    # https://github.com/googleapis/google-cloud-php/issues/871
    salt = str(uuid.uuid4())[:8]
    table_id = f"{project_id}.{dataset_id}.{settings.BQ_TABLE_ID}_{salt}"
    table = bigquery.table.Table(table_id, schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY, field="created_at"
    )
    client.create_table(table)

    # yield and cleanup
    yield client, table
    client.delete_dataset(dataset_id, delete_contents=True, not_found_ok=True)


@pytest.fixture
def json_poster(client):
    """
    Uses the client instance to make a client.post() call with the 'data'
    as a valid JSON string with the right header.
    """

    def inner(url, data, **extra):
        debug = extra.pop("debug", None)
        if not isinstance(data, str):
            data = json.dumps(data)
        extra["content_type"] = "application/json"
        if debug is not None:
            extra["HTTP_DEBUG"] = str(debug)
        return client.post(url, data, **extra)

    return inner


@pytest.fixture
def requestsmock():
    """Return a context where requests are all mocked.
    Usage::

        def test_something(requestsmock):
            requestsmock.get(
                'https://example.com/path'
                content=b'The content'
            )
            # Do stuff that involves requests.get('http://example.com/path')
    """
    with requests_mock.mock() as m:
        yield m


# # This needs to be imported at least once. Otherwise the mocking
# # done in botomock() doesn't work.
# # (peterbe) Would like to know why but for now let's just comply.
# import boto3  # noqa

# _orig_make_api_call = botocore.client.BaseClient._make_api_call


# @pytest.fixture
# def botomock():
#     """Return a class that can be used as a context manager when called.
#     Usage::

#         def test_something(botomock):

#             def my_make_api_call(self, operation_name, api_params):
#                 if random.random() > 0.5:
#                     from botocore.exceptions import ClientError
#                     parsed_response = {
#                         'Error': {'Code': '403', 'Message': 'Not found'}
#                     }
#                     raise ClientError(parsed_response, operation_name)
#                 else:
#                     return {
#                         'CustomS3': 'Headers',
#                     }

#             with botomock(my_make_api_call):
#                 ...things that depend on boto3...

#                 # You can also, whilst debugging on tests,
#                 # see what calls where made.
#                 # This is handy to see and assert that your replacement
#                 # method really was called.
#                 print(botomock.calls)

#     Whilst working on a test, you might want wonder "What would happen"
#     if I let this actually use the Internet to make the call un-mocked.
#     To do that use ``botomock.orig()``. For example::

#         def test_something(botomock):

#             def my_make_api_call(self, operation_name, api_params):
#                 if api_params == something:
#                     ...you know what to do...
#                 else:
#                     # Only in test debug mode
#                     result = botomock.orig(self, operation_name, api_params)
#                     print(result)
#                     raise NotImplementedError

#     """

#     class BotoMock:

#         def __init__(self):
#             self.calls = []

#         def __call__(self, mock_function):

#             def wrapper(f):
#                 def inner(*args, **kwargs):
#                     self.calls.append(args[1:])
#                     return f(*args, **kwargs)
#                 return inner

#             return mock.patch(
#                 'botocore.client.BaseClient._make_api_call',
#                 new=wrapper(mock_function)
#             )

#         def orig(self, *args, **kwargs):
#             return _orig_make_api_call(*args, **kwargs)

#     return BotoMock()


@pytest.fixture
def itertools_count():
    """Patches the `itertools` inside buildhub.ingest.sqs so that you can
    force it to not return too many iterations.
    Usage::

        def test_something(itertools_count):
            itertools_count.count.return_value = [0, 1, 2]

    Note, that the default is to return `[0]` so you don't need to do this::

        def test_something(itertools_count):
            itertools_count.count.return_value = [0]

    It's the default.
    """

    with mock.patch("buildhub.ingest.sqs.itertools") as mocked:
        mocked.count.return_value = [0]
        yield mocked


@pytest.fixture
def temp_static_root(settings):
    """Update settings such that settings.STATIC_ROOT is always an existing but
    empty temporary directory.
    This is useful when you want to control the settings.STATIC_ROOT content
    explicitly.
    Usage::

        def test_something(temp_static_root):
            assert os.path.isdir(temp_static_root)
            assert not os.listdir(temp_static_root)
            with open(temp_static_root + '/foo.html', 'w') as f:
                f.write('<html>')
                ...

    """
    assert os.path.basename(settings.STATIC_ROOT).startswith("test_")
    if os.path.isdir(settings.STATIC_ROOT):
        shutil.rmtree(settings.STATIC_ROOT)
    os.makedirs(settings.STATIC_ROOT)
    yield settings.STATIC_ROOT
