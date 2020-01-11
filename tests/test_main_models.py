# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from jsonschema import ValidationError

from buildhub.main.models import Build
from buildhub.main.search import BuildDoc
from utils import runif_bigquery_testing_enabled


@pytest.mark.django_db
def test_insert(settings, valid_build):
    build = valid_build()
    inserted = Build.insert(build)
    assert inserted.build_hash
    assert inserted.build == build
    assert inserted.created_at
    assert inserted.build_hash in repr(inserted)

    # It's idempotent.
    second_time = Build.insert(build)
    assert not second_time
    assert Build.objects.all().count() == 1


@pytest.mark.django_db
def test_model_serialization(valid_build):
    """Example document:
    ```
    {
        "build_hash": "v1:465552ab2ea1b5039a086987b70c598c",
        "metadata": {
            "version": "Testing"
        },
        "build": {
            ...
        },
        "created_at": "2020-01-10T22:46:32.274Z",
        "s3_object_key": "",
        "s3_object_etag": ""
    }
    ```
    """
    build = valid_build()
    inserted = Build.insert(build)
    doc = inserted.to_dict()
    assert set(doc.keys()) == {
        "build_hash",
        "build",
        "metadata",
        "created_at",
        "s3_object_key",
        "s3_object_etag",
    }


@runif_bigquery_testing_enabled
@pytest.mark.django_db
def test_serialized_instance_inserts_into_bigquery(bigquery_testing_table, valid_build):
    """Test that the fixture is created and insertion is successful."""
    client, table = bigquery_testing_table
    doc = Build.insert(valid_build()).to_dict()
    errors = client.insert_rows(table, [doc])
    assert errors == []

    table_id = f"{table.dataset_id}.{table.table_id}"
    job = client.query(f"SELECT COUNT(*) as n_rows FROM {table_id}")
    result = list(job.result())[0]
    assert result.n_rows == 1


@pytest.mark.django_db
def test_insert_writes_to_elasticsearch(settings, elasticsearch, valid_build):
    build = valid_build()
    inserted = Build.insert(build)
    assert inserted

    # Because Elasticsearch is async, the content written won't be there
    # until we wait or flush.
    elasticsearch.flush()
    search = BuildDoc.search()
    response = search.execute()
    assert response.hits.total == 1
    (build_doc,) = response
    assert build_doc.id == inserted.id
    as_dict = build_doc.to_dict()
    as_dict.pop("id")
    # Can't easily compare these because elasticseach_dsl will convert
    # dates to datetime.datetime objects.
    # But if we convert dates from the Elasticsearch query to a string
    # we can compare.
    as_dict["build"]["date"] = as_dict["build"]["date"].isoformat()[:19]
    as_dict["download"]["date"] = as_dict["download"]["date"].isoformat()[:19]
    build = inserted.build
    build["build"]["date"] = build["build"]["date"][:19]
    build["download"]["date"] = build["download"]["date"][:19]
    assert as_dict == build


@pytest.mark.django_db
def test_insert_invalid(settings, valid_build):
    build = valid_build()
    # We can't completely mess with the schema to the point were it
    # breaks Elasticsearch writes.
    build["source"]["junk"] = True
    with pytest.raises(ValidationError) as exception:
        Build.insert(build)
    err_msg = "Additional properties are not allowed ('junk' was unexpected)"
    assert err_msg in str(exception.value)

    # The 'skip_validation' is kinda dumb but it exists for when you're
    # super certain that the stuff you're inserting really is valid.
    Build.insert(build, skip_validation=True)


@pytest.mark.django_db
def test_bulk_insert(valid_build):
    one = valid_build()
    two = valid_build()
    assert one == two
    assert one is not two
    insert_count, skipped = Build.bulk_insert([one, two])
    assert skipped == 0
    # Because they're *equal*
    assert insert_count == 1
    assert Build.objects.all().count() == 1

    two["download"]["size"] += 1
    three = valid_build()
    three["download"]["size"] += 2
    insert_count, skipped = Build.bulk_insert([one, two, three])
    assert skipped == 0
    assert insert_count == 2
    # Even though they're "inserted at the same time", their created_at
    # should be different.
    created_ats = [x.created_at for x in Build.objects.all()]
    assert created_ats[0] != created_ats[1]
    assert created_ats[1] != created_ats[2]
    assert Build.objects.all().count() == 3

    insert_count, skipped = Build.bulk_insert([one, two, three])
    assert skipped == 0
    assert insert_count == 0


@pytest.mark.django_db
def test_bulk_insert_invalid(valid_build):
    one = valid_build()
    two = valid_build()
    two.pop("target")
    with pytest.raises(ValidationError) as exception:
        Build.bulk_insert([one, two])
    assert "'target' is a required property" in str(exception.value)
    # Even if the first one was valid, it won't be inserted.
    assert not Build.objects.exists()


@pytest.mark.django_db
def test_bulk_insert_invalid_skip_invalid(valid_build):
    one = valid_build()
    two = valid_build()
    two.pop("target")

    inserted, skipped = Build.bulk_insert([one, two], skip_invalid=True)
    assert inserted == 1
    assert skipped == 1
    # The first one would be inserted.
    assert Build.objects.count() == 1
