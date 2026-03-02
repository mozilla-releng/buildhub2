# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import io
import json
from unittest import mock

import pytest
from botocore.exceptions import ClientError
from django.core.management import call_command
from jsonschema import ValidationError

from buildhub.ingest.pubsub import start
from buildhub.main.models import Build


# cvalaas created this for nonprod:
# projects/moz-fx-productdelivery-no-7d6a/subscriptions/test-productdelivery-sub
# TODO: architect these tests in such a way that we don't need to exercise google crap code
# you can test that integration-y in local dev and/or deployed env
# you still may need the message format for the real code which is:

MESSAGE_TEMPLATE = {
  "kind": "storage#object",
  "id": "fake-bucket/{filePath}/1719270506555849",
  "selfLink": "https://www.googleapis.com/storage/v1/b/fake-bucket/o/{filePath.replace('/', '%2F')}",
  "name": "{filePath}",
  "bucket": "fake-bucket",
  "generation": "1719254245340314",
  "metageneration": "1",
  "contentType": "text/x-patch",
  "timeCreated": "2024-06-24T18:37:25.389Z",
  "updated": "2024-06-24T18:37:25.389Z",
  "storageClass": "STANDARD",
  "timeStorageClassUpdated": "2024-06-24T18:37:25.389Z",
  "size": "96312",
  # note: this md5 hash does not match the contents, but that doesn't matter for our tests
  "md5Hash": "zwNwO89jLAYb5j+Nw/OMQg==",
  "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/test-bucket/o/{filePath.replace('/', '%2F'}?generation=1719254245340314&alt=media",
  "crc32c": "pSankw==",
  "etag": "CJrpyZTx9IYDEAE="
}

class FakeSubscriber:
    def __init__(self, messages):
        self.messages = messages
        self.future = asyncio.get_running_loop().create_future()

        return self.future

    def subscribe(self, _, callback):
        for m in self.messages:
            callback(m)

        self.future.set_result(True)


@pytest.mark.parametrize("filePaths",
    (
        pytest.param(
            [
                "/foo/bar/buildhub.json",
            ],
            id="buildhub_only",
        )
    ),
   # TODO: many more tests. see test_ingest_sqs.py for inspiration
)
@pytest.mark.django_db
@mock.patch("buildhub.ingest.pubsub.pubsub_v1")
def test_start_happy_path(mocked_pubsub, settings, valid_build, mocker, filePaths):
    messages = []
    for f in filePaths:
        m = MESSAGE_TEMPLATE.copy()
        for key in ("id", "selfLink", "name", "mediaLink"):
            m[key].format(filePath=f)

    mocked_pubsub.SubscriberClient.return_value = FakeSubscriber(messages)

    # TODO: mock out any file downloads that may happen, and possibly other things
    # see test_ingest_sqs.py for inspiration

    start(settings.PUBSUB_TOPIC, settings.PUBSUB_SUBSCRIPTION)

    # It should have created 1 Build
    assert Build.objects.get()



# TODO: do we need a pubsub version of this test?
# @mock.patch("buildhub.ingest.pubsub.boto3")
# def test_call_daemon_command(
#     mocked_boto3, settings, valid_build, itertools_count, mocker
# ):
#     # Really making this test rough by forcing there to be no new messages.
#     mocked_queue = mocker.MagicMock()
#     mocked_queue.receive_messages().__iter__.return_value = []
#     mocked_boto3.resource().get_queue_by_name.return_value = mocked_queue
#
#     out = io.StringIO()
#     call_command("daemon", stdout=out)
#     assert not out.getvalue()
