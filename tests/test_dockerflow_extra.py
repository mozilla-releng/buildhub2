# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

from requests.exceptions import ConnectionError

from buildhub.dockerflow_extra import check_elasticsearch


def test_check_elasticsearch(elasticsearch, settings):
    """This is a fully functional test that requires a healthy Elasticsearch
    connection."""
    elasticsearch.flush()
    errors = check_elasticsearch(None)
    assert not errors


def test_check_elasticsearch_connection_error(mocker):
    mocked_fetch = mocker.patch("buildhub.dockerflow_extra.fetch")

    def mocked_side_effect(index):
        raise ConnectionError("Oh no!")

    mocked_fetch.side_effect = mocked_side_effect
    errors = check_elasticsearch(None)
    assert errors
    error, = errors
    assert "Unable to connect to Elasticsearch" in error.msg


def test_check_elasticsearch_failed_health(mocker):
    mocked_fetch = mocker.patch("buildhub.dockerflow_extra.fetch")

    def mocked_side_effect(index):
        return {"status": "brownish"}

    mocked_fetch.side_effect = mocked_side_effect
    errors = check_elasticsearch(None)
    assert errors
    error, = errors
    assert "not healthy" in error.msg
    assert "brownish" in error.msg
