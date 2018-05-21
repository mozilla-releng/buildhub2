
from django.core.management.base import BaseCommand
from django.conf import settings
from buildhub.ingest.sqs import start


class Command(BaseCommand):
    help = (
        "This will start a never-ending daemon that will sit and consume an "
        "AWS SQS queue forever. If it crashes in any way, it is the caller "
        "of this command's responsibility to start it again."
    )

    def handle(self, *args, **options):
        start(
            settings.SQS_QUEUE_URL,
            wait_time=settings.SQS_QUEUE_WAIT_TIME_SECONDS,
            visibility_timeout=settings.SQS_QUEUE_VISIBILITY_TIMEOUT,
            max_number_of_messages=settings.SQS_QUEUE_MAX_NUMBER_OF_MESSAGES,
        )
