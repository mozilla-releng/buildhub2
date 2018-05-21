import json
import logging
import re
import io
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from buildhub.main.models import Build


logger = logging.getLogger('buildhub')


def process_event(config, body):
    for record in body.get('Records', []):
        s3 = record.get('s3')
        if not s3:
            # If it's not an S3 event, we don't care.
            logger.debug(f"Ignoring record because it's not S3")
            continue
        # Only bother if the filename is exactly "buildhub.json"
        if not s3['object']['key'].endswith('/buildhub.json'):
            logger.debug(f"Ignoring S3 key {s3['object']['key']}")
            continue

        process_buildhub_json_key(config, s3)


def process_buildhub_json_key(config, s3):
    logger.debug(f"S3 buildhub.json key {s3!r}")
    key_name = s3['object']['key']
    assert key_name.endswith('/buildhub.json'), key_name
    bucket_name = s3['bucket']['name']
    # We need a S3 connection client to be able to download this one.
    if bucket_name not in config:
        print('Creating a new BOTO3 S3 CLIENT')
        config[bucket_name] = boto3.client('s3', config['region_name'])

    with io.BytesIO() as f:
        try:
            config[bucket_name].download_fileobj(bucket_name, key_name, f)
        except ClientError as exception:
            if exception.response['Error']['Code'] == '404':
                logger.warning(
                    f"Tried to download {key_name} (in {bucket_name}) "
                    "but not found."
                )
                return
            raise

        f.seek(0)
        build = json.load(f)
    inserted = Build.insert(build=build, validate=True)
    if inserted:
        logger.info(
            f"Inserted {key_name} as a valid Build ({inserted.build_hash})"
        )
    else:
        # Could compute
        logger.info(
            f"Did not insert {key_name} because we already had it"
        )
    # print(s3)
    # raise Exception('Stop!')


def start(
    queue_url,
    region_name=None,
    wait_time=10,
    visibility_timeout=5,
    max_number_of_messages=1,
):

    queue_name = urlparse(queue_url).path.split('/')[-1]
    if not region_name:
        region_name = re.findall(r'sqs\.(.*?)\.amazonaws\.com', queue_url)[0]

    logger.debug("Connecting to queue %r in %r", queue_name, region_name)
    sqs = boto3.resource('sqs', region_name=region_name)
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    # for i in itertools.count():
    count = 0

    # This is a mutable that will be included in every callback.
    # It's intended as cheap state so that things like S3 client configuration
    # and connection can be reused without having to be bootstrapped in vain.
    config = {
        'region_name': region_name
    }
    loops=0
    while True:
        loops+=1
        for message in queue.receive_messages(
            WaitTimeSeconds=wait_time,
            VisibilityTimeout=visibility_timeout,
            MaxNumberOfMessages=max_number_of_messages,
        ):
            process_event(config, json.loads(message.body))
            count += 1
            logger.info(f"Processed event number {count}")
            message.delete()

            # if count > 40:
            #     raise Exception

    print('count',count)
    print('loops',loops)


    # class Consumer(SqsListener):
    #     def handle_message(self, body, attributes, messages_attributes):
    #         # Remember, if this method runs without an exception the message
    #         # is automatically deleted.
    #         print("BODY")
    #         print(body)
    #         print('ATTRIBUTES')
    #         print(attributes)
    #         print('MESSAGES ATTRIBUTES')
    #         print(messages_attributes)
    #         print()
    #
    # print('QUEUE NAME ', repr(queue_name))
    # print('REGION NAME', repr(region_name))
    # print('OPTIONS', options)
    # Consumer(
    #     queue_name,
    #     # error_queue='my-error-queue',
    #     region_name=region_name,
    #     **options,
    # ).listen()
