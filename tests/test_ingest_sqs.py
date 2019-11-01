# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import io
import json
from unittest import mock

import pytest
from botocore.exceptions import ClientError
from django.core.management import call_command
from jsonschema import ValidationError

from buildhub.ingest.sqs import start
from buildhub.main.models import Build


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_start_happy_path(mocked_boto3, settings, valid_build, itertools_count, mocker):
    mocked_message = mocker.MagicMock()
    # See
    # https://gist.github.com/peterbe/f739b91c0674d36a1526ccb43b6844c3#file-stage-json
    # for a real life example of a SQS message.
    message = {
        "Message": json.dumps(
            {
                "Records": [
                    {"foot": "here"},
                    {
                        "s3": {
                            "object": {
                                "key": "some/path/to/buildhub.json",
                                "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    },
                    {
                        "s3": {
                            "object": {
                                "key": "not/a/buildhub.json/file",
                                "eTag": "77e09ba7e37836c2cf0ce59e1e8361ab",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    },
                ]
            }
        )
    }
    mocked_message.body = json.dumps(message)
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "some/path/to/buildhub.json"
        f.write(json.dumps(valid_build()).encode("utf-8"))

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    start(settings.SQS_QUEUE_URL)
    mocked_boto3.resource().get_queue_by_name.assert_called_with(
        QueueName="buildhub-s3-events"
    )
    # It should have created 1 Build
    assert Build.objects.get()

    mocked_boto3.client.assert_called_with("s3", "ca-north-2", config=mock.ANY)


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_start_happy_path_release_channel(
    mocked_boto3, settings, valid_build_release_channel, itertools_count, mocker
):

    mocked_message = mocker.MagicMock()
    # See
    # https://gist.github.com/peterbe/f739b91c0674d36a1526ccb43b6844c3#file-stage-json
    # for a real life example of a SQS message.
    message = {
        "Message": json.dumps(
            {
                "Records": [
                    {"foot": "here"},
                    {
                        "s3": {
                            "object": {
                                "key": "some/path/to/buildhub.json",
                                "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    },
                    {
                        "s3": {
                            "object": {
                                "key": "not/a/buildhub.json/file",
                                "eTag": "77e09ba7e37836c2cf0ce59e1e8361ab",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    },
                ]
            }
        )
    }
    mocked_message.body = json.dumps(message)
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "some/path/to/buildhub.json"
        f.write(json.dumps(valid_build_release_channel()).encode("utf-8"))

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    start(settings.SQS_QUEUE_URL)
    mocked_boto3.resource().get_queue_by_name.assert_called_with(
        QueueName="buildhub-s3-events"
    )
    # It should have created 2 Builds
    # TODO: verify channel on both objects
    assert Build.objects.all().count() == 2

    mocked_boto3.client.assert_called_with("s3", "ca-north-2", config=mock.ANY)


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_start_happy_path_fennec_release_channel(
    mocked_boto3, settings, valid_build_fennec_release_channel, itertools_count, mocker
):

    mocked_message = mocker.MagicMock()
    # See
    # https://gist.github.com/peterbe/f739b91c0674d36a1526ccb43b6844c3#file-stage-json
    # for a real life example of a SQS message.
    message = {
        "Message": json.dumps(
            {
                "Records": [
                    {"foot": "here"},
                    {
                        "s3": {
                            "object": {
                                "key": "some/path/to/buildhub.json",
                                "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    },
                    {
                        "s3": {
                            "object": {
                                "key": "not/a/buildhub.json/file",
                                "eTag": "77e09ba7e37836c2cf0ce59e1e8361ab",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    },
                ]
            }
        )
    }
    mocked_message.body = json.dumps(message)
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "some/path/to/buildhub.json"
        f.write(json.dumps(valid_build_fennec_release_channel()).encode("utf-8"))

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    start(settings.SQS_QUEUE_URL)
    mocked_boto3.resource().get_queue_by_name.assert_called_with(
        QueueName="buildhub-s3-events"
    )
    # It should have created 1 Builds
    assert Build.objects.all().count() == 1

    mocked_boto3.client.assert_called_with("s3", "ca-north-2", config=mock.ANY)


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_records_legacy_message(
    mocked_boto3, settings, valid_build, itertools_count, mocker
):
    """In production, in Buildhub2, the messages from S3 and routed through SNS.
    So the list of "Records" in a JSON string inside the "Message" key.
    However, if you have S3 events go straight to SQS, the list of "Records" is
    part of the main object and a top-level key.
    """
    mocked_message = mocker.MagicMock()
    mocked_message.body = json.dumps(
        {
            "Records": [
                {"foot": "here"},
                {
                    "s3": {
                        "object": {
                            "key": "some/path/to/buildhub.json",
                            "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                        },
                        "bucket": {"name": "buildhubses"},
                    }
                },
                {
                    "s3": {
                        "object": {
                            "key": "not/a/buildhub.json/file",
                            "eTag": "77e09ba7e37836c2cf0ce59e1e8361ab",
                        },
                        "bucket": {"name": "buildhubses"},
                    }
                },
            ]
        }
    )
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "some/path/to/buildhub.json"
        f.write(json.dumps(valid_build()).encode("utf-8"))

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    start(settings.SQS_QUEUE_URL)
    mocked_boto3.resource().get_queue_by_name.assert_called_with(
        QueueName="buildhub-s3-events"
    )
    # It should have created 1 Build
    assert Build.objects.get()


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_suffix_match(mocked_boto3, settings, valid_build, itertools_count, mocker):
    mocked_message = mocker.MagicMock()
    message = {
        "Message": json.dumps(
            {
                "Records": [
                    {"foot": "here"},
                    {
                        "s3": {
                            "object": {
                                "key": "firefox-99-buildhub.json",
                                "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    },
                ]
            }
        )
    }
    mocked_message.body = json.dumps(message)
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "firefox-99-buildhub.json"
        f.write(json.dumps(valid_build()).encode("utf-8"))

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    start(settings.SQS_QUEUE_URL)
    mocked_boto3.resource().get_queue_by_name.assert_called_with(
        QueueName="buildhub-s3-events"
    )
    # It should have created 1 Build
    assert Build.objects.get()


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_signed_s3_bucket(mocked_boto3, settings, valid_build, itertools_count, mocker):
    settings.UNSIGNED_S3_CLIENT = False
    mocked_message = mocker.MagicMock()
    message = {
        "Message": json.dumps(
            {
                "Records": [
                    {"foot": "here"},
                    {
                        "s3": {
                            "object": {
                                "key": "firefox-99-buildhub.json",
                                "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    },
                ]
            }
        )
    }
    mocked_message.body = json.dumps(message)
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "firefox-99-buildhub.json"
        f.write(json.dumps(valid_build()).encode("utf-8"))

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    start(settings.SQS_QUEUE_URL)
    mocked_boto3.resource().get_queue_by_name.assert_called_with(
        QueueName="buildhub-s3-events"
    )
    # It should have created 1 Build
    assert Build.objects.get()
    mocked_boto3.client.assert_called_with("s3", "ca-north-2", config=None)


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_ingest_idempotently(
    mocked_boto3, settings, valid_build, itertools_count, mocker
):
    mocked_message = mocker.MagicMock()
    message = {
        "Message": json.dumps(
            {
                "Records": [
                    {
                        "s3": {
                            "object": {
                                "key": "some/path/to/buildhub.json",
                                "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    }
                ]
            }
        )
    }

    mocked_message.body = json.dumps(message)
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    build = valid_build()
    Build.insert(build)

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "some/path/to/buildhub.json"
        f.write(json.dumps(build).encode("utf-8"))

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    start(settings.SQS_QUEUE_URL)
    mocked_boto3.resource().get_queue_by_name.assert_called_with(
        QueueName="buildhub-s3-events"
    )
    # It should have created no new Builds
    assert Build.objects.all().count() == 1


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_start_file_not_found(
    mocked_boto3, settings, valid_build, itertools_count, mocker
):
    mocked_message = mocker.MagicMock()

    message = {
        "Message": json.dumps(
            {
                "Records": [
                    {
                        "s3": {
                            "object": {
                                "key": "some/path/to/buildhub.json",
                                "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    }
                ]
            }
        )
    }

    mocked_message.body = json.dumps(message)
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "some/path/to/buildhub.json"
        parsed_response = {"Error": {"Code": "404", "Message": "Not found"}}
        raise ClientError(parsed_response, "GetObject")

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    start(settings.SQS_QUEUE_URL)
    mocked_boto3.resource().get_queue_by_name.assert_called_with(
        QueueName="buildhub-s3-events"
    )
    # It should have created 1 Build
    assert not Build.objects.all().exists()


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_bad_client_errors(
    mocked_boto3, settings, valid_build, itertools_count, mocker
):
    mocked_message = mocker.MagicMock()
    message = {
        "Message": json.dumps(
            {
                "Records": [
                    {
                        "s3": {
                            "object": {
                                "key": "some/path/to/buildhub.json",
                                "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    }
                ]
            }
        )
    }
    mocked_message.body = json.dumps(message)
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "some/path/to/buildhub.json"
        parsed_response = {"Error": {"Code": "500", "Message": "Oh no!"}}
        raise ClientError(parsed_response, "GetObject")

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    with pytest.raises(ClientError) as exception:
        start(settings.SQS_QUEUE_URL)
    assert "An error occurred (500)" in str(exception.value)


@pytest.mark.django_db
@mock.patch("buildhub.ingest.sqs.boto3")
def test_not_valid_buildhub_json(
    mocked_boto3, settings, valid_build, itertools_count, mocker
):
    mocked_message = mocker.MagicMock()
    message = {
        "Message": json.dumps(
            {
                "Records": [
                    {
                        "s3": {
                            "object": {
                                "key": "some/path/to/buildhub.json",
                                "eTag": "e4eb6609382efd6b3bc9deec616ad5c0",
                            },
                            "bucket": {"name": "buildhubses"},
                        }
                    }
                ]
            }
        )
    }
    mocked_message.body = json.dumps(message)
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = [mocked_message]
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    mocked_s3_client = mocker.MagicMock()
    mocked_boto3.client.return_value = mocked_s3_client

    def mocked_download_fileobj(bucket_name, key_name, f):
        # Sanity checks that the mocking is right
        assert bucket_name == "buildhubses"
        assert key_name == "some/path/to/buildhub.json"
        build = valid_build()
        build["source"]["junk"] = True  # will make it invalid
        f.write(json.dumps(build).encode("utf-8"))

    mocked_s3_client.download_fileobj.side_effect = mocked_download_fileobj
    with pytest.raises(ValidationError) as exception:
        start(settings.SQS_QUEUE_URL)
    err_msg = "Additional properties are not allowed ('junk' was unexpected)"
    assert err_msg in str(exception.value)


@mock.patch("buildhub.ingest.sqs.boto3")
def test_call_daemon_command(
    mocked_boto3, settings, valid_build, itertools_count, mocker
):
    # Really making this test rough by forcing there to be no new messages.
    mocked_queue = mocker.MagicMock()
    mocked_queue.receive_messages().__iter__.return_value = []
    mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue

    out = io.StringIO()
    call_command("daemon", stdout=out)
    assert not out.getvalue()
