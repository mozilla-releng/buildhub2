# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

# import copy
import os
import json
import pytest
from jsonschema import ValidationError

from buildhub.main.models import Build
from buildhub.main.search import BuildDoc


def load(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return json.load(f)


def VALID_BUILD():
    # Returns a new copy of a valid buildhub.json as a Python dict.
    return load('valid-buildhub.json')


@pytest.mark.django_db
def test_insert(settings):
    build = VALID_BUILD()
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
def test_insert_writes_to_elasticsearch(settings, elasticsearch):
    build = VALID_BUILD()
    inserted = Build.insert(build)
    assert inserted

    # Because Elasticsearch is async, the content written won't be there
    # until we wait or flush.
    elasticsearch.flush()
    search = BuildDoc.search()
    response = search.execute()
    assert response.hits.total == 1
    build_doc, = response
    assert build_doc.id == inserted.id
    as_dict = build_doc.to_dict()
    as_dict.pop('id')
    # Can't easily compare these because elasticseach_dsl will convert
    # dates to datetime.datetime objects.
    # But if we convert dates from the Elasticsearch query to a string
    # we can compare.
    as_dict['build']['date'] = as_dict['build']['date'].isoformat()[:19]
    as_dict['download']['date'] = as_dict['download']['date'].isoformat()[:19]
    build = inserted.build
    build['build']['date'] = build['build']['date'][:19]
    build['download']['date'] = build['download']['date'][:19]
    assert as_dict == build


@pytest.mark.django_db
def test_insert_invalid(settings):
    build = VALID_BUILD()
    # We can't completely mess with the schema to the point were it
    # breaks Elasticsearch writes.
    build['source']['junk'] = True
    with pytest.raises(ValidationError) as exception:
        Build.insert(build)
    err_msg = "Additional properties are not allowed ('junk' was unexpected)"
    assert err_msg in str(exception.value)

    # The 'skip_validation' is kinda dumb but it exists for when you're
    # super certain that the stuff you're inserting really is valid.
    Build.insert(build, skip_validation=True)


@pytest.mark.django_db
def test_bulk_insert():
    one = VALID_BUILD()
    two = VALID_BUILD()
    assert one == two
    assert one is not two
    insert_count = Build.bulk_insert([one, two])
    # Because they're *equal*
    assert insert_count == 1
    assert Build.objects.all().count() == 1

    two['download']['size'] += 1
    three = VALID_BUILD()
    three['download']['size'] += 2
    insert_count = Build.bulk_insert([one, two, three])
    assert insert_count == 2
    # Even though they're "inserted at the same time", their created_at
    # should be different.
    created_ats = [x.created_at for x in Build.objects.all()]
    assert created_ats[0] != created_ats[1]
    assert created_ats[1] != created_ats[2]
    assert Build.objects.all().count() == 3

    insert_count = Build.bulk_insert([one, two, three])
    assert insert_count == 0


@pytest.mark.django_db
def test_bulk_insert_invalid():
    one = VALID_BUILD()
    two = VALID_BUILD()
    two.pop('target')
    with pytest.raises(ValidationError) as exception:
        Build.bulk_insert([one, two])
    assert "'target' is a required property" in str(exception.value)
    # Even if the first one was valid, it won't be inserted.
    assert not Build.objects.exists()
