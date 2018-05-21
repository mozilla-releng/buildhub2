# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

# import copy
import os
import json
import pytest
from jsonschema import ValidationError

from buildhub.main.models import Build


def load(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return json.load(f)


def VALID_BUILD():
    # Returns a new copy of a valid buildhub.json as a Python dict.
    return load('valid-buildhub.json')


@pytest.mark.django_db
def test_insert():
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
def test_insert_invalid():
    build = VALID_BUILD()
    build.pop('target')
    with pytest.raises(ValidationError) as exception:
        Build.insert(build)
    assert "'target' is a required property" in str(exception.value)

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
