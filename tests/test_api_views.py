# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from django.urls import reverse

from buildhub.main.models import Build


@pytest.mark.django_db
def test_happy_path(valid_build, client, elasticsearch):
    build = valid_build()
    Build.insert(build)
    elasticsearch.flush()

    url = reverse("api:search")
    response = client.get(url)
    assert response.status_code == 200
    result = response.json()
    assert result["hits"]["total"] == 1
    hit, = result["hits"]["hits"]
    assert hit["_source"]["target"]["version"] == build["target"]["version"]

    # No CSP header for the API requests since they're always JSON.
    assert not response.has_header("Content-Security-Policy")


@pytest.mark.django_db
def test_search_aggregations(valid_build, json_poster, elasticsearch):
    build = valid_build()
    build["target"]["version"] = "60.0.1"
    Build.insert(build)
    build = valid_build()
    build["target"]["version"] = "60.0.2"
    Build.insert(build)
    build = valid_build()
    build["target"]["version"] = "60.1"
    Build.insert(build)

    elasticsearch.flush()

    search = {
        "aggs": {
            "versions": {
                "filter": {"match_all": {}},
                "aggs": {
                    "target.version": {
                        "terms": {
                            "field": "target.version",
                            "size": 1000,
                            "order": {"_term": "desc"},
                            "include": "6.*",
                        }
                    },
                    "target.version_count": {
                        "cardinality": {"field": "target.version"}
                    },
                },
            }
        },
        "size": 0,
    }

    url = reverse("api:search")
    response = json_poster(url, search)
    assert response.status_code == 200
    result = response.json()
    assert result["hits"]["total"] == 3
    assert not result["hits"]["hits"]  # because only aggregations
    agg_key = "versions"
    buckets = result["aggregations"][agg_key]["target.version"]["buckets"]
    assert buckets == [
        {"key": "60.1", "doc_count": 1},
        {"key": "60.0.2", "doc_count": 1},
        {"key": "60.0.1", "doc_count": 1},
    ]

    # This time filter more
    search["aggs"][agg_key]["aggs"]["target.version"]["terms"]["include"] = "60.0.*"
    response = json_poster(url, search)
    assert response.status_code == 200
    result = response.json()

    buckets = result["aggregations"][agg_key]["target.version"]["buckets"]
    assert buckets == [
        {"key": "60.0.2", "doc_count": 1},
        {"key": "60.0.1", "doc_count": 1},
    ]


@pytest.mark.django_db
def test_search_requesterror(valid_build, json_poster, elasticsearch):
    search = {"from": 0, "query": {"term": {}}, "size": 2}
    url = reverse("api:search")
    response = json_poster(url, search)
    assert response.status_code == 400
    assert response.json()["error"]["reason"] == "field name is null or empty"


@pytest.mark.django_db
def test_search_empty_filter(valid_build, json_poster, elasticsearch):
    search = {
        "query": {
            "bool": {
                "filter": [{}],
                "must": [
                    {"term": {"target.channel": "nightly"}},
                    {"term": {"source.product": "firefox"}},
                ],
            }
        },
        "size": 2,
    }
    url = reverse("api:search")
    response = json_poster(url, search)
    assert response.status_code == 400
    assert response.json()["error"] == (
        'Q() can only accept dict with a single query ({"match": {...}}). '
        "Instead it got ({})"
    )


@pytest.mark.django_db
def test_search_unbound_size(valid_build, json_poster, elasticsearch, settings):
    search = {"query": {"match_all": {}}, "size": settings.MAX_SEARCH_SIZE + 1}
    url = reverse("api:search")
    response = json_poster(url, search)
    assert response.status_code == 400
    assert response.json()["error"] == "Search size too large (1001)"


@pytest.mark.django_db
def test_happy_path_records(valid_build, client, elasticsearch):
    url = reverse("api:records")
    response = client.get(url)
    assert response.status_code == 200
    result = response.json()
    assert result["builds"]["total"] == 0

    build = valid_build()
    Build.insert(build)
    response = client.get(url)
    assert response.status_code == 200
    result = response.json()
    assert result["builds"]["total"] == 1
