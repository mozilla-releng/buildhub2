import logging
import json
import os
import io
from django.conf import settings
from google.cloud import bigquery


with open(os.path.join(settings.BASE_DIR, "schema.bigquery.json")) as f:
    PAYLOAD_SCHEMA = json.load(f)

logger = logging.getLogger("buildhub")

# Information outside of the payload, as defined by the main model specified
# using json syntax for BigQuery schemas.
# See: https://cloud.google.com/bigquery/docs/schemas
BQ_SCHEMA = [
    {"name": "build_hash", "type": "STRING", "mode": "REQUIRED"},
    {"name": "build", "type": "RECORD", "mode": "REQUIRED", "fields": PAYLOAD_SCHEMA},
    {
        "name": "metadata",
        "type": "RECORD",
        "mode": "NULLABLE",
        "fields": [{"name": "version", "type": "STRING", "mode": "NULLABLE"}],
    },
    {"name": "created_at", "type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "s3_object_key", "type": "STRING", "mode": "NULLABLE"},
    {"name": "s3_object_etag", "type": "STRING", "mode": "NULLABLE"},
]


def get_schema_file_object():
    serialized = json.dumps(BQ_SCHEMA)
    return io.StringIO(serialized)


def insert_build(document):
    """Insert a single document into an existing BigQuery table."""
    # new client instance for every insertion
    project_id = settings.BQ_PROJECT_ID
    dataset_id = settings.BQ_DATASET_ID
    table_id = f"{project_id}.{dataset_id}.{settings.BQ_TABLE_ID}"

    client = bigquery.Client(project=project_id)
    table = client.get_table(table_id)
    errors = client.insert_rows(table, [document])
    if errors:
        logging.error(f"failed into insert row: {errors[0]}")
