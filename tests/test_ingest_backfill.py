# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import io
import json
from unittest import mock

import pytest
from django.core.management import call_command

from buildhub.main.models import Build
from buildhub.ingest.backfill import backfill


@pytest.mark.django_db
@mock.patch("buildhub.ingest.backfill.boto3")
def test_backfill_happy_path(
    mocked_boto3, settings, valid_build, itertools_count, mocker
):

    # Create a ready build that is *exactly* like our mocked S3 thing is.
    build = valid_build()
    build["download"]["mimetype"] = "one/buildhub.json"
    Build.insert(
        build=build, s3_object_key="one/buildhub.json", s3_object_etag="abc123"
    )

    # Create one build that has the same build_hash as the second mocked
    # key but make the s3_object_etag mismatch.
    build = valid_build()
    build["download"]["mimetype"] = "two/buildhub.json"
    Build.insert(
        build=build,
        s3_object_key="two/buildhub.json",
        s3_object_etag="somethingdifferent",
    )

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        assert bucket_name == "buildhubses"
        build = valid_build()
        # Just need to mess with the build a little bit so that it's
        # still valid to the schema but makes a different build_hash.
        if key_name == "two/buildhub.json":
            build["download"]["mimetype"] = key_name
        elif key_name == "three/buildhub.json":
            build["download"]["mimetype"] = key_name
        elif key_name == "three/Firefox-99-buildhub.json":
            build["download"]["mimetype"] = key_name
        else:
            raise NotImplementedError(key_name)
        f.write(json.dumps(build).encode("utf-8"))

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj

    def mocked_list_objects(**kwargs):
        if kwargs.get("ContinuationToken"):  # you're on page 2
            return {"Contents": [{"Key": "three/buildhub.json", "ETag": "ghi345"}]}
        else:
            return {
                "Contents": [
                    {"Key": "one/buildhub.json", "ETag": "abc123"},
                    {"Key": "two/buildhub.json", "ETag": "def234"},
                    {"Key": "three/Firefox-99-buildhub.json", "ETag": "xyz987"},
                ],
                "NextContinuationToken": "nextpageplease",
            }

    mocked_s3_client.list_objects_v2.side_effect = mocked_list_objects
    backfill(settings.S3_BUCKET_URL)

    # We had 2 before, this should have created 2 new and edited 1
    assert Build.objects.all().count() == 4
    # The second one should have had its etag updated
    assert not Build.objects.filter(
        s3_object_key="two/buildhub.json", s3_object_etag="somethingdifferent"
    )
    assert Build.objects.get(s3_object_key="two/buildhub.json", s3_object_etag="def234")
    assert Build.objects.get(
        s3_object_key="three/Firefox-99-buildhub.json", s3_object_etag="xyz987"
    )


@pytest.mark.django_db
@mock.patch("buildhub.ingest.backfill.boto3")
def test_call_backfill_command(
    mocked_boto3, settings, valid_build, itertools_count, mocker
):
    # Really making this test rough by forcing there to be no new messages.
    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_list_objects(**kwargs):
        return {"Contents": []}

    mocked_s3_client.list_objects_v2.side_effect = mocked_list_objects
    out = io.StringIO()
    call_command("backfill", stdout=out)
    assert "Been backfilling for 0:00" in out.getvalue()
